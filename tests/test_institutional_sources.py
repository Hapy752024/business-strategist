"""Source families retain missing data, scope, credential and review boundaries."""
import hashlib
import json

import pytest

from scripts.market_research import institutional_sources as sources
from scripts.market_research.research_facts import check_fact


def args(provider, **kwargs):
    value = sources.parser().parse_args(['--provider', provider, '--out', '/unused'])
    for key, item in kwargs.items():
        setattr(value, key, item)
    return value


def test_csv_keeps_zero_missing_units_and_suppression():
    value = args('ecb', dataset='EXR', series='M.USD.EUR.SP00.A')
    rows, more = sources.normalize('ecb', {'text': 'TIME_PERIOD,OBS_VALUE,OBS_STATUS,UNIT\n2025-01,0,A,USD\n2025-02,,M,USD\n'}, value)
    assert not more and rows[0]['value'] == '0'
    assert rows[1]['value'] is None and rows[1]['flags'] == 'M'
    with pytest.raises(ValueError, match='SDMX CSV'):
        sources.normalize('ecb', {'text': '<html>Error</html>'}, value)


def test_world_bank_pagination_and_nulls_do_not_become_zero():
    body = [{'page': 1, 'pages': 2}, [{'indicator': {'id': 'SP.POP.TOTL'}, 'date': '2024', 'value': None}]]
    rows, more = sources.normalize('world_bank', body, args('world_bank'))
    assert more and rows[0]['value'] is None and rows[0]['unit'] == 'unknown'
    with pytest.raises(ValueError, match='World Bank'):
        sources.normalize('world_bank', [{'message': 'Invalid indicator'}], args('world_bank'))


def test_fred_missing_marker_and_vintage_preserved():
    rows, more = sources.normalize('fred', {'offset': 0, 'count': 2, 'observations': [
        {'date': '2025-01-01', 'value': '.', 'realtime_start': '2026-10-11'}]}, args('fred', series='FEDFUNDS'))
    assert more and rows[0]['value'] is None and rows[0]['realtime_start'] == '2026-10-11'


def test_company_registration_does_not_prove_commercial_success():
    rows, more = sources.normalize('companies_house', {'company_number': '00000006', 'company_name': 'Example',
        'company_status': 'active'}, args('companies_house', company_number='00000006'))
    assert not more and rows[0]['commercial_success'] == 'unresolved'


def test_credentials_stay_out_of_capture_and_facts(tmp_path, monkeypatch):
    secret = 'private-test-key-that-must-not-be-stored'
    monkeypatch.setenv('FRED_API_KEY', secret)
    monkeypatch.setattr(sources, 'get_secret', lambda *_: ('FRED_API_KEY', secret))
    def get(url, **kwargs):
        assert secret in url
        return {'ok': True, 'status_code': 200, 'final_url': url,
                'body': {'observations': [{'date': '2025-01-01', 'value': '0'}], 'count': 1}}
    monkeypatch.setattr(sources, 'http_get', get)
    capture = sources.collect('fred', args('fred', series='FEDFUNDS', population='US federal funds market'))
    raw = json.dumps(capture).encode()
    assert secret.encode() not in raw
    assert 'api_key=' not in capture['pages'][0]['url']
    (tmp_path / 'capture.json').write_bytes(raw)
    fact = list(sources.facts(capture, raw))[0]
    assert fact['content_sha256'] == hashlib.sha256(raw).hexdigest()
    check_fact(fact, tmp_path)
    with pytest.raises(ValueError, match='accepted review'):
        check_fact(fact, tmp_path, accepted=True)


def test_request_identifiers_prevent_arbitrary_hosts_and_paths():
    with pytest.raises(ValueError, match='dataflow'):
        sources.build_request('ecb', args('ecb', dataset='../other', series='M.US'))
    url, headers = sources.build_request('bis', args('bis', dataset='WS_CBPOL', series='M.CH', start='2025-01', end='2025-02'))
    assert '/api/v2/data/dataflow/BIS/WS_CBPOL/+/M.CH' in url
    assert 'c%5BTIME_PERIOD%5D=' in url and 'startPeriod=' not in url


def test_page_budget_retains_partial_coverage(monkeypatch):
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return {'ok': True, 'body': [{'page': 1, 'pages': 3}, [
            {'indicator': {'id': 'SP.POP.TOTL'}, 'date': '2024', 'value': 5}]]}
    monkeypatch.setattr(sources, 'http_get', get)
    capture = sources.collect('world_bank', args('world_bank', country='CHE', dataset='SP.POP.TOTL', max_pages=1))
    assert len(calls) == 1 and capture['complete_within_query'] is False


def test_overlapping_company_pages_deduplicate_without_hiding_conflicts(monkeypatch):
    monkeypatch.setattr(sources, 'get_secret', lambda *_: ('COMPANIES_HOUSE_API_KEY', 'fixture'))
    def get(url, **kwargs):
        second = 'start_index=1' in url
        return {'ok': True, 'body': {'items': [{'company_number': '00000006', 'title': 'Example', 'company_status': 'active'}],
                'start_index': int(second), 'total_results': 2}}
    monkeypatch.setattr(sources, 'http_get', get)
    capture = sources.collect('companies_house', args('companies_house', query='Example', limit=1, max_pages=2))
    assert len(capture['observations']) == 1 and capture['complete_within_query']


def test_no_empty_ecb_dates_are_sent():
    url, _ = sources.build_request('ecb', args('ecb', dataset='EXR', series='M.USD.EUR.SP00.A'))
    assert 'startPeriod=' not in url and 'endPeriod=' not in url
