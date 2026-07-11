#!/usr/bin/env python3
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_get, missing_credentials, status_from_response, with_query


PROVIDER = "x"


def main() -> int:
    key_name, bearer = get_secret("X_BEARER_TOKEN", "TWITTER_BEARER_TOKEN")
    if not bearer:
        return missing_credentials(
            PROVIDER,
            ["X_BEARER_TOKEN"],
            [
                "Apply/sign in at https://developer.x.com/",
                "Create a project/app with read access to recent search",
                "Copy the Bearer Token",
                "Set it with: export X_BEARER_TOKEN='your_token'",
                "Or add X_BEARER_TOKEN=your_token to ~/.secrets",
            ],
        )

    query = cli_arg("query", '"why is it so hard" startup -is:retweet lang:en')
    url = with_query(
        "https://api.x.com/2/tweets/search/recent",
        {
            "query": query,
            "max_results": 10,
            "tweet.fields": "created_at,public_metrics,lang,context_annotations",
        },
    )
    response = http_get(url, headers={"Authorization": f"Bearer {bearer}"})
    body = response.get("body")
    summary = {
        "status": status_from_response(response),
        "credential_source": key_name,
        "query": query,
        "http_status": response.get("status_code"),
        "fields": fields_present(body),
        "tweet_count": len(body.get("data", [])) if isinstance(body, dict) and isinstance(body.get("data"), list) else 0,
        "docs": "https://docs.x.com/x-api/introduction",
        "cost_note": "X access and pricing changes frequently. Treat this script as the source of truth for current account access.",
    }
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
