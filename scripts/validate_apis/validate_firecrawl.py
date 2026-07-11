#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_post, missing_credentials, status_from_response


PROVIDER = "firecrawl"


def main() -> int:
    key_name, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["FIRECRAWL_API_KEY_HGINVESTOR"],
            [
                "Create or log in at https://www.firecrawl.dev/app/api-keys",
                "Create/copy an API key",
                "Set it with: export FIRECRAWL_API_KEY_HGINVESTOR='your_key'",
                "Or add FIRECRAWL_API_KEY_HGINVESTOR=your_key to ~/.secrets",
                "This project always uses the HGINVESTOR Firecrawl account.",
            ],
        )

    query = cli_arg("query", "project management forum pain points")
    response = http_post(
        "https://api.firecrawl.dev/v1/search",
        headers={"Authorization": f"Bearer {api_key}"},
        data={"query": query, "limit": 3, "scrapeOptions": {"formats": ["markdown"]}},
    )
    body = response.get("body")
    data = body.get("data") if isinstance(body, dict) else None
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "query": query,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "result_count": len(data) if isinstance(data, list) else 0,
        "docs": "https://docs.firecrawl.dev/api-reference/introduction",
        "cost_note": "Search and scrape requests consume Firecrawl credits. This validation uses a low limit.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
