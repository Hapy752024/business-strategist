#!/usr/bin/env python3
"""Write the claims-only input for the claim-falsifier agent from a reviewed claim ledger.

Fields are allow-listed: supporting/counter evidence, rationale, verification passages and
independence keys never reach the falsifier, so it cannot anchor on the original findings.

Without a reviewed ledger, `--draft-claims <json>` (schemas/draft-claims.schema.json: claims the
agent extracted from its draft business case or insights) is the fallback. Every draft claim is
exported, without its sources, and labelled `basis: "draft"`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
DRAFT_SCHEMA = ROOT / "schemas/draft-claims.schema.json"

ALLOWED_FIELDS = {"claim_id", "claim", "claim_type", "claim_scope_type", "scope", "geography", "segment", "freshness"}
# Demand, willingness-to-pay and market-size style claims; competition/regulation claims are
# material through `decision_affected`, since the claim-type enum has no such values.
MATERIAL_TYPES = {"willingness_to_pay", "prevalence", "unmetness", "pattern", "transfer"}


def is_material(record: dict[str, Any]) -> bool:
    if str(record.get("decision_affected") or "").strip():
        return True
    return bool({record.get("claim_type"), record.get("claim_scope_type")} & MATERIAL_TYPES)


def load_ledger(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) and row.get("claim_id") for row in rows):
        raise ValueError(f"{path}: claim ledger must be a JSON array of records with claim_id")
    ids = [str(row["claim_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: claim ids must be unique")
    return rows


def load_draft_claims(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(json.loads(DRAFT_SCHEMA.read_text(encoding="utf-8")))
    errors = sorted(validator.iter_errors(rows), key=lambda e: list(map(str, e.absolute_path)))
    if errors:
        where = "/".join(map(str, errors[0].absolute_path)) or "<root>"
        raise ValueError(f"{path}: draft claims do not match schemas/draft-claims.schema.json at {where}: {errors[0].message}")
    ids = [row["claim_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: claim ids must be unique")
    return rows


def export_draft(draft: Path, output: Path, search_budget: int = 3) -> dict[str, Any]:
    if not 1 <= search_budget <= 10:
        raise ValueError("search_budget must be between 1 and 10")
    claims = [{"claim_id": row["claim_id"], "claim": row["text"], "section": row["section"], "basis": "draft"}
              for row in load_draft_claims(draft)]
    payload = {"schema_version": 1, "basis": "draft", "search_budget_per_claim": search_budget, "claims": claims}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"claims": len(claims), "output": str(output), "basis": "draft"}


def export(ledger: Path, output: Path, search_budget: int = 3, material_only: bool = True) -> dict[str, Any]:
    if not 1 <= search_budget <= 10:
        raise ValueError("search_budget must be between 1 and 10")
    rows = [row for row in load_ledger(ledger) if not material_only or is_material(row)]
    claims = [{key: row[key] for key in sorted(ALLOWED_FIELDS) if key in row} for row in rows]
    payload = {"schema_version": 1, "search_budget_per_claim": search_budget, "claims": claims}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"claims": len(claims), "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ledger", type=Path, help="reviewed claim-ledger.json (preferred when it exists)")
    source.add_argument("--draft-claims", type=Path, help="fallback without a ledger: draft claims JSON; output basis: draft")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--search-budget", type=int, default=3, help="Disconfirming searches per claim (1-10)")
    parser.add_argument("--all", action="store_true", help="Export every claim, not only material ones")
    args = parser.parse_args()
    try:
        result = (export_draft(args.draft_claims, args.output, args.search_budget) if args.draft_claims
                  else export(args.ledger, args.output, args.search_budget, material_only=not args.all))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
