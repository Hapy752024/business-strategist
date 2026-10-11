"""Bounded public company-register queries and original exported-row ingestion."""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts/validate_apis'))
from common import http_get, get_secret, now_iso, redact_sensitive, with_query
from scripts.market_research.institutional_sources import facts


def collect(args):
    if args.provider == 'france':
        url = with_query('https://recherche-entreprises.api.gouv.fr/search', {'q': args.query, 'per_page': args.limit, 'page': 1})
        response = http_get(url, timeout=30, max_bytes=2000000)
        if not response.get('ok'):
            raise ValueError('France registry request failed: ' + str(response.get('status_code')))
        body = response['body']
        if 'results' not in body:
            raise ValueError('France registry results missing')
        rows = [{'identity': row['siren'], 'name': row.get('nom_complet'), 'legal_status': row.get('etat_administratif'),
                 'industry': row.get('activite_principale'), 'establishments_count': row.get('nombre_etablissements'),
                 'commercial_success': 'unresolved'} for row in body['results']]
        complete = int(body.get('total_results', len(rows))) <= len(rows)
        publisher, country = 'French government company directory', 'France'
    elif args.provider == 'switzerland':
        term = json.dumps(args.query, ensure_ascii=False)
        query = ('SELECT ?company ?name FROM <https://lindas.admin.ch/foj/zefix> WHERE { '
                 '?company a <https://schema.ld.admin.ch/ZefixOrganisation> . '
                 '?company ?nameProperty ?name . VALUES ?nameProperty { <http://schema.org/name> <https://schema.org/name> } '
                 'FILTER(CONTAINS(LCASE(STR(?name)), LCASE(' + term + '))) } LIMIT ' + str(args.limit + 1))
        url = with_query('https://ld.admin.ch/query', {'query': query, 'format': 'json'})
        response = http_get(url, headers={'Accept': 'application/sparql-results+json'}, timeout=30, max_bytes=2000000)
        if not response.get('ok'):
            raise ValueError('Zefix linked-data request failed: ' + str(response.get('status_code')))
        bindings = response['body'].get('results', {}).get('bindings')
        if bindings is None:
            raise ValueError('Zefix query bindings missing')
        rows = [{'identity': row['company']['value'], 'name': row['name']['value'], 'commercial_success': 'unresolved'} for row in bindings[:args.limit]]
        complete = len(bindings) <= args.limit
        publisher, country = 'Swiss Federal Commercial Registry Office / LINDAS', 'Switzerland'
    elif args.provider == 'sec':
        if not re.fullmatch(r'\d{1,10}', args.identifier or ''):
            raise ValueError('SEC requires --identifier CIK (1–10 digits)')
        contact = get_secret('SEC_USER_AGENT')[1]
        if not contact and get_secret('CROSSREF_MAILTO')[1]:
            contact = 'business-strategist ' + get_secret('CROSSREF_MAILTO')[1]
        if not contact or '@' not in contact:
            raise ValueError('Missing SEC_USER_AGENT: supply a descriptive organization and contact email, not an API key')
        url = 'https://data.sec.gov/submissions/CIK' + args.identifier.zfill(10) + '.json'
        response = http_get(url, headers={'User-Agent': contact}, timeout=30, max_bytes=2000000)
        if not response.get('ok'):
            raise ValueError('SEC company request failed: ' + str(response.get('status_code')))
        body = response['body']
        rows = [{'identity': str(body['cik']), 'name': body['name'], 'industry': body.get('sic'),
                 'industry_description': body.get('sicDescription'), 'commercial_success': 'unresolved'}]
        complete, publisher, country = True, 'US Securities and Exchange Commission', 'United States'
    else:
        if not args.input or not args.source_url or not args.identifier_field:
            raise ValueError('Original register exports require --input, --source-url and --identifier-field')
        if not args.source_url.startswith('https://') or args.input.stat().st_size > 2000000:
            raise ValueError('Use an original HTTPS source and a bounded export')
        raw = args.input.read_bytes()
        values = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))) if args.input.suffix.lower() == '.csv' else json.loads(raw)
        if not isinstance(values, list) or any(not isinstance(row, dict) for row in values):
            raise ValueError('Export must contain rows of objects')
        rows = []
        for index, row in enumerate(values[:args.limit]):
            if not row.get(args.identifier_field):
                raise ValueError('Original export row has no declared legal identifier')
            rows.append({'identity': str(row[args.identifier_field]), 'original_row': row, 'row_index': index,
                         'commercial_success': 'unresolved'})
        url, response = args.source_url, {'ok': True, 'body': {'original_sha256': hashlib.sha256(raw).hexdigest()}}
        complete, publisher, country = len(values) <= args.limit, args.publisher, args.country
    return {'provider': args.provider, 'publisher': publisher, 'retrieved_at': now_iso(), 'kind': 'company_observation',
            'scope': {'geography': country, 'population': 'Registered legal entities; operating activity unverified', 'language': 'fr' if args.provider == 'france' else 'unknown'},
            'status': 'ok', 'complete_within_query': complete, 'coverage_gap': None if complete else 'Bounded result/export rows; broader population not covered',
            'pages': [redact_sensitive({'url': url, 'response': response})],
            'observations': [{**row, 'page': 0, 'currency': None, 'scope': 'Registered legal entities; operating activity unverified'} for row in rows]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=['france', 'switzerland', 'sec', 'register_export'], required=True)
    p.add_argument('--query', default='')
    p.add_argument('--identifier')
    p.add_argument('--input', type=Path)
    p.add_argument('--source-url')
    p.add_argument('--identifier-field')
    p.add_argument('--publisher', default='Unspecified register publisher')
    p.add_argument('--country', default='unknown')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists() or not 1 <= args.limit <= 100:
        p.error('Use a fresh output directory and limit 1–100')
    if args.provider in {'france', 'switzerland'} and not args.query.strip():
        p.error('A company query is required')
    try:
        capture = collect(args)
        args.out.mkdir(parents=True)
        if args.provider == 'register_export':
            original = args.out / ('original' + args.input.suffix.lower())
            original.write_bytes(args.input.read_bytes())
            capture.update(original_path=original.name, original_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
        raw = (json.dumps(capture, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()
        (args.out / 'capture.json').write_bytes(raw)
        (args.out / 'research-facts.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in facts(capture, raw)))
        print(json.dumps({'provider': args.provider, 'observations': len(capture['observations']), 'complete_within_query': capture['complete_within_query'], 'review_status': 'pending'}))
    except Exception as exc:
        p.exit(2, str(redact_sensitive(str(exc))) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
