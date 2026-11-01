#!/usr/bin/env python3
"""Frozen routing decisions for a differential corpus; any change to routing shows up as a changed row.

Corpus: every prompt in config/routing-evals.json, each route's first match phrase alone, and every ordered pair of
routes with match phrases as "<phrase A>, then <phrase B>". Each request is routed in-process in three contexts:

- ``no-project``: no project (standalone defaults).
- ``gate-not-passed``: a versioned project with a selected case whose problem_validation has not passed, routed with
  ``entry_mode=business_linked`` (what a Skill envelope with a project and ``standalone: false`` sends), so design and
  website routes meet their business-linked gates too.
- ``gate-not-passed-case``: the same project with its registered case ``a`` named, so case routes (insights,
  appraisal, case plan) reach their own gates instead of refusing for a missing case.

Decision per request: the route ID, ``clarify``, ``gate:<gate name>`` when blocked, or ``error:<message>`` when the router
refuses the request. ``--update`` rewrites tests/routing_expected.json; without it the script exits 1 and prints every
changed row. ``--steals`` prints pair rows that resolve to a route that is neither A nor B (nor clarify).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

try:
    from scripts import case_workspace as cases, route_workflow
except ModuleNotFoundError:  # Direct CLI execution from scripts/.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import case_workspace as cases, route_workflow

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATH = ROOT / 'tests' / 'routing_expected.json'
PROJECT = 'gate-not-passed'
CONTEXTS = {'no-project': {}, 'gate-not-passed': {'project': PROJECT, 'entry_mode': 'business_linked'},
            'gate-not-passed-case': {'project': PROJECT, 'case_id': 'a', 'entry_mode': 'business_linked'}}


def corpus() -> list[tuple[str, tuple[str, str] | None]]:
    """(request, (route A, route B) for pair rows else None), in a stable order without duplicates."""
    evals = json.loads((ROOT / 'config' / 'routing-evals.json').read_text(encoding='utf-8'))
    rows: dict[str, tuple[str, str] | None] = {}
    for pair in evals['pairs']:
        for case in pair['evals']:
            rows.setdefault(case['prompt'], None)
    phrased = [(route['id'], route['match'][0]) for route in route_workflow.load_routes() if route.get('match')]
    for _, phrase in phrased:
        rows.setdefault(phrase, None)
    for a, phrase_a in phrased:
        for b, phrase_b in phrased:
            if a != b:
                rows.setdefault(f'{phrase_a}, then {phrase_b}', (a, b))
    return list(rows.items())


def _decision(packet: dict) -> str:
    if packet['route_id'] == 'clarify':
        return 'clarify'
    if packet.get('gate_blocked'):
        return f"gate:{packet['gate']}"
    return packet['route_id']


def _gate_not_passed_project(root: Path) -> None:
    """A versioned project with a selected case and no passed problem_validation stage."""
    project = root / 'projects' / PROJECT
    cases.initialize(project, PROJECT)
    cases.add_case(project, 'a', 'A')
    cases.select(project, 'a', 'Fixture configuration', 'select-fixture', 'Explicit fixture selection')


def decisions() -> tuple[dict[str, dict[str, str]], list[tuple[str, str, str, str]]]:
    """Return ({context: {request: decision}}, suspected steals [(request, A, B, routed)])."""
    rows = corpus()
    result: dict[str, dict[str, str]] = {name: {} for name in CONTEXTS}
    steals = []
    original_root = route_workflow.ROOT
    with tempfile.TemporaryDirectory() as tmp:
        _gate_not_passed_project(Path(tmp))
        route_workflow.ROOT = Path(tmp)
        try:
            for name, kwargs in CONTEXTS.items():
                for request, pair in rows:
                    try:
                        packet = route_workflow._locked_route_request(request, **kwargs)
                    except ValueError as exc:
                        result[name][request] = 'error:' + str(exc).replace(tmp, '<tmp>')[:120]
                        continue
                    result[name][request] = _decision(packet)
                    if name == 'no-project' and pair and packet['route_id'] not in {*pair, 'clarify'}:
                        steals.append((request, *pair, packet['route_id']))
        finally:
            route_workflow.ROOT = original_root
    return result, steals


def changed_rows(expected: dict, actual: dict) -> list[str]:
    lines = []
    for context in sorted(set(expected) | set(actual)):
        before, after = expected.get(context, {}), actual.get(context, {})
        for request in [*before, *(r for r in after if r not in before)]:
            if before.get(request) != after.get(request):
                lines.append(f'[{context}] {request!r}: {before.get(request)} -> {after.get(request)}')
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--update', action='store_true', help='Rewrite the frozen decisions file.')
    parser.add_argument('--steals', action='store_true', help='Print pair rows routed to neither of their routes.')
    parser.add_argument('--expected', type=Path, default=EXPECTED_PATH)
    args = parser.parse_args(argv)
    actual, steals = decisions()
    if args.steals:
        for request, a, b, routed in steals:
            print(f'{routed}\t{a} + {b}\t{request}')
    if args.update:
        args.expected.write_text(json.dumps(actual, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'wrote {sum(map(len, actual.values()))} decisions to {args.expected}')
        return 0
    changes = changed_rows(json.loads(args.expected.read_text(encoding='utf-8')), actual)
    print('\n'.join(changes) if changes else 'routing decisions unchanged')
    return 1 if changes else 0


if __name__ == '__main__':
    raise SystemExit(main())
