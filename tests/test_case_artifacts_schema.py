"""Schema and semantic checks for assumption registers, experiment cards and the experiment library."""
from pathlib import Path

from scripts.validate_case_artifacts import load_library, validate_card, validate_library, validate_register

ROOT = Path(__file__).resolve().parents[1]
REF = {'path': 'cases/a/market_research/runs/r1/customer-feedback/claim-ledger.json', 'digest': 'a' * 64, 'id': 'c1'}


def minimal_register(status='unknown', evidence_refs=None):
    return {'schema_version': 1, 'case_id': 'a', 'revision': 1, 'updated_at': '2026-10-21T00:00:00Z',
            'riskiest': [], 'entries': [{
                'id': 'A-pay', 'statement': 'Owners pay for monthly bookkeeping help.', 'type': 'viability',
                'importance': 'critical', 'status': status, 'evidence_refs': evidence_refs or [],
                'counter_evidence_refs': [], 'confidence_note': 'Not checked.', 'owner_module': 'idea-grill',
                'updated_at': '2026-10-21T00:00:00Z', 'revision': 1, 'history': []}]}


def minimal_card(library_id='message-smoke-test'):
    return {'schema_version': 1, 'id': 'E-1', 'library_id': library_id, 'assumption_ids': ['A-pay'],
            'hypothesis': {'segment': 'owners', 'action': 'book a call', 'problem': 'manual bookkeeping',
                           'threshold': {'metric': 'booked', 'value': 5, 'sample': 200, 'window_days': 14}},
            'kill_rule': 'Fewer than 5 bookings from 200 qualified visitors.',
            'sample_plan': {'p_low': 0.02, 'p_high': 0.05, 'per_variant': 100}, 'channel': 'linkedin',
            'variants': ['V1', 'V2'], 'status': 'planned', 'authorization_refs': [], 'responders_ref': None,
            'supersedes': None, 'result': None, 'frozen_digest': None}


def test_library_config_valid():
    assert validate_library(load_library(ROOT)) == []


def test_library_has_ten_seed_entries():
    assert len(load_library(ROOT)['experiments']) == 10


def test_register_minimal_valid():
    assert validate_register(minimal_register()) == []


def test_register_rejects_supported_without_ref():
    errors = validate_register(minimal_register(status='supported', evidence_refs=[]))
    assert any('reference' in e for e in errors)


def test_register_accepts_supported_with_ref():
    assert validate_register(minimal_register(status='supported', evidence_refs=[REF])) == []


def test_register_rejects_bad_status():
    assert validate_register(minimal_register(status='likely'))


def test_register_rejects_bare_ref():
    reg = minimal_register(status='supported', evidence_refs=['c1'])
    assert validate_register(reg)


def test_card_minimal_valid():
    assert validate_card(minimal_card(), load_library(ROOT)) == []


def test_card_rejects_unknown_library_id():
    errs = validate_card(minimal_card(library_id='nope'), load_library(ROOT))
    assert any('library_id' in e for e in errs)


def test_card_requires_assumption():
    card = minimal_card()
    card['assumption_ids'] = []
    assert validate_card(card, load_library(ROOT))
