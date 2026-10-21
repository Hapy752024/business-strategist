"""Interview transcript coding: verbatim quotes become schema-valid evidence; themes stay interpretation."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.evidence_scout import ingest_transcript_coding as ing

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/evidence-record.schema.json').read_text())
TRANSCRIPT = 'Interviewer: How do you do month end?\nP1: Honestly it takes me   a full day, and I hate it.\nP1: I tried two apps and went back to Excel.\n'


def coding(quote='it takes me a full day, and I hate it', **extra):
    item = {'theme': 'month-end burden', 'interpretation': 'Month end is a recurring time cost.',
            'verbatim_quote': quote, 'speaker': 'P1', 'locator': 'line 2', 'evidence_type': 'pain'}
    item.update(extra)
    return {'transcript_id': 'int-01', 'items': [item]}


def test_ingest_rejects_missing_quote():
    with pytest.raises(ValueError, match='quote not found: it takes me two days'):
        ing.ingest(coding('it takes me two days'), {'int-01': TRANSCRIPT})


def test_ingest_rejects_unknown_transcript():
    with pytest.raises(ValueError, match='unknown transcript int-01'):
        ing.ingest(coding(), {})


def test_ingest_emits_schema_valid_records():
    records = ing.ingest(coding(), {'int-01': TRANSCRIPT})
    assert len(records) == 1
    rec = records[0]
    assert not list(Draft202012Validator(SCHEMA).iter_errors(rec))
    assert rec['source'] == 'interview_transcript' and rec['verbatim_quote'] == 'it takes me a full day, and I hate it'
    assert rec['confidence_notes'].startswith('Interpretation: ') and rec['author_voice_status'] == 'unresolved'
    assert rec['evidence_id'] == 'int-01-q1' and rec['collection_locator'] == 'int-01#line 2'


def test_ingest_rejects_invalid_evidence_type():
    with pytest.raises(ValueError, match='evidence_type'):
        ing.ingest(coding(evidence_type='delight'), {'int-01': TRANSCRIPT})


def test_ingest_cli_writes_jsonl(tmp_path):
    (tmp_path / 't.txt').write_text(TRANSCRIPT)
    (tmp_path / 'c.json').write_text(json.dumps(coding(author_voice_status='firsthand_customer')))
    out = tmp_path / 'evidence.jsonl'
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/ingest_transcript_coding.py'), '--coding',
                           str(tmp_path / 'c.json'), '--transcript', f"int-01={tmp_path / 't.txt'}", '--out', str(out)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert rows[0]['author_voice_status'] == 'firsthand_customer'
