import hashlib
import json
from pathlib import Path

import pytest

from scripts.marketing import search_feedback as sf

META = {'property': 'sc-domain:example.com', 'period_start': '2026-11-01', 'period_end': '2026-11-28',
        'timezone': 'UTC', 'exported_at': '2026-11-30', 'report_scope': 'Synthetic web search, all countries'}

MAP = {'schema_version': 1, 'rows': [
    {'id': 'r1', 'locale': 'de', 'primary_term': 'bu versicherung vergleich', 'secondary_terms': ['berufsunfähigkeit rechner'],
     'target_url': 'https://example.com/bu-vergleich', 'decision': 'create'},
    {'id': 'r2', 'locale': 'de', 'primary_term': 'dienstunfähigkeitsversicherung', 'secondary_terms': [],
     'target_url': 'https://example.com/du', 'decision': 'create'},
    {'id': 'r3', 'locale': 'de', 'primary_term': 'bu für studenten', 'secondary_terms': [],
     'target_url': 'https://example.com/studenten', 'decision': 'create'}]}

CSV = """Top queries,Clicks,Impressions,CTR,Position
BU Versicherung Vergleich!,12,400,3%,4.2
beste bu versicherung vergleich 2026,0,150,0%,9.8
berufsunfähigkeit rechner,5,60,8.3%,6.1
bu versicherung kosten selbstständige,0,220,0%,12.0
steuerberater finden,3,90,3.3%,8.0
bu für studenten,,,,
"""


@pytest.fixture
def files(tmp_path):
    m = tmp_path / 'keyword-map.json'
    m.write_text(json.dumps(MAP))
    g = tmp_path / 'gsc-queries.csv'
    g.write_text(CSV)
    return m, g


def test_search_feedback_flags_unplanned_queries(files):
    result = sf.compare(*files, metadata=META)
    unplanned = {q['query']: q for q in result['unplanned_with_impressions']['queries']}
    assert set(unplanned) == {'bu versicherung kosten selbstständige', 'steuerberater finden'}
    assert unplanned['bu versicherung kosten selbstständige']['impressions'] == 220
    assert result['unplanned_with_impressions']['count'] == 2
    assert result['window'] == {'period_start': '2026-11-01', 'period_end': '2026-11-28', 'timezone': 'UTC'}
    assert result['status'] == 'proposal' and result['reviewed'] is False


def test_planned_without_impressions_and_unknown_not_zero(files):
    result = sf.compare(*files, metadata=META)
    none = {c['id'] for c in result['planned_no_impressions']['clusters']}
    assert none == {'r2'}                          # no rows at all for the export window
    unknown = {c['id'] for c in result['unknown']['clusters']}
    assert unknown == {'r3'}                       # row present but values blank: unknown, never zero
    assert 'r3' not in none
    assert 'anonymi' in result['planned_no_impressions']['limitation'].lower()


def test_impressions_no_clicks_is_title_snippet_hypothesis(files):
    result = sf.compare(*files, metadata=META)
    got = result['impressions_no_clicks']
    assert [q['query'] for q in got['queries']] == ['beste bu versicherung vergleich 2026']
    assert got['queries'][0]['cluster_id'] == 'r1' and got['count'] == 1
    assert 'hypothesis' in got['interpretation'].lower()


def test_matching_rule_exact_beats_contained(files):
    result = sf.compare(*files, metadata=META)
    by_query = {m['query']: m for m in result['matched']}
    assert by_query['BU Versicherung Vergleich!']['match'] == 'exact'
    assert by_query['beste bu versicherung vergleich 2026']['match'] == 'contains'
    assert by_query['berufsunfähigkeit rechner']['cluster_id'] == 'r1'


def test_proposals_only_and_reviewed_map_not_modified(files, tmp_path):
    m, g = files
    before = hashlib.sha256(m.read_bytes()).hexdigest()
    result = sf.compare(m, g, metadata=META)
    assert hashlib.sha256(m.read_bytes()).hexdigest() == before
    kinds = {p['signal']: p['suggested_decision'] for p in result['decision_proposals']}
    assert kinds['impressions_no_clicks'] == 'improve' and kinds['unplanned_with_impressions'] == 'create'
    assert all(p['reviewed'] is False for p in result['decision_proposals'])
    with pytest.raises(ValueError):
        sf.write_proposal(result, m)                # must refuse the reviewed map name/path
    out = sf.write_proposal(result, tmp_path / 'keyword-map.search-feedback.proposed.json')
    assert json.loads(out.read_text())['status'] == 'proposal'
    assert hashlib.sha256(m.read_bytes()).hexdigest() == before


def test_accepts_imported_json_and_requires_metadata_for_csv(files, tmp_path):
    m, g = files
    from scripts.marketing.import_presets import import_export
    doc = import_export(g, 'gsc-queries-v1', META)
    j = tmp_path / 'imported.json'
    j.write_text(json.dumps(doc))
    assert sf.compare(m, j)['unplanned_with_impressions']['count'] == 2
    with pytest.raises(ValueError):
        sf.compare(m, g)


def test_query_preset_keeps_question_marks(tmp_path):
    from scripts.marketing.import_presets import import_export
    g = tmp_path / 'q.csv'
    g.write_text('Top queries,Clicks,Impressions,CTR,Position\nwas kostet eine bu? preis,1,10,10%,3\n')
    doc = import_export(g, 'gsc-queries-v1', META)
    assert doc['observations'][0]['dimension'] == 'was kostet eine bu? preis'
