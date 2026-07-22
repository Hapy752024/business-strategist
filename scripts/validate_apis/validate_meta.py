#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "meta"

SETUP_INSTRUCTIONS = [
    "Create/select a Meta app at https://developers.facebook.com/apps/",
    "Complete Meta identity verification (required for Ad Library API access)",
    "Use Graph API Explorer at https://developers.facebook.com/tools/explorer/ to generate a token with ads_read scope",
    "Set it with: export META_ACCESS_TOKEN='your_token'",
    "Or add META_ACCESS_TOKEN=your_token to ~/.secrets",
    "Note: tokens expire after ~60 days. Regenerate before runs when validate_meta reports token_expired.",
]


def main() -> int:
    key_name, token = get_secret("META_ACCESS_TOKEN", "FACEBOOK_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")
    if not token:
        return missing_credentials(PROVIDER, ["META_ACCESS_TOKEN"], SETUP_INSTRUCTIONS)

    me_response = http_get(with_query("https://graph.facebook.com/v20.0/me", {"fields": "id,name", "access_token": token}))
    me_body = me_response.get("body") or {}
    me_error = me_body.get("error") if isinstance(me_body, dict) else None

    # Probe Ad Library API access (ads_read scope) with a minimal archived-ads query.
    ads_response = http_get(
        with_query(
            "https://graph.facebook.com/v20.0/ads_archive",
            {
                "ad_reached_countries": "['DE']",
                "ad_active_status": "ALL",
                "ad_type": "ALL",
                "search_terms": "versicherung",
                "fields": "id,page_name",
                "limit": 1,
                "access_token": token,
            },
        )
    )
    ads_body = ads_response.get("body") or {}
    ads_error = ads_body.get("error") if isinstance(ads_body, dict) else None

    if me_error and (me_error.get("code") == 190 or "expired" in (me_error.get("message") or "").lower()):
        me_status = "token_expired"
    else:
        me_status = status_from_response(me_response)

    if ads_error:
        code = ads_error.get("code")
        message = (ads_error.get("message") or "").lower()
        if code == 190 or "expired" in message:
            ads_status = "token_expired"
        elif code in {10, 200, 294} or "permission" in message or "ads_read" in message:
            ads_status = "scope_denied"
        else:
            ads_status = f"error:{code}"
    elif ads_response.get("ok"):
        ads_status = "ok"
    else:
        ads_status = status_from_response(ads_response)

    overall = "ok" if me_status == "ok" and ads_status == "ok" else (ads_status if ads_status != "ok" else me_status)
    summary = {
        "status": overall,
        "credential_source": key_name,
        "http_status": me_response.get("status_code"),
        "fields": fields_present(me_body),
        "me_status": me_status,
        "ads_archive_status": ads_status,
        "docs": "https://developers.facebook.com/docs/marketing-api/reference/ads_archive/",
        "cost_note": "Official Meta APIs are free but require identity verification and only expose permitted assets. Ad Library commercial coverage is EU/UK/EEA-only; tokens expire after ~60 days.",
        "setup_instructions": SETUP_INSTRUCTIONS if overall != "ok" else [],
    }
    return finish(PROVIDER, summary, me_response)


if __name__ == "__main__":
    raise SystemExit(main())
