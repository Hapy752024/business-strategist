#!/usr/bin/env python3
"""Compare independently frozen source labels with a reviewer assessment.

This script measures disagreement; it does not decide whether a source supports
a business claim and is not a research or publication approval authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

LABELS = {"supported", "unsupported", "uncertain", "omission"}


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        raise ValueError(f"{path} needs an items list")
    return value


def _index(rows: list, label: str, field: str) -> dict:
    indexed = {}
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]
                or row["id"] in indexed or row.get(field) not in LABELS):
            raise ValueError(f"{label} has missing/duplicate ID or invalid label")
        indexed[row["id"]] = row
    return indexed


def score(gold_path: Path, assessment_path: Path) -> dict:
    gold_bytes = gold_path.read_bytes()
    gold = _index(_read(gold_path)["items"], "gold", "expected")
    assessment_packet = _read(assessment_path)
    assessment = _index(assessment_packet["items"], "assessment", "observed")
    if set(gold) != set(assessment):
        raise ValueError("assessment IDs must exactly equal frozen gold IDs")
    if assessment_packet.get("gold_sha256") != hashlib.sha256(gold_bytes).hexdigest():
        raise ValueError("assessment is not bound to this frozen gold file")
    if not isinstance(assessment_packet.get("reviewer"), str) or not assessment_packet["reviewer"].strip():
        raise ValueError("assessment needs a named reviewer")
    disagreements = []
    planted_false_accepts = []
    for ident in sorted(gold):
        expected = gold[ident]["expected"]
        observed = assessment[ident]["observed"]
        if not isinstance(assessment[ident].get("rationale"), str) or not assessment[ident]["rationale"].strip():
            raise ValueError(f"{ident}: assessment needs evidence-bearing rationale")
        if expected != observed:
            disagreements.append({"id": ident, "expected": expected, "observed": observed,
                                  "material": gold[ident].get("material") is True})
        if gold[ident].get("planted_error") is True and expected in {"unsupported", "omission"} and observed == "supported":
            planted_false_accepts.append(ident)
    return {"gold_sha256": hashlib.sha256(gold_bytes).hexdigest(),
            "assessment_sha256": hashlib.sha256(assessment_path.read_bytes()).hexdigest(),
            "reviewer": assessment_packet["reviewer"], "item_count": len(gold),
            "material_disagreement_count": sum(row["material"] for row in disagreements),
            "disagreements": disagreements, "planted_false_accepts": planted_false_accepts,
            "evaluator_ready_for_live_scoring": not planted_false_accepts and not any(
                row["material"] for row in disagreements),
            "boundary": "Label comparison only; independent source inspection and exact report review remain necessary."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--assessment", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = score(args.gold, args.assessment)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered)
    return 0 if result["evaluator_ready_for_live_scoring"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
