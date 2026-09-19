"""Stable coordination records for project-layout migrations.

The lock and journal intentionally live outside a migrated project tree.  A
directory replacement can therefore not create a second lock or hide an
interrupted migration from a supported reader.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
COORDINATION_ROOT = ROOT / "projects" / "_infra" / "layout-migrations"
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATES = {"prepared", "analysis_started", "snapshot_intent", "snapshotted", "original_move_intent", "original_moved", "legacy_retire_intent", "legacy_readme_removed", "legacy_retired", "replacement_intent", "replacement_installed", "cases_initialized", "shared_research_moved", "legacy_archived", "legacy_controller_retired", "rollback_started", "rolled_back", "verified"}
JOURNAL_FIELDS = {"project_id", "migration_id", "state", "project_path", "baseline_digest"}
_PERMITTED = ContextVar("layout_migration_permitted", default=frozenset())


def _project_id(project_id: str) -> str:
    if not IDENTIFIER.fullmatch(project_id):
        raise ValueError("invalid project migration identity")
    return project_id


def directory(project_id: str, *, root: Path = ROOT) -> Path:
    _project_id(project_id)
    return root / "projects" / "_infra" / "layout-migrations" / project_id


def _coordination_directory(project_id: str, *, root: Path = ROOT) -> Path:
    """Create a project coordination directory without accepting symlink escapes."""
    root = Path(root).absolute()
    if root.is_symlink():
        raise ValueError("migration repository root may not be a symlink")
    for part in (root / "projects", root / "projects" / "_infra"):
        if part.exists() and part.is_symlink():
            raise ValueError("migration coordination ancestry may not be a symlink")
    base = root / "projects" / "_infra" / "layout-migrations"
    base.mkdir(parents=True, exist_ok=True)
    if base.is_symlink():
        raise ValueError("migration coordination root may not be a symlink")
    target = directory(project_id, root=root)
    if target.is_symlink():
        raise ValueError("migration coordination directory may not be a symlink")
    target.mkdir(exist_ok=True)
    if target.is_symlink() or target.parent != base or not target.resolve().is_relative_to(base.resolve()):
        raise ValueError("migration coordination path escapes its root")
    return target


def _atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".migration-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def lock(project_id: str, *, root: Path = ROOT, exclusive: bool = False) -> Iterator[None]:
    """Hold a stable shared/exclusive project migration lock."""
    path = _coordination_directory(project_id, root=root) / "migration.lock"
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("migration lock must be a regular non-symlink file")
    with path.open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def journal(project_id: str, *, root: Path = ROOT) -> dict | None:
    path = _coordination_directory(project_id, root=root) / "journal.json"
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("migration journal must be a regular non-symlink file")
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("migration journal is unreadable; recovery is required") from exc
    if (value.get("project_id") != project_id or value.get("state") not in STATES
            or not JOURNAL_FIELDS.issubset(value)
            or not isinstance(value.get("migration_id"), str) or not IDENTIFIER.fullmatch(value["migration_id"])
            or value.get("project_path") != f"projects/{project_id}"
            or not isinstance(value.get("baseline_digest"), str) or not re.fullmatch(r"[0-9a-f]{64}", value["baseline_digest"])):
        raise ValueError("migration journal is invalid; recovery is required")
    return value


def assert_available(project_id: str, *, root: Path = ROOT) -> None:
    if project_id in _PERMITTED.get():
        return
    entry = journal(project_id, root=root)
    if entry and entry["state"] not in {"verified", "rolled_back"}:
        raise ValueError("layout migration in progress; recover before using this project")


def permitted(project_id: str) -> bool:
    return project_id in _PERMITTED.get()


@contextmanager
def permit(project_id: str) -> Iterator[None]:
    """Allow the migration owner to use guarded project APIs while it holds the lock."""
    token = _PERMITTED.set(_PERMITTED.get() | {project_id})
    try:
        yield
    finally:
        _PERMITTED.reset(token)


def write_journal(project_id: str, payload: dict, *, root: Path = ROOT) -> None:
    if (payload.get("project_id") != project_id or payload.get("state") not in STATES
            or not JOURNAL_FIELDS.issubset(payload)
            or not all(isinstance(payload.get(field), str) and payload[field] for field in JOURNAL_FIELDS - {"state"})
            or not IDENTIFIER.fullmatch(payload["migration_id"])
            or payload["project_path"] != f"projects/{project_id}"
            or not re.fullmatch(r"[0-9a-f]{64}", payload["baseline_digest"])):
        raise ValueError("invalid migration journal payload")
    _atomic(_coordination_directory(project_id, root=root) / "journal.json", payload)


def digest_tree(root: Path) -> dict[str, str]:
    """Digest a regular-file-only tree; a symlink is never silently ignored."""
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("migration tree contains a symlink")
        if not path.is_file():
            continue
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result
