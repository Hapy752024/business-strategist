#!/usr/bin/env python3
"""Create brand workspaces and archive stage iterations portably."""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
from datetime import datetime
from pathlib import Path


STAGES = ["logo", "colors", "typography", "imagery", "ui", "marketing"]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "brand-project"


def create_workspace(root: Path) -> list[str]:
    paths = [
        root / "stages",
        root / "old",
        root / "tokens",
        root / "logos" / "source",
        root / "logos" / "export",
        root / "icons",
        root / "ui",
        root / "marketing",
    ]
    paths.extend(root / "stages" / stage for stage in STAGES)
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
    return [str(path) for path in paths]


def archive_stage(root: Path, stage: str) -> Path | None:
    stage_dir = root / "stages" / stage
    if not stage_dir.exists():
        stage_dir.mkdir(parents=True, exist_ok=True)
        return None

    items = [item for item in stage_dir.iterdir() if item.name != ".gitkeep"]
    if not items:
        return None

    archive_dir = root / "old" / stage / datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        shutil.move(str(item), str(archive_dir / item.name))
    return archive_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Brand/project name")
    parser.add_argument("--base-dir", type=Path, default=Path("brand-projects"))
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--archive-stage", action="store_true")
    args = parser.parse_args()

    root = args.base_dir / slugify(args.name)
    created = create_workspace(root)
    archived = None
    if args.archive_stage and args.stage:
        archived_path = archive_stage(root, args.stage)
        archived = str(archived_path) if archived_path else None

    print(json.dumps({
        "platform": platform.system(),
        "workspace": str(root),
        "created": created,
        "archived": archived,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
