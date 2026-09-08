#!/usr/bin/env python3
"""Build an immutable, provenance-aware business-to-brand snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.brand.validate_business_to_brand_handoff import validate_data
from scripts.strategy_review import validate_plan


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


SOURCE_KEYS = {
    "business_identity": ("business_identity", "identity"),
    "segment": ("segment", "customer_segment"),
    "job_and_pain": ("job_and_pain", "problem", "pain"),
    "positioning": ("positioning", "value_proposition"),
    "buying_context": ("buying_context", "buyer_context"),
    "customer_language": ("customer_language", "language"),
    "channels_and_contexts": ("channels_and_contexts", "channels"),
}


def build_snapshot(source_path: Path, strategy_plan_path: Path | None = None) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    if not isinstance(source, dict):
        raise ValueError("business context must be an object")
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    plan = None
    positioning_source = None
    if strategy_plan_path is not None:
        plan_bytes = strategy_plan_path.read_bytes()
        plan = json.loads(plan_bytes)
        errors = validate_plan(plan)
        if errors:
            raise ValueError("invalid strategy plan: " + "; ".join(errors))
        if not plan.get("positioning"):
            raise ValueError("selected strategy plan has no positioning; do not fall back to stale business context")
        positioning_source = {"path": str(strategy_plan_path.resolve()), "sha256": hashlib.sha256(plan_bytes).hexdigest()}
    selected_keys = {name: next((key for key in keys if source.get(key) not in (None, "", [], {})), None) for name, keys in SOURCE_KEYS.items()}
    fields = {name: source[key] if key else ([] if name == "customer_language" else {}) for name, key in selected_keys.items()}
    if plan is not None:
        fields["positioning"] = plan["positioning"]
    provenance: dict[str, str] = {}
    field_refs: dict[str, list] = {}
    gaps = source.get("coverage_gaps", source.get("open_gaps", []))
    evidence_refs = source.get("evidence_refs", source.get("artifacts", []))
    if not isinstance(gaps, list) or not isinstance(evidence_refs, list):
        raise ValueError("coverage_gaps and evidence_refs must be arrays")
    gaps, evidence_refs = list(gaps), list(evidence_refs)
    for name, value in fields.items():
        origin = plan if name == "positioning" and plan is not None else source
        statuses = origin.get("field_provenance", {})
        declared_refs = origin.get("field_evidence_refs", {})
        if not isinstance(statuses, dict) or not isinstance(declared_refs, dict):
            raise ValueError("field_provenance and field_evidence_refs must be objects")
        key = name if origin is plan else selected_keys[name]
        refs = declared_refs.get(name, declared_refs.get(key, []))
        if isinstance(value, dict):
            refs = value.get("evidence_refs", refs)
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError(f"{name}: supporting evidence_refs must be nonempty strings")
        field_refs[name] = refs
        status = statuses.get(name, statuses.get(key, "unresolved"))
        if isinstance(value, dict):
            status = value.get("provenance", status)
        if not value:
            status = "unresolved"
        if status == "evidence_backed" and not refs:
            status = "unresolved"
            # Preserve the unsupported claim's content, but never its inflated label.
            if isinstance(value, dict) and value.get("provenance") == "evidence_backed":
                value["provenance"] = "unresolved"
            gaps.append(f"{name}: evidence_backed claim lacked field-specific supporting references")
        provenance[name] = status
        if value and status == "unresolved":
            gaps.append(f"{name}: provenance unresolved")
        for ref in refs:
            if ref not in evidence_refs:
                evidence_refs.append(ref)
    if plan is not None:
        if not isinstance(plan.get("coverage_gaps", []), list):
            raise ValueError("strategy coverage_gaps must be an array")
        for gap in plan.get("coverage_gaps", []):
            if gap not in gaps:
                gaps.append(gap)
    timestamp = now_iso()
    identity = source_hash if positioning_source is None else hashlib.sha256(f"{source_hash}:{positioning_source['sha256']}".encode()).hexdigest()
    snapshot = {
        "schema_version": "1.0",
        "snapshot_id": f"business-to-brand-{identity[:12]}",
        "created_at": timestamp,
        "source_workspace": str(source_path.parent.resolve()),
        "source_path": str(source_path.resolve()),
        "source_manifest_version": source.get("schema_version", "unknown"),
        **fields,
        "field_provenance": provenance,
        "field_evidence_refs": field_refs,
        "evidence_refs": evidence_refs,
        "coverage_gaps": gaps,
        "user_overrides": {},
        "source_sha256": source_hash,
    }
    if positioning_source is not None:
        snapshot["positioning_source"] = positioning_source
    errors = validate_data(snapshot)
    if errors:
        raise ValueError("invalid handoff: " + "; ".join(errors))
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--strategy-plan", type=Path, help="Explicitly selected strategy-plan.json; preserves its positioning and provenance.")
    args = parser.parse_args()
    try:
        snapshot = build_snapshot(args.source_manifest.resolve(), args.strategy_plan)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Cannot build handoff: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    except FileExistsError:
        parser.exit(1, "Snapshot already exists; choose a new revision path.\n")
    print(json.dumps({"snapshot_id": snapshot["snapshot_id"], "output": str(args.output), "unresolved": [key for key, value in snapshot["field_provenance"].items() if value == "unresolved"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
