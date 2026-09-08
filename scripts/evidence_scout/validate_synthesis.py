#!/usr/bin/env python3
"""Reject claims that overstate evidence, omit counter scope, or cite unknown IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from build_claim_ledger import stable_id, independent_groups

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected an object")
                if not value.get("evidence_id"):
                    value["evidence_id"] = stable_id(value)
                records.append(value)
    return records


CONFIDENCE_MINIMUM = {"unresolved": 0, "low": 1, "medium": 2, "high": 3}
SCOPE_KEYS = {"sources", "queries", "geography", "date_range", "failed_routes"}


def derived_independence(support: list[str], known: dict[str, dict[str, Any]]) -> int:
    return len(independent_groups([known[item] for item in support if item in known]))


def validate(ledger: list[dict[str, Any]], evidence: list[dict[str, Any]], *, require_source_review: bool = False) -> list[str]:
    known = {record["evidence_id"]: record for record in evidence}
    errors: list[str] = []
    for claim in ledger:
        ident = str(claim.get("claim_id", "<missing>"))
        support = claim.get("supporting_evidence", [])
        counter = claim.get("counter_evidence", [])
        unknown = [item for item in support + counter if item not in known]
        if unknown:
            errors.append(f"{ident}: unknown evidence IDs: {', '.join(unknown)}")
        derived = derived_independence(support, known)
        if int(claim.get("independence_count", -1)) != derived:
            errors.append(f"{ident}: submitted independence count does not match derived support")
        if derived < CONFIDENCE_MINIMUM.get(claim.get("confidence"), 99):
            errors.append(f"{ident}: confidence exceeds independent support")
        if not counter:
            scope = claim.get("none_found_scope")
            if not isinstance(scope, dict) or not SCOPE_KEYS.issubset(scope) or any(not scope[key] and key != "failed_routes" for key in SCOPE_KEYS):
                errors.append(f"{ident}: counter-evidence or complete none-found scope required")
        for evidence_id in support:
            record = known.get(evidence_id, {})
            if record.get("evidence_type") == "irrelevant" or record.get("relevance") == "irrelevant":
                errors.append(f"{ident}: irrelevant evidence cannot support claim")
        for evidence_id in set(support + counter):
            review = known.get(evidence_id, {}).get("analyst_review")
            if require_source_review and (
                not isinstance(review, dict)
                or review.get("status") != "accepted"
                or not isinstance(review.get("reason"), str)
                or not review["reason"].strip()
            ):
                errors.append(f"{ident}: {evidence_id}: accepted source review with reason required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--require-source-review", action="store_true", help="Require explicit analyst acceptance and rationale for every supporting and counter record.")
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    errors = validate(ledger, read_jsonl(args.evidence), require_source_review=args.require_source_review)
    print(json.dumps({"status": "pass" if not errors else "fail", "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
