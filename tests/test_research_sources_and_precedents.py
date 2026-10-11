"""Meaningful extraction, applicability and reviewed-source regressions."""
import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault('EVIDENCE_SCOUT_INFRA_DIR', '/tmp/business-strategist-test-infra')
from scripts import capability_lookup, publication_claims, case_workspace
from scripts.market_research import research_sources as sources, research_facts
from scripts.evidence_scout.entity_landscape import commercial_precedent
from scripts.evidence_scout import discover_competitors as discover
from scripts.validate_apis.common import redact_sensitive, sanitize_headers


def test_statistics_rank_by_positive_capability_and_geography():
    catalog = capability_lookup.load_catalog()
    query = 'Swiss official statistics business counts household spending representative market sizing'
    ranked = sorted(catalog['capabilities'], key=lambda row: capability_lookup.score(row, query), reverse=True)
    assert ranked[0]['id'] in {'swiss_stats', 'opendata_swiss'}
    negative = {'id': 'irrelevant', 'family': 'customer', 'avoid_when': ['official statistics market sizing']}
    assert capability_lookup.score(negative, 'official statistics market sizing') <= 0


def test_sparse_jsonstat_preserves_zero_unknown_and_coordinates():
    body = {'class': 'dataset', 'id': ['geo', 'time'], 'size': [2, 2], 'label': 'Household counts',
            'dimension': {'geo': {'category': {'index': {'CH': 0, 'DE': 1}}},
                          'time': {'category': {'index': ['2024', '2025']}}},
            'value': {'0': 0, '3': 12}, 'status': {'1': 'confidential'}}
    rows = sources.jsonstat(body)
    assert rows[0]['value'] == '0'
    assert rows[1]['value'] is None and rows[1]['flags'] == 'confidential'
    assert rows[3]['dimensions'] == {'time': '2025', 'geo': 'DE'}


def test_census_suppression_and_bls_semantic_errors():
    args = SimpleNamespace(variables='NAME,COUNT', dataset='2024/acs/acs5', unit='people')
    rows, kind = sources.normalize('census', [['NAME', 'COUNT', 'state'], ['Area', '-666666666', '01']], args)
    assert kind == 'statistics' and rows[0]['value'] is None and rows[0]['flags'] == 'suppressed'
    with pytest.raises(ValueError, match='rejected'):
        sources.normalize('bls', {'status': 'REQUEST_SUCCEEDED', 'message': ['Invalid Series for Series FAKE']}, args)


def make_fact(tmp_path, provider='eurostat'):
    observation = {'metric': 'count', 'value': '12', 'period': '2025', 'unit': 'people', 'dimensions': {'geo': 'CH'},
                   'flags': None, 'page': 0, 'currency': None, 'scope': 'Residents'}
    capture = {'provider': provider, 'publisher': 'Official statistics', 'retrieved_at': '2026-10-11T00:00:00Z',
               'kind': 'statistics', 'scope': {'geography': 'CH', 'population': 'Residents', 'language': 'en'},
               'pages': [{'url': 'https://example.org/table'}], 'observations': [observation]}
    raw = json.dumps(capture).encode()
    (tmp_path / 'capture.json').write_bytes(raw)
    return sources.facts(capture, 'capture.json', hashlib.sha256(raw).hexdigest())[0]


def test_review_binds_observation_and_rejects_mutation(tmp_path):
    fact = make_fact(tmp_path)
    decision = {'evidence_id': fact['evidence_id'], 'fact_digest': research_facts.fact_digest(fact), 'status': 'accepted',
                'reviewer': 'reviewer', 'reviewed_at': '2026-10-11', 'rationale': 'Original table and population inspected.'}
    reviewed = research_facts.review([fact], [decision], tmp_path)[0]
    research_facts.check_fact(reviewed, tmp_path, accepted=True)
    changed = copy.deepcopy(reviewed)
    changed['observation']['unit'] = 'firms'
    with pytest.raises(ValueError, match='does not match'):
        research_facts.check_fact(changed, tmp_path, accepted=True)
    (tmp_path / 'capture.json').write_text('{}')
    with pytest.raises(ValueError, match='capture changed'):
        research_facts.check_fact(reviewed, tmp_path, accepted=True)


def test_fact_publication_requires_review_and_original_capture(tmp_path):
    root = tmp_path
    run = root / 'cases/a/market_research/statistics/run'; run.mkdir(parents=True)
    fact = make_fact(run)
    decision = {'evidence_id': fact['evidence_id'], 'fact_digest': research_facts.fact_digest(fact), 'status': 'accepted',
                'reviewer': 'reviewer', 'reviewed_at': '2026-10-11', 'rationale': 'Original table and definitions reviewed.'}
    fact = research_facts.review([fact], [decision], run)[0]
    path = run / 'reviewed-facts.jsonl'; path.write_text(json.dumps(fact) + '\n')
    bind = case_workspace.source_binding(root, str(path.relative_to(root)), locator=fact['evidence_id'], applicability='a population denominator')
    capture = case_workspace.source_binding(root, str((run / 'capture.json').relative_to(root)), locator='/observations/0', applicability='a original population table')
    ref = {'id': 'population', 'document': 'section.customer_market', 'fact_binding': bind,
           'source_kind': 'original', 'limitation': '', 'supporting_passage': fact['text'], 'claim_scope': 'finding'}
    text = {'section.customer_market': 'Observed population {{evidence_claim.population}}'}
    result = publication_claims.render(root, text, [ref], [bind, capture])
    assert 'https://example.org/table' in result['section.customer_market']
    with pytest.raises(ValueError, match='capture must also be bound'):
        publication_claims.render(root, text, [ref], [bind])


def test_japanese_queries_reach_provider_with_their_locale(monkeypatch):
    plan = discover.query_plan('service', 'buyers', '', analog_locales=['JP:ja=生活支援'])
    queries = [{**row, 'provider': 'brave_search'} for row in plan['similar_company']]
    urls = []
    monkeypatch.setattr(discover, 'get_secret', lambda *_: ('KEY', 'fake'))
    monkeypatch.setattr(discover, 'http_get', lambda url, **_: urls.append(url) or {'ok': True, 'body': {'web': {'results': []}}})
    discover.search_candidates(queries, 2, {}, 'CH', 'de', 'similar_company', 'brave_search')
    assert urls and all('country=JP' in url and 'search_lang=ja' in url for url in urls)
    assert any('撤退' in row['query'] for row in queries)


def test_funding_alone_cannot_upgrade_commercial_precedent():
    bound = [{'path': 'capture.json', 'digest': 'a' * 64, 'locator': '/round', 'applicability': 'funding'}]
    funded = [{'kind': 'funding', 'status': 'accepted', 'source_bindings': bound, 'scope': 'Foreign company', 'rationale': 'Funding announced.'}]
    assert commercial_precedent(funded, {})['evidence_level'] == 'unresolved'
    purchase = {'kind': 'purchase', 'status': 'accepted', 'source_bindings': bound, 'scope': 'Foreign customer cohort', 'rationale': 'Purchase independently observed.'}
    assert commercial_precedent([*funded, purchase], {'regulation': 'unresolved'})['evidence_level'] == 'purchase_observed'
    assert commercial_precedent([purchase], {})['local_demand_status'] == 'requires_target_market_evidence'


def test_provider_credentials_are_redacted_from_payload_and_urls():
    safe = redact_sensitive({'registrationkey': 'bls-secret', 'key': 'census-secret',
                             'error': 'Failure https://api.example/data?api_key=openalex-secret&year=2025'})
    assert 'secret' not in json.dumps(safe)
    assert sanitize_headers({'X-Api-Key': 'parsers-secret', 'Authorization': 'Bearer openalex-secret'}) == {'X-Api-Key': '***', 'Authorization': '***'}
