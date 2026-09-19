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
POSITIONING_VALIDATOR = VALIDATOR.evolve(schema=SCHEMA["properties"]["positioning"])


def validate_positioning(position: object, *, experiment_ids: list[str] | None = None,
                         kpi_names: list[str] | None = None) -> list[str]:
    """Check declared support and local links, not strategic truth.

    Snapshots can check activity links and provenance without carrying duplicate
    experiment/KPI definitions. Plan validation supplies those authoritative IDs.
    """
    errors = [f"positioning{'.' if error.absolute_path else ''}{'.'.join(map(str, error.absolute_path))}: {error.message}"
              for error in POSITIONING_VALIDATOR.iter_errors(position)]
    if errors:
        return sorted(errors)
    rows = position["activities"]
    activity_ids = [row["id"] for row in rows if "id" in row]
    if len(activity_ids) != len(set(activity_ids)):
        errors.append("positioning.activities: IDs must be unique")
    items = [("positioning", position)]
    for index, row in enumerate(rows):
        label = f"positioning.activities.{index}"
        items.append((label, row))
        if row.get("relations") and not row.get("id"):
            errors.append(f"{label}: relations require a source activity id")
        for relation in row.get("relations", []):
            if relation["target"] not in activity_ids:
                errors.append(f"{label}.relations: unknown activity {relation['target']}")
    items.extend((f"positioning.value_proposition.{field}", claim)
                 for field, claim in position.get("value_proposition", {}).items())
    defense = position.get("defensibility", {})
    for index, hypothesis in enumerate(defense.get("hypotheses", [])):
        label = f"positioning.defensibility.hypotheses.{index}"
        items.append((label, hypothesis))
        for field in ("economic_benefit", "imitation_barrier", "value_capture"):
            claim = hypothesis[field]
            items.append((f"{label}.{field}", claim))
            if defense["status"] == "supported" and claim["provenance"] != "evidence_backed":
                errors.append(f"{label}.{field}: supported assessment requires evidence_backed provenance")
    for label, item in items:
        if item.get("provenance") == "evidence_backed" and not item["evidence_refs"]:
            errors.append(f"{label}: evidence_backed requires supporting evidence_refs")
        for field, known in (("activity_ids", activity_ids), ("experiment_ids", experiment_ids), ("kpi_names", kpi_names)):
            if known is not None:
                unknown = set(item.get(field, [])) - set(known)
                if unknown:
                    errors.append(f"{label}.{field}: unknown references {sorted(unknown)}")
    return sorted(errors)


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
        errors.extend(validate_positioning(plan["positioning"], experiment_ids=identifiers, kpi_names=names))
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
    try:
        from scripts.case_outputs import preflight, cases
    except ModuleNotFoundError:
        from case_outputs import preflight, cases
    import uuid
    destination = destination.absolute()
    authority = preflight(destination, 'strategy', 'business_linked' if plan.get('execution_binding') else 'standalone')
    if authority:
        root = authority['root']
        with cases.project_lock(root):
            if not plan.get('execution_binding'):
                raise ValueError('business baseline requires a selected-plan binding')
            cases.check_plan(root, plan)
            if destination.exists():
                raise FileExistsError(destination)
            current = cases.read_project(root)
            cases.publish_locked(root, {str(destination.relative_to(root)): cases.encoded(plan)},
                expected_revision=current['manifest_revision'], decision_id='baseline-' + uuid.uuid4().hex,
                reason='Freeze selected strategy baseline', affected=[plan['execution_binding']['case_id']])
        return
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
    try:
        try:
            from scripts import case_workspace as cases
        except ModuleNotFoundError:
            import case_workspace as cases
        root = cases.locate(args.plan)
        if root:
            destination_root = cases.locate_publication(args.output) if args.command == 'freeze' else None
            if destination_root and destination_root != root:
                raise ValueError('strategy source and destination controllers conflict')
            with cases.project_lock(root):
                cases.check_plan(root, plan)
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status': 'fail', 'errors': [str(exc)]}))
        return 1
    if args.command == "freeze":
        if root:
            with cases.project_lock(root):
                cases.check_plan(root, plan)
                if cases.load(args.plan) != plan:
                    raise ValueError('strategy source changed before freeze')
                if not cases.locate_publication(args.output):
                    freeze_plan(plan, args.output)
                    return 0
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
