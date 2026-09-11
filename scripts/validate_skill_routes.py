#!/usr/bin/env python3
"""Check installed skill/catalog parity and executable routing reachability."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path = ROOT) -> list[str]:
    skills = {p.parent.name for p in (root / '.agents/skills').glob('*/SKILL.md')}
    catalog = json.loads((root / 'config/skill-catalog.json').read_text())['skills']
    routes = json.loads((root / 'config/workflow-routes.json').read_text())['routes']
    errors = []
    for name in sorted(skills - catalog.keys()):
        errors.append(f'Installed skill missing from catalog: {name}')
    for name in sorted(catalog.keys() - skills):
        errors.append(f'Catalog skill missing from disk: {name}')
    seen = set()
    reached = {'business-strategist'}  # Router's explicit clarification fallback.
    for route in routes:
        route_id = route['id']
        if route_id in seen:
            errors.append(f'Duplicate route ID: {route_id}')
        seen.add(route_id)
        name = route['skill']
        reached.add(name)
        if name not in catalog or name not in skills:
            errors.append(f'Route {route_id} targets unknown skill: {name}')
        for forbidden in route.get('forbidden', []):
            if forbidden not in catalog:
                errors.append(f'Route {route_id} forbids unknown skill: {forbidden}')
        if name in route.get('forbidden', []):
            errors.append(f'Route {route_id} forbids its own skill')
    for name in sorted(skills - reached):
        errors.append(f'Orphan skill has no explicit route: {name}')
    return errors


def main() -> int:
    errors = validate()
    print(json.dumps({'passed': not errors, 'errors': errors}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
