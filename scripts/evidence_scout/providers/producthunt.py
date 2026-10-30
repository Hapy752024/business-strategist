"""Product Hunt API v2 (GraphQL, developer token). Posts and their comments.

The v2 ``posts`` connection has no free-text search argument, so a query is
resolved to topic slugs via ``topics(query:)`` and posts are read per topic.
Launch copy and comments by a post's makers are supplier context, never
customer voice. Rate limit: 6,250 complexity points per 15 minutes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_post, status_from_response  # noqa: E402

ENDPOINT = "https://api.producthunt.com/v2/api/graphql"
COMMENTS_PER_POST = 10
SAMPLING_NOTE = "Product Hunt posts via topic search, ordered by votes; launch audiences skew early-adopter and maker; not a representative sample."

TOPICS_QUERY = "query($q: String!, $n: Int!) { topics(query: $q, first: $n) { edges { node { slug name } } } }"
POSTS_QUERY = """query($topic: String!, $n: Int!, $c: Int!) {
  posts(topic: $topic, first: $n, order: VOTES) { edges { node {
    id name tagline description url votesCount commentsCount createdAt
    makers { id username }
    comments(first: $c, order: VOTES_COUNT) { edges { node {
      id body createdAt votesCount url user { id username isMaker } } } }
  } } }
}"""


def _header(response: dict, name: str) -> str | None:
    for key, value in (response.get("headers") or {}).items():
        if key.lower() == name:
            return str(value)
    return None


def graphql(token: str, query: str, variables: dict, timeout: int = 30) -> tuple[dict, dict]:
    """One GraphQL call. The token goes in the Authorization header only."""
    response = http_post(ENDPOINT, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                         data={"query": query, "variables": variables}, timeout=timeout, max_text_chars=2_000_000)
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    status = status_from_response(response)
    if status == "ok" and body.get("errors"):
        status = "failed"
    remaining = _header(response, "x-rate-limit-remaining")
    if status == "ok" and remaining is not None and remaining.isdigit() and int(remaining) <= 0:
        status = "rate_limited"
    return body, {"status": status, "response": response}


def _nodes(connection: Any) -> list[dict]:
    edges = connection.get("edges") if isinstance(connection, dict) else None
    return [e["node"] for e in edges or [] if isinstance(e, dict) and isinstance(e.get("node"), dict)]


def topic_slugs(body: dict) -> list[str]:
    return [str(n["slug"]) for n in _nodes((body.get("data") or {}).get("topics")) if n.get("slug")]


def _default_builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def to_records(body: dict, query: str, retrieved_at: str, build: Callable[..., dict[str, Any]] | None = None,
               customer_segment: str = "", hypothesis: str = "", sampling_frame: str = "topic_led_voc",
               subject_entity_id: str = "") -> list[dict]:
    build = build or _default_builder()
    frame = {"sampling_frame": sampling_frame, "subject_entity_id": subject_entity_id if sampling_frame == "entity_led_feedback" else ""}
    records: list[dict] = []

    def finish(rec: dict, parent: str | None = None) -> None:
        rec["retrieved_at"] = retrieved_at
        rec["collection_method"] = "official_api"
        rec["retrieval_backend"] = "producthunt"
        rec["sampling_metadata"]["subset_limitations"] = SAMPLING_NOTE
        if parent:
            rec["parent_source_record_id"] = parent
        records.append(rec)

    for post in _nodes((body.get("data") or {}).get("posts")):
        pid, url = str(post.get("id") or ""), post.get("url") or ""
        launch = "\n\n".join(p for p in [str(post.get("name") or "").strip(), str(post.get("tagline") or "").strip(),
                                         str(post.get("description") or "").strip()] if p)
        if not pid or not url or not launch:
            continue
        maker_ids = {str(m.get("id")) for m in post.get("makers") or [] if isinstance(m, dict) and m.get("id")}
        finish(build(source="producthunt", source_url=url, query=query, customer_segment=customer_segment,
                     hypothesis=hypothesis, text=launch, author_context="Product Hunt launch copy written by the post's makers",
                     engagement={"upvotes": post.get("votesCount"), "comments": post.get("commentsCount")},
                     raw_id=pid, published_at=(post.get("createdAt") or "")[:10] or None,
                     source_role_override="competitor_context", source_intent_override="competitor_content",
                     author_voice_status="supplier_context", **frame))
        for comment in _nodes(post.get("comments")):
            cid, body_text = str(comment.get("id") or ""), str(comment.get("body") or "").strip()
            if not cid or not body_text:
                continue
            user = comment.get("user") if isinstance(comment.get("user"), dict) else {}
            supplier = bool(user.get("isMaker")) or str(user.get("id") or "") in maker_ids
            extra = {"source_role_override": "competitor_context", "source_intent_override": "competitor_content",
                     "author_voice_status": "supplier_context"} if supplier else {
                     "source_role_override": "community_context", "author_voice_status": "unreviewed"}
            finish(build(source="producthunt_comment", source_url=comment.get("url") or url, query=query,
                         customer_segment=customer_segment, hypothesis=hypothesis, text=body_text,
                         author_context=("Product Hunt comment by a maker (supplier)" if supplier else "Product Hunt comment")
                         + f" on post {pid}",
                         engagement={"upvotes": comment.get("votesCount")}, raw_id=f"{pid}/{cid}",
                         published_at=(comment.get("createdAt") or "")[:10] or None, **extra, **frame), parent=pid)
    return records
