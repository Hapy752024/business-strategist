#!/usr/bin/env python3
"""Import smoke-test signups into an experiment result draft and an anonymised responder ledger.

Counts are cumulative per variant and channel: a row that reached `booked` also counts as
identified, exposed, responded and eligible. Rows with an unknown variant, missing channel
or unmapped stage are reported, never counted. Names, emails and other identity fields are
never copied; responder ids are salted-free SHA256 prefixes of the preset's id field.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGES = ('identified', 'exposed', 'responded', 'eligible', 'booked', 'attended', 'usable_incident')


def load_presets(root: Path = ROOT) -> dict:
    return json.loads((Path(root) / 'config/responder-import-presets.json').read_text())['presets']


def _field(row: dict, dotted: str | None):
    """Read a flat key, or walk a dotted path through nested objects when no flat key matches."""
    if not dotted:
        return None
    if dotted in row:
        return row[dotted]
    value = row
    for part in dotted.split('.'):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _empty() -> dict:
    return {stage: 0 for stage in STAGES}


def import_rows(rows: list[dict], mapping: dict, variants: set[str]) -> tuple[list[dict], dict, list[dict]]:
    responders, counts, unmapped = [], {}, []
    for index, row in enumerate(rows):
        variant = str(_field(row, mapping['variant_field']) or '').strip()
        channel = str(_field(row, mapping['channel_field']) or '').strip()
        raw_stage = str(_field(row, mapping['stage_field']) or '').strip()
        if variant not in variants:
            unmapped.append({'row': index, 'reason': f'unknown variant {variant or "<empty>"}'})
            continue
        if not channel:
            unmapped.append({'row': index, 'reason': 'missing channel'})
            continue
        stage = mapping['stage_values'].get(raw_stage)
        if stage not in STAGES:
            unmapped.append({'row': index, 'reason': f'unknown stage {raw_stage or "<empty>"}'})
            continue
        funnel = counts.setdefault(variant, {}).setdefault(channel, _empty())
        for name in STAGES[:STAGES.index(stage) + 1]:
            funnel[name] += 1
        ident = str(_field(row, mapping['id_field']) or f'row-{index}')
        fit = _field(row, mapping.get('segment_fit_field'))
        responders.append({'id': 'R-' + hashlib.sha256(ident.encode()).hexdigest()[:12], 'variant': variant,
                           'source': channel, 'stage': stage,
                           'segment_fit': str(fit) if fit not in (None, '') else 'unresolved'})
    return responders, counts, unmapped


def read_source(path: Path) -> list[dict]:
    if path.suffix == '.csv':
        with path.open(newline='', encoding='utf-8') as fh:
            return list(csv.DictReader(fh))
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ValueError('JSON source must be a list of objects')
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--card', required=True, type=Path, help='Draft or published experiment card JSON')
    ap.add_argument('--source', required=True, type=Path, help='CSV or JSON export')
    ap.add_argument('--preset', required=True, choices=sorted(load_presets()))
    ap.add_argument('--out', required=True, type=Path, help='Result draft for experiment-close')
    ap.add_argument('--responders', type=Path, help='Responder ledger to append to; defaults to the card responders_ref path')
    ap.add_argument('--allow-unmapped', action='store_true')
    a = ap.parse_args(argv)
    card = json.loads(a.card.read_text())
    responders, counts, unmapped = import_rows(read_source(a.source), load_presets()[a.preset], set(card['variants']))
    for item in unmapped:
        print(f"unmapped row {item['row']}: {item['reason']}", file=sys.stderr)
    if unmapped and not a.allow_unmapped:
        return 1
    ledger = a.responders or (Path(card['responders_ref']['path']) if card.get('responders_ref') else None)
    if ledger is not None:
        existing = json.loads(ledger.read_text()) if ledger.is_file() else []
        seen = {r.get('id') for r in existing}
        ledger.write_text(json.dumps(existing + [r for r in responders if r['id'] not in seen], indent=2) + '\n')
    a.out.write_text(json.dumps({'counts': counts, 'interpretation': None, 'assumption_updates': [],
                                 'limits': ['Volunteer signups, not customers.'] + (
                                     [f'{len(unmapped)} rows were not mapped and not counted.'] if unmapped else [])},
                                indent=2) + '\n')
    print(a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
