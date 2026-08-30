#!/usr/bin/env python3
"""Shared project control-plane helpers with atomic, revision-checked writes.

Track-specific manifests remain authoritative for their own stages. This module
only owns project links and active-track state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT / "projects"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def slugify(value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in safe.split("-") if part)[:80] or "project"


def _safe_path(path: str | Path, *, allow_external: bool = False) -> dict[str, Any]:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(ROOT.resolve())
    except ValueError:
        if not allow_external:
            raise ValueError(f"path is outside repository: {candidate}")
        return {"path": str(candidate), "external": True}
    return {"path": relative.as_posix(), "external": False}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, value: dict[str, Any], *, expected_revision: int | None = None) -> int:
    """Atomically write JSON and fail on a stale manifest revision."""
    path.parent.mkdir(parents=True, exist_ok=True)
    current: dict[str, Any] | None = None
    if path.exists():
        current = read_json(path)
    actual = int((current or {}).get("manifest_revision", 0))
    if expected_revision is not None and actual != expected_revision:
        raise RuntimeError(f"manifest revision conflict: expected {expected_revision}, found {actual}")
    next_revision = actual + 1
    payload = dict(value)
    payload["manifest_revision"] = next_revision
    payload["updated_at"] = now_iso()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return next_revision


def create_project(slug: str, *, business_workspace: str = "", brand_workspace: str = "") -> Path:
    slug = slugify(slug)
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"invalid project slug: {slug}")
    directory = PROJECTS_ROOT / slug
    manifest_path = directory / "project-manifest.json"
    if manifest_path.exists():
        return manifest_path
    timestamp = now_iso()
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "project_id": slug,
        "slug": slug,
        "created_at": timestamp,
        "updated_at": timestamp,
        "manifest_revision": 0,
        "active_track": "none",
        "business_workspace": _safe_path(business_workspace, allow_external=True) if business_workspace else None,
        "brand_workspace": _safe_path(brand_workspace, allow_external=True) if brand_workspace else None,
        "links": [],
        "next_action": "Choose a business, brand, or website track.",
        "open_blockers": [],
    }
    write_json_atomic(manifest_path, manifest, expected_revision=0)
    return manifest_path


def link_project(manifest_path: Path, *, track: str, workspace: str, active: bool = False) -> int:
    if track not in {"business", "brand", "website"}:
        raise ValueError("track must be business, brand, or website")
    manifest = read_json(manifest_path)
    entry = _safe_path(workspace, allow_external=True)
    manifest[f"{track}_workspace"] = entry
    links = [link for link in manifest.get("links", []) if link.get("track") != track]
    links.append({"track": track, "workspace": entry, "linked_at": now_iso()})
    manifest["links"] = links
    if active:
        manifest["active_track"] = track
    return write_json_atomic(manifest_path, manifest, expected_revision=int(manifest.get("manifest_revision", 0)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("slug")
    create.add_argument("--business-workspace", default="")
    create.add_argument("--brand-workspace", default="")
    link = subparsers.add_parser("link")
    link.add_argument("manifest", type=Path)
    link.add_argument("--track", required=True)
    link.add_argument("--workspace", required=True)
    link.add_argument("--active", action="store_true")
    args = parser.parse_args()
    if args.command == "create":
        result = create_project(args.slug, business_workspace=args.business_workspace, brand_workspace=args.brand_workspace)
        print(json.dumps({"manifest": str(result), "revision": read_json(result)["manifest_revision"]}, indent=2))
    else:
        revision = link_project(args.manifest.resolve(), track=args.track, workspace=args.workspace, active=args.active)
        print(json.dumps({"manifest": str(args.manifest), "revision": revision}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
