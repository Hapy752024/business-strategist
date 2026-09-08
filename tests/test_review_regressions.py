import json
import subprocess
import sys
from pathlib import Path

import pytest
from build_claim_ledger import build, read_jsonl, independent_groups
from validate_synthesis import validate, read_jsonl as read_synthesis
from workspace import create_topic_workspace, update_stage
from test_strategy_review import load_review, plan
from readiness import load_latest
from datetime import datetime, timezone, timedelta


def test_duplicates_and_unknowns_do_not_inflate_confidence():
    rows = [{"evidence_id": str(i), "text": "same story", "duplicate_cluster_id": "copy", "strength": "weak"} for i in range(3)]
    assert independent_groups(rows) == []
    for i, row in enumerate(rows):
        row["independence_key"] = str(i)
    assert len(independent_groups(rows)) == 1
    claims = build(rows, [{"supporting_evidence": ["0", "1", "2"], "confidence": "high"}])
    assert any("confidence exceeds" in error for error in validate(claims, rows))


def test_source_review_requires_acceptance_and_reason_for_both_sides():
    rows = [{"evidence_id": "support", "text": "sector article", "strength": "weak"},
            {"evidence_id": "counter", "text": "contrary experience", "strength": "weak"}]
    claims = build(rows, [{"supporting_evidence": ["support"], "counter_evidence": ["counter"], "confidence": "unresolved"}])
    assert sum("source review" in error for error in validate(claims, rows, require_source_review=True)) == 2
    rows[0]["analyst_review"] = {"status": "accepted", "reason": "Actual buyer describes this job in the target country."}
    rows[1]["analyst_review"] = {"status": "accepted", "reason": " "}
    assert sum("source review" in error for error in validate(claims, rows, require_source_review=True)) == 1
    rows[1]["analyst_review"]["reason"] = "Customer reports the existing alternative solved the same job."
    assert not any("source review" in error for error in validate(claims, rows, require_source_review=True))
    rows[0]["relevance"] = "irrelevant"
    assert any("irrelevant evidence" in error for error in validate(claims, rows, require_source_review=True))


def test_legacy_identity_agrees_between_consumers(tmp_path):
    path = tmp_path / "evidence.jsonl"
    row = {"source": "reddit", "source_url": "https://example.com/item", "text": "pain", "retrieved_at": "2026-09-01T00:00:00Z"}
    path.write_text(json.dumps(row) + "\n")
    original = read_jsonl(path)[0]["evidence_id"]
    assert read_synthesis(path)[0]["evidence_id"] == original
    row["retrieved_at"] = "2026-09-06T00:00:00Z"
    path.write_text(json.dumps(row) + "\n")
    assert read_synthesis(path)[0]["evidence_id"] == original


def test_final_decision_requires_artifacts_and_predecessor(tmp_path):
    workspace = create_topic_workspace("fixture", str(tmp_path))
    with pytest.raises(ValueError, match="require artifacts"):
        update_stage(workspace, "final_decision", status="passed", gate_result="pass")
    artifact = tmp_path / "decision.json"
    artifact.write_text("{}")
    with pytest.raises(ValueError, match="requires a passed"):
        update_stage(workspace, "final_decision", status="passed", gate_result="pass", artifacts=[artifact])


def test_cost_direction_missing_data_and_frozen_baseline(tmp_path):
    review = load_review()
    data = plan()
    data["kpis"][0].update(direction="at_most", target=100, numerator="spend", denominator="customers")
    assert review.weekly_review(data, {"spend": 2000, "customers": 10})["kpis"][0]["status"] == "off_track"
    assert review.weekly_review(data, {})["status"] == "incomplete"
    assert review.weekly_review(data, {"spend": True, "customers": 10})["status"] == "incomplete"
    baseline = tmp_path / "baseline.json"
    review.freeze_plan(data, baseline)
    with pytest.raises(FileExistsError):
        review.freeze_plan(data, baseline)
    data["kpis"][0]["target"] = 300
    current = tmp_path / "plan.json"
    current.write_text(json.dumps(data))
    observations = tmp_path / "observations.json"
    observations.write_text("{}")
    result = subprocess.run([sys.executable, "scripts/strategy_review.py", "weekly-review", "--plan", str(current), "--baseline", str(baseline), "--observations", str(observations)], capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "changed_protocol"


def test_cohort_currency_scope_and_maturity():
    review = load_review()
    data = plan()
    data["kpis"][0].update(cadence="cohort", cohort="September", window="30d", currency="CHF")
    observations = {"deposits": 2, "qualified_calls": 8}
    assert review.weekly_review(data, observations)["status"] == "incomplete"
    metadata = {"cohort": "September", "window": "30d", "currency": "CHF", "mature": False}
    observations["_metadata"] = {"pilot conversion": metadata}
    assert review.weekly_review(data, observations)["kpis"][0]["status"] == "immature_cohort"
    metadata["mature"] = True
    assert review.weekly_review(data, observations)["status"] == "complete"
    metadata["currency"] = "USD"
    assert review.weekly_review(data, observations)["status"] == "incomplete"


def test_newest_readiness_wins_and_old_results_are_stale(tmp_path):
    now = datetime.now(timezone.utc)
    old = {"provider": "fixture", "status": "failed", "validated_at": (now-timedelta(days=2)).isoformat()}
    fresh = {"provider": "fixture", "status": "ok", "validated_at": now.isoformat()}
    (tmp_path / "all.summary.json").write_text(json.dumps([old]))
    (tmp_path / "fixture.summary.json").write_text(json.dumps(fresh))
    assert load_latest(tmp_path)["fixture"]["status"] == "ok"
    (tmp_path / "fixture.summary.json").write_text(json.dumps(old))
    assert load_latest(tmp_path)["fixture"]["status"] == "stale"
