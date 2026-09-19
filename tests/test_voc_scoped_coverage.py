"""Research-quality coverage scenarios: absent evidence is not invalid evidence."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load("scoped_planner", "scripts/evidence_scout/plan_customer_feedback.py")
finalizer = load("scoped_finalizer", "scripts/evidence_scout/finalize_customer_feedback.py")


def topic_result(cell, ids=None):
    ids = [f"evidence:{cell['cell_id']}"] if ids is None else ids
    return {"cell_id": cell["cell_id"], "attempted": True, "retrieved_count": len(ids),
            "reviewed_count": len(ids), "accepted_count": len(ids), "accepted_evidence_ids": ids}


def entities():
    return [{"id": "care", "name": "Care", "domain": "care.example", "lane": "substitute",
             "sources": {"company_facebook_comments": [{"locator": "https://facebook.com/care", "locales": ["FR:fr"],
                          "review_status": "accepted", "review_reason": "Official public account checked"}]},
             "not_applicable": {lane: "Verified no applicable listing" for lane in planner.LANES if lane != "company_facebook_comments"}}]


def test_french_findings_do_not_cover_requested_german_market():
    p = planner.build_plan("care", "families", ["FR:fr", "DE:de"], [])
    results = {"topic_led_voc": {"cells": [topic_result(p["topic_matrix"][0])]}}
    out, errors = finalizer.validate(p, results)
    assert not errors
    assert out["status"] == "partial" and out["synthesis_allowed"]
    assert out["execution_status"] == "partial"
    assert any(gap.get("locale") == "DE:de" and gap["status"] == "pending" for gap in out["coverage_gaps"])
    assert out["topic_led_voc"]["cells"][1]["accepted_evidence_ids"] == []


def test_attempted_empty_market_stays_empty_not_absence_of_need():
    p = planner.build_plan("care", "families", ["FR:fr", "DE:de"], [])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [topic_result(cell, []) for cell in p["topic_matrix"]]}})
    assert not errors and out["status"] == "insufficient_evidence"
    assert out["execution_status"] == "complete"
    assert out["claim_status"] == "insufficient_evidence" and not out["synthesis_allowed"]
    assert out["accepted_evidence_ids"] == []


def test_attempted_german_search_without_voice_is_not_covered_by_french_voice():
    p = planner.build_plan("care", "families", ["FR:fr", "DE:de"], [])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [topic_result(p["topic_matrix"][0]), topic_result(p["topic_matrix"][1], [])]}})
    assert not errors and out["execution_status"] == "complete"
    assert out["status"] == "partial" and out["coverage_status"] == "partial"
    assert any(gap.get("locale") == "DE:de" and gap["status"] == "no_accepted_voice" for gap in out["coverage_gaps"])


def test_missing_facebook_does_not_block_reviewed_topic_findings():
    p = planner.build_plan("care", "families", ["FR:fr"], entities())
    row = next(row for row in p["source_matrix"] if row["applicable"])
    result = {key: row[key] for key in ("entity_id", "locale", "source_lane")}
    result.update({"attempted": True, "failed_or_blocked": "insufficient_credits", "locator_results": [
        {"locator": row["locators"][0], "attempted": True, "failed_or_blocked": "insufficient_credits"}]})
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [topic_result(p["topic_matrix"][0])]}, "source_results": [result]})
    assert not errors and out["synthesis_allowed"]
    assert out["status"] == "partial" and out["execution_status"] == "complete"
    assert any(gap["reason"] == "insufficient_credits" for gap in out["coverage_gaps"])
    assert out["source_matrix"][2]["accepted_evidence_ids"] == []


def test_unreviewed_locator_cannot_supply_customer_voice():
    p = planner.build_plan("care", "families", ["FR:fr"], entities())
    row = next(row for row in p["source_matrix"] if row["applicable"])
    result = {key: row[key] for key in ("entity_id", "locale", "source_lane")}
    result.update({"attempted": True, "retrieved_count": 1, "reviewed_count": 1, "accepted_customer_voice_count": 1,
                   "locator_results": [{"locator": "https://facebook.com/unreviewed", "attempted": True,
                                        "retrieved_count": 1, "reviewed_count": 1, "accepted_customer_voice_count": 1,
                                        "accepted_evidence_ids": ["fake-accepted"]}]})
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [topic_result(p["topic_matrix"][0])]}, "source_results": [result]})
    assert errors and out["claim_status"] == "blocked_invalid_input"
    assert not out["synthesis_allowed"] and "fake-accepted" not in out["accepted_evidence_ids"]
    assert any("unreviewed locator" in error for error in errors)


def test_legacy_aggregate_results_never_silently_prove_locale_coverage():
    p = planner.build_plan("care", "families", ["FR:fr", "DE:de"], [])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"attempted": True, "retrieved_count": 1,
                                    "reviewed_count": 1, "accepted_count": 1, "accepted_evidence_ids": ["old-1"]}})
    assert not errors and out["synthesis_allowed"]
    assert out["topic_led_voc"]["scope_binding_status"] == "legacy_unresolved"
    assert out["coverage_status"] == "partial"
    assert {gap.get("locale") for gap in out["coverage_gaps"]} >= {"FR:fr", "DE:de"}


def test_repeated_observation_across_sampling_cells_counts_once():
    p = planner.build_plan("care", "families", ["FR:fr"], [], [
        {"locale": "FR:fr", "cell_id": "current", "query_intent": "current_workaround"},
        {"locale": "FR:fr", "cell_id": "success", "query_intent": "successful_alternatives"}])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [topic_result(cell, ["same-episode"]) for cell in p["topic_matrix"]]}})
    assert not errors and out["unique_accepted_count"] == 1
    assert out["topic_led_voc"]["accepted_count"] == 1
    assert out["topic_led_voc"]["retrieved_count"] == 2  # explicit cell occurrences, not independent people


@pytest.mark.parametrize("bad_field,bad_value", [("locale", "DE:de"), ("role", "providers"), ("query_intent", "supplier_marketing")])
def test_result_cannot_relabel_a_planned_sampling_cell(bad_field, bad_value):
    p = planner.build_plan("care", "families", ["FR:fr"], [])
    row = topic_result(p["topic_matrix"][0]); row[bad_field] = bad_value
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [row]}})
    assert errors and not out["synthesis_allowed"]


def test_omitted_positive_workaround_cell_remains_visible():
    p = planner.build_plan("care", "families", ["FR:fr"], [], [
        {"locale": "FR:fr", "cell_id": "pain", "query_intent": "pain"},
        {"locale": "FR:fr", "cell_id": "success", "query_intent": "successful_alternatives"}])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [topic_result(p["topic_matrix"][0])]}})
    assert not errors and out["status"] == "partial"
    assert any(gap.get("query_intent") == "successful_alternatives" for gap in out["coverage_gaps"])


def test_duplicate_cell_result_is_invalid_not_silently_overwritten():
    p = planner.build_plan("care", "families", ["FR:fr"], [])
    row = topic_result(p["topic_matrix"][0])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [row, row]}})
    assert errors and out["status"] == "invalid"


def test_global_accepted_ids_cannot_hide_cell_omission():
    p = planner.build_plan("care", "families", ["FR:fr"], [])
    out, errors = finalizer.validate(p, {"topic_led_voc": {"cells": [], "accepted_evidence_ids": ["unbound-id"]}})
    assert errors and not out["synthesis_allowed"]
