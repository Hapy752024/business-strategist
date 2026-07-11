#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_post, missing_credentials, status_from_response


PROVIDER = "dataforseo_google_trends"


def main() -> int:
    login_name, login = get_secret("DATAFORSEO_LOGIN")
    password_name, password = get_secret("DATAFORSEO_PASSWORD")
    if not login or not password:
        return missing_credentials(
            PROVIDER,
            ["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"],
            [
                "Create or log in at https://app.dataforseo.com/register",
                "Copy API login/password from https://app.dataforseo.com/api-dashboard",
                "Set them with: export DATAFORSEO_LOGIN='...' DATAFORSEO_PASSWORD='...'",
                "Or add both keys to ~/.secrets",
            ],
        )

    query = cli_arg("query", "project management,task management,notion")
    keywords = [part.strip() for part in query.split(",") if part.strip()][:5]
    payload = [
        {
            "keywords": keywords,
            "location_name": "United States",
            "language_name": "English",
            "date_from": "2025-06-01",
            "date_to": "2026-06-01",
            "type": "web",
        }
    ]
    response = http_post(
        "https://api.dataforseo.com/v3/keywords_data/google_trends/explore/live",
        data=payload,
        basic_auth=(login, password),
    )
    body = response.get("body")
    provider_status_code = body.get("status_code") if isinstance(body, dict) else None
    provider_status_message = body.get("status_message") if isinstance(body, dict) else None
    summary = {
        "status": status_from_response(response),
        "credential_source": [login_name, password_name],
        "query": query,
        "http_status": response.get("status_code"),
        "provider_status_code": provider_status_code,
        "provider_status_message": provider_status_message,
        "fields": fields_present(body),
        "has_tasks": isinstance(body, dict) and bool(body.get("tasks")),
        "docs": "https://docs.dataforseo.com/v3/keywords_data/google_trends/overview/",
        "cost_note": "DataForSEO bills per API task. Check account pricing before running broad research.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
