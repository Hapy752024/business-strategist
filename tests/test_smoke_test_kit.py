import json
from scripts.evidence_scout import build_smoke_test_kit as kit
from scripts import route_workflow


def test_kit_writes_plan_variants_and_pending_budget(tmp_path):
    run = tmp_path / 'run'; run.mkdir()
    (run / 'summary.json').write_text(json.dumps({'topic': 'expat health insurance switching', 'customer_segment': 'expats in Germany'}))
    out = kit.build(run_dir=run, hypothesis_id='H1', offer='Switch your PKV in 7 days with a fee-only adviser',
                    segment='English-speaking employees in Germany', variants=3, out_dir=tmp_path / 'smoke')
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
