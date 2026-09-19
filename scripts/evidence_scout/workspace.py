#!/usr/bin/env python3
"""Durable project-workspace and stage-manifest helpers.

Layout: each venture is ``projects/<project-slug>/`` with workstream folders
(``market_research/``, ``strategy/``, ``branding/``, ``marketing/``,
``web-site/``, ``digital-assets/``). The research stage machine lives in
``market_research/manifest.json``; artifact paths are project-root-relative.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import fcntl
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import case_workspace as cases


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "templates" / "project"
RESEARCH_DIR = "market_research"
RESEARCH_MANIFEST_REL = Path(RESEARCH_DIR) / "manifest.json"
RESEARCH_LOCK_REL = Path(RESEARCH_DIR) / "manifest.lock"
STAGES = (
    "market_discovery",
    "intake",
    "segment_selection",
    "customer_profile",
    "business_model_draft",
    "problem_validation",
    "evidence_collection",
    "competitor_discovery",
    "competitor_marketing",
    "competitive_landscape",
    "offer_validation",
    "mvp_or_pilot",
    "first_customers",
    "retention",
    "channel_validation",
    "operator_playbook",
    "opportunity_risk",
    "scale_readiness",
    "synthesis",
    "final_decision",
)

# Pain-first rule: customer segment -> customer journey -> validated pain
# points come before any commitment work. ``problem_validation`` is the pain
# gate; it may only pass with web-searched evidence artifacts filed under
# market_research/pain_points/. Commitment stages require that gate.
PAIN_GATE_STAGE = "problem_validation"
PAIN_GATE_DOWNSTREAM = frozenset(
    {
        "business_model_draft",
        "offer_validation",
        "mvp_or_pilot",
        "first_customers",
        "channel_validation",
        "synthesis",
    }
)

PROJECT_SUBDIRS = (
    "market_research/customer_segments",
    "market_research/customer_journey",
    "market_research/pain_points/runs",
    "market_research/pain_point_sizing",
    "market_research/solution_alternatives/runs",
    "market_research/solution_alternatives/marketing",
    "market_research/solution_alternatives/ads",
    "market_research/solution_alternatives/landscape",
    "market_research/market_discovery/runs",
    "market_research/interviews",
    "market_research/deep_dives",
    "strategy/intake",
    "strategy/canvases",
    "strategy/decisions",
    "strategy/gtm",
    "strategy/playbooks/runs",
    "strategy/risks",
    "strategy/experiments",
)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in safe.split("-") if part)[:80] or "project"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextmanager
def manifest_lock(workspace: Path):
    """Serialize stage transitions so independent agents cannot overwrite them."""
    lock_path = workspace / RESEARCH_LOCK_REL
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _render_template(source: Path, destination: Path, replacements: dict[str, str]) -> None:
    if destination.exists():
        return
    text = source.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _project_workspace_module() -> Any:
    """Load scripts/project_workspace.py regardless of sys.path."""
    import importlib.util

    source = ROOT / "scripts" / "project_workspace.py"
    spec = importlib.util.spec_from_file_location("project_workspace", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def create_project_workspace(project: str, workspace: str = "", customer_segment: str = "", *, layout_version: int = 2) -> Path:
    try:
        from scripts import subprojects
    except ModuleNotFoundError:
        import subprojects
    projects_root = ROOT / "projects"
    path = Path(workspace).expanduser() if workspace else projects_root / slugify(project)
    if not path.is_absolute():
        path = ROOT / path
    old_roots = (
        (ROOT / "research", "projects/<slug>"),
        (ROOT / "brand-projects", "projects/<slug>/branding"),
        (ROOT / "projects" / "research", "projects/<slug>/market_research"),
        (ROOT / "projects" / "brand-projects", "projects/<slug>/branding"),
    )
    for old_root, hint in old_roots:
        if path.resolve().is_relative_to(old_root.resolve()):
            raise ValueError(f"Workspace relocated; use {hint}. Old roots are not created.")
    for reserved in (projects_root / "_infra", projects_root / "_archive"):
        if path.resolve().is_relative_to(reserved.resolve()):
            raise ValueError(f"{reserved.name} is reserved for shared infrastructure/archive, not project workspaces.")
    modern_root = cases.locate_publication(path)
    if modern_root:
        controller = cases.read_project(modern_root)
        if controller.get('controller_kind') == 'umbrella':
            if path.absolute() not in {modern_root, subprojects.path(modern_root, 'business')}:
                raise ValueError('research belongs to the business subproject')
            return subprojects.start(modern_root, 'business', project)
        if path.absolute() != modern_root:
            cid = path.name
            if cases.resolve(modern_root, cid) != path.absolute():
                raise ValueError("Workspace must be the project or registered case root")
        return path
    if layout_version == 2 and not (path / RESEARCH_MANIFEST_REL).exists() and not (path / "project-manifest.json").exists():
        return subprojects.start(path, 'business', project)
    path.mkdir(parents=True, exist_ok=True)
    for relative in PROJECT_SUBDIRS:
        (path / relative).mkdir(parents=True, exist_ok=True)

    replacements = {
        "TOPIC": project,
        "TOPIC_SLUG": slugify(project),
        "CUSTOMER_SEGMENT": customer_segment or "[UNRESOLVED]",
        "CREATED_AT": now_iso(),
    }
    for source_name, destination in (
        ("README.md", path / "README.md"),
        ("startup-thesis.md", path / "strategy" / "intake" / "startup-thesis.md"),
        ("business-model-canvas.md", path / "strategy" / "canvases" / "business-model-canvas.md"),
        ("value-proposition-canvas.md", path / "strategy" / "canvases" / f"value-proposition-{slugify(customer_segment or 'segment')}.md"),
    ):
        _render_template(TEMPLATE_DIR / source_name, destination, replacements)

    manifest_path = path / RESEARCH_MANIFEST_REL
    if not manifest_path.exists():
        created = now_iso()
        manifest = {
            "schema_version": "1.0",
            "manifest_revision": 1,
            "topic": project,
            "topic_slug": slugify(project),
            "created_at": created,
            "updated_at": created,
            "current_stage": "intake",
            "gate_result": "not_run",
            "blocked_reason": "",
            "next_action": "Complete the startup thesis, then pin the customer segment, journey, and pain points with web-searched evidence (pain-first rule).",
            "stages": {
                stage: {
                    "stage": stage,
                    "status": "pending",
                    "timestamp": created,
                    "gate_result": "not_run",
                    "artifacts": [],
                }
                for stage in STAGES
            },
            "events": [{"ts": created, "event": "project_workspace_created"}],
            "open_blockers": [],
            "artifacts": [
                "README.md",
                "strategy/intake/startup-thesis.md",
                "strategy/canvases/business-model-canvas.md",
                f"strategy/canvases/value-proposition-{slugify(customer_segment or 'segment')}.md",
            ],
        }
        manifest["stages"]["intake"]["status"] = "in_progress"
        write_json(manifest_path, manifest)

    # Create/link the controller manifest for real project directories.
    controller_script = ROOT / "scripts" / "project_workspace.py"
    if controller_script.exists() and path.resolve().parent == projects_root.resolve():
        project_workspace = _project_workspace_module()
        controller = project_workspace.create_project(path.name)
        project_workspace.link_project(
            controller,
            track="business",
            workspace=f"projects/{path.name}/{RESEARCH_DIR}",
            active=True,
        )
    return path


# Back-compat alias: older scripts and docs still say "topic workspace".
create_topic_workspace = create_project_workspace


def read_manifest(workspace: Path) -> dict[str, Any]:
    return json.loads((workspace / RESEARCH_MANIFEST_REL).read_text(encoding="utf-8"))


def _update_legacy_stage(
    workspace: Path,
    stage: str,
    *,
    status: str,
    gate_result: str,
    artifacts: list[Path] | None = None,
    provider_failures: list[dict[str, str]] | None = None,
    open_gaps: list[str] | None = None,
    next_action: str = "",
    override: str = "",
) -> None:
    if stage not in STAGES:
        raise ValueError(f"Unsupported stage: {stage}")
    if status not in {"pending", "in_progress", "passed", "failed", "blocked"}:
        raise ValueError(f"Unsupported stage status: {status}")
    if gate_result not in {"not_run", "pass", "conditional_pass", "fail"}:
        raise ValueError(f"Unsupported gate result: {gate_result}")
    if status == "passed" and gate_result not in {"pass", "conditional_pass"}:
        raise ValueError("Passed stages require a pass or conditional_pass gate result")
    if (gate_result == "pass" or (stage == PAIN_GATE_STAGE and gate_result == "conditional_pass")) and status != "passed":
        raise ValueError("A passing gate result requires status='passed'")
    override = override.strip()
    relative_artifacts: list[str] = []
    if status == "passed" and not artifacts:
        raise ValueError("Passed stages require artifacts")
    for artifact in artifacts or []:
        if status == "passed" and not artifact.exists():
            raise ValueError(f"Passed stage artifact does not exist: {artifact}")
        try:
            relative_artifacts.append(str(artifact.resolve().relative_to(workspace.resolve())))
        except ValueError:
            # Explicit --out paths predate topic workspaces and remain supported.
            # Existence is still required for a passed stage.
            relative_artifacts.append(str(artifact.resolve()))
    if stage == PAIN_GATE_STAGE and status == "passed" and not override:
        # Pain-first rule: the pain gate only passes with web-searched pain
        # evidence filed under market_research/pain_points/.
        evidence_root = workspace.resolve() / "market_research" / "pain_points"
        if not any(
            artifact.is_file() and artifact.stat().st_size > 0
            and artifact.resolve().is_relative_to(evidence_root)
            for artifact in artifacts or []
        ):
            raise ValueError(
                "problem_validation may only pass with pain-point evidence artifacts "
                "under market_research/pain_points/ (or pass override= with a recorded reason)."
            )
    with manifest_lock(workspace):
        manifest = read_manifest(workspace)
        if stage in PAIN_GATE_DOWNSTREAM and status in {"in_progress", "passed"} and not override:
            gate = manifest.get("stages", {}).get(PAIN_GATE_STAGE, {})
            if gate.get("status") != "passed" or gate.get("gate_result") not in {"pass", "conditional_pass"}:
                raise ValueError(
                    f"Stage '{stage}' requires the pain-first gate: pass '{PAIN_GATE_STAGE}' with "
                    "web-searched evidence under market_research/pain_points/ first "
                    "(or pass override= with a recorded reason)."
                )
        if stage == "final_decision" and status == "passed":
            stages = manifest.get("stages", {})
            if not any(stages.get(name, {}).get("gate_result") == "pass" for name in ("synthesis", "opportunity_risk", "market_discovery")):
                raise ValueError("Final decision requires a passed synthesis, opportunity risk, or market discovery gate")
        timestamp = now_iso()
        # Migrate older topic manifests lazily when a newly introduced stage is used.
        checkpoint = manifest.setdefault("stages", {}).setdefault(
            stage,
            {"stage": stage, "status": "pending", "timestamp": timestamp, "gate_result": "not_run", "artifacts": []},
        )
        checkpoint.update(
            {
                "status": status,
                "timestamp": timestamp,
                "gate_result": gate_result,
                "artifacts": [
                    {"path": path, "type": Path(path).suffix.lstrip(".") or "directory", "description": f"{stage} artifact"}
                    for path in relative_artifacts
                ],
                "provider_failures": provider_failures or [],
                "open_gaps": open_gaps or [],
                "next_action": next_action,
            }
        )
        manifest["updated_at"] = timestamp
        manifest["manifest_revision"] = int(manifest.get("manifest_revision", 0)) + 1
        manifest["current_stage"] = stage
        manifest["gate_result"] = gate_result
        manifest["next_action"] = next_action
        manifest["events"].append({"ts": timestamp, "event": f"stage:{stage}:{status}:{gate_result}"})
        if override:
            manifest["events"].append({"ts": timestamp, "event": f"gate_override:{stage}:{override}"})
        manifest["artifacts"] = sorted(set(manifest.get("artifacts", []) + relative_artifacts))
        write_json(workspace / RESEARCH_MANIFEST_REL, manifest)


def update_stage(workspace: Path, stage: str, **kwargs) -> None:
    workspace = Path(workspace).absolute()
    root = cases.locate(workspace)
    if not root:
        kwargs.pop('run_dir', None)
        kwargs.pop('expected_assessment_revision', None)
        return _update_legacy_stage(workspace, stage, **kwargs)
    if stage not in STAGES:
        raise ValueError("Unsupported stage: " + stage)
    status, gate = kwargs['status'], kwargs['gate_result']
    if status not in {"pending", "in_progress", "passed", "failed", "blocked"} or gate not in {"not_run", "pass", "conditional_pass", "fail"}:
        raise ValueError("Invalid stage status/gate")
    if (status == 'passed') != (gate in {'pass', 'conditional_pass'}):
        # Existing producers use conditional_pass/in_progress for incomplete lanes.
        if not (status == 'in_progress' and gate == 'conditional_pass'):
            raise ValueError("Passing checkpoint requires matching passed status")
    cid = '' if root == workspace else workspace.name
    cases.resolve(root, cid)
    artifacts = kwargs.get('artifacts') or []
    rels = []
    for a in artifacts:
        a = Path(a).absolute()
        if not a.is_relative_to(workspace):
            raise ValueError('Case checkpoints require case-local assessments')
        cases.safe(root, str(a.relative_to(root)))
        if status == 'passed' and (not a.is_file() or not a.stat().st_size):
            raise ValueError('Passed checkpoints need nonempty local files')
        rels.append(str(a.relative_to(workspace)))
    if status == 'passed' and not rels:
        raise ValueError('Passed stages require artifacts')
    if stage == PAIN_GATE_STAGE and status == 'passed' and not kwargs.get('override'):
        if not any(Path(a).is_file() and Path(a).absolute().is_relative_to(workspace / 'market_research/pain_points') for a in artifacts):
            raise ValueError('Pain gate requires pain-point evidence')
    with cases.project_lock(root):
        project = cases.read_project(root)
        manifest_path = workspace / RESEARCH_MANIFEST_REL
        if manifest_path.exists():
            m = cases.load(manifest_path)
        else:
            m = {'schema_version': '1.0', 'manifest_revision': 0, 'assessment_revision': 1,
                 'topic': project.get('title', project['slug']), 'topic_slug': project['slug'],
                 'created_at': now_iso(), 'stages': {}, 'events': [], 'artifacts': [], 'open_blockers': []}
        expected = kwargs.get('expected_assessment_revision')
        inputs = []
        if kwargs.get('run_dir'):
            context = cases.safe(root, str((Path(kwargs['run_dir']).absolute() / '.case-context.json').relative_to(root)))
            token = cases.load(context)
            if token['case_id'] != cid:
                raise ValueError('run belongs to a different case')
            expected = token['assessment_revision']
            inputs = token.get('source_bindings', [])
            for b in inputs:
                if b != cases.source_binding(root, b['path'], locator=b['locator'], applicability=b['applicability']):
                    raise ValueError('stale research input at stage closure')
        if cid and expected != m['assessment_revision']:
            raise ValueError('stale or missing expected assessment revision')
        if stage in PAIN_GATE_DOWNSTREAM and status in {'in_progress', 'passed'}:
            if not cid:
                raise ValueError('Select a case before commitment work')
            cases.binding(root, cid)  # selection cannot be overridden
            pain = m.get('stages', {}).get(PAIN_GATE_STAGE, {})
            if not kwargs.get('override') and (pain.get('status') != 'passed' or pain.get('reviewed_revision') != m['assessment_revision']):
                raise ValueError('Commitment requires current pain-first gate')
        entry = {'stage': stage, 'status': status, 'gate_result': gate, 'timestamp': now_iso(),
                 'reviewed_revision': m['assessment_revision'],
                 'artifacts': [{'path': a, 'type': Path(a).suffix.lstrip('.') or 'file', 'description': stage} for a in rels],
                 'source_bindings': inputs + [cases.source_binding(root, str(Path(a).absolute().relative_to(root)), locator='whole artifact', applicability=stage + ' within ' + (cid or 'topic')) for a in artifacts if Path(a).is_file() and Path(a).stat().st_size],
                 'provider_failures': kwargs.get('provider_failures') or [], 'open_gaps': kwargs.get('open_gaps') or [],
                 'next_action': kwargs.get('next_action', '')}
        m.setdefault('stages', {})[stage] = entry
        m.update(current_stage=stage, updated_at=now_iso(), gate_result=gate, next_action=entry['next_action'], manifest_revision=m.get('manifest_revision', 0) + 1)
        m['artifacts'] = sorted(set(m.get('artifacts', []) + rels))
        decision = 'stage-' + uuid.uuid4().hex
        m.setdefault('events', []).append({'ts': now_iso(), 'event': 'stage:' + stage, 'decision_id': decision, 'override': kwargs.get('override', '')})
        cases.publish_locked(root, {str(manifest_path.relative_to(root)): cases.encoded(m)}, expected_revision=project['manifest_revision'],
                             decision_id=decision, reason=f'{cid or "topic"}: {stage} {status}', affected=[cid] if cid else [])


def create_run_manifest(
    run_dir: Path,
    *,
    subject: str,
    run_type: str,
    stage: str = "intake",
    artifacts: list[Path] | None = None,
    sources: list[str] | None = None,
    next_action: str = "",
) -> Path:
    """Create a per-run manifest tracking run state for resume/replay."""
    timestamp = now_iso()
    run_manifest: dict[str, Any] = {
        "run_id": run_dir.name,
        "subject": subject,
        "run_date": timestamp,
        "run_type": run_type,
        "current_stage": stage,
        "stage_status": "in_progress",
        "gate_result": "not_run",
        "artifacts": [str(a) for a in (artifacts or [])],
        "sources": sources or [],
        "open_gaps": [],
        "blocked_reason": "",
        "next_action": next_action,
        "events": [{"ts": timestamp, "event": "run_created"}],
    }
    write_json(run_dir / "run-manifest.json", run_manifest)
    return run_dir / "run-manifest.json"


def read_run_manifest(run_dir: Path) -> dict[str, Any] | None:
    """Read a per-run manifest, returning None if absent."""
    path = run_dir / "run-manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_run_manifest(
    run_dir: Path,
    *,
    stage: str | None = None,
    stage_status: str | None = None,
    gate_result: str | None = None,
    artifacts: list[Path] | None = None,
    open_gaps: list[str] | None = None,
    blocked_reason: str = "",
    next_action: str = "",
    event: str = "",
    record_count: int | None = None,
    source_count: int | None = None,
) -> None:
    """Update a per-run manifest with new stage state and event."""
    run_manifest = read_run_manifest(run_dir)
    if run_manifest is None:
        run_manifest = {
            "run_id": run_dir.name,
            "subject": "",
            "run_date": now_iso(),
            "run_type": "unknown",
            "current_stage": "intake",
            "stage_status": "in_progress",
            "gate_result": "not_run",
            "artifacts": [],
            "sources": [],
            "open_gaps": [],
            "blocked_reason": "",
            "next_action": "",
            "events": [],
        }
    timestamp = now_iso()
    if stage is not None:
        run_manifest["current_stage"] = stage
    if stage_status is not None:
        run_manifest["stage_status"] = stage_status
    if gate_result is not None:
        run_manifest["gate_result"] = gate_result
    if artifacts is not None:
        existing = run_manifest.get("artifacts", [])
        run_manifest["artifacts"] = sorted(set(existing + [str(a) for a in artifacts]))
    if open_gaps is not None:
        run_manifest["open_gaps"] = open_gaps
    if blocked_reason:
        run_manifest["blocked_reason"] = blocked_reason
    if next_action:
        run_manifest["next_action"] = next_action
    if record_count is not None:
        run_manifest["record_count"] = record_count
    if source_count is not None:
        run_manifest["source_count"] = source_count
    event_text = event or f"stage:{stage or run_manifest['current_stage']}:{stage_status or run_manifest['stage_status']}:{gate_result or run_manifest['gate_result']}"
    run_manifest["events"].append({"ts": timestamp, "event": event_text})
    write_json(run_dir / "run-manifest.json", run_manifest)


def find_existing_workspaces() -> list[dict[str, Any]]:
    """Return summary of existing project workspaces for the 'continue or new' prompt."""
    workspaces: list[dict[str, Any]] = []
    projects_root = ROOT / "projects"
    if not projects_root.exists():
        return workspaces
    for manifest_path in sorted([*projects_root.glob(f"*/{RESEARCH_DIR}/manifest.json"), *projects_root.glob(f"*/business/{RESEARCH_DIR}/manifest.json"), *projects_root.glob(f"*/business-analysis/{RESEARCH_DIR}/manifest.json")]):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            project_manifest = manifest_path.parent.parent / "project-manifest.json"
            entry: dict[str, Any] = {
                "slug": cases.load(project_manifest).get('slug', manifest_path.parent.parent.name) if project_manifest.exists() else manifest_path.parent.parent.name,
                "path": str(manifest_path.parent.parent),
                "topic": manifest.get("topic", ""),
                "current_stage": manifest.get("current_stage", "unknown"),
                "updated_at": manifest.get("updated_at", ""),
                "next_action": manifest.get("next_action", ""),
                "open_blockers": manifest.get("open_blockers", []),
                "gate_result": manifest.get("gate_result", "not_run"),
            }
            if project_manifest.exists():
                entry["project_manifest"] = str(project_manifest)
            workspaces.append(entry)
        except (json.JSONDecodeError, OSError):
            continue
    known = {item['path'] for item in workspaces}
    for controller in sorted([*projects_root.glob('*/project-manifest.json'), *projects_root.glob('*/business/project-manifest.json'), *projects_root.glob('*/business-analysis/project-manifest.json')]):
        if cases.load(controller).get('layout_version') != 2:
            continue
        root = controller.parent
        m = cases.read_project(root)
        for cid, entry in m['cases'].items():
            if entry.get('retired'):
                continue
            cm = cases.case_manifest(root, cid)
            workspaces.append({'slug': m['slug'], 'case_id': cid, 'path': str(root / entry['path']),
                               'topic': entry['title'], 'current_stage': cm.get('current_stage'),
                               'updated_at': cm.get('updated_at'), 'next_action': cm.get('next_action'),
                               'open_blockers': cm.get('open_blockers', []), 'project_manifest': str(controller)})
        if str(root) not in known and not m['cases']:
            workspaces.append({'slug': m['slug'], 'path': str(root), 'topic': m.get('title'), 'current_stage': 'market_discovery', 'updated_at': m['updated_at'], 'next_action': m['next_action'], 'open_blockers': []})
    return workspaces


def resume_from_last_gate(run_dir: Path) -> dict[str, Any]:
    """Determine the resume state from a run manifest. Returns the next action to take."""
    run_manifest = read_run_manifest(run_dir)
    if run_manifest is None:
        return {
            "can_resume": False,
            "reason": "No run manifest found",
            "current_stage": "unknown",
            "next_action": "Start fresh",
        }
    gate = run_manifest.get("gate_result", "not_run")
    stage = run_manifest.get("current_stage", "unknown")
    status = run_manifest.get("stage_status", "unknown")

    if gate == "pass":
        return {
            "can_resume": True,
            "reason": f"Stage '{stage}' passed. Proceed to next stage.",
            "current_stage": stage,
            "next_action": run_manifest.get("next_action", "Proceed to next stage"),
            "artifacts": run_manifest.get("artifacts", []),
        }
    if gate == "conditional_pass":
        gaps = run_manifest.get("open_gaps", [])
        return {
            "can_resume": True,
            "reason": f"Stage '{stage}' conditionally passed. Open gaps: {gaps}",
            "current_stage": stage,
            "next_action": run_manifest.get("next_action", "Address open gaps before proceeding"),
            "artifacts": run_manifest.get("artifacts", []),
            "open_gaps": gaps,
        }
    if gate == "fail":
        return {
            "can_resume": True,
            "reason": f"Stage '{stage}' failed. Re-attempt with adjusted parameters.",
            "current_stage": stage,
            "next_action": run_manifest.get("next_action", "Re-attempt current stage"),
            "artifacts": run_manifest.get("artifacts", []),
        }
    if status == "in_progress":
        return {
            "can_resume": True,
            "reason": f"Stage '{stage}' was in progress. Resume from last event.",
            "current_stage": stage,
            "next_action": run_manifest.get("next_action", "Continue from where you left off"),
            "artifacts": run_manifest.get("artifacts", []),
        }
    return {
        "can_resume": True,
        "reason": f"Stage '{stage}' not yet run. Start from beginning.",
        "current_stage": stage,
        "next_action": run_manifest.get("next_action", "Start the workflow"),
        "artifacts": run_manifest.get("artifacts", []),
    }


def capture_run_scope(run_dir: Path, scope: Path, source_bindings=()) -> None:
    root = cases.locate(scope)
    if root:
        with cases.project_lock(root):
            cases.read_project(root)
            cases.safe(root, str(Path(run_dir).absolute().relative_to(root)))
            cid = '' if scope == root else scope.name
            cases.resolve(root, cid)
            manifest = scope / RESEARCH_MANIFEST_REL
            revision = cases.load(manifest).get('assessment_revision', 1) if manifest.exists() else 1
            cases.atomic(run_dir / '.case-context.json', cases.encoded({'case_id': cid, 'assessment_revision': revision,
                         'source_bindings': list(source_bindings)}))


def prepare_research_output(output: Path, *, workspace_arg='', case_id='', is_file=False,
                            input_paths=(), source_bindings_file=''):
    """Preflight direct builders before writing. V2 outputs are fresh run artifacts."""
    output = Path(output).absolute()
    try:
        from scripts.subprojects import business
    except ModuleNotFoundError:
        from subprojects import business
    if workspace_arg:
        workspace_arg = str(business(Path(workspace_arg)))
    owner = cases.locate_publication(output)
    if owner and cases.read_project(owner).get('controller_kind') == 'umbrella':
        raise ValueError('research outputs require an initialized business subproject')
    destination_root = cases.locate(output)
    workspace_root = cases.locate(Path(workspace_arg)) if workspace_arg else None
    if workspace_arg and destination_root != workspace_root:
        if destination_root or workspace_root:
            raise ValueError('workspace and destination authorities conflict')
    root = destination_root or workspace_root
    if not root:
        if case_id:
            raise ValueError('Explicit migration required for case mode')
        return Path(workspace_arg) if workspace_arg else None
    m = cases.read_project(root)
    if workspace_arg:
        scope = cases.resolve(root, case_id) if case_id else Path(workspace_arg).absolute()
    else:
        scope = root
        for cid in m['cases']:
            candidate = cases.resolve(root, cid)
            if output.is_relative_to(candidate):
                scope = candidate
                break
        if case_id:
            scope = cases.resolve(root, case_id)
    if scope != root and scope not in [cases.resolve(root, cid) for cid in m['cases'] if not m['cases'][cid].get('retired')]:
        raise ValueError('Unregistered research scope')
    cases.safe(root, str(output.relative_to(root)))
    relative = output.relative_to(scope)
    if relative.parts[0] != 'market_research' or 'runs' not in relative.parts or 'cases' in relative.parts:
        raise ValueError('Case research builders must write immutable research runs')
    directory = output.parent if is_file else output
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Research runs are immutable; choose a fresh run directory')
    bindings = research_input_bindings(root, scope, input_paths, source_bindings_file)
    directory.mkdir(parents=True, exist_ok=True)
    capture_run_scope(directory, scope, bindings)
    return scope


def research_input_bindings(root, scope, input_paths, source_bindings_file=''):
    """Record actual inputs and their declared upstream lineage, never inferred uses."""
    declared = cases.load(Path(source_bindings_file)) if source_bindings_file else []
    if not isinstance(declared, list):
        raise ValueError('source bindings must be a list')
    bindings, visited, visiting = {}, set(), set()

    def check(binding):
        current = cases.source_binding(root, binding['path'], locator=binding['locator'], applicability=binding['applicability'])
        if current != binding:
            raise ValueError('stale research input binding')
        bindings[(binding['path'], binding['locator'], binding['applicability'])] = binding

    for b in declared:
        check(b)

    def visit(path):
        path = cases.safe(root, str(Path(path).absolute().relative_to(root)))
        if path in visiting:
            raise ValueError('cyclic declared research dependencies')
        if len(visiting) >= 64:
            raise ValueError('research dependency chain exceeds bounded review scope')
        if path in visited:
            return
        visiting.add(path)
        relative = str(path.relative_to(root))
        if not any(b['path'] == relative for b in bindings.values()):
            if not path.is_relative_to(scope) or scope == root:
                raise ValueError('shared research input requires explicit --source-bindings applicability: ' + relative)
            check(cases.source_binding(root, relative, locator='whole artifact', applicability='Input to derived research within ' + scope.name))
        # Only declared run contexts confer upstream dependencies. Raw bytes stay put.
        for parent in path.parents:
            if parent == root or not parent.is_relative_to(root):
                break
            context = cases.safe(root, str((parent / '.case-context.json').relative_to(root)))
            if context.is_file():
                for upstream in cases.load(context).get('source_bindings', []):
                    check(upstream)
                    visit(cases.safe(root, upstream['path']))
                break
        visiting.remove(path)
        visited.add(path)
    for path in input_paths:
        if path:
            visit(Path(path))
    return list(bindings.values())


def resolve_run_dir(
    *,
    topic: str,
    workspace_arg: str,
    out_dir: str,
    legacy_output: bool,
    workspace_subdir: str,
    legacy_subdir: str = "",
    customer_segment: str = "",
    case_id: str = "",
) -> tuple[Path, Path | None]:
    try:
        from scripts.subprojects import business, is_umbrella
    except ModuleNotFoundError:
        from subprojects import business, is_umbrella
    if workspace_arg and is_umbrella(Path(workspace_arg)):
        # Initialization below may create Business; explicit outputs cannot cross
        # into another independent subproject.
        if (business(Path(workspace_arg)) / cases.PROJECT).exists():
            workspace_arg = str(business(Path(workspace_arg)))
    owner = cases.locate_publication(Path(out_dir)) if out_dir else None
    if owner and cases.read_project(owner).get('controller_kind') == 'umbrella':
        raise ValueError('research outputs require an initialized business subproject')
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    run_name = f"{timestamp}-{slugify(topic)}-{uuid.uuid4().hex[:12]}"
    existing = cases.locate(Path(workspace_arg)) if workspace_arg else None
    candidate = Path(workspace_arg) if workspace_arg else ROOT / 'projects' / slugify(topic)
    if case_id and not existing and ((candidate / RESEARCH_MANIFEST_REL).exists() or (candidate / cases.PROJECT).exists()):
        raise ValueError('Explicit migration required for case mode')
    output_root = cases.locate(Path(out_dir)) if out_dir else None
    if out_dir and workspace_arg and output_root != existing and (output_root or existing):
        raise ValueError('workspace and destination authorities conflict')
    if output_root and not workspace_arg and not case_id:
        # A parent producer may collect evidence into its own immutable run.
        output = Path(out_dir).absolute()
        prepare_research_output(output)
        return output, None
    if out_dir and not case_id and not existing and not cases.locate(Path(out_dir)):
        return Path(out_dir), None
    if legacy_output:
        raise ValueError(
            "--legacy-output layout removed: projects/research/evidence-scout is now "
            "projects/_archive (read-only). Use --out-dir for an explicit path."
        )
    workspace = create_project_workspace(topic, workspace_arg, customer_segment)
    root = cases.locate(workspace)
    if case_id:
        if not root:
            raise ValueError('Explicit migration required for case mode')
        workspace = cases.resolve(root, case_id)
    if root:
        if not workspace_subdir.startswith('market_research/'):
            raise ValueError('Research producers may only allocate research outputs')
        if out_dir:
            output = Path(out_dir).absolute()
            if not output.is_relative_to(workspace / workspace_subdir):
                raise ValueError('out-dir conflicts with case/output purpose')
            cases.safe(root, str(output.relative_to(root)))
            if output.exists() and any(output.iterdir()):
                raise ValueError('Research runs are immutable; choose a new output directory')
        else:
            output = workspace / workspace_subdir / run_name
        cases.safe(root, str(output.absolute().relative_to(root)))
        output.mkdir(parents=True, exist_ok=False)
        capture_run_scope(output, workspace)
        return output, workspace
    return Path(out_dir) if out_dir else workspace / workspace_subdir / run_name, None if out_dir else workspace
