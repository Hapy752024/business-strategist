#!/usr/bin/env python3
"""Check declared source numbers against digest-bound, structured local observations."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

try:
    from scripts import case_workspace as cases
except ModuleNotFoundError:
    import case_workspace as cases

TOKEN = re.compile(r'\{\{source_numeric\.([a-z][a-z0-9_-]*)\}\}')
ID = re.compile(r'^[a-z][a-z0-9_-]*$')
METRIC = re.compile(r'^[a-z][a-z0-9_]*$')
CURRENCY = re.compile(r'^[A-Z]{3}$')
NUMBER = re.compile(r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$')
CONTEXT = ('metric', 'period', 'currency', 'unit', 'scope')
DOCUMENTS = {'README.md', 'case_insights.md', 'feasibility.md', 'business-case.md',
             'comparison.summary', 'comparison.principal_uncertainty', 'comparison.next_action'}
BASE_FIELDS = {'id', 'document', 'status', 'value', *CONTEXT}


def decimal(value, label):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError(f'{label}: value must be a decimal string or integer')
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f'{label}: invalid decimal value') from exc
    if not number.is_finite():
        raise ValueError(f'{label}: value must be finite')
    return number


def pointer(document, locator):
    if not isinstance(locator, str) or not locator.startswith('/'):
        raise ValueError('source locator must be an absolute JSON Pointer')
    node = document
    for raw in locator[1:].split('/'):
        if re.search(r'~(?![01])', raw):
            raise ValueError('malformed JSON Pointer escape')
        key = raw.replace('~1', '/').replace('~0', '~')
        if isinstance(node, dict):
            if key not in node:
                raise ValueError('source locator does not resolve')
            node = node[key]
        elif isinstance(node, list):
            if not re.fullmatch(r'0|[1-9][0-9]*', key) or int(key) >= len(node):
                raise ValueError('source locator does not resolve')
            node = node[int(key)]
        else:
            raise ValueError('source locator does not resolve')
    return node


def checked_claims(root: Path, texts: dict[str, str], claims: list, bindings: list) -> tuple[dict[str, str], dict]:
    """Return rendered text and an auditable receipt; raise before publication on any mismatch."""
    if not isinstance(claims, list) or not isinstance(bindings, list):
        raise ValueError('numeric_claims and source_bindings must be lists')
    if set(texts) - DOCUMENTS or any(not isinstance(value, str) for value in texts.values()):
        raise ValueError('numeric claim documents must be current appraisal text')
    rendered = dict(texts)
    seen = set()
    checked = []
    for row in claims:
        if not isinstance(row, dict) or not BASE_FIELDS <= row.keys():
            raise ValueError('numeric claim needs id, document, status, value and full context')
        label = row['id']
        if not isinstance(label, str) or not ID.fullmatch(label) or label in seen:
            raise ValueError('numeric claim IDs must be unique lowercase identifiers')
        seen.add(label)
        if not isinstance(row['document'], str) or row['document'] not in DOCUMENTS or row['document'] not in texts:
            raise ValueError(f'{label}: declared document is not supplied')
        if not isinstance(row['value'], str) or not NUMBER.fullmatch(row['value']):
            raise ValueError(f'{label}: authored claim value must be a canonical decimal string')
        claim_value = decimal(row['value'], label)
        if not isinstance(row['metric'], str) or not METRIC.fullmatch(row['metric']):
            raise ValueError(f'{label}: metric must be a canonical snake-case ID')
        for field in ('period', 'unit', 'scope'):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f'{label}: {field} must be nonempty')
        if row['currency'] is not None and (not isinstance(row['currency'], str) or not CURRENCY.fullmatch(row['currency'])):
            raise ValueError(f'{label}: currency must be ISO uppercase or null')
        token = '{{source_numeric.' + label + '}}'
        occurrences = [(name, text.count(token)) for name, text in texts.items() if token in text]
        if occurrences != [(row['document'], 1)]:
            raise ValueError(f'{label}: marker must occur exactly once in its declared document')
        if row['status'] == 'unverified':
            if set(row) != BASE_FIELDS | {'reason'} or not isinstance(row['reason'], str) or not row['reason'].strip():
                raise ValueError(f'{label}: unverified claim needs a reason and no source binding')
            replacement = f'[unverified numeric value: {label}]'
            checked.append({**row, 'check_status': 'unverified'})
        elif row['status'] == 'verified':
            if set(row) != BASE_FIELDS | {'source_binding'}:
                raise ValueError(f'{label}: verified claim needs exactly one source binding')
            binding = row['source_binding']
            if not isinstance(binding, dict) or binding not in bindings:
                raise ValueError(f'{label}: source binding is missing from this publication')
            try:
                current = cases.source_binding(root, binding['path'], locator=binding['locator'], applicability=binding['applicability'])
            except (KeyError, AttributeError, TypeError) as exc:
                raise ValueError(f'{label}: invalid source binding') from exc
            if current != binding:
                raise ValueError(f'{label}: stale source binding')
            source = cases.safe(root, binding['path'])
            if source.suffix.lower() != '.json':
                raise ValueError(f'{label}: verified source must be structured JSON')
            try:
                observation = pointer(json.loads(source.read_text(encoding='utf-8'), parse_float=Decimal), binding['locator'])
            except (json.JSONDecodeError, UnicodeError) as exc:
                raise ValueError(f'{label}: source is not valid JSON') from exc
            if not isinstance(observation, dict) or not {*CONTEXT, 'value'} <= observation.keys():
                raise ValueError(f'{label}: source locator must name a structured numeric observation')
            if decimal(observation['value'], label) != claim_value:
                raise ValueError(f'{label}: numeric value or sign differs from source')
            for field in CONTEXT:
                if observation[field] != row[field]:
                    raise ValueError(f'{label}: {field} differs from source')
            replacement = row['value']
            checked.append({**row, 'check_status': 'verified', 'source_sha256': binding['digest']})
        else:
            raise ValueError(f'{label}: status must be verified or unverified')
        rendered[row['document']] = rendered[row['document']].replace(token, replacement)
    for name, text in texts.items():
        for match in TOKEN.finditer(text):
            if match[1] not in seen:
                raise ValueError(f'{name}: undeclared numeric marker {match[1]}')
        if '{{source_numeric.' in rendered[name]:
            raise ValueError(f'{name}: malformed numeric marker')
    return rendered, {'schema_version': '1.0', 'claims': checked,
                      'verified_count': sum(c['check_status'] == 'verified' for c in checked),
                      'unverified_count': sum(c['check_status'] == 'unverified' for c in checked)}


def render_markers(text: str, report: dict) -> str:
    for claim in report['claims']:
        marker = '{{source_numeric.' + claim['id'] + '}}'
        replacement = (claim['value'] if claim['check_status'] == 'verified'
                       else f"[unverified numeric value: {claim['id']}]")
        text = text.replace(marker, replacement)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--packet', type=Path, required=True)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding='utf-8'))
        texts = {**packet.get('documents', {}), **{'comparison.' + name: value for name, value in packet.get('comparison', {}).items()}}
        _, report = checked_claims(args.workspace.absolute(), texts, packet.get('numeric_claims', []), packet.get('source_bindings', []))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'fail', 'error': str(exc)}))
        return 2
    print(json.dumps({'status': 'pass', **report}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
