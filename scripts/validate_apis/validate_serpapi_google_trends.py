#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "serpapi_google_trends"


def main() -> int:
    key_name, api_key = get_secret("SERPAPI_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["SERPAPI_API_KEY"],
            [
                "Create or log in at https://serpapi.com/users/sign_up",
                "Copy your private API key from https://serpapi.com/manage-api-key",
                "Set it with: export SERPAPI_API_KEY='your_key'",
                "Or add SERPAPI_API_KEY=your_key to ~/.secrets",
            ],
        )

    query = cli_arg("query", "project management,task management,notion")
    url = with_query(
        "https://serpapi.com/search.json",
        {
            "engine": "google_trends",
            "q": query,
            "data_type": "TIMESERIES",
            "date": "today 12-m",
            "geo": "US",
            "api_key": api_key,
        },
    )
    response = http_get(url)
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "query": query,
        "http_status": response.get("status_code"),
        "quota_headers": {k: v for k, v in response.get("headers", {}).items() if "limit" in k.lower() or "remaining" in k.lower()},
        "fields": fields_present(body),
        "has_interest_over_time": isinstance(body, dict) and bool(body.get("interest_over_time")),
        "docs": "https://serpapi.com/google-trends-api",
        "cost_note": "Costs one SerpAPI search credit per request on most plans.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
