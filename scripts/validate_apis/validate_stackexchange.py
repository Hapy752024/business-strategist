#!/usr/bin/env python3
"""Smallest live check of the Stack Exchange API (works keyless at 300 requests/day)."""
from __future__ import annotations

from common import cli_arg, fields_present, finish, get_secret, http_get, status_from_response, with_query

PROVIDER = "stackexchange"
ENDPOINT = "https://api.stackexchange.com/2.3/search/advanced"


def main() -> int:
    key_name, key = get_secret("STACKEXCHANGE_KEY")
    query = cli_arg("query", "late invoice payment")
    params = {"q": query, "site": cli_arg("site", "stackoverflow"), "filter": "withbody", "pagesize": 1}
    if key:
        params["key"] = key
    response = http_get(with_query(ENDPOINT, params))
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    items = body.get("items") if isinstance(body.get("items"), list) else []
    summary = {"status": status_from_response(response), "credential_source": key_name or "none (keyless)",
               "query": query, "http_status": response.get("status_code"),
               "fields": fields_present(items[0] if items else body), "item_count": len(items),
               "quota_remaining": body.get("quota_remaining"), "quota_max": body.get("quota_max"),
               "docs": "https://api.stackexchange.com/docs/advanced-search",
               "cost_note": "Free. 300 requests/day keyless; STACKEXCHANGE_KEY (free app key) raises the quota."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
