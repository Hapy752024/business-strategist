#!/usr/bin/env python3
"""Locate proposed speaker/episode annotations in preserved documents.

Input annotations are analyst/model proposals, never automatic customer evidence.
Use exact character offsets in original text. Supplier replies, quotations and
unknown speakers are separate units. Source review happens after extraction.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def build(documents: list[dict], annotations: list[dict]) -> list[dict]:
    by_id = {d["evidence_id"]: d for d in documents}
    if len(by_id) != len(documents):
        raise ValueError("document IDs must be unique; merge discovery memberships before extraction")
    output, seen = [], set()
    for annotation in annotations:
        parent = by_id.get(annotation.get("document_id"))
        if not parent:
            raise ValueError("unknown annotation document_id")
        text = str(parent.get("text") or "")
        start, end = annotation.get("start"), annotation.get("end")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            raise ValueError("experience requires exact in-range start/end offsets")
        quote = text[start:end]
        if annotation.get("quote") != quote:
            raise ValueError("experience quote does not match preserved source span")
        speaker = str(annotation.get("speaker_id") or "").strip()
        if not speaker or not str(annotation.get("speaker_basis") or "").strip():
            raise ValueError("speaker_id (source-local or unknown) and speaker_basis required")
        role = annotation.get("speaker_role", "unresolved")
        if role not in {"customer_candidate", "supplier", "quoted_other", "unresolved"}:
            raise ValueError("invalid speaker_role")
        key = (parent["evidence_id"], start, end, speaker)
        if key in seen:
            raise ValueError("duplicate experience annotation")
        seen.add(key)
        ident = "ex-" + hashlib.sha256(json.dumps(key).encode()).hexdigest()[:20]
        sequence = annotation.get("episode_sequence")
        if sequence is not None and (type(sequence) is not int or sequence < 0):
            raise ValueError("episode_sequence must be a non-negative integer")
        update_of = annotation.get("update_of")
        if update_of is not None and not str(update_of).strip():
            raise ValueError("update_of must identify the earlier source-local episode")
        spans = annotation.get("observations", {})
        for name, observation in spans.items():
            if not isinstance(observation, dict) or observation.get("attribution") not in {"observed", "inferred", "unknown"}:
                raise ValueError(f"{name}: observation attribution required")
            if observation["attribution"] == "observed":
                support = observation.get("supporting_quote")
                if not isinstance(support, str) or not support.strip() or support not in quote:
                    raise ValueError(f"{name}: observed field must link to its original passage")
            elif observation["attribution"] == "inferred" and not observation.get("rationale"):
                raise ValueError(f"{name}: inferred field requires rationale")
        explicit_supplier = role == "supplier" or parent.get("classification_basis") == "explicit_supplier_identity" or parent.get("author_voice_status") in {"supplier_context", "supplier", "company", "affiliate"}
        result = {**parent, "evidence_id": ident, "document_id": parent["evidence_id"],
                  "original_classification": {key: parent.get(key) for key in ("classification_basis", "source_role", "source_intent", "relevance")},
                  "text": quote, "verbatim_quote": quote,
                  "content_sha256": hashlib.sha256(quote.encode()).hexdigest(),
                  "capture_unit": "experience", "source_span": {"start": start, "end": end},
                  "document_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "speaker_id": speaker, "speaker_basis": annotation["speaker_basis"],
                  "speaker_role_proposal": role, "observations": spans,
                  "incident_id": annotation.get("incident_id"),
                  "episode_sequence": sequence,
                  "episode_observed_at": annotation.get("episode_observed_at", "unknown"),
                  "update_of": update_of,
                  "resolution_status": annotation.get("resolution_status", "unknown"),
                  "resolution_observed_at": annotation.get("resolution_observed_at", "unknown"),
                  "observed_language": annotation.get("observed_language", "unknown"),
                  "author_geography": annotation.get("author_geography", "unknown"),
                  "author_geography_basis": annotation.get("author_geography_basis", "unknown"),
                  "translation": annotation.get("translation"),
                  "author_voice_status": "supplier_context" if explicit_supplier else "unresolved",
                  "source_role": "competitor_context" if explicit_supplier else "community_context",
                  "classification_basis": "explicit_supplier_identity" if explicit_supplier else "extraction_proposal",
                  "source_intent": "competitor_content" if explicit_supplier else "forum_discussion",
                  "independence_key": "unknown:" + ident}
        # Never copy a document-level acceptance onto one of its proposed voices.
        result.pop("analyst_review", None); result.pop("_source_review", None)
        if role in {"quoted_other", "unresolved"}:
            result["author_voice_status"] = "non_customer"
            result["source_role"] = "quoted_context" if role == "quoted_other" else "unresolved_context"
        if result["author_geography"] != "unknown" and result["author_geography_basis"] == "unknown":
            raise ValueError("author geography needs evidence; collection locale is not residence")
        if result["translation"] and (not isinstance(result["translation"], dict) or result["translation"].get("original_quote") != quote):
            raise ValueError("translation must link to complete original_quote")
        output.append(result)
    return output


def comparison_view(experiences: list[dict]) -> dict:
    """Generated episode comparison grouped by source-local speaker and incident."""
    rows = sorted(experiences, key=lambda row: (
        str(row.get("speaker_id", "")), str(row.get("incident_id") or ""),
        row.get("episode_sequence") if type(row.get("episode_sequence")) is int else -1,
        str(row.get("episode_observed_at", "")), str(row.get("evidence_id", ""))))
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = str(row.get("incident_id") or row.get("speaker_id") or "unresolved")
        groups.setdefault(key, []).append({
            "evidence_id": row.get("evidence_id"), "document_id": row.get("document_id"),
            "speaker_id": row.get("speaker_id"), "speaker_role_proposal": row.get("speaker_role_proposal"),
            "episode_sequence": row.get("episode_sequence"), "episode_observed_at": row.get("episode_observed_at"),
            "update_of": row.get("update_of"), "resolution_status": row.get("resolution_status"),
            "resolution_observed_at": row.get("resolution_observed_at"), "text": row.get("text"),
            "observations": row.get("observations", {}),
        })
    return {"generated_view": True, "authority": "experience ledger and reviewed sources", "groups": groups}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--comparison-out", type=Path, help="Optional generated episode-by-episode comparison JSON; edits do not alter evidence.")
    args = parser.parse_args()
    try:
        documents = [json.loads(line) for line in args.documents.read_text().splitlines() if line.strip()]
        rows = build(documents, json.loads(args.annotations.read_text()))
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    if args.comparison_out:
        args.comparison_out.parent.mkdir(parents=True, exist_ok=True)
        args.comparison_out.write_text(json.dumps(comparison_view(rows), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents": len(documents), "experiences": len(rows), "review_status": "unreviewed", "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
