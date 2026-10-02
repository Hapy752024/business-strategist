#!/usr/bin/env python3
"""Build a non-authoritative view of reviewed evidence yield by planned scope."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(plan: dict, evidence: list[dict], reviews: list[dict], execution_ledger: list[dict] | None = None) -> dict:
    review_by_id = {row.get("evidence_id"): row for row in reviews if isinstance(row, dict)}
    query_by_id = {row.get("query_id"): row for row in plan.get("input_plan", {}).get("queries", [])}
    cells = {}

    def cell_for(query: dict) -> dict:
        key = str(query.get("cell_id") or query.get("query_id") or "unassigned")
        return cells.setdefault(key, {"cell_id": key, "locale": query.get("locale", "unknown"),
            "role": query.get("role", "unknown"), "job": query.get("job", "unknown"),
            "source_family": query.get("source_family", "unknown"), "intent": query.get("intent", "unknown"),
            "records": set(), "reviewed": set(), "accepted": set(), "target": set(),
            "adjacent": set(), "rejected": set(), "origins": set()})

    # Plan-first initialization keeps planned zero-result and unattempted cells visible.
    for query in query_by_id.values():
        cell_for(query)
    for record in evidence:
        memberships = record.get("discovery_memberships", [])
        queries = [query_by_id.get(item.get("query_id")) for item in memberships if isinstance(item, dict)]
        queries = [row for row in queries if isinstance(row, dict)]
        if not queries:
            queries = [{"query_id": "unassigned", "locale": record.get("collection_locale", "unknown"),
                        "source_family": record.get("retrieval_backend", record.get("source", "unknown")),
                        "intent": record.get("source_intent", "unknown")}]
        review = review_by_id.get(record.get("evidence_id"), {})
        accepted = review.get("status") == "accepted"
        rejected = review.get("status") in {"rejected", "not_customer", "adjacent_rejected"}
        for query in queries:
            row = cell_for(query)
            ident = str(record.get("evidence_id") or "")
            if not ident:
                continue
            row["records"].add(ident)
            if review:
                row["reviewed"].add(ident)
            if accepted:
                row["accepted"].add(ident)
                if review.get("voice") == "customer" and review.get("segment_relation") == "target":
                    row["target"].add(ident)
                elif review.get("segment_relation") in {"adjacent", "unresolved"}:
                    row["adjacent"].add(ident)
            if rejected:
                row["rejected"].add(ident)
            row["origins"].add(str(record.get("source_url") or "unknown"))
    execution_by_query = {}
    for item in execution_ledger or []:
        if isinstance(item, dict) and item.get("query_id"):
            raw_status = str(item.get("status", "execution_unknown"))
            if raw_status.startswith("not_attempted"):
                reason = raw_status.partition(":")[2]
                status = "access_failed" if reason in {"missing_credentials", "access_failed", "provider_unavailable"} else "not_attempted"
            elif item.get("attempted") is False:
                status = "not_attempted"
            elif raw_status in {"ok", "partial"}:
                returned = item.get("returned_count")
                retained = item.get("record_ids") or item.get("evidence_ids") or []
                status = ("returned_zero" if returned == 0 else
                          "returned_but_not_retained" if isinstance(returned, int) and returned > 0 and not retained else
                          "returned" if isinstance(returned, int) and returned > 0 else "execution_unknown")
            elif raw_status in {"returned_zero", "returned_but_not_retained", "access_failed", "not_attempted"}:
                status = raw_status
            elif raw_status == "execution_unknown":
                status = raw_status
            else:
                status = "access_failed"
            normalized = {**item, "normalized_status": status}
            execution_by_query.setdefault(str(item["query_id"]), []).append(normalized)
    output = []
    for key, row in sorted(cells.items()):
        query_ids = [str(qid) for qid, query in query_by_id.items()
                     if str(query.get("cell_id") or query.get("query_id") or "unassigned") == key]
        attempts = [item for qid in query_ids for item in execution_by_query.get(qid, [])]
        statuses = sorted({str(item.get("normalized_status", "execution_unknown")) for item in attempts})
        if not attempts:
            statuses = ["execution_unknown"] if execution_ledger is None else ["not_attempted"]
        row_status = ("awaiting_review" if row["records"] and len(row["reviewed"]) < len(row["records"])
                      else "reviewed" if row["records"] and row["reviewed"]
                      else "mixed" if len(statuses) > 1
                      else "returned_but_not_retained" if any(s == "returned_but_not_retained" for s in statuses)
                      else "returned_zero" if statuses and all(s == "returned_zero" for s in statuses)
                      else "access_failed" if statuses and all(s == "access_failed" for s in statuses)
                      else "returned" if statuses and all(s == "returned" for s in statuses)
                      else "not_attempted" if statuses == ["not_attempted"] else "execution_unknown")
        if len(row["reviewed"]) < len(row["records"]):
            next_step = "Review retained original sources and the rejection sample."
        elif not row["target"]:
            next_step = "Refine the query/source frame or record a specific primary-research handoff; no target-user voice is established."
        else:
            next_step = "Synthesize target episodes and contrary cases, then check the remaining planned cells."
        output.append({**{name: value for name, value in row.items() if name not in {"records", "reviewed", "accepted", "target", "adjacent", "rejected", "origins"}},
            "retrieved_record_count": len(row["records"]), "reviewed_record_count": len(row["reviewed"]),
            "accepted_review_count": len(row["accepted"]), "rejected_review_count": len(row["rejected"]),
            "accepted_target_record_count": len(row["target"]),
            "accepted_adjacent_or_unresolved_record_count": len(row["adjacent"]),
            "distinct_source_urls": len(row["origins"]),
            "evidence_ids": sorted(row["records"]), "reviewed_ids": sorted(row["reviewed"]),
            "accepted_ids": sorted(row["accepted"]), "rejected_ids": sorted(row["rejected"]),
            "execution_statuses": statuses, "cell_status": row_status,
            "next_step": next_step,
            "independent_episode_count": None,
            "independence_note": "Source URLs and records are not customer episodes; distinct episodes require the reviewed experience ledger."})
    return {"generated_view": True, "authority": "query plan, capture records and source review",
        "interpretation_boundary": "This report prioritizes further review/search. It does not establish demand, prevalence, saturation or independent customers.",
        "cells": output}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-review", type=Path, required=True)
    parser.add_argument("--execution-ledger", type=Path, help="Optional provider query outcomes JSON.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        evidence = [json.loads(line) for line in args.evidence.read_text(encoding="utf-8").splitlines() if line.strip()]
        reviews = json.loads(args.source_review.read_text(encoding="utf-8")).get("reviews", [])
        execution = json.loads(args.execution_ledger.read_text(encoding="utf-8")) if args.execution_ledger else None
        if isinstance(execution, dict):
            if isinstance(execution.get("queries"), list):
                execution = execution["queries"]
            elif isinstance(execution.get("query_ledger"), list):
                execution = execution["query_ledger"]
            else:
                providers = execution.get("providers", execution)
                execution = [query for provider in providers.values() if isinstance(provider, dict)
                             for query in provider.get("query_ledger", []) if isinstance(query, dict)]
        if execution is not None and not isinstance(execution, list):
            raise ValueError("execution ledger must be a query list or collector summary with provider query_ledger entries")
        result = build(plan, evidence, reviews, execution)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "generated", "cells": len(result["cells"]), "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
