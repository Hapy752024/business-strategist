#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, http_get, status_from_response, with_query


PROVIDER = "itunes_reviews"


def main() -> int:
    # 284882215 is a long-lived public app ID used only as a connectivity probe.
    app_id = cli_arg("app-id", "284882215")
    country = cli_arg("country", "us")
    url = with_query(
        f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json",
        {"page": 1},
    )
    response = http_get(url)
    body = response.get("body")
    entries = body.get("feed", {}).get("entry") if isinstance(body, dict) else None
    summary = {
        "status": status_from_response(response),
        "app_id": app_id,
        "country": country,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "review_count": len(entries) if isinstance(entries, list) else (1 if isinstance(entries, dict) else 0),
        "docs": "https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json",
        "cost_note": "Free public iTunes customer-review RSS. No key, no credits. Public reviews only; not for owned-app reply workflows.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
