import json

import pytest

from scripts.marketing import keyword_volume as kv
from scripts.marketing.keyword_map import validate

RESPONSE = {'status_code': 20000, 'cost': 0.075, 'tasks': [{'status_code': 20000, 'cost': 0.075, 'result': [
    {'keyword': 'berufsunfähigkeitsversicherung', 'search_volume': 60500, 'cpc': 12.3, 'competition': 'HIGH', 'competition_index': 71},
    {'keyword': 'bu versicherung vergleich', 'search_volume': 2400, 'cpc': 9.1, 'competition': 'MEDIUM', 'competition_index': 55},
    {'keyword': 'no data keyword', 'search_volume': None, 'cpc': None, 'competition': None, 'competition_index': None}]}]}


def fake_post(calls):
    def post(url, payload, auth):
        calls.append((url, payload))
        return RESPONSE
    return post


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setattr(kv, 'credentials', lambda: ('login', 'password'))


def test_fixture_response_maps_to_fields(creds):
    calls = []
    rows = kv.fetch_volumes(['Berufsunfähigkeitsversicherung', 'BU Versicherung Vergleich', 'no data keyword'], 2276, 'de', post=fake_post(calls))
    assert calls[0][0].endswith('/keywords_data/google_ads/search_volume/live')
    assert calls[0][1][0]['location_code'] == 2276 and calls[0][1][0]['language_code'] == 'de'
    first = rows[0]
    assert first['volume'] == 60500 and first['cpc'] == 12.3 and first['competition'] == 71
    assert first['source'] == 'dataforseo' and first['fetched_at']
    assert rows[2]['volume'] is None and rows[2]['cpc'] is None and rows[2]['competition'] is None


def test_missing_credentials(monkeypatch):
    monkeypatch.setattr(kv, 'credentials', lambda: (None, None))
    with pytest.raises(kv.MissingCredentials) as exc:
        kv.fetch_volumes(['x'], 2276, 'de', post=fake_post([]))
    assert exc.value.status == 'missing_credentials'


def test_cap_refuses_before_network(creds):
    calls = []
    with pytest.raises(kv.CapExceeded):
        kv.fetch_volumes([f'k{i}' for i in range(5)], 2276, 'de', max_keywords=3, post=fake_post(calls))
    assert calls == []


def test_batches_and_cost_estimate():
    assert kv.estimate_cost(1) == kv.estimate_cost(1000) and kv.estimate_cost(1001) == 2 * kv.estimate_cost(1)
    assert kv.estimate_cost(0) == 0


def test_apply_to_map_keeps_unknown_null_and_validates(creds):
    rows = kv.fetch_volumes(['Berufsunfähigkeitsversicherung', 'no data keyword'], 2276, 'de', post=fake_post([]))
    doc = {'schema_version': 1, 'rows': [
        {'id': 'a', 'locale': 'DE:de', 'primary_term': 'berufsunfähigkeitsversicherung', 'intent': 'i', 'page_purpose': 'p',
         'target_url': 'https://x.example/a', 'existing_url': None, 'decision': 'create',
         'evidence_refs': [{'path': 'a', 'sha256': 'a' * 64}], 'checked_at': '2026-10-30', 'missing_information': '',
         'original_contribution': 'o', 'internal_links': [], 'conversion_bridge': 'c', 'priority_rationale': 'r'},
        {'id': 'b', 'locale': 'DE:de', 'primary_term': 'unrelated', 'intent': 'i', 'page_purpose': 'p',
         'target_url': 'https://x.example/b', 'existing_url': None, 'decision': 'create',
         'evidence_refs': [{'path': 'a', 'sha256': 'a' * 64}], 'checked_at': '2026-10-30', 'missing_information': '',
         'original_contribution': 'o', 'internal_links': [], 'conversion_bridge': 'c', 'priority_rationale': 'r'}]}
    assert kv.apply_to_map(doc, rows) == 1
    assert doc['rows'][0]['volume'] == 60500 and doc['rows'][0]['source'] == 'dataforseo'
    assert 'volume' not in doc['rows'][1]
    errors = validate(doc)
    assert not [e for e in errors if 'volume' in e or 'Additional' in e]
    doc['rows'][0]['volume_provider'] = doc['rows'][0]['volume_checked_at'] = doc['rows'][0]['source'] = doc['rows'][0]['fetched_at'] = None
    assert any('provider and date' in e for e in validate(doc))


def test_refetch_no_data_keeps_known_values(creds):
    doc = {'rows': [{'primary_term': 'x', 'volume': 500, 'cpc': 2.0, 'competition': 40, 'fetched_at': 'old'}]}
    nodata = [{'keyword': 'x', 'volume': None, 'cpc': None, 'competition': None, 'fetched_at': '2026-10-30T00:00:00Z'}]
    kv.apply_to_map(doc, nodata)
    assert doc['rows'][0]['volume'] == 500 and doc['rows'][0]['fetched_at'] == 'old' and doc['rows'][0]['last_refetch'] == 'no_data'


def test_http_errors_become_status(creds):
    def boom(url, payload, auth):
        raise kv.ProviderError('rate_limited', 'DataForSEO HTTP 429')
    with pytest.raises(kv.ProviderError) as exc:
        kv.fetch_volumes(['x'], 2276, 'de', post=boom)
    assert exc.value.status == 'rate_limited'


def test_post_maps_http_error(monkeypatch):
    import urllib.error

    def raise_429(*a, **k):
        raise urllib.error.HTTPError('u', 429, 'x', {}, None)
    monkeypatch.setattr(kv.urllib.request, 'urlopen', raise_429)
    with pytest.raises(kv.ProviderError) as exc:
        kv._post('https://x', [], ('a', 'b'))
    assert exc.value.status == 'rate_limited'
