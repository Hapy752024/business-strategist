#!/usr/bin/env python3
"""Manifest-aware brand workspace commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


STAGES = ("discovery", "research", "strategy", "logo", "colors", "typography", "imagery", "tokens", "motion", "components", "ui", "website", "marketing", "qa", "guidelines", "export")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def manifest(root: Path) -> Path:
    path = root / "brand-manifest.json"
    if not path.exists():
        raise SystemExit(f"brand manifest not found: {path}")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--name", required=True)
    create.add_argument("--base-dir", type=Path, default=Path("brand-projects"))
    create.add_argument("--entry-mode", choices=("standalone", "business_linked"), default="standalone")
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
    approve = sub.add_parser("approve-option")
    approve.add_argument("project_dir", type=Path)
    approve.add_argument("--artifact-id", required=True)
    promote = sub.add_parser("promote")
    promote.add_argument("project_dir", type=Path)
    promote.add_argument("--artifact-id", required=True)
    promote.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    if args.command == "create":
        from importlib.util import spec_from_file_location, module_from_spec
        source = Path(__file__).with_name("manage-brand-workspace.py")
        spec = spec_from_file_location("manager", source)
        module = module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)
        root = args.base_dir / module.slugify(args.name)
        module.create_workspace(root)
        path = module.write_manifest(root, entry_mode=args.entry_mode)
        print(json.dumps({"workspace": str(root), "manifest": str(path)}, indent=2)); return 0

    root = args.project_dir.resolve()
    path = manifest(root)
    data = load(path)
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
        print(json.dumps({"status": "archived", "destination": str(target)}, indent=2)); return 0
    if args.command == "record-option":
        candidate = (root / args.candidate).resolve()
        if root not in candidate.parents or not candidate.is_file(): raise SystemExit("candidate must be an existing file inside project")
        artifact = {"artifact_id": args.artifact_id, "status": "candidate", "candidate_path": candidate.relative_to(root).as_posix(), "destination": args.destination, "sha256": digest(candidate), "recorded_at": datetime.now(timezone.utc).isoformat()}
        data.setdefault("artifacts", []).append(artifact); save(path, data); print(json.dumps(artifact, indent=2)); return 0
    if args.command == "approve-option":
        matches = [item for item in data.get("artifacts", []) if item.get("artifact_id") == args.artifact_id]
        if len(matches) != 1: raise SystemExit("artifact id must identify exactly one option")
        matches[0]["status"] = "approved"; matches[0]["approved_at"] = datetime.now(timezone.utc).isoformat(); save(path, data); print(json.dumps(matches[0], indent=2)); return 0
    from importlib.util import spec_from_file_location, module_from_spec
    source = Path(__file__).parents[4] / "scripts" / "brand" / "promote_artifact.py"
    spec = spec_from_file_location("promoter", source); assert spec and spec.loader
    module = module_from_spec(spec); spec.loader.exec_module(module)
    result = module.promote(root, args.artifact_id, confirm=args.confirm)
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
