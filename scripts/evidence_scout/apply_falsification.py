#!/usr/bin/env python3
"""Apply untrusted claim-falsifier verdicts to a copy of a reviewed claim ledger.

The reviewed ledger is never rewritten. Outputs, beside it:
- claim-ledger.falsified.json: publishable claims plus quarantined (falsified) claims with reasons
- falsification-report.json / falsification-report.md: per-claim verdict, evidence, searches and action

falsified -> quarantined (excluded from publishable claims, not deleted)
weakened  -> confidence downgraded one level (high > medium > low > unresolved)
survived  -> unchanged; means only "no disconfirming evidence found within N searches"
inconclusive -> unchanged
No verdict can raise confidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

try:
    from scripts.evidence_scout.export_claims_for_falsification import is_material, load_ledger
except ModuleNotFoundError:  # direct script execution
    from export_claims_for_falsification import is_material, load_ledger

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/falsification-verdicts.schema.json"
LEVELS = ["unresolved", "low", "medium", "high"]
SURVIVED_PHRASE = re.compile(r"no disconfirming evidence found within (\d+) searches", re.I)
CONFIRMATION_WORDS = re.compile(r"\b(confirm|verif|validat)", re.I)
LEDGER_NAME = "claim-ledger.falsified.json"
REPORT_NAME = "falsification-report"


class FalsificationInputError(ValueError):
    """Verdict input failed validation; nothing was written."""


def _rank(level: Any) -> int:
    return LEVELS.index(level) if level in LEVELS else 0


def downgrade(level: str) -> str:
    return LEVELS[max(_rank(level) - 1, 0)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_verdicts(data: Any, ledger: dict[str, dict[str, Any]], exported: set[str]) -> list[str]:
    """Return all problems with an untrusted verdict file; empty means accepted."""
    validator = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    errors = []
    for e in sorted(validator.iter_errors(data), key=lambda e: list(map(str, e.absolute_path))):
        where = "/".join(map(str, e.absolute_path)) or "<root>"
        if e.validator == "minItems" and e.absolute_path and e.absolute_path[-1] == "evidence":
            errors.append(f"{where}: falsified/weakened verdicts require at least one dated evidence item")
        else:
            errors.append(f"schema: {where}: {e.message}")
    if errors:
        return errors
    seen: set[str] = set()
    for item in data["verdicts"]:
        cid = item["claim_id"]
        if cid in seen:
            errors.append(f"duplicate verdict for claim id {cid}")
        seen.add(cid)
        if cid not in ledger:
            errors.append(f"unknown claim id {cid}: not in the reviewed ledger")
            continue
        if cid not in exported:
            errors.append(f"claim id {cid} was not in the exported claims set given to the falsifier")
        current = ledger[cid].get("confidence")
        proposed = item.get("proposed_confidence")
        if proposed is not None and _rank(proposed) > _rank(current):
            errors.append(f"{cid}: verdict tries to upgrade confidence {current} -> {proposed}; falsification never upgrades")
        if item["verdict"] == "survived":
            match = SURVIVED_PHRASE.search(item["rationale"])
            if not match:
                errors.append(f"{cid}: survived rationale must state 'no disconfirming evidence found within N searches', not confirmation")
            elif int(match.group(1)) != len(item["searches_run"]):
                errors.append(f"{cid}: survived rationale says {match.group(1)} searches but searches_run lists {len(item['searches_run'])}")
            if CONFIRMATION_WORDS.search(item["rationale"]):
                errors.append(f"{cid}: survived rationale must not claim confirmation, verification or validation")
    return errors


def _note(rationale: str, text: str) -> str:
    return f"{rationale.rstrip()} Falsification: {text}".strip()


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Claim falsification report", "",
        f"Checked at {report['checked_at']}; budget {report['search_budget_per_claim']} searches per claim.",
        "`survived` means no disconfirming evidence was found within the search budget. It does not confirm a claim or raise its confidence.", "",
        "| Claim | Verdict | Action | Confidence | Evidence |", "|---|---|---|---|---|",
    ]
    for row in report["claims"]:
        ev = "; ".join(f"[{e['date']}]({e['url']})" for e in row["evidence"]) or "none"
        lines.append(f"| {row['claim_id']} | {row['verdict']} | {row['action']} | {row['confidence_before']} -> {row['confidence_after']} | {ev} |")
    for row in report["claims"]:
        if row["evidence"]:
            lines += ["", f"## {row['claim_id']}: {row['verdict']}", "", row["claim"], ""]
            lines += [f"- {e['date']} {e['url']}: \"{e['quote']}\"" for e in row["evidence"]]
    if report["not_checked"]:
        lines += ["", "Not checked: " + ", ".join(report["not_checked"])]
    if report["warnings"]:
        lines += ["", "Warnings:"] + [f"- {w}" for w in report["warnings"]]
    return "\n".join(lines) + "\n"


def exported_ids(claims_export: Path | None, rows: list[dict[str, Any]]) -> set[str]:
    """Claim ids the falsifier was given: from the export file, else recomputed materiality."""
    if claims_export is None:
        return {str(row["claim_id"]) for row in rows if is_material(row)}
    data = json.loads(Path(claims_export).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise FalsificationInputError(f"{claims_export}: not a falsification claims export")
    return {str(row.get("claim_id")) for row in data["claims"] if isinstance(row, dict)}


def apply(ledger: Path, verdicts: Path, out_dir: Path | None = None, checked_at: str | None = None,
          claims_export: Path | None = None) -> dict[str, Any]:
    ledger, verdicts = Path(ledger), Path(verdicts)
    rows = load_ledger(ledger)
    by_id = {str(row["claim_id"]): row for row in rows}
    exported = exported_ids(claims_export, rows)
    try:
        data = json.loads(verdicts.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FalsificationInputError(f"verdict file is not valid JSON: {exc}") from exc
    errors = validate_verdicts(data, by_id, exported)
    if errors:
        raise FalsificationInputError("rejected verdicts:\n- " + "\n- ".join(errors))

    checked_at = checked_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    budget = data["search_budget_per_claim"]
    verdict_by_id = {item["claim_id"]: item for item in data["verdicts"]}
    publishable, quarantined, entries, warnings = [], [], [], []
    for source in rows:
        cid = str(source["claim_id"])
        row = copy.deepcopy(source)
        item = verdict_by_id.get(cid)
        if item is None:
            publishable.append(row)
            continue
        before = row.get("confidence")
        kind = item["verdict"]
        if len(item["searches_run"]) > budget:
            warnings.append(f"{cid}: {len(item['searches_run'])} searches exceed the stated budget of {budget}")
        if kind == "falsified":
            action, after = "quarantined", before
            quarantined.append({"claim": row, "reason": f"falsified by adversarial search on {checked_at}: {item['rationale']}",
                                "evidence": item["evidence"]})
        elif kind == "weakened":
            after = downgrade(before)
            action = f"downgraded {before} -> {after}"
            row["confidence"] = after
            row["confidence_rationale"] = _note(row.get("confidence_rationale", ""), f"weakened on {checked_at}; downgraded {before} -> {after}.")
            publishable.append(row)
        else:
            after = before
            action = "unchanged (no upgrade)" if kind == "survived" else "unchanged (inconclusive)"
            publishable.append(row)
        entries.append({
            "claim_id": cid, "claim": row.get("claim", ""), "verdict": kind, "evidence": item["evidence"],
            "searches_run": item["searches_run"], "rationale": item["rationale"],
            "falsification_checked_at": checked_at, "action": action,
            "confidence_before": before, "confidence_after": after,
        })

    out_dir = Path(out_dir) if out_dir else ledger.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {k: sum(1 for e in entries if e["verdict"] == k) for k in ("falsified", "weakened", "survived", "inconclusive")}
    provenance = {"source_ledger": str(ledger), "source_ledger_sha256": _sha256(ledger),
                  "verdicts_sha256": _sha256(verdicts), "checked_at": checked_at}
    outputs = {"ledger": str(out_dir / LEDGER_NAME), "report_json": str(out_dir / f"{REPORT_NAME}.json"),
               "report_md": str(out_dir / f"{REPORT_NAME}.md")}
    report = {"schema_version": 1, **provenance, "search_budget_per_claim": budget, "counts": counts,
              "claims": entries, "not_checked": sorted(exported - verdict_by_id.keys()),
              "warnings": warnings, "outputs": outputs}
    falsified_ledger = {"schema_version": 1, **provenance, "claims": publishable, "quarantined": quarantined}
    if Path(outputs["ledger"]).resolve() == ledger.resolve():
        raise FalsificationInputError("refusing to overwrite the reviewed ledger")
    Path(outputs["ledger"]).write_text(json.dumps(falsified_ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(outputs["report_json"]).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(outputs["report_md"]).write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ledger", type=Path, required=True, help="Reviewed claim-ledger.json (read only)")
    parser.add_argument("--verdicts", type=Path, required=True, help="claim-falsifier JSON output (untrusted)")
    parser.add_argument("--claims", type=Path, help="The falsification-claims.json export given to the agent (default: recompute material claims)")
    parser.add_argument("--out-dir", type=Path, help="Defaults to the ledger's directory")
    args = parser.parse_args()
    try:
        report = apply(args.ledger, args.verdicts, args.out_dir, claims_export=args.claims)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"counts": report["counts"], "not_checked": len(report["not_checked"]), "outputs": report["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
