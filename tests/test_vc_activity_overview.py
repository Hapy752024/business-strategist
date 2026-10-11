"""Funding samples must not invent comparable totals or acceleration."""
from argparse import Namespace
import copy
from urllib.parse import parse_qs, urlsplit

import pytest

from scripts.market_research import scan_vc_topics as vc
from scripts.market_research.build_investor_activity import render


def signal(ident, amount, company='company', detected='2026-09-01', stage='Seed'):
    return {'id': 'signal-' + ident + detected, 'object': {'id': ident, 'type': 'round'},
            'subject': {'id': company, 'name': company, 'type': 'startup'}, 'amount': amount,
            'occurredAt': '2026-08-01', 'detectedAt': detected, 'label': stage}


def query(signals, *, complete=True):
    return {'complete': complete, 'pages': [{'type': 'round.recorded', 'signals': signals}]}


def test_live_pascal_case_records_and_cached_signals_are_normalized():
    row = {'Id': 's1', 'Object': {'Id': 'r1', 'Type': 'round'},
           'Subject': {'Id': 'c1', 'Type': 'startup'}, 'Amount': 10,
           'OccurredAt': '2026-09-01', 'DetectedAt': '2026-09-02'}
    assert vc._records({'signals': [row]}, 'signals')[0]['object']['id'] == 'r1'
    result = vc.summarize('AI', {'AI|current|round.recorded': query([row, row])})
    assert result['current_rounds'] == 1
    assert result['periods']['current']['disclosed_amount_sum_usd_sample'] == 10


def test_duplicates_collapse_and_unknown_disclosure_stays_unknown():
    rows = [signal('r1', None), signal('r1', 25, detected='2026-09-02'), signal('r2', None)]
    queries = {'AI|current|round.recorded': query(rows), 'AI|previous|round.recorded': query([]),
               'AI|current|investor.joined_round': {'complete': True, 'pages': []},
               'AI|previous|investor.joined_round': {'complete': True, 'pages': []}}
    result = vc.summarize('AI', queries)
    assert result['current_rounds'] == 2
    assert result['periods']['current']['disclosed_amount_sum_usd_sample'] == 25
    assert result['periods']['current']['amount_disclosure_count'] == 1
    assert result['round_count_change_fraction'] is None
    assert result['activity_hint'] == 'emerging_activity_from_zero_baseline'


def test_capped_or_missing_windows_suppress_growth_numbers():
    queries = {'AI|current|round.recorded': query([signal('r1', 10)], complete=False),
               'AI|previous|round.recorded': query([signal('r0', 1)])}
    result = vc.summarize('AI', queries)
    assert result['round_count_change_fraction'] is None and result['sample_capped']
    assert 'inconclusive' in result['activity_hint']


def test_bounded_pages_resume_and_do_not_recharge_completed_queries(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(vc, 'get_secret', lambda *_: ('PARSERSVC_API_KEY', 'fake'))
    def get(url, **_):
        if url == vc.USAGE_URL:
            return {'ok': True, 'body': {'remaining': 100}}
        if url.endswith('/pricing'):
            return {'ok': True, 'body': {'endpoints': [{'endpoint': 'GET v2/signals', 'base_credits': 0, 'credits_per_record': .25}]}}
        if '/categories/industry' in url:
            return {'ok': True, 'body': {'categories': [{'value': 'AI'}]}}
        params = parse_qs(urlsplit(url).query)
        calls.append(params)
        cursor = params.get('cursor', [None])[0]
        rows = [signal('r1', 10)] if not cursor else []
        return {'ok': True, 'headers': {'X-Credits-Charged': '1'},
                'body': {'signals': rows, 'hasMore': bool(rows), 'nextCursor': 'next' if rows else None}}
    monkeypatch.setattr(vc, 'http_get', get)
    checkpoint = tmp_path / 'state.json'
    args = Namespace(topic=['AI'], country='Japan', max_topics=1, window_days=365, signals_per_query=1,
                     max_credits=20, max_pages=2, as_of='2026-10-11', checkpoint=checkpoint, resume=None)
    first = vc.scan(args)
    assert len(calls) == 8 and first['topics'][0]['sample_capped'] is False
    args.resume = checkpoint
    vc.scan(args)
    assert len(calls) == 8
    args.country = 'Germany'
    with pytest.raises(ValueError, match='scope changed'):
        vc.scan(args)


def test_overview_marks_primary_verification_pending():
    result = vc.summarize('AI', {})
    scan = {'as_of_date_utc': '2026-10-11', 'collected_at': '2026-10-11', 'query_scope': {'country': 'Japan'},
            'topics': [result], 'evidence_limits': ['Capped counts are lower bounds.'], 'stop_reason': 'credit_budget'}
    text = render(scan, [])
    assert 'Primary verification is pending' in text
    assert 'Do not add these rows' in text and 'Lower bounds' in text


def test_startup_subject_is_not_reported_as_an_investor():
    row = signal('r1', 10, company='Customer company')
    assert vc.investor_identity(row) is None
    row['investor'] = {'id': 'f1', 'type': 'fund', 'name': 'Verified fund'}
    assert vc.investor_identity(row)['name'] == 'Verified fund'


def test_live_account_usage_pascal_case_balance():
    assert vc._remaining({'body': {'Remaining': 500, 'Balance': 0}}) == 500
    assert vc._records({'values': [{'Value': 'Service'}]}, 'values') == [{'Value': 'Service'}]
