from argparse import Namespace
import hashlib
from pathlib import Path

from scripts.evidence_scout import build_problem_validation_assessment as builder
from tests.problem_assessment_fixtures import prepare


def test_builder_records_reviewed_hash_bound_assessment(tmp_path, monkeypatch):
    scope = tmp_path / 'workspace'
    scope.mkdir()
    _, _, pack = prepare(scope, __import__('scripts.evidence_scout.workspace', fromlist=['workspace']), monkeypatch)
    (scope / 'market_research/pain_points/problem-validation-assessment.json').unlink()
    args = Namespace(
        workspace=str(scope), case_id='', assessment_revision=1, study_id='run-1',
        research_design_digest='a' * 64, customer_segments='market_research/customer_segments/current.md',
        customer_journey='market_research/customer_journey/current.md',
        pain_points='market_research/pain_points/current.md',
        voc_pack=str(pack.relative_to(scope)), target_segment='target customers', intent='customer_problem',
        geography='DE', scope_limits='Synthetic fixture only.', finding_id=['U1'], claim_id=['C1'],
        reviewer_id='reviewer-1', reviewer_type='independent_human', review_mode='independent_review',
        reviewed_at='2026-09-23T12:00:00Z', review_rationale='Reviewed the scoped evidence and counter-cases.', replace=False,
    )
    destination, assessment = builder.build(args)
    assert destination == scope / 'market_research/pain_points/problem-validation-assessment.json'
    assert assessment['status'] == 'supported'
    assert assessment['finding_ids'] == ['U1']
    assert assessment['claim_ids'] == ['C1']
    assert assessment['section_inputs']['pain_points']['sha256'] == hashlib.sha256(
        (scope / args.pain_points).read_bytes()).hexdigest()


def test_builder_rejects_study_identity_mismatch(tmp_path, monkeypatch):
    scope = tmp_path / 'workspace'
    scope.mkdir()
    _, _, pack = prepare(scope, __import__('scripts.evidence_scout.workspace', fromlist=['workspace']), monkeypatch)
    (scope / 'market_research/pain_points/problem-validation-assessment.json').unlink()
    args = Namespace(
        workspace=str(scope), case_id='', assessment_revision=1, study_id='wrong-run',
        research_design_digest='a' * 64, customer_segments='market_research/customer_segments/current.md',
        customer_journey='market_research/customer_journey/current.md',
        pain_points='market_research/pain_points/current.md', voc_pack=str(pack.relative_to(scope)),
        target_segment='target customers', intent='customer_problem', geography='DE', scope_limits='Synthetic only',
        finding_id=['U1'], claim_id=['C1'], reviewer_id='reviewer-1', reviewer_type='independent_human',
        review_mode='independent_review', reviewed_at='2026-09-23T12:00:00Z',
        review_rationale='Reviewed.', replace=False,
    )
    try:
        builder.build(args)
    except ValueError as exc:
        assert 'supported v3 synthesis' in str(exc)
    else:
        raise AssertionError('mismatched study identity was accepted')


def test_gate_records_legacy_untyped_evidence_warnings(tmp_path, monkeypatch, capsys):
    import json
    from types import SimpleNamespace
    scope = tmp_path / 'workspace'
    scope.mkdir()
    ws = __import__('scripts.evidence_scout.workspace', fromlist=['workspace'])
    _, _, pack = prepare(scope, ws, monkeypatch)
    (scope / 'market_research/pain_points/problem-validation-assessment.json').unlink()
    out = json.dumps({"status": "valid", "errors": [], "legacy_untyped_evidence": ["E1"]})
    monkeypatch.setattr(builder.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=out, stderr=''))
    args = Namespace(
        workspace=str(scope), case_id='', assessment_revision=1, study_id='run-1',
        research_design_digest='a' * 64, customer_segments='market_research/customer_segments/current.md',
        customer_journey='market_research/customer_journey/current.md',
        pain_points='market_research/pain_points/current.md',
        voc_pack=str(pack.relative_to(scope)), target_segment='target customers', intent='customer_problem',
        geography='DE', scope_limits='Synthetic fixture only.', finding_id=['U1'], claim_id=['C1'],
        reviewer_id='r', reviewer_type='independent_human', review_mode='independent_review',
        reviewed_at='2026-09-23T12:00:00Z', review_rationale='Reviewed.', replace=False,
    )
    _, assessment = builder.build(args)
    assert assessment['legacy_untyped_evidence'] == ['E1']
