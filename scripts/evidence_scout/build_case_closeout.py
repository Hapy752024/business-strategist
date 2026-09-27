#!/usr/bin/env python3
"""Read-only, input-derived work queue for a registered Business case.

This is a navigation aid. The source plan, collection ledgers, reviews, coverage,
case manifest and publication receipts remain the authorities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from case_workspace import case_manifest, safe  # noqa: E402
from evidence_scout import validate_research_completion as checks  # noqa: E402


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a JSON object")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:16]


def _captures(root: Path, run: str, plan: dict) -> list[Path]:
    paths = [safe(root, run)] + [safe(root, row["run_dir"]) for row in plan.get("capture_inputs", [])]
    return [path / "evidence" if (path / "evidence/query_plan.json").is_file() else path
            for path in dict.fromkeys(paths)]


def build(root: Path, case_id: str) -> dict:
    root = Path(root).absolute()
    manifest_path = safe(root, f"cases/{case_id}/market_research/manifest.json")
    assignment = case_manifest(root, case_id).get("research_assignment")
    if not isinstance(assignment, dict):
        case_root = safe(root, f"cases/{case_id}")
        runs = sorted((case_root / "market_research/pain_points/runs").glob("*"))
        captures = []
        inputs = {str(manifest_path.relative_to(root)): _digest(manifest_path)}
        for run in runs:
            if not run.is_dir() or not (run / "query_plan.json").is_file():
                continue
            result = checks.validate_collection(root, run)
            records = [json.loads(line) for line in (run / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
                       if line.strip()] if (run / "evidence.jsonl").is_file() else []
            documents = sum(row.get("capture_unit") == "document" for row in records)
            captures.append({"run_dir": str(run.relative_to(root)), "collection_status": result["status"],
                             "missing_requirements": result["missing_requirements"],
                             "retained_records": len(records), "multi_speaker_documents": documents})
            for name in ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl"):
                path = run / name
                if path.is_file():
                    inputs[str(path.relative_to(root))] = _digest(path)
        items = [{"id": _id(case_id, "register-assignment"), "kind": "register_assignment",
                  "blocking": True, "reason": "No requested-scope research assignment or reviewed source plan is registered; collection alone cannot close the case",
                  "artifact": str(manifest_path.relative_to(root)), "completion_check": "assignment"}]
        if not captures:
            items.append({"id": _id(case_id, "collect"), "kind": "plan_and_collect",
                          "blocking": True, "reason": "No case-local captured query run exists",
                          "artifact": str(case_root.relative_to(root)), "completion_check": "collection"})
        for capture in captures:
            if capture["collection_status"] != "complete":
                items.append({"id": _id(case_id, capture["run_dir"]), "kind": "complete_capture",
                              "blocking": True, "reason": "; ".join(capture["missing_requirements"]),
                              "artifact": capture["run_dir"], "completion_check": "collection"})
            if capture["multi_speaker_documents"]:
                items.append({"id": _id(case_id, capture["run_dir"], "experience-extraction"),
                              "kind": "extract_and_review_experiences", "blocking": True,
                              "reason": f"{capture['multi_speaker_documents']} retained multi-speaker or unsegmented documents need located experience extraction and source-role review before customer claims",
                              "artifact": capture["run_dir"] + "/evidence.jsonl", "completion_check": "research"})
        fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        return {"case_id": case_id, "assignment_version": None,
                "checks": {"collection": "complete" if captures and all(c["collection_status"] == "complete" for c in captures) else "partial",
                           "assignment": "partial", "delivery": "partial"},
                "outcome": "work_in_progress", "closure_status": "in_progress", "captured_runs": captures,
                "input_fingerprint": fingerprint, "inputs": inputs, "items": items}
    studies = (assignment["studies"] if assignment.get("schema_version") == 2 else
               [{"run_dir": assignment["parent_run"], "source_plan_path": assignment["source_plan_path"],
                 "relation": "target"}])
    primary_owner = {row["capture_run"]: row["study_run"] for row in assignment.get("capture_owners", [])}
    items: list[dict] = []
    inputs: dict[str, str] = {str(manifest_path.relative_to(root)): _digest(manifest_path)}
    for study in studies:
        run = study["run_dir"]
        plan_path = safe(root, study["source_plan_path"])
        plan = _load(plan_path)
        inputs[study["source_plan_path"]] = _digest(plan_path)
        results_rel = run + "/customer-feedback/customer-feedback-results.json"
        results_path = safe(root, results_rel)
        results = _load(results_path) if results_path.is_file() else {}
        if results_path.is_file():
            inputs[results_rel] = _digest(results_path)
        pack = safe(root, run + "/customer-feedback")
        for name in ("source-review.json", "customer-feedback-coverage.json", "claim-ledger.json",
                     "customer-voc-synthesis.json", "evidence.jsonl"):
            path = pack / name
            if path.is_file():
                inputs[str(path.relative_to(root))] = _digest(path)
        source_review = _load(pack / "source-review.json") if (pack / "source-review.json").is_file() else {}
        reviewed_ids = {row.get("evidence_id") for row in source_review.get("reviews", [])
                        if isinstance(row, dict)}
        cells = {row.get("cell_id"): row for row in results.get("topic_led_voc", {}).get("cells", [])}
        query_reviews = {row.get("query_id"): row for cell in results.get("topic_led_voc", {}).get("cells", [])
                         for row in cell.get("query_reviews", []) if isinstance(row, dict)}
        planned_cells = {cell.get("cell_id"): cell for cell in plan.get("topic_matrix", [])}
        query_cells = {query: cell for cell in plan.get("topic_matrix", [])
                       for query in cell.get("query_ids", [])}
        for result in results.get("topic_led_voc", {}).get("cells", []):
            cell = planned_cells.get(result.get("cell_id"), result)
            for query in result.get("query_ids", []):
                query_cells.setdefault(query, cell)
        records: dict[str, dict[str, dict]] = {}
        outcomes: dict[str, set[str]] = {}
        query_sources: dict[str, set[str]] = {}
        raw_candidates: dict[str, dict[str, dict]] = {}
        unretained_counts: dict[str, dict[str, int]] = {}
        locator_queries: set[str] = set()
        for capture in _captures(root, run, plan):
            capture_rel = str((capture.parent if capture.name == "evidence" else capture).relative_to(root))
            for name in ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl"):
                path = capture / name
                if path.is_file():
                    inputs[str(path.relative_to(root))] = _digest(path)
            if not (capture / "summary.json").is_file():
                items.append({"id": _id(run, str(capture), "capture"), "kind": "complete_capture",
                              "study_run": run, "capture_run": str(capture.relative_to(root)),
                              "reason": "Capture summary is missing", "artifact": str((capture / "summary.json").relative_to(root)),
                              "completion_check": "collection"})
                continue
            summary = _load(capture / "summary.json")
            for provider_name, provider in summary.get("providers", {}).items():
                for row in provider.get("query_ledger", []):
                    if row.get("query_id") and row.get("scheduled"):
                        outcomes.setdefault(row["query_id"], set()).add(str(row.get("status") or "pending"))
                        unretained = max(0, int(row.get("returned_count") or 0) - len(row.get("record_ids") or []))
                        if unretained:
                            unretained_counts.setdefault(row["query_id"], {})[provider_name] = unretained
                raw_path = capture / "raw" / f"{provider_name}.json"
                if raw_path.is_file():
                    inputs[str(raw_path.relative_to(root))] = _digest(raw_path)
                    if provider_name == "reddit":
                        raw = _load(raw_path)
                        for search in raw.get("searches", []):
                            ident = search.get("query_id")
                            children = search.get("response", {}).get("body", {}).get("data", {}).get("children", [])
                            for child in children:
                                data = child.get("data", {})
                                candidate_id = str(data.get("id") or "")
                                if ident and candidate_id:
                                    permalink = data.get("permalink") or ""
                                    raw_candidates.setdefault(ident, {})[candidate_id] = {
                                        "provider": "reddit", "candidate_id": candidate_id,
                                        "source_url": "https://www.reddit.com" + permalink if permalink.startswith("/") else permalink,
                                        "title": data.get("title"), "capture_run": capture_rel}
            manual = capture / "manual-captures.json"
            if manual.is_file():
                inputs[str(manual.relative_to(root))] = _digest(manual)
                for row in _load(manual).get("captures", []):
                    outcomes.setdefault(row["query_id"], set()).add("manual_capture")
            for name in ("evidence.jsonl", "irrelevant.jsonl"):
                path = capture / name
                if not path.is_file():
                    continue
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    for membership in record.get("discovery_memberships", []):
                        query = membership.get("query_id") if isinstance(membership, dict) else None
                        if query:
                            records.setdefault(query, {})[record["evidence_id"]] = {
                                "evidence_id": record["evidence_id"], "source_url": record.get("source_url"),
                                "capture_run": str(capture.relative_to(root))}
            query_plan = _load(capture / "query_plan.json")
            queries = (query_plan.get("input_plan") or {}).get("queries")
            if queries is None:
                queries = [row for rows in query_plan.get("provider_schedules", {}).values() for row in rows]
            for query in queries:
                ident = query.get("query_id")
                if ident and query.get("intent") == "entity_locator_discovery":
                    locator_queries.add(ident)
                elif ident and query.get("sampling_frame") != "entity_led_feedback":
                    query_cells.setdefault(ident, {"cell_id": "unassigned", "locale": query.get("locale")})
                    outcomes.setdefault(ident, set())
                    query_sources.setdefault(ident, set()).add(capture_rel)
        for ident, cell in sorted(query_cells.items()):
            if (assignment.get("schema_version") == 2 and study["relation"] != "target"
                    and query_sources.get(ident)
                    and all(primary_owner.get(source) not in {None, run} for source in query_sources[ident])):
                continue  # Historical shared binding; its target study owns query closeout.
            result = cells.get(cell.get("cell_id"), {})
            review = next((row for row in result.get("query_reviews", []) if row.get("query_id") == ident), None)
            attempted = ident in result.get("query_ids", []) and result.get("attempted") is True
            v4 = plan.get("execution_contract_version") == 4
            if not attempted:
                reason, kind = "No attempted result cell binds this captured query", "reconcile_query"
            elif v4 and review is None:
                reason, kind = "Query has no reviewed disposition", "review_query"
            elif v4 and review.get("status") == "refine":
                reason, kind = review["next_observation"], "refine_query"
            elif v4 and review.get("status") in {"primary_research_needed", "access_limited"}:
                reason, kind = review["next_observation"], "next_stage_limitation"
            elif not v4 and result.get("search_resolution", {}).get("status") == "refine":
                reason = result["search_resolution"]["next_observation"]
                kind = "refine_query"
            elif not v4 and result.get("search_resolution", {}).get("status") in {"primary_research_needed", "access_limited"}:
                reason = result["search_resolution"]["next_observation"]
                kind = "next_stage_limitation"
            elif not v4 and not result.get("accepted_evidence_ids") and not result.get("search_resolution"):
                reason, kind = "Cell has no accepted voice or reviewed low-yield resolution", "review_query"
            else:
                continue
            candidates = sorted(records.get(ident, {}).values(), key=lambda item: item["evidence_id"])
            items.append({"id": _id(run, str(cell.get("cell_id")), ident), "kind": kind,
                          "study_run": run, "relation": study["relation"],
                          "blocking": study["relation"] == "target" and kind != "next_stage_limitation",
                          "cell_id": cell.get("cell_id"),
                          "locale": cell.get("locale"), "query_id": ident, "provider_outcomes": sorted(outcomes.get(ident, [])),
                          "candidates": candidates, "review_status": review.get("status") if review else None,
                          "reason": reason, "artifact": results_rel, "completion_check": "research"})
        for ident, providers in sorted(unretained_counts.items()):
            if ident in locator_queries:
                continue  # Exact locator candidates are reconciled by the v4 lane resolution.
            if assignment.get("schema_version") == 2 and study["relation"] != "target" and all(
                    primary_owner.get(source) not in {None, run} for source in query_sources.get(ident, set())):
                continue
            declared = {row.get("provider"): row for row in query_reviews.get(ident, {}).get("raw_result_reviews", [])
                        if isinstance(row, dict)}
            if set(providers) <= set(declared) and not any(
                    candidate.get("disposition") == "promote" for row in declared.values()
                    for candidate in row.get("candidates", [])):
                continue
            items.append({"id": _id(run, "unretained", ident), "kind": "review_unretained_results",
                          "blocking": study["relation"] == "target" and plan.get("execution_contract_version") == 4,
                          "study_run": run,
                          "relation": study["relation"], "query_id": ident,
                          "unretained_counts": providers,
                          "raw_candidates": sorted(raw_candidates.get(ident, {}).values(),
                                                   key=lambda item: (item["provider"], item["candidate_id"])),
                          "reason": "Provider returned candidates that were not retained as evidence; inspect and disposition raw results",
                          "artifact": results_rel, "completion_check": "research"})
        selected_ids = set()
        for cell in results.get("topic_led_voc", {}).get("cells", []):
            selected_ids.update(cell.get("accepted_evidence_ids", []))
            selected_ids.update(ident for review in cell.get("query_reviews", [])
                                for ident in review.get("reviewed_ids", []))
            sample = cell.get("sampling")
            if isinstance(sample, dict):
                selected_ids.update(sample.get("selected_ids", []))
        for lane in results.get("source_results", []):
            for locator in lane.get("locator_results", []):
                selected_ids.update(locator.get("accepted_evidence_ids", []))
                sample = locator.get("sampling")
                if isinstance(sample, dict):
                    selected_ids.update(sample.get("selected_ids", []))
        record_index = {ident: row for query_records in records.values() for ident, row in query_records.items()}
        for ident in sorted(selected_ids - reviewed_ids):
            items.append({"id": _id(run, "selected-review", ident), "kind": "review_selected_source",
                          "blocking": True, "study_run": run, "relation": study["relation"],
                          "evidence_id": ident, "candidate": record_index.get(ident),
                          "reason": "Selected or accepted evidence ID has no source-review decision",
                          "artifact": str((pack / "source-review.json").relative_to(root)),
                          "completion_check": "research"})
        source_results = {(row.get("entity_id"), row.get("locale"), row.get("source_lane")): row
                          for row in results.get("source_results", [])}
        for lane in plan.get("source_matrix", []):
            key = tuple(lane.get(name) for name in ("entity_id", "locale", "source_lane"))
            result = source_results.get(key, {})
            if lane.get("applicable") is False:
                if plan.get("execution_contract_version") != 4 or lane.get("applicability_review"):
                    continue
                kind, reason = "review_applicability", "Not-applicable lane lacks source-bound review"
            elif lane.get("locator_resolution"):
                resolution = lane["locator_resolution"]
                items.append({"id": _id(run, *map(str, key), "locator-limitation"),
                              "kind": "next_stage_limitation", "study_run": run,
                              "relation": study["relation"], "blocking": False,
                              "entity_id": key[0], "locale": key[1], "source_lane": key[2],
                              "reason": resolution["reason"],
                              "next_observation": resolution["next_observation"],
                              "artifact": study["source_plan_path"], "completion_check": "research"})
                continue
            elif not lane.get("reviewed_locators"):
                kind, reason = "discover_entity_locator", "Applicable entity lane lacks a reviewed exact locator"
            elif not result.get("attempted"):
                kind, reason = "capture_entity_lane", "Reviewed entity lane lacks attempted capture/results"
            else:
                continue
            items.append({"id": _id(run, *map(str, key)), "kind": kind, "study_run": run,
                          "relation": study["relation"], "blocking": study["relation"] == "target",
                          "entity_id": key[0], "locale": key[1],
                          "source_lane": key[2], "reason": reason, "artifact": study["source_plan_path"]
                          if kind != "capture_entity_lane" else results_rel, "completion_check": "research"})
        if (plan.get("analysis_contract", {}).get("entity_led_feedback") == "pending_entity_discovery"
                and not plan.get("entity_count")):
            items.append({"id": _id(run, "entity-discovery"), "kind": "discover_entity",
                          "study_run": run, "relation": study["relation"],
                          "blocking": study["relation"] == "target",
                          "reason": "Verified entity discovery and applicable feedback lanes remain pending",
                          "artifact": study["source_plan_path"], "completion_check": "research"})
    anchor = safe(root, assignment["parent_run"])
    validation = {kind: getattr(checks, "validate_" + kind)(root, anchor)
                  for kind in ("assignment", "delivery")}
    checks_out = {kind: result["status"] for kind, result in validation.items()}
    for check in ("assignment", "delivery"):
        for reason in validation[check].get("missing_requirements", []):
            if check == "delivery" and reason in validation["assignment"].get("missing_requirements", []):
                continue
            items.append({"id": _id(case_id, check, str(reason)), "kind": "validator_requirement",
                          "blocking": True, "reason": reason, "artifact": assignment["source_plan_path"]
                          if check == "assignment" else f"cases/{case_id}/case_insights.md",
                          "completion_check": check,
                          "next_actions": validation[check].get("next_actions", [])})
    for gap in validation["delivery"].get("open_gaps", []):
        if gap.get("status") in {"handoff_required", "resolution_required", "refinement_required", "failed_or_blocked"}:
            items.append({"id": _id(case_id, "delivery-gap", json.dumps(gap, sort_keys=True)),
                          "kind": "validator_gap", "blocking": True, "scope": gap,
                          "reason": gap.get("reason", "Unresolved research gap"),
                          "artifact": assignment["source_plan_path"], "completion_check": "research"})
    if checks_out["assignment"] == "complete" and checks_out["delivery"] != "complete":
        items.append({"id": _id(case_id, "final-publication"), "kind": "review_and_publish_final_insights",
                      "reason": "Research assignment is closed but exact final case-insights review or publication remains",
                      "artifact": f"cases/{case_id}/case_insights.md", "completion_check": "delivery"})
    cm = case_manifest(root, case_id)
    try:
        from validate_case_insights import current_status
        insight_current = current_status(root, case_id).get("status") == "current"
    except (OSError, ValueError, KeyError):
        insight_current = False
    evidence = checks.initial_case_evidence(root, case_id)
    research = checks.validate_research(root, anchor)
    if (cm.get("appraisal_contract_version") == 2
            and (root / f"cases/{case_id}/business-case.md").is_file()
            and evidence.get("status") == "eligible" and insight_current
            and cm.get("insights", {}).get("assessment_revision") == cm.get("assessment_revision")):
        outcome = "provisional_plan_published"
    elif checks_out["delivery"] == "complete" and research.get("claim_status") == "insufficient_evidence":
        outcome = "evidence_insufficient"
    elif (checks_out["assignment"] == "complete" and research["status"] == "partial"
          and not research["missing_requirements"] and any(item["kind"] == "refine_query" for item in items)):
        outcome = "more_targeted_research_required"
    else:
        outcome = "work_in_progress"
    blocking = any(item.get("blocking") for item in items)
    closure_status = ("closed" if checks_out["delivery"] == "complete" and not blocking
                      and outcome in {"provisional_plan_published", "evidence_insufficient"}
                      else "interim" if outcome != "work_in_progress" else "in_progress")
    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    return {"case_id": case_id, "assignment_version": assignment["schema_version"],
            "outcome": outcome, "closure_status": closure_status,
            "checks": checks_out, "input_fingerprint": fingerprint, "inputs": inputs,
            "items": sorted(items, key=lambda item: (item.get("study_run", ""), item["kind"], item["id"]))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-terminal", action="store_true",
                        help="Exit 1 unless delivery is complete and blocking case work is closed")
    args = parser.parse_args()
    try:
        packet = build(args.workspace, args.case)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered if args.json else json.dumps({"case_id": packet["case_id"], "checks": packet["checks"],
                                                  "outcome": packet["outcome"], "closure_status": packet["closure_status"],
                                                  "item_count": len(packet["items"]),
                                                  "input_fingerprint": packet["input_fingerprint"]}))
    return 1 if args.require_terminal and packet["closure_status"] != "closed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
