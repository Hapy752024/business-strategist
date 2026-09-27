"""Behavioral checks for the shared research acceptance boundary."""
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from scripts import case_workspace as cases
from scripts.evidence_scout import validate_research_completion as checks
from scripts.evidence_scout.build_case_closeout import build as build_closeout
from scripts.evidence_scout.finalize_customer_feedback import validate as finalize_feedback
from scripts.evidence_scout.workspace import capture_run_scope, resume_from_last_gate, update_run_manifest, update_stage


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def collected_run(workspace: Path, *, records=None, status="ok") -> Path:
    run = workspace / "market_research/pain_points/runs/executed"
    run.mkdir(parents=True)
    capture_run_scope(run, workspace)
    plan = {"input_plan": None, "input_plan_digest": None,
            "provider_schedules": {"reddit": [{"query_id": "q1", "query": "PKV GKV Erfahrungen", "scheduled": True}]}}
    write(run / "query_plan.json", plan)
    write(run / "raw/reddit.json", {"response": {"ok": True, "body": {"data": {"children": []}}}})
    rows = records or []
    (run / "evidence.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    (run / "irrelevant.jsonl").write_text("")
    query = {"query_id": "q1", "query": "PKV GKV Erfahrungen", "scheduled": True, "attempted": True,
             "status": status, "returned_count": len(rows)}
    write(run / "summary.json", {"query_plan_digest": None, "providers_requested": ["reddit"],
                                    "providers": {"reddit": {"status": status, "query_ledger": [query]}},
                                    "record_count": len(rows), "irrelevant_count": 0,
                                    "collection_complete": True, "remaining_tasks": []})
    write(run / "run-checkpoint.json", {"query_plan_digest": hashlib.sha256(
        json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "provider_attempts": {"reddit": [{"status": status, "finished_at": "2026-09-25T00:00:00Z"}]}})
    return run


def case(tmp_path):
    root = tmp_path / "project"
    cases.initialize(root, "Research fixture")
    cases.add_case(root, "probe", "Probe")
    return root / "cases/probe"


def test_nonempty_file_cannot_pass_collection_without_execution(tmp_path):
    workspace = case(tmp_path)
    fake = workspace / "market_research/report.md"
    fake.write_text("No research collected.\n")
    before = (workspace / "market_research/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="run_dir"):
        update_stage(workspace, "evidence_collection", status="passed", gate_result="pass",
                     artifacts=[fake], expected_assessment_revision=1)
    assert (workspace / "market_research/manifest.json").read_bytes() == before


def test_valid_empty_capture_can_complete_collection_without_business_claim(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    result = checks.validate_collection(workspace, run)
    assert result["status"] == "complete" and result["claim_status"] == "not_reviewed"
    update_stage(workspace, "evidence_collection", run_dir=run, status="passed", gate_result="pass",
                 artifacts=[run / "summary.json"], expected_assessment_revision=1)
    manifest = json.loads((workspace / "market_research/manifest.json").read_text())
    receipt = manifest["stages"]["evidence_collection"]["validation_receipt"]
    assert receipt["kind"] == "evidence_collection"
    assert manifest["stages"].get("problem_validation", {}).get("status") != "passed"


def test_incomplete_or_tampered_capture_cannot_pass_and_keeps_manifest(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    summary = json.loads((run / "summary.json").read_text())
    summary["providers"]["reddit"]["query_ledger"][0]["attempted"] = False
    write(run / "summary.json", summary)
    assert checks.validate_collection(workspace, run)["status"] == "partial"
    before = (workspace / "market_research/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="not executed"):
        update_stage(workspace, "evidence_collection", run_dir=run, status="passed", gate_result="pass",
                     artifacts=[run / "summary.json"], expected_assessment_revision=1)
    assert (workspace / "market_research/manifest.json").read_bytes() == before


def test_changed_plan_invalidates_execution(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    plan = json.loads((run / "query_plan.json").read_text())
    plan["provider_schedules"]["reddit"].clear()
    write(run / "query_plan.json", plan)
    assert checks.validate_collection(workspace, run)["status"] == "invalid"


def test_query_ledger_cannot_claim_unretained_record(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    plan = json.loads((run / "query_plan.json").read_text())
    plan["input_plan"] = {"queries": [{"query_id": "q1", "query": "PKV GKV Erfahrungen"}]}
    plan["input_plan_digest"] = hashlib.sha256(json.dumps(plan["input_plan"], sort_keys=True,
        ensure_ascii=False).encode()).hexdigest()
    write(run / "query_plan.json", plan)
    checkpoint = json.loads((run / "run-checkpoint.json").read_text())
    checkpoint["query_plan_digest"] = hashlib.sha256(json.dumps(plan, sort_keys=True,
        ensure_ascii=False).encode()).hexdigest()
    write(run / "run-checkpoint.json", checkpoint)
    summary = json.loads((run / "summary.json").read_text())
    summary["query_plan_digest"] = plan["input_plan_digest"]
    summary["providers"]["reddit"]["query_ledger"][0]["record_ids"] = ["invented"]
    write(run / "summary.json", summary)
    result = checks.validate_collection(workspace, run)
    assert result["status"] == "invalid" and "retained query membership" in result["missing_requirements"][0]


def test_query_ledger_cannot_omit_captured_record(tmp_path):
    workspace = case(tmp_path)
    record = {"evidence_id": "e1", "source_url": "https://forum.test/1",
              "discovery_memberships": [{"query_id": "q1"}]}
    run = collected_run(workspace, records=[record])
    plan = json.loads((run / "query_plan.json").read_text())
    plan["input_plan"] = {"queries": [{"query_id": "q1", "query": "PKV GKV Erfahrungen"}]}
    plan["input_plan_digest"] = hashlib.sha256(json.dumps(plan["input_plan"], sort_keys=True,
        ensure_ascii=False).encode()).hexdigest()
    write(run / "query_plan.json", plan)
    checkpoint = json.loads((run / "run-checkpoint.json").read_text())
    checkpoint["query_plan_digest"] = hashlib.sha256(json.dumps(plan, sort_keys=True,
        ensure_ascii=False).encode()).hexdigest()
    write(run / "run-checkpoint.json", checkpoint)
    summary = json.loads((run / "summary.json").read_text())
    summary["query_plan_digest"] = plan["input_plan_digest"]
    summary["providers"]["reddit"]["query_ledger"][0]["record_ids"] = []
    write(run / "summary.json", summary)
    result = checks.validate_collection(workspace, run)
    assert result["status"] == "invalid" and "omits retained" in result["missing_requirements"][0]


def test_review_and_delivery_cannot_be_inferred_from_collection(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    assert checks.validate_research(workspace, run)["status"] == "partial"
    assert "customer-feedback-source-plan.json" in checks.validate_research(workspace, run)["missing_requirements"]
    assert checks.validate_delivery(workspace, run)["status"] == "partial"


def test_registered_case_assignment_requires_all_locales_and_linked_captures(tmp_path):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    parent = collected_run(workspace)
    extra = workspace / "market_research/pain_points/runs/second-locale"
    shutil.copytree(parent, extra)
    parent_rel = str(parent.relative_to(root))
    extra_rel = str(extra.relative_to(root))
    decision = "Do target payers repeatedly choose this bill route after all fees?"
    segment = "Direct bill payer"
    source_plan = parent / "customer-feedback/customer-feedback-source-plan.json"
    write(source_plan, {"execution_contract_version": 3, "research_design": {"decision": decision},
                        "customer_segment": segment, "locales": ["FR:fr"],
                        "topic_matrix": [{"cell_id": "fr", "locale": "FR:fr"}], "capture_inputs": []})
    write(parent / "customer-feedback/customer-feedback-results.json", {"topic_led_voc": {"cells": [
        {"cell_id": "fr", "attempted": True, "query_ids": ["q1"], "retrieved_count": 0,
         "reviewed_count": 0, "accepted_count": 0, "accepted_evidence_ids": []}]}, "source_results": []})
    assignment = {"schema_version": 1, "decision": decision, "customer_segment": segment,
                  "locales": ["FR:fr", "ES:es"], "parent_run": parent_rel,
                  "capture_runs": [extra_rel], "source_plan_path": str(source_plan.relative_to(root))}
    cases.register_research_assignment(root, "probe", assignment, "assignment-test-1", "Freeze the whole requested scope")
    result = checks.validate_assignment(root, parent)
    assert result["status"] == "partial"
    assert any("ES:es" in item for item in result["missing_requirements"])
    assert any("not linked" in item for item in result["missing_requirements"])
    assert result["work_items"]
    assert all(item["completion_check"] == "assignment" for item in result["work_items"])
    assert checks.validate_delivery(root, parent)["status"] == "partial"

    plan = json.loads(source_plan.read_text())
    plan["locales"].append("ES:es")
    plan["topic_matrix"].append({"cell_id": "es", "locale": "ES:es"})
    plan["capture_inputs"] = [{"run_dir": extra_rel, "artifact_digests": {
        name: hashlib.sha256((extra / name).read_bytes()).hexdigest()
        for name in ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl")}}]
    write(source_plan, plan)
    assert checks.validate_assignment(root, parent)["status"] == "complete"
    (extra / "evidence.jsonl").write_text("\n")  # count stays zero, content digest changes
    result = checks.validate_assignment(root, parent)
    assert result["status"] == "partial"
    assert any("digest changed" in item for item in result["missing_requirements"])


def test_v2_assignment_composes_narrow_parent_and_target_study_with_shared_capture(tmp_path, monkeypatch):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    parent = collected_run(workspace)
    capture = workspace / "market_research/pain_points/runs/shared-capture"
    shutil.copytree(parent, capture)
    target = workspace / "market_research/pain_points/runs/target-study"
    target.mkdir(parents=True)
    parent_rel, capture_rel, target_rel = (str(path.relative_to(root)) for path in (parent, capture, target))
    decision = "Do French target payers repeat this route after all fees?"
    segment = "French direct business bill payers"
    parent_plan = parent / "customer-feedback/customer-feedback-source-plan.json"
    target_plan = target / "customer-feedback/customer-feedback-source-plan.json"
    binding = {"run_dir": capture_rel, "artifact_digests": {
        name: hashlib.sha256((capture / name).read_bytes()).hexdigest()
        for name in ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl")}}
    write(parent_plan, {"execution_contract_version": 3, "customer_segment": "Spanish FX card users",
                        "research_design": {"decision": "Different narrow question"},
                        "locales": ["FR:fr"], "topic_matrix": [{"cell_id": "legacy", "locale": "FR:fr"}],
                        "capture_inputs": [binding]})
    write(target_plan, {"execution_contract_version": 4, "customer_segment": segment,
                        "research_design": {"decision": decision},
                        "locales": ["FR:fr"], "topic_matrix": [{"cell_id": "target-fr", "locale": "FR:fr"}],
                        "capture_inputs": [binding], "source_matrix": []})
    write(target / "customer-feedback/customer-feedback-results.json", {
        "topic_led_voc": {"cells": [{"cell_id": "target-fr", "attempted": True, "query_ids": ["q1"],
                                     "query_reviews": [{"query_id": "q1", "status": "reviewed"}]}]}})
    assignment = {"schema_version": 2, "decision": decision, "customer_segment": segment,
                  "locales": ["FR:fr"], "parent_run": parent_rel, "capture_runs": [capture_rel],
                  "source_plan_path": str(parent_plan.relative_to(root)),
                  "studies": [{"run_dir": rel, "source_plan_path": str(path.relative_to(root)),
                               "source_plan_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                               "relation": relation, "applicability": "Retain the exact original study scope for comparison."}
                              for rel, path, relation in ((parent_rel, parent_plan, "adjacent"),
                                                          (target_rel, target_plan, "target"))],
                  "capture_owners": [{"capture_run": capture_rel, "study_run": target_rel}],
                  "overlap_reviews": [],
                  "coverage_cells": [{"question": "Does the target payer have a real bill?", "locale": "FR:fr",
                                      "frame": "topic_led_voc", "study_run": target_rel, "cell_id": "target-fr"}]}
    cases.register_research_assignment(root, "probe", assignment, "v2-assignment", "Compose reviewed study scopes")
    monkeypatch.setattr(checks, "validate_research", lambda _root, run: {
        "status": "complete" if run == target else "partial", "inputs": {},
        "claim_status": "scoped_synthesis_ready"})
    assert checks.validate_assignment(root, parent)["status"] == "complete"
    absolute_delivery = checks.validate_delivery(root, parent)
    relative_delivery = checks.validate_delivery(Path(os.path.relpath(root)), Path(os.path.relpath(parent)))
    assert relative_delivery["status"] == absolute_delivery["status"]
    assert relative_delivery["missing_requirements"] == absolute_delivery["missing_requirements"]
    assert "case_insights.md is missing or stale" in relative_delivery["missing_requirements"]
    shared_url = "https://forum.test/one-original-post"
    for run in (parent, target):
        pack = run / "customer-feedback"
        (pack / "evidence.jsonl").write_text(json.dumps({"evidence_id": "same-post",
                                                      "source_url": shared_url}) + "\n")
        write(pack / "source-review.json", {"reviews": [{"evidence_id": "same-post",
                                                      "source_url": shared_url, "status": "accepted"}]})
    result = checks.validate_assignment(root, parent)
    assert result["status"] == "partial"
    assert any("dedupe/conflict review" in item for item in result["missing_requirements"])
    assignment["overlap_reviews"] = [{"source_url": shared_url,
        "study_runs": sorted([parent_rel, target_rel]), "disposition": "same_incident",
        "reviewer": "Independent reviewer", "reason": "Both packs use the same original customer post; count once."}]
    cases.register_research_assignment(root, "probe", assignment, "v2-overlap", "Count shared original once")
    result = checks.validate_assignment(root, parent)
    assert result["status"] == "complete"
    assert result["shared_source_overlaps"][0]["count_once"] is True
    assignment["coverage_cells"][0]["study_run"] = parent_rel
    cases.register_research_assignment(root, "probe", assignment, "v2-bad-coverage", "Probe narrow coverage")
    result = checks.validate_assignment(root, parent)
    assert result["status"] == "partial"
    assert any("narrow/context study" in item for item in result["missing_requirements"])
    assignment["coverage_cells"][0]["study_run"] = target_rel
    changed = json.loads(parent_plan.read_text())
    changed["capture_inputs"].append({**binding, "run_dir": "cases/other-case/market_research/pain_points/runs/cross-case"})
    write(parent_plan, changed)
    assignment["studies"][0]["source_plan_sha256"] = hashlib.sha256(parent_plan.read_bytes()).hexdigest()
    cases.register_research_assignment(root, "probe", assignment, "v2-bad-capture", "Probe cross-case binding")
    result = checks.validate_assignment(root, parent)
    assert result["status"] == "partial"
    assert any("cross-case capture" in item for item in result["missing_requirements"])


def test_closeout_queue_is_read_only_and_points_to_exact_unreviewed_query(tmp_path):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    record = {"evidence_id": "e1", "source_url": "https://forum.test/payer/1",
              "discovery_memberships": [{"query_id": "q1"}]}
    run = collected_run(workspace, records=[record])
    rel = str(run.relative_to(root))
    plan = run / "customer-feedback/customer-feedback-source-plan.json"
    write(plan, {"execution_contract_version": 4, "customer_segment": "Direct payer",
                 "research_design": {"decision": "Does the payer repeat this route after fees?"},
                 "locales": ["FR:fr"], "topic_matrix": [{"cell_id": "fr", "locale": "FR:fr"}],
                 "source_matrix": [], "capture_inputs": []})
    results = run / "customer-feedback/customer-feedback-results.json"
    write(results, {"topic_led_voc": {"cells": [{"cell_id": "fr", "attempted": True,
        "query_ids": ["q1"], "retrieved_count": 1, "reviewed_count": 0,
        "accepted_count": 0, "accepted_evidence_ids": []}]}, "source_results": []})
    assignment = {"schema_version": 1, "decision": "Does the payer repeat this route after fees?",
                  "customer_segment": "Direct payer", "locales": ["FR:fr"], "parent_run": rel,
                  "capture_runs": [], "source_plan_path": str(plan.relative_to(root))}
    cases.register_research_assignment(root, "probe", assignment, "queue-fixture", "Register exact queue scope")
    before = {path: path.read_bytes() for path in (plan, results, run / "evidence.jsonl")}
    packet = build_closeout(root, "probe")
    item = next(row for row in packet["items"] if row.get("query_id") == "q1")
    assert item["kind"] == "review_query"
    assert item["candidates"] == [{"evidence_id": "e1", "source_url": "https://forum.test/payer/1",
                                   "capture_run": rel}]
    assert all(path.read_bytes() == value for path, value in before.items())
    source_review = run / "customer-feedback/source-review.json"
    write(source_review, {"reviews": []})
    awaiting_review = build_closeout(root, "probe")
    assert awaiting_review["input_fingerprint"] != packet["input_fingerprint"]
    assert any(row["kind"] == "review_selected_source" and row["evidence_id"] == "e1"
               for row in awaiting_review["items"]) is False  # Not selected yet.
    result = json.loads(results.read_text())
    result["topic_led_voc"]["cells"][0]["accepted_evidence_ids"] = ["e1"]
    write(results, result)
    selected = build_closeout(root, "probe")
    assert any(row["kind"] == "review_selected_source" and row["evidence_id"] == "e1"
               for row in selected["items"])
    write(source_review, {"reviews": [{"evidence_id": "e1", "decision": "rejected"}]})
    reviewed = build_closeout(root, "probe")
    assert reviewed["input_fingerprint"] != selected["input_fingerprint"]
    assert not any(row["kind"] == "review_selected_source" and row["evidence_id"] == "e1"
               for row in reviewed["items"])


def test_closeout_does_not_route_entity_locator_search_to_topic_cell(tmp_path):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    run = collected_run(workspace)
    query_plan_path = run / "query_plan.json"
    query_plan = json.loads(query_plan_path.read_text())
    query_plan["provider_schedules"]["reddit"].append({
        "query_id": "locator-only", "query": "site:trustpilot.com Product Spain",
        "intent": "entity_locator_discovery", "scheduled": True})
    write(query_plan_path, query_plan)
    summary_path = run / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["providers"]["reddit"]["query_ledger"].append({
        "query_id": "locator-only", "query": "site:trustpilot.com Product Spain",
        "scheduled": True, "attempted": True, "status": "ok", "returned_count": 0})
    write(summary_path, summary)
    plan_path = run / "customer-feedback/customer-feedback-source-plan.json"
    write(plan_path, {"execution_contract_version": 4, "customer_segment": "Direct payer",
                      "research_design": {"decision": "Does a payer repeat this route after fees?"},
                      "locales": ["FR:fr"], "topic_matrix": [{"cell_id": "fr", "locale": "FR:fr"}],
                      "source_matrix": [], "capture_inputs": []})
    write(run / "customer-feedback/customer-feedback-results.json",
          {"topic_led_voc": {"cells": [{"cell_id": "fr", "attempted": True,
            "query_ids": ["q1"], "retrieved_count": 0, "reviewed_count": 0,
            "accepted_count": 0, "accepted_evidence_ids": []}]}, "source_results": []})
    rel = str(run.relative_to(root))
    assignment = {"schema_version": 1, "decision": "Does a payer repeat this route after fees?",
                  "customer_segment": "Direct payer", "locales": ["FR:fr"], "parent_run": rel,
                  "capture_runs": [], "source_plan_path": str(plan_path.relative_to(root))}
    cases.register_research_assignment(root, "probe", assignment, "queue-locator", "Register locator-only queue scope")
    packet = build_closeout(root, "probe")
    assert not any(item.get("query_id") == "locator-only" and item["kind"] == "reconcile_query"
                   for item in packet["items"])


def test_v4_query_review_must_match_exact_captured_membership(tmp_path, monkeypatch):
    workspace = case(tmp_path)
    record = {"evidence_id": "e1", "source_url": "https://forum.test/payer/1",
              "discovery_memberships": [{"query_id": "q1"}]}
    run = collected_run(workspace, records=[record])
    pack = run / "customer-feedback"
    plan = {"execution_contract_version": 4, "customer_segment": "Direct payer", "locales": ["FR:fr"],
            "entity_count": 0, "analysis_contract": {"entity_led_feedback": "not_applicable"},
            "topic_matrix": [{"cell_id": "fr", "locale": "FR:fr"}], "source_matrix": [],
            "capture_inputs": []}
    review = {"query_id": "q1", "status": "reviewed", "record_ids": ["e1"], "reviewed_ids": ["e1"],
              "provider_outcomes": {"reddit": "ok"},
              "reason": "The exact original account was inspected for payer role.",
              "next_observation": "Check the following bill for repeat behavior.", "reviewer": "Analyst"}
    results = {"topic_led_voc": {"cells": [{"cell_id": "fr", "attempted": True,
        "query_ids": ["q1"], "retrieved_document_ids": ["e1"], "retrieved_evidence_ids": ["e1"],
        "retrieved_count": 1, "reviewed_count": 1, "accepted_count": 1,
        "accepted_evidence_ids": ["e1"], "query_reviews": [review]}]}, "source_results": []}
    write(pack / "customer-feedback-source-plan.json", plan)
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    (pack / "evidence.jsonl").write_text(json.dumps(record) + "\n")
    write(pack / "source-review.json", {"reviews": [{"evidence_id": "e1", "segment_relation": "target"}]})
    write(pack / "customer-voc-synthesis.json", {})
    write(pack / "claim-ledger.json", {})
    monkeypatch.setattr(checks.subprocess, "run", lambda *_args, **_kwargs: type("R", (), {
        "returncode": 0, "stdout": "", "stderr": ""})())
    assert checks.validate_research(workspace, run)["status"] == "complete"
    results["topic_led_voc"]["cells"][0]["query_reviews"][0]["record_ids"] = []
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    actual = checks.validate_research(workspace, run)
    assert actual["status"] == "invalid"
    assert "topic query q1" in actual["missing_requirements"][0]
    results["topic_led_voc"]["cells"][0]["query_reviews"][0]["record_ids"] = ["e1"]
    capture_plan = json.loads((run / "query_plan.json").read_text())
    capture_plan["provider_schedules"]["brave_search"] = [{"query_id": "q1",
        "query": "PKV GKV Erfahrungen", "scheduled": True}]
    write(run / "query_plan.json", capture_plan)
    checkpoint = json.loads((run / "run-checkpoint.json").read_text())
    checkpoint["query_plan_digest"] = hashlib.sha256(json.dumps(capture_plan, sort_keys=True,
        ensure_ascii=False).encode()).hexdigest()
    checkpoint["provider_attempts"]["brave_search"] = [{"status": "failed", "finished_at": "2026-09-25T00:00:00Z"}]
    write(run / "run-checkpoint.json", checkpoint)
    summary = json.loads((run / "summary.json").read_text())
    summary["providers_requested"].append("brave_search")
    summary["providers"]["brave_search"] = {"status": "failed", "query_ledger": [{
        "query_id": "q1", "query": "PKV GKV Erfahrungen", "scheduled": True,
        "attempted": True, "status": "failed", "returned_count": 0}]}
    write(run / "summary.json", summary)
    assert checks.validate_collection(workspace, run)["status"] == "complete"
    assert checks.validate_collection(workspace, run)["open_gaps"]
    results["topic_led_voc"]["cells"][0]["query_reviews"][0]["provider_outcomes"] = {
        "reddit": "ok", "brave_search": "failed"}
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    actual = checks.validate_research(workspace, run)
    assert actual["status"] == "invalid"  # One successful provider cannot erase the failed route.
    results["topic_led_voc"]["cells"][0]["query_reviews"][0]["status"] = "access_limited"
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    actual = checks.validate_research(workspace, run)
    assert actual["status"] == "complete"
    assert any(gap.get("sampling_frame") == "collection" and gap["status"] == "inaccessible"
               for gap in actual["open_gaps"])


def test_collection_quality_notes_do_not_mask_or_create_provider_failures():
    collection = {"open_gaps": [
        "remaining source or review work: {'provider': 'evidence_quality', 'action': 'zero relevant results'}",
        "brave_search/q2: failed"]}
    results = {"topic_led_voc": {"cells": [{"query_reviews": [
        {"query_id": "q2", "status": "access_limited"}]}]}}
    gaps = checks._collection_coverage_gaps(collection, {"execution_contract_version": 4}, results,
                                            {"q1": {"reddit": "ok"}, "q2": {"brave_search": "failed"}})
    assert gaps[0]["status"] == "collection_observation"
    assert gaps[1]["status"] == "inaccessible"
    results["topic_led_voc"]["cells"][0]["query_reviews"] = []
    gaps = checks._collection_coverage_gaps(collection, {"execution_contract_version": 4}, results,
                                            {"q2": {"brave_search": "failed"}})
    assert gaps[1]["status"] == "provider_failure"


def test_v4_raw_returned_but_unretained_candidate_cannot_disappear(tmp_path, monkeypatch):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    summary = json.loads((run / "summary.json").read_text())
    summary["providers"]["reddit"]["query_ledger"][0]["returned_count"] = 1
    write(run / "summary.json", summary)
    raw = {"searches": [{"query_id": "q1", "response": {"body": {"data": {"children": [
        {"data": {"id": "post1", "permalink": "/r/finance/comments/post1/question/"}}]}}}}]}
    write(run / "raw/reddit.json", raw)
    pack = run / "customer-feedback"
    plan = {"execution_contract_version": 4, "customer_segment": "Direct payer", "locales": ["FR:fr"],
            "entity_count": 0, "analysis_contract": {"entity_led_feedback": "not_applicable"},
            "topic_matrix": [{"cell_id": "fr", "locale": "FR:fr"}], "source_matrix": [],
            "capture_inputs": []}
    review = {"query_id": "q1", "status": "reviewed", "record_ids": [], "reviewed_ids": [],
              "provider_outcomes": {"reddit": "ok"}, "reason": "The one raw result is outside the reviewed payer scope.",
              "next_observation": "Interview a qualifying payer with an actual bill.", "reviewer": "Analyst"}
    results = {"topic_led_voc": {"cells": [{"cell_id": "fr", "attempted": True,
        "query_ids": ["q1"], "retrieved_document_ids": [], "retrieved_evidence_ids": [],
        "retrieved_count": 0, "reviewed_count": 0, "accepted_count": 0,
        "accepted_evidence_ids": [], "query_reviews": [review]}]}, "source_results": []}
    write(pack / "customer-feedback-source-plan.json", plan)
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    (pack / "evidence.jsonl").write_text("")
    write(pack / "source-review.json", {"reviews": []})
    write(pack / "customer-voc-synthesis.json", {})
    write(pack / "claim-ledger.json", {})
    monkeypatch.setattr(checks.subprocess, "run", lambda *_args, **_kwargs: type("R", (), {
        "returncode": 0, "stdout": "", "stderr": ""})())
    actual = checks.validate_research(workspace, run)
    assert actual["status"] == "partial"
    assert any(gap.get("status") == "review_pending" for gap in actual["open_gaps"])
    review["raw_result_reviews"] = [{"provider": "reddit",
        "raw_sha256": hashlib.sha256((run / "raw/reddit.json").read_bytes()).hexdigest(),
        "returned_count": 1, "retained_count": 0, "reviewer": "Analyst",
        "reason": "The original post is outside the requested customer payment job.",
        "candidates": [{"candidate_id": "post1", "source_url": "https://www.reddit.com/r/finance/comments/post1/question/",
                        "disposition": "excluded", "reason": "Original post concerns another market and a different payment job."}]}]
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    assert checks.validate_research(workspace, run)["status"] == "complete"
    summary["providers"]["reddit"]["query_ledger"][0]["returned_count"] = 0
    write(run / "summary.json", summary)
    write(run / "raw/reddit.json", {"searches": [{"query_id": "q1", "response": {
        "body": {"data": {"children": []}}}}]})
    review.pop("raw_result_reviews")
    write(pack / "customer-feedback-results.json", results)
    coverage, errors = finalize_feedback(plan, results)
    assert not errors
    write(pack / "customer-feedback-coverage.json", coverage)
    assert checks.validate_research(workspace, run)["status"] == "complete"


def test_episode_document_cannot_remain_unextracted(tmp_path, monkeypatch):
    workspace = case(tmp_path)
    run = collected_run(workspace, records=[{"evidence_id": "d1", "source_url": "https://forum.test/one",
        "discovery_memberships": [{"query_id": "q1"}]}])
    pack = run / "customer-feedback"
    plan = {"execution_contract_version": 3, "customer_segment": "Direct payer",
            "topic_matrix": [{"cell_id": "fr", "locale": "FR:fr", "query_ids": ["q1"]}],
            "source_matrix": [], "capture_inputs": [], "analysis_contract": {"entity_led_feedback": "not_applicable"}}
    cell = {"cell_id": "fr", "attempted": True, "query_ids": ["q1"],
            "retrieved_document_ids": ["d1"], "retrieved_evidence_ids": ["ex1"],
            "retrieved_count": 1, "reviewed_count": 1, "accepted_count": 1,
            "accepted_evidence_ids": ["ex1"], "unextracted_document_ids": ["d1"],
            "sampling": {"unit": "episode", "reviewed_ids": ["ex1"]}}
    results = {"topic_led_voc": {"cells": [cell]}, "source_results": []}
    coverage = {"accepted_evidence_ids": ["ex1"], "coverage_gaps": [], "execution_status": "complete",
                "coverage_status": "partial",
                "claim_status": "scoped_synthesis_ready"}
    write(pack / "customer-feedback-source-plan.json", plan)
    write(pack / "customer-feedback-results.json", results)
    write(pack / "customer-feedback-coverage.json", coverage)
    (pack / "evidence.jsonl").write_text(json.dumps({"evidence_id": "ex1", "capture_unit": "experience",
        "document_id": "d1"}) + "\n")
    write(pack / "source-review.json", {"reviews": [{"evidence_id": "ex1", "segment_relation": "target"}]})
    write(pack / "customer-voc-synthesis.json", {})
    write(pack / "claim-ledger.json", [])
    from scripts.evidence_scout import finalize_customer_feedback
    monkeypatch.setattr(finalize_customer_feedback, "validate", lambda *_: (coverage, []))
    monkeypatch.setattr(checks.subprocess, "run", lambda *_args, **_kwargs: type("R", (), {
        "returncode": 0, "stdout": "", "stderr": ""})())
    invalid = checks.validate_research(workspace, run)
    assert invalid["status"] == "invalid"
    assert "unextracted document IDs" in invalid["missing_requirements"][0]
    cell["unextracted_document_ids"] = []
    write(pack / "customer-feedback-results.json", results)
    assert checks.validate_research(workspace, run)["status"] != "invalid"


def test_primary_research_resolution_needs_bound_case_handoff(tmp_path):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    run = collected_run(workspace)
    observation = "A recent buyer names the attempted alternative, paid amount and resulting decision."
    results = {"topic_led_voc": {"cells": [{"cell_id": "local-payer", "search_resolution": {
        "status": "primary_research_needed", "query_ids": ["q1"], "next_observation": observation}}]}}
    plan = {"execution_contract_version": 3}
    gaps, _ = checks._primary_research_handoff(root, run, plan, results)
    assert gaps[0]["status"] == "handoff_required"
    handoff = workspace / "market_research/interviews/recruitment-plan.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("Unpaid local-payer incident interview route and episode checklist.\n")
    plan["primary_research_handoff"] = {"path": str(handoff.relative_to(root)),
        "sha256": hashlib.sha256(handoff.read_bytes()).hexdigest(), "cell_ids": ["local-payer"]}
    assert checks._primary_research_handoff(root, run, plan, results)[0][0]["status"] == "handoff_required"
    handoff.write_text("\n".join([
        "# Primary research handoff", "", "### local-payer", "",
        "- Desk research limit: Query q1 and its public sources were reviewed but found no direct recent payer account.",
        "- Target participant: Recent local insurance buyer deciding how to pay for cover.",
        "- Recent firsthand screen: Personally compared options during the past twelve months; exclude advisers.",
        "- Unpaid access route: Ask a relevant local community to invite recent buyers without incentives.",
        "- Episode questions: What triggered the choice, which alternatives did you try, and what happened?",
        "- Distinguishing observation: " + observation,
        "- Decision rule: Repeated failed alternatives strengthen the hypothesis; satisfactory choices weaken it.",
    ]) + "\n")
    plan["primary_research_handoff"]["sha256"] = hashlib.sha256(handoff.read_bytes()).hexdigest()
    assert checks._primary_research_handoff(root, run, plan, results) == ([], {
        str(handoff.relative_to(root)): plan["primary_research_handoff"]["sha256"]})
    wrong = handoff.read_text().replace(observation, "A generic observation unrelated to the reviewed decision cell.")
    handoff.write_text(wrong)
    plan["primary_research_handoff"]["sha256"] = hashlib.sha256(handoff.read_bytes()).hexdigest()
    assert checks._primary_research_handoff(root, run, plan, results)[0][0]["status"] == "handoff_required"
    handoff.write_text(wrong.replace("A generic observation unrelated to the reviewed decision cell.", observation))
    plan["primary_research_handoff"]["sha256"] = hashlib.sha256(handoff.read_bytes()).hexdigest()
    plan["primary_research_handoff"]["cell_ids"] = ["some-other-cell"]
    assert checks._primary_research_handoff(root, run, plan, results)[0][0]["status"] == "handoff_required"
    plan["primary_research_handoff"]["cell_ids"] = ["local-payer"]
    plan["primary_research_handoff"]["path"] = "cases/another-case/market_research/interviews/recruitment-plan.md"
    assert checks._primary_research_handoff(root, run, plan, results)[0][0]["status"] == "handoff_required"
    plan["primary_research_handoff"]["path"] = str(handoff.relative_to(root))
    handoff.write_text("Edited after the review.\n")
    gaps, _ = checks._primary_research_handoff(root, run, plan, results)
    assert gaps[0]["status"] == "handoff_required"


def test_case_appraisal_requires_reviewed_run_and_admits_bounded_partial(tmp_path, monkeypatch):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    for section in ('customer_segments', 'customer_journey', 'pain_points'):
        path = workspace / 'market_research' / section / 'summary.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Authored summary without a reviewed source chain.')
    assert checks.initial_case_evidence(root, 'probe')['status'] == 'missing'
    run = workspace / 'market_research/pain_points/runs/reviewed'
    pack = run / 'customer-feedback'
    pack.mkdir(parents=True)
    write(pack / 'claim-ledger.json', [])
    write(pack / 'customer-feedback-coverage.json', {'accepted_evidence_ids': ['e1'],
                                                     'claim_status': 'scoped_synthesis_ready'})
    monkeypatch.setattr(checks, 'validate_research', lambda *_: {
        'status': 'partial', 'claim_status': 'reviewed', 'coverage_status': 'partial'})
    result = checks.initial_case_evidence(root, 'probe')
    assert result['status'] == 'eligible'
    assert result['eligible_runs'][0]['status'] == 'partial'
    assert result['eligible_runs'][0]['claim_ledger'].endswith('/customer-feedback/claim-ledger.json')


def test_case_appraisal_checks_local_run_against_business_workspace(tmp_path, monkeypatch):
    workspace = case(tmp_path)
    root = workspace.parent.parent
    for section in ('customer_segments', 'customer_journey', 'pain_points'):
        path = workspace / 'market_research' / section / 'summary.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Reviewed case-specific analysis.')
    run = workspace / 'market_research/pain_points/runs/linked-captures'
    pack = run / 'customer-feedback'
    pack.mkdir(parents=True)
    write(pack / 'claim-ledger.json', [])
    write(pack / 'customer-feedback-coverage.json', {
        'accepted_evidence_ids': ['e1'], 'claim_status': 'scoped_synthesis_ready'})
    seen = []

    def check(workspace_root, run_dir):
        seen.append((workspace_root, run_dir))
        return {'status': 'partial', 'claim_status': 'scoped_synthesis_ready'}

    monkeypatch.setattr(checks, 'validate_research', check)
    assert checks.initial_case_evidence(root, 'probe')['status'] == 'eligible'
    assert seen == [(root.absolute(), run)]


def test_manual_capture_requires_original_bound_source_and_query(tmp_path):
    workspace = case(tmp_path)
    run = workspace / "market_research/pain_points/runs/manual"
    run.mkdir(parents=True)
    capture_run_scope(run, workspace)
    write(run / "query_plan.json", {"input_plan": {"queries": [{"query_id": "q1", "query": "insurance frustration"}]}})
    original = run / "raw/forum.md"
    original.parent.mkdir()
    original.write_text("I asked about the policy after a claim was denied.\n")
    url = "https://forum.example.test/thread/1"
    capture = {"query_id": "q1", "query": "insurance frustration", "source_url": url,
               "capture_path": "raw/forum.md", "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
               "retrieved_at": "2026-09-25T00:00:00Z", "retrieval_outcome": "ok"}
    write(run / "manual-captures.json", {"schema_version": 1, "capture_method": "manual", "captures": [capture]})
    write(run / "summary.json", {"record_count": 1, "irrelevant_count": 0})
    (run / "evidence.jsonl").write_text(json.dumps({"evidence_id": "e1", "source_url": url,
        "discovery_memberships": [{"query_id": "q1"}]}) + "\n")
    (run / "irrelevant.jsonl").write_text("")
    assert checks.validate_collection(workspace, run)["status"] == "complete"
    update_stage(workspace, "evidence_collection", run_dir=run, status="passed", gate_result="pass",
                 artifacts=[run / "summary.json"], expected_assessment_revision=1)
    original.write_text("A different source.")
    assert checks.validate_collection(workspace, run)["status"] == "invalid"


def test_direct_discovery_pass_requires_reviewed_research_pack(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    before = (workspace / "market_research/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="market_discovery research is not complete"):
        update_stage(workspace, "market_discovery", run_dir=run, status="passed", gate_result="pass",
                     artifacts=[run / "summary.json"], expected_assessment_revision=1)
    assert (workspace / "market_research/manifest.json").read_bytes() == before


def test_edited_run_manifest_pass_does_not_override_shared_receipt(tmp_path):
    workspace = case(tmp_path)
    run = collected_run(workspace)
    update_run_manifest(run, stage="evidence_collection", stage_status="passed", gate_result="pass")
    state = resume_from_last_gate(run)
    assert "no current shared-stage validation receipt" in state["reason"]
    update_stage(workspace, "evidence_collection", run_dir=run, status="passed", gate_result="pass",
                 artifacts=[run / "summary.json"], expected_assessment_revision=1)
    resumed = resume_from_last_gate(run)
    assert resumed["reason"] == "Resume work derived from current research artifacts"
    assert resumed["research_status"] == "partial"
    plan = run / "query_plan.json"
    plan.write_text(plan.read_text() + " ")
    assert "no current shared-stage validation receipt" in resume_from_last_gate(run)["reason"]
