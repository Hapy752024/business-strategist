#!/usr/bin/env python3
"""Check installed skill/catalog parity and executable routing reachability."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.route_workflow import checked_references
except ModuleNotFoundError:
    from route_workflow import checked_references

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path = ROOT) -> list[str]:
    skills = {p.parent.name for p in (root / '.agents/skills').glob('*/SKILL.md')}
    catalog = json.loads((root / 'config/skill-catalog.json').read_text())['skills']
    routes = json.loads((root / 'config/workflow-routes.json').read_text())['routes']
    errors = []
    module_owners = {}
    full_catalog = json.loads((root / 'config/skill-catalog.json').read_text())
    for module_name, module in full_catalog.get('modules', {}).items():
        reference = module.get('reference')
        if not isinstance(reference, str) or not (root / reference).is_file() or not (root / reference).stat().st_size:
            errors.append(f'module {module_name}: missing or empty reference {reference!r}')
        quality_reference = module.get('quality_reference')
        if not isinstance(quality_reference, str) or not (root / quality_reference).is_file() or not (root / quality_reference).stat().st_size:
            errors.append(f'module {module_name}: missing or empty quality reference {quality_reference!r}')
        for skill in module.get('skills', []):
            if skill not in catalog:
                errors.append(f'module {module_name}: unknown skill {skill}')
            if skill in module_owners:
                errors.append(f'skill {skill}: assigned to multiple modules')
            module_owners[skill] = module_name
    specialist_owners = {}
    for owner, names in full_catalog.get('specialist_owners', {}).items():
        if not isinstance(names, list):
            errors.append(f'specialist owner {owner}: skills must be an array')
            continue
        for skill in names:
            if skill not in catalog:
                errors.append(f'specialist owner {owner}: unknown skill {skill}')
            if skill in specialist_owners:
                errors.append(f'skill {skill}: assigned to multiple specialist owners')
            specialist_owners[skill] = owner
            if skill in module_owners:
                errors.append(f'skill {skill}: assigned to both module and specialist owner')
    for skill in catalog:
        if (skill in module_owners) == (skill in specialist_owners):
            errors.append(f'skill {skill}: must have exactly one module or specialist owner')
    for name, metadata in catalog.items():
        try:
            checked_references(metadata, root)
        except (ValueError, OSError) as exc:
            errors.append(f'{name}: {exc}')
        for mode, contract in metadata.get('modes', {}).items():
            try:
                checked_references(contract, root)
                if not contract.get('inputs') or not contract.get('output_owner') or not contract.get('artifacts'):
                    raise ValueError('mode requires inputs, artifacts and output owner')
                if not any(r['skill'] == name and r.get('mode') == mode for r in routes):
                    raise ValueError('mode has no checked route')
            except (ValueError, OSError) as exc:
                errors.append(f'{name}/{mode}: {exc}')
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
