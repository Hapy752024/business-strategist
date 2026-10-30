#!/usr/bin/env python3
"""Smallest live check of Bluesky search: createSession, then one searchPosts call (limit 1)."""
from __future__ import annotations

from common import fields_present, finish, get_secret, http_get, http_post, missing_credentials, status_from_response, with_query

PROVIDER = "bluesky"
PDS = "https://bsky.social/xrpc"


def main() -> int:
    handle_name, handle = get_secret("BLUESKY_HANDLE")
    _, password = get_secret("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        return missing_credentials(PROVIDER, ["BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"], [
            "In Bluesky open Settings -> Privacy and security -> App passwords -> Add App Password",
            "Set them with: export BLUESKY_HANDLE='you.bsky.social' BLUESKY_APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'",
            "Or add both lines to ~/.secrets. Never use your main account password.",
        ])
    session = http_post(f"{PDS}/com.atproto.server.createSession", data={"identifier": handle, "password": password})
    jwt = (session.get("body") or {}).get("accessJwt") if isinstance(session.get("body"), dict) else None
    if not jwt:
        # Never persist the login exchange: it carries the app password and tokens.
        summary = {"status": status_from_response(session), "stage": "createSession", "http_status": session.get("status_code")}
        return finish(PROVIDER, summary, {"stage": "createSession", "http_status": session.get("status_code")})
    response = http_get(with_query(f"{PDS}/app.bsky.feed.searchPosts", {"q": "invoice", "limit": 1}),
                        headers={"Authorization": f"Bearer {jwt}"})
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    summary = {"status": status_from_response(response), "credential_source": handle_name, "http_status": response.get("status_code"),
               "fields": fields_present(body), "post_count": len(body.get("posts") or []),
               "docs": "https://docs.bsky.app/docs/api/app-bsky-feed-search-posts",
               "cost_note": "Free. About 3,000 requests per 5 minutes per account."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
