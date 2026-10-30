#!/usr/bin/env python3
"""Smallest live check of ScrapeCreators Reddit search (one request, one credit)."""
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query

PROVIDER = "scrapecreators_reddit"
ENDPOINT = "https://api.scrapecreators.com/v1/reddit/search"


def main() -> int:
    key_name, api_key = get_secret("SCRAPE_CREATORS_API_KEY", "SCRAPECREATORS_API_KEY")
    if not api_key:
        return missing_credentials(PROVIDER, ["SCRAPE_CREATORS_API_KEY"], [
            "Create or log in at https://app.scrapecreators.com/",
            "Copy your API key",
            "Set it with: export SCRAPE_CREATORS_API_KEY='your_key'",
            "Or add SCRAPE_CREATORS_API_KEY=your_key to ~/.secrets",
        ])
    response = http_get(with_query(ENDPOINT, {"query": "invoice", "filter": "posts", "timeframe": "week", "trim": "true"}),
                        headers={"x-api-key": api_key})
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    status = status_from_response(response)
    if status == "ok" and not body.get("posts"):
        status = "failed"
    summary = {"status": status, "credential_source": key_name, "http_status": response.get("status_code"),
               "fields": fields_present(body), "docs": "https://docs.scrapecreators.com/v1/reddit/search",
               "cost_note": "1 credit. Third-party API; fallback only."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
