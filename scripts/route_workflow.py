#!/usr/bin/env python3
"""Deterministically select the narrowest specialist workflow."""

from __future__ import annotations

import argparse
import json
import re
import time

try:
    from scripts.evidence_scout.workspace import manifest_lock, write_json
except ModuleNotFoundError:  # Direct CLI execution from scripts/.
    from evidence_scout.workspace import manifest_lock, write_json
from pathlib import Path
try:
    from scripts import case_workspace as cases
    from scripts import subprojects
except ModuleNotFoundError:
    import case_workspace as cases
    import subprojects
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "config" / "workflow-routes.json"
CATALOG_PATH = ROOT / "config" / "skill-catalog.json"
PAIN_GATE_MANIFEST_REL = Path("market_research") / "manifest.json"
PAIN_GATE_CONCEPTS = ["customer_segments", "customer_journey", "pain_points"]


def load_routes() -> list[dict[str, Any]]:
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))["routes"]


def load_catalog() -> dict[str, dict[str, Any]]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["skills"]


def checked_references(metadata: dict[str, Any], root: Path) -> list[str]:
    """Check bound instructions are available; this does not prove they were read."""
    references = metadata.get("required_references", [])
    if not isinstance(references, list) or any(not isinstance(p, str) or not p for p in references):
        raise ValueError("Required references must be a list of nonempty relative paths")
    for relative in references:
        path = root / relative
        if (Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve())
                or not path.is_file() or not path.stat().st_size):
            raise ValueError(f"Required reference missing, empty or outside repository: {relative}")
    return list(dict.fromkeys(references))


def missing_strategy_stages(manifest_path: Path | None, required: list[str]) -> list[str]:
    """Reuse explicit passed checkpoints, never infer a pass from filenames/text."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path else {}
    except (OSError, json.JSONDecodeError):
        data = {}
    stages = data.get("stages", {}) if isinstance(data, dict) else {}
    if isinstance(data, dict) and data.get('case_id'):
        root = cases.locate(manifest_path)
        try:
            cases.sources_current(root, data)
        except (ValueError, OSError):
            return list(required)
    missing = []
    for name in required:
        checkpoint = stages.get(name, {}) if isinstance(stages, dict) else {}
        valid = (isinstance(checkpoint, dict) and checkpoint.get("status") == "passed"
                 and checkpoint.get("gate_result") in {"pass", "conditional_pass"})
        if isinstance(data, dict) and data.get('case_id'):
            valid = valid and checkpoint.get('reviewed_revision') == data.get('assessment_revision')
        artifacts = checkpoint.get("artifacts", []) if isinstance(checkpoint, dict) else []
        valid = valid and isinstance(artifacts, list) and bool(artifacts)
        for artifact in artifacts if isinstance(artifacts, list) else []:
            relative = artifact.get("path") if isinstance(artifact, dict) else None
            if not isinstance(relative, str) or not relative or manifest_path is None:
                valid = False
                continue
            if Path(relative).is_absolute():
                valid = False
                continue
            project_root = cases.locate(manifest_path)
            root = cases.resolve(project_root, data['case_id']) if project_root and data.get('case_id') else manifest_path.parent.parent.resolve()
            path = root / relative
            try:
                if project_root:
                    cases.safe(project_root, str(path.relative_to(project_root)))
                valid = valid and path.resolve().is_relative_to(root) and path.is_file() and path.stat().st_size > 0
            except (OSError, ValueError):
                valid = False
        if not valid:
            missing.append(name)
    return missing


def pain_gate_state(project_slug: str, case_id: str = "") -> tuple[bool, Path | None]:
    """Return (passed, manifest_path) for a project's pain-first gate.

    A missing or unreadable research manifest means the gate has not passed:
    no evidence-backed segment/journey/pain analysis exists yet.
    """
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_slug):
        raise ValueError("Project must be a lowercase project slug, not a path")
    projects_root = ROOT / "projects"
    project_root = subprojects.business(projects_root / project_slug)
    manifest_path = project_root / PAIN_GATE_MANIFEST_REL
    if (project_root / cases.PROJECT).is_file() and cases.load(project_root / cases.PROJECT).get('layout_version') == 2:
        manifest_path = cases.resolve(project_root, case_id) / PAIN_GATE_MANIFEST_REL
    # Reject symlinked components even when they lead to another project in-repo.
    for path in (projects_root, manifest_path.parent.parent, manifest_path.parent, manifest_path,
                 manifest_path.parent / "manifest.lock"):
        if path.is_symlink():
            raise ValueError("Project gate paths must not be symlinks")
    if not manifest_path.exists():
        return False, None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, manifest_path
    stages = data.get("stages") if isinstance(data, dict) else None
    gate = stages.get("problem_validation") if isinstance(stages, dict) else None
    passed = (isinstance(gate, dict) and gate.get("status") == "passed"
              and gate.get("gate_result") in ("pass", "conditional_pass"))
    if isinstance(data, dict) and data.get('case_id'):
        passed = passed and gate.get('reviewed_revision') == data.get('assessment_revision')
        try:
            cases.sources_current(project_root, data)
        except (ValueError, OSError):
            passed = False
        passed = passed and not missing_strategy_stages(manifest_path, ['problem_validation'])
    return passed, manifest_path


def record_gate_override(manifest_path: Path, route_id: str, override_id: str = "", stages=()) -> None:
    """Append an auditable override event to the research manifest."""
    modern = cases.locate(manifest_path)
    if modern:
        data = cases.load(manifest_path)
        event_name = f'routing_gate_override:{route_id}'
        previous = next((e for e in data['events'] if override_id and e.get('override_id') == override_id and e.get('event') == event_name), None)
        if previous:
            if (previous.get('assessment_revision') != data.get('assessment_revision') or previous.get('stages') != list(stages)
                    or previous.get('selection_generation') != cases.read_project(modern)['selection_generation']):
                raise ValueError('stale override decision; current-scope authorization required')
            return
        data['events'].append({'ts': cases.now(), 'event': event_name, 'override_id': override_id,
                               'assessment_revision': data.get('assessment_revision'), 'stages': list(stages),
                               'selection_generation': cases.read_project(modern)['selection_generation']})
        m = cases.read_project(modern)
        import uuid
        cases.publish_locked(modern, {str(manifest_path.relative_to(modern)): cases.encoded(data)}, expected_revision=m['manifest_revision'],
                             decision_id='override-' + uuid.uuid4().hex, reason='Explicit user evidence override: ' + route_id)
        return
    with manifest_lock(manifest_path.parent.parent):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Cannot audit gate override: unreadable research manifest") from exc
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            raise ValueError("Cannot audit gate override: manifest requires an events list")
        if override_id and any(event.get("override_id") == override_id
                               and event.get("event") == f"routing_gate_override:{route_id}"
                               for event in data["events"] if isinstance(event, dict)):
            return
        data["events"].append({
            **({"override_id": override_id} if override_id else {}),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": f"routing_gate_override:{route_id}",
        })
        data["manifest_revision"] = int(data.get("manifest_revision", 0)) + 1
        data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_json(manifest_path, data)


def _route_request(
    request: str,
    *,
    intent: str = "",
    active_manifest: dict[str, Any] | None = None,
    task_scope: str = "",
    continue_workspace: bool = False,
    project: str = "",
    case_id: str = "",
    override_gate: bool = False,
    check_skill: str = "",
    override_id: str = "",
    override_stages: list[str] | None = None,
    entry_mode: str = 'standalone',
    subproject: str = '',
) -> dict[str, Any]:
    """Return a reproducible route packet from an explicit intent or phrase match."""
    if override_gate and not project:
        raise ValueError("Gate override requires --project and an existing research manifest")
    if override_stages is not None and (not isinstance(override_stages, list) or any(not isinstance(s, str) or not s for s in override_stages)):
        raise ValueError('override_stages must be a list of named evidence prerequisites')
    text = re.sub(r"[-–—]", " ", request.casefold())
    # A conservative fallback, not a language parser. The caller should supply
    # intent/scope for complex phrasing, quotations and multi-step requests.
    action = r"(?:build|create|develop|design|write|draft|find|discover|analy[sz]e|make|plan|prepare)"
    clauses = re.split(r"(?<!next)\.|[;!?\n]|\bbut\b|(?:,\s*(?:then\s+)?|\band(?:\s+then)?\b|\bthen\b)\s*(?=(?:also\s+)?" + action + r"\b)", text)
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
    # Explicit specialist names are aliases only when they identify one route.
    # Multi-mode specialists (e.g. website build/experiment) need the route ID.
    if requested_intent and not any(route["id"].casefold() == requested_intent for route in routes):
        aliases = [route for route in routes if route["skill"].casefold() == requested_intent]
        if len(aliases) == 1:
            requested_intent = aliases[0]["id"].casefold()
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
    catalog = load_catalog()
    if skill not in catalog:
        raise ValueError(f"Route targets uncatalogued skill: {skill}")
    metadata = {**catalog[skill], **catalog[skill].get("modes", {}).get(selected.get("mode", "default"), {})}
    if check_skill and (skill == "business-strategist" or check_skill != skill
                        or check_skill in selected.get("forbidden", [])):
        raise ValueError(f"Dispatch rejected: requested {check_skill}, routed {skill}")
    requested_strategy = bool(re.search(action + r"\b[^.;!?]*\bstrateg(?:y|ies)\b", outcome_text))
    scope = task_scope or ("strategy" if requested_strategy
                           else "focused" if re.search(r"\b(explain|what is|what does|why)\b", outcome_text)
                           else "execution" if re.search(r"\b(ad copy|content calendar|paid social|social campaign)\b", outcome_text)
                           else "strategy" if metadata.get("strategy_stage_prerequisites")
                           else "focused")
    artifacts = selected.get("artifacts", metadata.get("artifacts", []))
    if skill in {"marketing-strategy-builder", "social-digital-marketing-planner", "archetype-gtm-strategist"} and scope != "strategy":
        artifacts = ["requested deliverable only; preserve existing strategy" if scope == "execution" else "focused answer and material evidence limits"]
    packet = {
        "route_id": selected["id"],
        "skill": skill,
        "mode": selected.get("mode", "default"),
        "task_scope": scope,
        "matched": selected.get("matched", []),
        "forbidden_skills": selected.get("forbidden", []),
        "ask_question": skill == "business-strategist",
        "reason": reason,
        "prerequisites": metadata.get("prerequisites", []),
        "required_references": checked_references(metadata, CATALOG_PATH.parent.parent),
        "expected_artifacts": artifacts,
        "side_effect": metadata.get("side_effect", "unknown"),
        "estimated_cost": metadata.get("cost", "unknown"),
    }
    if entry_mode not in {'standalone', 'business_linked'}:
        raise ValueError('entry_mode must be standalone or business_linked')
    design = skill.startswith('brand-')
    umbrella = ROOT / 'projects' / project if project else None
    destination_name = 'website' if 'website' in skill else 'branding'
    subproject = subprojects.canonical_name(subproject)
    if subproject:
        if subproject not in subprojects.PATHS:
            raise ValueError('unknown subproject')
        if design and subproject not in {'branding', 'website', 'others'}:
            raise ValueError('design work belongs to Branding or Digital Assets')
        if not design and subproject != 'business':
            raise ValueError('this specialist belongs to Business')
        destination_name = subproject
    if design:
        packet['entry_mode'] = entry_mode
        packet['subproject'] = destination_name
        if umbrella:
            owner = cases.locate_publication(umbrella)
            if owner:
                cases.read_project(owner)
            destination = subprojects.path(umbrella, destination_name) if subprojects.is_umbrella(umbrella) else umbrella / {'website':'web-site', 'branding':'branding', 'others':'digital-assets'}[destination_name]
            packet['output_root'] = str(destination)
        if entry_mode == 'standalone':
            if case_id:
                raise ValueError('standalone design does not consume a business case; use business_linked for a case handoff')
            packet['prerequisites'] = ['Own brief and applicable design/asset approvals; no prior research required']
            packet['input_contract'] = ['requested scope', 'own brief', 'explicitly supplied optional handoffs']
            return packet
    if selected.get('mode') == 'appraisal':
        packet['expected_artifacts'] = metadata['artifacts']
    project_root = subprojects.business(umbrella) if project else None
    modern = bool(project_root and (project_root / cases.PROJECT).is_file() and cases.load(project_root / cases.PROJECT).get('layout_version') == 2)
    commitment = bool(selected.get('requires_pain_gate') or (scope == 'strategy' and metadata.get('strategy_stage_prerequisites')))
    if project and commitment and not modern and ((project_root / cases.PROJECT).exists() or (project_root / PAIN_GATE_MANIFEST_REL).exists()):
        packet.update(gate_blocked=True, gate='migration_required', first_skill=skill,
                      reason=reason + '; new execution requires explicit case-layout migration')
        return packet
    if selected.get('mode') == 'appraisal' and project and not modern:
        raise ValueError('case-appraisal requires a versioned project and registered case; migrate explicitly')
    if selected.get('mode') == 'appraisal' and not project:
        packet.update(gate_blocked=True, gate='case_scope_required', first_skill=skill)
    if case_id and not modern:
        raise ValueError('case mode requires explicit migration')
    if modern:
        project_state = cases.read_project(project_root)
        if commitment and not case_id:
            case_id = (project_state.get('selection') or {}).get('case_id', '')
        if commitment:
            execution = cases.binding(project_root, case_id)
            if design:
                cases.check_plan(project_root, cases.load(project_root / 'strategy/strategy-plan.json'))
        else:
            execution = None
        scope_root = cases.resolve(project_root, case_id)
        cm = cases.case_manifest(project_root, case_id) if case_id else {}
        if selected.get('mode') == 'appraisal':
            if not case_id:
                raise ValueError('case-appraisal requires a registered case')
            missing_baseline = [name for name in PAIN_GATE_CONCEPTS if not any(p.is_file() and p.stat().st_size for p in (scope_root / 'market_research' / name).rglob('*'))]
            if missing_baseline:
                packet.update(gate_blocked=True, gate='initial_research', first_skill='evidence-scout', missing_initial_research=missing_baseline)
        packet['case_context'] = {'project_root': str(project_root), 'case_id': case_id, 'layout_version': 2,
                                  'output_root': str(scope_root), 'assessment_revision': cm.get('assessment_revision'),
                                  'manifest_revision': cm.get('manifest_revision'),
                                  'selection_generation': project_state['selection_generation'], 'execution_binding': execution,
                                  'current_concept': str(scope_root / 'README.md'), 'source_bindings': cm.get('source_bindings', []),
                                  'open_blockers': cm.get('open_blockers', []), 'input_contract': metadata.get('inputs', []),
                                  'output_owner': metadata.get('output_owner', skill)}
        if skill == 'startup-business-builder':
            packet['output_root'] = str(project_root / 'strategy')
            packet['case_context']['output_root'] = packet['output_root']
            packet['case_context']['requested_sections'] = list(cases.PLAN_SECTIONS)
        elif design:
            packet['case_context']['output_root'] = packet['output_root']
        else:
            packet['output_root'] = str(scope_root)
        packet['case_context']['input_documents'] = {name: str(scope_root / name) for name in ('README.md', 'feasibility.md', 'business-case.md', 'economics.json') if (scope_root / name).is_file()}
        if skill == 'startup-business-builder':
            packet['required_references'] = list(dict.fromkeys(packet['required_references'] + checked_references({'required_references': ['references/case-assessment.md']}, CATALOG_PATH.parent.parent)))
    required_stages = metadata.get("strategy_stage_prerequisites", []) if scope == "strategy" else []
    if project and required_stages:
        _, manifest_path = pain_gate_state(project, case_id)
        missing = missing_strategy_stages(manifest_path, required_stages)
        packet["required_stages"] = required_stages
        packet["missing_stages"] = missing
        if missing:
            packet.update(gate_blocked=True, gate="strategy_prerequisites", first_skill={
                "intake": "idea-grill", "segment_selection": "idea-grill",
                "customer_profile": "idea-grill", "problem_validation": "evidence-scout",
                "opportunity_risk": "opportunity-risk-designer",
                "operator_playbook": "business-archetype-playbook-researcher",
            }[missing[0]])
            packet["reason"] += "; incomplete strategy prerequisites: " + ", ".join(missing)
            if override_gate:
                if manifest_path is None:
                    raise ValueError("Cannot audit gate override: research manifest is missing")
                if modern and not set(missing).issubset(override_stages or []):
                    raise ValueError('Override must explicitly name every missing evidence stage')
                record_gate_override(manifest_path, selected["id"], override_id, override_stages or [])
                packet.update(gate_blocked=False, gate_override=True)
    if project and selected.get("requires_pain_gate"):
        passed, manifest_path = pain_gate_state(project, case_id)
        if not passed:
            packet["gate_blocked"] = True
            packet["gate"] = "pain_first"
            packet["first_skill"] = "idea-grill"
            packet["gate_concepts"] = PAIN_GATE_CONCEPTS
            packet["reason"] = (
                reason
                + "; pain-first gate: problem_validation not passed for project "
                + project
                + " — establish customer segment, customer journey, and pain points with web-searched evidence first"
            )
            if override_gate:
                if modern and 'problem_validation' not in (override_stages or []):
                    raise ValueError('Override must explicitly name problem_validation')
                if manifest_path is None:
                    raise ValueError("Cannot audit gate override: research manifest is missing")
                if not packet.get("gate_override"):
                    record_gate_override(manifest_path, selected["id"], override_id, override_stages or [])
                packet["gate_blocked"] = False
                packet["gate_override"] = True
    return packet


def route_request(request: str, **kwargs) -> dict[str, Any]:
    project = kwargs.get('project', '')
    if project:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', project):
            raise ValueError('Project must be a lowercase project slug, not a path')
        root = ROOT / 'projects' / project
        if (root / cases.PENDING).exists():
            raise ValueError('pending publication: recover before dispatch')
        if (root / cases.PROJECT).is_file() and cases.load(root / cases.PROJECT).get('layout_version') in {2, 3}:
            with cases.project_lock(root):
                cases.read_project(root)
                business = subprojects.business(root)
                if business != root and (business / cases.PROJECT).exists():
                    with cases.project_lock(business):
                        return _route_request(request, **kwargs)
                return _route_request(request, **kwargs)
    return _route_request(request, **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--intent", help="Explicit route ID when the caller has already classified intent.")
    parser.add_argument("--task-scope", choices=["focused", "execution", "strategy"], default="")
    parser.add_argument("--continue-workspace", action="store_true")
    parser.add_argument("--project", default="", help="Project slug; enforces the pain-first gate on routes that require it.")
    parser.add_argument("--case", default="", help="Registered research case; execution resolves the selected case.")
    parser.add_argument('--entry-mode', choices=['standalone', 'business_linked'], default='standalone', help='Brand/website starts independently unless an explicit business handoff is requested.')
    parser.add_argument('--subproject', choices=[*subprojects.PATHS, 'business-analysis'], default='')
    parser.add_argument("--check-skill", default="", help="Reject dispatch unless this skill matches the selected route; blocked gates exit 2.")
    parser.add_argument("--override-gate", action="store_true", help="Record an explicit user override and dispatch despite a blocked pain-first gate.")
    parser.add_argument('--override-stage', action='append', default=[], help='Explicitly named evidence prerequisite; case mode only.')
    args = parser.parse_args()
    manifest = None
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    try:
        packet = route_request(args.request, intent=args.intent or "", active_manifest=manifest,
                               task_scope=args.task_scope, continue_workspace=args.continue_workspace,
                               project=args.project, case_id=args.case, entry_mode=args.entry_mode, subproject=args.subproject, override_gate=args.override_gate, override_stages=args.override_stage, check_skill=args.check_skill)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 2 if packet.get("gate_blocked") else 0


if __name__ == "__main__":
    raise SystemExit(main())
