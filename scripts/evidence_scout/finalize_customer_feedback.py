#!/usr/bin/env python3
"""Validate VOC evidence accounting without confusing missing coverage with invalid evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _counts(row: dict[str, Any], label: str, errors: list[str], *, topic: bool = False,
            require_ids: bool = True) -> tuple[list[int], list[str]]:
    accepted_name = "accepted_count" if topic else "accepted_customer_voice_count"
    values = [row.get(name, 0) for name in ("retrieved_count", "reviewed_count", accepted_name)]
    if any(type(value) is not int or value < 0 for value in values):
        errors.append(f"{label}: counts must be non-negative integers")
        values = [0, 0, 0]
    elif not values[2] <= values[1] <= values[0]:
        errors.append(f"{label}: counts require accepted <= reviewed <= retrieved")
    ids = row.get("accepted_evidence_ids", [])
    if not isinstance(ids, list) or any(not isinstance(item, str) or not item.strip() for item in ids):
        errors.append(f"{label}: accepted_evidence_ids must be a list of non-empty strings")
        ids = []
    elif len(ids) != len(set(ids)) or (require_ids and len(ids) != values[2]):
        errors.append(f"{label}: accepted_evidence_ids must be unique and reconcile to accepted count")
    if any(values) and row.get("attempted") is not True:
        errors.append(f"{label}: retrieved/reviewed/accepted evidence requires an attempted capture")
    return values, ids


def _review_accounting(row: dict[str, Any], label: str, errors: list[str], *,
                       population_ids: list[str] | None = None) -> tuple[bool, list[str]]:
    """Validate a bounded review declaration; counts alone never excuse unseen records."""
    retrieved = row.get("retrieved_count", 0)
    reviewed = row.get("reviewed_count", 0)
    accepted = row.get("accepted_evidence_ids", [])
    if reviewed == retrieved:
        return True, list(accepted) if isinstance(accepted, list) else []
    sample = row.get("sampling")
    if not isinstance(sample, dict) or sample.get("version") != 1:
        errors.append(f"{label}: incomplete review requires a version-1 sampling declaration")
        return False, []
    required = {"version", "unit", "population_ids", "selected_ids", "excluded", "reviewed_ids",
                "method", "strata", "rejection_audit_ids", "limitations"}
    if set(sample) != required or sample.get("unit") not in {"observation", "episode"}:
        errors.append(f"{label}: sampling declaration has invalid fields or unit")
        return False, []
    population = sample.get("population_ids")
    selected = sample.get("selected_ids")
    reviewed_ids = sample.get("reviewed_ids")
    excluded = sample.get("excluded")
    strata = sample.get("strata")
    audit = sample.get("rejection_audit_ids")
    limitations = sample.get("limitations")
    method = sample.get("method")
    lists = (population, selected, reviewed_ids, excluded, strata, audit)
    if any(not isinstance(value, list) for value in lists):
        errors.append(f"{label}: sampling population, selections, strata and audit must be lists")
        return False, []
    if (not isinstance(method, str) or len(method.strip()) < 12
            or not isinstance(limitations, list) or any(not isinstance(x, str) or len(x.strip()) < 12 for x in limitations)):
        errors.append(f"{label}: sampling method and limitations must be explicit")
        return False, []
    if any(not isinstance(x, str) or not x.strip() for x in population + selected + reviewed_ids + audit):
        errors.append(f"{label}: sampling IDs must be non-empty strings")
        return False, []
    if len(population) != len(set(population)) or len(selected) != len(set(selected)) or len(reviewed_ids) != len(set(reviewed_ids)):
        errors.append(f"{label}: sampling IDs must be unique within each set")
        return False, []
    expected = population_ids if population_ids is not None else row.get("retrieved_evidence_ids")
    if not isinstance(expected, list) or set(population) != set(expected) or len(population) != retrieved:
        errors.append(f"{label}: sampling population must reconcile to exact retrieved IDs/count")
    if len(selected) != reviewed or set(reviewed_ids) != set(selected):
        errors.append(f"{label}: every selected item must be reviewed and match reviewed_count")
    if not set(accepted).issubset(set(reviewed_ids)):
        errors.append(f"{label}: accepted evidence must be within the reviewed sample")
    excluded_ids: list[str] = []
    for item in excluded:
        if (not isinstance(item, dict) or set(item) != {"evidence_id", "reason"}
                or not isinstance(item.get("evidence_id"), str) or not item["evidence_id"].strip()
                or not isinstance(item.get("reason"), str) or len(item["reason"].strip()) < 12):
            errors.append(f"{label}: each sampled-out item needs an ID and reason")
            continue
        excluded_ids.append(item["evidence_id"])
    if (len(excluded_ids) != len(set(excluded_ids)) or set(excluded_ids) & set(selected)
            or set(excluded_ids) | set(selected) != set(population)):
        errors.append(f"{label}: selected and sampled-out IDs must partition the retrieved population")
    if not set(audit).issubset(set(reviewed_ids)):
        errors.append(f"{label}: rejection audit IDs must be reviewed")
    if not strata or any(not isinstance(item, dict) or set(item) != {"name", "population_ids", "selected_ids"}
                         or not isinstance(item.get("name"), str) or not item["name"].strip()
                         or not isinstance(item.get("population_ids"), list)
                         or not isinstance(item.get("selected_ids"), list)
                         or any(not isinstance(value, str) or not value.strip()
                                for value in item.get("population_ids", []) + item.get("selected_ids", []))
                         or len(item.get("population_ids", [])) != len(set(item.get("population_ids", [])))
                         or len(item.get("selected_ids", [])) != len(set(item.get("selected_ids", [])))
                         or not set(item["selected_ids"]).issubset(set(item["population_ids"]))
                         for item in strata):
        errors.append(f"{label}: sampling strata must identify the populations and selections reviewed")
    else:
        stratum_population: list[str] = []
        stratum_selected: list[str] = []
        for item in strata:
            stratum_population.extend(item["population_ids"])
            stratum_selected.extend(item["selected_ids"])
        if (len(stratum_population) != len(set(stratum_population))
                or len(stratum_selected) != len(set(stratum_selected))
                or set(stratum_population) != set(population)
                or set(stratum_selected) != set(selected)):
            errors.append(f"{label}: strata must partition the full population and selected sample exactly")
    if population and (not selected or not audit):
        errors.append(f"{label}: bounded review requires a nonempty sample and reviewed rejection audit")
    return not any(error.startswith(f"{label}:") for error in errors), list(accepted)


def _outcome(row: dict[str, Any] | None) -> str:
    if row is None:
        return "pending"
    if str(row.get("failed_or_blocked") or "").strip():
        return "inaccessible" if row.get("access_status") == "inaccessible" else "failed_or_blocked"
    return "attempted" if row.get("attempted") is True else "pending"


def _search_resolution(row: dict[str, Any], label: str, errors: list[str]) -> str | None:
    """Require a decision after a low-yield cell without treating absence as no need."""
    value = row.get("search_resolution")
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"status", "reason", "query_ids", "next_observation"}:
        errors.append(f"{label}: search_resolution needs status, reason, query_ids and next_observation")
        return None
    status = value["status"]
    if status not in {"refine", "primary_research_needed", "access_limited"}:
        errors.append(f"{label}: invalid search_resolution status")
    if not isinstance(value["reason"], str) or len(value["reason"].strip()) < 20:
        errors.append(f"{label}: search_resolution needs a specific observed reason")
    if not isinstance(value["next_observation"], str) or len(value["next_observation"].strip()) < 20:
        errors.append(f"{label}: search_resolution needs a distinguishing next observation")
    ids = value["query_ids"]
    executed = row.get("query_ids")
    if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
            or not isinstance(executed, list) or not set(ids) <= set(executed)):
        errors.append(f"{label}: search_resolution query IDs must identify executed cell queries")
    if status == "access_limited" and _outcome(row) != "inaccessible":
        errors.append(f"{label}: access_limited requires an observed inaccessible result")
    return status if status in {"refine", "primary_research_needed", "access_limited"} else None


def _query_reviews(row: dict[str, Any], label: str, errors: list[str]) -> list[dict[str, Any]]:
    """Require one analyst decision for every executed query in a v4 target cell."""
    queries = row.get("query_ids", [])
    reviews = row.get("query_reviews")
    if not isinstance(queries, list) or not queries or len(queries) != len(set(queries)) or not isinstance(reviews, list):
        errors.append(f"{label}: v4 needs query IDs and per-query reviews")
        return []
    seen: set[str] = set()
    for review in reviews:
        required = {"query_id", "status", "record_ids", "reviewed_ids", "provider_outcomes", "reason", "next_observation", "reviewer"}
        if not isinstance(review, dict) or set(review) not in (required, required | {"raw_result_reviews"}):
            errors.append(f"{label}: query review has invalid fields")
            continue
        ident = review["query_id"]
        if not isinstance(ident, str) or ident in seen or ident not in queries:
            errors.append(f"{label}: duplicate or unplanned query review {ident}")
        seen.add(ident)
        if review["status"] not in {"reviewed", "refine", "primary_research_needed", "access_limited"}:
            errors.append(f"{label}/{ident}: invalid query disposition")
        if (not isinstance(review["provider_outcomes"], dict) or not review["provider_outcomes"]
                or any(not isinstance(provider, str) or not provider or not isinstance(status, str) or not status
                       for provider, status in review["provider_outcomes"].items())):
            errors.append(f"{label}/{ident}: query review needs exact provider outcomes")
        if "raw_result_reviews" in review and not isinstance(review["raw_result_reviews"], list):
            errors.append(f"{label}/{ident}: raw_result_reviews must be a list")
        for field in ("record_ids", "reviewed_ids"):
            value = review[field]
            if not isinstance(value, list) or len(value) != len(set(value)) or any(not isinstance(item, str) or not item for item in value):
                errors.append(f"{label}/{ident}: {field} must contain unique record IDs")
        if (not isinstance(review["reason"], str) or len(review["reason"].strip()) < 20
                or not isinstance(review["next_observation"], str) or len(review["next_observation"].strip()) < 20
                or not isinstance(review["reviewer"], str) or len(review["reviewer"].strip()) < 3):
            errors.append(f"{label}/{ident}: query review needs reviewer, observed reason and next observation")
    if seen != set(queries):
        errors.append(f"{label}: every executed query needs exactly one review")
    return reviews


def _applicability_review(planned: dict[str, Any], label: str, errors: list[str]) -> None:
    review = planned.get("applicability_review")
    required = {"reviewer", "reviewed_at", "entity_id", "locale", "source_lane", "query_id",
                "source_url", "capture_path", "capture_sha256", "source_span", "observed_fact", "reason"}
    if not isinstance(review, dict) or set(review) != required:
        errors.append(f"{label}: v4 not-applicable lane needs a source-bound applicability review")
        return
    if any(not isinstance(review[name], str) or not review[name].strip() for name in required):
        errors.append(f"{label}: applicability review fields must be nonempty")
    if any(review.get(name) != planned.get(name) for name in ("entity_id", "locale", "source_lane")):
        errors.append(f"{label}: applicability review scope differs from source lane")
    if (not isinstance(review.get("reason"), str) or len(review["reason"].strip()) < 20
            or not isinstance(review.get("observed_fact"), str) or len(review["observed_fact"].strip()) < 20):
        errors.append(f"{label}: applicability review needs a specific observed fact and reason")


def _locator_resolution(planned: dict[str, Any], label: str, errors: list[str]) -> bool:
    review = planned.get("locator_resolution")
    required = {"status", "entity_id", "locale", "source_lane", "reviewer", "reviewed_at",
                "reason", "next_observation", "fallback_reason", "searches"}
    if not isinstance(review, dict) or set(review) != required:
        errors.append(f"{label}: locator resolution has invalid fields")
        return False
    if any(review.get(name) != planned.get(name) for name in ("entity_id", "locale", "source_lane")):
        errors.append(f"{label}: locator resolution scope differs from lane")
    if review.get("status") not in {"locator_unavailable", "platform_access_limited"}:
        errors.append(f"{label}: locator resolution status is invalid")
    for name in ("reviewer", "reviewed_at", "reason", "next_observation"):
        if not isinstance(review.get(name), str) or len(review[name].strip()) < (20 if name in {"reason", "next_observation"} else 3):
            errors.append(f"{label}: locator resolution {name} is missing or unspecific")
    if not isinstance(review.get("fallback_reason"), str):
        errors.append(f"{label}: locator fallback reason must be text")
    searches = review.get("searches")
    if not isinstance(searches, list) or not searches:
        errors.append(f"{label}: locator resolution requires executed exact-product searches")
        return False
    for search in searches:
        fields = {"run_dir", "query_id", "query_text", "provider", "source_domain", "entity_aliases",
                  "locale_terms", "relevance_rationale", "query_status", "raw_sha256", "candidates"}
        if not isinstance(search, dict) or set(search) != fields:
            errors.append(f"{label}: locator search has invalid fields")
            continue
        if any(not isinstance(search.get(name), str) or not search[name].strip()
               for name in fields - {"entity_aliases", "locale_terms", "candidates"}):
            errors.append(f"{label}: locator search is missing query or capture binding")
        if any(not isinstance(search.get(name), list) or not search[name]
               or any(not isinstance(value, str) or not value.strip() for value in search[name])
               for name in ("entity_aliases", "locale_terms")):
            errors.append(f"{label}: locator search needs product aliases and locale terms")
        candidates = search.get("candidates")
        if not isinstance(candidates, list):
            errors.append(f"{label}: locator search candidates must be a list")
            continue
        for candidate in candidates:
            if (not isinstance(candidate, dict)
                    or set(candidate) != {"candidate_id", "source_url", "disposition", "reason"}
                    or candidate.get("disposition") not in {"false_positive", "adjacent", "exact_match"}
                    or not isinstance(candidate.get("reason"), str) or len(candidate["reason"].strip()) < 20):
                errors.append(f"{label}: locator candidate needs an inspected disposition")
        if review.get("status") == "locator_unavailable" and any(
                isinstance(candidate, dict) and candidate.get("disposition") == "exact_match"
                for candidate in candidates):
            errors.append(f"{label}: exact locator contradicts locator_unavailable")
    if planned.get("locators") or planned.get("reviewed_locators"):
        errors.append(f"{label}: verified locator contradicts locator resolution")
    return True


def _index(rows: Any, fields: tuple[str, ...], label: str, errors: list[str]) -> dict[tuple[str, ...], dict[str, Any]]:
    output: dict[tuple[str, ...], dict[str, Any]] = {}
    if not isinstance(rows, list):
        errors.append(f"{label} must be a list")
        return output
    for row in rows:
        if not isinstance(row, dict):
            errors.append(f"{label} entries must be objects")
            continue
        key = tuple(str(row.get(field) or "") for field in fields)
        if not all(key) or key in output:
            errors.append(f"{label}: missing or duplicate key {key}")
        else:
            output[key] = row
    return output


def validate(plan: dict[str, Any], results: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    gaps: list[dict[str, Any]] = []
    outcomes: list[str] = []
    strict_search = plan.get("execution_contract_version") in {3, 4}
    strict_queries = plan.get("execution_contract_version") == 4

    def gap(scope: dict[str, Any], reason: str, status: str = "pending") -> None:
        gaps.append({**scope, "status": status, "reason": reason})

    raw_topic = results.get("topic_led_voc", {})
    if not isinstance(raw_topic, dict):
        errors.append("topic_led_voc must be an object")
        raw_topic = {}
    planned_cells = plan.get("topic_matrix", [])
    if not isinstance(planned_cells, list):
        errors.append("topic_matrix must be a list")
        planned_cells = []
    # Legacy plans/results are useful inputs, but cannot attest market coverage.
    if not planned_cells:
        planned_cells = [{"cell_id": f"topic:{locale}", "locale": locale} for locale in plan.get("locales", [])]
    planned_by_id = _index(planned_cells, ("cell_id",), "topic plan cells", errors)
    for locale in plan.get("locales", []):
        if not any(cell.get("locale") == locale for cell in planned_cells):
            gap({"sampling_frame": "topic_led_voc", "locale": locale}, "Requested locale has no planned topic cell")
            outcomes.append("pending")
    topic_ids: set[str] = set()
    topic_attempted = False
    topic_rows: list[dict[str, Any]] = []
    if "cells" not in raw_topic:
        counts, ids = _counts(raw_topic, "topic-led counts", errors, topic=True)
        topic_ids.update(ids)
        topic_attempted = _outcome(raw_topic) != "pending"
        gap({"sampling_frame": "topic_led_voc"},
            "Legacy aggregate topic results have no cell bindings; locale/job/role/source/intent coverage is unresolved", "unresolved")
        for cell in planned_cells:
            topic_rows.append({**cell, "execution_status": "pending", "coverage_status": "unresolved",
                               "accepted_evidence_ids": []})
            outcomes.append("pending")
            gap({"sampling_frame": "topic_led_voc", **cell}, "No cell-bound topic result; aggregate counts cannot establish this scope", "unresolved")
        topic = {**raw_topic, "cells": topic_rows, "accepted_evidence_ids": sorted(topic_ids),
                 "accepted_count": len(topic_ids), "scope_binding_status": "legacy_unresolved"}
    else:
        cells = _index(raw_topic["cells"], ("cell_id",), "topic result cells", errors)
        for key in cells.keys() - planned_by_id.keys():
            errors.append(f"topic result cell {key}: not in the sampling plan")
        topic_totals = [0, 0, 0]
        for key, cell in planned_by_id.items():
            result = cells.get(key)
            outcome = _outcome(result)
            outcomes.append(outcome)
            scope = {"sampling_frame": "topic_led_voc", **cell}
            if outcome != "attempted":
                gap(scope, str((result or {}).get("failed_or_blocked") or "No attempted topic result"), outcome)
            row = {**cell, "execution_status": outcome, "accepted_evidence_ids": []}
            if result is not None:
                # Results may report observations; they cannot change the planned scope.
                for field in ("locale", "job", "role", "source_family", "query_intent"):
                    if field in result and result[field] != cell.get(field):
                        errors.append(f"topic cell {key}: result {field} disagrees with planned scope")
                counts, ids = _counts(result, f"topic cell {key}", errors, topic=True)
                fully_reviewed, _ = _review_accounting(result, f"topic cell {key}", errors)
                topic_totals = [a + b for a, b in zip(topic_totals, counts)]
                topic_ids.update(ids)
                topic_attempted |= outcome != "pending"
                resolution = _search_resolution(result, f"topic cell {key}", errors) if strict_search else None
                query_reviews = _query_reviews(result, f"topic cell {key}", errors) if strict_queries and result.get("attempted") is True else []
                row.update({name: result[name] for name in ("attempted", "retrieved_count", "reviewed_count", "accepted_count", "accepted_evidence_ids", "failed_or_blocked", "queries", "sampling") if name in result})
                if resolution:
                    row["search_resolution"] = result["search_resolution"]
                if strict_queries:
                    row["query_reviews"] = query_reviews
                    for query_review in query_reviews:
                        if not isinstance(query_review, dict):
                            continue
                        status = query_review.get("status")
                        query_scope = {**scope, "query_id": query_review.get("query_id")}
                        if status == "refine":
                            gap(query_scope, query_review.get("next_observation", "Refinement pending"), "refinement_required")
                        elif status == "primary_research_needed":
                            gap(query_scope, query_review.get("next_observation", "Primary research needed"), "primary_research_needed")
                        elif status == "access_limited":
                            gap(query_scope, query_review.get("next_observation", "Access limited"), "inaccessible")
                if counts[1] < counts[0] and fully_reviewed:
                    gap(scope, "Only the declared bounded sample was reviewed; unselected records do not support claims or prevalence", "bounded_sample")
                if outcome == "attempted" and not ids:
                    gap(scope, "No accepted customer voice in this sampling cell; no conclusion about absence of need", "no_accepted_voice")
                    if strict_search and not strict_queries and resolution is None:
                        gap(scope, "Low-yield cell needs a reviewed refinement or primary-research handoff", "resolution_required")
                    elif resolution == "refine":
                        gap(scope, result["search_resolution"]["next_observation"], "refinement_required")
                    elif resolution == "primary_research_needed":
                        gap(scope, result["search_resolution"]["next_observation"], "primary_research_needed")
                    elif resolution == "access_limited":
                        gap(scope, result["search_resolution"]["next_observation"], "inaccessible")
                elif strict_search and outcome == "inaccessible" and not ids:
                    if resolution != "access_limited":
                        gap(scope, "Access failure needs an observed recovery or limitation disposition", "resolution_required")
                    else:
                        gap(scope, result["search_resolution"]["next_observation"], "inaccessible")
                row["coverage_status"] = "observed_customer_voice" if ids else "no_accepted_voice" if outcome == "attempted" else "unresolved"
            topic_rows.append(row)
        if "accepted_evidence_ids" in raw_topic:
            declared = raw_topic["accepted_evidence_ids"]
            if not isinstance(declared, list) or any(not isinstance(item, str) for item in declared) or len(declared) != len(set(declared)) or set(declared) != topic_ids:
                errors.append("topic-led aggregate accepted_evidence_ids must equal the unique union of cell IDs")
        if "accepted_count" in raw_topic and (type(raw_topic["accepted_count"]) is not int or raw_topic["accepted_count"] != len(topic_ids)):
            errors.append("topic-led aggregate accepted_count must equal unique accepted evidence IDs")
        topic = {"attempted": topic_attempted, "cells": topic_rows, "accepted_evidence_ids": sorted(topic_ids),
                 "accepted_count": len(topic_ids), "retrieved_count": topic_totals[0], "reviewed_count": topic_totals[1],
                 "counting_note": "retrieved/reviewed totals are sampling-cell occurrences; accepted_count is distinct evidence IDs",
                 "scope_binding_status": "cell_bound"}

    fields = ("entity_id", "locale", "source_lane")
    planned_sources = _index(plan.get("source_matrix", []), fields, "source plan", errors)
    keyed = _index(results.get("source_results", []), fields, "source_results", errors)
    for key in keyed.keys() - planned_sources.keys():
        errors.append(f"source result {key}: not in the reviewed source plan")
    finalized: list[dict[str, Any]] = []
    entity_ids: set[str] = set()
    for key, planned in planned_sources.items():
        row = dict(planned)
        scope = {"sampling_frame": "entity_led_feedback", **dict(zip(fields, key))}
        result = keyed.get(key)
        if not planned.get("applicable"):
            if not str(planned.get("not_applicable_reason") or "").strip():
                errors.append(f"{key}: not-applicable lane requires a reason")
            if strict_queries:
                _applicability_review(planned, str(key), errors)
                if planned.get("locators") or planned.get("reviewed_locators"):
                    errors.append(f"{key}: verified locator contradicts not-applicable lane")
            if result and (result.get("attempted") or result.get("locator_results") or any(result.get(name, 0) for name in ("retrieved_count", "reviewed_count", "accepted_customer_voice_count"))):
                errors.append(f"{key}: capture result contradicts a not-applicable planned lane")
            row["execution_status"] = "not_applicable"
            finalized.append(row)
            continue
        supplied = set(planned.get("locators", []))
        reviewed_items = _index(planned.get("reviewed_locators", []), ("locator",), f"{key} reviewed locators", errors)
        reviewed = {locator[0] for locator in reviewed_items}
        for locator, item in reviewed_items.items():
            if not str(item.get("review_reason") or "").strip() or locator[0] not in supplied:
                errors.append(f"{key}/{locator[0]}: reviewed locator requires a reason and planned locator")
        if not supplied:
            if strict_queries and planned.get("locator_resolution") is not None:
                if _locator_resolution(planned, str(key), errors):
                    resolution = planned["locator_resolution"]
                    row["execution_status"] = resolution["status"]
                    gap(scope, resolution["reason"], resolution["status"])
                    outcomes.append("attempted")
                    if result is not None:
                        errors.append(f"{key}: locator resolution contradicts captured lane results")
                    finalized.append(row)
                    continue
            gap(scope, "Applicable lane still requires locator discovery", "discovery_required")
            outcomes.append("pending")
        for locator in sorted(supplied - reviewed):
            gap({**scope, "locator": locator}, "Locator has no accepted review disposition", "review_pending")
            outcomes.append("pending")
        outcome = _outcome(result)
        outcomes.append(outcome)
        row["execution_status"] = outcome
        if outcome != "attempted":
            gap(scope, str((result or {}).get("failed_or_blocked") or "No completion result"), outcome)
        if result is None:
            finalized.append(row)
            continue
        counts, _ = _counts(result, str(key), errors, require_ids=False)
        if key[2] == "company_hosted_supplier_context" and counts[2]:
            errors.append(f"{key}: supplier context cannot count as accepted customer voice")
        by_locator = _index(result.get("locator_results", []), ("locator",), f"{key} locator_results", errors)
        for locator in {item[0] for item in by_locator} - reviewed:
            errors.append(f"{key}/{locator}: capture result from an unreviewed locator")
        totals = [0, 0, 0]
        accepted_here: set[str] = set()
        verified_results: list[dict[str, Any]] = []
        for locator in sorted(reviewed):
            item = by_locator.get((locator,))
            locator_outcome = _outcome(item)
            outcomes.append(locator_outcome)
            if locator_outcome != "attempted":
                gap({**scope, "locator": locator}, str((item or {}).get("failed_or_blocked") or "No completion result for locator"), locator_outcome)
            if item is None:
                continue
            locator_counts, ids = _counts(item, f"{key}/{locator}", errors)
            fully_reviewed, _ = _review_accounting(item, f"{key}/{locator}", errors)
            totals = [left + right for left, right in zip(totals, locator_counts)]
            accepted_here.update(ids)
            verified_results.append({**item, "execution_status": locator_outcome})
            if locator_counts[1] < locator_counts[0] and fully_reviewed:
                gap({**scope, "locator": locator}, "Only the declared bounded sample was reviewed; unselected records do not support claims or prevalence", "bounded_sample")
            if locator_outcome == "attempted" and not ids and key[2] != "company_hosted_supplier_context":
                gap({**scope, "locator": locator}, "No accepted customer voice from this source; no conclusion about absence of need", "no_accepted_voice")
        if counts != totals:
            errors.append(f"{key}: lane totals must equal the sum of per-locator totals")
        if "accepted_evidence_ids" in result:
            ids = result["accepted_evidence_ids"]
            if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids) or len(ids) != len(set(ids)) or set(ids) != accepted_here:
                errors.append(f"{key}: lane accepted_evidence_ids must equal the unique union of locator IDs")
        entity_ids.update(accepted_here)
        row.update({name: result[name] for name in ("attempted", "retrieved_count", "reviewed_count", "accepted_customer_voice_count", "failed_or_blocked", "sampling") if name in result})
        row.update({"locator_results": verified_results, "accepted_evidence_ids": sorted(accepted_here),
                    "unique_accepted_count": len(accepted_here)})
        finalized.append(row)

    if not plan.get("entity_count") and plan.get("analysis_contract", {}).get("entity_led_feedback") == "pending_entity_discovery":
        gap({"sampling_frame": "entity_led_feedback"}, "Verified entity discovery is pending; topic-led findings can still be reported", "pending_entity_discovery")
    all_ids = topic_ids | entity_ids
    execution = "complete" if outcomes and all(item != "pending" for item in outcomes) else "partial" if topic_attempted or any(item != "pending" for item in outcomes) else "not_started"
    coverage = "invalid" if errors else "partial" if gaps else "complete_for_declared_plan"
    claim = "blocked_invalid_input" if errors else "insufficient_evidence" if not all_ids else "pending_topic_discovery" if not topic_attempted else "scoped_synthesis_ready"
    status = "invalid" if errors else "insufficient_evidence" if not all_ids else "partial" if gaps or not topic_attempted else "complete"
    output = {"schema_version": 2, "status": status, "execution_status": execution, "coverage_status": coverage,
              "claim_status": claim, "topic_led_voc": topic, "source_matrix": finalized,
              "coverage_gaps": gaps, "errors": errors, "accepted_evidence_ids": sorted(all_ids),
              "unique_accepted_count": len(all_ids), "synthesis_allowed": claim == "scoped_synthesis_ready",
              "interpretation_boundary": "Coverage concerns declared sampling only, never market prevalence, author residence or problem validation. Partial findings must retain missing scopes."}
    return output, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        results = json.loads(Path(args.results).read_text(encoding="utf-8"))
        output, errors = validate(plan, results)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "error_count": len(errors), "out": str(out)}))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
