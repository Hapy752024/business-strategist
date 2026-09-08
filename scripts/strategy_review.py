#!/usr/bin/env python3
"""Validate a decision-ready strategy plan and calculate KPI review status."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "strategy-plan.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Return machine-readable shortcomings instead of silently accepting a plan."""
    errors = [f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}" for error in VALIDATOR.iter_errors(plan)]
    if not isinstance(plan, dict) or any(not isinstance(plan.get(key, []), list) for key in ("experiments", "kpis")):
        return sorted(errors)
    identifiers = [str(item.get("id", "")) for item in plan.get("experiments", []) if isinstance(item, dict)]
    if len(identifiers) != len(set(identifiers)):
        errors.append("experiments: IDs must be unique")
    names = [str(item.get("name", "")) for item in plan.get("kpis", []) if isinstance(item, dict)]
    if len(names) != len(set(names)):
        errors.append("kpis: names must be unique")
    for kpi in plan.get("kpis", []):
        if isinstance(kpi, dict) and kpi.get("cadence") == "cohort" and not kpi.get("cohort"):
            errors.append("cohort KPIs require a named cohort")
    if "positioning" in plan and not any(error.startswith(("positioning:", "positioning.")) for error in errors):
        position = plan["positioning"]
        for label, item in [("positioning", position), *[(f"positioning.activities.{i}", row) for i, row in enumerate(position["activities"])]]:
            if item["provenance"] == "evidence_backed" and not item["evidence_refs"]:
                errors.append(f"{label}: evidence_backed requires supporting evidence_refs")
            for field, known in (("experiment_ids", identifiers), ("kpi_names", names)):
                unknown = set(item.get(field, [])) - set(known)
                if unknown:
                    errors.append(f"{label}.{field}: unknown references {sorted(unknown)}")
    return sorted(errors)


def weekly_review(plan: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    """Calculate KPI ratios from named numerator/denominator observations."""
    errors = validate_plan(plan)
    if errors:
        return {"status": "invalid_plan", "errors": errors, "kpis": []}
    results = []
    for kpi in plan["kpis"]:
        numerator = observations.get(kpi["numerator"])
        denominator = observations.get(kpi["denominator"])
        metadata = observations.get("_metadata", {}).get(kpi["name"], {})
        if any(metadata.get(field) != kpi[field] for field in ("window", "cohort", "currency") if field in kpi):
            results.append({"name": kpi["name"], "status": "scope_mismatch"})
            continue
        if kpi.get("cohort") and metadata.get("mature") is not True:
            results.append({"name": kpi["name"], "status": "immature_cohort"})
            continue
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in (numerator, denominator)):
            results.append({"name": kpi["name"], "status": "missing_observation"})
        elif denominator <= 0 or numerator < 0:
            results.append({"name": kpi["name"], "status": "invalid_denominator"})
        else:
            value = numerator / denominator
            meets_target = value >= kpi["target"] if kpi["direction"] == "at_least" else value <= kpi["target"]
            results.append({"name": kpi["name"], "value": value, "target": kpi["target"], "status": "on_track" if meets_target else "off_track", "decision_rule": kpi["decision_rule"]})
    commitments = [{**item, "status": "completed" if item.get("completed_at") else "overdue" if item["due_date"] < date.today().isoformat() else "pending"} for item in plan["commitments"]]
    report = {"status": "complete" if all(item["status"] in {"on_track", "off_track"} for item in results) else "incomplete", "verdict": plan["verdict"], "kpis": results, "commitments": commitments}
    if "positioning" in plan:
        report["positioning"] = plan["positioning"]
        report["positioning_review"] = "Review disconfirming evidence, delivery/economic guardrails, and affected downstream outputs; KPI results alone do not validate the position."
    return report


def freeze_plan(plan: dict[str, Any], destination: Path) -> None:
    """Save a non-overwriting baseline before collecting results."""
    errors = validate_plan(plan)
    if errors:
        raise ValueError("; ".join(errors))
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--plan", type=Path, required=True)
    review_parser = subparsers.add_parser("weekly-review")
    review_parser.add_argument("--plan", type=Path, required=True)
    review_parser.add_argument("--observations", type=Path, required=True)
    review_parser.add_argument("--baseline", type=Path, required=True)
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--plan", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if args.command == "freeze":
        freeze_plan(plan, args.output)
        return 0
    if args.command == "validate":
        errors = validate_plan(plan)
        print(json.dumps({"status": "pass" if not errors else "fail", "errors": errors}, indent=2))
        return 0 if not errors else 1
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    if any(plan.get(key) != baseline.get(key) for key in ("experiments", "kpis")):
        print(json.dumps({"status": "changed_protocol", "errors": ["Experiment or KPI rules changed after baseline; create a new experiment revision."]}))
        return 1
    report = weekly_review(plan, observations)
    if plan.get("positioning") != baseline.get("positioning"):
        report["positioning_changed"] = True
        report["positioning_review"] = "Position changed since baseline: review affected service, operations, marketing, and brand outputs; preserve the original experiment interpretation."
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
