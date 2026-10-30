"""Apify-backed Reddit fallback (third-party scraper of public pages).

Fallback only: Reddit's public Data API closes in 2027. ToS risk sits with the
actor and availability can break without notice.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_post, status_from_response  # noqa: E402

ACTOR = "practicaltools~apify-reddit-api"
ENDPOINT = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items"
SCRAPE_NOTE = "apify_reddit (third-party scrape) of public Reddit pages; relevance-ranked, completeness unknown, not a representative sample."
# The actor exposes no per-post comment limit, so budget conservatively per post.
ITEMS_PER_POST = 10
TIME_WINDOWS = (("day", 1), ("week", 7), ("month", 31), ("year", 366))


def time_window_for_days(days: int) -> str:
    for name, limit in TIME_WINDOWS:
        if days <= limit:
            return name
    return "all"


def run_actor(token: str, searches: list[str], max_items: int, time_window: str,
              fetch_comments: bool, timeout_s: int = 150, start_urls: list[str] | None = None) -> tuple[list[dict], dict]:
    """Run the actor synchronously. The token goes in the Authorization header only.

    ``start_urls`` fetches exact post URLs (the post and its comments) instead of searching.
    """
    if start_urls:
        payload: dict[str, Any] = {"startUrls": [{"url": u} for u in start_urls], "maxItems": max_items,
                                   "skipComments": not fetch_comments, "skipCommunity": True, "skipUserPosts": True}
    else:
        payload = {"searches": searches, "searchPosts": True, "searchComments": False,
                   "fetchPostComments": fetch_comments, "maxItems": max_items,
                   "sort": "relevance", "time": time_window}
    response = http_post(
        f"{ENDPOINT}?timeout={timeout_s}&memory=512",
        headers={"Authorization": f"Bearer {token}"},
        data=payload,
        timeout=timeout_s + 30,
        max_text_chars=2_000_000,
    )
    body = response.get("body")
    items = [item for item in body if isinstance(item, dict)] if isinstance(body, list) else []
    status = status_from_response(response)
    return items, {"status": status, "http_status": response.get("status_code"), "response": response}


def _default_builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def to_records(items: list[dict], query: str, retrieved_at: str,
               build: Callable[..., dict[str, Any]] | None = None,
               customer_segment: str = "", hypothesis: str = "") -> list[dict]:
    """Posts become source=reddit records; each comment is its own reddit_comment record.

    capture_unit stays the schema value ``source_record`` for both; the comment
    link is carried in source_record_id (<post>/<comment>) and parent_source_record_id.
    """
    build = build or _default_builder()
    records: list[dict] = []
    for item in items:
        if item.get("dataType") not in (None, "post"):
            continue
        post_id = str(item.get("parsedId") or item.get("id") or "")
        url = item.get("url") or ""
        title = str(item.get("title") or "").strip()
        text = "\n\n".join(p for p in [title, str(item.get("body") or "").strip()] if p)
        if not post_id or not url or not text:
            continue
        community = str(item.get("parsedCommunityName") or item.get("communityName") or "")
        post = build(source="reddit", source_url=url, query=query, customer_segment=customer_segment,
                     hypothesis=hypothesis, text=text,
                     author_context=f"r/{community.removeprefix('r/')} u/{item.get('username', '')}",
                     engagement={"upvotes": item.get("upVotes"), "comments": item.get("numberOfComments")},
                     raw_id=post_id, published_at=item.get("createdAt") or None,
                     author_voice_status="unreviewed")
        post["retrieved_at"] = retrieved_at
        post["sampling_metadata"].update({"sort_requested": "relevance", "subset_limitations": SCRAPE_NOTE})
        post["collection_method"] = "third_party_scrape"
        post["retrieval_backend"] = "apify_reddit"
        records.append(post)
        for comment in item.get("comments") or []:
            if not isinstance(comment, dict):
                continue
            comment_id = str(comment.get("parsedId") or comment.get("id") or "")
            body = str(comment.get("body") or "").strip()
            curl = comment.get("url") or ""
            if not comment_id or not body or not curl:
                continue
            rec = build(source="reddit_comment", source_url=curl, query=query,
                        customer_segment=customer_segment, hypothesis=hypothesis, text=body,
                        author_context=f"r/{community.removeprefix('r/')} u/{comment.get('username', '')} (comment on {post_id})",
                        engagement={"upvotes": comment.get("upVotes")},
                        raw_id=f"{post_id}/{comment_id}", published_at=comment.get("createdAt") or None,
                        author_voice_status="unreviewed")
            rec["retrieved_at"] = retrieved_at
            rec["collection_method"] = "third_party_scrape"
            rec["retrieval_backend"] = "apify_reddit"
            rec["sampling_metadata"]["subset_limitations"] = SCRAPE_NOTE
            rec["parent_source_record_id"] = post_id
            records.append(rec)
    return records
