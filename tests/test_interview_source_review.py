"""Regression: collection labels must never authorize contaminated interview kits."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/evidence_scout/build_interview_kit.py"
SEGMENT = "Spanish small-business owners paying suppliers"


def record(evidence_id, text="A client paid late; I could not pay the supplier.", **extra):
    return {
        "evidence_id": evidence_id, "source": "reddit",
        "source_url": f"https://example.com/{evidence_id}", "text": text,
        "source_role": "customer_statement", "source_intent": "user_pain",
        "relevance": "relevant", "evidence_type": "pain", "strength": "weak", **extra,
    }


def acceptance(row, **extra):
    return {
        "evidence_id": row["evidence_id"], "source_url": row["source_url"],
        "status": "accepted", "reviewed_segment": SEGMENT, "segment_relation": "target",
        "journey_stage": "supplier invoice falls due before customer receipt",
        "relevance_rationale": "Owner describes their own supplier-payment incident in Spain.",
        "voice": "customer", "firsthand": True, "author_relationship": "firsthand_customer", **extra,
    }


def fixture_run(tmp_path, rows, entries=None, nested=False):
    evidence = tmp_path / "evidence" / "evidence.jsonl" if nested else tmp_path / "evidence.jsonl"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    (tmp_path / "summary.json").write_text(json.dumps({"topic": "supplier payments", "customer_segment": SEGMENT}))
    if entries is not None:
        review = {
            "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            "target_segment": SEGMENT, "reviews": entries,
        }
        (tmp_path / "source-review.json").write_text(json.dumps(review), encoding="utf-8")
    return evidence


def run(tmp_path, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--run-dir", str(tmp_path), *args], capture_output=True, text=True)


def test_unreviewed_auto_labelled_unrelated_reddit_fails_without_writes(tmp_path):
    row = record("unrelated", "I worked at Hooters during university. AMA")
    original = fixture_run(tmp_path, [row]).read_bytes()
    result = run(tmp_path)
    assert result.returncode == 1
    assert "source review required" in result.stderr
    assert not (tmp_path / "interview").exists()
    assert (tmp_path / "evidence.jsonl").read_bytes() == original


def test_rejected_unrelated_source_cannot_generate_kit(tmp_path):
    row = record("unrelated", "I worked at Hooters during university. AMA")
    fixture_run(tmp_path, [row], [acceptance(row, status="rejected", relevance_rationale="US restaurant employee story; no Spanish supplier-payment incident.")])
    result = run(tmp_path)
    assert result.returncode == 1
    assert "no accepted firsthand customer" in result.stderr
    assert not (tmp_path / "interview").exists()


def test_stale_review_does_not_overwrite_previous_artifacts(tmp_path):
    row = record("relevant")
    evidence = fixture_run(tmp_path, [row], [acceptance(row)])
    assert run(tmp_path).returncode == 0
    before = {p.name: p.read_bytes() for p in (tmp_path / "interview").iterdir()}
    evidence.write_text(evidence.read_text() + json.dumps(record("new-unreviewed")) + "\n")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "stale" in result.stderr
    assert {p.name: p.read_bytes() for p in (tmp_path / "interview").iterdir()} == before


def test_mixed_reviews_only_trace_firsthand_customers_and_label_discovery_context(tmp_path):
    rows = [
        record("customer", strength="strong"),
        record("creator", "My educational video about business cash flow.", source="youtube", source_role="creator_statement"),
        record("unrelated", "Restaurant story."),
        record("unresolved"), record("unreviewed"),
        record("secondhand", "A friend told me they had trouble."),
    ]
    entries = [
        acceptance(rows[0]),
        acceptance(rows[1], voice="operator", firsthand=False, relevance_rationale="Operator education; relevant context, not customer testimony."),
        acceptance(rows[2], status="rejected", relevance_rationale="Unrelated story."),
        acceptance(rows[3], status="unresolved", relevance_rationale="Country and participant role cannot be checked."),
        acceptance(rows[5], firsthand=False),
    ]
    evidence = fixture_run(tmp_path, rows, entries, nested=True)
    original = evidence.read_bytes()
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["items_traced"] == 1
    assert output["source_review_counts"] == {"accepted": 3, "rejected": 1, "unresolved": 1, "unreviewed": 1}
    guide = (tmp_path / "interview/interview-guide.md").read_text()
    screener = (tmp_path / "interview/interview-screener.md").read_text()
    tracker = (tmp_path / "interview/interview-tracker.md").read_text()
    assert "Evidence ID: customer" in guide
    for evidence_id in ("creator", "unrelated", "unresolved", "unreviewed", "secondhand"):
        assert f"https://example.com/{evidence_id}" not in guide
    assert "YouTube sources (operator voice; target segment; discovery lead only)" in screener
    for evidence_id in ("unrelated", "unresolved", "unreviewed"):
        assert f"https://example.com/{evidence_id}" not in screener
    assert "permission to message" in screener
    assert "Do not automatically disqualify someone without a workaround" in screener
    assert "no fixed confirmation count" in tracker
    assert "3 independent confirmations" not in tracker
    for document in (guide, screener, tracker):
        assert "3 accepted; 1 rejected; 1 unresolved; 1 unreviewed" in document
    assert evidence.read_bytes() == original


@pytest.mark.parametrize("change,error", [
    ({"source_url": "https://wrong.example"}, "URL mismatch"),
    ({"reviewed_segment": "French consumers"}, "reviewed_segment mismatch"),
    ({"segment_relation": None}, "segment_relation"),
    ({"relevance_rationale": " "}, "relevance_rationale"),
    ({"journey_stage": " "}, "journey_stage"),
    ({"firsthand": "true"}, "boolean firsthand"),
    ({"status": "auto_accepted"}, "invalid source review status"),
])
def test_invalid_acceptance_fails_before_creating_artifacts(tmp_path, change, error):
    row = record("one")
    fixture_run(tmp_path, [row], [acceptance(row, **change)])
    result = run(tmp_path)
    assert result.returncode == 1
    assert error in result.stderr
    assert not (tmp_path / "interview").exists()


def test_source_voice_cannot_be_coerced_into_customer(tmp_path):
    row = record("video", source="youtube", source_role="creator_statement")
    fixture_run(tmp_path, [row], [acceptance(row)])
    result = run(tmp_path)
    assert result.returncode == 1
    assert "contradicts original source_role" in result.stderr
    assert not (tmp_path / "interview").exists()


def test_ambiguous_community_record_needs_positive_firsthand_author_review(tmp_path):
    row = record("community", source_role="community_context")
    entry = acceptance(row); entry.pop("author_relationship")
    fixture_run(tmp_path, [row], [entry])
    result = run(tmp_path)
    assert result.returncode == 1
    assert "author_relationship=firsthand_customer" in result.stderr


def test_explicit_irrelevance_cannot_be_overridden_implicitly(tmp_path):
    row = record("spam", relevance="irrelevant")
    fixture_run(tmp_path, [row], [acceptance(row)])
    result = run(tmp_path)
    assert result.returncode == 1
    assert "contradicts explicit irrelevant" in result.stderr


def test_review_cannot_be_reused_for_different_requested_segment(tmp_path):
    row = record("one")
    fixture_run(tmp_path, [row], [acceptance(row)])
    result = run(tmp_path, "--segment", "French consumers")
    assert result.returncode == 1
    assert "target_segment" in result.stderr
    assert not (tmp_path / "interview").exists()


def test_explicit_review_path_is_supported(tmp_path):
    row = record("one")
    fixture_run(tmp_path, [row], [acceptance(row)])
    review = tmp_path / "checked.json"
    (tmp_path / "source-review.json").rename(review)
    assert run(tmp_path, "--source-review", str(review)).returncode == 0


@pytest.mark.parametrize("relation,discovery_label", [
    ("adjacent", "adjacent segment; comparator context only"),
    ("unresolved", "segment unresolved; discovery context only"),
])
def test_retailer_probes_exclude_contractor_or_unknown_segment_customer(tmp_path, relation, discovery_label):
    segment = "Spanish independent retailers paying wholesale suppliers"
    retailer = record("retailer", "I run a shop in Spain; my wholesaler required transfer before delivery.")
    contractor = record("contractor", "My construction client paid late and I could not pay subcontractors.")
    entries = [
        acceptance(retailer, reviewed_segment=segment, relevance_rationale="Retail shop owner describes paying their wholesale supplier."),
        acceptance(contractor, reviewed_segment=segment, segment_relation=relation,
                   relevance_rationale="Construction incident is not established as retailer pain; comparison only."),
    ]
    fixture_run(tmp_path, [retailer, contractor], entries)
    review_path = tmp_path / "source-review.json"
    review = json.loads(review_path.read_text())
    review["target_segment"] = segment
    review_path.write_text(json.dumps(review))
    result = run(tmp_path, "--segment", segment)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["items_traced"] == 1
    guide = (tmp_path / "interview/interview-guide.md").read_text()
    screener = (tmp_path / "interview/interview-screener.md").read_text()
    assert "Evidence ID: retailer" in guide
    assert "https://example.com/contractor" not in guide
    assert "subcontractors" not in guide
    assert discovery_label in screener
    assert "https://example.com/contractor" in screener
    assert "cannot establish target-segment pain or sentiment" in guide


def test_adjacent_customer_only_cannot_create_target_interview_kit(tmp_path):
    row = record("adjacent", "A contractor describes their construction cash flow.")
    fixture_run(tmp_path, [row], [acceptance(row, segment_relation="adjacent")])
    result = run(tmp_path)
    assert result.returncode == 1
    assert "no accepted firsthand customer" in result.stderr
    assert not (tmp_path / "interview").exists()
