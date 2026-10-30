#!/usr/bin/env python3
"""Smallest live check of the Arctic Shift archive (one subreddit, limit 3, no credentials)."""
from __future__ import annotations

from common import fields_present, finish, http_get, status_from_response, with_query

PROVIDER = "arctic_shift"
ENDPOINT = "https://arctic-shift.photon-reddit.com/api/posts/search"


def main() -> int:
    response = http_get(with_query(ENDPOINT, {"subreddit": "smallbusiness", "query": "invoice", "limit": 3}))
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    status = status_from_response(response)
    if response.get("status_code") == 422 and "timeout" in str(body.get("error", "")).lower():
        status = "rate_limited"
    elif status == "ok" and not body.get("data"):
        status = "failed"
    data = body.get("data")
    summary = {"status": status, "http_status": response.get("status_code"),
               "fields": fields_present(data[0] if isinstance(data, list) and data else body),
               "docs": "https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md",
               "note": "Volunteer-run archive; throttles hard. rate_limited is a coverage gap, not a failure of the lane."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
