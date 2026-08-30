#!/usr/bin/env python3
"""Validate a business-to-brand snapshot without upgrading uncertainty."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = ("schema_version", "snapshot_id", "source_workspace", "field_provenance", "coverage_gaps")
ALLOWED = {"evidence_backed", "user_confirmed", "inference", "assumption", "unresolved"}


def validate(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid JSON: {exc}"]
    errors = [f"missing {key}" for key in REQUIRED if key not in data]
    provenance = data.get("field_provenance", {})
    if not isinstance(provenance, dict):
        errors.append("field_provenance must be an object")
    else:
        for field, status in provenance.items():
            if status not in ALLOWED:
                errors.append(f"{field}: unsupported provenance {status}")
    if not isinstance(data.get("coverage_gaps", []), list):
        errors.append("coverage_gaps must be an array")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    errors = validate(args.snapshot)
    print(json.dumps({"status": "fail" if errors else "pass", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
