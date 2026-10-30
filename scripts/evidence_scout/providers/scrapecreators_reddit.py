"""ScrapeCreators Reddit lane (third-party paid API over public Reddit pages).

Fallback only: Reddit's public Data API closes in 2027. Terms-of-service risk sits
with the vendor. This module is the single home of ScrapeCreators Reddit HTTP calls.
Docs: https://docs.scrapecreators.com/v1/reddit/search and .../v1/reddit/post/comments.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_get, status_from_response, with_query  # noqa: E402

BASE = "https://api.scrapecreators.com/v1/reddit"
SCRAPE_NOTE = "scrapecreators_reddit (third-party API) over public Reddit pages; relevance-ranked, completeness unknown, not a representative sample."
COLLECTION_METHOD = "third_party_api"
BACKEND = "scrapecreators_reddit"


def search(api_key: str, query: str, sort: str = "relevance", timeframe: str = "all",
           after: str | None = None) -> tuple[list[dict], dict]:
    """GET /v1/reddit/search (posts). The key goes in the x-api-key header only."""
    response = http_get(with_query(f"{BASE}/search", {"query": query, "filter": "posts", "sort": sort,
                                                      "timeframe": timeframe, "trim": "true", "after": after}),
                        headers={"x-api-key": api_key})
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    posts = [p for p in body.get("posts") or [] if isinstance(p, dict)]
    return posts, {"status": status_from_response(response), "response": response, "after": body.get("after")}


def fetch_thread(api_key: str, post_url: str) -> tuple[dict | None, dict]:
    """GET /v1/reddit/post/comments for one exact post URL."""
    response = http_get(with_query(f"{BASE}/post/comments", {"url": post_url, "trim": "true"}),
                        headers={"x-api-key": api_key})
    body = response.get("body") if isinstance(response.get("body"), dict) else None
    return (body if response.get("ok") else None), {"status": status_from_response(response), "response": response}


def window_for_days(days: int) -> str:
    for name, limit in (("day", 1), ("week", 7), ("month", 31), ("year", 366)):
        if days <= limit:
            return name
    return "all"


def _builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def _iso(item: dict) -> str | None:
    if item.get("created_at_iso"):
        return str(item["created_at_iso"])
    try:
        return datetime.fromtimestamp(float(item["created_utc"]), timezone.utc).isoformat()
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def _abs(url: str) -> str:
    return "https://www.reddit.com" + url if url.startswith("/") else url


def _finish(rec: dict, retrieved_at: str, note: str = SCRAPE_NOTE) -> dict:
    rec["retrieved_at"] = retrieved_at
    rec["collection_method"] = COLLECTION_METHOD
    rec["retrieval_backend"] = BACKEND
    rec["sampling_metadata"]["subset_limitations"] = note
    return rec


def _post_record(post: dict, query: str, retrieved_at: str, build, customer_segment: str, hypothesis: str) -> dict | None:
    post_id = str(post.get("id") or "")
    url = _abs(str(post.get("url") or post.get("permalink") or ""))
    permalink = _abs(str(post.get("permalink") or ""))
    if permalink and "/comments/" in permalink:
        url = permalink
    title = str(post.get("title") or "").strip()
    text = "\n\n".join(p for p in [title, str(post.get("selftext") or "").strip()] if p)
    if not post_id or not url or not text:
        return None
    rec = build(source="reddit", source_url=url, query=query, customer_segment=customer_segment,
                hypothesis=hypothesis, text=text,
                author_context=f"r/{post.get('subreddit', '')} u/{post.get('author', '')}",
                engagement={"upvotes": post.get("ups", post.get("score")), "comments": post.get("num_comments")},
                raw_id=post_id, published_at=_iso(post), author_voice_status="unreviewed")
    return _finish(rec, retrieved_at)


def search_to_records(posts: list[dict], query: str, retrieved_at: str, build=None,
                      customer_segment: str = "", hypothesis: str = "") -> list[dict]:
    build = build or _builder()
    out = [_post_record(p, query, retrieved_at, build, customer_segment, hypothesis) for p in posts]
    return [r for r in out if r]


def _flatten(comments: list, depth_guard: int = 0) -> list[dict]:
    out: list[dict] = []
    for c in comments or []:
        if not isinstance(c, dict):
            continue
        out.append(c)
        replies = c.get("replies")
        nested = replies.get("items") if isinstance(replies, dict) else replies if isinstance(replies, list) else []
        if nested and depth_guard < 20:
            out.extend(_flatten(nested, depth_guard + 1))
    return out


def thread_to_records(body: dict, query: str, retrieved_at: str, build=None, customer_segment: str = "",
                      hypothesis: str = "", max_comments: int = 100, post_url: str = "") -> list[dict]:
    """The post (when the response carries one) plus its comments, nested replies flattened."""
    build = build or _builder()
    post = body.get("post") if isinstance(body.get("post"), dict) else {}
    records: list[dict] = []
    post_id = str(post.get("id") or "")
    community = str(post.get("subreddit") or "")
    thread_url = _abs(str(post.get("permalink") or post.get("url") or post_url))
    if post:
        rec = _post_record(post, query, retrieved_at, build, customer_segment, hypothesis)
        if rec:
            records.append(rec)
    for c in _flatten(body.get("comments") or [])[:max(1, max_comments)]:
        cid = str(c.get("id") or "")
        text = str(c.get("body") or "").strip()
        if not cid or text in {"", "[deleted]", "[removed]"}:
            continue
        url = _abs(str(c.get("url") or c.get("permalink") or "")) or thread_url.rstrip("/") + "/" + cid
        rec = build(source="reddit_comment", source_url=url, query=query, customer_segment=customer_segment,
                    hypothesis=hypothesis, text=text,
                    author_context=f"r/{c.get('subreddit', community)} u/{c.get('author', '')} (comment on {post_id})",
                    engagement={"upvotes": c.get("ups", c.get("score"))}, raw_id=f"{post_id}/{cid}",
                    published_at=_iso(c), author_voice_status="unreviewed")
        _finish(rec, retrieved_at)
        if post_id:
            rec["parent_source_record_id"] = post_id
        rec["sampling_metadata"].update({"parent_comment_id": c.get("parent_id"), "thread_url": thread_url})
        records.append(rec)
    return records
