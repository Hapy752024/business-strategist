"""Refresh bounded company-register access checks, independently of case research."""
import argparse
import os
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts/validate_apis'))

def main(provider=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=['france', 'switzerland', 'sec'], default=provider, required=provider is None)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.out:
        os.environ['EVIDENCE_SCOUT_VALIDATION_DIR'] = str(args.out.absolute())
    from scripts.market_research.registry_sources import collect
    from common import finish, redact_sensitive
    query = SimpleNamespace(provider=args.provider, query='Nestle' if args.provider == 'switzerland' else 'Carrefour', limit=1, identifier='320193')
    try:
        capture = collect(query)
        summary = {'status': 'ok' if capture['observations'] else 'empty_result', 'observations': len(capture['observations']), 'review_status': 'pending', 'complete_within_query': capture['complete_within_query']}
    except (ValueError, KeyError, TypeError) as exc:
        message = redact_sensitive(str(exc))
        summary = {'status': 'missing_credentials' if message.startswith('Missing ') else 'failed', 'error': message}
        capture = summary
    return finish({'france': 'france_register', 'switzerland': 'switzerland_register', 'sec': 'sec_register'}[args.provider], summary, capture)

if __name__ == '__main__':
    raise SystemExit(main())
