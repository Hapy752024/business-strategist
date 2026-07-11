#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "meta"


def main() -> int:
    key_name, token = get_secret("META_ACCESS_TOKEN", "FACEBOOK_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")
    if not token:
        return missing_credentials(
            PROVIDER,
            ["META_ACCESS_TOKEN"],
            [
                "Create/select a Meta app at https://developers.facebook.com/apps/",
                "Use Graph API Explorer at https://developers.facebook.com/tools/explorer/ to generate a token with permitted page/Instagram scopes",
                "Set it with: export META_ACCESS_TOKEN='your_token'",
                "Or add META_ACCESS_TOKEN=your_token to ~/.secrets",
            ],
        )

    response = http_get(with_query("https://graph.facebook.com/v20.0/me", {"fields": "id,name", "access_token": token}))
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "docs": "https://developers.facebook.com/docs/graph-api/",
        "cost_note": "Official Meta APIs generally require permissions and only expose owned/permitted assets. Do not assume arbitrary public group/profile access.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
