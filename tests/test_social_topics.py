import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.marketing.keyword_map import merge_content_inputs
from scripts.marketing.social_topics import build_social_topics

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/social-topics.schema.json').read_text())
SHA = 'a' * 64
SEARCH_ROW = {'cluster_id': 'late-invoices', 'queries': [{'query_id': 'q0', 'query': 'late invoices', 'seed_origin': 'autocomplete'}],
              'journey_stage': 'solution_aware', 'intent': 'commercial', 'searcher_role': 'buyer', 'locale': 'DE:de',
              'questions': {'paa': [], 'related_searches': [], 'ai_overview_prompts': []},
              'serp_features': {'ads': 'observed', 'ai_overview': True, 'paa': True, 'video': False, 'forum': False, 'local_pack': False, 'shopping': False},
              'ranking_by_type': {}, 'content_gap': {'status': 'hypothesis', 'hypothesis': 'x', 'evidence_refs': ['cap/1.json'], 'needs_review': True},
              'recommended_page_type': 'comparison', 'conversion_bridge': 'quote', 'evidence_refs': ['cap/1.json'],
              'evidence_status': 'includes_observed_seed', 'volume': None, 'observed_seed_fraction': 1.0}


def rec(i, text, source='reddit', role='community_context', up=None, likes=None, comments=None, **extra):
    r = {'source': source, 'evidence_id': f'ev-{i}', 'retrieved_at': '2026-10-01T00:00:00Z', 'published_at': f'2026-09-{(i % 27) + 1:02d}T10:00:00Z',
         'evidence_type': 'community', 'text': text, 'strength': 'weak', 'sampling_frame': 'topic_led_voc', 'author_voice_status': 'unresolved',
         'source_role': role, 'engagement': {'upvotes': up, 'likes': likes, 'comments': comments, 'views': None}}
    r.update(extra)
    return r


def base():
    out = []
    for i in range(4):
        out.append(rec(i, f'Why are late invoices so hard to collect? Late invoices again, variant {i}.', up=10 + i, comments=3))
    for i in range(4, 7):
        out.append(rec(i, f'Invoice financing explained in short video number {i}. Is invoice financing worth it?', source='tiktok', role='creator_statement', likes=50000 + i))
    for i in range(7, 10):
        out.append(rec(i, f'Our factoring platform pays you in {i} hours', source='producthunt_comment', role='competitor_context', up=2, author_voice_status='supplier_context'))
    return out


def test_topics_group_records_and_keep_refs():
    out = build_social_topics(base(), None)
    assert out['rows']
    ids = {r for t in out['rows'] for r in t['record_ids']}
    assert {'ev-0', 'ev-1', 'ev-2'} <= ids
    t = next(t for t in out['rows'] if 'ev-0' in t['record_ids'])
    assert t['platform_counts'].get('reddit', 0) >= 3
    assert t['first_seen'] <= t['last_seen']
    assert any('?' in q for q in t['questions'])
    assert build_social_topics(base(), None) == out  # deterministic


def test_speaker_mix_separates_creators_and_suppliers():
    out = build_social_topics(base(), None)
    mixes = [t['speaker_mix'] for t in out['rows']]
    assert any(m.get('creators') for m in mixes)
    assert any(m.get('suppliers') for m in mixes)
    creators = next(t for t in out['rows'] if 'ev-5' in t['record_ids'])
    assert creators['speaker_mix'] == {'creators': 3} and 'customers' not in creators['speaker_mix']
    assert any(set(m) == {'suppliers'} for m in mixes)


def test_supplier_only_topic_labelled():
    out = build_social_topics(base(), None)
    t = next(t for t in out['rows'] if 'ev-8' in t['record_ids'])
    assert t['supplier_only'] is True and 'supplier' in t['label'].lower()
    assert all(not x['supplier_only'] for x in out['rows'] if 'ev-0' in x['record_ids'])


def test_engagement_not_compared_across_platforms():
    out = build_social_topics(base(), None)
    t = next(t for t in out['rows'] if t['platform_counts'].get('tiktok'))
    assert 'tiktok' in t['engagement']
    assert t['engagement']['tiktok']['likes']['top'] >= 50000
    flat = json.dumps(out['rows'])
    for banned in ('total_engagement', 'engagement_total', 'rank_by_engagement'):
        assert banned not in flat
    assert all(set(v) >= {'records_with_engagement'} for tt in out['rows'] for v in tt['engagement'].values())
    assert 'attention' in out['method']['note'].lower() and 'never compared' in out['method']['note'].lower()


def test_topic_without_cluster_is_candidate_not_gap():
    clusters = [{'cluster_id': 'late-invoice-fees', 'queries': [{'query': 'late invoices fees'}]}]
    out = build_social_topics(base(), clusters)
    matched = next(t for t in out['rows'] if 'ev-0' in t['record_ids'])
    assert matched['cluster_ids'] == ['late-invoice-fees']
    assert matched['search_check'] == 'matched_search_cluster'
    other = next(t for t in out['rows'] if 'ev-5' in t['record_ids'])
    assert other['cluster_ids'] == [] and other['search_check'] == 'candidate_to_check_in_search'
    assert 'gap' not in json.dumps([t['search_check'] for t in out['rows']])


def test_single_platform_flag():
    out = build_social_topics(base(), None)
    t = next(t for t in out['rows'] if 'ev-0' in t['record_ids'])
    assert t['single_platform'] is True


def test_phrases_capped_and_social_row_schema_and_merge(tmp_path):
    long_text = 'Late invoices ' + 'really annoying ' * 30
    recs = [rec(i, long_text + f' number {i}', up=i) for i in range(9)]
    rf = tmp_path / 'evidence.jsonl'
    rf.write_text('\n'.join(json.dumps(r) for r in recs) + '\n')
    cdir = tmp_path / 'out'
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/marketing/social_topics.py'), '--records', str(rf), '--out', str(cdir)], capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    doc = json.loads((cdir / 'social-topics.json').read_text())
    assert (cdir / 'social-topics.md').read_text().strip()
    assert not list(Draft202012Validator(SCHEMA).iter_errors(doc))
    for row in doc['rows']:
        assert len(row['phrases']) <= 5 and all(len(p['text']) <= 120 for p in row['phrases'])
        assert row['refs'][0]['sha256'] != SHA and row['refs'][0]['path']
    search = tmp_path / 'content-opportunities.json'
    search.write_text(json.dumps({'schema_version': 1, 'source': 'search_journey_serp_study', 'caveats': ['c'], 'rows': [SEARCH_ROW]}))
    result = merge_content_inputs(search, social_topics=cdir / 'social-topics.json', out=tmp_path / 'keyword-map.proposed.json')
    assert 'social_topics' in result['inputs_present']
    assert any('social_topics' in r['inputs'] for r in result['rows'])
