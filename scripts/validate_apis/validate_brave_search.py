#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "brave_search"


def main() -> int:
    key_name, api_key = get_secret("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["BRAVE_SEARCH_API_KEY"],
            [
                "Create or log in at https://api.search.brave.com/app/keys",
                "Create/copy a Brave Search API key",
                "Set it with: export BRAVE_SEARCH_API_KEY='your_key'",
                "Or add BRAVE_SEARCH_API_KEY=your_key to ~/.secrets",
            ],
        )

    query = cli_arg("query", '"project management" "I hate" OR "frustrated" forum')
    response = http_get(
        with_query(
            "https://api.search.brave.com/res/v1/web/search",
            {
                "q": query,
                "count": 5,
                "country": "US",
                "search_lang": "en",
            },
        ),
        headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
    )
    body = response.get("body")
    web = body.get("web", {}) if isinstance(body, dict) else {}
    results = web.get("results", []) if isinstance(web, dict) else []
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "query": query,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "result_count": len(results),
        "docs": "https://api-dashboard.search.brave.com/app/documentation/web-search/get-started",
        "cost_note": "Useful low-friction fallback for forum/source discovery when Firecrawl search is unavailable.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
