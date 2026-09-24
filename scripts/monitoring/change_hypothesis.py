#!/usr/bin/env python3
"""Validate a dated supplier change and produce a bounded customer-impact research brief."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from jsonschema import Draft202012Validator, FormatChecker

KINDS = {'pricing', 'packaging', 'feature', 'integration', 'deprecation', 'closure', 'hiring', 'app_store'}
SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'schemas/competitor-change-input.schema.json').read_text())


def _date(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('observation dates require an ISO-8601 timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('observation dates require an explicit timezone')
    return parsed


def _source(row, label):
    url = row.get('url', '')
    if urlparse(url).scheme not in {'http', 'https'} or not urlparse(url).hostname:
        raise ValueError(f'{label} needs an HTTP(S) source URL')
    snapshot = row.get('snapshot_text')
    if not isinstance(snapshot, str) or not isinstance(row.get('sha256'), str) or len(row['sha256']) != 64:
        raise ValueError(f'{label} needs captured snapshot text and its SHA-256')
    if hashlib.sha256(snapshot.encode('utf-8')).hexdigest() != row['sha256']:
        raise ValueError(f'{label} snapshot digest does not match captured text')


def build(payload):
    if not isinstance(payload, dict):
        raise ValueError('input must be a JSON object')
    schema_errors = list(Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(payload))
    if schema_errors:
        raise ValueError(schema_errors[0].message)
    if payload.get('schema_version') != 1 or payload.get('event_type') not in KINDS:
        raise ValueError('schema_version 1 and a supported event_type are required')
    before, after = payload.get('before'), payload.get('after')
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError('dated before and after observations are required')
    for label, row in (('before', before), ('after', after)):
        _date(row.get('observed_at', ''))
        _source(row, label)
        if not isinstance(row.get('value'), dict) or not row['value']:
            raise ValueError(f'{label}.value must contain comparable observed fields')
    if _date(before['observed_at']) >= _date(after['observed_at']):
        raise ValueError('after observation must be later than the dated baseline')
    changed = {key: {'before': before['value'].get(key), 'after': after['value'].get(key)}
               for key in sorted(set(before['value']) | set(after['value']))
               if before['value'].get(key) != after['value'].get(key)}
    if not changed:
        status = 'no_change'
    else:
        status = 'change_observed'
    if payload['event_type'] in {'pricing', 'packaging'} and changed:
        required = ('currency', 'billing_period', 'unit', 'region', 'customer_scope')
        for key in required:
            if before['value'].get(key) != after['value'].get(key) or key not in before['value']:
                raise ValueError(f'pricing comparison is not normalized for {key}')
    customer_evidence = payload.get('customer_evidence', [])
    if not isinstance(customer_evidence, list):
        raise ValueError('customer_evidence must be a list')
    for item in customer_evidence:
        if item.get('role') not in {'customer', 'former_customer', 'prospective_buyer', 'supplier', 'intermediary'}:
            raise ValueError('customer evidence role must be explicit')
        _source(item, 'customer evidence')
        if not item.get('observation'):
            raise ValueError('customer evidence needs an observation')
        if item.get('relation') not in {'supports', 'contrary', 'context_only'}:
            raise ValueError('customer evidence relation must be supports, contrary or context_only')
    direct_customer = [x for x in customer_evidence if x['role'] in {'customer', 'former_customer', 'prospective_buyer'}]
    supplier = [x for x in customer_evidence if x['role'] == 'supplier']
    supporting = [x for x in direct_customer if x.get('relation') == 'supports']
    contrary = [x for x in direct_customer if x.get('relation') == 'contrary']
    hypothesis = payload.get('customer_impact_hypothesis', '').strip()
    segment = payload.get('customer_segment', '').strip()
    workflow = payload.get('workflow', '').strip()
    if status == 'change_observed' and (not hypothesis or not segment or not workflow):
        raise ValueError('an observed change needs a scoped customer segment, workflow and testable impact hypothesis')
    return {'schema_version': 1, 'event_type': payload['event_type'], 'status': status,
        'company': payload.get('company', ''), 'before': before, 'after': after, 'changed_fields': changed,
        'customer_segment': segment, 'workflow': workflow,
        'customer_impact_hypothesis': hypothesis,
        'customer_evidence': customer_evidence,
        'evidence_status': 'corroborated_in_bounded_accounts' if supporting else 'not_yet_corroborated',
        'supporting_customer_evidence': supporting, 'contrary_customer_evidence': contrary,
        'supplier_assertions': supplier,
        'next_check': payload.get('next_check') or ('Find affected and unaffected customers; ask about the last concrete episode, response and alternative.' if status == 'change_observed' and not supporting else 'Check whether the change persists and whether comparable customers experienced the predicted effect.'),
        'limits': ['Supplier change signals do not establish customer exposure, dissatisfaction, switching or demand.',
                   'Hiring indicates supplier intent only. A closure does not establish installed base or reachable migration demand.',
                   'App-store estimates are modeled store metrics, not company revenue, profit or retention.']}


def render(event):
    lines = ['# Change and customer-impact research brief', '', f"Status: `{event['status']}`", f"Event: `{event['event_type']}`", '']
    if event['status'] == 'no_change':
        lines += ['The supplied dated observations have no comparable field difference. Do not report a competitor event.', '']
        return '\n'.join(lines)
    lines += ['## Observed change', '']
    for field, pair in event['changed_fields'].items():
        lines.append(f"- `{field}`: `{pair['before']}` → `{pair['after']}`")
    lines += ['', 'Before: ' + event['before']['url'] + ' (' + event['before']['observed_at'] + ')',
              'After: ' + event['after']['url'] + ' (' + event['after']['observed_at'] + ')', '',
              '## Customer hypothesis', '', f"For **{event['customer_segment']}**, the change may affect **{event['workflow']}** because: {event['customer_impact_hypothesis']}", '',
              'Evidence status: ' + event['evidence_status'], '', 'Supporting customer accounts: ' + str(len(event['supporting_customer_evidence'])),
              'Contrary customer accounts: ' + str(len(event['contrary_customer_evidence'])),
              'Supplier assertions kept separate: ' + str(len(event['supplier_assertions'])), '',
              '## Next check', '', event['next_check'], '', '## Limits', '']
    lines.extend('- ' + item for item in event['limits'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding='utf-8'))
        event = build(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in {'change-event.json': json.dumps(event, ensure_ascii=False, indent=2) + '\n',
                          'customer-impact-brief.md': render(event)}.items():
        target = args.out_dir / name
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
