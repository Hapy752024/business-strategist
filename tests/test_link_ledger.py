import json

import pytest

from scripts.marketing import link_ledger as ll

CANDIDATES = {'candidates': [
    {'source_url': 'https://expat-blog.com/post', 'flags': [], 'links_to': [{'competitor': 'a.com'}, {'competitor': 'b.com'}]},
    {'source_url': 'https://pbn.biz/x', 'flags': ['link_seller_page'], 'links_to': [{'competitor': 'a.com'}]}]}


def observation(source, target, outcome, rel=None, checked='2026-11-05T10:00:00+00:00'):
    anchors = [{'href': ll.url_key(target), 'rel': rel, 'text': 'guide'}] if outcome == 'present' else []
    return {'source_url': source, 'target_url': target, 'outcome': outcome, 'checked_at': checked, 'anchors': anchors}


@pytest.fixture
def ledger():
    doc = ll.new_ledger('https://www.italyforretirees.com')
    assert doc['property'] == 'italyforretirees.com'
    return doc


def test_import_candidates_splits_prospects_from_flagged_and_is_idempotent(ledger):
    added = ll.import_candidates(ledger, CANDIDATES, candidates_path='competitor-backlinks/candidates.json', at='2026-10-31')
    assert added == {'prospect': 1, 'rejected': 1, 'skipped_existing': 0}
    rows = {r['source_domain']: r for r in ledger['rows']}
    assert rows['expat-blog.com']['stage'] == 'prospect' and 'a.com, b.com' in rows['expat-blog.com']['history'][0]['note']
    assert rows['pbn.biz']['stage'] == 'rejected' and 'link_seller_page' in rows['pbn.biz']['history'][0]['note']
    assert ll.import_candidates(ledger, CANDIDATES, candidates_path='x', at='2026-11-01')['skipped_existing'] == 2
    assert ll.validate(ledger) == []


def test_manual_stages_follow_the_allowed_path(ledger):
    ll.import_candidates(ledger, CANDIDATES, candidates_path='c.json', at='2026-10-31')
    src = 'https://expat-blog.com/post'
    with pytest.raises(ValueError, match='needs --target'):
        ll.set_stage(ledger, src, 'pitched', at='2026-11-01')
    with pytest.raises(ValueError, match='cannot move prospect -> promised'):
        ll.set_stage(ledger, src, 'promised', at='2026-11-01')
    ll.set_stage(ledger, src, 'pitched', at='2026-11-01', target_url='https://italyforretirees.com/guide/codice-fiscale', note='email 1')
    ll.set_stage(ledger, src, 'pitched', at='2026-11-08', note='follow-up')
    ll.set_stage(ledger, src, 'promised', at='2026-11-09', note='editor said yes')
    row = ll._row(ledger, src)
    assert [h['stage'] for h in row['history']] == ['prospect', 'pitched', 'pitched', 'promised']
    with pytest.raises(ValueError, match='only from a recorded observation'):
        ll.set_stage(ledger, src, 'live')
    assert ll.validate(ledger) == []


def test_observation_moves_live_then_lost_and_keeps_rel(ledger):
    src, tgt = 'https://expat-blog.com/post', 'https://italyforretirees.com/guide/codice-fiscale'
    ll.set_stage(ledger, src, 'prospect', at='2026-10-31')
    ll.set_stage(ledger, src, 'pitched', at='2026-11-01', target_url=tgt)
    ll.record(ledger, observation(src, tgt, 'present', rel='nofollow'), observation_path='link-checks/1/observation.json')
    row = ll._row(ledger, src)
    assert row['stage'] == 'live' and row['last_observation']['rel'] == 'nofollow' and row['last_checked_at'] == '2026-11-05'
    ll.record(ledger, observation(src, tgt, 'access_limited', checked='2026-12-01T00:00:00+00:00'), observation_path='link-checks/2/observation.json')
    assert row['stage'] == 'live' and row['last_checked_at'] == '2026-12-01'
    ll.record(ledger, observation(src, tgt, 'absent', checked='2027-01-01T00:00:00+00:00'), observation_path='link-checks/3/observation.json')
    assert row['stage'] == 'lost' and row['history'][-1] == {'stage': 'lost', 'at': '2027-01-01', 'note': 'observed absent', 'source': 'observation'}
    with pytest.raises(ValueError, match='target differs'):
        ll.record(ledger, observation(src, 'https://italyforretirees.com/other', 'present'), observation_path='x')
    rep = ll.report(ledger, today='2027-01-02')
    assert rep['counts']['lost'] == 1 and rep['live_domains'] == []


def test_search_console_import_is_reported_not_live(ledger):
    export = {'exported_at': '2026-11-02', 'candidates': [{'source_url': 'https://kiplinger.com/a', 'target_url': 'https://italyforretirees.com/'}]}
    assert ll.import_links(ledger, export, export_path='gsc.json') == {'reported': 1, 'skipped_existing': 0}
    row = ledger['rows'][0]
    assert row['stage'] == 'promised' and row['origin'] == 'search_console' and row['target_url'] == 'https://italyforretirees.com/'
    assert ll.due_checks(ledger) == [row]


def test_report_lists_overdue_follow_ups_and_renders(ledger):
    ll.set_stage(ledger, 'https://one.com/p', 'prospect', at='2026-10-01')
    ll.set_stage(ledger, 'https://one.com/p', 'pitched', at='2026-10-01', target_url='https://italyforretirees.com/check')
    ll.set_stage(ledger, 'https://two.com/p', 'prospect', at='2026-10-01')
    ll.set_stage(ledger, 'https://two.com/p', 'pitched', at='2026-10-01', target_url='https://italyforretirees.com/check')
    ll.set_stage(ledger, 'https://two.com/p', 'pitched', at='2026-10-08', note='follow-up sent')
    rep = ll.report(ledger, today='2026-10-09')
    assert [o['source_url'] for o in rep['overdue_follow_ups']] == ['https://one.com/p']
    md = ll.render(rep)
    assert '| pitched | 2 |' in md and 'https://one.com/p (pitched 2026-10-01)' in md and 'not ranking credit' in md


def test_check_runs_bounded_and_records(ledger, tmp_path):
    for i in range(3):
        ll.import_links(ledger, {'exported_at': '2026-11-02', 'candidates': [{'source_url': f'https://s{i}.com/a', 'target_url': 'https://italyforretirees.com/'}]}, export_path='g.json')
    calls = []
    def runner(source, target, ident, out_dir):
        calls.append(source)
        out_dir.mkdir(parents=True)
        obs = observation(source, target, 'present')
        (out_dir / 'observation.json').write_text(json.dumps(obs))
        return obs
    ledger_path = tmp_path / 'marketing/earned_media/link-ledger.json'
    results = ll.check(ledger, ledger_path=ledger_path, out_root=ledger_path.parent, max_rows=2, runner=runner)
    assert len(calls) == 2 and all(r['outcome'] == 'present' for r in results)
    assert ledger['rows'][0]['stage'] == 'live' and ledger['rows'][0]['last_observation']['path'].startswith('link-checks/')
    assert ledger['rows'][2]['stage'] == 'promised'


def test_cli_init_import_report(tmp_path, monkeypatch, capsys):
    base = tmp_path / 'biz'
    cand = tmp_path / 'candidates.json'; cand.write_text(json.dumps(CANDIDATES))
    for argv in (['--base', str(base), 'init', '--property', 'italyforretirees.com'],
                 ['--base', str(base), 'import-candidates', str(cand), '--at', '2026-10-31'],
                 ['--base', str(base), 'report', '--markdown']):
        monkeypatch.setattr('sys.argv', ['x', *argv])
        assert ll.main() == 0
    doc = ll.load(base / ll.RELATIVE)
    assert len(doc['rows']) == 2 and (base / 'marketing/earned_media/link-ledger.md').is_file()
    monkeypatch.setattr('sys.argv', ['x', '--base', str(base), 'init', '--property', 'italyforretirees.com'])
    assert ll.main() == 1 and 'already exists' in capsys.readouterr().out
