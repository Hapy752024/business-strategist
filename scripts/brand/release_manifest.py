#!/usr/bin/env python3
"""Record GitHub/Vercel release state without deploying or changing traffic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def update(path: Path, *, status: str, commit: str, url: str = "", rollback_commit: str = "") -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    release = data.setdefault("release", {})
    release["status"] = status
    release["commit"] = commit
    if url:
        release["preview_url" if status == "preview" else "production_url"] = url
    if rollback_commit:
        release["rollback_commit"] = rollback_commit
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--status", choices=("preview", "production", "rolled_back"), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--rollback-commit", default="")
    parser.add_argument("--confirm-production", action="store_true")
    args = parser.parse_args()
    if args.status == "production" and not args.confirm_production:
        parser.error("production status requires --confirm-production")
    release = update(args.manifest, status=args.status, commit=args.commit, url=args.url, rollback_commit=args.rollback_commit)
    print(json.dumps({"status": "recorded", "release": release}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
