"""Compare compatible dated SEO audit scopes, without claiming ranking improvement."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def compare(before: dict, after: dict) -> dict:
    fields = ('schema_version', 'site_identity', 'inventory_sha256', 'config_sha256', 'checker_version')
    if any(not before.get(k) or before.get(k) != after.get(k) for k in fields):
        return {'status': 'non_comparable', 'reason': 'missing or incompatible site/inventory/config/checker identity'}
    if not before.get('source_revision') or not after.get('source_revision'):
        return {'status': 'non_comparable', 'reason': 'source revision is unknown'}
    try:
        a, b = (datetime.fromisoformat(r['checked_at'].replace('Z', '+00:00')) for r in (before, after))
        if a.utcoffset() is None or b.utcoffset() is None or b <= a:
            raise ValueError('invalid ordering')
    except (KeyError, ValueError, TypeError):
        return {'status': 'non_comparable', 'reason': 'audit dates are missing or not ordered'}
    coverage = [r.get('coverage', {}) for r in (before, after)]
    if any(c.get('complete') is not True or not c.get('routes') for c in coverage) or coverage[0]['routes'] != coverage[1]['routes']:
        return {'status': 'non_comparable', 'reason': 'audit check coverage is incomplete, unknown or different'}
    if any(report.get('seo_limits') for report in (before, after)):
        return {'status': 'non_comparable', 'reason': 'SEO checks have unmeasured coverage'}
    left, right = set(before.get('errors', [])), set(after.get('errors', []))
    return {'status': 'observed_change', 'new_regressions': sorted(right-left), 'resolved': sorted(left-right),
            'existing': sorted(left&right), 'unmeasured': after.get('seo_limits', []),
            'boundary': 'Technical observations only; no search-performance or causal claim.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('before', type=Path); ap.add_argument('after', type=Path); ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    result = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
    raw = json.dumps(result, indent=2) + '\n'
    if args.out:
        args.out.write_text(raw)
    print(raw)
    return 0 if result['status'] == 'observed_change' else 1


if __name__ == '__main__':
    raise SystemExit(main())
