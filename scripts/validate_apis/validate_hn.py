#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, http_get, status_from_response, with_query


PROVIDER = "hn"


def main() -> int:
    query = cli_arg("query", "project management pain")
    url = with_query(
        "https://hn.algolia.com/api/v1/search",
        {"query": query, "tags": "story", "hitsPerPage": 3},
    )
    response = http_get(url)
    body = response.get("body")
    hits = body.get("hits") if isinstance(body, dict) else None
    summary = {
        "status": status_from_response(response),
        "query": query,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "hit_count": len(hits) if isinstance(hits, list) else 0,
        "docs": "https://hn.algolia.com/api",
        "cost_note": "Free public Algolia HN API. No key, no credits. Rate limits are generous but anonymous.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
