#!/usr/bin/env python3
"""Initialize a durable project workspace for one business venture."""

from __future__ import annotations

import argparse
import json

from workspace import RESEARCH_MANIFEST_REL, create_project_workspace


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a project workspace (market_research + strategy tracks) with startup canvases."
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
    args = parser.parse_args()
    workspace = create_project_workspace(args.project, args.workspace, args.customer_segment)
    controller = workspace / "project-manifest.json"
    print(
        json.dumps(
            {
                "project": args.project,
                "workspace": str(workspace),
                "manifest": str(workspace / RESEARCH_MANIFEST_REL),
                "project_manifest": str(controller) if controller.exists() else "",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
