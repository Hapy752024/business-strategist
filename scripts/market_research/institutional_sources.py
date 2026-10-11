"""Bounded institutional data retrieval using the existing captured-fact contract.

Explicit dataset IDs and series keys are inputs, not guessed research findings.
Every observation remains pending review against its original capture.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts/validate_apis'))
from common import get_secret, http_get, now_iso, redact_sensitive, request_budget, status_from_response, with_query
from scripts.market_research.research_sources import public_url

PROVIDERS = {
    'ecb': ('European Central Bank', None),
    'fred': ('Federal Reserve Bank of St. Louis', 'FRED_API_KEY'),
    'bis': ('Bank for International Settlements', None),
    'world_bank': ('World Bank', None),
    'companies_house': ('Companies House', 'COMPANIES_HOUSE_API_KEY'),
}


def identifier(value, label, pattern=r'[A-Za-z0-9_.+;-]+'):
    if not re.fullmatch(pattern, value):
        raise ValueError('Invalid or missing ' + label)
    return value


def build_request(provider, args, page=1):
    headers = {}
    key_name = PROVIDERS[provider][1]
    key = get_secret(key_name)[1] if key_name else None
    if key_name and not key:
        raise ValueError('Missing ' + key_name)
    if getattr(args, 'discover', False):
        if provider == 'companies_house':
            raise ValueError('Use Companies House search/profile for registry discovery')
        if provider == 'fred':
            return with_query('https://api.stlouisfed.org/fred/series', {'series_id': identifier(args.series, 'series ID'), 'api_key': key, 'file_type': 'json'}), headers
        if provider == 'world_bank':
            return with_query('https://api.worldbank.org/v2/indicator/' + identifier(args.dataset, 'indicator ID'), {'format': 'json'}), headers
        flow = identifier(args.dataset, 'dataflow ID')
        if provider == 'ecb':
            base = 'https://data-api.ecb.europa.eu/service/dataflow/ECB/' + flow + '/latest'
        else:
            base = 'https://stats.bis.org/api/v2/structure/dataflow/' + identifier(args.agency, 'agency ID') + '/' + flow + '/' + identifier(args.version, 'version')
        headers['Accept'] = 'application/vnd.sdmx.structure+xml;version=2.1'
        return with_query(base, {'references': 'all'}), headers
    if provider in {'ecb', 'bis'}:
        flow = identifier(args.dataset, 'dataflow ID')
        series = identifier(args.series, 'explicit series key')
        if provider == 'ecb':
            base = 'https://data-api.ecb.europa.eu/service/data/' + flow + '/' + series
            params = {'startPeriod': args.start, 'endPeriod': args.end, 'format': 'csvdata', 'lastNObservations': args.limit}
        else:
            agency = identifier(args.agency, 'agency ID')
            version = identifier(args.version, 'dataflow version', r'[A-Za-z0-9_.+-]+')
            base = 'https://stats.bis.org/api/v2/data/dataflow/' + agency + '/' + flow + '/' + version + '/' + series
            # v2 uses component filters; time selection is not the v1 startPeriod syntax.
            params = {'lastNObservations': args.limit}
            if args.start or args.end:
                predicates = []
                if args.start:
                    predicates.append('ge:' + args.start)
                if args.end:
                    predicates.append('le:' + args.end)
                params['c[TIME_PERIOD]'] = '+'.join(predicates)
            headers['Accept'] = 'application/vnd.sdmx.data+csv;version=1.0.0'
        url = with_query(base, {key: value for key, value in params.items() if value != ''})
    elif provider == 'fred':
        series = identifier(args.series, 'FRED series ID')
        url = with_query('https://api.stlouisfed.org/fred/series/observations',
                         {'series_id': series, 'api_key': key, 'file_type': 'json', 'limit': args.limit,
                          'offset': (page - 1) * args.limit, 'observation_start': args.start,
                          'observation_end': args.end, 'sort_order': 'desc'})
    elif provider == 'world_bank':
        country = identifier(args.country, 'World Bank country code')
        indicator = identifier(args.dataset, 'World Bank indicator ID')
        period = (args.start + ':' + args.end if args.start and args.end else args.start or args.end)
        url = with_query('https://api.worldbank.org/v2/country/' + country + '/indicator/' + indicator,
                         {'format': 'json', 'per_page': args.limit, 'page': page, 'date': period})
    else:
        headers['Authorization'] = 'Basic ' + base64.b64encode((key + ':').encode()).decode()
        if args.company_number:
            number = identifier(args.company_number, 'company number', r'[A-Za-z0-9]+')
            url = 'https://api.company-information.service.gov.uk/company/' + quote(number)
        elif args.query.strip():
            url = with_query('https://api.company-information.service.gov.uk/search/companies',
                             {'q': args.query, 'items_per_page': args.limit, 'start_index': (page - 1) * args.limit})
        else:
            raise ValueError('Companies House requires --query or --company-number')
    return url, headers


def normalize(provider, body, args):
    if provider in {'ecb', 'bis'}:
        if not isinstance(body, dict) or 'text' not in body or body.get('text_truncated'):
            raise ValueError('Expected complete SDMX CSV')
        rows = list(csv.DictReader(io.StringIO(body['text'].lstrip('\ufeff'))))
        if not rows or not {'TIME_PERIOD', 'OBS_VALUE'}.issubset(rows[0]):
            raise ValueError('SDMX CSV lacks observation/time columns or is empty')
        return [{'metric': args.dataset + ':' + args.series, 'period': row['TIME_PERIOD'],
                 'value': row['OBS_VALUE'] or None, 'unit': row.get('UNIT_MEASURE') or row.get('UNIT') or args.unit,
                 'dimensions': row, 'flags': row.get('OBS_STATUS')} for row in rows], False
    if provider == 'fred':
        if not isinstance(body, dict) or 'observations' not in body:
            raise ValueError('FRED observations response missing')
        rows = [{'metric': args.series, 'period': row['date'], 'value': None if row['value'] == '.' else row['value'],
                 'unit': args.unit, 'realtime_start': row.get('realtime_start'), 'realtime_end': row.get('realtime_end')}
                for row in body['observations']]
        return rows, int(body.get('offset', 0)) + len(rows) < int(body.get('count', len(rows)))
    if provider == 'world_bank':
        if not isinstance(body, list) or len(body) != 2 or not isinstance(body[0], dict):
            raise ValueError('World Bank returned an error or invalid paged response')
        rows = [{'metric': row['indicator']['id'], 'period': row['date'],
                 'value': None if row['value'] is None else str(row['value']), 'unit': row.get('unit') or args.unit,
                 'country': row.get('country'), 'country_code': row.get('countryiso3code'),
                 'indicator': row['indicator'], 'decimal': row.get('decimal')}
                for row in (body[1] or [])]
        return rows, int(body[0]['page']) < int(body[0]['pages'])
    if not isinstance(body, dict):
        raise ValueError('Companies House returned an invalid response')
    data = [body] if args.company_number else body.get('items')
    if data is None:
        raise ValueError('Companies House search results missing')
    rows = [{'identity': row['company_number'], 'company_number': row['company_number'],
             'name': row.get('company_name') or row.get('title'), 'company_status': row.get('company_status'),
             'company_type': row.get('type') or row.get('company_type'),
             'creation_date': row.get('date_of_creation'), 'cessation_date': row.get('date_of_cessation'),
             'sic_codes': row.get('sic_codes'), 'links': row.get('links', {}),
             'commercial_success': 'unresolved'} for row in data]
    return rows, not args.company_number and int(body.get('start_index', 0)) + len(rows) < int(body.get('total_results', len(rows)))


def collect(provider, args):
    pages, observations, seen, companies = [], [], set(), {}
    status, gap, more = 'ok', None, False
    with request_budget(args.max_pages) as budget:
        for page_number in range(1, args.max_pages + 1):
            url, headers = build_request(provider, args, page_number)
            response = http_get(url, headers=headers, timeout=30, max_bytes=2000000, max_text_chars=2000000)
            pages.append(redact_sensitive({'url': public_url(url), 'response': response}))
            if not response.get('ok'):
                status, gap = status_from_response(response), response.get('error') or 'Provider unavailable'
                break
            if getattr(args, 'discover', False):
                metadata = metadata_records(provider, response['body'])
                return {'provider': provider, 'publisher': PROVIDERS[provider][0], 'retrieved_at': now_iso(),
                        'kind': 'dataset_metadata', 'scope': {'population': args.population, 'geography': args.country or 'unknown', 'language': 'en'},
                        'status': 'ok', 'coverage_gap': None, 'complete_within_query': True,
                        'coverage_basis': 'Metadata for the explicitly requested dataset/series; no observations collected',
                        'request_budget': budget.summary(), 'pages': pages, 'observations': [], 'metadata': metadata}
            rows, more = normalize(provider, response['body'], args)
            for row in rows:
                fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
                if fingerprint in seen:
                    continue
                if row.get('identity'):
                    previous = companies.get(row['identity'])
                    if previous and previous != fingerprint:
                        raise ValueError('Conflicting company records within the paged capture')
                    companies[row['identity']] = fingerprint
                seen.add(fingerprint)
                observations.append({**row, 'page': page_number - 1, 'currency': None, 'scope': args.population})
            if not more:
                break
    return {'provider': provider, 'publisher': PROVIDERS[provider][0], 'retrieved_at': now_iso(),
            'kind': 'company_observation' if provider == 'companies_house' else 'statistics',
            'scope': {'population': args.population, 'geography': args.country or 'unknown', 'language': 'en'},
            'status': status, 'coverage_gap': gap, 'complete_within_query': status == 'ok' and not more,
            'coverage_basis': 'SDMX lastNObservations per series; broader history excluded' if provider in {'ecb', 'bis'} else 'bounded paged query',
            'request_budget': budget.summary(), 'pages': pages, 'observations': observations}


def metadata_records(provider, body):
    if provider == 'fred':
        if not isinstance(body, dict) or 'seriess' not in body:
            raise ValueError('FRED series definitions are missing')
        return body['seriess']
    if provider == 'world_bank':
        if not isinstance(body, list) or len(body) != 2:
            raise ValueError('World Bank indicator definitions are missing')
        return body[1] or []
    text = body.get('text', '') if isinstance(body, dict) else ''
    if not text or body.get('text_truncated') or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('Expected bounded SDMX structure XML')
    try:
        document = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise ValueError('Malformed SDMX metadata XML') from exc
    records = []
    for node in document.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in {'Dataflow', 'DataStructure', 'Codelist', 'ConceptScheme'}:
            records.append({'type': tag, **node.attrib, 'labels': [child.text for child in node.iter() if child.tag.rsplit('}', 1)[-1] in {'Name', 'Description'} and child.text]})
    if not records:
        raise ValueError('No SDMX structure definitions found')
    return records


def facts(capture, raw):
    digest = hashlib.sha256(raw).hexdigest()
    for index, row in enumerate(capture['observations']):
        identity = capture['provider'] + ':' + str(row.get('identity') or hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest())
        yield {'schema_version': '1.0', 'evidence_id': 'fact-' + hashlib.sha256(identity.encode()).hexdigest()[:20],
               'fact_kind': 'company_observation' if capture['kind'] == 'company_observation' else 'statistic',
               'source': capture['provider'], 'source_record_id': identity, 'source_url': capture['pages'][row['page']]['url'],
               'publisher': capture['publisher'], 'source_role': 'company_register' if capture['kind'] == 'company_observation' else 'official_statistics',
               'retrieved_at': capture['retrieved_at'], 'reference_period': row.get('period') or row.get('creation_date') or 'unknown',
               'geography': capture['scope']['geography'], 'population': capture['scope']['population'], 'original_language': capture['scope'].get('language', 'unknown'),
               'capture_path': 'capture.json', 'content_sha256': digest, 'locator': '/observations/' + str(index),
               'observation': row, 'text': json.dumps(row, ensure_ascii=False, sort_keys=True), 'review_status': 'pending',
               'uncertainty': ['Review source definitions, units and target-market applicability; this is not customer demand evidence.']}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=list(PROVIDERS), required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--dataset', default='')
    p.add_argument('--discover', action='store_true', help='Retrieve definitions for an explicit dataset/series rather than observations')
    p.add_argument('--series', default='')
    p.add_argument('--agency', default='BIS')
    p.add_argument('--version', default='+', help='Verified BIS flow version; + selects its latest version')
    p.add_argument('--country', default='')
    p.add_argument('--start', default='')
    p.add_argument('--end', default='')
    p.add_argument('--unit', default='unknown')
    p.add_argument('--population', default='unknown')
    p.add_argument('--query', default='')
    p.add_argument('--company-number', default='')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--max-pages', type=int, default=1)
    return p


def main():
    p = parser()
    args = p.parse_args()
    if args.out.exists() or not 1 <= args.limit <= 100 or not 1 <= args.max_pages <= 10:
        p.error('Use a fresh output directory, limit 1–100 and max-pages 1–10')
    for value in (args.start, args.end):
        if value and not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?', value):
            p.error('Dates must use YYYY, YYYY-MM or YYYY-MM-DD')
    if args.start and args.end and args.start > args.end:
        p.error('Start must precede end')
    try:
        capture = collect(args.provider, args)
    except (ValueError, KeyError, TypeError) as exc:
        p.exit(2, str(redact_sensitive(str(exc))) + '\n')
    raw = (json.dumps(capture, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()
    args.out.mkdir(parents=True)
    (args.out / 'capture.json').write_bytes(raw)
    rows = list(facts(capture, raw))
    (args.out / 'research-facts.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    summary = {key: capture[key] for key in ('provider', 'status', 'coverage_gap', 'complete_within_query', 'coverage_basis')}
    summary.update(observations=len(rows), review_status='pending')
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    return 0 if capture['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
