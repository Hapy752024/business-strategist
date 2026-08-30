#!/usr/bin/env python3
"""Build an immutable, provenance-aware business-to-brand snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def pick(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def build_snapshot(source_path: Path) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source_bytes = source_path.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    fields = {
        "business_identity": pick(source, "business_identity", "identity") or {},
        "segment": pick(source, "segment", "customer_segment") or {},
        "job_and_pain": pick(source, "job_and_pain", "problem", "pain") or {},
        "positioning": pick(source, "positioning", "value_proposition") or {},
        "buying_context": pick(source, "buying_context", "buyer_context") or {},
        "customer_language": pick(source, "customer_language", "language") or [],
        "channels_and_contexts": pick(source, "channels_and_contexts", "channels") or {},
    }
    provenance: dict[str, str] = {}
    for name, value in fields.items():
        provenance[name] = "evidence_backed" if value else "unresolved"
    timestamp = now_iso()
    return {
        "schema_version": "1.0",
        "snapshot_id": f"business-to-brand-{source_hash[:12]}",
        "created_at": timestamp,
        "source_workspace": str(source_path.parent.resolve()),
        "source_manifest_version": source.get("schema_version", "unknown"),
        **fields,
        "field_provenance": provenance,
        "evidence_refs": source.get("evidence_refs", source.get("artifacts", [])),
        "coverage_gaps": source.get("coverage_gaps", source.get("open_gaps", [])),
        "user_overrides": {},
        "source_sha256": source_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    snapshot = build_snapshot(args.source_manifest.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot_id": snapshot["snapshot_id"], "output": str(args.output), "unresolved": [key for key, value in snapshot["field_provenance"].items() if value == "unresolved"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
