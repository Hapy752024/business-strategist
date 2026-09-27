#!/usr/bin/env python3
"""Read-only checks for executed collection, reviewed research, and case delivery.

These checks compose the existing lifecycle and VOC authorities. A run summary
or a nonempty file alone is never proof that collection was executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be an object")
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _local(workspace: Path, path: Path) -> bool:
    root = workspace.absolute()
    candidate = path.absolute()
    if not candidate.is_relative_to(root):
        return False
    while candidate != root:
        if candidate.is_symlink():
            return False
        candidate = candidate.parent
    return candidate == root


def _result(check: str, status: str, *, missing=(), gaps=(), actions=(), inputs=None, **extra) -> dict:
    work_items = []
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        state = gap.get("status")
        if state in {"pending", "review_pending", "discovery_required", "pending_entity_discovery", "provider_failure",
                     "resolution_required", "refinement_required", "unresolved", "handoff_required"}:
            kind = ("refine_search" if state in {"resolution_required", "refinement_required"}
                    else "discover_entity" if state in {"discovery_required", "pending_entity_discovery"}
                    else "prepare_unpaid_interview_route" if state == "handoff_required"
                    else "review_or_capture_source")
            work_items.append({"kind": kind, "scope": {key: gap[key] for key in
                               ("sampling_frame", "cell_id", "locale", "entity_id", "source_lane") if key in gap},
                               "reason": gap.get("reason", ""), "owner": "agent",
                               "artifact": ("market_research/interviews/recruitment-plan.md" if state == "handoff_required"
                                            else "customer-feedback/customer-feedback-results.json"),
                               "completion_check": "research"})
        elif state == "primary_research_needed":
            work_items.append({"kind": "prepare_unpaid_interview_route", "scope": {key: gap[key] for key in
                               ("sampling_frame", "cell_id", "locale") if key in gap},
                               "reason": gap.get("reason", ""), "owner": "agent",
                               "artifact": "market_research/interviews/interview-guide.md",
                               "completion_check": "research"})
    for requirement in missing:
        work_items.append({"kind": "satisfy_requirement", "scope": {}, "reason": str(requirement),
                           "owner": "agent", "artifact": "", "completion_check": check})
    return {"check": check, "status": status, "missing_requirements": list(missing),
            "open_gaps": list(gaps), "next_actions": list(actions), "work_items": work_items,
            "inputs": inputs or {}, **extra}


def _capture_records(workspace: Path, run_dir: Path, plan: dict) -> tuple[dict[str, set[str]], set[str], set[str], dict[str, list[dict]], dict[str, str]]:
    """Load primary and explicitly digest-bound case-local capture runs."""
    inputs: dict[str, str] = {}
    by_query: dict[str, set[str]] = {}
    all_ids: set[str] = set()
    observed_all: set[str] = set()
    by_locator: dict[str, list[dict]] = {}
    capture_dirs = [run_dir / "evidence" if (run_dir / "evidence" / "query_plan.json").exists() else run_dir]
    bindings = plan.get("capture_inputs", [])
    if not isinstance(bindings, list):
        raise ValueError("capture_inputs must be a list of explicit case-local run bindings")
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"run_dir", "artifact_digests"}:
            raise ValueError("capture input needs run_dir and artifact_digests")
        path_text = binding["run_dir"]
        if not isinstance(path_text, str) or Path(path_text).is_absolute() or ".." in Path(path_text).parts:
            raise ValueError("capture input must use a safe workspace-relative path")
        capture_run = workspace / path_text
        if not _local(workspace, capture_run) or not capture_run.is_dir():
            raise ValueError("capture input is missing, symlinked or outside the workspace")
        capture_dir = capture_run / "evidence" if (capture_run / "evidence" / "query_plan.json").exists() else capture_run
        check = validate_collection(workspace, capture_dir)
        if check["status"] != "complete":
            raise ValueError(f"bound capture run is not complete: {path_text}")
        expected = binding["artifact_digests"]
        actual = {name: _digest(capture_dir / name) for name in ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl")}
        if expected != actual:
            raise ValueError(f"bound capture run changed since review: {path_text}")
        inputs.update({str((capture_dir / name).relative_to(workspace)): digest for name, digest in actual.items()})
        capture_dirs.append(capture_dir)
    for capture_dir in dict.fromkeys(capture_dirs):
        summary = _read(capture_dir / "summary.json")
        if (capture_dir / "manual-captures.json").is_file():
            observed = {row["query_id"] for row in _read(capture_dir / "manual-captures.json")["captures"]}
        else:
            observed = {row.get("query_id") for provider in summary.get("providers", {}).values()
                        for row in provider.get("query_ledger", []) if row.get("scheduled") and row.get("attempted")}
        observed_all.update(item for item in observed if isinstance(item, str))
        for name in ("evidence.jsonl", "irrelevant.jsonl"):
            for line in (capture_dir / name).read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                evidence_id = record.get("evidence_id")
                if not isinstance(evidence_id, str) or not evidence_id:
                    raise ValueError(f"capture record in {capture_dir} has no evidence_id")
                all_ids.add(evidence_id)
                locator = record.get("collection_locator")
                if isinstance(locator, str) and locator:
                    by_locator.setdefault(locator, []).append(record)
                for membership in record.get("discovery_memberships", []):
                    query_id = membership.get("query_id") if isinstance(membership, dict) else None
                    if query_id and query_id in observed:
                        by_query.setdefault(query_id, set()).add(evidence_id)
    return by_query, all_ids, observed_all, by_locator, inputs


def _query_outcomes(workspace: Path, run_dir: Path, plan: dict) -> dict[str, dict[str, str]]:
    """Read provider outcomes for exact captured query IDs, without treating failures as negative evidence."""
    directories = [run_dir / "evidence" if (run_dir / "evidence/query_plan.json").exists() else run_dir]
    for binding in plan.get("capture_inputs", []):
        capture = workspace / binding["run_dir"]
        directories.append(capture / "evidence" if (capture / "evidence/query_plan.json").exists() else capture)
    outcomes: dict[str, dict[str, str]] = {}
    for directory in dict.fromkeys(directories):
        summary = _read(directory / "summary.json")
        for provider_name, provider in summary.get("providers", {}).items():
            for row in provider.get("query_ledger", []):
                if row.get("scheduled") and row.get("attempted") and isinstance(row.get("query_id"), str):
                    previous = outcomes.setdefault(row["query_id"], {}).get(provider_name)
                    status = str(row.get("status") or "unknown")
                    if previous is not None and previous != status:
                        raise ValueError(f"query {row['query_id']} has conflicting {provider_name} outcomes")
                    outcomes[row["query_id"]][provider_name] = status
        manual = directory / "manual-captures.json"
        if manual.is_file():
            for row in _read(manual).get("captures", []):
                if isinstance(row.get("query_id"), str):
                    outcomes.setdefault(row["query_id"], {})["manual"] = str(row.get("retrieval_outcome") or "manual_capture")
    return outcomes


def _collection_coverage_gaps(collection: dict, plan: dict, results: dict,
                              query_outcomes: dict[str, dict[str, str]]) -> list[dict]:
    reviews = {review.get("query_id"): review for cell in results.get("topic_led_voc", {}).get("cells", [])
               for review in cell.get("query_reviews", []) if isinstance(review, dict)}
    strict = plan.get("execution_contract_version") == 4
    output = []
    for raw in collection.get("open_gaps", []):
        if not isinstance(raw, str):
            output.append(raw)
            continue
        if raw.startswith("remaining source or review work:"):
            # Collector quality notes describe yield or downstream review work,
            # not a failed provider route. Topic/entity reviews below decide
            # whether the study can close with insufficient evidence.
            output.append({"sampling_frame": "collection", "provider": "evidence_quality",
                           "query_ids": [], "status": "collection_observation",
                           "reason": raw + "; retained as a coverage limitation, not evidence of no demand"})
            continue
        head = raw.split(":", 1)[0]
        if "/" in head:
            provider, ident = head.split("/", 1)
            affected = [ident]
        else:
            provider = head
            affected = [ident for ident, outcomes in query_outcomes.items()
                        if provider in outcomes and outcomes[provider] not in {"ok", "empty", "no_results", "manual_capture"}]
        resolved = bool(affected) and all(reviews.get(ident, {}).get("status") in
                                          {"access_limited", "primary_research_needed"} for ident in affected)
        output.append({"sampling_frame": "collection", "provider": provider,
                       "query_ids": affected, "status": "inaccessible" if not strict or resolved else "provider_failure",
                       "reason": raw + "; retained as a coverage limitation, not evidence of no demand"})
    return output


def _raw_result_review(workspace: Path, run_dir: Path, plan: dict, results: dict,
                       captured_by_query: dict[str, set[str]]) -> tuple[list[str], list[dict], dict[str, str]]:
    """Reconcile provider-returned candidates that the collector did not retain."""
    reviews = {review.get("query_id"): review for cell in results.get("topic_led_voc", {}).get("cells", [])
               for review in cell.get("query_reviews", []) if isinstance(review, dict)}
    directories = [run_dir / "evidence" if (run_dir / "evidence/query_plan.json").exists() else run_dir]
    for binding in plan.get("capture_inputs", []):
        path = workspace / binding["run_dir"]
        directories.append(path / "evidence" if (path / "evidence/query_plan.json").exists() else path)
    errors: list[str] = []
    gaps: list[dict] = []
    inputs: dict[str, str] = {}
    for directory in dict.fromkeys(directories):
        summary = _read(directory / "summary.json")
        for provider_name, provider in summary.get("providers", {}).items():
            for ledger in provider.get("query_ledger", []):
                ident = ledger.get("query_id")
                if not ledger.get("scheduled") or not ledger.get("attempted") or ident not in reviews:
                    continue
                retained_ids = ledger.get("record_ids")
                if not isinstance(retained_ids, list):
                    retained_ids = list(captured_by_query.get(ident, set()))
                returned = ledger.get("returned_count")
                if type(returned) is not int or returned <= len(retained_ids):
                    continue
                raw_path = directory / "raw" / f"{provider_name}.json"
                if not raw_path.is_file() or raw_path.is_symlink():
                    errors.append(f"query {ident}: unretained provider results lack raw response")
                    continue
                raw_digest = _digest(raw_path)
                inputs[str(raw_path.relative_to(workspace))] = raw_digest
                declarations = [row for row in reviews[ident].get("raw_result_reviews", [])
                                if isinstance(row, dict) and row.get("provider") == provider_name]
                if len(declarations) != 1:
                    gaps.append({"sampling_frame": "topic_led_voc", "query_id": ident,
                                 "status": "review_pending", "reason": "Raw returned-but-unretained candidates need one source-bound review"})
                    continue
                declaration = declarations[0]
                expected = {"provider", "raw_sha256", "returned_count", "retained_count", "reviewer", "reason", "candidates"}
                if (set(declaration) != expected or declaration.get("raw_sha256") != raw_digest
                        or declaration.get("returned_count") != returned
                        or declaration.get("retained_count") != len(retained_ids)
                        or not isinstance(declaration.get("reviewer"), str) or len(declaration["reviewer"].strip()) < 3
                        or not isinstance(declaration.get("reason"), str) or len(declaration["reason"].strip()) < 20):
                    errors.append(f"query {ident}: raw-result review is malformed or stale")
                    continue
                candidates = declaration["candidates"]
                if not isinstance(candidates, list):
                    errors.append(f"query {ident}: raw candidate reviews must be a list")
                    continue
                if provider_name == "reddit":
                    raw = _read(raw_path)
                    expected_candidates = {}
                    for search in raw.get("searches", []):
                        if search.get("query_id") != ident:
                            continue
                        for child in search.get("response", {}).get("body", {}).get("data", {}).get("children", []):
                            data = child.get("data", {})
                            candidate_id = str(data.get("id") or "")
                            permalink = data.get("permalink") or ""
                            if candidate_id:
                                expected_candidates[candidate_id] = ("https://www.reddit.com" + permalink
                                                                     if permalink.startswith("/") else permalink)
                    actual_candidates = {row.get("candidate_id"): row for row in candidates
                                         if isinstance(row, dict)}
                    if (len(actual_candidates) != len(candidates) or set(actual_candidates) != set(expected_candidates)
                            or len(expected_candidates) != returned):
                        errors.append(f"query {ident}: Reddit raw candidate IDs do not reconcile")
                        continue
                    if any(set(row) != {"candidate_id", "source_url", "disposition", "reason"}
                           or row["source_url"] != expected_candidates[row["candidate_id"]]
                           or row["disposition"] not in {"retained", "excluded", "promote"}
                           or not isinstance(row["reason"], str) or len(row["reason"].strip()) < 20
                           for row in candidates):
                        errors.append(f"query {ident}: Reddit raw candidate disposition is invalid")
                        continue
                    if sum(row["disposition"] == "retained" for row in candidates) != len(retained_ids):
                        errors.append(f"query {ident}: retained raw candidates do not match collector ledger")
                        continue
                elif candidates:
                    errors.append(f"query {ident}: use an aggregate reason for non-Reddit raw results")
                    continue
                if any(row.get("disposition") == "promote" for row in candidates):
                    gaps.append({"sampling_frame": "topic_led_voc", "query_id": ident,
                                 "status": "review_pending", "reason": "Promoted raw candidates need exact retained source capture and review"})
    return errors, gaps, inputs


def _v4_applicability_inputs(workspace: Path, run_dir: Path, plan: dict,
                             observed_queries: set[str]) -> dict[str, str]:
    inputs: dict[str, str] = {}
    for row in plan.get("source_matrix", []):
        if row.get("applicable") is not False:
            continue
        review = row.get("applicability_review")
        if not isinstance(review, dict):
            raise ValueError("not-applicable lane lacks source-bound review")
        rel = review.get("capture_path")
        if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError("applicability capture path is unsafe")
        source = workspace / rel
        relative = source.relative_to(workspace)
        case_prefix = run_dir.relative_to(workspace).parts[:2]
        if (relative.parts[:2] != case_prefix or not _local(workspace, source) or not source.is_file()
                or source.is_symlink() or _digest(source) != review.get("capture_sha256")):
            raise ValueError("applicability review source is missing, changed or outside the case")
        body = source.read_text(encoding="utf-8")
        if (review.get("source_span") not in body or review.get("source_url") not in body
                or review.get("query_id") not in observed_queries):
            raise ValueError("applicability review lacks exact retained span, URL or observed query")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(review.get("reviewed_at", ""))):
            raise ValueError("applicability review date is invalid")
        inputs[rel] = _digest(source)
    return inputs


def _v4_locator_inputs(workspace: Path, run_dir: Path, plan: dict) -> dict[str, str]:
    """Bind bounded no-locator conclusions to executed exact-product searches."""
    inputs: dict[str, str] = {}
    bound = {row.get("run_dir") for row in plan.get("capture_inputs", [])}
    case_parts = run_dir.relative_to(workspace).parts[:2]
    for lane in plan.get("source_matrix", []):
        review = lane.get("locator_resolution")
        if review is None:
            continue
        if plan.get("execution_contract_version") != 4 or lane.get("applicable") is not True:
            raise ValueError("locator resolution requires an applicable v4 lane")
        identity = [row for row in plan.get("source_matrix", [])
                    if row.get("entity_id") == lane.get("entity_id")
                    and row.get("locale") == lane.get("locale")
                    and row.get("source_lane") == "company_hosted_supplier_context"
                    and row.get("reviewed_locators")]
        if len(identity) != 1:
            raise ValueError("locator resolution needs a reviewed official identity source for this entity and locale")
        entity_name = str(lane.get("entity_name") or "")
        if not entity_name or identity[0].get("entity_name") != entity_name:
            raise ValueError("locator resolution entity name does not match reviewed official identity")
        seen: set[tuple[str, str]] = set()
        successes = 0
        failures = 0
        for search in review["searches"]:
            rel = search["run_dir"]
            if (rel not in bound or Path(rel).is_absolute() or ".." in Path(rel).parts
                    or Path(rel).parts[:2] != case_parts):
                raise ValueError(f"locator search uses undeclared or cross-case capture: {rel}")
            directory = workspace / rel
            directory = directory / "evidence" if (directory / "evidence/query_plan.json").is_file() else directory
            if not _local(workspace, directory):
                raise ValueError("locator capture is symlinked or outside case")
            query_plan = _read(directory / "query_plan.json")
            rows = (query_plan.get("input_plan") or {}).get("queries", [])
            matching = [row for row in rows if row.get("query_id") == search["query_id"]]
            if len(matching) != 1:
                raise ValueError("locator query ID was not scheduled in capture")
            planned = matching[0]
            key = (rel, search["query_id"])
            if key in seen:
                raise ValueError("locator search query is duplicated")
            seen.add(key)
            query = search["query_text"]
            normal = lambda value: " ".join(str(value).casefold().split())
            if (query != planned.get("query") or search["provider"] != planned.get("provider")
                    or planned.get("intent") != "entity_locator_discovery"
                    or planned.get("candidate_id") != lane["entity_id"]
                    or planned.get("source_family") != lane["source_lane"]
                    or planned.get("locale") != lane["locale"]
                    or '\\"' in query
                    or normal(search["source_domain"]) not in normal(query)
                    or not all(normal(alias) in normal(query) for alias in search["entity_aliases"])
                    or not any(len(normal(alias)) >= 4 and normal(alias) in normal(entity_name)
                               for alias in search["entity_aliases"])
                    or not any(normal(term) in normal(query) for term in search["locale_terms"])
                    or len(search["relevance_rationale"].strip()) < 30):
                raise ValueError("locator query is not bound to exact product, locale and platform lane")
            summary_path = directory / "summary.json"
            summary = _read(summary_path)
            ledger = [row for row in summary.get("providers", {}).get(search["provider"], {}).get("query_ledger", [])
                      if row.get("query_id") == search["query_id"] and row.get("scheduled") and row.get("attempted")]
            if (len(ledger) != 1 or ledger[0].get("query") != query
                    or ledger[0].get("candidate_id") != lane["entity_id"]
                    or ledger[0].get("status") != search["query_status"]):
                raise ValueError("locator search outcome does not match executed provider ledger")
            status = search["query_status"]
            if status in {"ok", "empty", "no_results"}:
                successes += 1
            else:
                failures += 1
            raw_path = directory / "raw" / (search["provider"] + ".json")
            if not _local(workspace, raw_path) or not raw_path.is_file() or _digest(raw_path) != search["raw_sha256"]:
                raise ValueError("locator raw capture is missing or stale")
            if search["provider"] not in {"serper_search", "brave_search"}:
                raise ValueError("locator candidate reconciliation supports explicit Serper or Brave searches")
            raw = _read(raw_path)
            hits = [item for item in raw.get("searches", [])
                    if item.get("query_id") == search["query_id"] and item.get("query") == query]
            if len(hits) != 1:
                raise ValueError("locator raw query is absent or duplicated")
            response = hits[0].get("response", {})
            if search["provider"] == "serper_search":
                organic = response.get("body", {}).get("organic", []) if response.get("ok") else []
                expected = {item.get("link") for item in organic if isinstance(item, dict)}
            else:
                organic = response.get("body", {}).get("web", {}).get("results", []) if response.get("ok") else []
                expected = {item.get("url") for item in organic if isinstance(item, dict)}
            actual = {item.get("candidate_id") for item in search["candidates"]}
            if (len(expected) != len(organic) or actual != expected
                    or len(actual) != len(search["candidates"])
                    or any(item.get("candidate_id") != item.get("source_url") for item in search["candidates"])
                    or ledger[0].get("returned_count") != len(organic)
                    or (status in {"ok", "empty", "no_results"} and not response.get("ok"))):
                raise ValueError("locator returned candidates do not reconcile to raw response")
            inputs[str(raw_path.relative_to(workspace))] = _digest(raw_path)
            inputs[str(summary_path.relative_to(workspace))] = _digest(summary_path)
            inputs[str((directory / "query_plan.json").relative_to(workspace))] = _digest(directory / "query_plan.json")
        if review["status"] == "locator_unavailable" and (not successes or failures):
            raise ValueError("locator_unavailable requires successful exact-product searches without provider failures")
        if review["status"] == "platform_access_limited" and (not failures or
                (not successes and len(review["fallback_reason"].strip()) < 20)):
            raise ValueError("platform access limitation needs observed failure and viable fallback or reason")
    return inputs


def _provider_terminal(status: str) -> bool:
    return status in {"ok", "empty", "no_results", "partial", "failed", "rate_limited",
                      "permission_denied", "missing_credentials", "billing_required",
                      "insufficient_credits", "capture_gate_blocked", "invalid_records", "unsupported"}


def _primary_research_handoff(workspace: Path, run_dir: Path, plan: dict, results: dict) -> tuple[list[dict], dict[str, str]]:
    """Bind an unpaid interview handoff when a v3 case closes a web cell as insufficient."""
    cells = {row.get("cell_id") for row in results.get("topic_led_voc", {}).get("cells", [])
             if isinstance(row, dict) and isinstance(row.get("search_resolution"), dict)
             and row["search_resolution"].get("status") == "primary_research_needed"}
    if plan.get("execution_contract_version") == 4:
        cells |= {row.get("cell_id") for row in results.get("topic_led_voc", {}).get("cells", [])
                  if isinstance(row, dict) and any(
                      isinstance(item, dict) and item.get("status") == "primary_research_needed"
                      for item in row.get("query_reviews", []))}
    if not cells or plan.get("execution_contract_version") not in {3, 4}:
        return [], {}
    relative = run_dir.relative_to(workspace) if run_dir.is_relative_to(workspace) else Path()
    if len(relative.parts) < 3 or relative.parts[0] != "cases":
        return [], {}  # Non-case studies retain their existing handoff contract.
    case_id = relative.parts[1]
    handoff = plan.get("primary_research_handoff")
    reason = "Primary research handoff needs a case-local unpaid recruitment plan bound to every unresolved cell"
    scope = {"sampling_frame": "topic_led_voc", "case_id": case_id}
    if not isinstance(handoff, dict) or set(handoff) != {"path", "sha256", "cell_ids"}:
        return [{**scope, "status": "handoff_required", "reason": reason}], {}
    rel = handoff["path"]
    cell_ids = handoff["cell_ids"]
    if (not isinstance(cell_ids, list) or any(not isinstance(item, str) for item in cell_ids)
            or len(cell_ids) != len(set(cell_ids))
            or not isinstance(rel, str) or not rel.startswith(f"cases/{case_id}/market_research/interviews/")
            or Path(rel).is_absolute() or ".." in Path(rel).parts
            or set(cell_ids) != cells):
        return [{**scope, "status": "handoff_required", "reason": reason}], {}
    path = workspace / rel
    if (not _local(workspace, path) or not path.is_file() or path.is_symlink()
            or not path.read_text(encoding="utf-8").strip() or _digest(path) != handoff["sha256"]):
        return [{**scope, "status": "handoff_required", "reason": "Primary research handoff is missing or changed since review"}], {}
    body = path.read_text(encoding="utf-8")
    required = ("Desk research limit", "Target participant", "Recent firsthand screen", "Unpaid access route",
                "Episode questions", "Distinguishing observation", "Decision rule")
    for cell_id in sorted(cells):
        match = re.search(r"(?ms)^### " + re.escape(cell_id) + r"\s*\n(.*?)(?=^### |\Z)", body)
        if not match:
            return [{**scope, "status": "handoff_required", "reason": f"Primary research handoff lacks a plan for cell {cell_id}"}], {}
        fields = {}
        for line in match.group(1).splitlines():
            field = re.match(r"^- ([^:]+):\s*(.+)$", line)
            if field:
                fields[field.group(1)] = field.group(2).strip()
        if any(len(fields.get(name, "")) < 20 for name in required):
            return [{**scope, "status": "handoff_required", "reason": f"Primary research handoff for {cell_id} needs desk limit, target, screen, unpaid route, episode questions, distinguishing observation and decision rule"}], {}
        cell = next(row for row in results["topic_led_voc"]["cells"] if row.get("cell_id") == cell_id)
        reviewed_queries = set(cell.get("search_resolution", {}).get("query_ids", []))
        reviewed_queries.update(row.get("query_id") for row in cell.get("query_reviews", [])
                                if row.get("status") == "primary_research_needed"
                                and isinstance(row.get("query_id"), str))
        if reviewed_queries and not any(ident in fields["Desk research limit"] for ident in reviewed_queries):
            return [{**scope, "status": "handoff_required", "reason": f"Primary research handoff for {cell_id} does not name an executed query"}], {}
        observations = [cell.get("search_resolution", {}).get("next_observation", "")]
        observations.extend(row.get("next_observation", "") for row in cell.get("query_reviews", [])
                            if row.get("status") == "primary_research_needed")
        if fields["Distinguishing observation"] not in observations:
            return [{**scope, "status": "handoff_required", "reason": f"Primary research handoff for {cell_id} does not match the reviewed distinguishing observation"}], {}
    return [], {rel: _digest(path)}


def _manual_collection(workspace: Path, run_dir: Path) -> dict:
    required = ("query_plan.json", "manual-captures.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl")
    missing = [name for name in required if not (run_dir / name).is_file() or (run_dir / name).is_symlink()]
    if missing:
        return _result("collection", "partial", missing=missing, actions=["Supply retained manual capture sources"])
    try:
        plan, packet, summary = (_read(run_dir / name) for name in required[:3])
        planned = {row["query_id"]: row for row in plan["input_plan"]["queries"]}
        if not planned or len(planned) != len(plan["input_plan"]["queries"]):
            raise ValueError("manual query IDs must be unique and nonempty")
        if packet.get("capture_method") != "manual" or packet.get("schema_version") != 1:
            raise ValueError("manual capture method/version missing")
        captures = packet["captures"]
        if not isinstance(captures, list) or not captures:
            raise ValueError("manual captures must retain at least one source response")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _result("collection", "invalid", missing=[str(exc)])
    inputs = {str((run_dir / name).relative_to(workspace)): _digest(run_dir / name) for name in required}
    covered, gaps = set(), []
    captured_sources = set()
    for capture in captures:
        ident = capture.get("query_id")
        path = run_dir / str(capture.get("capture_path", ""))
        if (ident not in planned or capture.get("query") != planned[ident].get("query")
                or not capture.get("retrieved_at") or not capture.get("source_url")
                or capture.get("retrieval_outcome") not in {"ok", "empty", "failed", "blocked"}
                or not _local(workspace, path) or not path.is_file() or not path.stat().st_size
                or _digest(path) != capture.get("sha256")):
            return _result("collection", "invalid", missing=[f"manual capture {ident}: unbound or missing source response"], inputs=inputs)
        covered.add(ident)
        captured_sources.add((ident, capture["source_url"]))
        inputs[str(path.relative_to(workspace))] = _digest(path)
        if capture["retrieval_outcome"] in {"failed", "blocked"}:
            gaps.append(f"{ident}: {capture['retrieval_outcome']}")
    missing = [f"{ident}: no retained attempt" for ident in planned.keys() - covered]
    for filename, count_name in (("evidence.jsonl", "record_count"), ("irrelevant.jsonl", "irrelevant_count")):
        rows = [json.loads(line) for line in (run_dir / filename).read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != summary.get(count_name):
            return _result("collection", "invalid", missing=[f"{filename}: summary count mismatch"], inputs=inputs)
        for row in rows:
            memberships = row.get("discovery_memberships", [])
            if not memberships or not any((item.get("query_id"), row.get("source_url")) in captured_sources for item in memberships):
                return _result("collection", "invalid", missing=[f"{filename}: evidence lacks captured query membership"], inputs=inputs)
    return _result("collection", "partial" if missing else "complete", missing=missing, gaps=gaps,
                   actions=["Complete manual source capture"] if missing else ["Review manual source episodes"],
                   inputs=inputs, execution_status="partial" if missing else "complete",
                   coverage_status="partial" if gaps or missing else "complete_for_declared_plan",
                   claim_status="not_reviewed")


def validate_collection(workspace: Path, run_dir: Path) -> dict:
    workspace, run_dir = Path(workspace).absolute(), Path(run_dir).absolute()
    if not _local(workspace, run_dir):
        return _result("collection", "invalid", missing=["run must be workspace-local without symlinks"])
    if (run_dir / "manual-captures.json").exists():
        return _manual_collection(workspace, run_dir)
    names = ("query_plan.json", "run-checkpoint.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl")
    missing = [name for name in names if not (run_dir / name).is_file() or (run_dir / name).is_symlink()]
    if missing:
        return _result("collection", "partial", missing=missing, actions=["Resume the collector or import verifiable manual captures"])
    try:
        plan, checkpoint, summary = (_read(run_dir / name) for name in names[:3])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _result("collection", "invalid", missing=[str(exc)])
    inputs = {str((run_dir / name).relative_to(workspace)): _digest(run_dir / name) for name in names}
    expected = hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if checkpoint.get("query_plan_digest") != expected or summary.get("query_plan_digest") != plan.get("input_plan_digest"):
        return _result("collection", "invalid", missing=["query plan, checkpoint and summary digests disagree"], inputs=inputs)
    input_plan = plan.get("input_plan")
    if input_plan is not None and plan.get("input_plan_digest") != hashlib.sha256(
            json.dumps(input_plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest():
        return _result("collection", "invalid", missing=["input query plan changed"], inputs=inputs)
    providers = summary.get("providers")
    requested = summary.get("providers_requested")
    if not isinstance(providers, dict) or not isinstance(requested, list) or not requested:
        return _result("collection", "invalid", missing=["requested provider outcomes are missing"], inputs=inputs)
    if set(providers) != set(requested) or len(requested) != len(set(requested)):
        return _result("collection", "invalid", missing=["provider outcomes do not match requested providers"], inputs=inputs)
    missing, gaps = [], []
    for provider in requested:
        outcome = providers[provider]
        status = str(outcome.get("status", ""))
        if not _provider_terminal(status):
            missing.append(f"{provider}: unfinished or unknown provider outcome ({status or 'missing'})")
            continue
        ledger = outcome.get("query_ledger", [])
        if not isinstance(ledger, list):
            return _result("collection", "invalid", missing=[f"{provider}: invalid query ledger"], inputs=inputs)
        planned = plan.get("provider_schedules", {}).get(provider)
        if planned is not None:
            planned_rows = [(row.get("query_id"), row.get("query")) for row in planned if row.get("scheduled")]
            actual_rows = [(row.get("query_id"), row.get("query")) for row in ledger if row.get("scheduled")]
            if planned_rows != actual_rows:
                return _result("collection", "invalid", missing=[f"{provider}: executed queries differ from planned queries"], inputs=inputs)
        for row in ledger:
            if not isinstance(row, dict) or not row.get("query_id") or not row.get("query"):
                return _result("collection", "invalid", missing=[f"{provider}: malformed query outcome"], inputs=inputs)
            if row.get("scheduled") and not row.get("attempted"):
                missing.append(f"{provider}/{row['query_id']}: planned query was not attempted")
            elif row.get("scheduled") and not row.get("status"):
                missing.append(f"{provider}/{row['query_id']}: outcome missing")
            elif row.get("scheduled") and row.get("status") not in {"ok", "empty", "no_results"}:
                gaps.append(f"{provider}/{row['query_id']}: {row['status']}")
        if status not in {"ok", "empty", "no_results"}:
            gaps.append(f"{provider}: {status}")
        attempt_rows = checkpoint.get("provider_attempts", {}).get(provider, [])
        if not attempt_rows or not any(row.get("finished_at") and row.get("status") == status for row in attempt_rows):
            missing.append(f"{provider}: no matching completed attempt in checkpoint")
        raw = run_dir / "raw" / f"{provider}.json"
        if status in {"ok", "empty", "no_results", "partial"}:
            if not raw.is_file() or raw.is_symlink():
                missing.append(f"{provider}: saved provider response missing")
            else:
                inputs[str(raw.relative_to(workspace))] = _digest(raw)
    captured_records = []
    for filename, key in (("evidence.jsonl", "record_count"), ("irrelevant.jsonl", "irrelevant_count")):
        lines = [line for line in (run_dir / filename).read_text(encoding="utf-8").splitlines() if line.strip()]
        if summary.get(key) != len(lines):
            return _result("collection", "invalid", missing=[f"{filename}: count disagrees with summary"], inputs=inputs)
        try:
            for line in lines:
                captured_records.append(json.loads(line))
        except json.JSONDecodeError:
            return _result("collection", "invalid", missing=[f"{filename}: invalid JSONL"], inputs=inputs)
    if input_plan is not None:
        memberships = {}
        for record in captured_records:
            evidence_id = record.get("evidence_id")
            if not evidence_id or evidence_id in memberships:
                return _result("collection", "invalid", missing=["captured evidence IDs missing or duplicated"], inputs=inputs)
            memberships[evidence_id] = {m.get("query_id") for m in record.get("discovery_memberships", []) if isinstance(m, dict)}
        for provider in requested:
            outcome = providers[provider]
            if outcome.get("rejected_record_count", 0):
                missing.append(f"{provider}: collected records were rejected before retention")
            for row in outcome.get("query_ledger", []):
                if not row.get("scheduled"):
                    continue
                ids = row.get("record_ids")
                if not isinstance(ids, list) or len(ids) != len(set(ids)):
                    return _result("collection", "invalid", missing=[f"{provider}/{row.get('query_id')}: missing or duplicate record IDs"], inputs=inputs)
                if any(row["query_id"] not in memberships.get(evidence_id, set()) for evidence_id in ids):
                    return _result("collection", "invalid", missing=[f"{provider}/{row['query_id']}: record IDs lack retained query membership"], inputs=inputs)
                observed = {evidence_id for evidence_id, query_ids in memberships.items() if row["query_id"] in query_ids}
                if set(ids) != observed:
                    return _result("collection", "invalid", missing=[f"{provider}/{row['query_id']}: ledger omits retained query records"], inputs=inputs)
    if summary.get("collection_complete") is True and summary.get("remaining_tasks"):
        return _result("collection", "invalid", missing=["collection_complete disagrees with remaining_tasks"], inputs=inputs)
    for item in summary.get("remaining_tasks", []):
        if item.get("status") in {"request_budget_exhausted", "not_attempted", "unknown"}:
            missing.append(f"remaining task: {item}")
        else:
            gaps.append(f"remaining source or review work: {item}")
    state = "partial" if missing else "complete"
    return _result("collection", state, missing=missing, gaps=gaps,
                   actions=["Resume unfinished retrieval"] if missing else ["Review customer episodes and source coverage"],
                   inputs=inputs, execution_status="partial" if missing else "complete",
                   coverage_status="partial" if gaps or missing else "complete_for_declared_plan",
                   claim_status="not_reviewed")


def collection_receipt(workspace: Path, run_dir: Path) -> dict:
    result = validate_collection(workspace, run_dir)
    if result["status"] != "complete":
        raise ValueError("evidence_collection is not executed: " + "; ".join(result["missing_requirements"]))
    return {"contract_version": 1, "kind": "evidence_collection", "status": "valid",
            "run_dir": str(Path(run_dir).absolute().relative_to(Path(workspace).absolute())),
            "inputs": result["inputs"], "open_gaps": result["open_gaps"]}


def receipt_current(workspace: Path, receipt: dict, kind: str) -> bool:
    if not isinstance(receipt, dict) or receipt.get("contract_version") != 1 or receipt.get("kind") != kind or receipt.get("status") != "valid":
        return False
    inputs = receipt.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        return False
    for relative, digest in inputs.items():
        path = Path(workspace).absolute() / relative
        if not _local(workspace, path) or not path.is_file() or _digest(path) != digest:
            return False
    return True


def validate_research(workspace: Path, run_dir: Path) -> dict:
    workspace = Path(workspace).absolute()
    run_dir = Path(run_dir).absolute()
    capture_dir = run_dir / "evidence" if (run_dir / "evidence" / "query_plan.json").exists() else run_dir
    collection = validate_collection(workspace, capture_dir)
    if collection["status"] != "complete":
        return _result("research", collection["status"], missing=collection["missing_requirements"],
                       gaps=collection["open_gaps"], actions=collection["next_actions"], inputs=collection["inputs"])
    pack = Path(run_dir) / "customer-feedback"
    names = ("customer-feedback-source-plan.json", "customer-feedback-results.json",
             "customer-feedback-coverage.json", "evidence.jsonl", "source-review.json",
             "customer-voc-synthesis.json", "claim-ledger.json")
    missing = [name for name in names if not (pack / name).is_file()]
    if missing:
        return _result("research", "partial", missing=missing, actions=["Complete the reviewed VOC pack"], inputs=collection["inputs"])
    try:
        if __package__:
            from .finalize_customer_feedback import validate as finalize_coverage
        else:
            from finalize_customer_feedback import validate as finalize_coverage
        plan = _read(pack / names[0]); results = _read(pack / names[1]); declared = _read(pack / names[2])
        actual, errors = finalize_coverage(plan, results)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _result("research", "invalid", missing=[str(exc)], inputs=collection["inputs"])
    if errors or actual != declared:
        return _result("research", "invalid", missing=errors or ["coverage artifact differs from bound plan/results"], inputs=collection["inputs"])
    try:
        captured_by_query, captured_ids, observed_queries, captured_by_locator, bound_inputs = _capture_records(workspace, run_dir, plan)
        query_outcomes = _query_outcomes(workspace, run_dir, plan) if plan.get("execution_contract_version") == 4 else {}
        applicability_inputs = (_v4_applicability_inputs(workspace, run_dir, plan, observed_queries)
                                if plan.get("execution_contract_version") == 4 else {})
        locator_inputs = (_v4_locator_inputs(workspace, run_dir, plan)
                          if plan.get("execution_contract_version") == 4 else {})
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return _result("research", "invalid", missing=[str(exc)], inputs=collection["inputs"])
    reviews = _read(pack / "source-review.json").get("reviews", [])
    reviewed_ids = {row.get("evidence_id") for row in reviews if isinstance(row, dict)}
    pack_evidence = {}
    for line in (pack / "evidence.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        pack_evidence[record.get("evidence_id")] = record
        if record.get("evidence_id") not in captured_ids and record.get("document_id") not in captured_ids:
            return _result("research", "invalid", missing=[f"{record.get('evidence_id')}: reviewed evidence has no captured source parent"], inputs=collection["inputs"])
    for row in results.get("topic_led_voc", {}).get("cells", []):
        if not row.get("attempted"):
            continue
        query_ids = row.get("query_ids")
        source_ids = row.get("retrieved_evidence_ids")
        expected_ids = set().union(*(captured_by_query.get(query_id, set()) for query_id in (query_ids or [])))
        sampling = row.get("sampling")
        unit = sampling.get("unit") if isinstance(sampling, dict) else "observation"
        document_ids = row.get("retrieved_document_ids", source_ids)
        if (not isinstance(query_ids, list) or not query_ids or not set(query_ids) <= observed_queries
                or not isinstance(document_ids, list) or len(document_ids) != len(set(document_ids))
                or set(document_ids) != expected_ids
                or not isinstance(source_ids, list) or len(source_ids) != len(set(source_ids))):
            return _result("research", "invalid", missing=[f"topic cell {row.get('cell_id')}: claimed execution/records lack matching captured query IDs and evidence IDs"], inputs=collection["inputs"])
        if unit == "episode":
            episode_ids = {ident for ident, record in pack_evidence.items()
                           if record.get("capture_unit") == "experience"
                           and (record.get("document_id") in expected_ids or ident in expected_ids)}
            if set(source_ids) != episode_ids or row.get("retrieved_count") != len(episode_ids):
                return _result("research", "invalid", missing=[f"topic cell {row.get('cell_id')}: episode population does not reconcile to extracted source-linked experiences"], inputs=collection["inputs"])
            extracted_documents = {pack_evidence[ident].get("document_id", ident) for ident in episode_ids}
            unextracted = row.get("unextracted_document_ids")
            if (plan.get("execution_contract_version") in {3, 4}
                    and (not isinstance(unextracted, list) or len(unextracted) != len(set(unextracted))
                         or set(unextracted) != expected_ids - extracted_documents)):
                return _result("research", "invalid", missing=[f"topic cell {row.get('cell_id')}: unextracted document IDs do not reconcile to extracted episode parents"], inputs=collection["inputs"])
        elif set(source_ids) != expected_ids or row.get("retrieved_count") != len(source_ids):
            return _result("research", "invalid", missing=[f"topic cell {row.get('cell_id')}: observation population does not reconcile to captured records"], inputs=collection["inputs"])
        reviewed_scope = set(source_ids) if not isinstance(sampling, dict) else set(sampling.get("reviewed_ids", []))
        if (row.get("reviewed_count") != len(reviewed_scope) or not reviewed_scope.issubset(set(source_ids))
                or not reviewed_scope.issubset(reviewed_ids)):
            return _result("research", "invalid", missing=[f"topic cell {row.get('cell_id')}: reviewed IDs do not reconcile to the source review"], inputs=collection["inputs"])
        if plan.get("execution_contract_version") == 4:
            failed_statuses = {"failed", "blocked", "partial", "invalid_records", "rate_limited",
                               "permission_denied", "missing_credentials", "billing_required",
                               "insufficient_credits", "capture_gate_blocked", "unsupported"}
            for query_review in row.get("query_reviews", []):
                ident = query_review["query_id"]
                exact = captured_by_query.get(ident, set())
                reviewed = set(query_review["reviewed_ids"])
                status = query_review["status"]
                provider_outcomes = query_outcomes.get(ident, {})
                failed = any(status in failed_statuses for status in provider_outcomes.values())
                if (set(query_review["record_ids"]) != exact or not reviewed.issubset(exact)
                        or not reviewed.issubset(reviewed_ids)
                        or query_review["provider_outcomes"] != provider_outcomes
                        or (status == "reviewed" and exact and not reviewed)
                        or (status == "access_limited" and not failed)
                        or (status == "reviewed" and failed)):
                    return _result("research", "invalid", missing=[f"topic query {ident}: reviewed disposition differs from capture or source review"], inputs=collection["inputs"])
    for lane in results.get("source_results", []):
        for locator_row in lane.get("locator_results", []):
            locator = locator_row.get("locator")
            if not locator_row.get("attempted"):
                continue
            exact_records = captured_by_locator.get(locator, [])
            exact_ids = {record.get("evidence_id") for record in exact_records}
            sampling = locator_row.get("sampling")
            unit = sampling.get("unit") if isinstance(sampling, dict) else "observation"
            document_ids = set(locator_row.get("retrieved_document_ids", exact_ids))
            if document_ids != exact_ids:
                return _result("research", "invalid", missing=[f"entity locator {locator}: document IDs do not match exact-URL capture"], inputs=collection["inputs"])
            population = {ident for ident, record in pack_evidence.items()
                          if record.get("collection_locator") == locator
                          and (unit != "episode" or record.get("capture_unit") == "experience")}
            expected_population = population if unit == "episode" else exact_ids
            if (set(locator_row.get("retrieved_evidence_ids", expected_population)) != expected_population
                    or locator_row.get("retrieved_count", 0) != len(expected_population)):
                return _result("research", "invalid", missing=[f"entity locator {locator}: reviewed population does not match exact-URL capture"], inputs=collection["inputs"])
            accepted = set(locator_row.get("accepted_evidence_ids", []))
            if not accepted.issubset(expected_population) or any(
                    pack_evidence.get(evidence_id, {}).get("collection_locator") != locator
                    for evidence_id in accepted):
                return _result("research", "invalid", missing=[f"entity locator {locator}: accepted evidence is not from its reviewed target"], inputs=collection["inputs"])
    raw_review_gaps: list[dict] = []
    raw_review_inputs: dict[str, str] = {}
    if plan.get("execution_contract_version") == 4:
        raw_errors, raw_review_gaps, raw_review_inputs = _raw_result_review(
            workspace, run_dir, plan, results, captured_by_query)
        if raw_errors:
            return _result("research", "invalid", missing=raw_errors, inputs=collection["inputs"])
    cmd = [sys.executable, str(Path(__file__).parent / "validate_customer_voc_synthesis.py"),
           "--evidence", str(pack / "evidence.jsonl"), "--source-review", str(pack / "source-review.json"),
           "--coverage", str(pack / "customer-feedback-coverage.json"),
           "--synthesis", str(pack / "customer-voc-synthesis.json"),
           "--study-plan", str(pack / "customer-feedback-source-plan.json"),
           "--customer-segment", str(plan.get("customer_segment", ""))]
    checked = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if checked.returncode:
        return _result("research", "invalid", missing=[(checked.stdout + checked.stderr)[-3000:]], inputs=collection["inputs"])
    claims = subprocess.run([sys.executable, str(Path(__file__).parent / "validate_synthesis.py"),
        "--evidence", str(pack / "evidence.jsonl"), "--ledger", str(pack / "claim-ledger.json"),
        "--source-review", str(pack / "source-review.json"),
        "--customer-segment", str(plan.get("customer_segment", "")), "--require-verification",
        "--synthesis", str(pack / "customer-voc-synthesis.json")], capture_output=True, text=True, check=False)
    if claims.returncode:
        return _result("research", "invalid", missing=[(claims.stdout + claims.stderr)[-3000:]], inputs=collection["inputs"])
    inputs = {**collection["inputs"], **bound_inputs, **applicability_inputs, **locator_inputs, **raw_review_inputs,
              **{str((pack / name).relative_to(workspace)): _digest(pack / name) for name in names}}
    semantic_gaps = []
    if plan.get("execution_contract_version") in {3, 4}:
        review_by_id = {row.get("evidence_id"): row for row in reviews if isinstance(row, dict)}
        for cell in results.get("topic_led_voc", {}).get("cells", []):
            ids = cell.get("accepted_evidence_ids", [])
            if not ids or any(review_by_id.get(ident, {}).get("segment_relation") == "target" for ident in ids):
                continue
            resolution = cell.get("search_resolution", {})
            status = resolution.get("status") if isinstance(resolution, dict) else None
            if plan.get("execution_contract_version") == 4:
                query_states = {review.get("status") for review in cell.get("query_reviews", [])
                                if isinstance(review, dict)}
                status = "refine" if "refine" in query_states else (
                    "primary_research_needed" if "primary_research_needed" in query_states else status)
            scope = {"sampling_frame": "topic_led_voc", "cell_id": cell.get("cell_id"),
                     "locale": next((row.get("locale") for row in plan.get("topic_matrix", [])
                                     if row.get("cell_id") == cell.get("cell_id")), None)}
            if status == "primary_research_needed":
                semantic_gaps.append({**scope, "status": "primary_research_needed",
                    "reason": "Only adjacent accepted voices; reconstruct target-customer episodes"})
            elif status == "refine":
                semantic_gaps.append({**scope, "status": "refinement_required",
                    "reason": "Only adjacent accepted voices; inspect the planned refinement"})
            else:
                semantic_gaps.append({**scope, "status": "resolution_required",
                    "reason": "Only adjacent accepted voices; resolve target fit before closing the cell"})
    handoff_gaps, handoff_inputs = _primary_research_handoff(workspace, run_dir, plan, results)
    inputs.update(handoff_inputs)
    all_gaps = [*_collection_coverage_gaps(collection, plan, results, query_outcomes),
                *actual.get("coverage_gaps", []), *raw_review_gaps, *semantic_gaps, *handoff_gaps]
    unfinished = [gap for gap in all_gaps if gap.get("status") in {
        "pending", "review_pending", "discovery_required", "pending_entity_discovery", "unresolved",
        "resolution_required", "refinement_required", "failed_or_blocked", "handoff_required",
        "provider_failure"}]
    if actual.get("execution_status") != "complete" or unfinished:
        actions = ["Review the remaining selected sources or close each required source lane with an observed outcome"]
        if actual.get("accepted_evidence_ids"):
            actions.insert(0, "Publish or update case_insights.md with current reviewed findings and state the remaining coverage")
        return _result("research", "partial", gaps=all_gaps, actions=actions,
                       inputs=inputs, execution_status=actual.get("execution_status"),
                       coverage_status=actual.get("coverage_status"), claim_status=actual.get("claim_status"))
    return _result("research", "complete", gaps=all_gaps,
                   actions=["Update and publish case insights"], inputs=inputs,
                   execution_status=actual["execution_status"], coverage_status=actual["coverage_status"],
                   claim_status=actual["claim_status"])


def initial_case_evidence(business_root: Path, case_id: str, bindings=()) -> dict:
    """Assess reviewed case research; narrative files alone never qualify.

    A local run is eligible for routing. An appraisal must additionally bind its
    reviewed claim ledger, so the publisher can check the exact research input.
    Shared runs are considered only through an explicit applicable binding.
    """
    try:
        from scripts import case_workspace as cases
    except ModuleNotFoundError:
        import case_workspace as cases
    root = Path(business_root).absolute()
    scope = cases.resolve(root, case_id)
    missing = [part for part in ("customer_segments", "customer_journey", "pain_points")
               if not any(p.is_file() and p.stat().st_size for p in
                          (scope / "market_research" / part).rglob("*"))]
    if missing:
        return {"status": "missing", "missing": missing, "eligible_runs": [],
                "reason": "case segment, journey and pain analysis is incomplete"}
    local_runs = sorted(p.parent.parent for p in (scope / "market_research").rglob("customer-feedback/claim-ledger.json"))
    # Capture inputs and research assignments are relative to the Business
    # workspace, even when the claim ledger lives inside a case directory.
    candidates = [(root, run, None) for run in local_runs]
    for binding in bindings or ():
        if not isinstance(binding, dict) or not str(binding.get("path", "")).startswith("market_research/"):
            continue
        applicability = str(binding.get("applicability", ""))
        if not re.search(r"\bcase(?:[_ -]?id)?[:= -]+" + re.escape(case_id) + r"(?![a-z0-9_-])", applicability, re.I):
            continue
        if not str(binding["path"]).endswith("/customer-feedback/claim-ledger.json"):
            continue
        try:
            if binding != cases.source_binding(root, binding["path"],
                                              locator=binding["locator"], applicability=applicability):
                continue
            candidates.append((root, cases.safe(root, binding["path"]).parent.parent, binding))
        except (OSError, ValueError, KeyError):
            continue
    eligible = []
    checked = []
    for workspace, run, binding in candidates:
        result = validate_research(workspace, run)
        checked.append({"run_dir": str(run), "status": result["status"]})
        if result["status"] not in {"complete", "partial"} or "claim_status" not in result:
            continue
        pack = run / "customer-feedback"
        try:
            coverage = _read(pack / "customer-feedback-coverage.json")
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if result["status"] == "partial" and (
                not coverage.get("accepted_evidence_ids") or coverage.get("claim_status") != "scoped_synthesis_ready"):
            continue
        ledger = pack / "claim-ledger.json"
        rel = str(ledger.relative_to(root))
        eligible.append({"run_dir": str(run), "claim_ledger": rel,
                         "status": result["status"], "shared_binding": binding})
    return {"status": "eligible" if eligible else "missing", "missing": [] if eligible else ["reviewed_case_evidence"],
            "eligible_runs": eligible, "checked_runs": checked,
            "reason": "reviewed case evidence available" if eligible else "no completed or reviewed partial case research run"}


def _validate_assignment_v2(root: Path, case_id: str, assignment: dict, manifest_path: Path) -> dict:
    from case_workspace import safe
    prefix = f"cases/{case_id}/market_research/pain_points/runs/"
    missing: list[str] = []
    inputs = {str(manifest_path.relative_to(root)): _digest(manifest_path)}
    studies = assignment.get("studies")
    owners = assignment.get("capture_owners")
    requirements = assignment.get("coverage_cells")
    if not isinstance(studies, list) or not isinstance(owners, list) or not isinstance(requirements, list):
        raise ValueError("v2 assignment lacks study, capture-owner or coverage rows")
    by_run = {}
    results_by_run = {}
    for study in studies:
        if not isinstance(study, dict) or set(study) != {"run_dir", "source_plan_path", "source_plan_sha256", "relation", "applicability"}:
            raise ValueError("v2 study binding is malformed")
        rel = study["run_dir"]
        if (not isinstance(rel, str) or not rel.startswith(prefix) or rel in by_run
                or study["source_plan_path"] != rel + "/customer-feedback/customer-feedback-source-plan.json"
                or study["relation"] not in {"target", "adjacent", "context"}
                or not isinstance(study["applicability"], str) or len(study["applicability"].strip()) < 20):
            raise ValueError("v2 study scope is missing, duplicate or outside the case")
        plan_path = safe(root, study["source_plan_path"])
        if not plan_path.is_file() or plan_path.is_symlink():
            missing.append(f"study source plan is missing: {rel}")
            continue
        actual_digest = _digest(plan_path)
        inputs[study["source_plan_path"]] = actual_digest
        if actual_digest != study["source_plan_sha256"]:
            missing.append(f"study source plan changed: {rel}")
        plan = _read(plan_path)
        result = validate_research(root, safe(root, rel))
        inputs.update(result.get("inputs", {}))
        by_run[rel] = (study, plan, result)
        result_path = safe(root, rel + "/customer-feedback/customer-feedback-results.json")
        if result_path.is_file():
            results_by_run[rel] = _read(result_path)
        if result["status"] == "invalid" or (study["relation"] == "target" and result["status"] != "complete"):
            missing.append(f"{study['relation']} study is not reviewed complete: {rel} ({result['status']})")
        if study["relation"] != "target" and result["status"] == "partial" and not result.get("claim_status"):
            missing.append(f"narrow/context study has no reviewed claim chain: {rel}")
        if study["relation"] == "target":
            if (plan.get("execution_contract_version") != 4
                    or plan.get("customer_segment") != assignment.get("customer_segment")
                    or plan.get("research_design", {}).get("decision") != assignment.get("decision")):
                missing.append(f"target study does not match requested decision/segment or v4 closeout: {rel}")
    if assignment.get("parent_run") not in by_run or assignment.get("source_plan_path") != (
            assignment.get("parent_run", "") + "/customer-feedback/customer-feedback-source-plan.json"):
        missing.append("v2 delivery anchor is not a bound study")
    owner_by_capture = {}
    for owner in owners:
        if not isinstance(owner, dict) or set(owner) != {"capture_run", "study_run"}:
            raise ValueError("v2 capture owner is malformed")
        capture, study_run = owner["capture_run"], owner["study_run"]
        if capture in owner_by_capture or capture not in assignment.get("capture_runs", []) or study_run not in by_run:
            missing.append(f"duplicate, undeclared or missing primary capture owner: {capture}")
            continue
        owner_by_capture[capture] = study_run
        study, plan, _ = by_run[study_run]
        if study["relation"] != "target" or (
                capture != study_run and capture not in {row.get("run_dir") for row in plan.get("capture_inputs", [])}):
            missing.append(f"primary capture owner does not bind target capture: {capture}")
            continue
        capture_dir = safe(root, capture)
        capture_dir = capture_dir / "evidence" if (capture_dir / "evidence/query_plan.json").is_file() else capture_dir
        query_plan = _read(capture_dir / "query_plan.json")
        planned_queries = (query_plan.get("input_plan") or {}).get("queries")
        if planned_queries is None:
            planned_queries = [row for rows in query_plan.get("provider_schedules", {}).values() for row in rows]
        topic_queries = {row.get("query_id") for row in planned_queries
                         if isinstance(row, dict) and row.get("sampling_frame") != "entity_led_feedback"
                         and row.get("intent") != "entity_locator_discovery"}
        reviewed_queries = {query for cell in results_by_run.get(study_run, {}).get("topic_led_voc", {}).get("cells", [])
                            if isinstance(cell, dict) and cell.get("attempted") is True
                            for query in cell.get("query_ids", [])}
        for ident in sorted(topic_queries - reviewed_queries):
            missing.append(f"owned capture query has no attempted target-study topic cell: {capture}/{ident}")
    if set(owner_by_capture) != set(assignment.get("capture_runs", [])):
        missing.append("declared captures need exactly one primary target-study owner")
    seen_requirements = set()
    topic_locales = set()
    for requirement in requirements:
        if not isinstance(requirement, dict) or set(requirement) != {"question", "locale", "frame", "study_run", "cell_id"}:
            raise ValueError("v2 coverage requirement is malformed")
        key = tuple(requirement[field] for field in ("question", "locale", "frame", "study_run", "cell_id"))
        if key in seen_requirements:
            missing.append(f"duplicate coverage requirement: {key}")
        seen_requirements.add(key)
        locale, frame, rel, ident = (requirement[field] for field in ("locale", "frame", "study_run", "cell_id"))
        if locale not in assignment.get("locales", []) or frame not in {"topic_led_voc", "entity_led_feedback"}:
            missing.append(f"coverage requirement outside requested scope: {key}")
            continue
        if rel not in by_run or by_run[rel][0]["relation"] != "target":
            missing.append(f"target coverage cannot be closed by narrow/context study: {key}")
            continue
        plan, result = by_run[rel][1], results_by_run.get(rel, {})
        if frame == "topic_led_voc":
            topic_locales.add(locale)
            planned = any(row.get("cell_id") == ident and row.get("locale") == locale
                          for row in plan.get("topic_matrix", []))
            observed = any(row.get("cell_id") == ident and row.get("attempted") is True
                           for row in result.get("topic_led_voc", {}).get("cells", []))
        else:
            planned = any("/".join(str(row.get(x, "")) for x in ("entity_id", "locale", "source_lane")) == ident
                          and row.get("locale") == locale for row in plan.get("source_matrix", []))
            observed = planned and by_run[rel][2]["status"] == "complete"
        if not planned or not observed:
            missing.append(f"coverage cell is not planned and reviewed in target study: {key}")
    if set(assignment.get("locales", [])) != topic_locales:
        missing.append("each requested locale needs a target topic-led coverage cell")
    bound_capture_runs: set[str] = set()
    for rel, (study, plan, _) in by_run.items():
        if rel in assignment.get("capture_runs", []):
            bound_capture_runs.add(rel)  # A study can review its own collection run.
        for binding in plan.get("capture_inputs", []):
            capture = binding.get("run_dir")
            if not isinstance(capture, str) or not capture.startswith(prefix):
                missing.append(f"study binds a cross-case capture: {rel}/{capture}")
                continue
            bound_capture_runs.add(capture)
            if capture not in assignment.get("capture_runs", []):
                missing.append(f"study binds an undeclared case capture: {rel}/{capture}")
            elif capture not in owner_by_capture:
                missing.append(f"bound capture lacks primary review owner: {capture}")
    if bound_capture_runs != set(assignment.get("capture_runs", [])):
        missing.append("study capture inputs do not equal the declared case capture set")
    accepted_by_url: dict[str, set[str]] = {}
    for rel in by_run:
        pack = safe(root, rel + "/customer-feedback")
        evidence_path = pack / "evidence.jsonl"
        review_path = pack / "source-review.json"
        if not evidence_path.is_file() or not review_path.is_file():
            continue
        evidence = {row.get("evidence_id"): row for line in evidence_path.read_text(encoding="utf-8").splitlines()
                    if line.strip() for row in [json.loads(line)]}
        for review in _read(review_path).get("reviews", []):
            if review.get("status") != "accepted":
                continue
            url = evidence.get(review.get("evidence_id"), {}).get("source_url") or review.get("source_url")
            if isinstance(url, str) and url.startswith(("https://", "http://")):
                accepted_by_url.setdefault(url, set()).add(rel)
    overlaps = {url: sorted(runs) for url, runs in accepted_by_url.items() if len(runs) > 1}
    declared_overlaps = assignment.get("overlap_reviews")
    if not isinstance(declared_overlaps, list):
        raise ValueError("v2 overlap_reviews must be a list")
    seen_overlaps = set()
    for review in declared_overlaps:
        if not isinstance(review, dict) or set(review) != {"source_url", "study_runs", "disposition", "reviewer", "reason"}:
            raise ValueError("v2 overlap review is malformed")
        url = review["source_url"]
        if (url in seen_overlaps or overlaps.get(url) != sorted(review["study_runs"])
                or review["disposition"] not in {"same_incident", "distinct_interpretations"}
                or not isinstance(review["reviewer"], str) or len(review["reviewer"].strip()) < 3
                or not isinstance(review["reason"], str) or len(review["reason"].strip()) < 20):
            missing.append(f"shared source overlap has stale or invalid review: {url}")
        seen_overlaps.add(url)
    for url in sorted(set(overlaps) - seen_overlaps):
        missing.append(f"shared source needs case-level dedupe/conflict review: {url}")
    return _result("assignment", "partial" if missing else "complete", missing=missing, inputs=inputs,
                   actions=["Complete the exact target-study query, lane and coverage reviews"] if missing else [],
                   case_id=case_id, requested_locales=assignment.get("locales", []),
                   shared_source_overlaps=[{"source_url": url, "study_runs": runs, "count_once": True}
                                           for url, runs in sorted(overlaps.items())],
                   reviewed_studies=[{"run_dir": rel, "relation": study["relation"], "status": result["status"]}
                                     for rel, (study, _, result) in by_run.items()])


def validate_assignment(workspace: Path, run_dir: Path) -> dict:
    """Check the whole registered case scope against its parent and linked captures."""
    workspace, run_dir = Path(workspace).resolve(), Path(run_dir).resolve()
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from case_workspace import locate, case_manifest, safe
        root = locate(run_dir)
        relative = run_dir.relative_to(root) if root else None
        if relative is None or len(relative.parts) < 3 or relative.parts[0] != "cases":
            return _result("assignment", "partial", missing=["no registered Business case run"],
                           actions=["Register the requested case research scope"])
        case_id = relative.parts[1]
        cm = case_manifest(root, case_id)
        assignment = cm.get("research_assignment")
        if not isinstance(assignment, dict):
            return _result("assignment", "partial", missing=["case research assignment is not registered"],
                           actions=["Register the decision, locales, parent run and all linked capture runs"])
        if assignment.get("schema_version") not in {1, 2} or assignment.get("parent_run") != str(relative):
            return _result("assignment", "partial", missing=["delivery run is not the registered parent run"],
                           actions=["Run delivery on the registered parent research run"])
        manifest_path = safe(root, f"cases/{case_id}/market_research/manifest.json")
        if assignment.get("schema_version") == 2:
            return _validate_assignment_v2(root, case_id, assignment, manifest_path)
        plan_rel = assignment.get("source_plan_path")
        if plan_rel != f"{assignment['parent_run']}/customer-feedback/customer-feedback-source-plan.json":
            raise ValueError("registered source plan is not under the parent run")
        plan_path = safe(root, plan_rel)
        if not plan_path.is_file():
            return _result("assignment", "partial", missing=["registered source plan is missing"],
                           actions=["Write the requested-scope customer-feedback source plan"])
        plan = _read(plan_path)
        inputs = {str(manifest_path.relative_to(root)): _digest(manifest_path),
                  plan_rel: _digest(plan_path)}
        missing, actions = [], []
        if plan.get("execution_contract_version") != 3:
            missing.append("registered case source plan lacks the search-resolution contract")
            actions.append("Upgrade the source plan and reconcile each low-yield cell")
        design = plan.get("research_design", {})
        if design.get("decision") != assignment.get("decision"):
            missing.append("source plan decision differs from registered case assignment")
            actions.append("Reconcile the source plan with the requested case decision")
        if plan.get("customer_segment") != assignment.get("customer_segment"):
            missing.append("source plan customer segment differs from registered case assignment")
            actions.append("Reconcile the source plan customer segment")
        locales = set(assignment.get("locales", []))
        planned = set(plan.get("locales", []))
        cells = {row.get("locale") for row in plan.get("topic_matrix", []) if isinstance(row, dict)}
        for locale in sorted(locales - planned):
            missing.append(f"requested locale {locale} is absent from source plan")
        for locale in sorted(locales - cells):
            missing.append(f"requested locale {locale} has no topic-led source cell")
        if locales - planned or locales - cells:
            actions.append("Plan topic-led source cells for every registered locale")
        expected_runs = set(assignment.get("capture_runs", []))
        if any(not isinstance(rel, str) or not rel.startswith(f"cases/{case_id}/market_research/pain_points/runs/")
               for rel in expected_runs):
            raise ValueError("registered capture runs must be case-local")
        bindings = plan.get("capture_inputs", [])
        if not isinstance(bindings, list):
            raise ValueError("source plan capture_inputs must be a list")
        bound = {row.get("run_dir") for row in bindings if isinstance(row, dict)}
        for rel in sorted(expected_runs - bound):
            missing.append(f"declared capture run is not linked in source plan: {rel}")
        for rel in sorted(bound - expected_runs):
            missing.append(f"source plan has an undeclared capture run: {rel}")
        if expected_runs != bound:
            actions.append("Link every declared capture run using capture_inputs and current artifact digests")
        results_path = safe(root, assignment["parent_run"] + "/customer-feedback/customer-feedback-results.json")
        topic_query_ids = set()
        if results_path.is_file():
            results = _read(results_path)
            topic_query_ids = {ident for cell in results.get("topic_led_voc", {}).get("cells", [])
                               if isinstance(cell, dict) and cell.get("attempted") is True
                               for ident in cell.get("query_ids", [])}
            inputs[str(results_path.relative_to(root))] = _digest(results_path)
        else:
            missing.append("parent customer-feedback results are missing")
            actions.append("Record observed query and source-lane outcomes in the parent results")
        for binding in bindings:
            if not isinstance(binding, dict) or set(binding) != {"run_dir", "artifact_digests"}:
                raise ValueError("capture input binding is malformed")
            rel = binding["run_dir"]
            capture = safe(root, rel)
            check = validate_collection(root, capture)
            if check["status"] != "complete":
                missing.append(f"linked capture is not complete: {rel}")
                actions.append(f"Complete collection for {rel}")
                continue
            actual = {name: _digest(capture / name) for name in
                      ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl")}
            if binding["artifact_digests"] != actual:
                missing.append(f"linked capture digest changed: {rel}")
                actions.append(f"Rebind and review changed capture {rel}")
            inputs.update({str((capture / name).relative_to(root)): digest for name, digest in actual.items()})
            query_plan = _read(capture / "query_plan.json")
            planned_queries = (query_plan.get("input_plan") or {}).get("queries")
            if planned_queries is None:
                planned_queries = [row for rows in query_plan.get("provider_schedules", {}).values() for row in rows]
            linked_topic_queries = {row.get("query_id") for row in planned_queries
                                    if isinstance(row, dict) and row.get("sampling_frame") != "entity_led_feedback"}
            for ident in sorted(linked_topic_queries - topic_query_ids):
                missing.append(f"linked capture query has no attempted parent topic cell: {rel}/{ident}")
            if linked_topic_queries - topic_query_ids:
                actions.append("Reconcile every linked topic query and its captured IDs in parent source results")
        work_items = [{"kind": "reconcile_assignment", "scope": {"case_id": case_id},
                       "reason": item, "owner": "agent", "artifact": plan_rel,
                       "completion_check": "assignment"} for item in missing]
        return _result("assignment", "partial" if missing else "complete", missing=missing,
                       actions=list(dict.fromkeys(actions)), inputs=inputs, work_items=work_items,
                       case_id=case_id, requested_locales=sorted(locales),
                       declared_capture_runs=sorted(expected_runs))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return _result("assignment", "invalid", missing=[str(exc)])


def validate_delivery(workspace: Path, run_dir: Path) -> dict:
    workspace = Path(workspace).resolve()
    run_dir = Path(run_dir).resolve()
    assignment = validate_assignment(workspace, run_dir)
    try:
        from case_workspace import locate, case_manifest
        case_root = locate(run_dir)
        rel_run = run_dir.relative_to(case_root) if case_root else None
        current_assignment = (case_manifest(case_root, rel_run.parts[1]).get("research_assignment", {})
                              if rel_run and len(rel_run.parts) >= 2 and rel_run.parts[0] == "cases" else {})
    except (OSError, ValueError, KeyError):
        current_assignment = {}
    composed = current_assignment.get("schema_version") == 2
    research = (_result("research", "complete" if assignment["status"] == "complete" else "partial",
                        inputs=assignment.get("inputs", {}),
                        execution_status="complete" if assignment["status"] == "complete" else "partial",
                        coverage_status="complete_for_declared_plan" if assignment["status"] == "complete" else "partial",
                        claim_status="composed_reviewed" if assignment["status"] == "complete" else "pending") if composed
                else validate_research(workspace, run_dir))
    if assignment["status"] != "complete":
        return _result("delivery", assignment["status"],
                       missing=[*assignment["missing_requirements"], *research["missing_requirements"]],
                       gaps=research["open_gaps"],
                       actions=list(dict.fromkeys([*assignment["next_actions"], *research["next_actions"]])),
                       inputs={**research["inputs"], **assignment["inputs"]},
                       work_items=[*assignment["work_items"], *research["work_items"]])
    if research["status"] != "complete":
        return _result("delivery", research["status"], missing=research["missing_requirements"],
                       gaps=research["open_gaps"], actions=research["next_actions"], inputs=research["inputs"])
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_case_insights import current_status
        from case_workspace import locate
        root = locate(run_dir)
        relative = run_dir.relative_to(root) if root else None
        if root is None or relative is None or len(relative.parts) < 3 or relative.parts[0] != "cases":
            return _result("delivery", "partial", missing=["no registered Business case"],
                           actions=["Report scoped research without a case document"], inputs=research["inputs"])
        current = current_status(root, relative.parts[1])
    except (OSError, ValueError, KeyError) as exc:
        return _result("delivery", "invalid", missing=[str(exc)], inputs=research["inputs"])
    if current.get("status") != "current":
        return _result("delivery", "partial", missing=["case_insights.md is missing or stale"],
                       actions=["Publish reviewed consolidated case insights"], inputs=research["inputs"])
    if current.get("scope_status") != "complete":
        return _result("delivery", "partial", missing=["case_insights.md is a current progress snapshot, not final delivery"],
                       actions=["Resolve the remaining research scope and publish a complete case-insights revision"],
                       inputs=research["inputs"], pending_summary=current.get("pending_summary"))
    if current.get("contract_version", 1) < 2:
        return _result("delivery", "partial", missing=["current insights use the legacy publication contract"],
                       actions=["Republish exact-run insights with reviewed citations and a separate final review"],
                       inputs=research["inputs"])
    try:
        from case_workspace import insights_bindings, case_manifest
        root = locate(workspace)
        case_id = relative.parts[1]
        bound = {row["path"] for row in insights_bindings(root, case_manifest(root, case_id))}
        pack = (Path(run_dir) / "customer-feedback").absolute()
        bound_runs = ([row["run_dir"] for row in current_assignment["studies"]]
                      if composed else [str(Path(run_dir).relative_to(root))])
        required = {f"{rel}/customer-feedback/{name}" for rel in bound_runs for name in
                    ("claim-ledger.json", "source-review.json", "evidence.jsonl", "customer-feedback-coverage.json")}
        if not required.issubset(bound):
            return _result("delivery", "partial", missing=["current insights do not bind the completed research run: " +
                                                        ", ".join(sorted(required - bound))],
                           actions=["Review and incorporate this run in case_insights.md"], inputs=research["inputs"])
    except (OSError, ValueError, KeyError) as exc:
        return _result("delivery", "invalid", missing=[str(exc)], inputs=research["inputs"])
    return _result("delivery", "complete", gaps=research["open_gaps"], inputs=research["inputs"],
                   execution_status=research["execution_status"], coverage_status=research["coverage_status"],
                   claim_status=research["claim_status"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--check", choices=("collection", "research", "assignment", "delivery"), required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = {"collection": validate_collection, "research": validate_research, "assignment": validate_assignment,
              "delivery": validate_delivery}[args.check](args.workspace, args.run_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return {"complete": 0, "partial": 1, "invalid": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
