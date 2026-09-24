"""Synthetic gate fixtures; validation CLIs are stubbed only in gate lifecycle tests."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(scope: Path, workspace, monkeypatch, *, case_id="", revision=1, study_id="run-1"):
    monkeypatch.setattr(workspace.subprocess, "run",
                        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="valid", stderr=""))
    section_inputs = {}
    artifacts = []
    for section in ("customer_segments", "customer_journey", "pain_points"):
        path = scope / "market_research" / section / "current.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Reviewed synthetic scope; finding U1. https://evidence.example/{section} 2026-09-23\n")
        artifacts.append(path)
        section_inputs[section] = {"path": path.relative_to(scope).as_posix(), "sha256": _sha(path)}

    pack = scope / "market_research/pain_points/runs" / study_id / "customer-feedback"
    pack.mkdir(parents=True, exist_ok=True)
    payloads = {
        "evidence.jsonl": '{"evidence_id":"E1","text":"A relevant customer episode."}\n',
        "source-review.json": {"study_id": study_id, "target_segment": "target customers"},
        "customer-feedback-coverage.json": {"coverage_status": "complete_for_declared_plan"},
        "customer-voc-synthesis.json": {"schema_version": 3, "topic": "customer workflow", "status": "supported",
            "study_id": study_id, "research_design_digest": "a" * 64,
            "customer_needs": [{"id": "U1", "outcome": "Customers encounter a recurring workflow problem.", "claim_ids": ["C1"]}]},
        "claim-ledger.json": [{"claim_id": "C1"}],
        "customer-feedback-source-plan.json": {"schema_version": 2, "topic": "customer workflow", "customer_segment": "target customers", "study_intent": "customer_problem",
            "study_id": study_id, "research_design_digest": "a" * 64},
    }
    for filename, payload in payloads.items():
        path = pack / filename
        path.write_text(payload if isinstance(payload, str) else json.dumps(payload))
    assessment = {
        "schema_version": 1, "status": "supported", "intent": "customer_problem", "case_id": case_id,
        "assessment_revision": revision, "target_segment": "target customers",
        "scope": {"geography": "DE", "limits": "Synthetic fixture only."},
        "study_id": study_id, "research_design_digest": "a" * 64,
        "section_inputs": section_inputs,
        "voc_pack_path": pack.relative_to(scope).as_posix(),
        "voc_pack_hashes": {filename: _sha(pack / filename) for filename in payloads},
        "finding_ids": ["U1"], "claim_ids": ["C1"],
        "review": {"reviewer_id": "fixture-reviewer", "reviewer_type": "independent_human",
                   "review_mode": "independent_review", "reviewed_at": "2026-09-23T12:00:00Z",
                   "rationale": "Synthetic gate lifecycle fixture."},
    }
    assessment_path = scope / "market_research/pain_points/problem-validation-assessment.json"
    assessment_path.write_text(json.dumps(assessment))
    artifacts.append(assessment_path)
    return artifacts, assessment, pack
