"""One shared, digest-bound claim-challenge check for every final recommendation path (Task 8 fix round 1)."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts import claim_challenge as cc

LEDGER_REL = 'cases/a/market_research/pain_points/runs/r1/customer-feedback/claim-ledger.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def ledger(root):
    return write(root / LEDGER_REL, [{'claim_id': 'C1'}])


def reviewed_report(root, digest):
    return write(root / LEDGER_REL.replace('claim-ledger.json', 'falsification-report.json'),
                 {'basis': 'reviewed_ledger', 'source_ledger_sha256': digest, 'counts': {}})


def draft(root):
    path = write(root / 'cases/a/draft/draft-claims.json', [{'claim_id': 'D1', 'text': 't', 'section': 's', 'sources': []}])
    return path


def draft_report(root, path, digest):
    return write(path.parent / 'draft-falsification-report.json',
                 {'basis': 'draft', 'source_ledger': str(path), 'source_ledger_sha256': digest, 'counts': {}})


def test_missing_challenge_refused(tmp_path):
    with pytest.raises(ValueError, match='no claim challenge'):
        cc.require_current(tmp_path, 'a', [])


def test_reviewed_report_must_match_bound_ledger_digest(tmp_path):
    led = ledger(tmp_path)
    reviewed_report(tmp_path, '0' * 64)
    with pytest.raises(ValueError, match='claim challenge stale or unrelated to current claims'):
        cc.require_current(tmp_path, 'a', [LEDGER_REL])
    reviewed_report(tmp_path, sha(led))
    assert cc.require_current(tmp_path, 'a', [LEDGER_REL])['basis'] == 'reviewed_ledger'


def test_draft_report_never_satisfies_while_ledger_bound(tmp_path):
    ledger(tmp_path)
    d = draft(tmp_path)
    draft_report(tmp_path, d, sha(d))
    with pytest.raises(ValueError, match='stale or unrelated'):
        cc.require_current(tmp_path, 'a', [LEDGER_REL])


def test_draft_report_must_match_its_draft_claims(tmp_path):
    d = draft(tmp_path)
    draft_report(tmp_path, d, '0' * 64)
    with pytest.raises(ValueError, match='stale or unrelated'):
        cc.require_current(tmp_path, 'a', [])
    draft_report(tmp_path, d, sha(d))
    assert cc.require_current(tmp_path, 'a', [])['basis'] == 'draft'
    d.write_text('[]')  # draft changed after the challenge
    with pytest.raises(ValueError, match='stale or unrelated'):
        cc.require_current(tmp_path, 'a', [])
