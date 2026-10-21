import json
from scripts.evidence_scout import build_smoke_test_kit as kit
from scripts import route_workflow


def test_kit_writes_plan_variants_and_pending_budget(tmp_path):
    run = tmp_path / 'run'; run.mkdir()
    (run / 'summary.json').write_text(json.dumps({'topic': 'expat health insurance switching', 'customer_segment': 'expats in Germany'}))
    out = kit.build(run_dir=run, experiment_id='E-pkv', assumption_ids=['A-switch'], library_id='message-smoke-test',
                    offer='Switch your PKV in 7 days with a fee-only adviser',
                    segment='English-speaking employees in Germany', variants=3, p_low=0.02, p_high=0.05,
                    out_dir=tmp_path / 'smoke')
    assert (out / 'smoke-test-plan.md').exists()
    variants = json.loads((out / 'message-variants.json').read_text())
    assert len(variants) == 3 and all({'id', 'headline', 'promise', 'cta', 'pain_frame'} <= set(v) for v in variants)
    budget = json.loads((out / 'budget-approval.json').read_text())
    assert budget['status'] == 'pending' and budget['approved_by'] is None
    assert json.loads((out / 'responders.json').read_text()) == []
    plan = (out / 'smoke-test-plan.md').read_text()
    for heading in ['## Hypothesis', '## Conversion action and thresholds', '## Disclosure', '## Budget approval', '## Responder to interview funnel', '## Stop rules']:
        assert heading in plan


def test_smoke_test_route_selects_risk_designer_mode():
    packet = route_workflow.route_request('design a landing page smoke test for my idea', intent='smoke-test-design',
                                         task_scope='strategy', check_skill='opportunity-risk-designer')
    assert packet['skill'] == 'opportunity-risk-designer' and packet['mode'] == 'smoke_test'
    assert 'references/smoke-test.md' in packet['required_references']
    assert 'references/interview-recruitment.md' in packet['required_references']


def test_sample_size_two_vs_five_percent():
    n = kit.sample_per_variant(0.02, 0.05)
    assert 400 <= n <= 700 and n == 463


def test_sample_size_rejects_inverted_rates():
    import pytest
    with pytest.raises(ValueError):
        kit.sample_per_variant(0.05, 0.02)


def test_kit_writes_draft_card_with_responders_ref(tmp_path):
    from scripts.validate_case_artifacts import load_library, validate_card
    run = tmp_path / 'run'; run.mkdir()
    (run / 'summary.json').write_text(json.dumps({'topic': 'bookkeeping delays'}))
    out = kit.build(run_dir=run, experiment_id='E-book', assumption_ids=['A-pay'], library_id='priced-fake-door',
                    offer='Bookkeeping done in 48 hours', segment='solo owners', variants=2,
                    p_low=0.02, p_high=0.05, out_dir=tmp_path / 'smoke')
    card = json.loads((out / 'experiment-card.json').read_text())
    assert card['status'] is None and card['frozen_digest'] is None and card['result'] is None
    assert card['sample_plan'] == {'p_low': 0.02, 'p_high': 0.05, 'per_variant': 463}
    assert card['hypothesis']['threshold'] == {'metric': 'booked', 'value': 47, 'sample': 926, 'window_days': 14}
    assert card['variants'] == ['V1', 'V2'] and card['responders_ref']['digest']
    assert validate_card(card, load_library(kit.ROOT)) == []
    plan = (out / 'smoke-test-plan.md').read_text()
    assert '463 qualified visitors per variant' in plan and '<x%' not in plan


def test_kit_rejects_missing_run(tmp_path):
    import pytest
    with pytest.raises(ValueError, match='existing summary'):
        kit.build(run_dir=tmp_path / 'absent', experiment_id='E-x', assumption_ids=['A-x'], library_id='message-smoke-test',
                  offer='o', segment='s', variants=2, p_low=0.02, p_high=0.05, out_dir=tmp_path / 'out')
