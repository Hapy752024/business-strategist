#!/usr/bin/env python3
"""Create a website manifest without running installers or external services."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("website_dir", type=Path)
    parser.add_argument("--website-id", required=True)
    parser.add_argument("--entry-mode", choices=("standalone", "business_linked"), default="standalone")
    parser.add_argument("--next-version", default="16.3.3")
    parser.add_argument("--preferences", default="website-preferences.json")
    args = parser.parse_args()
    timestamp = now_iso()
    manifest = {
        "schema_version": "1.0",
        "manifest_revision": 1,
        "updated_at": timestamp,
        "website_id": args.website_id,
        "entry_mode": args.entry_mode,
        "stack": {"next": args.next_version, "react": "resolved-by-next", "node": ">=20.9", "package_manager": "pnpm", "lockfile": "source/pnpm-lock.yaml", "resolver_source": "https://nextjs.org/docs/app/getting-started/installation", "resolved_at": timestamp},
        "preferences": args.preferences,
        "brand_refs": [],
        "concept": {"territories": [], "selected": "", "signature_device": "", "approval_status": "pending"},
        "pages": [],
        "fal_assets": [],
        "experiment": None,
        "qa": {"build": "pending", "accessibility": "pending", "performance": "pending", "responsive": "pending", "visual_review": "pending"},
        "release": {"status": "local", "environment": "local"},
        "next_action": "Select a creative territory and build the vertical slice.",
        "open_blockers": [],
    }
    args.website_dir.mkdir(parents=True, exist_ok=True)
    output = args.website_dir / "website-manifest.json"
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing manifest: {output}")
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(output), "status": "created"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
