"""Validate source-linked questions and content use; render private extracts as withheld."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.link_observations import ROOT, bound_bytes
from scripts.evidence_scout.reviewed_voice import review_voice

SCHEMA = json.loads((ROOT / 'schemas/customer-questions.schema.json').read_text())


def validate(document: dict, base: Path | None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(document)]
    if errors:
        return errors
    ids = set()
    for row in document['questions']:
        ident = row['id']
        if ident in ids:
            errors.append('duplicate question ID: ' + ident)
        ids.add(ident)
        try:
            if row['visibility'] == 'private' and (not row.get('access_context', '').strip() or row.get('sanitized_extract') is not True):
                errors.append(ident + ': private material requires access context and a sanitized supplied extract')
            if row['kind'] == 'hypothesis':
                if row.get('review') or row.get('source') or row.get('outcome'):
                    errors.append(ident + ': hypothesis cannot claim source review or observed answer outcome')
                continue
            record = json.loads(bound_bytes(row['source'], base, staged))
            if not isinstance(record, dict) or not isinstance(record.get('text'), str):
                raise ValueError('source requires a captured text record')
            if row['passage'] not in record['text']:
                errors.append(ident + ': question passage is absent from source')
            if row['source_date'] != record.get('published_at'):
                errors.append(ident + ': source date differs from capture (null means unknown)')
            if row['kind'] == 'customer':
                review = json.loads(bound_bytes(row['review'], base, staged))
                if review.get('status') != 'accepted' or review.get('evidence_id') != record.get('evidence_id') or not record.get('evidence_id'):
                    errors.append(ident + ': customer question requires an accepted matching source review')
                if review.get('voice') not in {'customer', 'former_customer', 'prospective_user', 'nonadopter'} or review.get('firsthand') is not True:
                    errors.append(ident + ': customer question requires reviewed firsthand customer voice')
                if review.get('segment_relation') != row['segment_relation']:
                    errors.append(ident + ': segment applicability differs from source review')
                errors += [ident + ': ' + e for e in review_voice(record, review, row['segment'])]
            if row.get('outcome'):
                outcome = json.loads(bound_bytes(row['outcome'], base, staged))
                answer = row['current_answer']
                if not answer or outcome.get('question_id') != ident or outcome.get('answer_sha256') != hashlib.sha256(answer.encode()).hexdigest():
                    errors.append(ident + ': answer outcome does not bind this question/current answer')
                if outcome.get('outcome') not in {'helped', 'did_not_help', 'inconclusive'} or not str(outcome.get('limits', '')).strip():
                    errors.append(ident + ': outcome requires observed result and limitations')
                if datetime.fromisoformat(outcome['observed_at'].replace('Z', '+00:00')).utcoffset() is None:
                    errors.append(ident + ': outcome observation needs timezone')
        except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
            errors.append(ident + ': ' + str(exc))
    return errors


def validate_brief(brief: dict, base: Path | None, staged: dict | None = None) -> list[str]:
    if 'customer_questions' not in brief:
        return []
    contract = json.loads((ROOT / 'schemas/content-brief.schema.json').read_text())['properties']['customer_questions']
    errors = [e.message for e in Draft202012Validator(contract).iter_errors(brief['customer_questions'])]
    if errors:
        return errors
    binding = brief['customer_questions']
    try:
        document = json.loads(bound_bytes(binding['artifact'], base, staged))
        errors += validate(document, base, staged)
        if errors:
            return errors
        rows = {r['id']: r for r in document['questions']}
        for ident in binding['question_ids']:
            row = rows.get(ident)
            if not row or row['kind'] != 'customer' or row['segment_relation'] != 'target':
                errors.append('brief requires a reviewed target-customer question: ' + ident)
            elif brief.get('audience_segment') != row['segment']:
                errors.append('brief audience differs from reviewed question segment: ' + ident)
            elif brief.get('brief_id') not in row['linked_brief_ids']:
                errors.append('question does not name this content brief: ' + ident)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    return errors


def render(document: dict) -> str:
    def cell(value):
        return html.escape(str(value or 'unknown')).replace('\\', '&#92;').replace('|', '&#124;').replace('`', '&#96;').replace('\n', ' ')
    lines = ['# Customer questions', '', '| ID | Kind / applicability | Question | Current answer | Outcome |', '| --- | --- | --- | --- | --- |']
    for row in document['questions']:
        private = row['visibility'] == 'private'
        lines.append('| ' + ' | '.join(map(cell, [row['id'], row['kind'] + ' / ' + row['segment_relation'],
            '[private extract withheld]' if private else row['passage'],
            '[private answer withheld]' if private else row['current_answer'],
            'bound observation; inspect authorized source' if row.get('outcome') else 'unknown'])) + ' |')
    lines += ['', 'Questions are source-linked inputs, not prevalence, demand or answer-effectiveness proof.', '']
    return '\n'.join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('document', type=Path); ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    try:
        document = json.loads(args.document.read_text())
        errors = validate(document, args.base)
        if args.out and not errors:
            args.out.write_text(render(document))
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    print(json.dumps({'valid': not errors, 'errors': errors}))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
