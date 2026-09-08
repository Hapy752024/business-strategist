import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_review():
    spec = importlib.util.spec_from_file_location("strategy_review", ROOT / "scripts/strategy_review.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plan():
    return {
        "schema_version": "1.0", "verdict": "test", "decisive_uncertainty": "Will independent firms pay?",
        "experiments": [{"id": "interviews", "hypothesis": "The buyer will pay", "segment": "Independent firms", "action": "Ask for a paid pilot", "success_metric": "paid pilots", "success_threshold": 2, "stop_condition": "No deposits after 10 asks", "owner": "Founder", "due_date": "2026-09-20"}],
        "kpis": [{"name": "pilot conversion", "direction": "at_least", "formula": "numerator / denominator", "numerator": "deposits", "denominator": "qualified_calls", "cadence": "weekly", "owner": "Founder", "target": 0.2, "decision_rule": "Continue only if conversion reaches target."}],
        "commitments": [{"owner": "Founder", "action": "Run ten calls", "due_date": "2026-09-20"}],
    }


def test_strategy_plan_and_weekly_review() -> None:
    review = load_review()
    assert review.validate_plan(plan()) == []
    report = review.weekly_review(plan(), {"deposits": 2, "qualified_calls": 8})
    assert report["kpis"][0]["status"] == "on_track"


def test_strategy_plan_rejects_missing_owner_and_duplicate_experiment() -> None:
    review = load_review()
    invalid = plan()
    invalid["experiments"].append(dict(invalid["experiments"][0]))
    invalid["commitments"][0].pop("owner")
    errors = review.validate_plan(invalid)
    assert any("IDs must be unique" in error for error in errors)
    assert any("owner" in error for error in errors)


def position():
    return {
        "decision_status": "selected", "statement": "Fixed-scope document collection for independent firms at a predictable price",
        "exclusions": ["Bespoke tax advice"], "provenance": "assumption", "evidence_refs": [],
        "activities": [{"customer_priority": "Predictability (inferred)", "promise": "Fixed scope and price",
                        "choice": "Standard checklist and asynchronous intake", "consequences": "Lower labor per case; exceptions must be priced separately; avoid a long software commitment until tested",
                        "implications": "Market scope and price clearly; do not promise bespoke tax advice",
                        "provenance": "inference", "evidence_refs": [], "experiment_ids": ["interviews"]}],
        "experiment_ids": ["interviews"], "kpi_names": ["pilot conversion"],
    }


def test_position_selection_does_not_imply_evidence_or_require_legacy_migration():
    review = load_review()
    data = plan()
    assert review.validate_plan(data) == []
    data["positioning"] = position()
    assert review.validate_plan(data) == []
    result = review.weekly_review(data, {"deposits": 2, "qualified_calls": 8})
    assert result["positioning"]["provenance"] == "assumption"
    assert result["positioning"] == data["positioning"]


def test_positioning_rejects_unknown_links_and_unsupported_evidence():
    review = load_review()
    data = plan()
    data["positioning"] = position()
    data["positioning"]["kpi_names"] = ["vanity KPI"]
    data["positioning"]["activities"][0]["experiment_ids"] = ["missing-test"]
    data["positioning"]["activities"][0]["provenance"] = "evidence_backed"
    errors = review.validate_plan(data)
    assert any("vanity KPI" in error for error in errors)
    assert any("missing-test" in error for error in errors)
    assert any("supporting evidence_refs" in error for error in errors)


def test_malformed_position_and_plan_return_errors_without_crashing():
    review = load_review()
    for value in (None, [], "selected"):
        data = plan()
        data["positioning"] = value
        assert review.validate_plan(data)
    assert review.validate_plan({"experiments": None})


def test_weekly_cli_flags_strategy_revision_without_rewriting_experiment(tmp_path):
    data = plan()
    data["positioning"] = position()
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(data))
    original = baseline.read_bytes()
    data["positioning"]["statement"] = "A revised strategic promise"
    active, observations = tmp_path / "strategy-plan.json", tmp_path / "observations.json"
    active.write_text(json.dumps(data))
    observations.write_text(json.dumps({"deposits": 2, "qualified_calls": 8}))
    result = subprocess.run(["python3", str(ROOT / "scripts/strategy_review.py"), "weekly-review", "--plan", str(active), "--baseline", str(baseline), "--observations", str(observations)], capture_output=True, text=True)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["positioning_changed"] is True
    assert report["kpis"][0]["status"] == "on_track"
    assert baseline.read_bytes() == original
