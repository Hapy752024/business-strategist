"""Normalize supplied aggregate marketing exports without retaining lead-level data."""
from __future__ import annotations

import csv
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

ALLOWED = {"property", "source", "period_start", "period_end", "timezone", "query", "page", "dimension", "metric", "unit", "value", "availability", "denominator", "exported_at"}


def normalize(path: Path, mapping: dict[str, str], metadata: dict) -> dict:
    raw = path.read_bytes()
    if set(mapping) - ALLOWED:
        raise ValueError("mapping contains unsupported fields")
    if not {"property", "source", "period_start", "period_end", "timezone", "metric", "unit", "value"} <= set(mapping):
        raise ValueError("property, source, period, timezone, metric, unit and value mappings are required")
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    elif path.suffix.lower() == ".json":
        payload = json.loads(raw)
        rows = payload if isinstance(payload, list) else payload.get("rows", [])
    else:
        raise ValueError("only local CSV and JSON exports are supported")
    observations = []
    for index, row in enumerate(rows):
        item = {key: row.get(column) for key, column in mapping.items()}
        item.update({k: metadata.get(k) for k in ("property", "source", "period_start", "period_end", "timezone") if not item.get(k)})
        if not all(item.get(k) for k in ("property", "source", "period_start", "period_end", "timezone", "metric", "unit")):
            raise ValueError(f"row {index + 1}: required context is missing")
        exported_at = item.get("exported_at") or metadata.get("exported_at")
        if not exported_at:
            raise ValueError(f"row {index + 1}: export date is required")
        if str(item.get("availability") or "available").lower() in {"unavailable", "suppressed", "not available", "na"}:
            value = None
            availability = "unavailable"
        else:
            value_raw = item.get("value")
            if value_raw in (None, ""):
                value, availability = None, "unknown"
            else:
                try: value = float(value_raw)
                except (TypeError, ValueError) as exc: raise ValueError(f"row {index + 1}: value must be numeric or blank") from exc
                availability = "available"
        # Only whitelisted aggregate dimensions survive normalization.
        denominator = None
        if mapping.get("denominator"):
            try: denominator = float(row.get(mapping["denominator"])) if row.get(mapping["denominator"]) not in (None, "") else None
            except (TypeError, ValueError) as exc: raise ValueError(f"row {index + 1}: denominator must be numeric or blank") from exc
        observations.append({key: item.get(key) for key in ("property", "source", "period_start", "period_end", "timezone", "query", "page", "dimension", "metric", "unit")} |
                            {"value": value, "availability": availability, "denominator": denominator, "exported_at": exported_at})
    return {"schema_version": 1, "input_sha256": hashlib.sha256(raw).hexdigest(),
            "row_count": len(observations), "observations": observations,
            "interpretation_boundary": "Aggregate export normalization does not establish attribution or causal uplift."}


def compare(before: dict, after: dict) -> dict:
    """Compare matching aggregate measures only; report observed change without causal language."""
    def duration(row):
        try: return (date.fromisoformat(row["period_end"]) - date.fromisoformat(row["period_start"])).days
        except (KeyError, ValueError): return None
    def key(row):
        return tuple(row.get(k) for k in ("property", "source", "timezone", "query", "page", "dimension", "metric", "unit"))
    def group(rows):
        grouped = {}
        for row in rows:
            grouped.setdefault(key(row), []).append(row)
        return grouped
    left = group(before.get("observations", []))
    right = group(after.get("observations", []))
    results = []
    for ident in sorted(set(left) | set(right), key=str):
        left_rows, right_rows = left.get(ident, []), right.get(ident, [])
        if len(left_rows) > 1 or len(right_rows) > 1:
            results.append({"key": list(ident), "status": "non_comparable",
                            "reason": "multiple rows share this metric and dimension; aggregate with metric-specific rules before comparison",
                            "before_row_count": len(left_rows), "after_row_count": len(right_rows)}); continue
        a, b = (left_rows[0] if left_rows else None), (right_rows[0] if right_rows else None)
        if a is None or b is None:
            results.append({"key": ident, "status": "non_comparable", "reason": "metric/dimension is missing from one export"}); continue
        if duration(a) is None or duration(a) != duration(b):
            results.append({"key": ident, "status": "non_comparable", "reason": "observation windows have different or unknown durations"}); continue
        if a["availability"] != "available" or b["availability"] != "available":
            results.append({"key": ident, "status": "unknown", "reason": "one or both values are unavailable"}); continue
        results.append({"key": list(ident), "status": "observed_change", "before_period": [a["period_start"], a["period_end"]],
                        "after_period": [b["period_start"], b["period_end"]], "before": a["value"], "after": b["value"],
                        "difference": b["value"] - a["value"], "before_denominator": a.get("denominator"),
                        "after_denominator": b.get("denominator"), "causal_attribution": "not_established"})
    return {"results": results, "interpretation_boundary": "Observed changes are descriptive; confounders and attribution require separate review."}


def decision_record(*, action_id: str, before: dict, after: dict, changed_at: str,
                    expected_effect: str, applied_change: str, confounders: list[str],
                    limitations: list[str], next_decision: str) -> dict:
    """Bind a page change to two exports and a bounded follow-up decision."""
    if not all(str(value).strip() for value in (action_id, changed_at, expected_effect, applied_change)):
        raise ValueError("action, change date, expected effect and applied change are required")
    if next_decision not in {"continue", "change", "stop", "collect_more_data"}:
        raise ValueError("next_decision must be continue, change, stop or collect_more_data")
    from datetime import date as _date
    change_date = _date.fromisoformat(changed_at)
    for report, name in ((before, "baseline"), (after, "follow-up")):
        if not report.get("input_sha256"):
            raise ValueError(f"{name} export digest is required")
    for row in before.get("observations", []):
        if _date.fromisoformat(row["period_end"]) > change_date:
            raise ValueError("baseline window must end on or before the applied change")
    for row in after.get("observations", []):
        if _date.fromisoformat(row["period_start"]) <= change_date:
            raise ValueError("follow-up window must start after the applied change")
    return {"action_id": action_id, "expected_effect": expected_effect, "applied_change": applied_change,
            "changed_at": changed_at, "baseline_sha256": before["input_sha256"], "followup_sha256": after["input_sha256"],
            "comparison": compare(before, after), "confounders": confounders, "limitations": limitations,
            "next_decision": next_decision, "causal_claim": "not_established"}


def decision_record_is_current(record: dict, before: dict, after: dict) -> bool:
    return record.get("baseline_sha256") == before.get("input_sha256") and record.get("followup_sha256") == after.get("input_sha256")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Local CSV/JSON aggregate export.")
    parser.add_argument("--mapping", type=Path, required=True, help="JSON normalized-field to source-column mapping.")
    parser.add_argument("--metadata", type=Path, required=True, help="JSON property/source/window/timezone/exported_at context.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, help="Previously normalized baseline export JSON.")
    parser.add_argument("--action-id")
    parser.add_argument("--changed-at")
    parser.add_argument("--expected-effect")
    parser.add_argument("--applied-change")
    parser.add_argument("--confounder", action="append", default=[])
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--next-decision", choices=("continue", "change", "stop", "collect_more_data"))
    args = parser.parse_args()
    report = normalize(args.input, json.loads(args.mapping.read_text(encoding="utf-8")),
                       json.loads(args.metadata.read_text(encoding="utf-8")))
    result = report
    if args.baseline:
        required = (args.action_id, args.changed_at, args.expected_effect, args.applied_change, args.next_decision)
        if not all(required): parser.error("comparison requires action, change date, expected effect, applied change and next decision")
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        result = decision_record(action_id=args.action_id, before=baseline, after=report, changed_at=args.changed_at,
            expected_effect=args.expected_effect, applied_change=args.applied_change,
            confounders=args.confounder, limitations=args.limitation, next_decision=args.next_decision)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status":"generated", "input_sha256":report["input_sha256"], "out":str(args.out)}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
