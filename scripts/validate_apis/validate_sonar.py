#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "sonar"


def main() -> int:
    key_name, api_key = get_secret("SONAR_API_KEY")
    if not api_key:
        return missing_credentials(
            PROVIDER,
            ["SONAR_API_KEY"],
            [
                "Create an API key in the Sonar dashboard at https://trysonar.app/developers",
                "Set it with: export SONAR_API_KEY='aso_...'",
                "Or add SONAR_API_KEY=aso_... to ~/.secrets",
            ],
        )

    response = http_get(
        with_query(
            "https://trysonar.app/api/v1/keywords/suggestions",
            {"q": "habit tracker", "store": "ios", "country": "us"},
        ),
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(response.get("body")),
        "docs": "https://trysonar.app/docs/api",
        "cost_note": "Validation uses Sonar keyword suggestions, listed as a 1-credit endpoint. Use app reviews/revenue only after the target app IDs are known.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
