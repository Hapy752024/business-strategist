#!/usr/bin/env python3
"""Initialize a durable research workspace for one business topic."""

from __future__ import annotations

import argparse
import json

from workspace import create_topic_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a topic research workspace and startup canvases.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--customer-segment", default="")
    parser.add_argument("--workspace", default="", help="Optional explicit workspace path.")
    args = parser.parse_args()
    workspace = create_topic_workspace(args.topic, args.workspace, args.customer_segment)
    print(json.dumps({"topic": args.topic, "workspace": str(workspace), "manifest": str(workspace / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
