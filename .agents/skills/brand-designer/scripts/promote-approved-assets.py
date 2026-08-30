#!/usr/bin/env python3
"""Promote approved staged brand artifacts into canonical delivery folders."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROMOTIONS = {
    "stages/colors": "colors",
    "stages/typography": "typography",
    "stages/ui": "ui",
    "stages/imagery": "imagery",
    "stages/marketing": "marketing",
}


def copy_tree_contents(src: Path, dst: Path) -> int:
    if not src.exists():
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            count += 1
        elif item.is_file():
            shutil.copy2(item, target)
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    args = parser.parse_args()

    project = args.project_dir
    total = 0
    for src_rel, dst_rel in PROMOTIONS.items():
        copied = copy_tree_contents(project / src_rel, project / dst_rel)
        total += copied
        print(f"{src_rel} -> {dst_rel}: {copied}")

    manifest = project / "PACKAGE-MANIFEST.md"
    if not manifest.exists():
        manifest.write_text(
            "# Brand Package Manifest\n\n"
            "Status: canonical delivery structure.\n\n"
            "## Canonical Delivery Folders\n\n"
            "- `logos/source/`: approved SVG logo masters.\n"
            "- `logos/export/`: generated logo exports.\n"
            "- `colors/`: approved palette assets.\n"
            "- `typography/`: approved typography assets.\n"
            "- `tokens/`: implementation tokens.\n"
            "- `ui/`: approved UI previews and component guidance.\n"
            "- `imagery/`: imagery and voice guidance.\n"
            "- `marketing/`: document and presentation templates.\n"
            "- `qa/`: QA reports and screenshots.\n\n"
            "## Working History\n\n"
            "- `stages/` contains design-stage working files.\n"
            "- `old/` contains archived iterations.\n\n"
            "## Implementation Rule\n\n"
            "Use root-level canonical folders for handoff and implementation.\n",
            encoding="utf-8",
        )
        print("created PACKAGE-MANIFEST.md")

    print(f"promoted {total} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
