#!/usr/bin/env python3
"""Validate VOC evidence accounting without confusing missing coverage with invalid evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _counts(row: dict[str, Any], label: str, errors: list[str], *, topic: bool = False,
            require_ids: bool = True) -> tuple[list[int], list[str]]:
    accepted_name = "accepted_count" if topic else "accepted_customer_voice_count"
    values = [row.get(name, 0) for name in ("retrieved_count", "reviewed_count", accepted_name)]
    if any(type(value) is not int or value < 0 for value in values):
        errors.append(f"{label}: counts must be non-negative integers")
        values = [0, 0, 0]
    elif not values[2] <= values[1] <= values[0]:
        errors.append(f"{label}: counts require accepted <= reviewed <= retrieved")
    ids = row.get("accepted_evidence_ids", [])
    if not isinstance(ids, list) or any(not isinstance(item, str) or not item.strip() for item in ids):
        errors.append(f"{label}: accepted_evidence_ids must be a list of non-empty strings")
        ids = []
    elif len(ids) != len(set(ids)) or (require_ids and len(ids) != values[2]):
        errors.append(f"{label}: accepted_evidence_ids must be unique and reconcile to accepted count")
    if any(values) and row.get("attempted") is not True:
        errors.append(f"{label}: retrieved/reviewed/accepted evidence requires an attempted capture")
    return values, ids


def _outcome(row: dict[str, Any] | None) -> str:
    if row is None:
        return "pending"
    if str(row.get("failed_or_blocked") or "").strip():
        return "inaccessible" if row.get("access_status") == "inaccessible" else "failed_or_blocked"
    return "attempted" if row.get("attempted") is True else "pending"


def _index(rows: Any, fields: tuple[str, ...], label: str, errors: list[str]) -> dict[tuple[str, ...], dict[str, Any]]:
    output: dict[tuple[str, ...], dict[str, Any]] = {}
    if not isinstance(rows, list):
        errors.append(f"{label} must be a list")
        return output
    for row in rows:
        if not isinstance(row, dict):
            errors.append(f"{label} entries must be objects")
            continue
        key = tuple(str(row.get(field) or "") for field in fields)
        if not all(key) or key in output:
            errors.append(f"{label}: missing or duplicate key {key}")
        else:
            output[key] = row
    return output


def validate(plan: dict[str, Any], results: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    gaps: list[dict[str, Any]] = []
    outcomes: list[str] = []

    def gap(scope: dict[str, Any], reason: str, status: str = "pending") -> None:
        gaps.append({**scope, "status": status, "reason": reason})

    raw_topic = results.get("topic_led_voc", {})
    if not isinstance(raw_topic, dict):
        errors.append("topic_led_voc must be an object")
        raw_topic = {}
    planned_cells = plan.get("topic_matrix", [])
    if not isinstance(planned_cells, list):
        errors.append("topic_matrix must be a list")
        planned_cells = []
    # Legacy plans/results are useful inputs, but cannot attest market coverage.
    if not planned_cells:
        planned_cells = [{"cell_id": f"topic:{locale}", "locale": locale} for locale in plan.get("locales", [])]
    planned_by_id = _index(planned_cells, ("cell_id",), "topic plan cells", errors)
    for locale in plan.get("locales", []):
        if not any(cell.get("locale") == locale for cell in planned_cells):
            gap({"sampling_frame": "topic_led_voc", "locale": locale}, "Requested locale has no planned topic cell")
            outcomes.append("pending")
    topic_ids: set[str] = set()
    topic_attempted = False
    topic_rows: list[dict[str, Any]] = []
    if "cells" not in raw_topic:
        counts, ids = _counts(raw_topic, "topic-led counts", errors, topic=True)
        topic_ids.update(ids)
        topic_attempted = _outcome(raw_topic) != "pending"
        gap({"sampling_frame": "topic_led_voc"},
            "Legacy aggregate topic results have no cell bindings; locale/job/role/source/intent coverage is unresolved", "unresolved")
        for cell in planned_cells:
            topic_rows.append({**cell, "execution_status": "pending", "coverage_status": "unresolved",
                               "accepted_evidence_ids": []})
            outcomes.append("pending")
            gap({"sampling_frame": "topic_led_voc", **cell}, "No cell-bound topic result; aggregate counts cannot establish this scope", "unresolved")
        topic = {**raw_topic, "cells": topic_rows, "accepted_evidence_ids": sorted(topic_ids),
                 "accepted_count": len(topic_ids), "scope_binding_status": "legacy_unresolved"}
    else:
        cells = _index(raw_topic["cells"], ("cell_id",), "topic result cells", errors)
        for key in cells.keys() - planned_by_id.keys():
            errors.append(f"topic result cell {key}: not in the sampling plan")
        topic_totals = [0, 0, 0]
        for key, cell in planned_by_id.items():
            result = cells.get(key)
            outcome = _outcome(result)
            outcomes.append(outcome)
            scope = {"sampling_frame": "topic_led_voc", **cell}
            if outcome != "attempted":
                gap(scope, str((result or {}).get("failed_or_blocked") or "No attempted topic result"), outcome)
            row = {**cell, "execution_status": outcome, "accepted_evidence_ids": []}
            if result is not None:
                # Results may report observations; they cannot change the planned scope.
                for field in ("locale", "job", "role", "source_family", "query_intent"):
                    if field in result and result[field] != cell.get(field):
                        errors.append(f"topic cell {key}: result {field} disagrees with planned scope")
                counts, ids = _counts(result, f"topic cell {key}", errors, topic=True)
                topic_totals = [a + b for a, b in zip(topic_totals, counts)]
                topic_ids.update(ids)
                topic_attempted |= outcome != "pending"
                row.update({name: result[name] for name in ("attempted", "retrieved_count", "reviewed_count", "accepted_count", "accepted_evidence_ids", "failed_or_blocked", "queries", "sampling") if name in result})
                if counts[1] < counts[0]:
                    gap(scope, "Retrieved observations remain unreviewed", "review_pending")
                if outcome == "attempted" and not ids:
                    gap(scope, "No accepted customer voice in this sampling cell; no conclusion about absence of need", "no_accepted_voice")
                row["coverage_status"] = "observed_customer_voice" if ids else "no_accepted_voice" if outcome == "attempted" else "unresolved"
            topic_rows.append(row)
        if "accepted_evidence_ids" in raw_topic:
            declared = raw_topic["accepted_evidence_ids"]
            if not isinstance(declared, list) or any(not isinstance(item, str) for item in declared) or len(declared) != len(set(declared)) or set(declared) != topic_ids:
                errors.append("topic-led aggregate accepted_evidence_ids must equal the unique union of cell IDs")
        if "accepted_count" in raw_topic and (type(raw_topic["accepted_count"]) is not int or raw_topic["accepted_count"] != len(topic_ids)):
            errors.append("topic-led aggregate accepted_count must equal unique accepted evidence IDs")
        topic = {"attempted": topic_attempted, "cells": topic_rows, "accepted_evidence_ids": sorted(topic_ids),
                 "accepted_count": len(topic_ids), "retrieved_count": topic_totals[0], "reviewed_count": topic_totals[1],
                 "counting_note": "retrieved/reviewed totals are sampling-cell occurrences; accepted_count is distinct evidence IDs",
                 "scope_binding_status": "cell_bound"}

    fields = ("entity_id", "locale", "source_lane")
    planned_sources = _index(plan.get("source_matrix", []), fields, "source plan", errors)
    keyed = _index(results.get("source_results", []), fields, "source_results", errors)
    for key in keyed.keys() - planned_sources.keys():
        errors.append(f"source result {key}: not in the reviewed source plan")
    finalized: list[dict[str, Any]] = []
    entity_ids: set[str] = set()
    for key, planned in planned_sources.items():
        row = dict(planned)
        scope = {"sampling_frame": "entity_led_feedback", **dict(zip(fields, key))}
        result = keyed.get(key)
        if not planned.get("applicable"):
            if not str(planned.get("not_applicable_reason") or "").strip():
                errors.append(f"{key}: not-applicable lane requires a reason")
            if result and (result.get("attempted") or result.get("locator_results") or any(result.get(name, 0) for name in ("retrieved_count", "reviewed_count", "accepted_customer_voice_count"))):
                errors.append(f"{key}: capture result contradicts a not-applicable planned lane")
            row["execution_status"] = "not_applicable"
            finalized.append(row)
            continue
        supplied = set(planned.get("locators", []))
        reviewed_items = _index(planned.get("reviewed_locators", []), ("locator",), f"{key} reviewed locators", errors)
        reviewed = {locator[0] for locator in reviewed_items}
        for locator, item in reviewed_items.items():
            if not str(item.get("review_reason") or "").strip() or locator[0] not in supplied:
                errors.append(f"{key}/{locator[0]}: reviewed locator requires a reason and planned locator")
        if not supplied:
            gap(scope, "Applicable lane still requires locator discovery", "discovery_required")
            outcomes.append("pending")
        for locator in sorted(supplied - reviewed):
            gap({**scope, "locator": locator}, "Locator has no accepted review disposition", "review_pending")
            outcomes.append("pending")
        outcome = _outcome(result)
        outcomes.append(outcome)
        row["execution_status"] = outcome
        if outcome != "attempted":
            gap(scope, str((result or {}).get("failed_or_blocked") or "No completion result"), outcome)
        if result is None:
            finalized.append(row)
            continue
        counts, _ = _counts(result, str(key), errors, require_ids=False)
        if key[2] == "company_hosted_supplier_context" and counts[2]:
            errors.append(f"{key}: supplier context cannot count as accepted customer voice")
        by_locator = _index(result.get("locator_results", []), ("locator",), f"{key} locator_results", errors)
        for locator in {item[0] for item in by_locator} - reviewed:
            errors.append(f"{key}/{locator}: capture result from an unreviewed locator")
        totals = [0, 0, 0]
        accepted_here: set[str] = set()
        verified_results: list[dict[str, Any]] = []
        for locator in sorted(reviewed):
            item = by_locator.get((locator,))
            locator_outcome = _outcome(item)
            outcomes.append(locator_outcome)
            if locator_outcome != "attempted":
                gap({**scope, "locator": locator}, str((item or {}).get("failed_or_blocked") or "No completion result for locator"), locator_outcome)
            if item is None:
                continue
            locator_counts, ids = _counts(item, f"{key}/{locator}", errors)
            totals = [left + right for left, right in zip(totals, locator_counts)]
            accepted_here.update(ids)
            verified_results.append({**item, "execution_status": locator_outcome})
            if locator_counts[1] < locator_counts[0]:
                gap({**scope, "locator": locator}, "Retrieved observations remain unreviewed", "review_pending")
            if locator_outcome == "attempted" and not ids and key[2] != "company_hosted_supplier_context":
                gap({**scope, "locator": locator}, "No accepted customer voice from this source; no conclusion about absence of need", "no_accepted_voice")
        if counts != totals:
            errors.append(f"{key}: lane totals must equal the sum of per-locator totals")
        if "accepted_evidence_ids" in result:
            ids = result["accepted_evidence_ids"]
            if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids) or len(ids) != len(set(ids)) or set(ids) != accepted_here:
                errors.append(f"{key}: lane accepted_evidence_ids must equal the unique union of locator IDs")
        entity_ids.update(accepted_here)
        row.update({name: result[name] for name in ("attempted", "retrieved_count", "reviewed_count", "accepted_customer_voice_count", "failed_or_blocked", "sampling") if name in result})
        row.update({"locator_results": verified_results, "accepted_evidence_ids": sorted(accepted_here),
                    "unique_accepted_count": len(accepted_here)})
        finalized.append(row)

    if not plan.get("entity_count") and plan.get("analysis_contract", {}).get("entity_led_feedback") == "pending_entity_discovery":
        gap({"sampling_frame": "entity_led_feedback"}, "Verified entity discovery is pending; topic-led findings can still be reported", "pending_entity_discovery")
    all_ids = topic_ids | entity_ids
    execution = "complete" if outcomes and all(item != "pending" for item in outcomes) else "partial" if topic_attempted or any(item != "pending" for item in outcomes) else "not_started"
    coverage = "invalid" if errors else "partial" if gaps else "complete_for_declared_plan"
    claim = "blocked_invalid_input" if errors else "insufficient_evidence" if not all_ids else "pending_topic_discovery" if not topic_attempted else "scoped_synthesis_ready"
    status = "invalid" if errors else "insufficient_evidence" if not all_ids else "partial" if gaps or not topic_attempted else "complete"
    output = {"schema_version": 2, "status": status, "execution_status": execution, "coverage_status": coverage,
              "claim_status": claim, "topic_led_voc": topic, "source_matrix": finalized,
              "coverage_gaps": gaps, "errors": errors, "accepted_evidence_ids": sorted(all_ids),
              "unique_accepted_count": len(all_ids), "synthesis_allowed": claim == "scoped_synthesis_ready",
              "interpretation_boundary": "Coverage concerns declared sampling only, never market prevalence, author residence or problem validation. Partial findings must retain missing scopes."}
    return output, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        results = json.loads(Path(args.results).read_text(encoding="utf-8"))
        output, errors = validate(plan, results)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "error_count": len(errors), "out": str(out)}))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
