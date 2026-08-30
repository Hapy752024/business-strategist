#!/usr/bin/env python3
"""Reject executable or externally-loaded SVG/HTML before preview or packaging."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


UNSAFE = (
    re.compile(r"<\s*script\b", re.I),
    re.compile(r"\bon[a-z]+\s*=", re.I),
    re.compile(r"<\s*foreignObject\b", re.I),
    re.compile(r"(?:javascript:|data:text/html|vbscript:)", re.I),
    re.compile(r"(?:href|src|xlink:href)\s*=\s*['\"](?:https?:|//)", re.I),
)


def validate(path: Path) -> list[str]:
    if path.suffix.lower() not in {".svg", ".html", ".htm"}:
        return ["unsupported preview type"]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"cannot read asset: {exc}"]
    errors = ["unsafe pattern detected" for pattern in UNSAFE if pattern.search(text)]
    if ".." in path.parts:
        errors.append("path traversal")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", type=Path)
    args = parser.parse_args()
    errors = validate(args.asset)
    print(json.dumps({"status": "fail" if errors else "pass", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
