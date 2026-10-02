#!/usr/bin/env python3
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, status_from_response


PROVIDER = "parsersvc"
PRICING_URL = "https://vcapi.parsers.vc/v2/pricing"


def main() -> int:
    _name, key = get_secret("PARSERSVC_API_KEY")
    if not key:
        from common import missing_credentials
        return missing_credentials(PROVIDER, ["PARSERSVC_API_KEY"], [
            "Set PARSERSVC_API_KEY in the environment, project .secrets, or ~/.secrets."
        ])
    response = http_get(PRICING_URL, headers={"X-Api-Key": key}, timeout=20)
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "probe": "Authenticated GET /v2/pricing; provider documents this endpoint as zero-credit.",
        "docs": "https://parsers.vc/api_page/reference/",
        "required_env": ["PARSERSVC_API_KEY"],
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
