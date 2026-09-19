#!/usr/bin/env python3
"""Initialize a durable project workspace for one business venture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from workspace import RESEARCH_MANIFEST_REL, create_project_workspace, cases, ROOT, slugify


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a topic with lazy research cases; legacy workspaces are preserved."
    )
    parser.add_argument(
        "--project",
        "--topic",
        dest="project",
        required=True,
        help="Venture/project name. --topic is a deprecated alias.",
    )
    parser.add_argument("--customer-segment", default="")
    parser.add_argument("--workspace", default="", help="Optional explicit workspace path.")
    parser.add_argument("--case", default="", help="Register a specific investigated idea.")
    args = parser.parse_args()
    candidate = Path(args.workspace) if args.workspace else ROOT / 'projects' / slugify(args.project)
    from subprojects import business, is_umbrella
    if is_umbrella(candidate):
        candidate = business(candidate)
    if args.case and ((candidate / cases.PROJECT).exists() or (candidate / RESEARCH_MANIFEST_REL).exists()):
        cases.read_project(candidate)  # reject legacy case requests before any writes
    workspace = create_project_workspace(args.project, args.workspace, args.customer_segment)
    if args.case:
        cases.add_case(workspace, args.case, args.customer_segment or args.case)
    controller = workspace / "project-manifest.json"
    print(
        json.dumps(
            {
                "project": args.project,
                "workspace": str(workspace),
                "manifest": str((cases.resolve(workspace, args.case) if args.case else workspace) / RESEARCH_MANIFEST_REL) if args.case or (workspace / RESEARCH_MANIFEST_REL).exists() else None,
                "project_manifest": str(controller) if controller.exists() else "",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
