"""Bluesky post search via the AT Protocol (app password -> session JWT).

Search needs an authenticated session. The access JWT is cached in
.research-infra/bluesky-session.json (gitignored, mode 0600); the app password
and refresh token are never stored, and the createSession exchange is never
written to raw captures. Rate limit: ~3,000 requests per 5 minutes; on 429 the
collector stops with ``rate_limited`` rather than sleeping.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_get, http_post, status_from_response, with_query  # noqa: E402

PDS = "https://bsky.social/xrpc"
SESSION_PATH = Path(__file__).resolve().parents[3] / ".research-infra" / "bluesky-session.json"
SESSION_MAX_AGE_S = 90 * 60  # access JWTs live about two hours
SAMPLING_NOTE = "Bluesky post search (relevance/latest per API), public posts only; users skew tech, media and early adopters; not a representative sample."
EXPIRED_ERRORS = {"ExpiredToken", "InvalidToken", "AuthenticationRequired"}


def _read_cache(handle: str) -> str | None:
    try:
        cached = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (isinstance(cached, dict) and cached.get("handle") == handle and cached.get("accessJwt")
            and time.time() - float(cached.get("created_at") or 0) < SESSION_MAX_AGE_S):
        return str(cached["accessJwt"])
    return None


def clear_session() -> None:
    try:
        SESSION_PATH.unlink()
    except OSError:
        pass


def login(handle: str, password: str, timeout: int = 30) -> tuple[str | None, str]:
    """createSession; returns (accessJwt or None, status). Caches only handle + access JWT."""
    response = http_post(f"{PDS}/com.atproto.server.createSession", data={"identifier": handle, "password": password}, timeout=timeout)
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    jwt = body.get("accessJwt")
    if not response.get("ok") or not jwt:
        status = status_from_response(response)
        return None, "permission_denied" if status in {"ok", "failed"} else status
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(SESSION_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle_file:
        json.dump({"handle": handle, "accessJwt": jwt, "created_at": time.time()}, handle_file)
    return str(jwt), "ok"


def get_session(handle: str, password: str) -> tuple[str | None, str]:
    cached = _read_cache(handle)
    return (cached, "ok") if cached else login(handle, password)


def search(jwt: str, query: str, limit: int, days: int | None = None, lang: str = "", timeout: int = 30) -> tuple[dict, dict]:
    params: dict[str, Any] = {"q": query, "limit": max(1, min(int(limit), 100)), "sort": "latest"}
    if lang:
        params["lang"] = lang
    if days:
        params["since"] = (datetime.now(timezone.utc) - timedelta(days=int(days))).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = http_get(with_query(f"{PDS}/app.bsky.feed.searchPosts", params), headers={"Authorization": f"Bearer {jwt}"},
                        timeout=timeout, max_text_chars=2_000_000)
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    status = status_from_response(response)
    if status != "ok" and body.get("error") in EXPIRED_ERRORS:
        status = "session_expired"
    remaining = {k.lower(): v for k, v in (response.get("headers") or {}).items()}.get("ratelimit-remaining")
    if status == "ok" and str(remaining or "").isdigit() and int(remaining) <= 0:
        status = "rate_limited"
    return body, {"status": status, "response": response}


def _default_builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def to_records(body: dict, query: str, retrieved_at: str, build: Callable[..., dict[str, Any]] | None = None,
               customer_segment: str = "", hypothesis: str = "", sampling_frame: str = "topic_led_voc",
               subject_entity_id: str = "") -> list[dict]:
    build = build or _default_builder()
    records: list[dict] = []
    for post in body.get("posts") or []:
        if not isinstance(post, dict):
            continue
        uri = str(post.get("uri") or "")
        record = post.get("record") if isinstance(post.get("record"), dict) else {}
        text = str(record.get("text") or "").strip()
        did = str((post.get("author") or {}).get("did") or "")
        rkey = uri.rsplit("/", 1)[-1]
        if not uri or not text or not did or not rkey:
            continue
        rec = build(source="bluesky", source_url=f"https://bsky.app/profile/{did}/post/{rkey}", query=query,
                    customer_segment=customer_segment, hypothesis=hypothesis, text=text,
                    author_context="Bluesky public post",
                    engagement={"likes": post.get("likeCount"), "comments": post.get("replyCount")},
                    raw_id=uri, published_at=record.get("createdAt") or None,
                    source_language=",".join(record.get("langs") or [])[:20],
                    source_role_override="community_context", author_voice_status="unreviewed",
                    sampling_frame=sampling_frame,
                    subject_entity_id=subject_entity_id if sampling_frame == "entity_led_feedback" else "")
        rec["retrieved_at"] = retrieved_at
        rec["collection_method"] = "official_api"
        rec["retrieval_backend"] = "bluesky"
        rec["sampling_metadata"]["subset_limitations"] = SAMPLING_NOTE
        records.append(rec)
    return records
