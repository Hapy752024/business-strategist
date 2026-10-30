"""Reddit discovery-then-hydrate helpers.

Discover threads cheaply with web search (Brave/Serper ``site:reddit.com``), then fetch only
the threads that matter. This module extracts thread references from saved search output and
converts Reddit Data API thread listings into evidence records; backend order and spend
control live in ``collect.collect_reddit_hydrate``.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

REDDIT_HOSTS = {"reddit.com", "www.reddit.com", "old.reddit.com", "np.reddit.com", "new.reddit.com", "m.reddit.com"}
THREAD_PATH = re.compile(r"^/r/([A-Za-z0-9_]+)/comments/([a-z0-9]+)(?:/([^/?#]*))?", re.I)
URL_IN_TEXT = re.compile(r"https?://[^\s\"'<>)\]]+")


def _strings(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)
    elif isinstance(node, str):
        yield node


def _load(path: Path) -> list[Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        return [json.loads(text)]
    except ValueError:
        out = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
        return out


def thread_ref(url: str) -> dict[str, str] | None:
    """Canonical thread reference for a Reddit post URL; subreddit, user and other pages return None."""
    parsed = urllib.parse.urlparse(url.strip())
    if (parsed.hostname or "").lower() not in REDDIT_HOSTS:
        return None
    match = THREAD_PATH.match(parsed.path)
    if not match:
        return None
    sub, post_id, slug = match.group(1), match.group(2).lower(), match.group(3) or "_"
    return {"post_id": post_id, "subreddit": sub,
            "url": f"https://www.reddit.com/r/{sub}/comments/{post_id}/{slug}/"}


def extract_thread_refs(path: Path) -> list[dict[str, str]]:
    """Thread references from a JSON/JSONL of web-search output, deduped by post id, first-seen order."""
    seen: dict[str, dict[str, str]] = {}
    for document in _load(path):
        for value in _strings(document):
            for candidate in ([value] if value.startswith("http") and " " not in value.strip() else URL_IN_TEXT.findall(value)):
                ref = thread_ref(candidate)
                if ref and ref["post_id"] not in seen:
                    seen[ref["post_id"]] = ref
    return list(seen.values())


def _iso(created_utc: Any) -> str | None:
    try:
        return datetime.fromtimestamp(float(created_utc), timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def api_listing_to_records(listing: Any, ref: dict[str, str], query: str, retrieved_at: str,
                           build: Callable[..., dict[str, Any]], customer_segment: str = "",
                           hypothesis: str = "", max_comments: int = 100) -> list[dict]:
    """Reddit Data API ``/comments/<id>`` listing -> post record plus comment records."""
    if not isinstance(listing, list) or len(listing) < 2:
        return []
    post = (((listing[0].get("data") or {}).get("children") or [{}])[0]).get("data") or {}
    comments: list[dict] = []

    def walk(children: list) -> None:
        for child in children:
            if child.get("kind") == "t1":
                data = child.get("data") or {}
                comments.append(data)
                replies = data.get("replies")
                if isinstance(replies, dict):
                    walk((replies.get("data") or {}).get("children") or [])
    walk((listing[1].get("data") or {}).get("children") or [])
    records: list[dict] = []
    text = "\n\n".join(p for p in [str(post.get("title") or "").strip(), str(post.get("selftext") or "").strip()] if p)
    if text:
        rec = build(source="reddit", source_url=ref["url"], query=query, customer_segment=customer_segment,
                    hypothesis=hypothesis, text=text,
                    author_context=f"r/{post.get('subreddit', ref['subreddit'])} u/{post.get('author', '')}",
                    engagement={"upvotes": post.get("ups"), "comments": post.get("num_comments")},
                    raw_id=ref["post_id"], published_at=_iso(post.get("created_utc")), author_voice_status="unreviewed")
        rec["retrieved_at"] = retrieved_at
        records.append(rec)
    for data in comments[:max(1, max_comments)]:
        cid, body = str(data.get("id") or ""), str(data.get("body") or "").strip()
        if not cid or body in {"", "[deleted]", "[removed]"}:
            continue
        link = str(data.get("permalink") or "")
        url = "https://www.reddit.com" + link if link.startswith("/") else ref["url"].rstrip("/") + "/" + cid
        rec = build(source="reddit_comment", source_url=url, query=query, customer_segment=customer_segment,
                    hypothesis=hypothesis, text=body,
                    author_context=f"r/{ref['subreddit']} u/{data.get('author', '')} (comment on {ref['post_id']})",
                    engagement={"upvotes": data.get("ups")}, raw_id=f"{ref['post_id']}/{cid}",
                    published_at=_iso(data.get("created_utc")), author_voice_status="unreviewed")
        rec["retrieved_at"] = retrieved_at
        rec["parent_source_record_id"] = ref["post_id"]
        records.append(rec)
    return records


def apify_items_with_comments(items: list[dict]) -> list[dict]:
    """A single-URL Apify run: attach separate comment items to the requested post item."""
    posts = [i for i in items if i.get("dataType") in (None, "post")]
    comments = [i for i in items if i.get("dataType") == "comment"]
    if posts and comments:
        posts[0] = {**posts[0], "comments": [*(posts[0].get("comments") or []), *comments]}
    return posts
