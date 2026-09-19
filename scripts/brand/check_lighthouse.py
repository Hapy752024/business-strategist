"""Fail when a Lighthouse JSON report misses the default website lab budgets."""
import argparse
import json
import math
from pathlib import Path


def errors(report):
    failures = []
    limits = {'largest-contentful-paint': 2500, 'cumulative-layout-shift': 0.1, 'total-blocking-time': 200}
    for key, limit in limits.items():
        value = report.get('audits', {}).get(key, {}).get('numericValue')
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or value > limit:
            failures.append(f'{key}: missing/invalid or exceeds {limit}')
    for key, floor in [('performance', .9), ('seo', .95)]:
        value = report.get('categories', {}).get(key, {}).get('score')
        if type(value) not in (int, float) or not math.isfinite(value) or not floor <= value <= 1:
            failures.append(f'{key}: missing/invalid or below {floor}')
    if report.get('runtimeError'):
        failures.append('Lighthouse runtime error')
    return failures


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    args = p.parse_args()
    try:
        failures = errors(json.loads(args.report.read_text()))
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        failures = [str(exc)]
    print(json.dumps({'status': 'fail' if failures else 'pass', 'errors': failures, 'boundary': 'single lab run; not field INP or full SEO proof'}))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
