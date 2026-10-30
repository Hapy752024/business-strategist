#!/usr/bin/env python3
"""Turn agent-authored interview coding into evidence records after verifying every quote verbatim.

No model is called here: the agent codes the transcript under interview-bridge instructions;
this script only checks that each quote appears in the transcript (whitespace-normalised)
and emits records conforming to schemas/evidence-record.schema.json. Quotes are
observations; themes and interpretations are carried as labelled interpretation.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / 'schemas/evidence-record.schema.json').read_text())
ITEM_FIELDS = {'theme', 'interpretation', 'verbatim_quote', 'speaker', 'locator'}
OPTIONAL = {'evidence_type', 'author_voice_status', 'strength', 'statement_type'}


def _norm(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def ingest(coding: dict, transcripts: dict[str, str]) -> list[dict]:
    tid = coding.get('transcript_id')
    if tid not in transcripts:
        raise ValueError(f'unknown transcript {tid}')
    haystack = _norm(transcripts[tid])
    records = []
    stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    for index, item in enumerate(coding.get('items', []), start=1):
        if not isinstance(item, dict) or not ITEM_FIELDS <= set(item) or set(item) - ITEM_FIELDS - OPTIONAL:
            raise ValueError(f'coding item {index} needs ' + ', '.join(sorted(ITEM_FIELDS)))
        quote = _norm(item['verbatim_quote'])
        if not quote or quote not in haystack:
            raise ValueError('quote not found: ' + quote[:40])
        record = {'evidence_id': f'{tid}-q{index}', 'source': 'interview_transcript', 'retrieved_at': stamp,
                  'evidence_type': item.get('evidence_type', 'pain'), 'text': quote, 'verbatim_quote': quote,
                  'strength': item.get('strength', 'medium'), 'statement_type': item.get('statement_type', 'unclassified'), 'sampling_frame': 'topic_led_voc',
                  'author_voice_status': item.get('author_voice_status', 'unresolved'),
                  'author_context': f"speaker {item['speaker']}", 'collection_locator': f"{tid}#{item['locator']}",
                  'confidence_notes': 'Interpretation: ' + item['interpretation'].strip() + ' Theme: ' + item['theme'].strip()}
        errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(record)]
        if errors:
            field = 'evidence_type' if any("'" + record['evidence_type'] + "'" in e for e in errors) else 'record'
            raise ValueError(f'coding item {index} {field} invalid: ' + '; '.join(errors))
        records.append(record)
    return records


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--coding', required=True, type=Path)
    ap.add_argument('--transcript', action='append', required=True, help='<id>=<path>; repeatable')
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args(argv)
    transcripts = {}
    for spec in a.transcript:
        ident, _, path = spec.partition('=')
        transcripts[ident] = Path(path).read_text(encoding='utf-8')
    records = ingest(json.loads(a.coding.read_text()), transcripts)
    if a.out.exists():
        raise SystemExit('choose a fresh output file')
    a.out.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    print(a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
