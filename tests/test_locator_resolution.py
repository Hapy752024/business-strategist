import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("completion_locator", ROOT / "scripts/evidence_scout/validate_research_completion.py")
completion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(completion)
spec = importlib.util.spec_from_file_location("finalizer_locator", ROOT / "scripts/evidence_scout/finalize_customer_feedback.py")
finalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finalizer)


def fixture(tmp_path, *, status="ok", urls=()):
    workspace = tmp_path / "workspace"
    run = workspace / "cases/case/market_research/pain_points/runs/study"
    capture_rel = "cases/case/market_research/pain_points/runs/locator"
    capture = workspace / capture_rel
    (capture / "raw").mkdir(parents=True)
    query = 'site:trustpilot.com "Product Plus" "Example Spain" España'
    query_row = {"query_id": "q1", "query": query, "provider": "brave_search",
                 "intent": "entity_locator_discovery", "source_family": "independent_review_platforms",
                 "locale": "ES:es", "candidate_id": "example"}
    (capture / "query_plan.json").write_text(json.dumps({"input_plan": {"queries": [query_row]}}))
    (capture / "summary.json").write_text(json.dumps({"providers": {"brave_search": {"query_ledger": [
        {"query_id": "q1", "query": query, "scheduled": True, "attempted": True,
         "candidate_id": "example", "status": status, "returned_count": len(urls)}]}}}))
    raw = {"searches": [{"query_id": "q1", "query": query, "response": {
        "ok": status == "ok", "body": {"web": {"results": [{"url": url} for url in urls]}}}}]}
    raw_path = capture / "raw/brave_search.json"
    raw_path.write_text(json.dumps(raw))
    review = {"status": "locator_unavailable", "entity_id": "example", "locale": "ES:es",
              "source_lane": "independent_review_platforms", "reviewer": "Research analyst",
              "reviewed_at": "2026-09-27",
              "reason": "Bounded public search returned no verified exact product profile.",
              "next_observation": "Recheck the exact platform profile and interview a recent product user.",
              "fallback_reason": "", "searches": [{
                  "run_dir": capture_rel, "query_id": "q1", "query_text": query,
                  "provider": "brave_search", "source_domain": "trustpilot.com",
                  "entity_aliases": ["Product Plus", "Example Spain"], "locale_terms": ["España"],
                  "relevance_rationale": "The domain, exact product and entity names, and Spain locate the intended profile.",
                  "query_status": status, "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                  "candidates": [{"candidate_id": url, "source_url": url,
                                  "disposition": "adjacent", "reason": "This page concerns another product, not Product Plus."}
                                 for url in urls]}]}
    lane = {"entity_id": "example", "entity_name": "Example Spain Product Plus",
            "locale": "ES:es", "source_lane": "independent_review_platforms",
            "applicable": True, "locators": [], "reviewed_locators": [], "locator_resolution": review}
    official = {"entity_id": "example", "entity_name": "Example Spain Product Plus",
                "locale": "ES:es", "source_lane": "company_hosted_supplier_context",
                "reviewed_locators": [{"locator": "https://example.test/product",
                                       "review_reason": "Exact official product identity confirmed."}]}
    plan = {"execution_contract_version": 4, "capture_inputs": [{"run_dir": capture_rel}],
            "source_matrix": [lane, official]}
    return workspace, run, plan


def test_bounded_zero_locator_and_structural_disposition(tmp_path):
    workspace, run, plan = fixture(tmp_path)
    assert completion._v4_locator_inputs(workspace, run, plan)
    errors = []
    assert finalizer._locator_resolution(plan["source_matrix"][0], "lane", errors)
    assert not errors


def test_positive_locator_stale_capture_and_irrelevant_query_fail(tmp_path):
    workspace, run, plan = fixture(tmp_path, urls=["https://trustpilot.com/review/example"])
    review = plan["source_matrix"][0]["locator_resolution"]
    review["searches"][0]["candidates"][0]["disposition"] = "exact_match"
    errors = []
    finalizer._locator_resolution(plan["source_matrix"][0], "lane", errors)
    assert any("contradicts" in error for error in errors)
    review["searches"][0]["candidates"][0]["disposition"] = "adjacent"
    review["searches"][0]["candidates"] = []
    with pytest.raises(ValueError, match="candidates"):
        completion._v4_locator_inputs(workspace, run, plan)
    review["searches"][0]["candidates"] = [{"candidate_id": "https://trustpilot.com/review/example",
        "source_url": "https://trustpilot.com/review/example", "disposition": "adjacent",
        "reason": "This page concerns another product, not Product Plus."}]
    review["searches"][0]["entity_aliases"] = ["Unrelated Brand"]
    with pytest.raises(ValueError, match="exact product"):
        completion._v4_locator_inputs(workspace, run, plan)
    review["searches"][0]["entity_aliases"] = ["Product Plus", "Example Spain"]
    (workspace / review["searches"][0]["run_dir"] / "raw/brave_search.json").write_text("{}")
    with pytest.raises(ValueError, match="stale"):
        completion._v4_locator_inputs(workspace, run, plan)


def test_provider_failure_cannot_be_zero_but_can_be_access_limited(tmp_path):
    workspace, run, plan = fixture(tmp_path, status="insufficient_credits")
    with pytest.raises(ValueError, match="successful"):
        completion._v4_locator_inputs(workspace, run, plan)
    review = plan["source_matrix"][0]["locator_resolution"]
    review["status"] = "platform_access_limited"
    review["fallback_reason"] = "No second provider was accessible during this bounded capture."
    assert completion._v4_locator_inputs(workspace, run, plan)
    review["fallback_reason"] = ""
    with pytest.raises(ValueError, match="fallback"):
        completion._v4_locator_inputs(workspace, run, plan)


def test_wrong_entity_zero_query_fails_even_with_current_digests(tmp_path):
    workspace, run, plan = fixture(tmp_path)
    search = plan["source_matrix"][0]["locator_resolution"]["searches"][0]
    wrong = 'site:trustpilot.com "Unrelated Shop" España'
    capture = workspace / search["run_dir"]
    query_plan = json.loads((capture / "query_plan.json").read_text())
    query_plan["input_plan"]["queries"][0]["query"] = wrong
    (capture / "query_plan.json").write_text(json.dumps(query_plan))
    summary = json.loads((capture / "summary.json").read_text())
    summary["providers"]["brave_search"]["query_ledger"][0]["query"] = wrong
    (capture / "summary.json").write_text(json.dumps(summary))
    raw_path = capture / "raw/brave_search.json"
    raw = json.loads(raw_path.read_text())
    raw["searches"][0]["query"] = wrong
    raw_path.write_text(json.dumps(raw))
    search.update(query_text=wrong, entity_aliases=["Unrelated Shop"],
                  raw_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="exact product"):
        completion._v4_locator_inputs(workspace, run, plan)


def test_reported_five_results_cannot_close_with_empty_raw_capture(tmp_path):
    workspace, run, plan = fixture(tmp_path)
    search = plan["source_matrix"][0]["locator_resolution"]["searches"][0]
    summary_path = workspace / search["run_dir"] / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["providers"]["brave_search"]["query_ledger"][0]["returned_count"] = 5
    summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="candidates"):
        completion._v4_locator_inputs(workspace, run, plan)


def test_literal_escaped_quotes_do_not_count_as_exact_search(tmp_path):
    workspace, run, plan = fixture(tmp_path)
    search = plan["source_matrix"][0]["locator_resolution"]["searches"][0]
    escaped = search["query_text"].replace('"', '\\"')
    capture = workspace / search["run_dir"]
    query_plan = json.loads((capture / "query_plan.json").read_text())
    query_plan["input_plan"]["queries"][0]["query"] = escaped
    (capture / "query_plan.json").write_text(json.dumps(query_plan))
    summary = json.loads((capture / "summary.json").read_text())
    summary["providers"]["brave_search"]["query_ledger"][0]["query"] = escaped
    (capture / "summary.json").write_text(json.dumps(summary))
    raw_path = capture / "raw/brave_search.json"
    raw = json.loads(raw_path.read_text())
    raw["searches"][0]["query"] = escaped
    raw_path.write_text(json.dumps(raw))
    search.update(query_text=escaped, raw_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="exact product"):
        completion._v4_locator_inputs(workspace, run, plan)
