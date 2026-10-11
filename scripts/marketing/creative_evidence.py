"""Source-bound comparative creative observations; attention is not customer demand."""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.link_observations import ROOT, bound_bytes, url_key

SCHEMA = json.loads((ROOT / 'schemas/creative-evidence.schema.json').read_text())
OBSERVED = ('url', 'creator', 'platform', 'format', 'language', 'market', 'published_at', 'observed_at', 'distribution', 'metrics')


def validate(document: dict, base: Path | None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(document)]
    if errors:
        return errors
    ids, urls = set(), set()
    for row in document['examples']:
        ident = row['id']
        if ident in ids:
            errors.append('duplicate example ID: ' + ident)
        ids.add(ident)
        try:
            url = url_key(row['url'])
            if url in urls:
                errors.append('duplicate example URL: ' + ident)
            urls.add(url)
            published, observed = (datetime.fromisoformat(row[k].replace('Z', '+00:00')) for k in ('published_at', 'observed_at'))
            if published.utcoffset() is None or observed.utcoffset() is None or observed < published:
                errors.append(ident + ': invalid observation chronology/timezone')
            snapshot = json.loads(bound_bytes(row['source'], base, staged))
            if any(row[key] != snapshot.get(key) for key in OBSERVED):
                errors.append(ident + ': observed fields differ from retained source extract')
            for name, metric in row['metrics'].items():
                value = metric['value']
                if metric['availability'] == 'available':
                    if type(value) is not int or value < 0:
                        errors.append(ident + ': available counts require nonnegative integers: ' + name)
                elif value is not None:
                    errors.append(ident + ': unavailable counts must be null: ' + name)
        except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
            errors.append(ident + ': ' + str(exc))
    by_id = {r['id']: r for r in document['examples']}
    tests = document.get('tests', [])
    if len({t['id'] for t in tests}) != len(tests):
        errors.append('test IDs must be unique')
    for test in tests:
        for ident in test['example_ids'] + test['counterexample_ids']:
            if ident not in by_id:
                errors.append('test refers to unknown example: ' + ident)
    return errors


def compare(document: dict) -> dict:
    """Only call after validation; ratios and grouping never establish causality."""
    cohorts = {}
    excluded = []
    for row in document['examples']:
        age = int((datetime.fromisoformat(row['observed_at'].replace('Z', '+00:00')) -
                   datetime.fromisoformat(row['published_at'].replace('Z', '+00:00'))).total_seconds() // 86400)
        metric_defs = tuple((name, metric['definition']) for name, metric in sorted(row['metrics'].items()))
        key = (row['platform'], row['format'], row['language'], row['market'], row['distribution'], age, metric_defs)
        if row['distribution'] == 'unknown':
            excluded.append({'id': row['id'], 'reason': 'distribution is unknown; no known-distribution comparison'})
            continue
        views = row['metrics']['views']
        ratios = {}
        for name in ('saves', 'shares', 'comments'):
            metric = row['metrics'].get(name)
            eligible = (views['availability'] == 'available' and views['value'] > 0 and metric and metric['availability'] == 'available')
            try:
                ratio = metric['value'] * 1000 / views['value'] if eligible else None
            except OverflowError:
                ratio = None
            ratios[name + '_per_1000_views'] = ratio if ratio is None or math.isfinite(ratio) else None
        cohorts.setdefault(key, []).append({'id': row['id'], 'creator': row['creator'], 'pattern': row['pattern'], 'ratios': ratios})
    results = []
    for key, rows in cohorts.items():
        patterns = {}
        for row in rows:
            if row['pattern']:
                patterns.setdefault(row['pattern'], set())
                if row['creator']:
                    patterns[row['pattern']].add(row['creator'])
        results.append({'context': {'platform': key[0], 'format': key[1], 'language': key[2], 'market': key[3],
                                   'distribution': key[4], 'observation_age_days': key[5], 'metric_definitions': dict(key[6])},
                        'examples': rows, 'patterns': [{'pattern': p, 'known_creators': sorted(c), 'replicated': len(c) >= 2} for p, c in patterns.items()],
                        'limits': 'Small, selected sample. Descriptive ratios and format annotations do not explain causal or commercial success.'})
    return {'cohorts': results, 'excluded': excluded, 'selection_basis': document['selection_basis'],
            'tests': document.get('tests', []),
            'annotation_boundary': 'Hooks, patterns and test held conditions are unverified analyst annotations; replication counts annotations across known creators, not independent confirmation. Tests are proposals, not observed controlled experiments.', 'boundary': 'Attention observations and test hypotheses only; no demand or revenue receipt.'}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('document', type=Path); ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    try:
        document = json.loads(args.document.read_text())
        errors = validate(document, args.base)
        result = {'valid': not errors, 'errors': errors}
        if not errors:
            result['comparison'] = compare(document)
        if args.out and not errors:
            args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    except (ValueError, OSError) as exc:
        result = {'valid': False, 'errors': [str(exc)]}
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(not result['valid'])


if __name__ == '__main__':
    raise SystemExit(main())
