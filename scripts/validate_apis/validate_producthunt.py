#!/usr/bin/env python3
"""Smallest live check of the Product Hunt GraphQL API (one cheap topics query)."""
from __future__ import annotations

from common import fields_present, finish, get_secret, http_post, missing_credentials, status_from_response

PROVIDER = "producthunt"
ENDPOINT = "https://api.producthunt.com/v2/api/graphql"


def main() -> int:
    key_name, token = get_secret("PRODUCTHUNT_TOKEN")
    if not token:
        return missing_credentials(PROVIDER, ["PRODUCTHUNT_TOKEN"], [
            "Sign in at https://www.producthunt.com/ and open https://www.producthunt.com/v2/oauth/applications",
            "Create an application, then generate a Developer Token",
            "Set it with: export PRODUCTHUNT_TOKEN='your_developer_token'",
            "Or add PRODUCTHUNT_TOKEN=your_developer_token to ~/.secrets",
        ])
    response = http_post(ENDPOINT, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                         data={"query": "query { topics(first: 1) { edges { node { slug } } } }"})
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    status = status_from_response(response)
    if status == "ok" and body.get("errors"):
        status = "failed"
    summary = {"status": status, "credential_source": key_name, "http_status": response.get("status_code"),
               "fields": fields_present(body), "docs": "https://api.producthunt.com/v2/docs",
               "cost_note": "Free. Rate limit 6,250 complexity points per 15 minutes."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
