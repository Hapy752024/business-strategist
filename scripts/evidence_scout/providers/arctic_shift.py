"""Arctic Shift Reddit archive lane (subreddit history only).

Arctic Shift is a volunteer-run archive: indexing lags live Reddit, search needs a
subreddit (or author), and the service throttles hard. Be polite: >= 1 request/s,
bounded backoff, never sleep more than 30 s in total for one call.
API: https://arctic-shift.photon-reddit.com/api/ (posts/search, comments/search).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_get, status_from_response, with_query  # noqa: E402

BASE = "https://arctic-shift.photon-reddit.com/api/"
MIN_INTERVAL_S = 1.0
BACKOFF_S = 5
MAX_BACKOFFS = 3
MAX_TOTAL_SLEEP_S = 30
COLLECTION_METHOD = "community_archive"
BACKEND = "arctic_shift"
NOTE = ("arctic_shift (volunteer-run Reddit archive): subreddit-only search, indexing lag, "
        "may omit or lag recent content; not a representative sample.")
_last_request = [None]


def _reset_throttle() -> None:
    _last_request[0] = None


def _header(response: dict, name: str) -> str | None:
    for key, value in (response.get("headers") or {}).items():
        if str(key).lower() == name:
            return str(value)
    return None


def _is_timeout(response: dict) -> bool:
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    code = response.get("status_code")
    return code == 429 or (code == 422 and "timeout" in str(body.get("error", "")).lower())


def get_json(path: str, params: dict[str, Any], sleep: Callable[[float], None] = time.sleep,
             clock: Callable[[], float] = time.monotonic) -> tuple[Any, dict]:
    """Throttled GET. Returns (data, meta); meta.status is rate_limited after bounded backoff."""
    slept = 0.0
    attempts = 0
    while True:
        last = _last_request[0]
        if last is not None:
            wait = MIN_INTERVAL_S - (clock() - last)
            if wait > 0:
                sleep(wait)
        _last_request[0] = clock()
        response = http_get(with_query(BASE + path, params), timeout=30)
        attempts += 1
        if response.get("ok"):
            body = response.get("body")
            data = body.get("data") if isinstance(body, dict) else None
            return data, {"status": "ok", "response": response, "attempts": attempts}
        if not _is_timeout(response):
            return None, {"status": status_from_response(response), "response": response, "attempts": attempts}
        delay: float = BACKOFF_S
        reset = _header(response, "x-ratelimit-reset")
        if reset is not None:
            try:
                delay = float(reset)
            except ValueError:
                pass
        if attempts > MAX_BACKOFFS or slept + delay > MAX_TOTAL_SLEEP_S or (reset is not None and delay > 10):
            return None, {"status": "rate_limited", "response": response, "attempts": attempts,
                          "reason": f"Arctic Shift throttled (retry hint {reset or 'none'} s); stopped after {attempts} attempt(s)."}
        sleep(delay)
        slept += delay
        _last_request[0] = None  # the backoff already spaced the next request


def search_posts(subreddit: str, query: str, limit: int, **extra: Any) -> tuple[list[dict], dict]:
    data, meta = get_json("posts/search", {"subreddit": subreddit, "query": query, "limit": limit, **extra})
    return [d for d in data or [] if isinstance(d, dict)], meta


def search_comments(link_id: str, limit: int = 100) -> tuple[list[dict], dict]:
    data, meta = get_json("comments/search", {"link_id": link_id.removeprefix("t3_"), "limit": limit})
    return [d for d in data or [] if isinstance(d, dict)], meta


def _builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record
    return normalize_record


def _finish(rec: dict, retrieved_at: str) -> dict:
    rec["retrieved_at"] = retrieved_at
    rec["collection_method"] = COLLECTION_METHOD
    rec["retrieval_backend"] = BACKEND
    rec["sampling_metadata"]["subset_limitations"] = NOTE
    return rec


def _iso(created_utc: Any) -> str | None:
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(float(created_utc), timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def posts_to_records(posts: list[dict], query: str, retrieved_at: str, build=None,
                     customer_segment: str = "", hypothesis: str = "") -> list[dict]:
    build = build or _builder()
    out = []
    for p in posts:
        pid = str(p.get("id") or "")
        text = "\n\n".join(x for x in [str(p.get("title") or "").strip(), str(p.get("selftext") or "").strip()] if x)
        permalink = str(p.get("permalink") or "")
        url = "https://www.reddit.com" + permalink if permalink.startswith("/") else str(p.get("url") or "")
        if not pid or not text or not url:
            continue
        rec = build(source="reddit", source_url=url, query=query, customer_segment=customer_segment,
                    hypothesis=hypothesis, text=text,
                    author_context=f"r/{p.get('subreddit', '')} u/{p.get('author', '')}",
                    engagement={"upvotes": p.get("score"), "comments": p.get("num_comments")}, raw_id=pid,
                    published_at=_iso(p.get("created_utc")), author_voice_status="unreviewed")
        out.append(_finish(rec, retrieved_at))
    return out


def comments_to_records(comments: list[dict], query: str, retrieved_at: str, build=None,
                        customer_segment: str = "", hypothesis: str = "") -> list[dict]:
    build = build or _builder()
    out = []
    for c in comments:
        cid = str(c.get("id") or "")
        text = str(c.get("body") or "").strip()
        post_id = str(c.get("link_id") or "").removeprefix("t3_")
        permalink = str(c.get("permalink") or "")
        if not cid or not post_id or text in {"", "[deleted]", "[removed]"} or not permalink:
            continue
        rec = build(source="reddit_comment", source_url="https://www.reddit.com" + permalink, query=query,
                    customer_segment=customer_segment, hypothesis=hypothesis, text=text,
                    author_context=f"r/{c.get('subreddit', '')} u/{c.get('author', '')} (comment on {post_id})",
                    engagement={"upvotes": c.get("score")}, raw_id=f"{post_id}/{cid}",
                    published_at=_iso(c.get("created_utc")), author_voice_status="unreviewed")
        _finish(rec, retrieved_at)
        rec["parent_source_record_id"] = post_id
        out.append(rec)
    return out
