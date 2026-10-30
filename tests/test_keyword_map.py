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
    comp = _write(tmp_path / 'competitor-content.json', {'rows': [{'cluster_id': 'bu-vergleich', 'topic': 'BU Vergleich', 'questions': ['Wie vergleiche ich Tarife?'], 'entity': 'Acme Versicherung', 'entity_type': 'similar_company', 'coverage': 'covered_thin', 'refs': [{'path': 'comp/a.json', 'sha256': 'd' * 64}]}]})
    social = _write(tmp_path / 'social-topics.json', {'rows': [{'topic': 'BU Tipps für Berufseinsteiger', 'questions': ['Ab wann BU abschließen?'], 'platforms': ['reddit'], 'speaker_mix': {'customers': 0.8}, 'refs': [{'path': 'soc/b.json', 'sha256': 'e' * 64}]}]})
    return tmp_path, search, voc, comp, social


def test_merge_keeps_input_attribution(inputs):
    tmp, search, voc, comp, social = inputs
    result = merge_content_inputs(search, comp, voc, social)
    rows = {r['cluster_id']: r for r in result['rows']}
    r = rows['bu-vergleich']
    assert set(r['inputs']) == {'search', 'competitor_content', 'voc_questions'}
    assert r['inputs']['voc_questions']['refs'] and r['inputs']['competitor_content']['refs'][0]['path'] == 'comp/a.json'
    cov = r['inputs']['competitor_content']['coverage'][0]
    assert cov['entity_type'] == 'similar_company' and cov['entity'] == 'Acme Versicherung' and cov['coverage'] == 'covered_thin'
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


def test_null_cluster_id_accepted_and_bad_refs_rejected(inputs):
    tmp, search, voc, comp, social = inputs
    doc = json.loads(social.read_text()); doc['rows'][0]['cluster_id'] = None
    assert merge_content_inputs(search, social_topics=_write(tmp / 's2.json', doc))
    doc['rows'][0]['refs'] = ['bare-string']
    with pytest.raises(ValueError):
        merge_content_inputs(search, social_topics=_write(tmp / 's3.json', doc))
    doc = json.loads(comp.read_text()); doc['rows'][0]['entity_type'] = 'market_leader'
    with pytest.raises(ValueError):
        merge_content_inputs(search, competitor_content=_write(tmp / 'c2.json', doc))


def test_question_only_row_and_voc_refs_and_input_target_refused(inputs):
    tmp, search, voc, comp, social = inputs
    doc = json.loads(voc.read_text()); doc['questions'][0]['cluster_id'] = None
    result = merge_content_inputs(search, voc_questions=_write(tmp / 'v2.json', doc))
    row = next(r for r in result['rows'] if r['question_only'])
    assert row['primary_term'] is None and row['decision'] == 'create'
    ref = row['inputs']['voc_questions']['refs'][0]
    assert ref['review']['sha256'] == 'b' * 64 and ref['source']['path'] == 'sources/q1.json'
    with pytest.raises(ValueError):
        merge_content_inputs(search, out=search)
    assert not list(tmp.glob('*.tmp'))


def _comp(tmp, name, **row):
    base = {'cluster_id': 'bu-student', 'topic': 'x', 'questions': [], 'refs': [{'path': 'c.json', 'sha256': 'd' * 64}]}
    return _write(tmp / name, {'rows': [{**base, **row}]})


def test_analog_and_untyped_competitor_content_never_counts(inputs):
    tmp, search, *_ = inputs
    def row(path):
        return next(r for r in merge_content_inputs(search, competitor_content=path)['rows'] if r['cluster_id'] == 'bu-student')
    analog = row(_comp(tmp, 'a.json', entity='Acme', entity_type='similar_company'))
    assert analog['single_input'] is True and analog['input_count'] == 1 and analog['inspiration_count'] == 1
    assert analog['inputs']['competitor_content']['coverage'][0]['analog_only'] is True
    cap = row(_comp(tmp, 'b.json', entity='Acme', entity_type='capability_reference'))
    assert cap['single_input'] is True
    market = row(_comp(tmp, 'c.json', entity='Rival', entity_type='competitor'))
    assert market['single_input'] is False and market['input_count'] == 2 and market['inspiration_count'] == 0
    uncovered = row(_comp(tmp, 'f.json', entity='Rival', entity_type='competitor', coverage='uncovered'))
    assert uncovered['single_input'] is True and uncovered['input_count'] == 1
    low = row(_comp(tmp, 'g.json', entity='Rival', entity_type='competitor', coverage='covered_low_confidence', match_confidence='low'))
    assert low['single_input'] is True and low['input_count'] == 1
    assert low['inputs']['competitor_content']['coverage'][0]['match_confidence'] == 'low'
    low_thin = row(_comp(tmp, 'h.json', entity='Rival', entity_type='competitor', coverage='covered_thin', match_confidence='low'))
    assert low_thin['single_input'] is True
    high = row(_comp(tmp, 'i.json', entity='Rival', entity_type='competitor', coverage='covered_thin', match_confidence='high'))
    assert high['single_input'] is False and high['input_count'] == 2
    untyped = row(_comp(tmp, 'd.json'))
    assert untyped['single_input'] is True and untyped['inputs']['competitor_content']['coverage'][0]['untyped'] is True
    with pytest.raises(ValueError):
        merge_content_inputs(search, competitor_content=_comp(tmp, 'e.json', entity='Acme'))
