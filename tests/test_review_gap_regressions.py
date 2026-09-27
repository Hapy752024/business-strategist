"""Regression evidence for the five reproduced review gaps."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import case_workspace as cases
from scripts import run_live_evals as live
from scripts.case_economics import calculate
from scripts.evidence_scout import build_smoke_test_kit as smoke
from test_case_economics import cash_inputs

ROOT = Path(__file__).resolve().parents[1]


def test_live_empty_catalog_answers_never_pass():
    for path in (ROOT / '.agents/skills').glob('*/evals/evals.json'):
        for case in json.loads(path.read_text()).get('evals', []):
            assert not live.score(case, '')['passed']
    assert live.score({'id': 1}, 'arbitrary text')['status'] == 'unscored'


def test_live_model_error_cannot_be_scored(monkeypatch):
    monkeypatch.setattr(live.subprocess, 'run', lambda *a, **kw: SimpleNamespace(
        returncode=0, stdout=json.dumps({'is_error': True, 'result': 'segment assumption'})))
    with pytest.raises(RuntimeError, match='error'):
        live.run_case('idea-grill', {'prompt': 'synthetic'})


def test_viability_unknown_future_and_unfunded_owner_income():
    d = cash_inputs(); d['viability_targets'] = {'profitable_by_month': 24}
    v = calculate(d)['results']['viability']
    assert v['status'] == 'unresolved' and v['profit_target_met'] is None
    d.update(opening_cash=0, sales_per_month=[0]*6, viability_targets={'owner_income_per_month': 2500})
    v = calculate(d)['results']['viability']
    assert v['status'] == 'fail' and v['owner_income_met'] is False
    d['viability_targets']['profitable_by_month'] = 24
    assert calculate(d)['results']['viability']['status'] == 'fail'


def test_viability_profit_accounts_for_declared_imputed_labor():
    d = cash_inputs(); d.update(sales_per_month=[100]*6, imputed_owner_labor_per_month=2000,
                              viability_targets={'profitable_by_month':6})
    assert calculate(d)['results']['viability']['profit_target_met'] is False


def case_run(tmp_path):
    root = tmp_path / 'project'; cases.initialize(root, 'Synthetic')
    scope = cases.add_case(root, 'a', 'A')
    cases.add_case(root, 'b', 'B')
    run = scope / 'market_research/pain_points/runs/source'; run.mkdir(parents=True)
    (run / 'summary.json').write_text(json.dumps({'topic':'fixture', 'customer_segment':'fixture users'}))
    return root, scope, run


def build(run, out, **kwargs):
    return smoke.build(run_dir=run, hypothesis_id='H1', offer='Synthetic offer', segment='fixture users',
                       variants=2, out_dir=out, **kwargs)


def test_smoke_requires_real_source_and_registered_output(tmp_path):
    with pytest.raises(ValueError, match='existing summary'):
        build(tmp_path / 'absent', tmp_path / 'out')
    root, scope, run = case_run(tmp_path)
    with pytest.raises(ValueError, match='authority'):
        build(run, tmp_path / 'outside')
    with pytest.raises(ValueError, match='immutable research runs'):
        build(run, scope / 'wrong')
    out = build(run, run / 'experiments/smoke')
    context = json.loads((out / '.case-context.json').read_text())
    assert any(b['path'].endswith('source/summary.json') for b in context['source_bindings'])
    with pytest.raises(ValueError, match='fresh'):
        build(run, out)
    other = cases.resolve(root, 'b') / 'market_research/pain_points/runs/smoke'
    with pytest.raises(ValueError, match='shared research input'):
        build(run, other)


def test_interview_responders_are_bound_and_cross_case_inputs_rejected(tmp_path):
    root, scope, run = case_run(tmp_path)
    responders = run / 'responders.json'
    responders.write_text(json.dumps([{'id':'R1','variant':'V1','source':'fixture'}]))
    command = [sys.executable, str(ROOT / 'scripts/evidence_scout/build_interview_kit.py'),
               '--run-dir', str(run), '--responders', str(responders), '--allow-empty-evidence']
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    context_paths = list(run.glob('interview-*/.case-context.json'))
    assert len(context_paths) == 1
    bindings = json.loads(context_paths[0].read_text())['source_bindings']
    binding = next(b for b in bindings if b['path'].endswith('responders.json'))
    assert binding == cases.source_binding(root, binding['path'], locator=binding['locator'], applicability=binding['applicability'])
    other = cases.resolve(root,'b') / 'market_research/responders.json'; other.write_text(responders.read_text())
    command[command.index('--responders')+1] = str(other)
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'shared research input' in result.stderr
    assert len(list(run.glob('interview-*'))) == 1


def test_brand_audit_accepts_lean_but_checks_started_optional_stages(tmp_path):
    import runpy
    audit = runpy.run_path(str(ROOT / '.agents/skills/brand-quality-reviewer/scripts/audit-brand-package.py'))
    for path in ('BRAND-GUIDELINES.md','DECISIONS.md','PACKAGE-MANIFEST.md'):
        (tmp_path / path).write_text('Synthetic lean package')
    for path in ('logos/source','logos/export','colors','typography','qa'):
        (tmp_path / path).mkdir(parents=True)
    manifest = tmp_path / 'brand-manifest.json'
    manifest.write_text(json.dumps({'stages':{'motion':'skipped','components':'not_started'}}))
    assert audit['check_required'](tmp_path) == []
    manifest.write_text(json.dumps({'stages':{'motion':'not_started'}, 'requested_deliverables':['motion']}))
    assert 'motion/motion-guidelines.md' in audit['check_required'](tmp_path)
    manifest.write_text(json.dumps({'stages':{'motion':'approved','components':'in_progress'}}))
    missing = audit['check_required'](tmp_path)
    assert 'motion/motion-guidelines.md' in missing and 'components/README.md' in missing


def test_smoke_to_interview_cli_flow(tmp_path):
    from scripts.route_workflow import route_request
    packet = route_request('design a smoke test', intent='smoke-test-design', task_scope='strategy')
    assert packet['mode'] == 'smoke_test' and not packet.get('gate_blocked')
    page = route_request('build a validation page', intent='validation-page', task_scope='execution', entry_mode='standalone')
    assert page['mode'] == 'validation_page' and not page.get('gate_blocked')
    run = tmp_path / 'run'; run.mkdir()
    (run / 'summary.json').write_text(json.dumps({'topic':'synthetic test','customer_segment':'fixture users'}))
    out = run / 'experiments/smoke'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/build_smoke_test_kit.py'),
        '--run-dir', str(run), '--hypothesis-id', 'H1', '--offer', 'Synthetic offer', '--segment', 'fixture users',
        '--out-dir', str(out)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads((out / 'budget-approval.json').read_text())['status'] == 'pending'
    responders = out / 'responders.json'
    responders.write_text(json.dumps([{'id':'R1','variant':'V1','source':'synthetic'}]))
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/build_interview_kit.py'),
        '--run-dir', str(run), '--responders', str(responders), '--allow-empty-evidence'], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    tracker = (run / 'interview/interview-tracker.md').read_text()
    assert '| R1 | V1 | synthetic | unresolved | unresolved |' in tracker


def test_live_cli_records_unscored_and_returns_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['run_live_evals.py','--skill','fixture','--live','--out',str(tmp_path)])
    monkeypatch.setattr(live, 'load_cases', lambda skill: [{'id':'one','prompt':'fixture'}])
    monkeypatch.setattr(live, 'run_case', lambda skill, case: 'An answer without an assertion contract')
    assert live.main() == 1
    result = json.loads((tmp_path / 'fixture-one.json').read_text())
    assert result['status'] == 'unscored' and result['passed'] is False
