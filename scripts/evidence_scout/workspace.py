#!/usr/bin/env python3
"""Durable project-workspace and stage-manifest helpers.

Layout: each venture is ``projects/<project-slug>/`` with workstream folders
(``market_research/``, ``strategy/``, ``branding/``, ``marketing/``,
``web-site/``, ``digital-assets/``). The research stage machine lives in
``market_research/manifest.json``; artifact paths are project-root-relative.
"""

from __future__ import annotations

import json
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import fcntl
import hashlib
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import case_workspace as cases


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT
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
PAIN_REQUIRED_SECTIONS = {
    "customer_segments": "market_research/customer_segments",
    "customer_journey": "market_research/customer_journey",
    "pain_points": "market_research/pain_points",
}


def _problem_validation_receipt(workspace: Path, artifacts: list[Path], *, case_id: str = "", revision: int = 1) -> dict:
    """Bind a problem-gate decision to reviewed current findings and sources."""
    from jsonschema import Draft202012Validator
    selected: dict[str, Path] = {}
    for artifact in artifacts:
        path = Path(artifact).absolute()
        if not path.is_file() or not path.stat().st_size:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(workspace.resolve()):
            raise ValueError("pain_points/segment/journey artifacts must be workspace-local files without symlinks")
        try:
            relative = path.relative_to(workspace.absolute()).as_posix()
        except ValueError:
            continue
        if path == workspace / PAIN_REQUIRED_SECTIONS["pain_points"] / "problem-validation-assessment.json":
            continue
        for section, prefix in PAIN_REQUIRED_SECTIONS.items():
            if relative.startswith(prefix + "/"):
                if section in selected and selected[section] != path:
                    raise ValueError(f"problem_validation requires one unambiguous current {section} artifact")
                selected[section] = path
    missing = sorted(set(PAIN_REQUIRED_SECTIONS) - set(selected))
    if missing:
        raise ValueError("problem_validation requires current artifacts for: " + ", ".join(missing))
    assessment_path = workspace / PAIN_REQUIRED_SECTIONS["pain_points"] / "problem-validation-assessment.json"
    if assessment_path not in [Path(p).absolute() for p in artifacts]:
        raise ValueError("problem_validation requires the reviewed problem-validation-assessment.json artifact")
    if assessment_path.is_symlink() or not assessment_path.is_file():
        raise ValueError("problem-validation assessment must be a workspace-local regular file")
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    schema = json.loads((REPO_ROOT / "schemas/problem-validation-assessment.schema.json").read_text(encoding="utf-8"))
    assessment_errors = list(Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(assessment))
    if assessment_errors:
        raise ValueError("problem-validation assessment is invalid: " + assessment_errors[0].message)
    if assessment.get("status") != "supported":
        raise ValueError("insufficient-evidence assessments may close discovery but cannot pass problem_validation")
    if assessment.get("case_id") != case_id or assessment.get("assessment_revision") != revision:
        raise ValueError("problem-validation assessment is stale or belongs to another case/revision")

    material: dict[str, str] = {}
    for section, path in selected.items():
        body = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(workspace.absolute()).as_posix()
        binding = assessment["section_inputs"].get(section, {})
        if binding.get("path") != relative or binding.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"{section} artifact differs from the reviewed assessment binding")
        if not body.strip():
            raise ValueError(f"{section} artifact is empty")
        material[relative] = binding["sha256"]

    pack_path = (workspace / assessment["voc_pack_path"]).absolute()
    if not pack_path.resolve().is_relative_to(workspace.resolve()):
        raise ValueError("reviewed VoC pack must remain inside the workspace without symlinked paths")
    current = pack_path
    while current != workspace and current != current.parent:
        if current.is_symlink():
            raise ValueError("reviewed VoC pack must remain inside the workspace without symlinked paths")
        current = current.parent
    required_pack_files = ("evidence.jsonl", "source-review.json", "customer-feedback-coverage.json",
                           "customer-voc-synthesis.json", "claim-ledger.json", "customer-feedback-source-plan.json")
    for name in required_pack_files:
        path = pack_path / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"reviewed VoC pack is missing a local regular file: {name}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if assessment["voc_pack_hashes"].get(name) != actual:
            raise ValueError(f"reviewed VoC pack changed since assessment review: {name}")
        material[path.relative_to(workspace).as_posix()] = actual

    synthesis = json.loads((pack_path / "customer-voc-synthesis.json").read_text(encoding="utf-8"))
    source_review = json.loads((pack_path / "source-review.json").read_text(encoding="utf-8"))
    source_plan = json.loads((pack_path / "customer-feedback-source-plan.json").read_text(encoding="utf-8"))
    needs = {str(item.get("id")): item for item in synthesis.get("customer_needs", []) if isinstance(item, dict)}
    claims = json.loads((pack_path / "claim-ledger.json").read_text(encoding="utf-8"))
    claim_ids = {str(item.get("claim_id")) for item in claims if isinstance(item, dict)}
    if (synthesis.get("schema_version") != 3 or synthesis.get("status") not in {"supported", "scoped"}
            or synthesis.get("study_id") != assessment.get("study_id")
            or synthesis.get("research_design_digest") != assessment.get("research_design_digest")
            or source_plan.get("study_id") != assessment.get("study_id")
            or source_plan.get("research_design_digest") != assessment.get("research_design_digest")
            or source_review.get("study_id") != assessment.get("study_id")
            or source_review.get("target_segment") != assessment.get("target_segment")):
        raise ValueError("assessment, research plan, source review and v3 synthesis must identify the same supported study and segment")
    if not set(assessment["finding_ids"]) <= set(needs):
        raise ValueError("problem assessment references customer findings that are absent from the current synthesis")
    associated_claims = {str(claim_id) for finding_id in assessment["finding_ids"]
                         for claim_id in needs[finding_id].get("claim_ids", [])}
    if not associated_claims or not set(assessment["claim_ids"]) <= associated_claims or not set(assessment["claim_ids"]) <= claim_ids:
        raise ValueError("problem assessment claim IDs must resolve from its selected customer findings")

    check_voc = subprocess.run([
        sys.executable, str(REPO_ROOT / "scripts/evidence_scout/validate_customer_voc_synthesis.py"),
        "--evidence", str(pack_path / "evidence.jsonl"), "--source-review", str(pack_path / "source-review.json"),
        "--coverage", str(pack_path / "customer-feedback-coverage.json"),
        "--synthesis", str(pack_path / "customer-voc-synthesis.json"),
        "--study-plan", str(pack_path / "customer-feedback-source-plan.json"),
        "--customer-segment", assessment["target_segment"],
    ], capture_output=True, text=True, check=False)
    if check_voc.returncode:
        raise ValueError("problem-validation VoC pack failed validation: " + check_voc.stdout + check_voc.stderr)
    check_claims = subprocess.run([
        sys.executable, str(REPO_ROOT / "scripts/evidence_scout/validate_synthesis.py"),
        "--evidence", str(pack_path / "evidence.jsonl"), "--ledger", str(pack_path / "claim-ledger.json"),
        "--source-review", str(pack_path / "source-review.json"),
        "--customer-segment", assessment["target_segment"], "--require-verification",
        "--synthesis", str(pack_path / "customer-voc-synthesis.json"),
    ], capture_output=True, text=True, check=False)
    if check_claims.returncode:
        raise ValueError("problem-validation claim ledger failed validation: " + check_claims.stdout + check_claims.stderr)

    assessment_relative = assessment_path.relative_to(workspace.absolute()).as_posix()
    material[assessment_relative] = hashlib.sha256(assessment_path.read_bytes()).hexdigest()
    return {"contract_version": 2, "status": "valid", "case_id": case_id,
            "assessment_revision": revision, "scope": {"case_id": case_id or workspace.name,
            "segment": assessment["target_segment"], "intent": assessment["intent"],
            "study_id": assessment["study_id"], "geography": assessment["scope"]["geography"],
            "finding_ids": assessment["finding_ids"], "claim_ids": assessment["claim_ids"],
            "limits": assessment["scope"]["limits"]},
            "inputs": material}


def _receipt_current(workspace: Path, checkpoint: dict, *, case_id: str = "", revision: int | None = None) -> bool:
    receipt = checkpoint.get("validation_receipt") if isinstance(checkpoint, dict) else None
    if not isinstance(receipt, dict) or receipt.get("contract_version") != 2 or receipt.get("status") != "valid":
        return False
    if receipt.get("case_id", "") != case_id or (revision is not None and receipt.get("assessment_revision") != revision):
        return False
    inputs = receipt.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        return False
    for relative, digest in inputs.items():
        path = Path(workspace) / relative
        try:
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                return False
        except OSError:
            return False
    return True
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
    run_dir: Path | None = None,
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
    validation_receipt = None
    if stage in {"evidence_collection", "market_discovery"} and status == "passed":
        from evidence_scout.validate_research_completion import collection_receipt, validate_research
        if run_dir is None:
            raise ValueError(f"{stage} pass requires its verifiable run_dir")
        if stage == "evidence_collection":
            validation_receipt = collection_receipt(workspace, run_dir)
        else:
            check = validate_research(workspace, run_dir)
            if check["status"] != "complete":
                raise ValueError("market_discovery research is not complete: " + "; ".join(check["missing_requirements"]))
            validation_receipt = {"contract_version": 1, "kind": "market_discovery", "status": "valid",
                                  "run_dir": str(Path(run_dir).absolute().relative_to(workspace.absolute())),
                                  "inputs": check["inputs"]}
    if stage == PAIN_GATE_STAGE and status == "passed" and not override:
        manifest = read_manifest(workspace)
        validation_receipt = _problem_validation_receipt(workspace, artifacts or [],
            revision=1)
        assessment_artifact = workspace / PAIN_REQUIRED_SECTIONS["pain_points"] / "problem-validation-assessment.json"
        if assessment_artifact.exists():
            relative_assessment = assessment_artifact.relative_to(workspace.absolute()).as_posix()
            if relative_assessment not in relative_artifacts:
                relative_artifacts.append(relative_assessment)
    with manifest_lock(workspace):
        manifest = read_manifest(workspace)
        if stage in PAIN_GATE_DOWNSTREAM and status in {"in_progress", "passed"} and not override:
            gate = manifest.get("stages", {}).get(PAIN_GATE_STAGE, {})
            if (gate.get("status") != "passed" or gate.get("gate_result") not in {"pass", "conditional_pass"}
                    or not _receipt_current(workspace, gate)):
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
        if stage == PAIN_GATE_STAGE and status != "passed":
            checkpoint.pop("validation_receipt", None)
        if stage == PAIN_GATE_STAGE and status == "passed":
            checkpoint["validation_receipt"] = validation_receipt or {
                "contract_version": 1, "status": "owner_override", "case_id": "",
                "assessment_revision": 1,
                "scope": {"case_id": workspace.name, "segment": "owner override", "limits": override},
                "inputs": {relative: hashlib.sha256((workspace / relative).read_bytes()).hexdigest()
                           for relative in relative_artifacts if not Path(relative).is_absolute() and (workspace / relative).is_file()},
            }
        elif validation_receipt is not None:
            checkpoint["validation_receipt"] = validation_receipt
        elif stage in {"evidence_collection", "market_discovery"}:
            checkpoint.pop("validation_receipt", None)
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
        research_receipt = None
        if stage in {'evidence_collection', 'market_discovery'} and status == 'passed':
            from evidence_scout.validate_research_completion import collection_receipt, validate_research
            if not kwargs.get('run_dir'):
                raise ValueError(stage + ' pass requires a verifiable run_dir')
            if stage == 'evidence_collection':
                research_receipt = collection_receipt(workspace, kwargs['run_dir'])
            else:
                check = validate_research(workspace, kwargs['run_dir'])
                if check['status'] != 'complete':
                    raise ValueError('market_discovery research is not complete: ' + '; '.join(check['missing_requirements']))
                research_receipt = {'contract_version': 1, 'kind': 'market_discovery', 'status': 'valid',
                                    'run_dir': str(Path(kwargs['run_dir']).absolute().relative_to(workspace)),
                                    'inputs': check['inputs']}
            research_receipt['case_id'] = cid
            research_receipt['assessment_revision'] = m['assessment_revision']
        if stage == PAIN_GATE_STAGE and status == 'passed' and not kwargs.get('override'):
            _problem_validation_receipt(workspace, artifacts, case_id=cid,
                                        revision=expected or kwargs.get('expected_assessment_revision', 1))
            assessment_artifact = workspace / PAIN_REQUIRED_SECTIONS["pain_points"] / "problem-validation-assessment.json"
            relative_assessment = str(assessment_artifact.relative_to(workspace))
            if relative_assessment not in rels:
                rels.append(relative_assessment)
        if stage in PAIN_GATE_DOWNSTREAM and status in {'in_progress', 'passed'}:
            if not cid:
                raise ValueError('Select a case before commitment work')
            cases.binding(root, cid)  # selection cannot be overridden
            pain = m.get('stages', {}).get(PAIN_GATE_STAGE, {})
            if not kwargs.get('override') and (pain.get('status') != 'passed' or pain.get('reviewed_revision') != m['assessment_revision']
                                                or not _receipt_current(workspace, pain, case_id=cid, revision=m['assessment_revision'])):
                raise ValueError('Commitment requires current pain-first gate')
        entry = {'stage': stage, 'status': status, 'gate_result': gate, 'timestamp': now_iso(),
                 'reviewed_revision': m['assessment_revision'],
                 'artifacts': [{'path': a, 'type': Path(a).suffix.lstrip('.') or 'file', 'description': stage} for a in rels],
                 'source_bindings': inputs + [cases.source_binding(root, str(Path(a).absolute().relative_to(root)), locator='whole artifact', applicability=stage + ' within ' + (cid or 'topic')) for a in artifacts if Path(a).is_file() and Path(a).stat().st_size],
                 'provider_failures': kwargs.get('provider_failures') or [], 'open_gaps': kwargs.get('open_gaps') or [],
                 'next_action': kwargs.get('next_action', '')}
        if stage == PAIN_GATE_STAGE and status == 'passed':
            entry['validation_receipt'] = (_problem_validation_receipt(
                workspace, artifacts, case_id=cid, revision=m['assessment_revision']) if not kwargs.get('override') else
                {'contract_version': 1, 'status': 'owner_override', 'case_id': cid,
                 'assessment_revision': m['assessment_revision'],
                 'scope': {'case_id': cid, 'segment': 'owner override', 'limits': kwargs['override']},
                 'inputs': {str(Path(a).absolute().relative_to(workspace)): hashlib.sha256(Path(a).read_bytes()).hexdigest()
                            for a in artifacts if Path(a).is_file()}})
        elif research_receipt is not None:
            entry['validation_receipt'] = research_receipt
        m.setdefault('stages', {})[stage] = entry
        m.update(current_stage=stage, updated_at=now_iso(), gate_result=gate, next_action=entry['next_action'], manifest_revision=m.get('manifest_revision', 0) + 1)
        m['artifacts'] = sorted(set(m.get('artifacts', []) + rels))
        outputs = {}
        if cid and rels and m.get('insights', {}).get('state') == 'current':
            m['insights']['state'] = 'update_pending'
            insight_path = workspace / 'case_insights.md'
            if insight_path.is_file():
                outputs[str(insight_path.relative_to(root))] = cases.pending_insights(insight_path.read_text())
        decision = 'stage-' + uuid.uuid4().hex
        m.setdefault('events', []).append({'ts': now_iso(), 'event': 'stage:' + stage, 'decision_id': decision, 'override': kwargs.get('override', '')})
        outputs[str(manifest_path.relative_to(root))] = cases.encoded(m)
        cases.publish_locked(root, outputs, expected_revision=project['manifest_revision'],
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

    if stage in {"evidence_collection", "market_discovery"} and gate in {"pass", "conditional_pass"}:
        from evidence_scout.validate_research_completion import receipt_current
        workspace = next((parent for parent in (Path(run_dir), *Path(run_dir).parents)
                          if (parent / RESEARCH_MANIFEST_REL).is_file()), None)
        if workspace is None:
            return {"can_resume": True, "reason": "Run pass has no checked research workspace",
                    "current_stage": stage, "next_action": "Locate and verify the research stage before proceeding"}
        manifest = read_manifest(workspace)
        checkpoint = manifest.get("stages", {}).get(stage, {})
        receipt = checkpoint.get("validation_receipt")
        if (checkpoint.get("status") != "passed" or not receipt_current(workspace, receipt, stage)
                or ("assessment_revision" in receipt and receipt["assessment_revision"] != manifest.get("assessment_revision"))):
            return {"can_resume": True, "reason": "Run pass has no current shared-stage validation receipt",
                    "current_stage": stage, "next_action": "Run the completion check and repair missing or stale research"}

    # Resume from authoritative current artifacts rather than a stale prose
    # next_action. This reports work; it does not perform semantic review.
    if stage == "evidence_collection":
        from evidence_scout.validate_research_completion import validate_collection, validate_research
        workspace = next((parent for parent in (Path(run_dir), *Path(run_dir).parents)
                          if (parent / RESEARCH_MANIFEST_REL).is_file()), None)
        if workspace is not None:
            capture = Path(run_dir) / "evidence" if (Path(run_dir) / "evidence" / "query_plan.json").is_file() else Path(run_dir)
            collection = validate_collection(workspace, capture)
            if collection.get("status") == "complete":
                research = validate_research(workspace, Path(run_dir))
                actions = research.get("next_actions", [])
                if actions:
                    return {"can_resume": True, "reason": "Resume work derived from current research artifacts",
                            "current_stage": stage, "next_action": actions[0],
                            "next_actions": actions, "research_status": research.get("status"),
                            "open_gaps": research.get("open_gaps", []),
                            "artifacts": run_manifest.get("artifacts", [])}
            else:
                actions = collection.get("next_actions", [])
                if actions:
                    return {"can_resume": True, "reason": "Resume collection from current capture artifacts",
                            "current_stage": stage, "next_action": actions[0],
                            "next_actions": actions, "open_gaps": collection.get("open_gaps", []),
                            "artifacts": run_manifest.get("artifacts", [])}

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
                            input_paths=(), source_bindings_file='', allow_existing=False):
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
    if directory.exists() and any(directory.iterdir()) and not allow_existing:
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
    resume: bool = False,
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
        prepare_research_output(output, allow_existing=resume)
        return output, None
    if out_dir and not case_id and not existing and not cases.locate(Path(out_dir)):
        output = Path(out_dir).absolute()
        if resume:
            return output, None
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
            if output.exists() and any(output.iterdir()) and not resume:
                raise ValueError('Research runs are immutable; choose a new output directory')
        else:
            output = workspace / workspace_subdir / run_name
        cases.safe(root, str(output.absolute().relative_to(root)))
        if resume:
            if not output.is_dir():
                raise ValueError('Resume destination does not exist')
        else:
            output.mkdir(parents=True, exist_ok=False)
            capture_run_scope(output, workspace)
        return output, workspace
    return Path(out_dir) if out_dir else workspace / workspace_subdir / run_name, None if out_dir else workspace
