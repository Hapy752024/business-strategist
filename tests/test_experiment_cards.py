"""Experiment card lifecycle: plan, approve, start, close and the learn loop into the register."""
import json

import pytest

from scripts import case_workspace as c

FUNNEL = ('identified', 'exposed', 'responded', 'eligible', 'booked', 'attended', 'usable_incident')


def topic(tmp_path):
    p = tmp_path / 'topic'
    c.initialize(p, 'Topic')
    c.add_case(p, 'a', 'A')
    c.publish_assumptions(p, 'a', {'revision': 1, 'owner_module': 'idea-grill', 'entries': [{
        'id': 'A-pay', 'statement': 'Owners pay for monthly bookkeeping help.', 'type': 'viability',
        'importance': 'critical', 'status': 'unknown', 'evidence_refs': [], 'counter_evidence_refs': [],
        'confidence_note': 'Not checked.'}]}, 'seed', 'seed register')
    return p


def draft(exp_id='E-one', library_id='unit-economics-run', **extra):
    card = {'schema_version': 1, 'id': exp_id, 'library_id': library_id, 'assumption_ids': ['A-pay'],
            'hypothesis': {'segment': 'owners', 'action': 'book a call', 'problem': 'manual bookkeeping',
                           'threshold': {'metric': 'booked', 'value': 5, 'sample': 200, 'window_days': 14}},
            'kill_rule': 'Fewer than 5 bookings from 200 qualified visitors.',
            'sample_plan': {'p_low': 0.02, 'p_high': 0.05, 'per_variant': 100}, 'channel': 'linkedin',
            'variants': ['V1', 'V2'], 'status': None, 'authorization_refs': [], 'responders_ref': None,
            'supersedes': None, 'result': None, 'frozen_digest': None}
    card.update(extra)
    return card


def approval(p, status='approved'):
    path = p / 'cases/a/market_research/smoke/budget-approval.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'status': status}))
    return {'path': 'cases/a/market_research/smoke/budget-approval.json', 'digest': c.digest(path.read_bytes())}


def result(booked_v1, booked_v2=0, interpretation='pass', updates=None):
    def funnel(booked):
        return {k: (booked if k in {'booked', 'attended', 'usable_incident'} else 100) for k in FUNNEL}
    return {'counts': {'V1': {'linkedin': funnel(booked_v1)}, 'V2': {'linkedin': funnel(booked_v2)}},
            'interpretation': interpretation,
            'assumption_updates': updates if updates is not None else [{'assumption_id': 'A-pay', 'to': 'supported', 'reason': 'Bookings above threshold.'}],
            'limits': ['Bookings show intent to talk, not willingness to pay.']}


def test_plan_freezes_hypothesis(tmp_path):
    p = topic(tmp_path)
    card = c.experiment_plan(p, 'a', draft(), 'plan-1', 'plan experiment')
    assert card['status'] == 'planned' and len(card['frozen_digest']) == 64
    assert c.experiment_card(p, 'a', 'E-one') == card
    assert [x['id'] for x in c.experiment_cards(p, 'a')] == ['E-one']


def test_plan_rejects_unregistered_assumption(tmp_path):
    p = topic(tmp_path)
    with pytest.raises(ValueError, match='not in the register'):
        c.experiment_plan(p, 'a', draft(assumption_ids=['A-ghost']), 'plan-1', 'plan')


def test_plan_rejects_duplicate_id(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(), 'plan-1', 'plan')
    with pytest.raises(ValueError, match='already exists'):
        c.experiment_plan(p, 'a', draft(), 'plan-2', 'plan again')


def test_approve_requires_budget_when_ad_spend(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(library_id='message-smoke-test'), 'plan-1', 'plan')
    with pytest.raises(ValueError, match='authorization'):
        c.experiment_transition(p, 'a', 'E-one', 'approve', 'approve-1', 'approve')


def test_approve_rejects_pending_budget(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(library_id='message-smoke-test', authorization_refs=[approval(p, 'pending')]), 'plan-1', 'plan')
    with pytest.raises(ValueError, match='not approved'):
        c.experiment_transition(p, 'a', 'E-one', 'approve', 'approve-1', 'approve')


def test_approve_and_start_with_approved_budget(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(library_id='message-smoke-test', authorization_refs=[approval(p)]), 'plan-1', 'plan')
    c.experiment_transition(p, 'a', 'E-one', 'approve', 'approve-1', 'approve')
    card = c.experiment_transition(p, 'a', 'E-one', 'start', 'start-1', 'start')
    assert card['status'] == 'running'


def test_start_requires_approved(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(), 'plan-1', 'plan')
    with pytest.raises(ValueError, match='approved'):
        c.experiment_transition(p, 'a', 'E-one', 'start', 'start-1', 'start')


def test_supersede_marks_old_card(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(), 'plan-1', 'plan')
    c.experiment_plan(p, 'a', draft(exp_id='E-two', supersedes='E-one', kill_rule='Fewer than 6 bookings from 200 visitors.'), 'plan-2', 'fix kill rule')
    assert c.experiment_card(p, 'a', 'E-one')['status'] == 'superseded'
    assert c.experiment_card(p, 'a', 'E-two')['status'] == 'planned'


def _approved(p):
    c.experiment_plan(p, 'a', draft(), 'plan-1', 'plan')
    c.experiment_transition(p, 'a', 'E-one', 'approve', 'approve-1', 'approve')


def test_close_rejects_pass_below_threshold(tmp_path):
    p = topic(tmp_path)
    _approved(p)
    with pytest.raises(ValueError, match='pass below predeclared threshold'):
        c.experiment_close(p, 'a', 'E-one', result(2, 2), 'close-1', 'close')


def test_close_updates_assumption_with_card_ref(tmp_path):
    p = topic(tmp_path)
    _approved(p)
    c.experiment_close(p, 'a', 'E-one', result(3, 3), 'close-1', 'bookings above threshold')
    card = c.experiment_card(p, 'a', 'E-one')
    entry = c.assumption_register(p, 'a')['entries'][0]
    assert card['status'] == 'closed'
    assert entry['status'] == 'supported' and entry['owner_module'] == 'opportunity-risk-designer'
    assert entry['evidence_refs'][-1]['path'] == 'cases/a/experiments/E-one.json'
    assert entry['evidence_refs'][-1]['digest'] == c.digest((p / 'cases/a/experiments/E-one.json').read_bytes())


def test_close_stop_refutes_assumption(tmp_path):
    p = topic(tmp_path)
    _approved(p)
    c.experiment_close(p, 'a', 'E-one', result(0, 1, 'stop', [{'assumption_id': 'A-pay', 'to': 'refuted', 'reason': 'One booking.'}]), 'close-1', 'stop')
    assert c.assumption_register(p, 'a')['entries'][0]['status'] == 'refuted'


def test_close_from_planned_rejected(tmp_path):
    p = topic(tmp_path)
    c.experiment_plan(p, 'a', draft(), 'plan-1', 'plan')
    with pytest.raises(ValueError, match='approved or running'):
        c.experiment_close(p, 'a', 'E-one', result(3, 3), 'close-1', 'close')


def test_close_rejects_update_for_unbound_assumption(tmp_path):
    p = topic(tmp_path)
    _approved(p)
    with pytest.raises(ValueError, match='not tested by this experiment'):
        c.experiment_close(p, 'a', 'E-one', result(3, 3, updates=[{'assumption_id': 'A-other', 'to': 'supported', 'reason': 'x'}]), 'close-1', 'close')


def test_experiment_cli_plan(tmp_path):
    p = topic(tmp_path)
    path = tmp_path / 'card.json'
    path.write_text(json.dumps(draft()))
    assert c.main(['experiment-plan', '--workspace', str(p), '--case', 'a', '--input', str(path),
                   '--decision-id', 'cli-plan', '--reason', 'plan']) == 0
    assert c.experiment_card(p, 'a', 'E-one')['status'] == 'planned'
