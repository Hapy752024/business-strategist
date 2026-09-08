#!/usr/bin/env python3
"""Deterministically select the narrowest specialist workflow."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "config" / "workflow-routes.json"
CATALOG_PATH = ROOT / "config" / "skill-catalog.json"


def load_routes() -> list[dict[str, Any]]:
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))["routes"]


def load_catalog() -> dict[str, dict[str, Any]]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["skills"]


def route_request(
    request: str,
    *,
    intent: str = "",
    active_manifest: dict[str, Any] | None = None,
    task_scope: str = "",
    continue_workspace: bool = False,
) -> dict[str, Any]:
    """Return a reproducible route packet from an explicit intent or phrase match."""
    text = re.sub(r"[-–—]", " ", request.casefold())
    # A conservative fallback, not a language parser. The caller should supply
    # intent/scope for complex phrasing, quotations and multi-step requests.
    action = r"(?:build|create|develop|design|write|draft|find|discover|analy[sz]e|make|plan|prepare)"
    clauses = re.split(r"[.;!?\n]|\bbut\b|(?:,\s*(?:then\s+)?|\band(?:\s+then)?\b|\bthen\b)\s*(?=(?:also\s+)?" + action + r"\b)", text)
    clauses = [re.split(r"\bwithout\b", clause, maxsplit=1)[0] for clause in clauses]
    actionable = [clause for clause in clauses if not re.search(
        r"\b(do not|don't|don’t|never|not asking|no need to)\b|"
        r"\b(keep|leave)\b.*\b(unchanged|as is|intact)\b", clause)]
    search_text = " ".join(actionable)
    # Include/with/cover clauses elaborate an outcome, not a second workflow.
    outcomes = [re.split(r"\b(?:including|with|covering)\b", clause, maxsplit=1)[0]
                for clause in actionable
                if not re.match(r"\s*(?:and\s+)?(?:include|including|cover|covering|with)\b", clause)]
    outcome_text = " ".join(outcomes)
    if task_scope not in {"", "focused", "execution", "strategy"}:
        raise ValueError(f"Unknown task scope: {task_scope}")
    requested_intent = intent.strip().casefold()
    routes = load_routes()
    if requested_intent and not any(route["id"].casefold() == requested_intent for route in routes):
        raise ValueError(f"Unknown route intent: {intent}")
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for index, route in enumerate(routes):
        if requested_intent and route["id"].casefold() == requested_intent:
            candidates.append((10_000, 1, {**route, "matched": [f"intent:{intent}"], "order": index}))
            continue
        hits = [phrase for phrase in route.get("match", [])
                if re.sub(r"[-–—]", " ", phrase.casefold()) in outcome_text]
        if hits:
            # Longer phrases are more specific; index is a stable tie-breaker.
            candidates.append((max(map(len, hits)), len(hits), {**route, "matched": hits, "order": index}))
    if candidates:
        _, _, selected = max(candidates, key=lambda item: (item[0], item[1], -item[2]["order"]))
        reason = "explicit intent" if requested_intent else "explicit phrase match"
    else:
        selected = {
            "id": "clarify",
            "skill": "business-strategist",
            "forbidden": [],
            "matched": [],
            "order": -1,
        }
        reason = "no route phrase matched"
    # Only a continuation with no new routed action may inherit a track.
    continuation = continue_workspace or bool(re.fullmatch(
        r"\s*(continue|resume|proceed)(\s+(this|the|our)(\s+workspace|\s+project)?)?[.!]?\s*", text))
    if active_manifest and not requested_intent and not candidates and continuation:
        route_id = {"website": "website-build", "brand": "standalone-brand"}.get(active_manifest.get("active_track"))
        if route_id:
            selected = {**next(route for route in routes if route["id"] == route_id), "matched": ["workspace continuation"]}
            reason = "explicit workspace continuation"
    # Distinct independently requested workflows need semantic resolution.
    if not requested_intent and len(candidates) > 1:
        clause_winners = set()
        for clause in outcomes:
            matches = [(length, hits, candidate) for length, hits, candidate in candidates
                       if any(re.sub(r"[-–—]", " ", phrase.casefold()) in clause
                              for phrase in candidate["matched"])]
            if matches:
                clause_winners.add(max(matches, key=lambda item: (item[0], item[1], -item[2]["order"]))[2]["skill"])
        if len(clause_winners) > 1:
            selected = {"id": "clarify", "skill": "business-strategist", "matched": []}
            reason = "multiple requested workflows; resolve scope before dispatch"
    skill = selected["skill"]
    metadata = load_catalog().get(skill, {})
    requested_strategy = bool(re.search(action + r"\b[^.;!?]*\bstrateg(?:y|ies)\b", outcome_text))
    scope = task_scope or ("strategy" if requested_strategy
                           else "focused" if re.search(r"\b(explain|what is|what does|why)\b", outcome_text)
                           else "execution" if re.search(r"\b(ad copy|content calendar|paid social|social campaign)\b", outcome_text)
                           else "strategy" if skill in {"marketing-strategy-builder", "social-digital-marketing-planner", "archetype-gtm-strategist"}
                           else "focused")
    artifacts = selected.get("artifacts", metadata.get("artifacts", []))
    if skill in {"marketing-strategy-builder", "social-digital-marketing-planner", "archetype-gtm-strategist"} and scope != "strategy":
        artifacts = ["requested deliverable only; preserve existing strategy" if scope == "execution" else "focused answer and material evidence limits"]
    return {
        "route_id": selected["id"],
        "skill": skill,
        "mode": selected.get("mode", "default"),
        "task_scope": scope,
        "matched": selected.get("matched", []),
        "forbidden_skills": selected.get("forbidden", []),
        "ask_question": skill == "business-strategist",
        "reason": reason,
        "prerequisites": metadata.get("prerequisites", []),
        "expected_artifacts": artifacts,
        "side_effect": metadata.get("side_effect", "unknown"),
        "estimated_cost": metadata.get("cost", "unknown"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--intent", help="Explicit route ID when the caller has already classified intent.")
    parser.add_argument("--task-scope", choices=["focused", "execution", "strategy"], default="")
    parser.add_argument("--continue-workspace", action="store_true")
    args = parser.parse_args()
    manifest = None
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    try:
        packet = route_request(args.request, intent=args.intent or "", active_manifest=manifest,
                               task_scope=args.task_scope, continue_workspace=args.continue_workspace)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
