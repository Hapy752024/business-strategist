"""Assumption register lifecycle in the case workspace."""
import json

import pytest

from scripts import case_workspace as c


def topic(tmp_path):
    p = tmp_path / 'topic'
    c.initialize(p, 'Topic')
    c.add_case(p, 'a', 'A')
    return p


def test_add_case_creates_empty_register(tmp_path):
    p = topic(tmp_path)
    reg = c.assumption_register(p, 'a')
    assert reg['entries'] == [] and reg['revision'] == 1 and reg['case_id'] == 'a'
    assert c.register_adopted(p, 'a')


def test_initial_insights_has_v3_sections(tmp_path):
    text = (topic(tmp_path) / 'cases/a/case_insights.md').read_text()
    assert '## What would change this recommendation' in text
    assert text.index('## What we could not check') < text.index('## Sources')


def test_legacy_case_without_register_not_adopted(tmp_path):
    p = topic(tmp_path)
    (p / 'cases/a/assumptions.json').unlink()
    assert not c.register_adopted(p, 'a')
    with pytest.raises(FileNotFoundError):
        c.assumption_register(p, 'a')


LEDGER = 'cases/a/market_research/runs/r1/customer-feedback/claim-ledger.json'


def with_ledger(p, claims=('c1', 'c2')):
    path = p / LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'claims': [{'claim_id': cid, 'text': 'x'} for cid in claims]}))
    return {'path': LEDGER, 'digest': c.digest(path.read_bytes()), 'id': 'c1'}


def entry(aid='A-pay', status='unknown', importance='critical', refs=(), counter=()):
    return {'id': aid, 'statement': 'Owners pay for monthly bookkeeping help.', 'type': 'viability',
            'importance': importance, 'status': status, 'evidence_refs': list(refs),
            'counter_evidence_refs': list(counter), 'confidence_note': 'Not checked.'}


def publish(p, entries, owner='idea-grill', did='reg-1', revision=None):
    rev = c.assumption_register(p, 'a')['revision'] if revision is None else revision
    return c.publish_assumptions(p, 'a', {'revision': rev, 'owner_module': owner, 'entries': entries}, did, 'update register')


def test_publish_register_sets_riskiest_and_history(tmp_path):
    p = topic(tmp_path)
    publish(p, [entry('A-low', importance='low'), entry('A-pay')])
    reg = c.assumption_register(p, 'a')
    assert reg['revision'] == 2 and reg['riskiest'][0] == 'A-pay'
    assert reg['entries'][0]['history'][0]['to'] == 'unknown'
    assert reg['entries'][0]['history'][0]['reason'] == 'update register'
    assert reg['entries'][0]['owner_module'] == 'idea-grill'


def test_publish_register_marks_current_insights_pending(tmp_path):
    p = topic(tmp_path)
    manifest = p / 'cases/a/market_research/manifest.json'
    m = json.loads(manifest.read_text()); m['insights']['state'] = 'current'; manifest.write_text(json.dumps(m))
    publish(p, [entry()])
    assert c.case_manifest(p, 'a')['insights']['state'] == 'update_pending'
    assert 'Assessment update pending' in (p / 'cases/a/case_insights.md').read_text()


def test_register_supported_with_resolving_ref(tmp_path):
    p = topic(tmp_path)
    ref = with_ledger(p)
    publish(p, [entry(status='supported', refs=[ref])], owner='evidence-scout')
    assert c.assumption_register(p, 'a')['entries'][0]['status'] == 'supported'


def test_register_rejects_outside_path(tmp_path):
    p = topic(tmp_path)
    ref = with_ledger(p)
    (p / 'notes.json').write_text('{"claim_id": "c1"}')
    bad = {'path': 'notes.json', 'digest': c.digest((p / 'notes.json').read_bytes()), 'id': 'c1'}
    with pytest.raises(ValueError, match='case-local'):
        publish(p, [entry(status='supported', refs=[bad])])


def test_register_rejects_stale_ref_digest(tmp_path):
    p = topic(tmp_path)
    ref = with_ledger(p)
    (p / LEDGER).write_text(json.dumps({'claims': [{'claim_id': 'c1', 'text': 'changed'}]}))
    with pytest.raises(ValueError, match='stale'):
        publish(p, [entry(status='supported', refs=[ref])])


def test_register_rejects_unresolved_ref_id(tmp_path):
    p = topic(tmp_path)
    ref = dict(with_ledger(p), id='c9')
    with pytest.raises(ValueError, match='does not resolve'):
        publish(p, [entry(status='supported', refs=[ref])])


def test_register_rejects_refuted_from_other_module(tmp_path):
    p = topic(tmp_path)
    ref = with_ledger(p)
    with pytest.raises(ValueError, match='opportunity-risk-designer'):
        publish(p, [entry(status='refuted', counter=[ref])], owner='evidence-scout')


def test_register_rejects_revision_conflict(tmp_path):
    p = topic(tmp_path)
    with pytest.raises(ValueError, match='revision'):
        publish(p, [entry()], revision=7)


def test_register_rejects_removed_entry(tmp_path):
    p = topic(tmp_path)
    publish(p, [entry('A-one'), entry('A-two')])
    with pytest.raises(ValueError, match='removed'):
        publish(p, [entry('A-one')], did='reg-2')


def test_register_cli(tmp_path):
    p = topic(tmp_path)
    draft = tmp_path / 'draft.json'
    draft.write_text(json.dumps({'revision': 1, 'owner_module': 'idea-grill', 'entries': [entry()]}))
    assert c.main(['assumptions', '--workspace', str(p), '--case', 'a', '--input', str(draft),
                   '--decision-id', 'cli-reg', '--reason', 'seed']) == 0
    assert c.assumption_register(p, 'a')['revision'] == 2
