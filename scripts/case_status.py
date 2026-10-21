#!/usr/bin/env python3
"""Report which contract-declaring routes are runnable, blocked, stale or not adopted for a case.

Read-only. Staleness uses provenance that already exists: case manifest source-binding
digests and the insights state. Routes without a receipt are reported runnable or
blocked on presence alone; nothing here records runs or authorizes dispatch.

Usage: python3 scripts/route_workflow.py status (--project <slug> | --workspace <business-root>) --case <id> [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import case_workspace as cases  # noqa: E402
from scripts import subprojects  # noqa: E402

REGISTER_ARTIFACT = 'assumption-register'


def _consumes(catalog: dict, skill: str, mode: str | None) -> list[dict] | None:
    metadata = catalog.get(skill, {})
    if mode and 'consumes' in metadata.get('modes', {}).get(mode, {}):
        return metadata['modes'][mode]['consumes']
    return metadata.get('consumes')


def _matches(root: Path, item: dict, case_id: str) -> list[Path]:
    found = []
    for pattern in item['path_patterns']:
        found.extend(p for p in root.glob(pattern.replace('{case}', case_id)) if p.is_file())
    return sorted(set(found))


def _stale(root: Path, item: dict, paths: list[Path], manifest: dict) -> bool:
    if item['artifact'] == 'case-insights':
        return manifest.get('insights', {}).get('state') == 'update_pending'
    if item['freshness'] != 'digest':
        return False
    bound = {b['path']: b['digest'] for b in manifest.get('source_bindings', []) if isinstance(b, dict)}
    for path in paths:
        relative = str(path.relative_to(root))
        if relative in bound and bound[relative] != cases.digest(path.read_bytes()):
            return True
    return False


def _booked_responders(root: Path, case_id: str) -> list[str]:
    notes = []
    for card in cases.experiment_cards(root, case_id):
        if card.get('status') not in {'running', 'closed'} or not card.get('responders_ref'):
            continue
        counts = (card.get('result') or {}).get('counts', {})
        if sum(stage.get('booked', 0) for variant in counts.values() for stage in variant.values()) > 0:
            notes.append(card['responders_ref']['path'])
    return notes


def case_status(root: Path, case_id: str) -> list[dict]:
    root = Path(root).absolute()
    try:
        manifest = cases.case_manifest(root, case_id)
    except ValueError as exc:
        print(f'case status unavailable: {exc}', file=sys.stderr)
        raise SystemExit(2) from exc
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text())['skills']
    routes = json.loads((ROOT / 'config/workflow-routes.json').read_text())['routes']
    adopted = (cases.resolve(root, case_id) / cases.REGISTER).is_file()
    rows = []
    for route in routes:
        consumes = _consumes(catalog, route['skill'], route.get('mode'))
        if consumes is None:
            continue
        missing, stale = [], []
        not_adopted = False
        for item in consumes:
            if item['artifact'] == REGISTER_ARTIFACT and not adopted:
                not_adopted = True
                continue
            paths = _matches(root, item, case_id)
            if not paths:
                missing.append(item['artifact'])
            elif _stale(root, item, paths, manifest):
                stale.append(item['artifact'])
        state = 'not_adopted' if not_adopted else 'blocked' if missing else 'stale' if stale else 'runnable'
        notes = ''
        if route['skill'] == 'interview-bridge':
            responders = _booked_responders(root, case_id)
            if responders:
                notes = 'smoke-test responders with bookings: ' + ', '.join(responders)
        rows.append({'route_id': route['id'], 'skill': route['skill'], 'state': state,
                     'missing': missing, 'stale': stale, 'notes': notes})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog='route_workflow.py status', description=__doc__)
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument('--project', default='')
    where.add_argument('--workspace', type=Path)
    ap.add_argument('--case', required=True)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    root = a.workspace or subprojects.business(ROOT / 'projects' / a.project)
    rows = case_status(root, a.case)
    if a.json:
        print(json.dumps(rows, indent=2))
        return 0
    for row in rows:
        detail = ', '.join(filter(None, [
            'missing: ' + ', '.join(row['missing']) if row['missing'] else '',
            'upstream changed: ' + ', '.join(row['stale']) if row['stale'] else '', row['notes']]))
        print(f"{row['state']:<12} {row['route_id']:<28} {row['skill']}" + (f'  ({detail})' if detail else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
