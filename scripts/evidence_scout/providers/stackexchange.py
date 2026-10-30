"""Stack Exchange API v2.3 question search (official API; key optional).

Keyless access allows 300 requests/day per IP; STACKEXCHANGE_KEY raises it.
The ``backoff`` field in a response is honoured: short backoffs are slept
(never more than MAX_SLEEP_S in total per process), longer ones stop the
provider with ``rate_limited``.
"""

from __future__ import annotations

import html
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_get, status_from_response, with_query  # noqa: E402

ENDPOINT = "https://api.stackexchange.com/2.3/search/advanced"
DEFAULT_SITE = "stackoverflow"
MAX_SLEEP_S = 30.0
SAMPLING_NOTE = "Stack Exchange relevance-ranked question search; askers skew technical/professional; not a representative sample."

_state: dict[str, float] = {"until": 0.0, "slept": 0.0}


def reset_throttle() -> None:
    _state.update(until=0.0, slept=0.0)


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def strip_html(value: str) -> str:
    parser = _Text()
    parser.feed(value or "")
    parser.close()
    return re.sub(r"\s+", " ", html.unescape("".join(parser.parts))).strip()


def fetch(query: str, site: str, pagesize: int, key: str | None = None, timeout: int = 30) -> tuple[dict, dict]:
    """One search call. Returns (body, meta); meta['status'] may be rate_limited without a call."""
    wait = _state["until"] - time.monotonic()
    if wait > 0:
        if _state["slept"] + wait > MAX_SLEEP_S:
            return {}, {"status": "rate_limited", "response": {"ok": False, "status_code": None,
                        "error": f"Stack Exchange backoff of {wait:.0f}s exceeds the {MAX_SLEEP_S:.0f}s sleep cap; no call made."}}
        time.sleep(wait)
        _state["slept"] += wait
    params = {"q": query, "site": site, "filter": "withbody", "pagesize": pagesize, "order": "desc", "sort": "relevance"}
    if key:
        params["key"] = key
    response = http_get(with_query(ENDPOINT, params), timeout=timeout, max_text_chars=2_000_000)
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    status = status_from_response(response)
    if body.get("error_id") == 502 or (status == "ok" and body.get("quota_remaining") == 0 and not body.get("items")):
        status = "rate_limited"
    backoff = body.get("backoff")
    if isinstance(backoff, (int, float)) and backoff > 0:
        _state["until"] = time.monotonic() + float(backoff)
    return body, {"status": status, "response": response}


def _default_builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def to_records(body: dict, query: str, site: str, retrieved_at: str, build: Callable[..., dict[str, Any]] | None = None,
               customer_segment: str = "", hypothesis: str = "") -> list[dict]:
    build = build or _default_builder()
    records: list[dict] = []
    for item in body.get("items") or []:
        if not isinstance(item, dict):
            continue
        qid, url = str(item.get("question_id") or ""), item.get("link") or ""
        text = "\n\n".join(p for p in [strip_html(item.get("title") or ""), strip_html(item.get("body") or "")] if p)
        if not qid or not url or not text:
            continue
        created = item.get("creation_date")
        published = datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d") if isinstance(created, (int, float)) else None
        tags = ",".join(item.get("tags") or [])
        rec = build(source="stackexchange", source_url=url, query=query, customer_segment=customer_segment,
                    hypothesis=hypothesis, text=text, author_context=f"Stack Exchange question on {site}; tags={tags}",
                    engagement={"upvotes": item.get("score"), "comments": item.get("answer_count"), "views": item.get("view_count")},
                    raw_id=f"{site}:{qid}", published_at=published, source_role_override="community_context",
                    author_voice_status="unreviewed")
        rec["retrieved_at"] = retrieved_at
        rec["collection_method"] = "official_api"
        rec["retrieval_backend"] = "stackexchange"
        rec["sampling_metadata"]["subset_limitations"] = SAMPLING_NOTE
        records.append(rec)
    return records
