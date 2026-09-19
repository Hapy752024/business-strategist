import importlib.util
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module)
    return module


planner = load("feedback_planner", "scripts/evidence_scout/plan_customer_feedback.py")
finalizer = load("feedback_finalizer", "scripts/evidence_scout/finalize_customer_feedback.py")


def plan():
    entity = {"id": "e1", "name": "Example", "domain": "example.test", "lane": "similar_company", "sources": {lane: [{"locator": f"{lane}-locator", "locales": ["FR:fr"], "review_status": "accepted", "review_reason": "verified"}] for lane in planner.LANES}}
    return planner.build_plan("support", "families", ["FR:fr"], [entity])


def complete_results(p):
    results = {"topic_led_voc": {"cells": [{"cell_id": cell["cell_id"], "attempted": True, "retrieved_count": 4, "reviewed_count": 4, "accepted_count": 2, "accepted_evidence_ids": ["topic-1", "topic-2"]} for cell in p["topic_matrix"]]}, "source_results": [{"entity_id": row["entity_id"], "locale": row["locale"], "source_lane": row["source_lane"], "attempted": True, "retrieved_count": 3, "reviewed_count": 3, "accepted_customer_voice_count": 1, "locator_results": [{"locator": item["locator"], "attempted": True, "retrieved_count": 3, "reviewed_count": 3, "accepted_customer_voice_count": 1, "accepted_evidence_ids": [f"{row['source_lane']}-{index}"]} for index, item in enumerate(row["reviewed_locators"])]} for row in p["source_matrix"]]}
    for row in results["source_results"]:
        if row["source_lane"] == "company_hosted_supplier_context":
            row["accepted_customer_voice_count"] = 0
            for item in row["locator_results"]:
                item["accepted_customer_voice_count"] = 0
                item["accepted_evidence_ids"] = []
    return results


def test_completion_validator_requires_every_applicable_lane_and_topic_pass():
    p = plan(); output, errors = finalizer.validate(p, complete_results(p))
    assert not errors and output["synthesis_allowed"] is True
    incomplete = complete_results(p); incomplete["source_results"].pop(); incomplete["topic_led_voc"] = {}
    output, errors = finalizer.validate(p, incomplete)
    assert not errors and output["synthesis_allowed"] is False
    assert output["claim_status"] == "pending_topic_discovery"


def test_completion_validator_rejects_impossible_denominators():
    p = plan(); results = complete_results(p); results["source_results"][0]["accepted_customer_voice_count"] = 4
    _output, errors = finalizer.validate(p, results)
    assert any("accepted <= reviewed <= retrieved" in error for error in errors)


def test_completion_validator_rejects_bad_topic_counts_and_missing_locator_attempt():
    p = plan(); results = complete_results(p)
    results["topic_led_voc"] = {"attempted": True, "retrieved_count": 0, "reviewed_count": 0, "accepted_count": 999, "accepted_evidence_ids": []}
    results["source_results"][0]["locator_results"] = []
    output, errors = finalizer.validate(p, results)
    assert any("topic-led counts" in error for error in errors)
    assert any("No completion result for locator" in gap["reason"] for gap in output["coverage_gaps"])


def test_unattempted_locator_and_lane_failure_preserve_other_scoped_findings():
    p = plan(); row = p["source_matrix"][0]
    row["locators"].append("unreviewed-local-platform")
    results = complete_results(p); results["source_results"][0]["failed_or_blocked"] = "HTTP 402 insufficient credits"
    output, errors = finalizer.validate(p, results)
    assert not errors and output["synthesis_allowed"] is True
    assert output["status"] == "partial"
    assert any("no accepted review disposition" in gap["reason"] for gap in output["coverage_gaps"])
    assert any("402" in gap["reason"] for gap in output["coverage_gaps"])


def test_voc_synthesis_validator_enforces_frames_and_u_r_links(tmp_path, monkeypatch, capsys):
    evidence = tmp_path / "evidence.jsonl"
    valid_evidence_text = "\n".join([json.dumps({"evidence_id": "t1", "source_url": "https://example.test/t1", "sampling_frame": "topic_led_voc", "source_role": "community_context", "author_voice_status": "unreviewed"}), json.dumps({"evidence_id": "e1", "source_url": "https://example.test/e1", "sampling_frame": "entity_led_feedback", "subject_entity_id": "x", "collection_locale": "DE:de", "collection_source_lane": "independent_review_platforms", "collection_locator": "example", "source_role": "customer_review", "author_voice_status": "unreviewed"})]) + "\n"
    evidence.write_text(valid_evidence_text)
    review = tmp_path / "source-review.json"; review.write_text(json.dumps({"evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(), "target_segment": "families", "reviews": [{"evidence_id": item, "source_url": f"https://example.test/{item}", "status": "accepted", "voice": "customer", "firsthand": True, "author_relationship": "firsthand_customer", "reviewed_segment": "families", "segment_relation": "target", "relevance_rationale": "The author describes firsthand use."} for item in ("t1", "e1")]}))
    coverage = tmp_path / "coverage.json"; coverage.write_text(json.dumps({"synthesis_allowed": True, "topic_led_voc": {"accepted_evidence_ids": ["t1"]}, "source_matrix": [{"entity_id": "x", "locale": "DE:de", "source_lane": "independent_review_platforms", "applicable": True, "locator_results": [{"locator": "example", "accepted_evidence_ids": ["e1"]}]}]}))
    synthesis = tmp_path / "synthesis.json"; synthesis.write_text(json.dumps({"topic_led_evidence_ids": ["t1"], "entity_led_evidence_ids": ["e1"], "customer_needs": [{"id": "U1", "outcome": "finish the job", "evidence_ids": ["t1"], "perspectives": ["customer"], "attribution": "customer_stated"}], "solution_requirements": [{"id": "R1", "condition_or_capability": "show status", "evidence_ids": ["e1"], "perspectives": ["customer"], "linked_u_ids": ["U1"], "operational_root_unknown": False, "attribution": "customer_stated"}]}))
    validator = load("voc_validator", "scripts/evidence_scout/validate_customer_voc_synthesis.py")
    monkeypatch.setattr("sys.argv", ["validate", "--evidence", str(evidence), "--synthesis", str(synthesis), "--coverage", str(coverage), "--source-review", str(review), "--customer-segment", "families"])
    assert validator.main() == 0
    wrong_binding_rows = [json.loads(line) for line in evidence.read_text().splitlines()]
    wrong_binding_rows[1]["subject_entity_id"] = "unplanned-e2"
    evidence.write_text("\n".join(json.dumps(row) for row in wrong_binding_rows) + "\n")
    updated_review = json.loads(review.read_text()); updated_review["evidence_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest(); review.write_text(json.dumps(updated_review))
    assert validator.main() == 2
    evidence.write_text(valid_evidence_text)
    updated_review["evidence_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest(); review.write_text(json.dumps(updated_review))
    wrong_locator_rows = [json.loads(line) for line in evidence.read_text().splitlines()]
    wrong_locator_rows[1]["collection_locator"] = "different-place"
    evidence.write_text("\n".join(json.dumps(row) for row in wrong_locator_rows) + "\n")
    updated_review["evidence_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest(); review.write_text(json.dumps(updated_review))
    assert validator.main() == 2
    evidence.write_text(valid_evidence_text)
    updated_review["evidence_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest(); review.write_text(json.dumps(updated_review))
    bad = json.loads(synthesis.read_text()); bad["topic_led_evidence_ids"] = ["e1"]; synthesis.write_text(json.dumps(bad))
    assert validator.main() == 2


def test_voc_synthesis_rejects_supplier_record_even_if_review_calls_it_customer(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence.jsonl"
    row = {"evidence_id": "s1", "source_url": "https://example.test/s1", "sampling_frame": "topic_led_voc", "source_role": "competitor_context", "author_voice_status": "supplier_context", "source_intent": "competitor_content"}
    evidence.write_text(json.dumps(row) + "\n")
    review = tmp_path / "review.json"; review.write_text(json.dumps({"evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(), "target_segment": "families", "reviews": [{"evidence_id": "s1", "source_url": row["source_url"], "status": "accepted", "voice": "customer", "firsthand": True, "author_relationship": "firsthand_customer", "reviewed_segment": "families", "segment_relation": "target", "relevance_rationale": "Incorrect fixture label"}]}))
    coverage = tmp_path / "coverage.json"; coverage.write_text(json.dumps({"synthesis_allowed": True, "topic_led_voc": {"accepted_evidence_ids": ["s1"]}, "source_matrix": []}))
    synthesis = tmp_path / "synthesis.json"; synthesis.write_text(json.dumps({"topic_led_evidence_ids": ["s1"], "entity_led_evidence_ids": [], "customer_needs": [{"id": "U1", "outcome": "outcome", "evidence_ids": ["s1"], "perspectives": ["customer"], "attribution": "customer_stated"}], "solution_requirements": []}))
    validator = load("voc_supplier_validator", "scripts/evidence_scout/validate_customer_voc_synthesis.py")
    monkeypatch.setattr("sys.argv", ["validate", "--evidence", str(evidence), "--synthesis", str(synthesis), "--coverage", str(coverage), "--source-review", str(review), "--customer-segment", "families"])
    assert validator.main() == 2


def test_local_forum_nonadopter_can_be_promoted_without_becoming_customer_usage(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence.jsonl"
    row = {"evidence_id": "n1", "source_url": "https://forumconstruire.example/thread", "sampling_frame": "topic_led_voc", "source_role": "search_result", "author_voice_status": "non_customer", "source_intent": "forum_discussion"}
    evidence.write_text(json.dumps(row) + "\n")
    review = tmp_path / "review.json"; review.write_text(json.dumps({"evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(), "target_segment": "families", "reviews": [{"evidence_id": "n1", "source_url": row["source_url"], "status": "accepted", "voice": "nonadopter", "firsthand": True, "author_relationship": "firsthand_nonadopter", "reviewed_segment": "families", "segment_relation": "target", "relevance_rationale": "Target family describes its own decision.", "reviewed_source_kind": "forum", "source_kind_rationale": "Thread contains independent participant discussion.", "decision_context": "Compared providers and continued a manual workaround."}]}))
    coverage = tmp_path / "coverage.json"; coverage.write_text(json.dumps({"synthesis_allowed": True, "topic_led_voc": {"accepted_evidence_ids": ["n1"]}, "source_matrix": []}))
    synthesis = tmp_path / "synthesis.json"; synthesis.write_text(json.dumps({"topic_led_evidence_ids": ["n1"], "entity_led_evidence_ids": [], "customer_needs": [{"id": "U1", "outcome": "retain control", "evidence_ids": ["n1"], "perspectives": ["nonadopter"], "attribution": "customer_stated"}], "solution_requirements": []}))
    validator = load("voc_nonadopter_validator", "scripts/evidence_scout/validate_customer_voc_synthesis.py")
    monkeypatch.setattr("sys.argv", ["validate", "--evidence", str(evidence), "--synthesis", str(synthesis), "--coverage", str(coverage), "--source-review", str(review), "--customer-segment", "families"])
    assert validator.main() == 0
    inflated = json.loads(synthesis.read_text()); inflated["customer_needs"][0]["perspectives"] = ["nonadopter", "customer"]; synthesis.write_text(json.dumps(inflated))
    assert validator.main() == 2
