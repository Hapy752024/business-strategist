#!/usr/bin/env python3
"""Build a read-only, source-linked review packet from existing research artifacts."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def build(plan: dict, evidence: list[dict], annotations: list[dict], reviews: list[dict], closeout: dict,
          evidence_ids: list[str] | None = None, limit: int = 30) -> dict:
    by_id = {str(row.get("evidence_id")): row for row in evidence if row.get("evidence_id")}
    ann: dict[str, list[dict]] = defaultdict(list)
    for row in annotations:
        if not isinstance(row, dict):
            continue
        document_id = row.get("document_id") or row.get("evidence_id")
        if not document_id:
            continue
        proposals = row.get("annotations", row.get("spans"))
        if isinstance(proposals, list):
            ann[str(document_id)].extend(s for s in proposals if isinstance(s, dict))
        else:
            ann[str(document_id)].append(row)
    rev = {str(row.get("evidence_id")): row for row in reviews if row.get("evidence_id")}
    ids = list(dict.fromkeys(evidence_ids or list(by_id)))
    ids = [ident for ident in ids if ident in by_id][:max(0, limit)]
    items = []
    for ident in ids:
        record, proposals, review = by_id[ident], ann.get(ident, []), rev.get(ident, {})
        text = str(record.get("text", ""))
        spans = []
        for proposal in proposals:
            start, end = proposal.get("start"), proposal.get("end")
            valid_span = type(start) is int and type(end) is int and 0 <= start < end <= len(text)
            quote = text[start:end] if valid_span else None
            spans.append({"start": start, "end": end, "quote": quote,
                          "quote_matches_proposal": quote is not None and proposal.get("quote") == quote,
                          "proposal": proposal})
        items.append({"evidence_id": ident, "source_url": record.get("source_url"),
                      "source": record.get("source"), "text": text,
                      "annotations": spans,
                      "review_status": review.get("status", "unreviewed"),
                      "review": review, "sampling_frame": record.get("sampling_frame")})
    return {"generated_view": True, "read_only": True,
            "authority": "original evidence, annotations, source review and research closeout",
            "closeout": closeout, "planned_queries": plan.get("input_plan", {}).get("queries", []),
            "items": items,
            "warning": "Packet creation does not accept evidence or annotations. Review original source context before changing existing review artifacts."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "evidence", "annotations", "source-review", "closeout", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--ids", default="", help="Comma-separated exact evidence IDs; defaults to file order.")
    p.add_argument("--limit", type=int, default=30)
    a = p.parse_args()
    load_json = lambda path: json.loads(path.read_text(encoding="utf-8"))
    def load_jsonl(path): return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    plan, evidence = load_json(a.plan), load_jsonl(a.evidence)
    annotation_data = load_json(a.annotations)
    annotations = annotation_data if isinstance(annotation_data, list) else annotation_data.get("annotations", [])
    reviews = load_json(a.source_review).get("reviews", [])
    closeout = load_json(a.closeout)
    result = build(plan, evidence, annotations, reviews, closeout,
                   [x for x in a.ids.split(",") if x] or None, a.limit)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__": raise SystemExit(main())
