"""Read-only source-worker repair assessment; never dispatches or promotes a stage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.link_observations import ROOT, bound_bytes, resolve_bytes

SCHEMA = json.loads((ROOT / 'schemas/source-work-packet.schema.json').read_text())


def validate(document: dict) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(document)]
    if errors:
        return errors
    units = {u['id']: u for u in document['units']}
    if len(units) != len(document['units']):
        errors.append('unit IDs must be unique')
    owners = {}
    for unit in units.values():
        if len(set(unit['checks'])) != len(unit['checks']):
            errors.append(unit['id'] + ': duplicate checks')
        for path in unit['output_paths']:
            if any(path == other or path.startswith(other + '/') or other.startswith(path + '/') for other in owners):
                errors.append('overlapping output ownership: ' + path)
            owners[path] = unit['id']
        if len({b['path'] for b in unit['inputs']}) != len(unit['inputs']):
            errors.append(unit['id'] + ': duplicate inputs')
        if unit['state'] == 'accepted' and not unit.get('receipt'):
            errors.append(unit['id'] + ': accepted unit requires a receipt')
        if unit['state'] == 'rejected' and not unit.get('return'):
            errors.append(unit['id'] + ': rejected unit requires a return packet')
    for unit in units.values():
        dependencies = set(unit['dependencies'])
        for dep in dependencies:
            if dep not in units or dep == unit['id']:
                errors.append(unit['id'] + ': unknown or self dependency')
            elif not set(units[dep]['output_paths']) & {b['path'] for b in unit['inputs']}:
                errors.append(unit['id'] + ': dependency must supply a named input')
        for binding in unit['inputs']:
            owner = owners.get(binding['path'])
            if owner and owner not in dependencies:
                errors.append(unit['id'] + ': input owner missing from dependencies')
    visiting, visited = set(), set()
    def visit(ident):
        if ident in visiting:
            errors.append('dependency cycle: ' + ident)
            return
        if ident in visited:
            return
        visiting.add(ident)
        for dep in units[ident]['dependencies']:
            if dep in units:
                visit(dep)
        visiting.remove(ident)
        visited.add(ident)
    for ident in units:
        visit(ident)
    return errors


def assess(document: dict, base: Path, previous: dict | None = None) -> dict:
    errors = validate(document)
    if previous is not None:
        errors += ['previous ledger: ' + e for e in validate(previous)]
    if errors:
        return {'valid': False, 'complete': False, 'errors': errors, 'units': []}
    units = {u['id']: u for u in document['units']}
    old_units = {u['id']: u for u in (previous or {}).get('units', [])}
    errors += [ident + ': accepted unit cannot be removed' for ident, old in old_units.items() if old['state'] == 'accepted' and ident not in units]
    rows = {}
    for unit in units.values():
        issues = []
        # Apply the same path checks to not-yet-created owned outputs.
        for path in unit['output_paths']:
            if path in {'.', ''}:
                errors.append(unit['id'] + ': output must name a file')
            try:
                resolve_bytes(base, path, {path: b''})
            except (ValueError, OSError) as exc:
                errors.append(unit['id'] + ': ' + str(exc))
        for binding in unit['inputs']:
            try:
                bound_bytes(binding, base)
            except (ValueError, OSError) as exc:
                issues.append('input: ' + str(exc))
        status = 'stale' if issues else unit['state']
        old = old_units.get(unit['id'])
        if old:
            if unit['attempts'] < old['attempts']:
                errors.append(unit['id'] + ': attempt counter cannot decrease')
            if old['state'] == 'accepted' and old['inputs'] == unit['inputs']:
                if old.get('receipt') != unit.get('receipt') or unit['state'] != 'accepted' or old['output_paths'] != unit['output_paths'] or old['checks'] != unit['checks'] or old['scope'] != unit['scope']:
                    errors.append(unit['id'] + ': unchanged accepted work cannot be rewritten')
        if unit['state'] == 'accepted':
            try:
                receipt = json.loads(bound_bytes(unit['receipt'], base))
                expected = {'unit_id', 'scope', 'inputs', 'outputs', 'checks'}
                if not isinstance(receipt, dict) or set(receipt) != expected:
                    raise ValueError('invalid receipt shape')
                if receipt['unit_id'] != unit['id'] or receipt['scope'] != unit['scope'] or receipt['inputs'] != unit['inputs']:
                    raise ValueError('receipt does not match unit/input scope')
                output_paths = [b['path'] for b in receipt['outputs']]
                if len(set(output_paths)) != len(output_paths) or set(output_paths) != set(unit['output_paths']):
                    raise ValueError('receipt does not bind every owned output')
                for binding in receipt['outputs']:
                    bound_bytes(binding, base)
                if not isinstance(receipt['checks'], dict) or set(receipt['checks']) != set(unit['checks']):
                    raise ValueError('receipt does not cover required checks')
                for check in receipt['checks'].values():
                    if set(check) != {'status', 'evidence'} or check['status'] != 'pass':
                        raise ValueError('check is not passed')
                    bound_bytes(check['evidence'], base)
            except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
                status = 'stale'
                issues.append('receipt: ' + str(exc))
        if unit['state'] == 'rejected':
            packet = unit['return']
            if packet['requirement'] not in unit['checks'] or packet['allowed_outputs'] != unit['output_paths']:
                errors.append(unit['id'] + ': return exceeds unit scope or names unknown check')
            try:
                bound_bytes(packet['evidence'], base)
            except (ValueError, OSError) as exc:
                issues.append('return: ' + str(exc))
                status = 'stale'
        if unit['state'] in {'pending', 'rejected'} and unit['attempts'] >= unit['attempt_limit']:
            status = 'blocked'
            issues.append('correction attempt limit reached; revise the plan')
        rows[unit['id']] = {'id': unit['id'], 'status': status, 'issues': issues,
                           'ready': status in {'pending', 'rejected'}, 'return': unit.get('return')}
    # Propagate invalid acceptance/unfinished dependencies until stable.
    changed = True
    while changed:
        changed = False
        for unit in units.values():
            row = rows[unit['id']]
            if any(rows[dep]['status'] != 'accepted' for dep in unit['dependencies']):
                row['ready'] = False
                if row['status'] == 'accepted':
                    row['status'] = 'stale'
                    row['issues'].append('dependency acceptance is not current')
                    changed = True
    return {'valid': not errors, 'complete': not errors and all(r['status'] == 'accepted' for r in rows.values()),
            'errors': errors, 'units': list(rows.values()),
            'boundary': 'Receipt consistency only; no source-interpretation or stage acceptance is certified.'}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('ledger', type=Path)
    ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--previous', type=Path)
    args = ap.parse_args()
    try:
        result = assess(json.loads(args.ledger.read_text()), args.base,
                        json.loads(args.previous.read_text()) if args.previous else None)
    except (ValueError, OSError) as exc:
        result = {'valid': False, 'complete': False, 'errors': [str(exc)]}
    print(json.dumps(result, indent=2))
    return int(not result['valid'] or not result['complete'])


if __name__ == '__main__':
    raise SystemExit(main())
