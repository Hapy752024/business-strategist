#!/usr/bin/env python3
"""Smallest live check of the Apify Reddit fallback actor (maxItems 1, no comments)."""
from __future__ import annotations

from common import fields_present, finish, get_secret, http_post, missing_credentials, status_from_response

PROVIDER = "apify_reddit"
ENDPOINT = "https://api.apify.com/v2/acts/practicaltools~apify-reddit-api/run-sync-get-dataset-items?timeout=120&memory=512"


def main() -> int:
    key_name, token = get_secret("APIFY_TOKEN")
    if not token:
        return missing_credentials(PROVIDER, ["APIFY_TOKEN"], [
            "Create or log in at https://console.apify.com/",
            "Open Settings -> Integrations -> API token",
            "Set it with: export APIFY_TOKEN='your_token'",
            "Or add APIFY_TOKEN=your_token to ~/.secrets",
        ])
    response = http_post(ENDPOINT, headers={"Authorization": f"Bearer {token}"}, timeout=150, data={
        "searches": ["invoice"], "searchPosts": True, "searchComments": False,
        "fetchPostComments": False, "maxItems": 1, "sort": "relevance", "time": "week"})
    body = response.get("body")
    status = status_from_response(response)
    if status == "ok" and not (isinstance(body, list) and body):
        status = "failed"
    summary = {"status": status, "credential_source": key_name, "http_status": response.get("status_code"),
               "fields": fields_present(body[0] if isinstance(body, list) and body else body),
               "docs": "https://apify.com/practicaltools/apify-reddit-api",
               "cost_note": "maxItems 1, comments off: cents at most. Third-party scraper; fallback only."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
