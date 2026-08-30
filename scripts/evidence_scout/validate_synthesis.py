#!/usr/bin/env python3
"""Reject claims that overstate evidence, omit counter scope, or cite unknown IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected an object")
                if not value.get("evidence_id"):
                    material = "\n".join(str(value.get(key, "")) for key in ("source", "source_url", "text", "retrieved_at"))
                    value["evidence_id"] = f"ev-{hashlib.sha256(material.encode()).hexdigest()[:16]}"
                records.append(value)
    return records


CONFIDENCE_MINIMUM = {"unresolved": 0, "low": 1, "medium": 2, "high": 3}
SCOPE_KEYS = {"sources", "queries", "geography", "date_range", "failed_routes"}


def validate(ledger: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[str]:
    known = {record["evidence_id"]: record for record in evidence}
    errors: list[str] = []
    for claim in ledger:
        ident = str(claim.get("claim_id", "<missing>"))
        support = claim.get("supporting_evidence", [])
        counter = claim.get("counter_evidence", [])
        unknown = [item for item in support + counter if item not in known]
        if unknown:
            errors.append(f"{ident}: unknown evidence IDs: {', '.join(unknown)}")
        if int(claim.get("independence_count", 0)) < CONFIDENCE_MINIMUM.get(claim.get("confidence"), 99):
            errors.append(f"{ident}: confidence exceeds independent support")
        if not counter:
            scope = claim.get("none_found_scope")
            if not isinstance(scope, dict) or not SCOPE_KEYS.issubset(scope):
                errors.append(f"{ident}: counter-evidence or complete none-found scope required")
        for evidence_id in support:
            record = known.get(evidence_id, {})
            if record.get("evidence_type") == "irrelevant":
                errors.append(f"{ident}: irrelevant evidence cannot support claim")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    errors = validate(ledger, read_jsonl(args.evidence))
    print(json.dumps({"status": "pass" if not errors else "fail", "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
