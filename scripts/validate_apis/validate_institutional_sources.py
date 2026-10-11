"""Explicit low-volume institutional probes; writes only to the supplied directory."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(provider=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=['ecb', 'fred', 'bis', 'world_bank', 'companies_house'], default=provider, required=provider is None)
    p.add_argument('--out', type=Path, default=Path(os.environ['EVIDENCE_SCOUT_VALIDATION_DIR']) if os.environ.get('EVIDENCE_SCOUT_VALIDATION_DIR') else None)
    args = p.parse_args()
    if args.out is None:
        p.error('--out or EVIDENCE_SCOUT_VALIDATION_DIR is required')
    os.environ['EVIDENCE_SCOUT_VALIDATION_DIR'] = str(args.out.absolute())
    from scripts.market_research.institutional_sources import collect, parser, PROVIDERS
    from common import finish, redact_sensitive
    query = parser().parse_args(['--provider', args.provider, '--out', '/unused', '--limit', '1'])
    if args.provider == 'ecb':
        query.dataset, query.series, query.country = 'EXR', 'M.USD.EUR.SP00.A', 'Euro area'
    elif args.provider == 'bis':
        query.dataset, query.series, query.country = 'WS_CBPOL', 'M.CH', 'Switzerland'
    elif args.provider == 'fred':
        query.series, query.country = 'FEDFUNDS', 'United States'
    elif args.provider == 'world_bank':
        query.dataset, query.country, query.start, query.end = 'SP.POP.TOTL', 'CHE', '2024', '2024'
        query.unit, query.population = 'persons', 'Total population'
    else:
        query.company_number, query.country = '00000006', 'United Kingdom'
    try:
        capture = collect(args.provider, query)
        summary = {'status': capture['status'], 'observations': len(capture['observations']),
                   'coverage_basis': capture['coverage_basis'], 'review_status': 'pending',
                   'required_env': [PROVIDERS[args.provider][1]] if PROVIDERS[args.provider][1] else []}
        if summary['status'] == 'ok' and not capture['observations']:
            summary['status'] = 'empty_result'
    except (ValueError, KeyError, TypeError) as exc:
        message = redact_sensitive(str(exc))
        summary = {'status': 'missing_credentials' if message.startswith('Missing ') else 'failed', 'error': message}
        capture = summary
    return finish(args.provider, summary, capture)


if __name__ == '__main__':
    raise SystemExit(main())
