import json
from copy import deepcopy
from pathlib import Path

from scripts.marketing.keyword_map import validate,validate_resource

FIXTURE=Path(__file__).resolve().parents[1]/'fixtures/marketing/earned-media'


def test_existing_page_reuse_and_evidence_binding(tmp_path):
    doc=json.loads((FIXTURE/'keyword-map.json').read_text())
    assert not validate(doc,FIXTURE)
    doc['rows'][0]['decision']='create'
    assert any('existing page' in e for e in validate(doc,FIXTURE))
    doc['rows'][0]['decision']='improve'
    assert validate(doc,tmp_path)


def test_volume_conflicting_assignment_and_locale():
    doc=json.loads((FIXTURE/'keyword-map.json').read_text())
    second={**deepcopy(doc['rows'][0]),'id':'other','target_url':'https://workshop.example/other'}
    doc['rows'].append(second)
    assert any('conflicting primary' in e for e in validate(doc,FIXTURE))
    second['locale']='DE:de'
    assert not validate(doc,FIXTURE)
    second['volume']=100
    assert any('provider and date' in e for e in validate(doc,FIXTURE))


def test_public_resource_requires_real_source_binding():
    binding=json.loads((FIXTURE/'keyword-map.json').read_text())['rows'][0]['evidence_refs'][0]
    resource={k:'Reviewed public fixture' for k in ['audience_job','utility','original_vs_compiled','limitations',
        'public_use_suitability','maintenance_trigger','maintenance_owner','distribution_rationale']}
    resource.update(source_bindings=[binding],destination_url='https://workshop.example/guide')
    assert not validate_resource(resource,FIXTURE)
    resource['source_bindings'][0]['sha256']='a'*64
    assert validate_resource(resource,FIXTURE)


# ---- merge_content_inputs ----
import pytest
from scripts.marketing.keyword_map import merge_content_inputs


def _search_row(cid, queries, paa=()):
    return {'cluster_id': cid, 'queries': [{'query_id': f'{cid}-{i}', 'query': q, 'seed_origin': 'autocomplete'} for i, q in enumerate(queries)],
            'journey_stage': 'solution_aware', 'intent': 'commercial', 'searcher_role': 'buyer', 'locale': 'DE:de',
            'questions': {'paa': list(paa), 'related_searches': [], 'ai_overview_prompts': []},
            'serp_features': {'ads': 'observed', 'ai_overview': True, 'paa': True, 'video': False, 'forum': False, 'local_pack': False, 'shopping': False},
            'ranking_by_type': {}, 'content_gap': {'status': 'hypothesis', 'hypothesis': 'no comparison table', 'evidence_refs': ['cap/1.json'], 'needs_review': True},
            'recommended_page_type': 'comparison', 'conversion_bridge': 'quote request', 'evidence_refs': ['cap/1.json'],
            'evidence_status': 'includes_observed_seed', 'volume': None, 'observed_seed_fraction': 1.0}


def _write(path, doc):
    path.write_text(json.dumps(doc)); return path


@pytest.fixture
def inputs(tmp_path):
    search = _write(tmp_path / 'content-opportunities.json', {'schema_version': 1, 'source': 'search_journey_serp_study', 'caveats': ['c'],
        'rows': [_search_row('bu-vergleich', ['bu versicherung vergleich'], ['Was kostet eine BU?']), _search_row('bu-student', ['bu für studenten'])]})
    voc = _write(tmp_path / 'customer-questions.json', {'schema_version': 1, 'questions': [
        {'id': 'q1', 'kind': 'customer', 'passage': 'Welche BU lohnt sich?', 'source_date': None, 'segment': 's', 'segment_relation': 'target',
         'buyer_context': None, 'cluster_id': 'bu-vergleich', 'buyer_stage': None, 'current_answer': None, 'linked_brief_ids': [], 'visibility': 'public',
         'source': {'path': 'sources/q1.json', 'sha256': 'a' * 64}, 'review': {'path': 'reviews/q1.json', 'sha256': 'b' * 64}},
        {'id': 'q2', 'kind': 'supplier', 'passage': 'Supplier claim', 'source_date': None, 'segment': 's', 'segment_relation': 'target',
         'buyer_context': None, 'cluster_id': 'bu-student', 'buyer_stage': None, 'current_answer': None, 'linked_brief_ids': [], 'visibility': 'public',
         'source': {'path': 'sources/q2.json', 'sha256': 'c' * 64}}]})
    comp = _write(tmp_path / 'competitor-content.json', {'rows': [{'cluster_id': 'bu-vergleich', 'topic': 'BU Vergleich', 'questions': ['Wie vergleiche ich Tarife?'], 'refs': ['comp/a.json']}]})
    social = _write(tmp_path / 'social-topics.json', {'rows': [{'topic': 'BU Tipps für Berufseinsteiger', 'questions': ['Ab wann BU abschließen?'], 'refs': ['soc/b.json']}]})
    return tmp_path, search, voc, comp, social


def test_merge_keeps_input_attribution(inputs):
    tmp, search, voc, comp, social = inputs
    result = merge_content_inputs(search, comp, voc, social)
    rows = {r['cluster_id']: r for r in result['rows']}
    r = rows['bu-vergleich']
    assert set(r['inputs']) == {'search', 'competitor_content', 'voc_questions'}
    assert r['inputs']['voc_questions']['refs'] and r['inputs']['competitor_content']['refs'] == ['comp/a.json']
    assert {q['text']: q['inputs'] for q in r['questions']}['Welche BU lohnt sich?'] == ['voc_questions']
    assert (tmp / 'keyword-map.proposed.json').exists() and result['status'] == 'proposal'
    assert all(row['inputs'] and all(v['refs'] for v in row['inputs'].values()) for row in result['rows'])


def test_single_input_cluster_flagged(inputs):
    _, search, voc, comp, social = inputs
    rows = {r['cluster_id']: r for r in merge_content_inputs(search, comp, voc, social)['rows']}
    assert rows['bu-student']['single_input'] is True  # supplier-kind question is not customer voice
    assert rows['bu-vergleich']['single_input'] is False
    social_only = [r for r in rows.values() if set(r['inputs']) == {'social_topics'}]
    assert social_only and social_only[0]['single_input'] is True


def test_absent_optional_inputs_tolerated(inputs):
    _, search, *_ = inputs
    result = merge_content_inputs(search)
    assert all(set(r['inputs']) == {'search'} and r['single_input'] for r in result['rows'])
    assert result['inputs_present'] == ['search']


def test_existing_pages_matched_first_and_reviewed_map_not_overwritten(inputs):
    tmp, search, voc, comp, social = inputs
    reviewed = tmp / 'keyword-map.json'
    doc = json.loads((FIXTURE / 'keyword-map.json').read_text())
    doc['rows'][0].update(primary_term='bu versicherung vergleich', locale='DE:de')
    _write(reviewed, doc)
    before = reviewed.read_bytes()
    result = merge_content_inputs(search, comp, voc, social, existing_map=reviewed)
    row = next(r for r in result['rows'] if r['cluster_id'] == 'bu-vergleich')
    assert row['decision'] == 'improve' and row['existing_url'] == doc['rows'][0]['existing_url'] and row['matched_row_id'] == doc['rows'][0]['id']
    assert next(r for r in result['rows'] if r['cluster_id'] == 'bu-student')['decision'] == 'create'
    assert reviewed.read_bytes() == before
    with pytest.raises(ValueError):
        merge_content_inputs(search, existing_map=reviewed, out=reviewed)
    with pytest.raises(ValueError):
        merge_content_inputs(search, out=tmp / 'keyword-map.json')
    assert reviewed.read_bytes() == before


def test_invalid_optional_input_rejected(inputs):
    tmp, search, *_ = inputs
    with pytest.raises(ValueError):
        merge_content_inputs(search, _write(tmp / 'bad.json', {'rows': [{'refs': ['x']}]}))
