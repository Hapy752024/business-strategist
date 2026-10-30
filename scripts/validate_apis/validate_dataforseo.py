#!/usr/bin/env python3
"""Free auth and balance check for DataForSEO keyword volumes (appendix/user_data; no task is billed)."""
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, missing_credentials, status_from_response

PROVIDER = "dataforseo"


def main() -> int:
    login_name, login = get_secret("DATAFORSEO_LOGIN", "DATAFORSEO_USERNAME")
    password_name, password = get_secret("DATAFORSEO_PASSWORD")
    if not login or not password:
        return missing_credentials(
            PROVIDER,
            ["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"],
            [
                "Copy API login/password from https://app.dataforseo.com/api-access",
                "Set them with: export DATAFORSEO_LOGIN='...' DATAFORSEO_PASSWORD='...'",
                "Or add both keys to ~/.secrets",
            ],
        )
    response = http_get("https://api.dataforseo.com/v3/appendix/user_data", basic_auth=(login, password))
    body = response.get("body")
    task = (body.get("tasks") or [{}])[0] if isinstance(body, dict) else {}
    result = (task.get("result") or [{}])[0] if isinstance(task, dict) else {}
    money = result.get("money") if isinstance(result, dict) else None
    summary = {
        "status": status_from_response(response),
        "credential_source": [login_name, password_name],
        "http_status": response.get("status_code"),
        "provider_status_code": body.get("status_code") if isinstance(body, dict) else None,
        "balance_usd": money.get("balance") if isinstance(money, dict) else None,
        "fields": fields_present(body),
        "docs": "https://docs.dataforseo.com/v3/appendix/user_data/",
        "cost_note": "This endpoint is free. Keyword volumes bill per task (up to 1000 keywords); see scripts/marketing/keyword_volume.py.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
