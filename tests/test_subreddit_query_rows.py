"""Discovered subreddits become schema-valid Reddit query-plan rows for the existing collector."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.evidence_scout import subreddit_query_rows as sq

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/pain-query-plan.schema.json').read_text())


def test_rows_combine_keywords_and_subreddits():
    rows = sq.build_rows(['Finanzen', 'r/Versicherung'], ['PKV Wechsel', 'BU Ablehnung'], 'DE:de', 'pain')
    assert [r['query'] for r in rows] == ['PKV Wechsel subreddit:Finanzen', 'BU Ablehnung subreddit:Finanzen',
                                          'PKV Wechsel subreddit:Versicherung', 'BU Ablehnung subreddit:Versicherung']
    assert all(r['provider'] == 'reddit' and r['seed_origin'] == 'source_derived' for r in rows)
    assert rows[0]['seed_locators'] == ['dialog:discover_subreddits:Finanzen']
    plan = {'schema_version': 1, 'revision': 'dialog-1', 'queries': rows}
    assert not list(Draft202012Validator(SCHEMA).iter_errors(plan))


def test_rejects_invalid_subreddit_names():
    with pytest.raises(ValueError, match='invalid subreddit name'):
        sq.build_rows(['bad name!'], ['x'], 'DE:de', 'pain')


def test_dedupes_case_insensitively():
    rows = sq.build_rows(['Finanzen', 'finanzen'], ['PKV'], 'DE:de', 'pain')
    assert len(rows) == 1


def test_reads_dialog_discover_output():
    payload = {'results': [{'name': 'Finanzen', 'confidence': 0.8}, {'name': 'Versicherung', 'confidence': 0.4}]}
    assert sq.names_from_dialog(payload, min_confidence=0.5) == ['Finanzen']


def test_cli_appends_to_existing_plan(tmp_path):
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'schema_version': 1, 'revision': 'r1', 'queries': [
        {'query_id': 'q1', 'candidate_id': 'c1', 'query': 'PKV', 'provider': 'reddit', 'locale': 'DE:de',
         'intent': 'pain', 'source_family': 'reddit', 'seed_origin': 'supplied'}]}))
    out = tmp_path / 'plan-with-subreddits.json'
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/subreddit_query_rows.py'),
                           '--subreddits', 'Finanzen', '--keywords', 'PKV Wechsel', '--locale', 'DE:de',
                           '--plan', str(plan), '--out', str(out)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    merged = json.loads(out.read_text())
    assert len(merged['queries']) == 2 and merged['revision'] == 'r1+dialog-subreddits'
    assert not list(Draft202012Validator(SCHEMA).iter_errors(merged))


def test_reads_real_dialog_response_shape():
    payload = {'success': True, 'data': {'query': 'x', 'subreddits': [
        {'name': 'fireGermany', 'confidence': 0.499, 'match_tier': 'peripheral'},
        {'name': 'medizin', 'confidence': 0.431, 'match_tier': 'peripheral'}]}}
    assert sq.names_from_dialog(payload, min_confidence=0.45) == ['fireGermany']
