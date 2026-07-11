#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_post, missing_credentials, status_from_response


PROVIDER = "serper"


def main() -> int:
    key_name, api_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["SERPER_DEV_API_KEY"],
            [
                "Create or log in at https://serper.dev/",
                "Copy your API key",
                "Set it with: export SERPER_DEV_API_KEY='your_key'",
                "Or add SERPER_DEV_API_KEY=your_key to ~/.secrets",
            ],
        )

    response = http_post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        data={"q": "Serper smoke test", "num": 1, "gl": "us", "hl": "en"},
    )
    body = response.get("body")
    organic = body.get("organic", []) if isinstance(body, dict) else []
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "result_count": len(organic),
        "docs": "https://serper.dev/",
        "cost_note": "Cheap/default Google-only SERP route. Use SerpApi/DataForSEO only for non-Google engines, edge-case parsers, Trends, or SEO-depth datasets.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
