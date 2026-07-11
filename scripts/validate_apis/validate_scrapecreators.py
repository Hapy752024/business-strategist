#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response


PROVIDER = "scrapecreators"


def main() -> int:
    key_name, api_key = get_secret("SCRAPE_CREATORS_API_KEY", "SCRAPECREATORS_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["SCRAPE_CREATORS_API_KEY"],
            [
                "Create or log in at https://app.scrapecreators.com/",
                "Copy your API key from the dashboard",
                "Set it with: export SCRAPE_CREATORS_API_KEY='your_key'",
                "Or add SCRAPE_CREATORS_API_KEY=your_key to ~/.secrets",
            ],
        )

    response = http_get(
        "https://api.scrapecreators.com/v1/credit-balance",
        headers={"x-api-key": api_key},
    )
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "docs": "https://docs.scrapecreators.com/",
        "coverage_note": "Covers public social data across TikTok, Instagram, YouTube, Facebook, X/Twitter, Reddit, Threads, LinkedIn, Pinterest, Bluesky, and more.",
        "cost_note": "ScrapeCreators is credit based. The site states 100 free credits, pay-as-you-go top-ups, and most endpoints use 1 request = 1 credit.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
