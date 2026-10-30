"""Live AI-answer collector: format-2 output, cost cap before network, failures kept, keys never written.

All HTTP is mocked with fixtures shaped after each provider's documented responses.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.monitoring import ai_answer_collect as c
from scripts.monitoring import ai_answer_probe as p

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'fixtures/monitoring/collector-responses'
SENTINELS = {'OPENAI_API_KEY': 'sk-SENTINEL-openai-123456', 'GEMINI_API_KEY': 'AIza-SENTINEL-gemini-123456',
             'GROK_API_KEY': 'xai-SENTINEL-grok-123456', 'DATAFORSEO_LOGIN': 'login-SENTINEL',
             'DATAFORSEO_PASSWORD': 'pw-SENTINEL-123456'}
REDIRECT = 'https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA'


def fixture(name):
    return json.loads((FIX / f'{name}.json').read_text())


def target(engine, model, locale='en-GB', repetitions=1):
    return {'engine': engine, 'model': model, 'search_config': c.expected_search_config(engine, locale),
            'surface': c.ENGINES[engine]['surface'], 'locale': locale, 'repetitions': repetitions}


def panel(*targets, prompts=None):
    return {'schema_version': 2, 'panel_version': 'v1', 'subject': {'name': 'Cedar', 'domains': ['cedar.example']},
            'prompts': prompts or [{'id': 'discover', 'version': 1, 'type': 'unbranded_discovery',
                                    'text': 'Which garden service can I use?', 'source': 'synthetic fixture, not demand evidence'}],
            'targets': list(targets)}


FULL = panel(target('openai', 'gpt-5.4-mini-2026-03-17'), target('gemini', 'gemini-3.8-flash'),
             target('xai', 'grok-4.7'), target('anthropic', 'claude-sonnet-5-5'),
             target('google-ai-mode', 'google-ai-mode'))

BY_HOST = {'api.openai.com': 'openai', 'generativelanguage.googleapis.com': 'gemini', 'api.x.ai': 'xai',
           'api.anthropic.com': 'anthropic', 'api.perplexity.ai': 'perplexity', 'api.dataforseo.com': 'dataforseo_ai_mode'}


class Transport:
    def __init__(self, overrides=None):
        self.calls, self.overrides = [], overrides or {}

    def __call__(self, url, headers, body):
        host = url.split('/')[2]
        self.calls.append((url, headers, body))
        if host in self.overrides:
            return self.overrides[host]
        return 200, {'x-request-id': 'req_header_' + BY_HOST[host]}, json.dumps(fixture(BY_HOST[host])).encode()


def secrets(missing=()):
    return lambda name: None if name in missing else SENTINELS.get(name)


def resolver(url):
    return 'https://cedar.example/from-redirect' if url == REDIRECT else None


def run(tmp_path, panel_raw=FULL, transport=None, **kw):
    transport = transport or Transport()
    out = tmp_path / 'collected'
    summary = c.collect(panel_raw, out, transport=transport, secret_lookup=kw.pop('secret_lookup', secrets()),
                        resolver=resolver, **kw)
    rows = [json.loads(line) for line in (out / 'recorded.jsonl').read_text().splitlines()]
    return summary, rows, transport, out


def test_ai_answer_collect_writes_format2(tmp_path):
    summary, rows, transport, out = run(tmp_path)
    assert len(rows) == 5 and len(transport.calls) == 4  # anthropic has no key: no call, but a failed row
    by_engine = {r['engine']: r for r in rows}
    for row in rows:
        assert row['collection_method'] == 'api'
        assert row['prompt_text'] == 'Which garden service can I use?'
        assert row['target_brand'] == 'Cedar' and row['target_url'] == 'https://cedar.example'
    for engine in ('openai', 'gemini', 'xai', 'google-ai-mode'):
        row = by_engine[engine]
        assert row['status'] == 'success' and row['provider_request_id'] and row['answer_text']
        assert row['annotation_method'].startswith('rule')
    assert by_engine['xai']['brand_mentioned'] is False and by_engine['xai']['recommended'] is False
    # Mentions need a reviewer for the recommendation flag; nothing is guessed.
    assert by_engine['openai']['brand_mentioned'] is True and by_engine['openai']['recommended'] is None
    assert summary['rows_needing_review'] == 3 and summary['importable'] is False
    decisions = {r['row_id']: {'recommended': False, 'reviewer': 'test reviewer', 'note': 'listed, not recommended'}
                 for r in rows if r.get('review_required')}
    reviewed = tmp_path / 'reviewed.jsonl'
    c.apply_review(out / 'recorded.jsonl', decisions, reviewed)
    reviewed_rows = [p.normalize_observation(json.loads(l)) for l in reviewed.read_text().splitlines()]
    assert all('reviewer' in r['annotation_method'] for r in reviewed_rows if r['row_id'] in decisions)
    (tmp_path / 'panel.json').write_text(json.dumps(FULL))
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/monitoring/ai_answer_probe.py'), '--panel',
                             str(tmp_path / 'panel.json'), '--recorded', str(reviewed), '--out', str(tmp_path / 'run')],
                            capture_output=True, text=True)
    assert result.returncode == 2, result.stdout  # partial: anthropic unknown, not absent
    loaded = p.load_run(tmp_path / 'run')
    assert loaded['summary']['status'] == 'partial'
    assert loaded['summary']['coverage']['successful_observations'] == 4
    assert [g['detail'] for g in loaded['summary']['coverage_gaps']] == ['missing_credentials: ANTHROPIC_API_KEY']


def test_cap_checked_before_any_network(tmp_path):
    prompts = [{'id': f'q{i}', 'version': 1, 'type': 'educational', 'text': f'Question {i}?', 'source': 'fixture'} for i in range(3)]
    big = panel(target('openai', 'gpt-5.4-mini-2026-03-17', repetitions=4), target('gemini', 'gemini-3.8-flash', repetitions=4),
                prompts=prompts)
    transport = Transport()
    with pytest.raises(c.CapExceeded):
        c.collect(big, tmp_path / 'out', transport=transport, secret_lookup=secrets(), max_calls=20)
    assert transport.calls == [] and not (tmp_path / 'out').exists()


def test_missing_credential_targets_do_not_count_toward_cap(tmp_path):
    transport = Transport()
    summary = c.collect(panel(target('anthropic', 'claude-sonnet-5-5', repetitions=3)), tmp_path / 'out',
                        transport=transport, secret_lookup=secrets(), max_calls=0)
    assert transport.calls == [] and summary['planned_calls'] == 0


def test_cli_prints_estimate_and_refuses_over_cap_without_network(tmp_path):
    (tmp_path / 'panel.json').write_text(json.dumps(FULL))
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(tmp_path), **SENTINELS, 'AI_ANSWER_COLLECT_OFFLINE': '1'}
    result = subprocess.run([sys.executable, '-m', 'scripts.monitoring.ai_answer_collect', 'collect', '--panel',
                             str(tmp_path / 'panel.json'), '--out', str(tmp_path / 'out'), '--max-calls', '2'],
                            capture_output=True, text=True, cwd=ROOT, env=env)
    lines = [json.loads(l) for l in result.stdout.splitlines() if l.strip()]
    assert result.returncode == 1
    assert lines[0]['planned_calls'] == 4 and lines[0]['estimated_cost_usd'] > 0
    assert lines[-1]['status'] == 'cap_exceeded' and not (tmp_path / 'out').exists()
    assert 'SENTINEL' not in result.stdout + result.stderr


def test_missing_credentials_rows_recorded_as_failed(tmp_path):
    _, rows, _, _ = run(tmp_path, secret_lookup=secrets(missing=('GEMINI_API_KEY',)))
    failed = [r for r in rows if r['engine'] in ('gemini', 'anthropic')]
    assert len(failed) == 2
    for row in failed:
        assert row['status'] == 'error' and row['error_detail'].startswith('missing_credentials')
        assert all(row[f] is None for f in p.TRACKED)
        p.normalize_observation(row)


@pytest.mark.parametrize('engine,name,citations,consulted,request_id,model', [
    ('openai', 'openai', ['https://cedar.example/services?utm_source=openai', 'https://birch.example/'],
     ['https://consulted.example/a'], 'resp_fixture_openai_1', 'gpt-5.4-mini-2026-03-17'),
    ('xai', 'xai', ['https://birch.example/'], ['https://birch.example/', 'https://cedar.example/blog'],
     'resp_fixture_xai_1', 'grok-4.7'),
    ('gemini', 'gemini', ['https://cedar.example/from-redirect', 'https://birch.example/about'], [],
     'gemini-fixture-response-1', 'gemini-3.8-flash'),
    ('anthropic', 'anthropic', ['https://cedar.example/'], ['https://cedar.example/'], 'msg_fixture_anthropic', 'claude-sonnet-5-5'),
    ('perplexity', 'perplexity', ['https://birch.example/'], ['https://birch.example/'], 'pplx-fixture-1', 'sonar'),
    ('google-ai-mode', 'dataforseo_ai_mode', ['https://cedar.example/'], [], '10311200-fixture-task', None),
])
def test_citations_parsed_per_engine(engine, name, citations, consulted, request_id, model):
    parsed = c.ENGINES[engine]['parse'](fixture(name), resolver)
    assert parsed['citation_urls'] == citations
    assert parsed['consulted_urls'] == consulted
    assert parsed['request_id'] == request_id
    assert parsed['response_model'] == model
    assert parsed['answer_text'].strip()


def test_gemini_unresolved_redirect_kept_and_flagged():
    parsed = c.ENGINES['gemini']['parse'](fixture('gemini'), lambda url: None)
    assert parsed['citation_urls'][0] == REDIRECT
    assert parsed['citation_details'][0]['resolved'] is False and parsed['citation_details'][0]['title'] == 'cedar.example'


def test_mention_and_citation_rules_are_conservative():
    subject = {'name': 'Cedar', 'domains': ['cedar.example']}
    assert c.annotate('Try cedar for gardens.', [], subject)['brand_mentioned'] is True
    assert c.annotate('Cedarwood furniture is nice.', [], subject)['brand_mentioned'] is False
    assert c.annotate('See cedar.example for details.', [], subject)['brand_mentioned'] is True
    sub = c.annotate('Nothing here.', ['https://www.cedar.example/x'], subject)
    assert sub['url_cited'] is False and sub['subdomain_citations'] == ['https://www.cedar.example/x']
    assert sub['recommended'] is False and sub['review_required'] == []
    cited = c.annotate('Nothing here.', ['https://cedar.example/x'], subject)
    assert cited['url_cited'] is True and cited['brand_mentioned'] is False


def test_search_config_mismatch_rejected_before_network(tmp_path):
    bad = panel({**target('openai', 'gpt-5.4-mini-2026-03-17'), 'search_config': 'search:on'})
    transport = Transport()
    with pytest.raises(ValueError, match='search_config'):
        c.collect(bad, tmp_path / 'out', transport=transport, secret_lookup=secrets())
    assert transport.calls == []


def test_no_ai_overview_is_unsupported_not_success(tmp_path):
    transport = Transport({'api.dataforseo.com': (200, {}, json.dumps(fixture('dataforseo_no_overview')).encode())})
    _, rows, _, _ = run(tmp_path, panel(target('google-ai-overview', 'google-ai-overview')), transport)
    assert rows[0]['status'] == 'unsupported' and 'no AI' in rows[0]['error_detail']
    p.normalize_observation(rows[0])


def test_credit_failure_recorded_with_reason(tmp_path):
    body = json.dumps({'error': {'type': 'insufficient_quota', 'message': 'You exceeded your current quota'}}).encode()
    transport = Transport({'api.openai.com': (429, {'x-request-id': 'req_q'}, body)})
    _, rows, _, _ = run(tmp_path, panel(target('openai', 'gpt-5.4-mini-2026-03-17')), transport)
    assert rows[0]['status'] == 'error' and rows[0]['error_detail'].startswith('credit_exhausted')
    assert rows[0]['provider_request_id'] == 'req_q'


def test_no_api_key_in_any_written_file(tmp_path):
    leaky = json.dumps({'error': {'message': 'Incorrect API key provided: ' + SENTINELS['OPENAI_API_KEY']}}).encode()
    transport = Transport({'api.openai.com': (401, {}, leaky)})
    run(tmp_path, transport=transport)
    assert any(SENTINELS['GEMINI_API_KEY'] in json.dumps(call[1]) for call in transport.calls)  # keys were used...
    for path in (tmp_path / 'collected').rglob('*'):
        if path.is_file():
            text = path.read_text()
            for value in SENTINELS.values():
                assert value not in text, f'{value} leaked into {path.name}'  # ...but never written
    assert all('key=' not in call[0] for call in transport.calls)  # no key in URLs


def test_existing_output_never_replaced(tmp_path):
    (tmp_path / 'collected').mkdir()
    with pytest.raises(ValueError, match='new'):
        run(tmp_path)


def test_repetitions_honoured(tmp_path):
    summary, rows, transport, _ = run(tmp_path, panel(target('xai', 'grok-4.7', repetitions=3)))
    assert [r['repetition'] for r in rows] == [1, 2, 3] and len(transport.calls) == 3
    assert summary['planned_calls'] == 3


def test_xai_unpositioned_annotations_are_sources_not_citations():
    parsed = c.ENGINES['xai']['parse'](fixture('xai'), None)
    assert parsed['citation_urls'] == ['https://birch.example/']
    assert 'https://cedar.example/blog' in parsed['consulted_urls']
    assert {d['via'] for d in parsed['citation_details']} <= {'annotation', 'inline_link'}


def test_inline_markdown_links_count_as_visible_citations():
    body = {'id': 'r', 'model': 'grok-4.7', 'output': [{'type': 'message', 'content': [{'type': 'output_text',
            'text': 'Compare at [cedar.example](https://cedar.example/compare).', 'annotations': []}]}]}
    parsed = c.ENGINES['xai']['parse'](body, None)
    assert parsed['citation_urls'] == ['https://cedar.example/compare']


def test_provider_reported_cost_recorded(tmp_path):
    summary, rows, _, _ = run(tmp_path, panel(target('xai', 'grok-4.7')))
    assert rows[0]['provider_cost_usd'] == 0.0037756
    assert summary['provider_reported_cost_usd'] == 0.0037756


def test_plan_quota_429_is_quota_exceeded_not_absence(tmp_path):
    body = json.dumps({'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details.',
                                 'status': 'RESOURCE_EXHAUSTED'}}).encode()
    transport = Transport({'generativelanguage.googleapis.com': (429, {}, body)})
    _, rows, _, _ = run(tmp_path, panel(target('gemini', 'gemini-3.8-flash')), transport)
    assert rows[0]['error_detail'].startswith('quota_exceeded') and rows[0]['brand_mentioned'] is None


# ---------- fix round 1 ----------

def responses_body(text, urls):
    return json.dumps({'id': 'resp_r', 'model': 'gpt-5.4-mini-2026-03-17', 'output': [{'type': 'message', 'content': [
        {'type': 'output_text', 'text': text, 'annotations': [
            {'type': 'url_citation', 'url': u, 'start_index': 0, 'end_index': 4, 'title': 't'} for u in urls]}]}]}).encode()


def test_redaction_never_rewrites_answers_or_citations(tmp_path):
    text = 'Compare task-management-tools and desk-booking-software; also see AIza-like words and xai-research-notes.'
    urls = ['https://desk-booking-software.example/x', 'https://cedar.example/task-management-tools']
    transport = Transport({'api.openai.com': (200, {}, responses_body(text, urls))})
    _, rows, _, out = run(tmp_path, panel(target('openai', 'gpt-5.4-mini-2026-03-17')), transport)
    assert rows[0]['answer_text'] == text and rows[0]['citation_urls'] == urls
    assert rows[0]['url_cited'] is True
    assert 'desk-booking-software' in (out / 'raw.jsonl').read_text()


def test_unconfigured_key_shapes_redacted_in_raw_and_errors(tmp_path):
    foreign = 'sk-proj-' + 'A1b2C3d4E5f6G7h8I9j0K1l2'
    body = json.dumps({'error': {'message': 'Incorrect API key provided: ' + foreign}}).encode()
    transport = Transport({'api.openai.com': (401, {}, body)})
    _, rows, _, out = run(tmp_path, panel(target('openai', 'gpt-5.4-mini-2026-03-17')), transport)
    for path in out.iterdir():
        assert foreign not in path.read_text(), path.name
    assert rows[0]['error_detail'].startswith('auth_failed')


def test_unmapped_dataforseo_locale_fails_before_network(tmp_path):
    bad = panel({'engine': 'google-ai-mode', 'model': 'google-ai-mode', 'search_config': 'x', 'surface': 'consumer',
                 'locale': 'ja-JP', 'repetitions': 1})
    transport = Transport()
    with pytest.raises(ValueError, match='location_code'):
        c.collect(bad, tmp_path / 'out', transport=transport, secret_lookup=secrets())
    assert transport.calls == [] and not (tmp_path / 'out').exists()


def test_rows_and_raw_written_incrementally(tmp_path):
    seen = []
    base = Transport()

    def transport(url, headers, body):
        out = tmp_path / 'collected'
        seen.append((len((out / 'raw.jsonl').read_text().splitlines()), len((out / 'recorded.jsonl').read_text().splitlines()),
                     (out / c.INCOMPLETE_MARKER).exists()))
        return base(url, headers, body)
    summary, rows, _, out = run(tmp_path, panel(target('xai', 'grok-4.7', repetitions=3)), transport)
    assert seen == [(0, 0, True), (1, 1, True), (2, 2, True)]
    assert summary['completion'] == 'complete' and not (out / c.INCOMPLETE_MARKER).exists()


def test_interrupt_keeps_paid_responses_and_marks_incomplete(tmp_path):
    base, count = Transport(), []

    def transport(url, headers, body):
        count.append(1)
        if len(count) == 2:
            raise KeyboardInterrupt
        return base(url, headers, body)
    out = tmp_path / 'collected'
    summary = c.collect(panel(target('xai', 'grok-4.7', repetitions=3)), out, transport=transport,
                        secret_lookup=secrets(), resolver=resolver)
    rows = [json.loads(l) for l in (out / 'recorded.jsonl').read_text().splitlines()]
    assert summary['completion'] == 'incomplete' and (out / c.INCOMPLETE_MARKER).exists()
    assert json.loads((out / 'collection.json').read_text())['completion'] == 'incomplete'
    assert len((out / 'raw.jsonl').read_text().splitlines()) == 1
    assert [r['status'] for r in rows] == ['success', 'error', 'error']
    assert all(r['error_detail'].startswith('interrupted') for r in rows[1:])
    for row in rows:
        p.normalize_observation(row)


def test_unexpected_job_exception_becomes_failed_row(tmp_path):
    def bad_resolver(url):
        raise RuntimeError('resolver exploded')
    out = tmp_path / 'collected'
    c.collect(panel(target('gemini', 'gemini-3.8-flash')), out, transport=Transport(), secret_lookup=secrets(),
              resolver=bad_resolver)
    row = json.loads((out / 'recorded.jsonl').read_text())
    assert row['status'] == 'error' and row['error_detail'].startswith('internal_error')


def test_apex_domain_without_www_warns_and_subdomain_counts_reported(tmp_path):
    summary, _, _, _ = run(tmp_path)
    assert any('www.cedar.example' in w for w in summary['warnings'])
    assert 'subdomain_citation_rows' in summary
    assert 'upper' not in summary['note']


@pytest.mark.parametrize('status,body,expected', [
    (402, '{}', 'credit_exhausted'),
    (429, '{"error": {"code": "insufficient_quota"}}', 'credit_exhausted'),
    (400, '{"error": {"message": "Your credit balance is too low"}}', 'credit_exhausted'),
    (400, '{"error": {"message": "credits are mentioned in this unrelated validation error"}}', 'http_error'),
    (429, '{"error": {"message": "Rate limit reached"}}', 'rate_limited'),
])
def test_credit_classification_is_narrow(status, body, expected):
    assert c._classify_http(status, body) == expected


def test_review_can_override_brand_mentioned(tmp_path):
    _, rows, _, out = run(tmp_path, panel(target('xai', 'grok-4.7')))
    row_id = rows[0]['row_id']
    assert rows[0]['brand_mentioned'] is False
    reviewed = tmp_path / 'reviewed.jsonl'
    c.apply_review(out / 'recorded.jsonl', {row_id: {'brand_mentioned': True, 'recommended': False, 'reviewer': 'R'}}, reviewed)
    row = json.loads(reviewed.read_text())
    assert row['brand_mentioned'] is True and row['recommended'] is False
    assert 'brand_mentioned by reviewer R' in row['annotation_method']
    with pytest.raises(ValueError):
        c.apply_review(out / 'recorded.jsonl', {row_id: {'brand_mentioned': False, 'recommended': True, 'reviewer': 'R'}},
                       tmp_path / 'bad.jsonl')
