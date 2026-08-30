#!/usr/bin/env python3
"""Promote one approved brand artifact with hash and path safety checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inside(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project: {candidate}") from exc
    return resolved


def write_json_atomic(path: Path, data: dict, *, expected_revision: int) -> None:
    current = json.loads(path.read_text(encoding="utf-8"))
    actual_revision = int(current.get("manifest_revision", 1))
    if actual_revision != expected_revision:
        raise RuntimeError(f"manifest revision conflict: expected {expected_revision}, found {actual_revision}")
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def promote(project: Path, artifact_id: str, *, confirm: bool = False, replace_conflict: bool = False, replacement_approver: str = "") -> dict[str, object]:
    project = project.resolve()
    manifest_path = project / "brand-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_revision = int(data.get("manifest_revision", 1))
    artifacts = [item for item in data.get("artifacts", []) if item.get("artifact_id") == artifact_id or item.get("id") == artifact_id]
    if len(artifacts) != 1:
        raise ValueError(f"expected exactly one artifact with id {artifact_id!r}")
    artifact = artifacts[0]
    if artifact.get("status") != "approved":
        raise ValueError("artifact is not approved")
    candidate = inside(project, project / str(artifact.get("candidate_path", "")))
    destination = inside(project, project / str(artifact.get("destination", "")))
    if not candidate.is_file():
        raise ValueError(f"candidate does not exist: {candidate}")
    expected = str(artifact.get("sha256", ""))
    actual = digest(candidate)
    if expected != actual:
        raise ValueError(f"candidate hash mismatch: expected {expected}, found {actual}")
    if destination == candidate:
        raise ValueError("candidate and destination must differ")
    conflict = destination.exists()
    destination_hash = digest(destination) if destination.is_file() else None
    idempotent = destination_hash == actual
    if conflict and not destination.is_file():
        raise ValueError("destination exists and is not a file")
    if conflict and not idempotent and not replace_conflict:
        raise ValueError("destination conflict: refusing to overwrite a different artifact")
    if conflict and not idempotent and replace_conflict and not replacement_approver.strip():
        raise ValueError("replacement requires an explicit replacement approver")
    result = {"status": "ready" if not confirm else ("already_current" if idempotent else "promoted"), "artifact_id": artifact_id, "candidate": str(candidate), "destination": str(destination), "sha256": actual, "destination_conflict": conflict, "replacement_authorized": replace_conflict}
    if not confirm:
        return result
    current_revision = int(json.loads(manifest_path.read_text(encoding="utf-8")).get("manifest_revision", 1))
    if current_revision != expected_revision:
        raise RuntimeError(f"manifest revision conflict: expected {expected_revision}, found {current_revision}")
    if not idempotent:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        os.close(fd)
        temporary = Path(temp_name)
        try:
            shutil.copy2(candidate, temporary)
            if digest(temporary) != actual:
                raise ValueError("temporary copy hash mismatch")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    artifact["status"] = "promoted"
    artifact["promoted_at"] = datetime.now(timezone.utc).isoformat()
    artifact["promoted_sha256"] = actual
    artifact["replaced_destination_sha256"] = destination_hash
    if replacement_approver:
        artifact["replacement_approval"] = {"approver": replacement_approver, "timestamp": datetime.now(timezone.utc).isoformat()}
    data["manifest_revision"] = expected_revision + 1
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json_atomic(manifest_path, data, expected_revision=expected_revision)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--replace-conflict", action="store_true", help="explicitly replace a different destination file")
    parser.add_argument("--replacement-approver", default="")
    args = parser.parse_args()
    if args.dry_run and args.confirm:
        parser.error("choose --dry-run or --confirm, not both")
    if not args.dry_run and not args.confirm:
        parser.error("refusing to write without --dry-run or --confirm")
    try:
        result = promote(args.project_dir, args.artifact_id, confirm=args.confirm, replace_conflict=args.replace_conflict, replacement_approver=args.replacement_approver)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
