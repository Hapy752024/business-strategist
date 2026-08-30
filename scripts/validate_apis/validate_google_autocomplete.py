#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, http_get, status_from_response, with_query


PROVIDER = "google_autocomplete"


def main() -> int:
    query = cli_arg("query", "why is my accountant so slow")
    language = cli_arg("language", "en")
    country = cli_arg("country", "us")
    url = with_query(
        "https://suggestqueries.google.com/complete/search",
        {"client": "firefox", "hl": language, "gl": country, "q": query},
    )
    response = http_get(url)
    body = response.get("body")
    suggestions = body[1] if isinstance(body, list) and len(body) > 1 else None
    summary = {
        "status": status_from_response(response),
        "query": query,
        "language": language,
        "country": country,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "suggestion_count": len(suggestions) if isinstance(suggestions, list) else 0,
        "docs": "https://suggestqueries.google.com/complete/search?client=firefox&q=...",
        "cost_note": "Free public autocomplete endpoint. No key. Unofficial; treat as demand-language proxy only.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
