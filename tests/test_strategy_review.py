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


def detailed_position():
    """Synthetic transfer case: a route service, not the source video's examples."""
    from copy import deepcopy
    data = position()
    data['need_refs'] = ['research/synthesis.json#U-route-reliability']
    def claim(statement, provenance='assumption', refs=None):
        return {'statement': statement, 'provenance': provenance, 'evidence_refs': refs or []}
    data['value_proposition'] = {field: claim(value) for field, value in {
        'segment': 'Independent repair shops', 'situation': 'Scheduled parts collection',
        'outcome': 'Predictable collection window', 'alternative': 'Ad hoc courier booking',
        'mechanism': 'Fixed dense routes', 'boundaries': 'Within a defined district',
        'sacrifices': 'No same-day exceptions',
    }.items()}
    data['value_proposition']['situation'] = claim('Scheduled parts collection', 'evidence_backed', ['synthetic:episode-1'])
    data['activities'][0]['id'] = 'schedule'
    second = deepcopy(data['activities'][0]); second['id'] = 'density'
    data['activities'].append(second)
    data['activities'][0]['relations'] = [{'type': 'reinforces', 'target': 'density'}]
    data['activities'][1]['relations'] = [{'type': 'reinforces', 'target': 'schedule'}]
    data['defensibility'] = {
        'status': 'hypothesis', 'rationale': 'Density may improve costs but entry is untested',
        'scope': 'One district; fixed-route service', 'assessed_at': '2026-09-17',
        'hypotheses': [{
            'economic_benefit': claim('Lower travel cost per stop'),
            'imitation_barrier': claim('Insufficient available volume for a duplicate route', 'inference'),
            'value_capture': claim('Savings remain after customer discounts'),
            'formation': 'Requires route density; cost and time unresolved',
            'incumbent_response': 'Can consolidate its existing customers',
            'entrant_response': 'Can target an adjacent district or subsidize entry',
            'erosion_conditions': 'Customers spread out or switch routes',
            'activity_ids': ['schedule', 'density'], 'experiment_ids': ['interviews'],
            'kpi_names': ['pilot conversion'],
        }],
    }
    return data


def test_optional_contract_accepts_mixed_claims_and_reinforcement_cycles():
    review = load_review()
    data = plan(); data['positioning'] = detailed_position()
    assert review.validate_plan(data) == []
    assert review.validate_positioning(data['positioning']) == []
    result = review.weekly_review(data, {'deposits': 2, 'qualified_calls': 8})
    assert result['positioning'] == data['positioning']
    assert result['positioning']['defensibility']['status'] == 'hypothesis'


def test_activity_and_defense_links_reject_dangling_ids():
    review = load_review()
    data = plan(); data['positioning'] = detailed_position()
    pos = data['positioning']
    pos['activities'][0]['relations'][0]['target'] = 'absent'
    pos['activities'][1]['id'] = 'schedule'
    hyp = pos['defensibility']['hypotheses'][0]
    hyp['activity_ids'] = ['missing-activity']
    hyp['experiment_ids'] = ['missing-test']
    hyp['kpi_names'] = ['missing-metric']
    errors = review.validate_plan(data)
    for message in ['IDs must be unique', 'unknown activity absent', 'missing-activity', 'missing-test', 'missing-metric']:
        assert any(message in error for error in errors), errors
    pos['activities'][0].pop('id')
    assert any('source activity id' in e for e in review.validate_plan(data))


def test_supported_defense_needs_declared_support_per_economic_claim():
    review = load_review()
    data = plan(); data['positioning'] = detailed_position()
    pos = data['positioning']; pos['defensibility']['status'] = 'supported'
    assert any('supported assessment' in e for e in review.validate_plan(data))
    for name in ['economic_benefit', 'imitation_barrier', 'value_capture']:
        claim = pos['defensibility']['hypotheses'][0][name]
        claim['provenance'] = 'evidence_backed'
        assert any('supporting evidence_refs' in e for e in review.validate_plan(data))
        claim['evidence_refs'] = ['synthetic:verified-' + name]
    assert review.validate_plan(data) == []  # Declared support is not verified strategic truth.
    pos['value_proposition']['mechanism']['provenance'] = 'evidence_backed'
    assert any('value_proposition.mechanism' in e for e in review.validate_plan(data))


def test_no_moat_and_not_assessed_are_valid_without_manufactured_hypotheses():
    review = load_review()
    data = plan(); data['positioning'] = detailed_position()
    defense = data['positioning']['defensibility']
    for status in ['none_identified', 'not_assessed']:
        defense.update(status=status, hypotheses=[], rationale='No supported barrier in this scope')
        assert review.validate_plan(data) == []
    defense['status'] = 'emerging'
    assert review.validate_plan(data)


def test_malformed_optional_fields_return_errors_without_crashing():
    from copy import deepcopy
    review = load_review()
    baseline = detailed_position()
    for field, bad in [('need_refs', [' ']), ('value_proposition', None), ('defensibility', 'durable'), ('defensibility', {'status': 'supported'})]:
        data = plan(); data['positioning'] = deepcopy(baseline)
        data['positioning'][field] = bad
        assert review.validate_plan(data)
    for field, value in [('assessed_at', 'yesterday'), ('status', 'permanent')]:
        data = plan(); data['positioning'] = deepcopy(baseline)
        data['positioning']['defensibility'][field] = value
        assert review.validate_plan(data)
    data = plan(); data['positioning'] = deepcopy(baseline)
    data['positioning']['activities'][0]['relations'][0]['type'] = 'guarantees'
    assert review.validate_plan(data)


def test_defense_revision_flags_baseline_without_changing_tests(tmp_path):
    data = plan(); data['positioning'] = detailed_position()
    baseline = tmp_path / 'baseline.json'; baseline.write_text(json.dumps(data))
    original = baseline.read_bytes()
    data['positioning']['defensibility']['hypotheses'][0]['entrant_response'] = 'New entrant has signed anchor customers'
    active = tmp_path / 'strategy-plan.json'; active.write_text(json.dumps(data))
    observed = tmp_path / 'observations.json'; observed.write_text(json.dumps({'deposits': 2, 'qualified_calls': 8}))
    result = subprocess.run(['python3', str(ROOT / 'scripts/strategy_review.py'), 'weekly-review', '--plan', str(active), '--baseline', str(baseline), '--observations', str(observed)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['positioning_changed'] is True
    assert baseline.read_bytes() == original
