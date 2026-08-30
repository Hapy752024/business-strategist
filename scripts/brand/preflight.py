#!/usr/bin/env python3
"""Report only the tooling required by the requested brand stage."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import json


STAGE_REQUIREMENTS = {
    "discovery": ([], ["node"]),
    "strategy": ([], []),
    "logo": (["inkscape"], []),
    "export": (["inkscape"], ["PIL", "fitz"]),
    "website": (["node", "pnpm"], []),
}


def inspect_stage(stage: str) -> dict[str, list[str]]:
    blocking, optional = STAGE_REQUIREMENTS.get(stage, ([], []))
    available: list[str] = []
    blocking_missing: list[str] = []
    optional_missing: list[str] = []
    for tool in blocking:
        (available if shutil.which(tool) else blocking_missing).append(tool)
    for module in optional:
        (available if importlib.util.find_spec(module) else optional_missing).append(module)
    return {"stage": stage, "available": available, "optional_missing": optional_missing, "blocking_missing": blocking_missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=sorted(STAGE_REQUIREMENTS))
    args = parser.parse_args()
    result = inspect_stage(args.stage)
    print(json.dumps(result, indent=2))
    return 1 if result["blocking_missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
