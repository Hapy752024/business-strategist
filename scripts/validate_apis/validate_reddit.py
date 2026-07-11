#!/usr/bin/env python3
from __future__ import annotations

import urllib.parse

from common import cli_arg, fields_present, finish, get_secret, http_get, http_post, missing_credentials, status_from_response, with_query


PROVIDER = "reddit"


def main() -> int:
    client_id_name, client_id = get_secret("REDDIT_CLIENT_ID")
    client_secret_name, client_secret = get_secret("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return missing_credentials(
            PROVIDER,
            ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"],
            [
                "Open https://www.reddit.com/prefs/apps",
                "Create an app. For read-only validation, a script app is fine.",
                "Copy the client ID under the app name and the secret field.",
                "Set: export REDDIT_CLIENT_ID='...' REDDIT_CLIENT_SECRET='...'",
                "Or add both keys to ~/.secrets",
            ],
        )

    token_response = http_post(
        "https://www.reddit.com/api/v1/access_token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}),
        basic_auth=(client_id, client_secret),
    )
    raw = {"token": token_response}
    status = status_from_response(token_response)
    subreddit_count = 0
    post_count = 0
    if status == "ok":
        token = (token_response.get("body") or {}).get("access_token")
        headers = {"Authorization": f"Bearer {token}", "User-Agent": "evidence-scout-validator/0.1"}
        query = cli_arg("query", "projectmanagement")
        subreddits = http_get(
            with_query("https://oauth.reddit.com/subreddits/search", {"q": query, "limit": 5}),
            headers=headers,
        )
        posts = http_get(
            with_query("https://oauth.reddit.com/r/productivity/search", {"q": "frustrated", "restrict_sr": "on", "limit": 5, "sort": "relevance"}),
            headers=headers,
        )
        raw["subreddits"] = subreddits
        raw["posts"] = posts
        subreddit_count = len(((subreddits.get("body") or {}).get("data") or {}).get("children", [])) if subreddits.get("ok") else 0
        post_count = len(((posts.get("body") or {}).get("data") or {}).get("children", [])) if posts.get("ok") else 0

    summary = {
        "status": status,
        "credential_source": [client_id_name, client_secret_name],
        "http_status": token_response.get("status_code"),
        "fields": fields_present(raw),
        "subreddit_count": subreddit_count,
        "post_count": post_count,
        "docs": "https://www.reddit.com/dev/api/",
        "cost_note": "Reddit API terms and commercial access can vary. Validate intended volume and use case before production research.",
    }
    return finish(PROVIDER, summary, raw)


if __name__ == "__main__":
    raise SystemExit(main())
