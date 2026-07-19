#!/usr/bin/env python3
"""Durable topic-workspace and stage-manifest helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "templates" / "research-topic"
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


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in safe.split("-") if part)[:80] or "research-topic"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _render_template(source: Path, destination: Path, replacements: dict[str, str]) -> None:
    if destination.exists():
        return
    text = source.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def create_topic_workspace(topic: str, workspace: str = "", customer_segment: str = "") -> Path:
    path = Path(workspace).expanduser() if workspace else ROOT / "research" / "topics" / slugify(topic)
    if not path.is_absolute():
        path = ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    for relative in (
        "intake",
        "canvases",
        "market-discovery/runs",
        "evidence/runs",
        "competitors/runs",
        "competitors/marketing",
        "customer-discovery",
        "experiments",
        "go-to-market",
        "decisions",
        "playbooks",
        "reviews",
    ):
        (path / relative).mkdir(parents=True, exist_ok=True)

    replacements = {
        "TOPIC": topic,
        "TOPIC_SLUG": slugify(topic),
        "CUSTOMER_SEGMENT": customer_segment or "[UNRESOLVED]",
        "CREATED_AT": now_iso(),
    }
    for source_name, destination in (
        ("README.md", path / "README.md"),
        ("startup-thesis.md", path / "intake" / "startup-thesis.md"),
        ("business-model-canvas.md", path / "canvases" / "business-model-canvas.md"),
        ("value-proposition-canvas.md", path / "canvases" / f"value-proposition-{slugify(customer_segment or 'segment')}.md"),
    ):
        _render_template(TEMPLATE_DIR / source_name, destination, replacements)

    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        created = now_iso()
        manifest = {
            "schema_version": "1.0",
            "topic": topic,
            "topic_slug": slugify(topic),
            "created_at": created,
            "updated_at": created,
            "current_stage": "intake",
            "gate_result": "not_run",
            "blocked_reason": "",
            "next_action": "Complete the startup thesis and customer-segment hypothesis.",
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
            "events": [{"ts": created, "event": "topic_workspace_created"}],
            "open_blockers": [],
            "artifacts": [
                "README.md",
                "intake/startup-thesis.md",
                "canvases/business-model-canvas.md",
                f"canvases/value-proposition-{slugify(customer_segment or 'segment')}.md",
            ],
        }
        manifest["stages"]["intake"]["status"] = "in_progress"
        write_json(manifest_path, manifest)
    return path


def read_manifest(workspace: Path) -> dict[str, Any]:
    return json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))


def update_stage(
    workspace: Path,
    stage: str,
    *,
    status: str,
    gate_result: str,
    artifacts: list[Path] | None = None,
    provider_failures: list[dict[str, str]] | None = None,
    open_gaps: list[str] | None = None,
    next_action: str = "",
) -> None:
    if stage not in STAGES:
        raise ValueError(f"Unsupported stage: {stage}")
    manifest = read_manifest(workspace)
    timestamp = now_iso()
    relative_artifacts: list[str] = []
    for artifact in artifacts or []:
        try:
            relative_artifacts.append(str(artifact.resolve().relative_to(workspace.resolve())))
        except ValueError:
            relative_artifacts.append(str(artifact))
    checkpoint = manifest["stages"][stage]
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
    manifest["current_stage"] = stage
    manifest["gate_result"] = gate_result
    manifest["next_action"] = next_action
    manifest["events"].append({"ts": timestamp, "event": f"stage:{stage}:{status}:{gate_result}"})
    manifest["artifacts"] = sorted(set(manifest.get("artifacts", []) + relative_artifacts))
    write_json(workspace / "manifest.json", manifest)


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
    """Return summary of existing topic workspaces for the 'continue or new' prompt."""
    workspaces: list[dict[str, Any]] = []
    topics_dir = ROOT / "research" / "topics"
    if not topics_dir.exists():
        return workspaces
    for manifest_path in sorted(topics_dir.glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            workspaces.append(
                {
                    "slug": manifest_path.parent.name,
                    "path": str(manifest_path.parent),
                    "topic": manifest.get("topic", ""),
                    "current_stage": manifest.get("current_stage", "unknown"),
                    "updated_at": manifest.get("updated_at", ""),
                    "next_action": manifest.get("next_action", ""),
                    "open_blockers": manifest.get("open_blockers", []),
                    "gate_result": manifest.get("gate_result", "not_run"),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
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


def resolve_run_dir(
    *,
    topic: str,
    workspace_arg: str,
    out_dir: str,
    legacy_output: bool,
    workspace_subdir: str,
    legacy_subdir: str,
    customer_segment: str = "",
) -> tuple[Path, Path | None]:
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    run_name = f"{timestamp}-{slugify(topic)}"
    if out_dir:
        return Path(out_dir), None
    if legacy_output:
        return ROOT / "research" / "evidence-scout" / legacy_subdir / run_name, None
    workspace = create_topic_workspace(topic, workspace_arg, customer_segment)
    return workspace / workspace_subdir / run_name, workspace
