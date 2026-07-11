#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "apify"


def main() -> int:
    key_name, token = get_secret("APIFY_TOKEN")
    if not token:
        return missing_credentials(
            PROVIDER,
            ["APIFY_TOKEN"],
            [
                "Create or log in at https://console.apify.com/",
                "Open Settings -> Integrations -> API token",
                "Set it with: export APIFY_TOKEN='your_token'",
                "Or add APIFY_TOKEN=your_token to ~/.secrets",
            ],
        )

    response = http_get(with_query("https://api.apify.com/v2/users/me", {"token": token}))
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "docs": "https://docs.apify.com/api/v2",
        "cost_note": "This validates account access only. Actor-specific cost/schema validation should be done after choosing actors.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
