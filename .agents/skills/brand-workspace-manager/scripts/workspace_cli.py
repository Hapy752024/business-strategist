#!/usr/bin/env python3
"""Manifest-aware brand workspace commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


STAGES = ("discovery", "research", "strategy", "logo", "colors", "typography", "imagery", "tokens", "motion", "components", "ui", "website", "marketing", "qa", "guidelines", "export")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict, *, expected_revision: int) -> None:
    current = load(path)
    actual_revision = int(current.get("manifest_revision", 1))
    if actual_revision != expected_revision:
        raise RuntimeError(
            f"manifest revision conflict: expected {expected_revision}, found {actual_revision}"
        )
    data["manifest_revision"] = actual_revision + 1
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def manifest(root: Path) -> Path:
    path = root / "brand-manifest.json"
    if not path.exists():
        raise SystemExit(f"brand manifest not found: {path}")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_path(root: Path, value: str, *, must_exist: bool = False) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise SystemExit("artifact paths must be relative to the project")
    resolved = (root / candidate).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SystemExit("artifact path escapes project") from exc
    if must_exist and not resolved.is_file():
        raise SystemExit("candidate must be an existing file inside project")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--name", required=True)
    create.add_argument("--base-dir", type=Path, default=Path("brand-projects"))
    create.add_argument("--entry-mode", choices=("standalone", "business_linked"), default="standalone")
    create.add_argument("--business-to-brand", default="")
    resume = sub.add_parser("resume")
    resume.add_argument("project_dir", type=Path)
    archive = sub.add_parser("archive-stage")
    archive.add_argument("project_dir", type=Path)
    archive.add_argument("--stage", required=True, choices=STAGES)
    record = sub.add_parser("record-option")
    record.add_argument("project_dir", type=Path)
    record.add_argument("--artifact-id", required=True)
    record.add_argument("--candidate", required=True)
    record.add_argument("--destination", required=True)
    record.add_argument("--artifact-type", default="other")
    record.add_argument("--stage", choices=STAGES)
    record.add_argument("--provenance", default="agent_generated")
    record.add_argument("--rights-status", default="not_applicable")
    record.add_argument("--source-artifact-id", action="append", default=[])
    approve = sub.add_parser("approve-option")
    approve.add_argument("project_dir", type=Path)
    approve.add_argument("--artifact-id", required=True)
    approve.add_argument("--approver", required=True)
    approve.add_argument("--notes", default="")
    approve.add_argument("--supersedes", action="append", default=[])
    promote = sub.add_parser("promote")
    promote.add_argument("project_dir", type=Path)
    promote.add_argument("--artifact-id", required=True)
    promote.add_argument("--confirm", action="store_true")
    promote.add_argument("--replace-conflict", action="store_true")
    promote.add_argument("--replacement-approver", default="")
    args = parser.parse_args()

    if args.command == "create":
        from importlib.util import spec_from_file_location, module_from_spec
        source = Path(__file__).with_name("manage-brand-workspace.py")
        spec = spec_from_file_location("manager", source)
        module = module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)
        handoff: Path | None = None
        if args.entry_mode == "business_linked":
            if not args.business_to_brand:
                raise SystemExit("business_linked entry requires --business-to-brand")
            handoff = Path(args.business_to_brand).expanduser().resolve()
            if not handoff.is_file():
                raise SystemExit("business-to-brand handoff must be an existing local file")
        root = args.base_dir / module.slugify(args.name)
        module.create_workspace(root)
        handoff_ref = ""
        if handoff is not None:
            snapshot = root / "business-to-brand.json"
            if snapshot.exists() and digest(snapshot) != digest(handoff):
                raise SystemExit("refusing to replace a different business-to-brand snapshot")
            if not snapshot.exists():
                shutil.copy2(handoff, snapshot)
            handoff_ref = snapshot.relative_to(root).as_posix()
        path = module.write_manifest(root, entry_mode=args.entry_mode, business_to_brand=handoff_ref)
        print(json.dumps({"workspace": str(root), "manifest": str(path)}, indent=2)); return 0

    root = args.project_dir.resolve()
    path = manifest(root)
    data = load(path)
    revision = int(data.get("manifest_revision", 1))
    if args.command == "resume":
        print(json.dumps({"project_dir": str(root), "next_action": data.get("next_action", ""), "open_blockers": data.get("open_blockers", []), "stages": data.get("stages", {})}, indent=2)); return 0
    if args.command == "archive-stage":
        stage = root / "stages" / args.stage
        items = [item for item in stage.iterdir()] if stage.exists() else []
        items = [item for item in items if item.name != ".gitkeep"]
        if not items: print(json.dumps({"status": "empty", "stage": args.stage})); return 0
        target = root / "old" / args.stage / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        target.mkdir(parents=True, exist_ok=False)
        for item in items: shutil.move(str(item), target / item.name)
        data.setdefault("stage_archives", []).append({"stage": args.stage, "destination": target.relative_to(root).as_posix(), "archived_at": datetime.now(timezone.utc).isoformat()})
        save(path, data, expected_revision=revision)
        print(json.dumps({"status": "archived", "destination": str(target)}, indent=2)); return 0
    if args.command == "record-option":
        if any(item.get("artifact_id") == args.artifact_id for item in data.get("artifacts", [])):
            raise SystemExit("artifact id already exists")
        candidate = project_path(root, args.candidate, must_exist=True)
        destination = project_path(root, args.destination)
        if candidate == destination:
            raise SystemExit("candidate and destination must differ")
        parts = candidate.relative_to(root).parts
        inferred_stage = parts[1] if len(parts) > 1 and parts[0] == "stages" else None
        artifact = {
            "artifact_id": args.artifact_id,
            "artifact_type": args.artifact_type,
            "stage": args.stage or inferred_stage,
            "status": "candidate",
            "candidate_path": candidate.relative_to(root).as_posix(),
            "destination": destination.relative_to(root).as_posix(),
            "sha256": digest(candidate),
            "provenance": args.provenance,
            "rights_status": args.rights_status,
            "source_artifact_ids": sorted(set(args.source_artifact_id)),
            "generated_derivatives": [],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        data.setdefault("artifacts", []).append(artifact)
        save(path, data, expected_revision=revision)
        print(json.dumps(artifact, indent=2)); return 0
    if args.command == "approve-option":
        matches = [item for item in data.get("artifacts", []) if item.get("artifact_id") == args.artifact_id]
        if len(matches) != 1: raise SystemExit("artifact id must identify exactly one option")
        if matches[0].get("status") not in {"candidate", "approved"}:
            raise SystemExit("only a candidate option can be approved")
        known_ids = {str(item.get("artifact_id")) for item in data.get("artifacts", [])}
        unknown_superseded = sorted(set(args.supersedes) - known_ids)
        if unknown_superseded:
            raise SystemExit(f"unknown superseded artifact ids: {', '.join(unknown_superseded)}")
        now = datetime.now(timezone.utc).isoformat()
        for item in data.get("artifacts", []):
            if item.get("artifact_id") in args.supersedes:
                item["status"] = "superseded"
                item["superseded_at"] = now
                item["superseded_by"] = args.artifact_id
        approval = {"artifact_id": args.artifact_id, "approver": args.approver, "timestamp": now, "notes": args.notes, "superseded_ids": sorted(set(args.supersedes))}
        matches[0]["status"] = "approved"
        matches[0]["approval"] = approval
        data.setdefault("approvals", {})[args.artifact_id] = approval
        save(path, data, expected_revision=revision)
        print(json.dumps(matches[0], indent=2)); return 0
    from importlib.util import spec_from_file_location, module_from_spec
    source = Path(__file__).parents[4] / "scripts" / "brand" / "promote_artifact.py"
    spec = spec_from_file_location("promoter", source); assert spec and spec.loader
    module = module_from_spec(spec); spec.loader.exec_module(module)
    result = module.promote(root, args.artifact_id, confirm=args.confirm, replace_conflict=args.replace_conflict, replacement_approver=args.replacement_approver)
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
