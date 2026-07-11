#!/usr/bin/env python3
from __future__ import annotations

import urllib.parse

from common import fields_present, finish, get_secret, http_post, missing_credentials, status_from_response


PROVIDER = "tiktok"


def main() -> int:
    key_name, client_key = get_secret("TIKTOK_CLIENT_KEY")
    secret_name, client_secret = get_secret("TIKTOK_CLIENT_SECRET")
    if not client_key or not client_secret:
        return missing_credentials(
            PROVIDER,
            ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
            [
                "Start at https://developers.tiktok.com/products/research-api/",
                "Apply for Research API access if eligible",
                "Copy client key and client secret from your approved app",
                "Set: export TIKTOK_CLIENT_KEY='...' TIKTOK_CLIENT_SECRET='...'",
                "Or add both keys to ~/.secrets",
                "If not eligible, validate APIFY_TOKEN or BRIGHTDATA_API_KEY as fallback providers.",
            ],
        )

    response = http_post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=urllib.parse.urlencode(
            {
                "client_key": client_key,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            }
        ),
    )
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": [key_name, secret_name],
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "docs": "https://developers.tiktok.com/doc/research-api-get-started",
        "cost_note": "Official TikTok Research API access is eligibility-gated and may be incomplete for general market research.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
