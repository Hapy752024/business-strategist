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
