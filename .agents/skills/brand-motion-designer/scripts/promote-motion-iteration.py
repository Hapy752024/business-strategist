#!/usr/bin/env python3
"""Promote approved motion stage artifacts to canonical motion/ folder.

Usage:
  promote-motion-iteration.py --project <dir> --phase <pillar|element> --name <name> [--dry-run]

For --phase pillar, --name is the pillar name (e.g., "responsive").
For --phase element, --name is "<category>/<element>" (e.g., "press-feedback/button").

Exit codes:
  0 = promoted (or dry-run succeeded)
  1 = source not found
  2 = usage error
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--phase", required=True, choices=["pillar", "element"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    stages_root = args.project / "stages" / "motion"
    canonical_root = args.project / "motion"

    if args.phase == "pillar":
        src = stages_root / "pillars" / args.name
        dst = canonical_root / "pillars" / args.name
    else:
        parts = args.name.split("/")
        if len(parts) != 2:
            print(f"Element --name must be '<category>/<element>', got: {args.name}", file=sys.stderr)
            return 2
        src = stages_root / "elements" / parts[0] / parts[1]
        dst = canonical_root / "elements" / parts[0] / parts[1]

    if not src.exists():
        print(f"Source not found: {src}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"DRY RUN: would copy {src} -> {dst}")
        return 0

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"Promoted: {src} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
