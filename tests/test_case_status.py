"""Router status: runnable, blocked, stale and not-adopted routes for a case."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import case_status as st
from scripts import case_workspace as c

ROOT = Path(__file__).resolve().parents[1]


def project(tmp_path):
    p = tmp_path / 'biz'
    c.initialize(p, 'Biz')
    c.add_case(p, 'a', 'A')
    c.publish_assumptions(p, 'a', {'revision': 1, 'owner_module': 'idea-grill', 'entries': [{
        'id': 'A-pay', 'statement': 'Owners pay for monthly bookkeeping help.', 'type': 'viability',
        'importance': 'critical', 'status': 'unknown', 'evidence_refs': [], 'counter_evidence_refs': [],
        'confidence_note': 'Not checked.'}]}, 'seed', 'seed')
    return p


def by_route(rows):
    return {r['route_id']: r for r in rows}


def test_status_reports_blocked_without_evidence_run(tmp_path):
    rows = by_route(st.case_status(project(tmp_path), 'a'))
    assert rows['smoke-test-design']['state'] == 'blocked'
    assert 'evidence-run' in rows['smoke-test-design']['missing']
    assert rows['idea-validation']['state'] == 'runnable'


def test_status_not_adopted_without_register(tmp_path):
    p = project(tmp_path)
    (p / 'cases/a/assumptions.json').unlink()
    rows = by_route(st.case_status(p, 'a'))
    assert rows['smoke-test-design']['state'] == 'not_adopted'


def _run(p):
    run = p / 'cases/a/market_research/pain_points/runs/r1'
    run.mkdir(parents=True)
    (run / 'summary.json').write_text(json.dumps({'topic': 'bookkeeping'}))
    return run


def test_status_interview_bridge_runnable_after_booking(tmp_path):
    p = project(tmp_path)
    run = _run(p)
    rows = by_route(st.case_status(p, 'a'))
    assert rows['interview-bridge']['state'] == 'runnable' and 'responders' not in rows['interview-bridge']['notes']
    from scripts.evidence_scout import build_smoke_test_kit as kit
    out = kit.build(run_dir=run, experiment_id='E-s', assumption_ids=['A-pay'], library_id='unit-economics-run',
                    offer='o', segment='s', variants=1, p_low=0.02, p_high=0.05, out_dir=run / 'experiments/s')
    card = json.loads((out / 'experiment-card.json').read_text()); card['authorization_refs'] = []
    c.experiment_plan(p, 'a', card, 'plan', 'plan')
    c.experiment_transition(p, 'a', 'E-s', 'approve', 'approve', 'approve')
    funnel = {k: 1 for k in ('identified', 'exposed', 'responded', 'eligible', 'booked', 'attended', 'usable_incident')}
    c.experiment_close(p, 'a', 'E-s', {'counts': {'V1': {'ads': funnel}}, 'interpretation': 'repeat',
                                       'assumption_updates': [], 'limits': ['one booking']}, 'close', 'close')
    rows = by_route(st.case_status(p, 'a'))
    assert rows['interview-bridge']['state'] == 'runnable'
    assert 'cases/a/market_research/pain_points/runs/r1/experiments/s/responders.json' in rows['interview-bridge']['notes']


def test_status_stale_when_bound_source_changed(tmp_path):
    p = project(tmp_path)
    ledger = p / 'cases/a/market_research/pain_points/runs/r1/customer-feedback/claim-ledger.json'
    ledger.parent.mkdir(parents=True)
    ledger.write_text('[]')
    _ = (p / 'cases/a/market_research/pain_points/runs/r1/summary.json').write_text('{}')
    manifest = p / 'cases/a/market_research/manifest.json'
    m = json.loads(manifest.read_text())
    m['source_bindings'] = [{'path': 'cases/a/market_research/pain_points/runs/r1/customer-feedback/claim-ledger.json',
                             'digest': '0' * 64, 'locator': 'x', 'applicability': 'case a'}]
    manifest.write_text(json.dumps(m))
    rows = by_route(st.case_status(p, 'a'))
    assert rows['case-appraisal']['state'] == 'stale' and rows['case-appraisal']['stale'] == ['claim-ledger']


def test_status_plan_stale_when_insights_pending(tmp_path):
    p = project(tmp_path)
    manifest = p / 'cases/a/market_research/manifest.json'
    m = json.loads(manifest.read_text()); m['insights']['state'] = 'update_pending'; manifest.write_text(json.dumps(m))
    rows = by_route(st.case_status(p, 'a'))
    assert rows['case-business-plan']['state'] == 'stale'


def test_status_refuses_pending_workspace(tmp_path):
    p = project(tmp_path)
    (p / 'history/pending.json').write_text('{}')
    with pytest.raises(SystemExit) as exc:
        st.case_status(p, 'a')
    assert exc.value.code == 2


def test_router_status_subcommand_and_positional_request_still_work(tmp_path):
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/route_workflow.py'), 'status', '--workspace',
                           str(project(tmp_path)), '--case', 'a', '--json'], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert any(r['route_id'] == 'smoke-test-design' for r in json.loads(done.stdout))
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/route_workflow.py'), 'find customer problems',
                           '--intent', 'market-discovery'], capture_output=True, text=True)
    assert done.returncode == 0 and json.loads(done.stdout)['skill'] == 'market-problem-discovery'
