#!/usr/bin/env python3
"""Build a deterministic claim ledger from evidence IDs and claim definitions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def stable_id(record: dict[str, Any]) -> str:
    existing = record.get("evidence_id")
    if existing:
        return str(existing)
    material = "\n".join(str(record.get(key, "")) for key in ("source", "source_url", "text", "retrieved_at"))
    return f"ev-{hashlib.sha256(material.encode()).hexdigest()[:16]}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            record["evidence_id"] = stable_id(record)
            records.append(record)
    return records


def build(evidence: list[dict[str, Any]], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {record["evidence_id"]: record for record in evidence}
    ledger = []
    for claim in claims:
        row = dict(claim)
        support = [str(item) for item in row.get("supporting_evidence", [])]
        counter = [str(item) for item in row.get("counter_evidence", [])]
        unknown = sorted({item for item in support + counter if item not in by_id})
        if unknown:
            claim_id = str(row.get("claim_id", "<missing claim_id>"))
            raise ValueError(f"{claim_id}: unknown evidence IDs: {', '.join(unknown)}")
        independence = {str(by_id[item].get("independence_key") or by_id[item].get("source_url") or item) for item in support}
        clusters = sorted({str(by_id[item].get("duplicate_cluster_id")) for item in support + counter if by_id[item].get("duplicate_cluster_id")})
        row["supporting_evidence"] = support
        row["counter_evidence"] = counter
        row["independence_count"] = len(independence)
        row["duplicate_clusters"] = clusters
        ledger.append(row)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True, help="JSON array of claim definitions")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    claims = json.loads(args.claims.read_text(encoding="utf-8"))
    if not isinstance(claims, list):
        parser.error("--claims must contain a JSON array")
    try:
        ledger = build(read_jsonl(args.evidence), claims)
    except (KeyError, ValueError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"claims": len(ledger), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
