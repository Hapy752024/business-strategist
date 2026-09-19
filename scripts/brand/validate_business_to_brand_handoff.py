#!/usr/bin/env python3
"""Validate a business-to-brand snapshot without upgrading uncertainty."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import case_workspace as cases, subprojects
from scripts.strategy_review import validate_positioning
SCHEMA = json.loads((ROOT / "schemas/business-to-brand.schema.json").read_text())


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
        position_errors = validate_positioning(position)
        errors.extend(position_errors)
        if not position_errors:
            if data["field_provenance"].get("positioning") != position["provenance"]:
                errors.append("positioning: field provenance must match the selected decision's provenance")
    return errors


def validate(path: Path, *, check_sources: bool = False) -> list[str]:
    try:
        owner = cases.locate_publication(path)
        if owner:
            cases.read_project(owner)
            cases.safe(owner, str(path.absolute().relative_to(owner)))
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"invalid JSON: {exc}"]
    errors = validate_data(data)
    if errors:
        return errors
    try:
        roots = {r for p in [path, Path(data.get('source_path', '.')), Path(data.get('positioning_source', {}).get('path', '.'))]
                 for r in [cases.locate(p)] if r}
        if len(roots) > 1:
            raise ValueError('conflicting handoff project roots')
        root = next(iter(roots), None)
        if owner and cases.read_project(owner).get('controller_kind') == 'umbrella' and root and root != subprojects.business(owner):
            raise ValueError('handoff source belongs to another project')
        if root or data.get('case_project_root') or data.get('execution_binding'):
            if not root or data.get('case_project_root') != str(root):
                raise ValueError('missing or mismatched case project identity')
            with cases.project_lock(root):
                cases.check_binding(root, data.get('execution_binding', {}))
                plan = cases.load(root / 'strategy/strategy-plan.json')
                cases.check_plan(root, plan)
            check_sources = True
    except (ValueError, OSError, KeyError) as exc:
        errors.append(str(exc))
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
