import json

import pytest

from scripts.marketing import competitor_backlinks as cb


def item(domain, url_to='https://competitor-a.com/guide', **over):
    base = {'type': 'backlink', 'domain_from': domain, 'url_from': f'https://{domain}/post', 'url_to': url_to,
            'anchor': 'useful guide', 'dofollow': True, 'is_lost': False, 'page_from_language': 'en',
            'page_from_rank': 120, 'domain_from_rank': 300, 'first_seen': '2026-01-02 00:00:00 +00:00',
            'last_seen': '2026-10-01 00:00:00 +00:00', 'item_type': 'anchor', 'page_from_title': 'Moving to Italy: resources',
            'is_sponsored': None, 'is_ugc': None}
    return {**base, **over}


RESPONSES = {
    'italyforretirees.com': [item('already-linking.org', url_to='https://italyforretirees.com/')],
    'competitor-a.com': [item('expat-blog.com'), item('already-linking.org'), item('competitor-b.com'),
                         item('scraper.us', anchor=None, item_type='image', page_from_rank=0,
                              page_from_title='Find Backlinks, Owners & WHOIS - New & Old Domains'),
                         item('pbn.biz', anchor='High Quality Dofollow Backlink', page_from_rank=0,
                              page_from_title='Boost your Google rankings with Premium PBN & Link Building')],
    'competitor-b.com': [item('expat-blog.com', url_to='https://competitor-b.com/costs'), item('retire-news.com', domain_from_rank=500)],
}


def fake_post(calls):
    def post(url, payload, auth):
        calls.append(payload[0])
        return {'tasks': [{'status_code': 20000, 'cost': 0.024, 'result': [{'items': RESPONSES[payload[0]['target']]}]}]}
    return post


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setattr(cb, 'credentials', lambda: ('login', 'password'))


def test_candidates_exclude_known_links_and_rank_shared_domains_first(creds):
    calls = []
    doc = cb.prospect(['https://www.competitor-a.com/x', 'competitor-b.com'], 'www.italyforretirees.com', post=fake_post(calls))
    assert [c['target'] for c in calls] == ['italyforretirees.com', 'competitor-a.com', 'competitor-b.com']
    assert calls[1]['mode'] == 'one_per_domain' and ['dofollow', '=', True] in calls[1]['filters']
    assert ['page_from_language', '=', 'en'] in calls[1]['filters'] and calls[0]['filters'][-1] == ['is_lost', '=', False]
    domains = [r['source_domain'] for r in doc['candidates']]
    assert domains == ['expat-blog.com', 'retire-news.com', 'pbn.biz', 'scraper.us']
    shared = doc['candidates'][0]
    assert shared['competitor_count'] == 2 and {l['competitor'] for l in shared['links_to']} == {'competitor-a.com', 'competitor-b.com'}
    assert doc['excluded'] == {'already_linking': 1, 'own_or_competitor_domain': 1}
    assert doc['already_linking_domains'] == ['already-linking.org']
    assert all(r['qualification'] == 'candidate' and r['link_inclusion'] == 'unknown' for r in doc['candidates'])
    assert doc['returned_cost_usd'] == pytest.approx(0.072)


def test_scraper_rows_are_flagged_not_dropped(creds):
    doc = cb.prospect(['competitor-a.com'], 'italyforretirees.com', post=fake_post([]))
    scraper = next(r for r in doc['candidates'] if r['source_domain'] == 'scraper.us')
    assert set(scraper['flags']) >= {'scraper_or_whois_page', 'non_text_link:image', 'empty_anchor'}
    assert next(r for r in doc['candidates'] if r['source_domain'] == 'expat-blog.com')['flags'] == []
    assert next(r for r in doc['candidates'] if r['source_domain'] == 'pbn.biz')['flags'] == ['link_seller_page']


def test_cost_cap_refuses_before_any_call(creds):
    calls = []
    with pytest.raises(cb.CapExceeded):
        cb.prospect(['a.com', 'b.com', 'c.com'], 'own.com', max_cost_usd=0.05, post=fake_post(calls))
    assert calls == []


def test_missing_credentials(monkeypatch):
    monkeypatch.setattr(cb, 'credentials', lambda: (None, None))
    with pytest.raises(cb.MissingCredentials):
        cb.prospect(['a.com'], 'own.com', post=fake_post([]))


def test_task_failure_surfaces_provider_error(creds):
    def post(url, payload, auth):
        return {'tasks': [{'status_code': 40402, 'status_message': 'No data'}]}
    with pytest.raises(cb.ProviderError) as exc:
        cb.prospect(['a.com'], 'own.com', post=post)
    assert exc.value.status == 'task_failed'


def test_cli_writes_candidates_and_raw_with_provenance(creds, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cb, '_post', fake_post([]))
    out = tmp_path / 'run'
    monkeypatch.setattr('sys.argv', ['x', '--competitor', 'competitor-a.com', '--own', 'italyforretirees.com', '--out', str(out)])
    assert cb.main() == 0
    doc = json.loads((out / 'candidates.json').read_text())
    assert 'raw' not in doc and {p['path'] for p in doc['provenance']} == {'raw/italyforretirees.com.json', 'raw/competitor-a.com.json'}
    assert (out / 'raw' / 'competitor-a.com.json').is_file()
    lines = [json.loads(l) for l in capsys.readouterr().out.strip().splitlines()]
    assert lines[0]['estimated_cost_usd'] == cb.estimate_cost(1) and lines[-1]['status'] == 'ok'
