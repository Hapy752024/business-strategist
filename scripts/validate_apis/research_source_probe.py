"""Low-volume source checks; successful extraction is not reviewed research."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.market_research.research_sources import PROVIDERS, collect, parser
from common import finish, redact_sensitive


def main(provider):
    args = parser(provider).parse_args(['--out', '/unused-probe-output'])
    args.query = 'consumer behavior'
    args.discover = provider == 'swiss_stats'
    if provider == 'census':
        # The full catalog exceeds the bounded capture size and does not test key authentication.
        args.dataset = '2024/acs/acs5'
        args.variables = 'NAME,B01003_001E'
        args.geography = 'us:*'
        args.unit = 'persons'
        args.population = 'US resident population, ACS 5-year estimate'
    if provider == 'eurostat':
        args.dataset = 'demo_pjan'
        args.dimension = ['geo=CH', 'time=2025', 'sex=T', 'age=TOTAL']
        args.population = 'Swiss population on 1 January'
        args.unit = 'people'
    args.series = ['CUUR0000SA0'] if provider == 'bls' else []
    args.limit = 1
    try:
        capture = collect(provider, args)
        summary = {'status': capture['status'], 'probe': 'Bounded retrieval; original-source review remains pending',
                   'kind': capture['kind'], 'observations': len(capture['observations']),
                   'required_env': [PROVIDERS[provider][1]] if PROVIDERS[provider][1] else []}
        if not args.discover and not capture['observations'] and capture['kind'] != 'discovery':
            summary['status'] = 'empty_result'
    except (ValueError, KeyError, TypeError) as exc:
        error = redact_sensitive(str(exc))
        capture = {'error': error}
        summary = {'status': 'missing_credentials' if error.startswith('Missing ') else 'failed', 'error': error}
    return finish(provider, summary, capture)
