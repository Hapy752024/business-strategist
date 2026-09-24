#!/usr/bin/env python3
"""Reject claims that overstate evidence, omit counter scope, or cite unknown IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from build_claim_ledger import stable_id, independent_groups
from reviewed_voice import review_voice, reviewed_view, VOICES

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected an object")
                if not value.get("evidence_id"):
                    value["evidence_id"] = stable_id(value)
                records.append(value)
    return records


CONFIDENCE_LEVELS = {"unresolved", "low", "medium", "high"}
SCOPE_KEYS = {"sources", "queries", "geography", "date_range", "failed_routes"}


def derived_independence(support: list[str], known: dict[str, dict[str, Any]]) -> int:
    return len(independent_groups([known[item] for item in support if item in known]))


def _passage_errors(rows: Any, label: str, record_ids: set[str], evidence_by_id: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(rows, list):
        return [f"{label}: passage references must be a list"]
    for reference in rows:
        if not isinstance(reference, str) or "::" not in reference:
            errors.append(f"{label}: passage reference must be evidence_id::exact source span")
            continue
        evidence_id, passage = reference.split("::", 1)
        if evidence_id not in record_ids:
            errors.append(f"{label}: passage evidence {evidence_id} is not linked to the claim")
        elif not passage.strip() or passage not in str(evidence_by_id.get(evidence_id, {}).get("text") or ""):
            errors.append(f"{label}: passage does not resolve in captured evidence {evidence_id}")
    return errors


def validate_finding_claim_links(synthesis: dict[str, Any], ledger: list[dict[str, Any]],
                                 evidence: list[dict[str, Any]] | None = None) -> list[str]:
    """Require each finding to have a current, text-bound support review."""
    errors: list[str] = []
    by_claim = {str(row.get("claim_id")): row for row in ledger if row.get("claim_id")}
    evidence_by_id = {str(row.get("evidence_id")): row for row in (evidence or []) if row.get("evidence_id")}
    findings = synthesis.get("customer_needs", []) + synthesis.get("solution_requirements", [])
    if not findings and synthesis.get("status") != "insufficient_evidence":
        errors.append("zero findings require an insufficient_evidence disposition")
    for item in findings:
        finding_id = str(item.get("id", "<missing>"))
        finding_text = str(item.get("outcome") or item.get("condition_or_capability") or "").strip()
        finding_sha = hashlib.sha256(finding_text.encode()).hexdigest()
        linked = item.get("claim_ids", [])
        if not isinstance(linked, list) or not linked:
            errors.append(f"{finding_id}: material finding requires linked verified claim IDs")
            continue
        for claim_id in linked:
            claim = by_claim.get(str(claim_id))
            if not claim:
                errors.append(f"{finding_id}: unknown claim ID {claim_id}")
                continue
            if finding_id not in claim.get("finding_ids", []):
                errors.append(f"{finding_id}: claim {claim_id} does not bind back to this finding")
            verification = claim.get("verification")
            if not isinstance(verification, dict):
                errors.append(f"{finding_id}: claim {claim_id} has no verification record")
                continue
            reviews = verification.get("finding_reviews", [])
            matches = [row for row in reviews if isinstance(row, dict) and row.get("finding_id") == finding_id]
            if len(matches) != 1:
                errors.append(f"{finding_id}: claim {claim_id} needs one exact-text finding review")
                continue
            review = matches[0]
            if review.get("finding_sha256") != finding_sha:
                errors.append(f"{finding_id}: claim {claim_id} finding review is stale for finding text")
            if review.get("support_assessment") != "supported":
                errors.append(f"{finding_id}: claim {claim_id} does not support this published finding")
            if not str(review.get("rationale") or "").strip():
                errors.append(f"{finding_id}: claim {claim_id} finding review needs a rationale")
            errors.extend(_passage_errors(review.get("supporting_passages"), f"{finding_id}/{claim_id}",
                                          set(claim.get("supporting_evidence", [])), evidence_by_id))
    return errors


def validate(ledger: list[dict[str, Any]], evidence: list[dict[str, Any]], *, require_source_review: bool = False,
             require_verification: bool = False, evidence_sha256: str = "", source_review_sha256: str = "") -> list[str]:
    known = {record["evidence_id"]: record for record in evidence}
    errors: list[str] = []
    for claim in ledger:
        ident = str(claim.get("claim_id", "<missing>"))
        support = claim.get("supporting_evidence", [])
        counter = claim.get("counter_evidence", [])
        unknown = [item for item in support + counter if item not in known]
        if unknown:
            errors.append(f"{ident}: unknown evidence IDs: {', '.join(unknown)}")
        derived = derived_independence(support, known)
        if int(claim.get("independence_count", -1)) != derived:
            errors.append(f"{ident}: submitted independence count does not match derived support")
        if claim.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{ident}: unknown confidence level")
        if require_verification:
            verification = claim.get("verification")
            if not isinstance(verification, dict):
                errors.append(f"{ident}: current verification record required")
            else:
                expected_claim = hashlib.sha256(str(claim.get("claim", "")).encode()).hexdigest()
                if verification.get("claim_sha256") != expected_claim:
                    errors.append(f"{ident}: verification is stale for claim text")
                if evidence_sha256 and verification.get("evidence_sha256") != evidence_sha256:
                    errors.append(f"{ident}: verification is stale for evidence bytes")
                if source_review_sha256 and verification.get("source_review_sha256") != source_review_sha256:
                    errors.append(f"{ident}: verification is stale for source review")
                if verification.get("support_assessment") not in {"supported", "contradicted", "unsupported", "unresolved"}:
                    errors.append(f"{ident}: invalid verification support assessment")
                if not str(verification.get("verification_question") or "").strip() or not str(verification.get("rationale") or "").strip():
                    errors.append(f"{ident}: verification question and rationale required")
                assessment = verification.get("support_assessment")
                passages = (verification.get("supporting_passages") if assessment == "supported"
                            else verification.get("contrary_passages") if assessment == "contradicted" else [])
                if assessment in {"supported", "contradicted"} and not passages:
                    errors.append(f"{ident}: assessed support requires exact source passage references")
                refs = support if assessment == "supported" else counter if assessment == "contradicted" else []
                errors.extend(_passage_errors(passages, ident, set(refs), known))
        kind = claim.get("claim_scope_type", claim.get("claim_type"))
        if kind in {"observation", "inference", "hypothesis", "recommendation"}:
            kind = None  # Legacy epistemic label does not establish the claim's scope.
        if kind is None:
            if claim.get("confidence") in {"medium", "high"}:
                errors.append(f"{ident}: legacy claim requires claim_type and contextual assessment before medium/high confidence")
        elif kind not in {"occurrence", "pattern", "unmetness", "prevalence", "willingness_to_pay", "transfer"}:
            errors.append(f"{ident}: unknown claim_type")
        else:
            assessment = claim.get("confidence_assessment", {})
            dimensions = {"provenance", "target_fit", "independence", "context", "recency", "counterevidence", "coverage"}
            if not isinstance(assessment, dict) or any(not str(assessment.get(k) or "").strip() for k in dimensions):
                errors.append(f"{ident}: claim-specific confidence_assessment requires {', '.join(sorted(dimensions))}")
            if not claim.get("scope"):
                errors.append(f"{ident}: claim scope required")
            if not support and claim.get("confidence") != "unresolved":
                errors.append(f"{ident}: assessed claim needs observed support")
            if kind == "prevalence" and not claim.get("sampling_basis"):
                errors.append(f"{ident}: prevalence requires a sampling_basis, not mention counts")
            if kind == "unmetness" and not claim.get("alternatives_assessment"):
                errors.append(f"{ident}: unmetness requires alternatives_assessment")
            if kind == "willingness_to_pay":
                behavioral_ids = claim.get("price_bearing_behavior_evidence")
                if not isinstance(behavioral_ids, list) or not behavioral_ids or not set(behavioral_ids) <= set(support):
                    errors.append(f"{ident}: willingness_to_pay needs price-bearing behavior evidence IDs within supporting evidence")
            if kind == "transfer" and not claim.get("applicability_basis"):
                errors.append(f"{ident}: transfer requires applicability_basis")
            if kind == "pattern" and claim.get("confidence") == "high" and derived < 2:
                errors.append(f"{ident}: high-confidence cross-customer pattern requires independently attributable customers; one occurrence is not a pattern")
        if not counter:
            scope = claim.get("none_found_scope")
            if not isinstance(scope, dict) or not SCOPE_KEYS.issubset(scope) or any(not scope[key] and key != "failed_routes" for key in SCOPE_KEYS):
                errors.append(f"{ident}: counter-evidence or complete none-found scope required")
        for evidence_id in support:
            record = known.get(evidence_id, {})
            if record.get("evidence_type") == "irrelevant" or record.get("relevance") == "irrelevant":
                source_review = record.get("_source_review", {})
                corrected = source_review.get("status") == "accepted" and source_review.get("voice") in VOICES and source_review.get("relevance_correction_rationale") and not review_voice(record, source_review, source_review.get("reviewed_segment", ""))
                if not corrected:
                    errors.append(f"{ident}: irrelevant evidence cannot support claim")
        for evidence_id in set(support + counter):
            review = known.get(evidence_id, {}).get("analyst_review")
            if require_source_review and (
                not isinstance(review, dict)
                or review.get("status") != "accepted"
                or not isinstance(review.get("reason"), str)
                or not review["reason"].strip()
            ):
                errors.append(f"{ident}: {evidence_id}: accepted source review with reason required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--require-source-review", action="store_true", help="Require explicit analyst acceptance and rationale for every supporting and counter record.")
    parser.add_argument("--source-review", type=Path, help="Shared digest-bound source-review sidecar; overrides inline review proposals.")
    parser.add_argument("--customer-segment", default="")
    parser.add_argument("--require-verification", action="store_true")
    parser.add_argument("--synthesis", type=Path, help="Also check finding-to-claim associations.")
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    records = read_jsonl(args.evidence)
    errors = []
    if args.source_review:
        review = json.loads(args.source_review.read_text())
        if review.get("evidence_sha256") != hashlib.sha256(args.evidence.read_bytes()).hexdigest() or review.get("target_segment") != args.customer_segment:
            errors.append("stale or wrong-segment source review")
        by_id = {r.get("evidence_id"): r for r in review.get("reviews", [])}
        for index, record in enumerate(records):
            item = by_id.get(record["evidence_id"], {})
            record.pop("analyst_review", None)
            if item.get("status") == "accepted":
                problems = review_voice(record, item, args.customer_segment)
                errors.extend(f"{record['evidence_id']}: {p}" for p in problems)
                if not problems:
                    records[index] = reviewed_view(record, item)
    errors.extend(validate(ledger, records, require_source_review=args.require_source_review or bool(args.source_review),
                           require_verification=args.require_verification,
                           evidence_sha256=hashlib.sha256(args.evidence.read_bytes()).hexdigest(),
                           source_review_sha256=hashlib.sha256(args.source_review.read_bytes()).hexdigest() if args.source_review else ""))
    if args.synthesis:
        errors.extend(validate_finding_claim_links(json.loads(args.synthesis.read_text()), ledger, records))
    print(json.dumps({"status": "pass" if not errors else "fail", "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
