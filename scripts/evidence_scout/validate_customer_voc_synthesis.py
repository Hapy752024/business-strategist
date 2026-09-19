#!/usr/bin/env python3
"""Validate separate topic/entity sampling frames and U/R VOC mappings."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reviewed_voice import review_voice, reviewed_collection_locales, VOICES


def validate_quality(synthesis: dict, evidence: dict, reviews: dict, coverage: dict) -> list[str]:
    """Version-2 research contract; semantic support still requires source review."""
    errors = []
    if synthesis.get("schema_version", 1) < 2:
        return errors
    all_items = synthesis.get("customer_needs", []) + synthesis.get("solution_requirements", [])
    ids = [item.get("id") for item in all_items]
    if len(ids) != len(set(ids)):
        errors.append("U/R IDs must be unique")
    if not all_items and synthesis.get("status") != "insufficient_evidence":
        errors.append("empty maps must state insufficient_evidence")
    if all_items and synthesis.get("status") == "insufficient_evidence":
        errors.append("insufficient_evidence cannot publish supported U/R maps")
    if coverage.get("coverage_status") != "complete_for_declared_plan" and synthesis.get("status") == "supported":
        errors.append("incomplete coverage requires scoped/provisional synthesis status")
    for item in all_items:
        ident = item.get("id")
        for field in ("context", "assessment", "scope", "counter_evidence_ids", "inference_rationale"):
            if field not in item:
                errors.append(f"{ident}: research-quality field {field} required")
        scope = item.get("scope", {})
        support = [evidence[e] for e in item.get("evidence_ids", []) if e in evidence]
        locales = set(scope.get("collection_locales", []))
        available = set().union(*(reviewed_collection_locales(r, reviews.get(r.get("evidence_id"), {})) for r in support))
        if not locales or not locales <= available:
            errors.append(f"{ident}: scope collection_locales must be evidenced (not assumed author geography)")
        relations = {reviews[e].get("segment_relation") for e in item.get("evidence_ids", []) if e in reviews}
        if set(scope.get("segment_relations", [])) != relations:
            errors.append(f"{ident}: scope segment_relations must match source review")
        if not str(scope.get("applicability_limits") or "").strip():
            errors.append(f"{ident}: scope applicability_limits required")
        if item.get("attribution") == "analyst_inferred" and not str(item.get("inference_rationale") or "").strip():
            errors.append(f"{ident}: analyst inference requires rationale")
        context = item.get("context", {})
        fields = ("role", "trigger", "current_alternative", "observed_behavior", "consequence") if str(ident).startswith("U") else ("role", "use_episode", "acceptable_outcome", "actual_performance")
        for field in fields:
            if not str(context.get(field) or "").strip():
                errors.append(f"{ident}: context {field} required; use unknown if unsupported")
        assessment = item.get("assessment", {})
        for field in ("unmetness", "confidence_rationale", "disposition", "next_question"):
            if not str(assessment.get(field) or "").strip():
                errors.append(f"{ident}: assessment {field} required")
        if not item.get("counter_evidence_ids") and not str(item.get("counter_search_scope") or "").strip():
            errors.append(f"{ident}: contrary cases or bounded counter_search_scope required")
        for e in item.get("counter_evidence_ids", []):
            if e not in reviews or reviews[e].get("status") != "accepted" or e not in evidence:
                errors.append(f"{ident}: counter evidence {e} is not reviewed")
            elif reviews[e].get("voice") not in VOICES or reviews[e].get("firsthand") is not True or review_voice(evidence[e], reviews[e], reviews[e].get("reviewed_segment", "")):
                errors.append(f"{ident}: counter evidence {e} must be reviewed firsthand voice; supplier context stays separate")
        if item.get("claim_type", "occurrence") in {"prevalence", "demand", "willingness_to_pay", "market_unmetness"}:
            errors.append(f"{ident}: commercial/population claims require separate claim-ledger validation, not a U/R map")
    codebook = synthesis.get("codebook", {})
    codes = codebook.get("codes", [])
    if not codebook.get("version") or not isinstance(codes, list):
        errors.append("versioned codebook required")
    known_codes = set()
    for code in codes:
        if not code.get("id") or code.get("id") in known_codes:
            errors.append("code IDs must be present and unique")
        known_codes.add(code.get("id"))
        for field in ("definition", "include_when", "exclude_when"):
            if not str(code.get(field) or "").strip():
                errors.append(f"code {code.get('id')}: {field} required")
        for instance in code.get("instances", []):
            record = evidence.get(instance.get("evidence_id"), {})
            quote = instance.get("quote")
            if not quote or quote not in record.get("text", ""):
                errors.append(f"code {code.get('id')}: instance must resolve to source passage")
    for item in all_items:
        if not item.get("code_ids") or not set(item.get("code_ids", [])) <= known_codes:
            errors.append(f"{item.get('id')}: mapped code_ids required")
    for investigation in synthesis.get("next_investigations", []):
        if any(not str(investigation.get(k) or "").strip() for k in ("question", "method", "reason", "decision_change")):
            errors.append("next investigation must name question, method, reason and decision_change")
    if not synthesis.get("next_investigations"):
        errors.append("next investigations required, including for insufficient evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--synthesis", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--source-review", required=True)
    parser.add_argument("--customer-segment", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / "schemas/customer-voc-synthesis.schema.json").read_text(encoding="utf-8"))
    synthesis = json.loads(Path(args.synthesis).read_text(encoding="utf-8"))
    coverage = json.loads(Path(args.coverage).read_text(encoding="utf-8"))
    evidence_path = Path(args.evidence)
    evidence = {}
    for line in evidence_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line); evidence[str(item.get("evidence_id"))] = item
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(synthesis)]
    review = json.loads(Path(args.source_review).read_text(encoding="utf-8"))
    if review.get("evidence_sha256") != hashlib.sha256(evidence_path.read_bytes()).hexdigest():
        errors.append("source review is stale: evidence_sha256 mismatch")
    if review.get("target_segment") != args.customer_segment:
        errors.append("source review target_segment mismatch")
    reviewed_user_ids: set[str] = set()
    perspective_by_id: dict[str, str] = {}
    relationship_by_voice = VOICES
    review_by_id = {}
    for item in review.get("reviews", []) if isinstance(review.get("reviews"), list) else []:
        evidence_id = str(item.get("evidence_id") or "")
        record = evidence.get(evidence_id)
        if evidence_id in review_by_id:
            errors.append(f"duplicate review for {evidence_id}")
        review_by_id[evidence_id] = item
        if not record or item.get("source_url") != record.get("source_url"):
            continue
        voice = str(item.get("voice") or "")
        if item.get("status") == "accepted" and voice in relationship_by_voice and item.get("firsthand") is True and item.get("author_relationship") == relationship_by_voice[voice] and item.get("reviewed_segment") == args.customer_segment:
            problems = review_voice(record, item, args.customer_segment)
            if problems:
                errors.extend(f"{evidence_id}: {problem}" for problem in problems)
                continue
            reviewed_user_ids.add(evidence_id)
            perspective_by_id[evidence_id] = voice
    empty_result = synthesis.get("status") == "insufficient_evidence" and not any(synthesis.get(k) for k in ("topic_led_evidence_ids", "entity_led_evidence_ids", "customer_needs", "solution_requirements"))
    if coverage.get("synthesis_allowed") is not True and not (empty_result and coverage.get("status") == "insufficient_evidence"):
        errors.append("customer-feedback coverage does not allow scoped synthesis")
    topic_ids = set(synthesis.get("topic_led_evidence_ids", []))
    entity_ids = set(synthesis.get("entity_led_evidence_ids", []))
    covered_topic_ids = set(coverage.get("topic_led_voc", {}).get("accepted_evidence_ids", []))
    for cell in coverage.get("topic_led_voc", {}).get("cells", []):
        for evidence_id in cell.get("accepted_evidence_ids", []):
            record = evidence.get(evidence_id, {})
            memberships = [m for m in record.get("discovery_memberships", []) if isinstance(m, dict)]
            locales = {record.get("collection_locale")} | {m.get("collection_locale") for m in memberships if m.get("sampling_frame") == "topic_led_voc"}
            if cell.get("locale") not in locales:
                errors.append(f"{evidence_id}: topic cell {cell.get('cell_id')} locale has no matching collection membership")
    covered_entity: dict[str, list[tuple[str, str, str, str]]] = {}
    for row in coverage.get("source_matrix", []):
        if not isinstance(row, dict) or not row.get("applicable"):
            continue
        for locator_result in row.get("locator_results", []):
            if not isinstance(locator_result, dict):
                continue
            for evidence_id in locator_result.get("accepted_evidence_ids", []):
                covered_entity.setdefault(str(evidence_id), []).append((str(row.get("entity_id")), str(row.get("locale")), str(row.get("source_lane")), str(locator_result.get("locator"))))
    for evidence_id in topic_ids | entity_ids:
        if evidence_id not in evidence:
            errors.append(f"unknown evidence ID: {evidence_id}")
        elif evidence_id not in reviewed_user_ids:
            errors.append(f"{evidence_id}: not accepted as reviewed firsthand target-user voice")
    for evidence_id in topic_ids:
        if evidence_id in evidence and evidence[evidence_id].get("sampling_frame") != "topic_led_voc" and not any(m.get("sampling_frame") == "topic_led_voc" for m in evidence[evidence_id].get("discovery_memberships", []) if isinstance(m, dict)):
            errors.append(f"{evidence_id}: listed as topic-led but record frame differs")
        if evidence_id not in covered_topic_ids:
            errors.append(f"{evidence_id}: topic-led evidence is not accepted by finalized coverage")
    for evidence_id in entity_ids:
        if evidence_id in evidence and evidence[evidence_id].get("sampling_frame") != "entity_led_feedback" and not any(m.get("sampling_frame") == "entity_led_feedback" for m in evidence[evidence_id].get("discovery_memberships", []) if isinstance(m, dict)):
            errors.append(f"{evidence_id}: listed as entity-led but record frame differs")
        bindings = covered_entity.get(evidence_id)
        if not bindings:
            errors.append(f"{evidence_id}: entity evidence is not accepted by finalized coverage")
        elif evidence_id in evidence:
            record = evidence[evidence_id]
            for binding in bindings:
                if (record.get("subject_entity_id"), record.get("collection_source_lane"), record.get("collection_locator")) != (binding[0], binding[2], binding[3]) or binding[1] not in reviewed_collection_locales(record, review_by_id.get(evidence_id, {})):
                    errors.append(f"{evidence_id}: entity/locale/source lane/locator does not match finalized coverage")
    allowed = topic_ids | entity_ids
    u_ids = {item.get("id") for item in synthesis.get("customer_needs", [])}
    for group in (synthesis.get("customer_needs", []), synthesis.get("solution_requirements", [])):
        for item in group:
            observed_perspectives = {perspective_by_id[evidence_id] for evidence_id in item.get("evidence_ids", []) if evidence_id in perspective_by_id}
            declared_perspectives = set(item.get("perspectives", []))
            if observed_perspectives != declared_perspectives:
                errors.append(f"{item.get('id')}: perspectives must exactly match contributing reviewed evidence")
            for evidence_id in item.get("evidence_ids", []) + item.get("counter_evidence_ids", []):
                if evidence_id not in allowed:
                    errors.append(f"{item.get('id')}: evidence {evidence_id} is not declared in a sampling frame")
    for item in synthesis.get("solution_requirements", []):
        for linked in item.get("linked_u_ids", []):
            if linked not in u_ids:
                errors.append(f"{item.get('id')}: unknown linked customer need {linked}")
    errors.extend(validate_quality(synthesis, evidence, review_by_id, coverage))
    result = {"status": "blocked" if errors else "valid", "quality_contract": "v2" if synthesis.get("schema_version", 1) >= 2 else "legacy_unassessed", "error_count": len(errors), "errors": errors}
    print(json.dumps(result, indent=2))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
