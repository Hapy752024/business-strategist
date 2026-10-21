#!/usr/bin/env python3
"""Validate assumption registers, experiment cards and the experiment library.

Schema checks use JSON Schema 2020-12; semantic rules (status needs references,
library membership) run after the schema. Returns error strings; empty means valid.

Usage: python3 scripts/validate_case_artifacts.py [--workspace <business-root> --case <id>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'schemas'


def _schema_errors(data, name: str) -> list[str]:
    schema = json.loads((SCHEMAS / f'{name}.schema.json').read_text())
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))]


def load_library(root: Path = ROOT) -> dict:
    return json.loads((Path(root) / 'config/experiment-library.json').read_text())


def validate_library(data: dict) -> list[str]:
    errors = _schema_errors(data, 'experiment-library')
    if errors:
        return errors
    ids = [item['id'] for item in data['experiments']]
    return [f'duplicate library id {i}' for i in sorted({i for i in ids if ids.count(i) > 1})]


def validate_register(data: dict) -> list[str]:
    errors = _schema_errors(data, 'assumption-register')
    if errors:
        return errors
    ids = [entry['id'] for entry in data['entries']]
    errors += [f'duplicate assumption id {i}' for i in sorted({i for i in ids if ids.count(i) > 1})]
    for entry in data['entries']:
        if entry['status'] == 'supported' and not entry['evidence_refs']:
            errors.append(f"{entry['id']}: supported status needs an evidence reference")
        if entry['status'] == 'refuted' and not (entry['counter_evidence_refs'] or entry['evidence_refs']):
            errors.append(f"{entry['id']}: refuted status needs a counter-evidence reference")
        if entry['status'] == 'contested' and not (entry['counter_evidence_refs'] and entry['evidence_refs']):
            errors.append(f"{entry['id']}: contested status needs both evidence and counter-evidence references")
    unknown = [i for i in data['riskiest'] if i not in ids]
    errors += [f'riskiest names unknown assumption {i}' for i in unknown]
    return errors


def validate_card(data: dict, library: dict) -> list[str]:
    errors = _schema_errors(data, 'experiment-card')
    if errors:
        return errors
    if data['library_id'] not in {item['id'] for item in library['experiments']}:
        errors.append(f"library_id {data['library_id']} is not in config/experiment-library.json")
    plan = data['sample_plan']
    if plan['p_low'] >= plan['p_high']:
        errors.append('sample_plan p_low must be below p_high')
    if len(set(data['variants'])) != len(data['variants']):
        errors.append('variants must be unique')
    result = data['result']
    if result:
        unknown = sorted(set(result['counts']) - set(data['variants']))
        errors += [f'result counts name unknown variant {v}' for v in unknown]
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace', type=Path)
    ap.add_argument('--case', default='')
    a = ap.parse_args(argv)
    library = load_library()
    errors = [f'experiment-library: {e}' for e in validate_library(library)]
    if a.workspace and a.case:
        case = a.workspace / 'cases' / a.case
        reg = case / 'assumptions.json'
        if reg.is_file():
            errors += [f'{reg}: {e}' for e in validate_register(json.loads(reg.read_text()))]
        for card in sorted((case / 'experiments').glob('*.json')):
            errors += [f'{card}: {e}' for e in validate_card(json.loads(card.read_text()), library)]
    for line in errors:
        print(line, file=sys.stderr)
    print('case artifacts: ' + ('FAIL' if errors else 'ok'))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
