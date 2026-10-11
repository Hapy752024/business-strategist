"""Bounded public-statistics and scholarly-discovery adapters.

API observations are candidates for review, never automatically verified claims.
The retained capture is the extraction authority; units/populations remain unknown
unless supplied or explicitly documented by the provider.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/validate_apis'))
from common import get_secret, http_get, http_post, now_iso, redact_sensitive, request_budget, status_from_response, with_query

PROVIDERS = {
    'eurostat': ('Eurostat', None), 'swiss_stats': ('Swiss Federal Statistical Office', None),
    'opendata_swiss': ('opendata.swiss', None), 'census': ('US Census Bureau', 'CENSUS_API_KEY'),
    'bls': ('US Bureau of Labor Statistics', 'BLS_API_KEY'), 'openalex': ('OpenAlex', 'OPENALEX_API_KEY'),
    'crossref': ('Crossref', None),
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def jsonstat(body):
    """Decode sparse JSON-stat coordinates without dropping zero or suppression."""
    dimensions = body.get('id', [])
    sizes = body.get('size', [])
    if len(dimensions) != len(sizes) or not dimensions:
        raise ValueError('JSON-stat dimensions/sizes missing')
    categories = []
    for name, size in zip(dimensions, sizes):
        category = body['dimension'][name]['category']
        index = category.get('index', {})
        codes = index if isinstance(index, list) else sorted(index, key=index.get)
        if len(codes) != size:
            raise ValueError('JSON-stat dimension index incomplete')
        categories.append(codes)
    values = body.get('value', {})
    flags = body.get('status', {})
    length = 1
    for size in sizes:
        length *= size
    if length > 100000:
        raise ValueError('Narrow the requested statistical dimensions (100000 cells maximum)')
    rows = []
    for index in range(length):
        remaining = index
        coordinates = {}
        for name, size, codes in reversed(list(zip(dimensions, sizes, categories))):
            coordinates[name] = codes[remaining % size]
            remaining //= size
        value = values[index] if isinstance(values, list) and index < len(values) else values.get(str(index)) if isinstance(values, dict) else None
        flag = flags[index] if isinstance(flags, list) and index < len(flags) else flags.get(str(index)) if isinstance(flags, dict) else None
        rows.append({'dimensions': coordinates, 'value': None if value is None else str(value), 'flags': flag,
                     'period': coordinates.get('time', 'unknown'), 'unit': coordinates.get('unit', 'unknown'),
                     'metric': metric(body.get('label', 'statistical_observation'))})
    return rows


def metric(value):
    return re.sub(r'[^a-z0-9]+', '_', str(value).lower()).strip('_') or 'observation'


def normalize(provider, body, args):
    """Return observations or study metadata; discovery responses stay discovery."""
    if provider == 'eurostat' and isinstance(body, dict) and body.get('class') == 'dataset':
        rows = jsonstat(body)
        for row in rows:
            if row['unit'] == 'unknown':
                row['unit'] = args.unit
        return rows, 'statistics'
    if provider == 'opendata_swiss' and isinstance(body, dict) and body.get('success') is False:
        raise ValueError('opendata.swiss rejected the catalogue query')
    if provider == 'swiss_stats' and isinstance(body, dict) and 'text' in body and not args.discover:
        if body.get('text_truncated'):
            raise ValueError('Statistical CSV was truncated; narrow the query')
        text = body['text'].lstrip('\ufeff')
        if not text.strip() or text.lstrip().startswith('<'):
            raise ValueError('Expected SDMX CSV; received empty/non-CSV response')
        rows = list(csv.DictReader(io.StringIO(text)))
        if rows and not {'OBS_VALUE', 'TIME_PERIOD'}.issubset(rows[0]):
            raise ValueError('SDMX CSV lacks observation/time columns')
        return [{'dimensions': {k: v for k, v in row.items() if k != 'OBS_VALUE'},
                 'value': row['OBS_VALUE'] or None, 'period': row['TIME_PERIOD'],
                 'unit': row.get('UNIT_MEASURE') or args.unit,
                 'metric': metric(args.dataset), 'flags': row.get('OBS_STATUS')} for row in rows], 'statistics'
    if provider == 'census' and isinstance(body, list) and body:
        header, *data = body
        if not isinstance(header, list) or any(len(row) != len(header) for row in data):
            raise ValueError('Malformed Census table')
        rows = []
        for row in data:
            dims = dict(zip(header, row))
            for variable in args.variables.split(','):
                if variable == 'NAME' or variable not in dims:
                    continue
                value = dims[variable]
                if value is not None and not re.fullmatch(r'-?\d+(?:\.\d+)?', str(value)):
                    continue  # labels are metadata, not numerical observations
                suppressed = str(value) in {'-666666666', '-999999999', '-888888888', '-222222222', '-555555555', '-333333333'}
                rows.append({'dimensions': dims, 'metric': metric(variable), 'value': None if suppressed else value,
                             'period': args.dataset.split('/')[0], 'unit': args.unit,
                             'flags': 'suppressed' if suppressed else None})
        return rows, 'statistics'
    if provider == 'bls' and isinstance(body, dict):
        if body.get('status') != 'REQUEST_SUCCEEDED' or any('Invalid Series' in msg for msg in body.get('message', [])):
            raise ValueError('BLS rejected the request/series: ' + '; '.join(body.get('message', [])))
        rows = []
        for series in body.get('Results', {}).get('series', []):
            for observation in series.get('data', []):
                rows.append({'dimensions': {'series_id': series['seriesID'], 'catalog': series.get('catalog', {})},
                             'metric': metric(series['seriesID']), 'period': observation['year'] + '-' + observation['period'],
                             'value': observation['value'], 'unit': args.unit, 'flags': observation.get('footnotes', [])})
        return rows, 'statistics'
    if provider in {'openalex', 'crossref'} and isinstance(body, dict):
        works = body.get('results', []) if provider == 'openalex' else body.get('message', {}).get('items', [])
        rows = []
        for work in works:
            doi = str(work.get('doi') or work.get('DOI') or '').lower().removeprefix('https://doi.org/')
            title = work.get('display_name') or work.get('title') or ''
            title = ' '.join(title) if isinstance(title, list) else title
            rows.append({'identity': doi or work.get('id') or work.get('URL'), 'doi': doi or None,
                         'title': title, 'publication_date': work.get('publication_date') or work.get('published'),
                         'access': work.get('open_access') or work.get('link') or [],
                         'reviewed_material': 'metadata_only', 'finding': None,
                         'publisher': work.get('publisher') or None})
        return rows, 'study_metadata'
    return [], 'discovery'


def request(provider, args, cursor=None):
    label, key_name = PROVIDERS[provider]
    key = get_secret(key_name)[1] if key_name else None
    if key_name and not key and provider != 'openalex':
        raise ValueError('Missing ' + key_name)
    headers, payload = {}, None
    filters = {}
    for pair in args.dimension:
        if '=' not in pair:
            raise ValueError('--dimension requires NAME=VALUE')
        k, v = pair.split('=', 1)
        filters.setdefault(k, []).append(v)
    if provider == 'eurostat':
        url = ('https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/dataflow/ESTAT/all/latest' if args.discover or not args.dataset else
               with_query('https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/' + quote(args.dataset, safe=''), {'lang': args.language, **filters}))
    elif provider == 'swiss_stats':
        if not args.dataset and not args.discover:
            raise ValueError('--dataset requires AGENCY,FLOW,VERSION from discovered metadata')
        url = 'https://disseminate.stats.swiss/rest/' + ('dataflow/all/all/latest' if args.discover else 'data/' + quote(args.dataset, safe=',') + '/' + quote(args.filter, safe='.'))
        headers['Accept'] = 'application/vnd.sdmx.structure+xml;version=2.1' if args.discover else 'text/csv;version=2.0.0'
    elif provider == 'opendata_swiss':
        url = with_query('https://ckan.opendata.swiss/api/3/action/package_search', {'q': args.query, 'rows': args.limit})
    elif provider == 'census':
        url = 'https://api.census.gov/data.json' if args.discover else with_query('https://api.census.gov/data/' + quote(args.dataset, safe='/'), {'get': args.variables, 'for': args.geography, 'key': key, **filters})
        if not args.discover and not args.dataset:
            raise ValueError('--dataset required, e.g. YEAR/acs/acs5')
    elif provider == 'bls':
        if not args.series:
            raise ValueError('--series requires a verified BLS series ID')
        url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        payload = {'seriesid': args.series, 'startyear': str(args.start_year), 'endyear': str(args.end_year), 'catalog': True, 'registrationkey': key}
    elif provider == 'openalex':
        url = with_query('https://api.openalex.org/works', {'search': args.query, 'per_page': args.limit, 'cursor': cursor or '*'})
        if key:
            headers['Authorization'] = 'Bearer ' + key
    else:
        email = get_secret('CROSSREF_MAILTO')[1]
        url = with_query('https://api.crossref.org/works', {'query.bibliographic': args.query, 'rows': args.limit, 'cursor': cursor or '*', 'mailto': email})
    kwargs = {'headers': headers, 'timeout': 30, 'max_bytes': 2000000, 'max_text_chars': 2000000}
    response = http_get(url, **kwargs) if payload is None else http_post(url, data=payload, **kwargs)
    return redact_sensitive({'url': url, 'method': 'GET' if payload is None else 'POST', 'parameters': payload, 'response': response})


def collect(provider, args):
    pages, observations, seen, cursor = [], [], set(), None
    kind, complete, status, gap = 'discovery', True, 'ok', None
    with request_budget(args.max_pages) as budget:
        for page_index in range(args.max_pages):
            page = request(provider, args, cursor)
            pages.append(page)
            response = page['response']
            if not response.get('ok'):
                complete, status, gap = False, status_from_response(response), response.get('error') or 'Provider request failed'
                break
            rows, kind = normalize(provider, response.get('body'), args)
            for row in rows:
                identity = row.get('identity') or sha(json.dumps(row, sort_keys=True).encode())
                if identity in seen:
                    continue
                seen.add(identity)
                observations.append({**row, 'page': page_index})
            body = response.get('body') or {}
            if provider == 'openalex':
                next_cursor = body.get('meta', {}).get('next_cursor')
                more = bool(rows) and bool(next_cursor)
            elif provider == 'crossref':
                next_cursor = body.get('message', {}).get('next-cursor')
                more = len(rows) == args.limit and bool(next_cursor)
            else:
                next_cursor, more = None, False
            if not more:
                break
            if next_cursor == cursor:
                raise ValueError('Provider returned a repeated cursor')
            cursor = next_cursor
            if page_index + 1 == args.max_pages:
                complete = False
    captured = {'provider': provider, 'publisher': PROVIDERS[provider][0], 'retrieved_at': now_iso(),
                'scope': {'dataset': args.dataset, 'geography': args.geography, 'population': args.population,
                          'language': args.language, 'query': args.query, 'unit': args.unit},
                'kind': kind, 'status': status, 'complete_within_query': complete, 'next_cursor': cursor,
                'coverage_gap': gap, 'request_budget': budget.summary(), 'pages': pages, 'observations': [{**row, 'currency': None, 'scope': args.population} for row in observations]}
    return captured


def facts(capture, capture_path, capture_digest):
    rows = []
    for index, obs in enumerate(capture['observations']):
        kind = 'study_metadata' if capture['kind'] == 'study_metadata' else 'statistic'
        identity = obs.get('identity') or capture['provider'] + ':' + sha(json.dumps(obs, sort_keys=True).encode())
        rows.append({'schema_version': '1.0', 'evidence_id': 'fact-' + sha(str(identity).encode())[:20],
                     'fact_kind': kind, 'source': capture['provider'], 'source_record_id': identity,
                     'source_url': public_url(capture['pages'][obs['page']]['url']), 'publisher': capture['publisher'],
                     'source_role': 'research_metadata' if kind == 'study_metadata' else 'official_statistics',
                     'retrieved_at': capture['retrieved_at'], 'reference_period': str(obs.get('period') or obs.get('publication_date') or 'unknown'),
                     'geography': capture['scope']['geography'] or 'unknown', 'population': capture['scope']['population'],
                     'original_language': capture['scope']['language'], 'capture_path': capture_path,
                     'content_sha256': capture_digest, 'locator': '/observations/' + str(index),
                     'observation': {**obs, 'currency': None, 'scope': capture['scope']['population']},
                     'text': obs.get('title') or json.dumps(obs, ensure_ascii=False, sort_keys=True),
                     'review_status': 'pending', 'uncertainty': ['Extraction candidate; original capture and contextual definitions require review.']})
    return rows


def public_url(url):
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key.lower() not in {'key', 'api_key', 'apikey', 'registrationkey', 'mailto'}]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def parser(provider):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True, help='Fresh run directory; no automatic project access')
    p.add_argument('--query', default='')
    p.add_argument('--dataset', default='')
    p.add_argument('--discover', action='store_true')
    p.add_argument('--dimension', action='append', default=[])
    p.add_argument('--filter', default='')
    p.add_argument('--variables', default='NAME')
    p.add_argument('--geography', default='')
    p.add_argument('--population', default='unknown')
    p.add_argument('--unit', default='unknown')
    p.add_argument('--language', default='en')
    p.add_argument('--series', action='append', default=[])
    p.add_argument('--start-year', type=int, default=date.today().year - 1)
    p.add_argument('--end-year', type=int, default=date.today().year)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--max-pages', type=int, default=1)
    return p


def main(provider):
    p = parser(provider)
    args = p.parse_args()
    if not 1 <= args.limit <= 100 or not 1 <= args.max_pages <= 10 or args.start_year > args.end_year:
        p.error('Invalid limit, page budget or date range')
    if args.out.exists():
        p.error('--out must be a fresh run directory')
    try:
        capture = collect(provider, args)
    except (ValueError, KeyError, TypeError) as exc:
        p.exit(2, str(redact_sensitive(str(exc))) + '\n')
    args.out.mkdir(parents=True)
    encoded = (json.dumps(capture, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
    (args.out / 'capture.json').write_bytes(encoded)
    rows = facts(capture, 'capture.json', sha(encoded))
    (args.out / 'research-facts.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    summary = {key: capture[key] for key in ('provider', 'status', 'kind', 'complete_within_query', 'coverage_gap')}
    summary.update(observations=len(rows), output=str(args.out), review_status='pending')
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    return 0 if capture['status'] == 'ok' else 1
