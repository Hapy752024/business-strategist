#!/usr/bin/env python3
"""Smallest live check of the CFPB Consumer Complaint Database API (no key)."""
from __future__ import annotations

import json
import sys

from common import cli_arg, project_root, fields_present, finish, http_get, status_from_response, with_query

PROVIDER = "cfpb_complaints"
ENDPOINT = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"


def blocked_reason() -> str | None:
    try:
        data = json.loads((project_root() / "config" / "source-capabilities.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for item in data.get("capabilities", []):
        if item.get("id") == PROVIDER and item.get("status") == "blocked_by_provider":
            return str(item.get("status_reason") or "blocked by provider")
    return None


def main() -> int:
    reason = blocked_reason()
    if reason and "--force-blocked" not in sys.argv:
        summary = {"status": "optional_unavailable", "blocked": "blocked_by_provider", "status_reason": reason,
                   "note": "Live probe skipped. Pass --force-blocked to probe anyway."}
        finish(PROVIDER, summary, {"skipped": True, "reason": reason})
        return 0  # blocked is an expected state, not a validation failure
    query = cli_arg("query", "overdraft fee")
    response = http_get(with_query(ENDPOINT, {"search_term": query, "field": "all", "size": 3,
                                              "has_narrative": "true", "no_aggs": "true"}), timeout=40)
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    hits = (body.get("hits") or {}).get("hits") if isinstance(body.get("hits"), dict) else []
    hits = hits if isinstance(hits, list) else []
    narratives = sum(1 for h in hits if isinstance(h, dict) and (h.get("_source") or {}).get("complaint_what_happened"))
    summary = {"status": status_from_response(response), "query": query, "http_status": response.get("status_code"),
               "fields": fields_present(hits[0].get("_source") if hits else body),
               "hit_count": len(hits), "hits_with_narrative": narratives,
               "docs": "https://cfpb.github.io/ccdb5-api/documentation/",
               "cost_note": "Free, no key. Public API metadata only unless narratives are returned (hits_with_narrative)."}
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
