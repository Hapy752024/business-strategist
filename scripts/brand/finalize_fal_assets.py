#!/usr/bin/env python3
"""Download, validate, and locally record outputs from an approved FAL request."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from pathlib import Path


def load_adapter():
    source = Path(__file__).parents[1] / "fal_assets.py"
    spec = importlib.util.spec_from_file_location("fal_assets", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--response", type=Path, required=True, help="completed FAL result JSON")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True, help="URL-free local asset record")
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    args = parser.parse_args()
    adapter = load_adapter()
    payload = json.loads(args.response.read_text(encoding="utf-8"))
    try:
        assets = adapter.download_assets(payload, args.output_dir, expected_width=args.expected_width, expected_height=args.expected_height)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, indent=2))
        return 1
    result = {"status": "finalized", "asset_count": len(assets), "assets": assets}
    write_atomic(args.record, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
