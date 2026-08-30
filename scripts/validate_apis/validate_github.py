#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_get, status_from_response, with_query


PROVIDER = "github"


def main() -> int:
    key_name, token = get_secret("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT")
    query = cli_arg("query", "spreadsheet reporting workaround")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = with_query(
        "https://api.github.com/search/issues",
        {"q": f"{query} type:issue", "sort": "reactions", "per_page": 3},
    )
    response = http_get(url, headers=headers)
    body = response.get("body")
    items = body.get("items") if isinstance(body, dict) else None
    remaining = {k: v for k, v in response.get("headers", {}).items() if "rate" in k.lower()}
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "query": query,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "item_count": len(items) if isinstance(items, list) else 0,
        "rate_limit_headers": remaining,
        "docs": "https://docs.github.com/rest/search/search-issues",
        "cost_note": "Free. Anonymous: ~10 search requests/min; with GITHUB_TOKEN: ~30/min.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
