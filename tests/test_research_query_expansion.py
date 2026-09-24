"""Execution regressions using synthetic providers; no claim of live research quality."""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/evidence_scout'))
import collect as c
import discover_competitors as competitors
import discover_market_problems as market
import research_founder_playbooks as operators
import discover_communities as communities

PROVIDERS = ['hn', 'github', 'google_autocomplete', 'youtube', 'x', 'xai_x_search', 'scrapecreators']


def plan(provider, phrases=None):
    return {'schema_version': 1, 'revision': 'refined', 'previous_plan_digest': 'a' * 64, 'queries': [
        {'query_id': f'q{i}', 'candidate_id': f'c{i}', 'query': text, 'provider': provider,
         'locale': 'JP:ja', 'intent': 'open_discovery', 'source_family': 'test',
         'seed_origin': 'source_derived', 'seed_locators': ['https://example.test/post#original']}
        for i, text in enumerate(phrases or ['配送 遅延', '返品 手続き', '自分で 解決'])]}


def args(provider, **overrides):
    values = dict(topic='配送', customer_segment='buyers', hypothesis_id='T1', geo='JP', language='ja',
        limit=6, days=365, query_limit=3, results_per_query=2, query_plan_data=plan(provider),
        providers=provider, topic_keywords='', problem_keywords='', workaround_keywords='', segment_keywords='',
        sampling_frame='topic_led_voc', youtube_transcripts=False, youtube_transcript_max=2,
        xai_prompt='', xai_model='fixture', x_handles='', x_from_date='', x_to_date='',
        social_per_endpoint=2, fb_max_posts=3, fb_groups='', fb_pages='', fb_entity_pages='',
        ig_handles='', ig_hashtags='', social_comments=False, comments_max=2,
        community_capture_authorization='', community_verified_sources='', community_review_receipt='')
    values.update(overrides)
    return argparse.Namespace(**values)


def stub(monkeypatch, provider, calls, *, duplicates=False, failure=None, empty=False):
    monkeypatch.setattr(c, 'get_secret', lambda *a: (a[0], 'fixture'))
    monkeypatch.setattr(c, 'assess_relevance', lambda *a: ('relevant', 'fixture', 1))
    def request(url, **kw):
        params = kw.get('data') or {key: value[0] for key, value in parse_qs(urlsplit(url).query).items()}
        if 'credit-balance' in url:
            return {'ok': True, 'status_code': 200, 'body': {'creditCount': 100}}
        if 'commentThreads' in url:
            return {'ok': True, 'status_code': 200, 'body': {'items': []}}
        query = params.get('query') or params.get('q') or params['input'][0]['content']
        calls.append((url, query, params))
        if failure:
            return failure
        stem = 'same' if duplicates else str(len(calls))
        items = [] if empty else [{'id': f'{stem}-{i}', 'objectID': f'{stem}-{i}', 'title': '配送の経験',
            'text': '配送の経験', 'body': '配送の経験', 'url': f'https://forum.test/{stem}/{i}',
            'html_url': f'https://github.com/test/repo/issues/{stem}-{i}'} for i in range(5)]
        if provider == 'hn': body = {'hits': items}
        elif provider == 'github': body = {'items': items}
        elif provider == 'google_autocomplete': body = [query, [] if empty else [f'配送 {stem} {i}' for i in range(5)]]
        elif provider == 'youtube': body = {'items': [dict(id={'videoId': item['id']}, snippet={'title': item['title']}) for item in items]}
        elif provider == 'x': body = {'data': items}
        elif provider == 'xai_x_search': body = {} if empty else {'id': stem, 'output_text': 'Cited discovery', 'citations': [f'https://x.com/test/status/{stem}']}
        else: body = {'items': items}
        return {'ok': True, 'status_code': 200, 'body': body}
    monkeypatch.setattr(c, 'http_get', request)
    monkeypatch.setattr(c, 'http_post', request)


@pytest.mark.parametrize('provider', PROVIDERS)
def test_every_exact_seed_executes_despite_full_first_result(provider, tmp_path, monkeypatch):
    calls = []; stub(monkeypatch, provider, calls)
    records, summary = getattr(c, 'collect_' + provider)(args(provider), ['unplanned English'], tmp_path)
    for text in ['配送 遅延', '返品 手続き', '自分で 解決']:
        assert any(text in call[1] for call in calls)
    assert all('unplanned English' not in call[1] for call in calls)
    if provider == 'scrapecreators' and args(provider).results_per_query < 3:
        assert summary['status'] == 'partial'
        assert summary['query_ledger'][0]['platform_allocation'] and sum(summary['query_ledger'][0]['platform_allocation'].values()) == args(provider).results_per_query
        assert any(value == 'excluded_by_allocation' for value in summary['endpoint_statuses'].values())
    else:
        assert summary['status'] == 'ok'
    assert all(row['attempted'] and row['record_ids'] for row in summary['query_ledger'])
    assert len(records) <= 6
    assert {m['candidate_id'] for r in records for m in r['discovery_memberships'] if 'candidate_id' in m} == {'c0', 'c1', 'c2'}
    assert not c.accepted_records(records)[1]


@pytest.mark.parametrize('provider', PROVIDERS)
def test_duplicates_keep_all_query_memberships_and_skipped_queries(provider, tmp_path, monkeypatch):
    calls = []; stub(monkeypatch, provider, calls, duplicates=True)
    records, summary = getattr(c, 'collect_' + provider)(args(provider, query_limit=2), [], tmp_path)
    assert records
    assert summary['query_ledger'][2]['status'] == 'not_attempted:query_limit'
    assert any({m.get('candidate_id') for m in row['discovery_memberships']} >= {'c0', 'c1'} for row in records)


@pytest.mark.parametrize('provider', PROVIDERS)
@pytest.mark.parametrize('status,response', [
    ('permission_denied', {'ok': False, 'status_code': 403}),
    ('insufficient_credits', {'ok': False, 'status_code': 402, 'error': 'insufficient_credits'}),
    ('request_budget_exhausted', {'ok': False, 'error_type': 'request_budget_exhausted'}),
])
def test_search_failures_remain_visible(provider, status, response, tmp_path, monkeypatch):
    calls = []; stub(monkeypatch, provider, calls, failure=response)
    records, summary = getattr(c, 'collect_' + provider)(args(provider), [], tmp_path)
    assert not records
    assert summary['status'] == status
    assert all(row['returned_count'] is None for row in summary['query_ledger'])
    if status == 'request_budget_exhausted':
        assert not any(row['attempted'] for row in summary['query_ledger'])


@pytest.mark.parametrize('provider', PROVIDERS)
def test_one_generated_query_and_successful_empty_results(provider, tmp_path, monkeypatch):
    calls = []; stub(monkeypatch, provider, calls, empty=True)
    records, summary = getattr(c, 'collect_' + provider)(args(provider, query_plan_data={}), ['短い検索'], tmp_path)
    assert not records and summary['status'] == 'ok'
    assert all('短い検索' in call[1] for call in calls)


@pytest.mark.parametrize('provider', ['youtube', 'x', 'xai_x_search', 'scrapecreators'])
def test_missing_credentials_retain_schedule(provider, tmp_path, monkeypatch):
    monkeypatch.setattr(c, 'get_secret', lambda *a: (None, None))
    records, summary = getattr(c, 'collect_' + provider)(args(provider), [], tmp_path)
    assert not records and summary['status'] == 'missing_credentials'
    assert all(row['status'] == 'not_attempted:missing_credentials' for row in summary['query_ledger'])


def test_market_wrapper_forwards_all_calibration_controls(tmp_path):
    a = args('hn', query_plan='/tmp/refinement.json', max_http_requests=7, query_preview=True)
    command = market.collector_command(a, tmp_path)
    for flag, value in [('--query-plan', '/tmp/refinement.json'), ('--results-per-query', '2'), ('--query-limit', '3'), ('--max-http-requests', '7')]:
        assert command[command.index(flag)+1] == value
    assert '--query-preview' in command


def test_youtube_transcript_survives_separate_raw_capture_and_result_slice(tmp_path, monkeypatch):
    monkeypatch.setattr(c, 'get_secret', lambda *a: ('YOUTUBE_API_KEY', 'fixture'))
    monkeypatch.setattr(c, 'fetch_youtube_transcript', lambda *a: ('ok', 'exact full transcript text'))
    def request(url, **kwargs):
        if 'commentThreads' in url:
            return {'ok': True, 'status_code': 200, 'body': {'items': []}}
        return {'ok': True, 'status_code': 200, 'body': {'items': [
            {'id': {'videoId': 'video-1'}, 'snippet': {'title': 'A title', 'description': 'Description', 'channelTitle': 'Creator'}}]}}
    monkeypatch.setattr(c, 'http_get', request)
    records, summary = c._collect_youtube_query(args('youtube', youtube_transcripts=True, youtube_transcript_max=1), ['seed'], tmp_path)
    capture = json.loads((tmp_path / 'raw/youtube-transcripts/video-1.json').read_text())
    def fake_query(local_args, queries, run_dir):
        c.write_json(run_dir / 'raw/youtube.json', {})
        regular = [c.normalize_record(source='youtube', source_url=f'https://youtu.be/{i}', query='seed',
            customer_segment='buyers', hypothesis='T1', text=f'video {i}', raw_id=str(i)) for i in range(3)]
        transcript = c.normalize_record(source='youtube_transcript', source_url='https://youtu.be/t', query='seed',
            customer_segment='buyers', hypothesis='T1', text='transcript', raw_id='t')
        return regular + [transcript], {'status': 'ok', 'transcripts': {'attempted': 1, 'fetched': 1, 'statuses': {'ok': 1}}}
    monkeypatch.setattr(c, '_collect_youtube_query', fake_query)
    transcript_records, scheduled = c.collect_scheduled_provider(
        args('youtube', youtube_transcripts=True, youtube_transcript_max=1, results_per_query=2, query_limit=1), ['seed'], tmp_path, 'youtube'
    )
    assert capture['text'] == 'exact full transcript text'
    assert len(capture['text_sha256']) == 64
    assert any(row['source'] == 'youtube_transcript' for row in transcript_records)
    assert len(transcript_records) == 3
    assert scheduled['transcripts']['fetched'] == 1


def test_scrapecreators_three_record_allowance_covers_each_available_platform(tmp_path, monkeypatch):
    calls = []; stub(monkeypatch, 'scrapecreators', calls)
    records, summary = c.collect_scrapecreators(args('scrapecreators', results_per_query=3), [], tmp_path)
    platform_sources = {row['source'] for row in records if row['source'] in {'tiktok', 'instagram', 'threads'}}
    assert platform_sources == {'tiktok', 'instagram', 'threads'}
    assert summary['status'] == 'ok'
    assert all(sum(row['platform_allocation'].values()) == 3 for row in summary['query_ledger'] if row['scheduled'])


def test_resume_settings_bind_to_identical_plan_and_capture_options():
    original = args('hn')
    digest = c.checkpoint_settings(original, ['same query'])
    resumed = args('hn', resume=True, out_dir='/tmp/run')
    assert c.checkpoint_settings(resumed, ['same query']) == digest
    changed = args('hn', resume=True, out_dir='/tmp/run', results_per_query=4)
    assert c.checkpoint_settings(changed, ['same query']) != digest


def test_partial_provider_retry_merges_prior_capture_and_query_memberships():
    prior = [{"evidence_id": "ev-1", "retrieval_backend": "hn", "text": "captured",
              "discovery_memberships": [{"query_id": "q1"}]}]
    retried = [{"evidence_id": "ev-1", "retrieval_backend": "hn", "text": "captured",
                "discovery_memberships": [{"query_id": "q2"}]},
               {"evidence_id": "ev-2", "retrieval_backend": "hn", "text": "new"}]
    merged = c.merge_provider_records(prior, retried)
    assert {row["evidence_id"] for row in merged} == {"ev-1", "ev-2"}
    first = next(row for row in merged if row["evidence_id"] == "ev-1")
    assert first["discovery_memberships"] == [{"query_id": "q1"}, {"query_id": "q2"}]
    assert c.merge_provider_records(merged, []) == merged


@pytest.mark.parametrize('language,seed,expected', [('de', 'Nachhilfe', 'erste Kunden'), ('fr', 'cours particuliers', 'premiers clients'), ('ja', '家庭教師', '最初の顧客')])
def test_operator_plan_uses_local_situations(language, seed, expected):
    a = args('hn', language=language, geo='DE', topic_keywords=seed, archetype='English business label',
             operator_keywords='最初の顧客,集客の失敗' if language == 'ja' else '')
    p = operators.founder_query_plan(a)
    assert any(expected in row['query'] for row in p['queries'])
    assert all(seed in row['query'] and 'English business label' not in row['query'] for row in p['queries'])
    schema = json.loads((c.ROOT / 'schemas/pain-query-plan.schema.json').read_text())
    assert not list(Draft202012Validator(schema).iter_errors(p))


def test_operator_unsupported_language_requires_local_vocabulary():
    with pytest.raises(ValueError, match='operator-keywords'):
        operators.founder_query_plan(args('hn', archetype='agency', operator_keywords='', topic_keywords='家庭教師'))


def competitor_args(**updates):
    base = dict(query_plan='', topic='business brief', topic_keywords='家庭教師', customer_segment='families',
        segment_keywords='家族', known_competitors='', analog_market=['大阪'], reference_capability=['予約'],
        language='ja', geo='JP', query_limit=12, results_per_query=2)
    base.update(updates)
    return argparse.Namespace(**base)


def test_competitor_plan_preserves_input_and_does_not_inject_english():
    snapshot = competitors.execution_plan(competitor_args())
    assert snapshot['warnings']
    queries = snapshot['query_sets']['competitive_market']
    assert all(row['query'] == '家庭教師 家族' for row in queries)
    assert all('scheduled' not in row for row in snapshot['input_plan']['queries'])


@pytest.mark.parametrize('provider', ['firecrawl', 'brave_search'])
def test_competitor_later_queries_execute_after_full_shortlist(provider, monkeypatch):
    calls = []
    monkeypatch.setattr(competitors, 'get_secret', lambda *a: (a[0], 'fixture'))
    def response(url, **kw):
        params = kw.get('data') or {k: v[0] for k,v in parse_qs(urlsplit(url).query).items()}
        calls.append(params)
        items = [{'url': 'https://supplier.test/', 'title': 'Local service', 'description': 'We provide local service'}]
        return {'ok': True, 'status_code': 200, 'body': {'data': items} if provider == 'firecrawl' else {'web': {'results': items}}}
    monkeypatch.setattr(competitors, 'http_get', response); monkeypatch.setattr(competitors, 'http_post', response)
    queries = [{'query': f'Anbieter {i}', 'query_id': f'q{i}', 'candidate_id': f'c{i}', 'scope_value': 'Familien', 'per_query_result_limit': 2} for i in range(7)]
    found, summary = competitors.search_candidates(queries, 1, {}, 'DE', 'de', 'competitive_market', provider)
    assert len(calls) == 7 and len(found) == 1
    assert len(found['supplier.test']['sources']) == 7
    assert all(row['attempted'] for row in summary['query_ledger'])
    assert all(call['country'] == 'DE' for call in calls)


def test_competitor_exact_refinement_retains_lineage(tmp_path):
    data = plan('firecrawl', ['家庭教師 比較'])
    data['queries'][0].update(lane_scope='competitive_market', scope_value='家族')
    path = tmp_path / 'plan.json'; path.write_text(json.dumps(data))
    snapshot = competitors.execution_plan(competitor_args(query_plan=str(path)))
    assert snapshot['input_plan'] == data
    assert snapshot['query_sets']['competitive_market'][0]['seed_locators']
    data['queries'][0]['locale'] = 'DE:de'; path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='locale'):
        competitors.execution_plan(competitor_args(query_plan=str(path)))


def test_community_preview_needs_neither_signing_key_nor_workspace(monkeypatch, capsys):
    monkeypatch.delenv('COMMUNITY_DISCOVERY_PRIVATE_KEY_B64', raising=False)
    monkeypatch.setattr(communities, 'resolve_run_dir', lambda **kw: pytest.fail('Preview mutated workspace'))
    monkeypatch.setattr(sys, 'argv', ['discover_communities.py', '--topic', '移住', '--customer-segment', '家族',
        '--locale', 'JP:ja', '--locale-keywords', 'JP:ja=引越し', '--locale-source-terms', 'JP:ja=掲示板|グループ|ページ', '--query-preview'])
    assert communities.main() == 0
    snapshot = json.loads(capsys.readouterr().out)
    assert len(snapshot['query_plan']) == 3 and snapshot['query_plan_digest']


def test_community_source_refinement_requires_matching_seed_locator(tmp_path):
    a = argparse.Namespace(topic='paperwork', community_keywords='', locales=[{'locale_id': 'GB:en', 'country': 'GB', 'language': 'en'}],
        locale_keyword_map={'GB:en': ['estate paperwork']}, locale_source_term_map={}, query_review=str(tmp_path / 'review.json'))
    review = {'revision': 'r2', 'review_notes': 'Observed local phrase', 'previous_plan_digest': 'b'*64,
              'seeds': [{'locale': 'GB:en', 'seed': 'estate paperwork', 'seed_origin': 'source_derived'}]}
    Path(a.query_review).write_text(json.dumps(review))
    with pytest.raises(ValueError, match='seed_locators'):
        communities.reviewed_query_plan(a)
    review['seeds'][0]['seed_locators'] = ['https://example.test/thread#post-2']
    Path(a.query_review).write_text(json.dumps(review))
    rows, kept = communities.reviewed_query_plan(a)
    assert kept == review and all(row['seed_locators'] for row in rows)


def test_operator_preview_runs_real_collector_without_customer_segment(monkeypatch, capsys):
    monkeypatch.setattr(operators, 'create_topic_workspace', lambda *a: pytest.fail('Preview created project'))
    monkeypatch.setattr(sys, 'argv', ['research_founder_playbooks.py', '--topic', 'Tutoring', '--archetype', 'local service',
        '--topic-keywords', 'cours particuliers', '--geo', 'FR', '--language', 'fr', '--providers', 'hn', '--query-preview'])
    assert operators.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result['provider_schedules']['hn']) == 4
    assert all('cours particuliers' in row['query'] for row in result['provider_schedules']['hn'])


def test_known_competitor_lookup_does_not_inject_insurance_or_english(monkeypatch):
    calls = []
    monkeypatch.setattr(competitors, 'get_secret', lambda *a: (a[0], 'fixture'))
    def get(url, **kw):
        calls.append(parse_qs(urlsplit(url).query)['q'][0])
        return {'ok': True, 'status_code': 200, 'body': {'web': {'results': []}}}
    monkeypatch.setattr(competitors, 'http_get', get)
    competitors.enrich_known_competitors({}, '教室A', {}, 'JP', 'ja', '家庭教師')
    assert calls == ['教室A', '教室A 家庭教師']


def test_youtube_enrichment_failure_is_partial_not_clean_success(tmp_path, monkeypatch):
    calls = []; stub(monkeypatch, 'youtube', calls)
    search = c.http_get
    def get(url, **kw):
        if 'commentThreads' in url:
            return {'ok': False, 'status_code': 403}
        return search(url, **kw)
    monkeypatch.setattr(c, 'http_get', get)
    records, summary = c.collect_youtube(args('youtube'), [], tmp_path)
    assert records and summary['status'] == 'partial'
    assert all(row['status'] == 'partial' for row in summary['query_ledger'])


def test_competitor_preview_precedes_workspace_and_credentials(monkeypatch, capsys):
    monkeypatch.setattr(competitors, 'resolve_run_dir', lambda **kw: pytest.fail('Preview created project'))
    monkeypatch.setattr(competitors, 'get_secret', lambda *a: pytest.fail('Preview accessed credentials'))
    monkeypatch.setattr(sys, 'argv', ['discover_competitors.py', '--topic', 'Local tutoring', '--topic-keywords', 'Nachhilfe',
        '--geo', 'DE', '--language', 'de', '--query-preview'])
    assert competitors.main() == 0
    snapshot = json.loads(capsys.readouterr().out)
    schema = json.loads((c.ROOT / 'schemas/pain-query-plan.schema.json').read_text())
    assert not list(Draft202012Validator(schema).iter_errors(snapshot['input_plan']))
