"""Review candidate evidence and prepare proposed actions; never sends or submits."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing import link_observations as links
from scripts.marketing.public_fetch import fetch

SCHEMA = json.loads((links.ROOT / 'schemas/earned-media-opportunity.schema.json').read_text())
CATALOGUE = 'https://submitmystartup.com/api/v1/directories.json'


def validate(records: dict | list, base: Path | None, staged: dict | None = None) -> list[str]:
    records = records if isinstance(records, list) else [records]
    errors, ids, pairs = [], set(), set()
    for row in records:
        issues = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(row)]
        if issues:
            errors.extend(issues)
            continue
        if row['id'] in ids:
            errors.append('duplicate opportunity ID')
        ids.add(row['id'])
        try:
            pair = (links.url_key(row['source_url']), links.url_key(row['destination_url']))
            if pair in pairs:
                errors.append('duplicate source/destination opportunity')
            pairs.add(pair)
            captures = [links.bound_bytes(b, base, staged).decode('utf-8', errors='replace') for b in row['provenance']]
            if row['source_passage'] not in '\n'.join(captures):
                errors.append('source passage is missing from retained provenance')
            if row['qualification'] == 'qualified':
                if urlsplit(row['source_url']).hostname != row['official_domain']:
                    errors.append('qualified opportunity source is not the verified official domain')
                if not all(row.get(k) for k in ('eligibility', 'contact_route', 'fee', 'renewal_terms')):
                    errors.append('qualified opportunity requires current eligibility, contact route and fee/renewal terms')
                if row['reciprocal_requirement'] not in {'none', 'not required'}:
                    errors.append('reciprocal/unknown requirement requires further review')
        except (ValueError, OSError, KeyError) as exc:
            errors.append(str(exc))
    return errors


def prepare(row: dict, *, base: Path, material: str) -> dict:
    errors = validate(row, base)
    if errors or row.get('qualification') != 'qualified':
        raise ValueError('; '.join(errors) or 'opportunity has not been qualified')
    raw = links.resolve_bytes(base, material)
    if not raw.strip():
        raise ValueError('prepared material is empty')
    kind = 'send_pitch' if row['route_class'] in {'editorial', 'paid_partnership'} else 'submit_listing'
    action = {'id': row['id'], 'objective': 'Prepare relevant ' + row['route_class'] + ' action',
        'actor': 'owner', 'action_kind': kind, 'intended_result': 'Submit exact reviewed packet for consideration',
        'dependencies': [], 'prepared_materials': [{'path': material, 'sha256': links.sha(raw)}],
        'next_step': 'Review packet and provide task-specific authorization',
        'completion_criterion': 'Authorized exact submission/send has a delivery receipt; placement is separate',
        'commitment_state': 'proposed', 'execution_status': 'prepared', 'required_for_scope': False,
        'destination': row['contact_route'], 'recipient': row['contact_route'],
        'eligibility_checked_at': row['checked_at'], 'audience_fit': row['audience_fit'],
        'user_step': 'Review the prepared material and submit via the recorded contact route',
        'fee': row['fee'], 'authorization_basis': 'proposed; no external-action authorization recorded',
        'follow_up': 'Record reply/rejection and separately inspect any resulting public placement'}
    return {'schema_version': 2, 'scope': 'Prepare ' + row['id'], 'revision': 1, 'actions': [action]}


def import_links(path: Path, *, source_column: str, target_column: str, property_url: str, exported_at: str) -> dict:
    """Explicit source-page export only; domain-only tables are not live links."""
    property_url = links.url_key(property_url)
    datetime.strptime(exported_at, '%Y-%m-%d')
    rows = list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()))
    candidates = []
    for row in rows:
        source, target = row.get(source_column), row.get(target_column)
        if not source or not target:
            raise ValueError('Links export requires explicit source-page and target URL columns')
        candidates.append({'source_url': links.url_key(source), 'target_url': links.url_key(target), 'qualification': 'candidate'})
    return {'schema_version': 1, 'property': property_url, 'exported_at': exported_at,
            'input_sha256': links.sha(path.read_bytes()), 'candidates': candidates,
            'limits': 'Sampled export may include historical links; no live placement verification.'}


def catalogue_candidates(payload: dict | list) -> list[dict]:
    rows = payload if isinstance(payload, list) else payload.get('directories', payload.get('data', []))
    if not isinstance(rows, list):
        raise ValueError('catalogue response has no directory array')
    result, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = row.get('url') or row.get('website') or row.get('websiteUrl')
        try:
            url = links.url_key(url or '')
        except ValueError:
            continue
        if url in seen:
            continue
        seen.add(url)
        result.append({'source_url': url, 'catalogue_id': row.get('id'), 'qualification': 'candidate',
                       'fee': None, 'link_inclusion': 'unknown', 'destination_verification': 'pending'})
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    check = sub.add_parser('validate'); check.add_argument('input', type=Path); check.add_argument('--base', required=True, type=Path)
    prep = sub.add_parser('prepare'); prep.add_argument('input', type=Path); prep.add_argument('--base', required=True, type=Path)
    prep.add_argument('--material', required=True); prep.add_argument('--out', required=True, type=Path)
    cat = sub.add_parser('catalogue'); cat.add_argument('--out', required=True, type=Path)
    cat.add_argument('--input', type=Path, help='retained catalogue JSON instead of a live fetch')
    imp = sub.add_parser('import-links'); imp.add_argument('input', type=Path)
    for flag in ('source-column', 'target-column', 'property', 'exported-at'):
        imp.add_argument('--' + flag, required=True)
    imp.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    try:
        if args.command == 'validate':
            errors = validate(json.loads(args.input.read_text()), args.base)
            print(json.dumps({'valid': not errors, 'errors': errors})); return int(bool(errors))
        if args.command == 'prepare':
            doc = prepare(json.loads(args.input.read_text()), base=args.base, material=args.material)
            args.out.write_text(json.dumps(doc, indent=2) + '\n')
        elif args.command == 'import-links':
            doc = import_links(args.input, source_column=args.source_column, target_column=args.target_column,
                               property_url=args.property, exported_at=args.exported_at)
            args.out.write_text(json.dumps(doc, indent=2) + '\n')
        else:
            if args.input:
                raw = args.input.read_bytes()
            else:
                result = fetch(CATALOGUE)
                if result['status'] != 200:
                    raise ValueError('catalogue unavailable')
                raw = result['raw']
            rows = catalogue_candidates(json.loads(raw))
            args.out.mkdir(parents=True, exist_ok=False)
            (args.out/'raw.json').write_bytes(raw)
            doc = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'source_url': CATALOGUE,
                   'raw_sha256': links.sha(raw), 'candidates': rows, 'limits': 'Catalogue claims require destination review.'}
            (args.out/'candidates.json').write_text(json.dumps(doc, indent=2) + '\n')
        print(json.dumps({'status': 'prepared', 'out': str(args.out)})); return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status': 'unavailable', 'reason': str(exc)})); return 1


if __name__ == '__main__':
    raise SystemExit(main())
