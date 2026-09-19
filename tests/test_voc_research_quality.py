"""Research-quality regressions. Synthetic fault fixtures, not semantic gold data."""
import hashlib
import argparse
import json
import sys
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/evidence_scout"))
from reviewed_voice import review_voice, reviewed_view, reviewed_collection_locales
from build_experience_ledger import build
from build_interview_kit import select_interview_items
from validate_customer_voc_synthesis import validate_quality
from validate_synthesis import validate as validate_claims


def review(record, **extra):
    return {"evidence_id": record["evidence_id"], "source_url": record["source_url"], "status": "accepted",
            "reviewed_segment": "households", "segment_relation": "target", "relevance_rationale": "Firsthand own incident",
            "voice": "customer", "firsthand": True, "author_relationship": "firsthand_customer",
            "journey_stage": "use", **extra}


def record(**extra):
    return {"evidence_id": "t1", "source_url": "https://community.example/1", "text": "Erfahrungen: I arranged delivery; it arrived before my move.",
            "sampling_frame": "topic_led_voc", "collection_locale": "CH:de", "source_role": "community_context",
            "author_voice_status": "unreviewed", **extra}


def synthesis():
    return {"schema_version": 2, "status": "scoped", "topic_led_evidence_ids": ["t1"], "entity_led_evidence_ids": [],
            "customer_needs": [{"id": "U1", "outcome": "Have belongings available at move-in", "evidence_ids": ["t1"],
                "perspectives": ["customer"], "attribution": "customer_stated", "inference_rationale": "",
                "context": {"role": "household", "trigger": "move", "current_alternative": "delivery", "observed_behavior": "arranged delivery", "consequence": "available before move"},
                "scope": {"collection_locales": ["CH:de"], "segment_relations": ["target"], "applicability_limits": "One account, geography of author unknown"},
                "assessment": {"unmetness": "satisfied in this incident", "confidence_rationale": "Located account; generality unknown", "disposition": "compare", "next_question": "When does the alternative fail?"},
                "counter_evidence_ids": [], "counter_search_scope": "One source only; more contrasts needed", "code_ids": ["C1"]}],
            "solution_requirements": [],
            "codebook": {"version": 1, "codes": [{"id": "C1", "definition": "timely availability", "include_when": "timing relative to move is stated", "exclude_when": "generic speed praise", "instances": [{"evidence_id": "t1", "quote": "it arrived before my move"}]}]},
            "next_investigations": [{"question": "Which contexts fail?", "method": "contrasting incident interviews", "reason": "Context unknown", "decision_change": "Differentiate satisfied contexts from unmet ones"}]}


def test_local_heuristic_label_correctable_but_supplier_not():
    r = record(source_role="editorial_context", source_intent="editorial_content", classification_basis="heuristic")
    accepted = review(r, reviewed_source_kind="forum", source_kind_rationale="Independent discussion",
                      supporting_passage=r["text"], author_context_basis="Source-local participant describes own action")
    assert not review_voice(r, accepted, "households")
    r["author_voice_status"] = "supplier_context"
    assert any("supplier" in error for error in review_voice(r, accepted, "households"))
    r["author_voice_status"] = "unreviewed"; accepted["supporting_passage"] = "invented"
    assert any("supporting_passage" in error for error in review_voice(r, accepted, "households"))


@pytest.mark.parametrize("label", ["search_snippet", "snippet"])
def test_snippet_cannot_be_customer_voice(label):
    r = record(content_completeness=label)
    assert any("snippet" in error for error in review_voice(r, review(r), "households"))


def test_split_located_customer_supplier_and_quote_roles():
    text = "Customer: I used a spreadsheet.\nCompany: Buy our app.\nCustomer quotes a friend: I hate it."
    d = record(text=text, capture_unit="document", classification_basis="heuristic")
    spans = [(0, text.index("\n"), "customer_candidate"), (text.index("Company:"), text.index("\nCustomer quotes"), "supplier"), (text.index("Customer quotes"), len(text), "quoted_other")]
    annotations = [{"document_id": "t1", "start": start, "end": end, "quote": text[start:end], "speaker_id": str(i), "speaker_basis": "post header", "speaker_role": role} for i, (start, end, role) in enumerate(spans)]
    out = build([d], annotations)
    assert len(out) == 3 and not review_voice(out[0], review(out[0]), "households")
    assert review_voice(out[1], review(out[1]), "households")
    assert review_voice(out[2], review(out[2]), "households")
    annotations[0]["quote"] = "wrong"
    with pytest.raises(ValueError, match="span"):
        build([d], annotations)


def test_relevant_episode_from_heuristically_irrelevant_page_can_be_corrected():
    d = record(classification_basis="heuristic", capture_unit="document", relevance="irrelevant", evidence_type="irrelevant")
    episode = build([d], [{"document_id": "t1", "start": 0, "end": len(d["text"]), "quote": d["text"], "speaker_id": "p1", "speaker_basis": "post header", "speaker_role": "customer_candidate"}])[0]
    accepted = review(episode, reviewed_source_kind="forum", source_kind_rationale="Independent discussion", supporting_passage=episode["text"], author_context_basis="Own move", relevance_correction_rationale="Page keyword classifier missed this relevant episode")
    assert not review_voice(episode, accepted, "households")
    claim = {"claim_id": "corrected", "supporting_evidence": [episode["evidence_id"]], "counter_evidence": [], "confidence": "unresolved", "independence_count": 0,
             "none_found_scope": {"sources": ["forum"], "queries": ["q"], "geography": "unknown", "date_range": "unknown", "failed_routes": []}}
    assert not validate_claims([claim], [reviewed_view(episode, accepted)], require_source_review=True)


def test_interview_selection_does_not_truncate_successful_contrast():
    rows = []
    for index in range(8):
        r = record(evidence_id=str(index), evidence_type="pain", source_intent="user_pain")
        rows.append({**r, "_source_review": review(r)})
    r = record(evidence_id="successful", evidence_type="counter_evidence")
    rows.append({**r, "_source_review": review(r, material_counterexample=True, outcome_status="satisfied")})
    chosen = select_interview_items(rows, 8)
    assert "successful" in {r["evidence_id"] for r in chosen}
    assert len(chosen) == 8


def test_needs_quality_requires_context_and_blocks_supplier_countervoice():
    r = record(); s = synthesis()
    assert not validate_quality(s, {"t1": r}, {"t1": review(r)}, {"coverage_status": "partial"})
    supplier = record(evidence_id="supplier", source_role="competitor_context", author_voice_status="supplier_context")
    s["customer_needs"][0]["counter_evidence_ids"] = ["supplier"]
    errors = validate_quality(s, {"t1": r, "supplier": supplier}, {"t1": review(r), "supplier": review(supplier, voice="operator")}, {"coverage_status": "partial"})
    assert any("counter evidence supplier" in error for error in errors)
    s["customer_needs"][0]["context"].pop("trigger")
    assert any("trigger" in e for e in validate_quality(s, {"t1": r}, {"t1": review(r)}, {}))


def write_pack(path, *, empty=False):
    path.mkdir(parents=True, exist_ok=True)
    r = record(); s = synthesis()
    evidence = "" if empty else json.dumps(r) + "\n"
    (path / "evidence.jsonl").write_text(evidence)
    (path / "source-review.json").write_text(json.dumps({"evidence_sha256": hashlib.sha256(evidence.encode()).hexdigest(), "target_segment": "households", "reviews": [] if empty else [review(r)]}))
    coverage = {"status": "insufficient_evidence" if empty else "partial", "synthesis_allowed": not empty, "coverage_status": "partial", "topic_led_voc": {"accepted_evidence_ids": [] if empty else ["t1"], "cells": [] if empty else [{"cell_id": "CH:de", "locale": "CH:de", "accepted_evidence_ids": ["t1"]}]}, "source_matrix": []}
    if empty:
        s.update(status="insufficient_evidence", topic_led_evidence_ids=[], customer_needs=[], codebook={"version": 1, "codes": []})
    (path / "customer-feedback-coverage.json").write_text(json.dumps(coverage))
    (path / "customer-voc-synthesis.json").write_text(json.dumps(s))
    return s, coverage


def validate_pack(path):
    return subprocess.run([sys.executable, str(ROOT / "scripts/evidence_scout/validate_customer_voc_synthesis.py"), "--evidence", str(path / "evidence.jsonl"), "--source-review", str(path / "source-review.json"), "--coverage", str(path / "customer-feedback-coverage.json"), "--synthesis", str(path / "customer-voc-synthesis.json"), "--customer-segment", "households"], capture_output=True, text=True)


def test_scoped_cli_synthesis_and_false_country_coverage(tmp_path):
    s, coverage = write_pack(tmp_path)
    result = validate_pack(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    coverage["topic_led_voc"]["cells"].append({"cell_id": "CH:fr", "locale": "CH:fr", "accepted_evidence_ids": ["t1"]})
    (tmp_path / "customer-feedback-coverage.json").write_text(json.dumps(coverage))
    result = validate_pack(tmp_path)
    assert result.returncode == 2 and "collection membership" in result.stdout


def test_zero_voice_is_valid_insufficient_not_invented_need(tmp_path):
    write_pack(tmp_path, empty=True)
    result = validate_pack(tmp_path)
    assert result.returncode == 0, result.stdout


def test_country_feed_has_reviewed_language_resolution_not_automatic_membership():
    r = record(collection_locale="CH:und", requested_locales=["CH:de", "CH:fr"])
    assert not reviewed_collection_locales(r, review(r))
    resolved = review(r, language_review={"language": "de", "supporting_passage": "Erfahrungen", "rationale": "Original review in German"})
    assert reviewed_collection_locales(r, resolved) == {"CH:de"}
    assert r["collection_locale"] == "CH:und"


def test_each_entity_coverage_binding_checked_not_only_last(tmp_path):
    s, coverage = write_pack(tmp_path)
    e = record(evidence_id="e1", sampling_frame="entity_led_feedback", subject_entity_id="app", collection_source_lane="apple_app_store_reviews", collection_locator="123")
    path = tmp_path / "evidence.jsonl"
    path.write_text(path.read_text() + json.dumps(e) + "\n")
    reviews = json.loads((tmp_path / "source-review.json").read_text())
    reviews["evidence_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    reviews["reviews"].append(review(e))
    (tmp_path / "source-review.json").write_text(json.dumps(reviews))
    s["entity_led_evidence_ids"] = ["e1"]
    coverage["source_matrix"] = [{"entity_id": "app", "locale": locale, "source_lane": "apple_app_store_reviews", "applicable": True, "locator_results": [{"locator": "123", "accepted_evidence_ids": ["e1"]}]} for locale in ("CH:fr", "CH:de")]
    (tmp_path / "customer-feedback-coverage.json").write_text(json.dumps(coverage))
    (tmp_path / "customer-voc-synthesis.json").write_text(json.dumps(s))
    assert validate_pack(tmp_path).returncode == 2


def test_occurrence_confidence_not_fixed_customer_count():
    r = record(independence_key="unknown:t1")
    claim = {"claim_id": "c1", "claim_type": "occurrence", "scope": "this incident only", "confidence": "high", "supporting_evidence": ["t1"], "counter_evidence": [], "independence_count": 0,
             "none_found_scope": {"sources": ["thread"], "queries": ["q"], "geography": "unknown", "date_range": "unknown", "failed_routes": []},
             "confidence_assessment": {k: "Located incident; wider scope unknown" for k in ("provenance", "target_fit", "independence", "context", "recency", "counterevidence", "coverage")}}
    assert not validate_claims([claim], [r])
    claim["claim_type"] = "prevalence"
    assert any("sampling_basis" in error for error in validate_claims([claim], [r]))


def test_reviewed_forum_capture_to_experience_coverage_and_synthesis(tmp_path, monkeypatch):
    """Ordinary collector/annotation/finalizer/validator interfaces; no metadata repair."""
    import collect
    from plan_customer_feedback import build_plan, LANES
    from finalize_customer_feedback import validate as finalize
    url = "https://forum.example/thread/123"
    entity = {"id": "mover", "name": "Mover", "domain": "mover.example", "lane": "similar_company",
              "sources": {"external_forums_communities": [{"locator": url, "locales": ["CH:de"], "review_status": "accepted", "review_reason": "Checked public forum and entity identity"}]},
              "not_applicable": {lane: "Not applicable to this scoped fixture" for lane in LANES if lane != "external_forums_communities"}}
    plan = build_plan("move", "households", ["CH:de"], [entity])
    plan_path = tmp_path / "plan.json"; plan_path.write_text(json.dumps(plan))
    args = argparse.Namespace(topic="move", customer_segment="households", hypothesis_id="H1", geo="CH", language="de", limit=10,
        sampling_frame="entity_led_feedback", subject_entity_id="mover", entity_source_url=url, entity_source_lane="external_forums_communities", customer_feedback_source_plan=str(plan_path), segment_keywords="", problem_keywords="", workaround_keywords="")
    monkeypatch.setattr(collect, "get_secret", lambda *a: (a[0], "fixture"))
    monkeypatch.setattr(collect, "assess_relevance", lambda *a: ("relevant", "fixture", 1))
    text = "My belongings arrived before my move."
    monkeypatch.setattr(collect, "http_post", lambda *a, **k: {"ok": True, "body": {"data": {"markdown": text}}})
    documents, result = collect.collect_firecrawl(args, [], tmp_path)
    assert result["status"] == "ok"
    annotation = {"document_id": documents[0]["evidence_id"], "start": 0, "end": len(text), "quote": text, "speaker_id": "p1", "speaker_basis": "post author", "speaker_role": "customer_candidate"}
    episode = build(documents, [annotation])[0]
    # Producer metadata flows through extraction without hand-written binding fields.
    assert episode["collection_locator"] == url and episode["subject_entity_id"] == "mover"
    results = {"topic_led_voc": {"cells": [{"cell_id": plan["topic_matrix"][0]["cell_id"], "attempted": True, "retrieved_count": 1, "reviewed_count": 1, "accepted_count": 1, "accepted_evidence_ids": ["t1"]}]},
               "source_results": [{"entity_id": "mover", "locale": "CH:de", "source_lane": "external_forums_communities", "attempted": True, "retrieved_count": 1, "reviewed_count": 1, "accepted_customer_voice_count": 1,
                   "locator_results": [{"locator": url, "attempted": True, "retrieved_count": 1, "reviewed_count": 1, "accepted_customer_voice_count": 1, "accepted_evidence_ids": [episode["evidence_id"]]}]}]}
    coverage, errors = finalize(plan, results)
    assert not errors and coverage["synthesis_allowed"]
    pack = tmp_path / "pack"; s, _ = write_pack(pack)
    evidence_path = pack / "evidence.jsonl"
    evidence_path.write_text(evidence_path.read_text() + json.dumps(episode) + "\n")
    review_path = pack / "source-review.json"; reviews = json.loads(review_path.read_text())
    reviews["evidence_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    reviews["reviews"].append(review(episode))
    review_path.write_text(json.dumps(reviews))
    s["entity_led_evidence_ids"] = [episode["evidence_id"]]
    (pack / "customer-feedback-coverage.json").write_text(json.dumps(coverage))
    (pack / "customer-voc-synthesis.json").write_text(json.dumps(s))
    result = validate_pack(pack)
    assert result.returncode == 0, result.stdout + result.stderr
