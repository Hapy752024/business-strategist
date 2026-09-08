#!/usr/bin/env python3
"""Validate a business-to-brand snapshot without upgrading uncertainty."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/business-to-brand.schema.json").read_text())
POSITIONING_SCHEMA = json.loads((ROOT / "schemas/strategy-plan.schema.json").read_text())["properties"]["positioning"]


def validate_data(data: object) -> list[str]:
    errors = [error.message for error in Draft202012Validator(SCHEMA).iter_errors(data)]
    if errors:
        return errors
    for field, status in data["field_provenance"].items():
        value = data.get(field)
        refs = data.get("field_evidence_refs", {}).get(field, [])
        if isinstance(value, dict):
            refs = value.get("evidence_refs", refs)
        if status == "evidence_backed" and (not value or not refs):
            errors.append(f"{field}: evidence_backed requires field-specific supporting references")
    position = data.get("positioning", {})
    if "decision_status" in position:
        position_errors = [error.message for error in Draft202012Validator(POSITIONING_SCHEMA).iter_errors(position)]
        errors.extend(position_errors)
        if not position_errors:
            for item in [position, *position["activities"]]:
                if item["provenance"] == "evidence_backed" and not item["evidence_refs"]:
                    errors.append("positioning: evidence_backed requires supporting evidence_refs")
            if data["field_provenance"].get("positioning") != position["provenance"]:
                errors.append("positioning: field provenance must match the selected decision's provenance")
    return errors


def validate(path: Path, *, check_sources: bool = False) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid JSON: {exc}"]
    errors = validate_data(data)
    if errors or not check_sources:
        return errors
    sources = [{"path": data.get("source_path"), "sha256": data["source_sha256"]}]
    if "positioning_source" in data:
        sources.append(data["positioning_source"])
    for source in sources:
        if not source.get("path"):
            errors.append("source path not recorded; refresh handoff before claiming source freshness")
            continue
        try:
            actual = hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest()
        except OSError:
            errors.append(f"source unavailable: {source['path']}")
            continue
        if actual != source["sha256"]:
            errors.append(f"source changed: {source['path']}; review affected outputs and create a new snapshot")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--check-sources", action="store_true", help="Verify the recorded business and positioning source hashes before downstream work.")
    args = parser.parse_args()
    errors = validate(args.snapshot, check_sources=args.check_sources)
    print(json.dumps({"status": "fail" if errors else "pass", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
