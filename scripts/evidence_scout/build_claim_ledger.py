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
    # Retrieval time is an occurrence, not the identity of the published item.
    material = "\n".join(str(record.get(key, "")) for key in ("source", "source_record_id", "source_url", "content_sha256", "text"))
    return f"ev-{hashlib.sha256(material.encode()).hexdigest()[:16]}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            record["evidence_id"] = stable_id(record)
            records.append(record)
    return records


def independent_groups(records: list[dict[str, Any]]) -> list[str]:
    """Collapse connected author, content, and duplicate identities conservatively."""
    groups: list[set[str]] = []
    for record in records:
        key = record.get("independence_key")
        tokens = {f"author:{key}"} if key and not str(key).startswith("unknown:") else set()
        for field in ("duplicate_cluster_id", "content_sha256"):
            if record.get(field):
                tokens.add(f"{field}:{record[field]}")
        if record.get("text"):
            tokens.add("text:" + hashlib.sha256(" ".join(record["text"].split()).encode()).hexdigest())
        overlaps = [group for group in groups if group & tokens]
        for group in overlaps:
            tokens |= group
            groups.remove(group)
        groups.append(tokens)
    return sorted(min(token for token in group if token.startswith("author:")) for group in groups if any(token.startswith("author:") for token in group))


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
        independence = independent_groups([by_id[item] for item in support])
        clusters = sorted({str(by_id[item].get("duplicate_cluster_id")) for item in support + counter if by_id[item].get("duplicate_cluster_id")})
        row["supporting_evidence"] = support
        row["counter_evidence"] = counter
        row["independence_count"] = len(independence)
        row["independence_keys"] = sorted(independence)
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
