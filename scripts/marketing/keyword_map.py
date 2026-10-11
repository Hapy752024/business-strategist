"""Validate the intent/page map and capture bindings; legacy maps need reviewed conversion."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.link_observations import ROOT, bound_bytes, url_key

SCHEMA = json.loads((ROOT / 'schemas/keyword-map.schema.json').read_text())
RESOURCE = json.loads((ROOT / 'schemas/content-brief.schema.json').read_text())['properties']['public_resource']


def validate(document: dict, base: Path | None = None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(document)]
    if errors:
        return errors
    ids, assignments = set(), {}
    for row in document['rows']:
        if row['id'] in ids:
            errors.append('duplicate page-map row ID: ' + row['id'])
        ids.add(row['id'])
        identity = (row['locale'], row['primary_term'].casefold().strip())
        if identity in assignments and assignments[identity] != row['target_url'] and not row.get('assignment_exception', '').strip():
            errors.append('conflicting primary assignment needs reviewed exception: ' + row['id'])
        assignments[identity] = row['target_url']
        for value in [row['target_url'], *row.get('internal_links', []),
                      *[row[k] for k in ('existing_url', 'redirect_to') if row.get(k)]]:
            try:
                url_key(value)
            except ValueError:
                errors.append('invalid page-map URL: ' + row['id'])
        if row['decision'] != 'create' and not row['existing_url']:
            errors.append('existing-page decision needs existing_url: ' + row['id'])
        if row['decision'] == 'create' and row['existing_url']:
            errors.append('existing page requires retain/improve/consolidate decision: ' + row['id'])
        if row['decision'] in {'consolidate', 'retire'} and 'redirect_to' not in row:
            errors.append('consolidate/retire requires intentional redirect_to (null allowed): ' + row['id'])
        if row.get('volume') is not None and not (row.get('volume_provider') and row.get('volume_checked_at')):
            errors.append('volume estimate requires provider and date: ' + row['id'])
        for binding in row['evidence_refs']:
            try:
                bound_bytes(binding, base, staged)
            except (ValueError, OSError) as exc:
                errors.append(row['id'] + ': ' + str(exc))
    return errors


def validate_resource(resource: dict, base: Path | None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(RESOURCE).iter_errors(resource)]
    if errors:
        return errors
    try:
        url_key(resource['destination_url'])
        for binding in resource['source_bindings']:
            bound_bytes(binding, base, staged)
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    return errors


def render(document: dict) -> str:
    rows = ['# Page decisions', '', '| Page | Locale | Intent | Decision | Conversion path |', '| --- | --- | --- | --- | --- |']
    rows += [f"| {r['target_url']} | {r['locale']} | {r['intent']} | {r['decision']} | {r['conversion_bridge']} |" for r in document['rows']]
    return '\n'.join(rows) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('map', type=Path); ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    doc = json.loads(args.map.read_text())
    errors = validate(doc, args.base)
    if args.out and not errors:
        args.out.write_text(render(doc))
    print(json.dumps({'valid': not errors, 'errors': errors}))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
