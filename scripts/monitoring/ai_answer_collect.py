"""Live AI-answer collection into format-2 recordings for `ai_answer_probe.py`.

Each declared panel target/prompt/repetition becomes exactly one row: the raw answer, citations and provider
request id on success, or null flags plus an explicit reason on failure (missing credentials included).
Answers are never synthesized. Brand mentions and subject-domain citations are annotated by rule; whether an
answer *recommends* the subject is left to a reviewer whenever the subject is mentioned (`review` subcommand).

Cost control: planned calls are counted and an estimate printed before any network access; a run above
`--max-calls` (default 20) is refused before the first request. Keys are read via `get_secret`, sent only in
headers and redacted from every written file.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.monitoring import ai_answer_probe as probe  # noqa: E402
from scripts.validate_apis.common import get_secret  # noqa: E402

DEFAULT_CAP = 20
TIMEOUT = 180
# location_code values from DataForSEO /v3/serp/google/locations for common panel countries.
DATAFORSEO_LOCATIONS = {'DE': 2276, 'AT': 2040, 'CH': 2756, 'GB': 2826, 'US': 2840, 'FR': 2250, 'NL': 2528}


class CapExceeded(RuntimeError):
    status = 'cap_exceeded'


def _country(locale: str) -> str:
    parts = re.split(r'[-_]', locale)
    if len(parts) < 2 or len(parts[-1]) != 2:
        raise ValueError(f'locale {locale!r}: language-COUNTRY required (e.g. de-DE)')
    return parts[-1].upper()


def _language(locale: str) -> str:
    return re.split(r'[-_]', locale)[0].lower()


# ---------- request builders (body only; auth goes in headers) ----------

def _openai_request(target, prompt):
    tool = {'type': 'web_search', 'user_location': {'type': 'approximate', 'country': _country(target['locale'])}}
    return ('https://api.openai.com/v1/responses',
            {'model': target['model'], 'input': prompt, 'tools': [tool], 'tool_choice': 'auto',
             'include': ['web_search_call.action.sources']})


def _xai_request(target, prompt):
    return ('https://api.x.ai/v1/responses',
            {'model': target['model'], 'input': [{'role': 'user', 'content': prompt}], 'tools': [{'type': 'web_search'}]})


def _gemini_request(target, prompt):
    return (f"https://generativelanguage.googleapis.com/v1beta/models/{target['model']}:generateContent",
            {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}], 'tools': [{'google_search': {}}]})


def _anthropic_request(target, prompt):
    tool = {'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': 5,
            'user_location': {'type': 'approximate', 'country': _country(target['locale'])}}
    return ('https://api.anthropic.com/v1/messages',
            {'model': target['model'], 'max_tokens': 2048, 'messages': [{'role': 'user', 'content': prompt}], 'tools': [tool]})


def _perplexity_request(target, prompt):
    return ('https://api.perplexity.ai/chat/completions',
            {'model': target['model'], 'messages': [{'role': 'user', 'content': prompt}]})


def _dataforseo_task(target, prompt):
    country = _country(target['locale'])
    if country not in DATAFORSEO_LOCATIONS:
        raise ValueError(f'locale {target["locale"]!r}: no DataForSEO location_code mapping')
    return {'keyword': prompt[:700], 'location_code': DATAFORSEO_LOCATIONS[country],
            'language_code': _language(target['locale']), 'device': 'desktop'}


def _ai_mode_request(target, prompt):
    return 'https://api.dataforseo.com/v3/serp/google/ai_mode/live/advanced', [_dataforseo_task(target, prompt)]


def _ai_overview_request(target, prompt):
    return ('https://api.dataforseo.com/v3/serp/google/organic/live/advanced',
            [{**_dataforseo_task(target, prompt), 'load_async_ai_overview': True}])


# ---------- response parsers (documented shapes; see fixtures/monitoring/collector-responses) ----------

def _unique(urls):
    seen, out = set(), []
    for url in urls:
        if isinstance(url, str) and url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


INLINE_LINK = re.compile(r'\]\((https?://[^)\s]+)\)')


def _responses_api(body, _resolver=None):
    """OpenAI and xAI Responses API.

    Cited = url_citation annotations anchored to answer text (end_index > start_index) plus markdown links the
    answer visibly shows. xAI also returns every search source as an unanchored annotation (start=end=0) and in
    top-level `citations`; those are consulted sources, not citations.
    """
    texts, details, consulted, unanchored = [], [], [], []
    for item in body.get('output') or []:
        if item.get('type') == 'web_search_call':
            consulted += [s.get('url') for s in (item.get('action') or {}).get('sources') or []]
        if item.get('type') == 'message':
            for part in item.get('content') or []:
                if part.get('type') != 'output_text':
                    continue
                texts.append(part.get('text') or '')
                for note in part.get('annotations') or []:
                    if note.get('type') != 'url_citation':
                        continue
                    anchored = (note.get('end_index') or 0) > (note.get('start_index') or 0)
                    if anchored:
                        details.append({'url': note.get('url'), 'title': note.get('title'), 'via': 'annotation'})
                    else:
                        unanchored.append(note.get('url'))
    answer = '\n'.join(texts)
    details += [{'url': url, 'via': 'inline_link'} for url in INLINE_LINK.findall(answer)]
    cited = _unique(d['url'] for d in details)
    consulted += (body.get('citations') or []) + unanchored
    usage = body.get('usage') or {}
    ticks = usage.get('cost_in_usd_ticks')  # xAI: 1 USD = 1e10 ticks
    seen, unique_details = set(), []
    for d in details:
        if d['url'] and d['url'] not in seen:
            seen.add(d['url'])
            unique_details.append(d)
    return {'answer_text': answer, 'citation_urls': cited, 'consulted_urls': _unique(consulted),
            'request_id': body.get('id'), 'response_model': body.get('model'), 'citation_details': unique_details,
            'provider_cost_usd': round(ticks / 1e10, 10) if isinstance(ticks, (int, float)) else None}


def _gemini(body, resolver=None):
    candidate = (body.get('candidates') or [{}])[0]
    text = ''.join(part.get('text', '') for part in (candidate.get('content') or {}).get('parts') or [])
    details = []
    for chunk in (candidate.get('groundingMetadata') or {}).get('groundingChunks') or []:
        web = chunk.get('web') or {}
        uri = web.get('uri')
        if not uri:
            continue
        resolved = resolver(uri) if resolver and urlsplit(uri).hostname == 'vertexaisearch.cloud.google.com' else None
        details.append({'url': resolved or uri, 'title': web.get('title'), 'grounding_uri': uri,
                        'resolved': bool(resolved) or urlsplit(uri).hostname != 'vertexaisearch.cloud.google.com'})
    if not text and candidate.get('finishReason') not in (None, 'STOP'):
        raise ProviderFailure('provider_error', f"finishReason {candidate.get('finishReason')}")
    return {'answer_text': text, 'citation_urls': _unique(d['url'] for d in details), 'consulted_urls': [],
            'request_id': body.get('responseId'), 'response_model': body.get('modelVersion'), 'citation_details': details,
            'search_queries': (candidate.get('groundingMetadata') or {}).get('webSearchQueries') or []}


def _anthropic(body, _resolver=None):
    if body.get('stop_reason') == 'pause_turn':
        raise ProviderFailure('provider_error', 'pause_turn: long-running search turn was not continued')
    texts, cited, consulted = [], [], []
    for block in body.get('content') or []:
        if block.get('type') == 'text':
            texts.append(block.get('text') or '')
            cited += [c.get('url') for c in block.get('citations') or [] if c.get('type') == 'web_search_result_location']
        elif block.get('type') == 'web_search_tool_result' and isinstance(block.get('content'), list):
            consulted += [r.get('url') for r in block['content']]
    return {'answer_text': ''.join(texts), 'citation_urls': _unique(cited), 'consulted_urls': _unique(consulted),
            'request_id': body.get('id'), 'response_model': body.get('model'),
            'citation_details': [{'url': u} for u in _unique(cited)]}


def _perplexity(body, _resolver=None):
    message = ((body.get('choices') or [{}])[0].get('message') or {})
    cited = body.get('citations') or []
    return {'answer_text': message.get('content') or '', 'citation_urls': _unique(cited),
            'consulted_urls': _unique([r.get('url') for r in body.get('search_results') or []]),
            'request_id': body.get('id'), 'response_model': body.get('model'),
            'citation_details': [{'url': u} for u in _unique(cited)]}


def _dataforseo(body, _resolver=None):
    tasks = body.get('tasks') or []
    if body.get('status_code') != 20000 or not tasks:
        raise ProviderFailure('provider_error', f"DataForSEO {body.get('status_code')} {body.get('status_message')}")
    task = tasks[0]
    if task.get('status_code') != 20000:
        status = 'credit_exhausted' if task.get('status_code') in (40200, 40210) else 'provider_error'
        raise ProviderFailure(status, f"DataForSEO task {task.get('status_code')} {task.get('status_message')}",
                              request_id=task.get('id'))
    overviews = [item for result in task.get('result') or [] for item in result.get('items') or []
                 if item.get('type') == 'ai_overview']
    if not overviews:
        raise ProviderFailure('unsupported', 'no AI answer shown for this query at collection time', request_id=task.get('id'))
    texts, refs = [], []
    for overview in overviews:
        texts.append(overview.get('markdown') or '\n'.join(e.get('text') or '' for e in overview.get('items') or []))
        for element in overview.get('items') or []:
            refs += element.get('references') or []
        refs += overview.get('references') or []
    urls = _unique(r.get('url') for r in refs)
    return {'answer_text': '\n\n'.join(t for t in texts if t), 'citation_urls': urls, 'consulted_urls': [],
            'request_id': task.get('id'), 'response_model': None, 'provider_cost_usd': task.get('cost'),
            'citation_details': [{'url': r.get('url'), 'title': r.get('title'), 'source': r.get('source')} for r in refs if r.get('url')]}


def _bearer(key):
    return {'Authorization': 'Bearer ' + key}


ENGINES = {
    'openai': {'surface': 'api', 'secrets': ('OPENAI_API_KEY',), 'request': _openai_request, 'parse': _responses_api,
               'headers': lambda k: _bearer(k[0]), 'source': 'api:openai:/v1/responses',
               'config': lambda loc: f'web_search;user_location.country={_country(loc)};include=web_search_call.action.sources',
               'estimate_usd': 0.03},
    'xai': {'surface': 'api', 'secrets': ('GROK_API_KEY', 'XAI_API_KEY'), 'request': _xai_request, 'parse': _responses_api,
            'headers': lambda k: _bearer(k[0]), 'source': 'api:xai:/v1/responses',
            'config': lambda loc: 'web_search', 'estimate_usd': 0.25},
    'gemini': {'surface': 'api', 'secrets': ('GEMINI_API_KEY',), 'request': _gemini_request, 'parse': _gemini,
               'headers': lambda k: {'x-goog-api-key': k[0]}, 'source': 'api:gemini:generateContent',
               'config': lambda loc: 'google_search', 'estimate_usd': 0.06},
    'anthropic': {'surface': 'api', 'secrets': ('ANTHROPIC_API_KEY',), 'request': _anthropic_request, 'parse': _anthropic,
                  'headers': lambda k: {'x-api-key': k[0], 'anthropic-version': '2023-06-01'},
                  'source': 'api:anthropic:/v1/messages',
                  'config': lambda loc: f'web_search_20250305;max_uses=5;user_location.country={_country(loc)}',
                  'estimate_usd': 0.08},
    'perplexity': {'surface': 'api', 'secrets': ('PERPLEXITY_API_KEY',), 'request': _perplexity_request, 'parse': _perplexity,
                   'headers': lambda k: _bearer(k[0]), 'source': 'api:perplexity:/chat/completions',
                   'config': lambda loc: 'sonar_builtin_search', 'estimate_usd': 0.02},
    'google-ai-mode': {'surface': 'consumer', 'secrets': ('DATAFORSEO_LOGIN', 'DATAFORSEO_PASSWORD'), 'pair': True,
                       'request': _ai_mode_request, 'parse': _dataforseo, 'source': 'dataforseo:serp/google/ai_mode/live/advanced',
                       'headers': lambda k: {'Authorization': 'Basic ' + base64.b64encode(f'{k[0]}:{k[1]}'.encode()).decode()},
                       'config': lambda loc: f'dataforseo:ai_mode;location_code={DATAFORSEO_LOCATIONS.get(_country(loc))};device=desktop',
                       'estimate_usd': 0.01},
    'google-ai-overview': {'surface': 'ai_overview', 'secrets': ('DATAFORSEO_LOGIN', 'DATAFORSEO_PASSWORD'), 'pair': True,
                           'request': _ai_overview_request, 'parse': _dataforseo,
                           'source': 'dataforseo:serp/google/organic/live/advanced',
                           'headers': lambda k: {'Authorization': 'Basic ' + base64.b64encode(f'{k[0]}:{k[1]}'.encode()).decode()},
                           'config': lambda loc: (f'dataforseo:organic+load_async_ai_overview;location_code='
                                                  f'{DATAFORSEO_LOCATIONS.get(_country(loc))};device=desktop'),
                           'estimate_usd': 0.01},
}


class ProviderFailure(RuntimeError):
    def __init__(self, status, message, request_id=None):
        super().__init__(message)
        self.status, self.request_id = status, request_id


def expected_search_config(engine: str, locale: str) -> str:
    return ENGINES[engine]['config'](locale)


# ---------- annotation ----------

def annotate(answer: str, citations: list[str], subject: dict) -> dict:
    """Rule annotation. A mention is the subject name or a declared domain as a whole word in the answer text."""
    terms = [subject['name'], *subject['domains']]
    hits = []
    for term in terms:
        for match in re.finditer(r'(?<![\w.-])' + re.escape(term) + r'(?![\w-])', answer, re.I):
            hits.append(answer[max(0, match.start() - 80):match.end() + 80])
    domains = set(subject['domains'])
    exact = [u for u in citations if urlsplit(u).hostname in domains]
    sub = [u for u in citations if u not in exact and any((urlsplit(u).hostname or '').endswith('.' + d) for d in domains)]
    mentioned = bool(hits)
    return {'brand_mentioned': mentioned, 'url_cited': bool(exact),
            # Not named means not recommended; a named subject needs a human judgement.
            'recommended': None if mentioned else False,
            'review_required': ['recommended'] if mentioned else [],
            'mention_evidence': hits[:5], 'subject_citations': exact, 'subdomain_citations': sub}


# ---------- transport and secrets ----------

def _urllib_transport(url, headers, body):
    if os.environ.get('AI_ANSWER_COLLECT_OFFLINE'):
        raise RuntimeError('network disabled by AI_ANSWER_COLLECT_OFFLINE')
    request = urllib.request.Request(url, json.dumps(body).encode(), {**headers, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()


def _resolve_redirect(url):
    """Read the Location of a Gemini grounding redirect without following it (no provider charge)."""
    class NoFollow(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        urllib.request.build_opener(NoFollow).open(urllib.request.Request(url, method='HEAD'), timeout=20)
    except urllib.error.HTTPError as exc:
        location = exc.headers.get('Location')
        return location if location and urlsplit(location).scheme in ('http', 'https') else None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    return None


def _secret_lookup(name):
    return get_secret(name)[1]


def _redactor(secrets):
    values = sorted({s for s in secrets if s}, key=len, reverse=True)

    def redact(text):
        for value in values:
            text = text.replace(value, '[REDACTED]')
        return re.sub(r'(sk-|xai-|AIza)[A-Za-z0-9_\-]{8,}', r'\1[REDACTED]', text)
    return redact


def _classify_http(status, body_text):
    lower = body_text.lower()
    if status == 402 or 'insufficient_quota' in lower or 'credit balance' in lower or 'credits' in lower:
        return 'credit_exhausted'
    if status == 429 and ('quota' in lower or 'billing' in lower):
        return 'quota_exceeded'  # plan/tier quota: check the provider billing/quota page, then rerun
    return {401: 'auth_failed', 403: 'auth_failed', 404: 'model_or_endpoint_not_found', 429: 'rate_limited'}.get(
        status, 'http_error')


# ---------- planning and collection ----------

def plan(panel_raw: dict, secret_lookup=_secret_lookup) -> list[dict]:
    panel = probe.load_panel(panel_raw)
    jobs = []
    for target in panel_raw['targets']:
        engine = target['engine']
        if engine not in ENGINES:
            raise ValueError(f'target.engine {engine!r}: supported engines are {sorted(ENGINES)}')
        spec = ENGINES[engine]
        if target['surface'] != spec['surface']:
            raise ValueError(f"target {engine}: surface must be {spec['surface']!r}")
        expected = expected_search_config(engine, target['locale'])
        if target['search_config'] != expected:
            raise ValueError(f'target {engine}: search_config must state the effective settings exactly: {expected!r}')
        names = spec['secrets']
        if spec.get('pair'):
            keys = [secret_lookup(n) for n in names]
            missing = [n for n, k in zip(names, keys) if not k]
        else:
            found = next(((n, secret_lookup(n)) for n in names if secret_lookup(n)), None)
            keys, missing = ([found[1]], []) if found else ([], [names[0]])
        for prompt in panel['prompts']:
            for repetition in range(1, target['repetitions'] + 1):
                jobs.append({'target': target, 'prompt': prompt, 'repetition': repetition,
                             'keys': keys, 'missing': missing})
    return jobs


def estimate(jobs) -> dict:
    calls = [j for j in jobs if not j['missing']]
    by_engine = {}
    for job in calls:
        engine = job['target']['engine']
        by_engine[engine] = by_engine.get(engine, 0) + 1
    return {'planned_calls': len(calls), 'skipped_missing_credentials': len(jobs) - len(calls), 'calls_by_engine': by_engine,
            'estimated_cost_usd': round(sum(ENGINES[e]['estimate_usd'] * n for e, n in by_engine.items()), 4),
            'note': 'assumed per-call upper estimates (search fee + typical tokens); actual usage is recorded per row'}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _row(job, subject, timestamp):
    target, prompt = job['target'], job['prompt']
    spec = ENGINES[target['engine']]
    return {**{k: target[k] for k in probe.TARGET_FIELDS},
            'prompt_id': prompt['prompt_id'], 'prompt_version': prompt['prompt_version'],
            'prompt_type': prompt['prompt_type'], 'prompt_text': prompt['text'], 'repetition': job['repetition'],
            'timestamp': timestamp, 'target_brand': subject['name'], 'target_url': 'https://' + subject['domains'][0],
            'recording_source': spec['source'], 'collection_method': 'api',
            'row_id': f"{target['engine']}|{target['model']}|{prompt['prompt_id']}@{prompt['prompt_version']}|{job['repetition']}"}


def _failed(row, status, detail, request_id=None):
    return {**row, 'status': 'unsupported' if status == 'unsupported' else 'error',
            'error_detail': f'{status}: {detail}' if status != 'unsupported' else detail,
            'provider_request_id': request_id, 'annotation_method': 'none (no answer)',
            **{f: None for f in probe.TRACKED}}


def _execute(job, row, subject, transport, resolver, redact):
    spec = ENGINES[job['target']['engine']]
    url, body = spec['request'](job['target'], job['prompt']['text'])
    raw = {'row_id': row['row_id'], 'timestamp': row['timestamp'], 'url': url, 'request_body': body}
    try:
        status, headers, payload = transport(url, spec['headers'](job['keys']), body)
    except Exception as exc:  # network failure: unknown, never absence
        raw['error'] = redact(f'{type(exc).__name__}: {exc}')
        return _failed(row, 'network_error', raw['error']), raw
    text = payload.decode('utf-8', 'replace') if isinstance(payload, bytes) else str(payload)
    header_id = next((v for k, v in (headers or {}).items() if k.lower() in ('x-request-id', 'request-id')), None)
    raw.update(http_status=status, response_request_id=header_id, response=redact(text))
    if status != 200:
        return _failed(row, _classify_http(status, text), redact(text)[:300], header_id), raw
    try:
        parsed = spec['parse'](json.loads(text), resolver)
    except ProviderFailure as exc:
        return _failed(row, exc.status, redact(str(exc)), exc.request_id or header_id), raw
    except (ValueError, AttributeError, TypeError, IndexError) as exc:
        return _failed(row, 'parse_error', type(exc).__name__, header_id), raw
    if not parsed['answer_text'].strip():
        return _failed(row, 'empty_answer', 'provider returned no answer text', parsed['request_id'] or header_id), raw
    valid = [u for u in parsed['citation_urls'] if _public(u)]
    notes = annotate(parsed['answer_text'], valid, subject)
    usage = json.loads(text).get('usage') or json.loads(text).get('usageMetadata')
    return {**row, 'status': 'success', 'answer_text': parsed['answer_text'], 'citation_urls': valid,
            'citation_details': parsed['citation_details'], 'consulted_urls': [u for u in parsed['consulted_urls'] if _public(u)],
            'provider_request_id': parsed['request_id'] or header_id, 'provider_http_request_id': header_id,
            'provider_response_model': parsed['response_model'], 'search_queries': parsed.get('search_queries', []),
            'usage': usage, 'provider_cost_usd': parsed.get('provider_cost_usd'),
            'brand_mentioned': notes['brand_mentioned'], 'url_cited': notes['url_cited'], 'recommended': notes['recommended'],
            'review_required': notes['review_required'], 'mention_evidence': notes['mention_evidence'],
            'subdomain_citations': notes['subdomain_citations'],
            'annotation_method': 'rule: brand/domain whole-word match; citation hostname exactly in subject.domains'
                                 + ('; recommended pending reviewer' if notes['review_required'] else '; not named so not recommended')}, raw


def _public(url):
    try:
        probe._url(url, 'citation_url')
        return True
    except ValueError:
        return False


def collect(panel_raw: dict, out: Path, *, max_calls: int = DEFAULT_CAP, transport=None, secret_lookup=_secret_lookup,
            resolver=_resolve_redirect, announce=None) -> dict:
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError('--out must be a new, non-existing directory')
    jobs = plan(panel_raw, secret_lookup)
    budget = estimate(jobs)
    if announce:
        announce({**budget, 'cap': max_calls})
    if budget['planned_calls'] > max_calls:
        raise CapExceeded(f"{budget['planned_calls']} planned calls exceed --max-calls {max_calls}; nothing was sent")
    transport = transport or _urllib_transport
    subject = probe.load_panel(panel_raw)['subject']
    redact = _redactor([k for j in jobs for k in j['keys']])
    rows, raws, sent = [], [], 0
    for job in jobs:
        row = _row(job, subject, _now())
        if job['missing']:
            rows.append(_failed(row, 'missing_credentials', ', '.join(job['missing'])))
            continue
        if sent >= max_calls:  # defensive: never exceed the cap even if planning changes
            rows.append(_failed(row, 'cap_exceeded', f'--max-calls {max_calls} reached'))
            continue
        sent += 1
        result, raw = _execute(job, row, subject, transport, resolver, redact)
        rows.append(result)
        raws.append(raw)
    for row in rows:
        probe.normalize_observation({**row, 'recommended': False} if row.get('review_required') else row)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()
    pending = sum(1 for r in rows if r.get('review_required'))
    costs = [r['provider_cost_usd'] for r in rows if isinstance(r.get('provider_cost_usd'), (int, float))]
    summary = {**budget, 'cap': max_calls, 'calls_sent': sent, 'rows': len(rows),
               'statuses': {s: sum(1 for r in rows if r['status'] == s) for s in probe.STATUSES},
               'failures': [{'row_id': r['row_id'], 'detail': r['error_detail']} for r in rows if r['status'] != 'success'],
               'rows_needing_review': pending, 'importable': pending == 0,
               'provider_reported_cost_usd': round(sum(costs), 8) if costs else None,
               'next_step': ('run `review` with reviewer decisions for rows with review_required, then ai_answer_probe.py'
                             if pending else 'run ai_answer_probe.py with this panel and recorded.jsonl')}
    files = {'recorded.jsonl': ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows),
             'raw.jsonl': ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in raws),
             'panel.json': json.dumps(panel_raw, indent=2, ensure_ascii=False) + '\n',
             'collection.json': json.dumps(summary, indent=2, ensure_ascii=False) + '\n'}
    for name, content in files.items():
        with (out / name).open('x', encoding='utf-8') as handle:
            handle.write(redact(content))
    return summary


def apply_review(recorded: Path, decisions: dict, out: Path) -> int:
    """Write a new recordings file with reviewer judgements for `recommended`; returns rows still pending."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError('review output must be a new file')
    lines, pending = [], 0
    for line in Path(recorded).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        decision = decisions.get(row.get('row_id'))
        if row.get('review_required') and decision:
            if type(decision.get('recommended')) is not bool or not str(decision.get('reviewer', '')).strip():
                raise ValueError(f"{row['row_id']}: decision needs boolean recommended and a reviewer")
            row.update(recommended=decision['recommended'], review_required=[], review_note=decision.get('note'),
                       annotation_method=row['annotation_method'].replace('recommended pending reviewer',
                                                                          f"recommended by reviewer {decision['reviewer']}"))
            probe.normalize_observation(row)
        elif row.get('review_required'):
            pending += 1
        lines.append(json.dumps(row, ensure_ascii=False) + '\n')
    with out.open('x', encoding='utf-8') as handle:
        handle.write(''.join(lines))
    return pending


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('collect', help='Collect live answers for a format-2 panel')
    run.add_argument('--panel', type=Path, required=True)
    run.add_argument('--out', type=Path, required=True, help='New directory; never replaced')
    run.add_argument('--max-calls', type=int, default=DEFAULT_CAP)
    run.add_argument('--dry-run', action='store_true', help='Print the plan and estimate only')
    configs = sub.add_parser('configs', help='Print the exact search_config/surface for an engine and locale')
    configs.add_argument('--locale', required=True)
    review = sub.add_parser('review', help='Apply reviewer decisions {row_id: {recommended, reviewer, note}}')
    review.add_argument('--recorded', type=Path, required=True)
    review.add_argument('--decisions', type=Path, required=True)
    review.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)

    def say(data):
        print(json.dumps(data, ensure_ascii=False), flush=True)
    try:
        if args.command == 'configs':
            say({e: {'surface': s['surface'], 'search_config': s['config'](args.locale)} for e, s in ENGINES.items()})
            return 0
        if args.command == 'review':
            pending = apply_review(args.recorded, json.loads(args.decisions.read_text(encoding='utf-8')), args.out)
            say({'status': 'ok', 'out': str(args.out), 'rows_still_pending': pending})
            return 0 if pending == 0 else 2
        panel_raw = json.loads(args.panel.read_text(encoding='utf-8'))
        if args.dry_run:
            say({**estimate(plan(panel_raw)), 'cap': args.max_calls, 'dry_run': True})
            return 0
        summary = collect(panel_raw, args.out, max_calls=args.max_calls, announce=say)
    except CapExceeded as exc:
        say({'status': 'cap_exceeded', 'message': str(exc)})
        return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        say({'status': 'fail', 'message': str(exc)})
        return 1
    say({'status': 'complete', 'out': str(args.out), **summary})
    return 0 if summary['importable'] and not summary['failures'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
