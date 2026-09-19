#!/usr/bin/env python3
"""Journaled first live migration: individualized-marketing-content only.

This is intentionally narrow.  It converts the smallest legacy project after
the copy rehearsal, proving recovery and current/history separation before the
larger multi-case projects are attempted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import case_workspace as cases
from scripts import layout_migration as migration
from scripts.rehearse_existing_migration import SLUG, transition


def inventory_digest(project: Path) -> str:
    return hashlib.sha256(json.dumps(migration.digest_tree(project), sort_keys=True).encode()).hexdigest()


def payload(project: Path, migration_id: str, state: str, baseline: str, **extra: str) -> dict:
    return {"project_id": SLUG, "migration_id": migration_id, "state": state,
            "project_path": str(project.relative_to(project.parents[1])),
            "baseline_digest": baseline, **extra}


def safe_file(path: Path, *, missing: bool = False) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()) or (not missing and not path.exists()):
        raise ValueError("migration path is not a contained regular file")


def same_tree(project: Path, expected: dict[str, str]) -> bool:
    return migration.digest_tree(project) == expected


def expected_after_research_move(before: dict[str, str]) -> dict[str, str]:
    """The one planned move has a deterministic digest-level after state."""
    after = {name: value for name, value in before.items() if not name.startswith("market_research/")}
    after.update({"business-analysis/market_research/" + name.removeprefix("market_research/"): value
                  for name, value in before.items() if name.startswith("market_research/")})
    return after


def without_files(before: dict[str, str], *names: str) -> dict[str, str]:
    return {name: value for name, value in before.items() if name not in names}


def retired_file(before: dict[str, str], name: str) -> dict[str, str]:
    """Expected state after atomically preserving one retiring root file."""
    after = without_files(before, name)
    after[f"business-analysis/history/snapshots/first-live-migration/retired-root/{name}"] = before[name]
    return after


def compatible_tree(project: Path, original: dict[str, str], before_rollback: dict[str, str]) -> bool:
    """A resumed rollback may contain only known original or replacement bytes."""
    current = migration.digest_tree(project)
    allowed = set(original) | set(before_rollback)
    if not set(current).issubset(allowed):
        return False
    return all(value in {original.get(name), before_rollback.get(name)} for name, value in current.items())


def recover_partial_replacement(project: Path, expected: dict[str, str], *, repo_root: Path) -> bool:
    """Remove only root files a recorded replacement publication may create.

    `replacement_intent` is written before the umbrella initializer.  The
    pre-publication tree must still match exactly below business-analysis; the
    only accepted additions are the initializer's root controller, its
    history, and its lock.  Everything else is an ambiguous edit.
    """
    current = migration.digest_tree(project)
    if any(current.get(name) != value for name, value in expected.items()):
        return False
    additions = set(current) - set(expected)
    allowed = {"README.md", "project-manifest.json", "project.lock"}
    temporary = lambda name: name.startswith(".README.md-") or name.startswith(".project-manifest.json-")
    if any(name not in allowed and not name.startswith("history/") and not temporary(name) for name in additions):
        return False
    backup = migration.directory(SLUG, root=repo_root) / "partial-root-replacement"
    if backup.is_symlink() or (backup.exists() and not backup.is_dir()):
        raise ValueError("partial replacement backup is unsafe; manual recovery required")
    backup.mkdir(exist_ok=True)
    for name in ("README.md", "project-manifest.json", "project.lock", "history"):
        source = project / name
        if source.exists():
            if source.is_symlink():
                raise ValueError("partial replacement contains a symlink")
            destination = backup / name
            if destination.exists() or destination.is_symlink():
                raise ValueError("partial replacement backup conflicts; manual recovery required")
            os.replace(source, destination)
    for name in sorted(item for item in additions if temporary(item)):
        source = project / name
        destination = backup / "atomic-tmp" / name
        destination.parent.mkdir(exist_ok=True)
        if source.is_symlink() or destination.exists() or destination.is_symlink():
            raise ValueError("partial replacement temporary-file recovery conflicts")
        os.replace(source, destination)
    if not same_tree(project, expected):
        raise ValueError("partial replacement recovery did not restore its recorded boundary")
    return True


def canonical_project(project: Path, repo_root: Path) -> Path:
    project = Path(project).absolute()
    repo_root = Path(repo_root).absolute()
    expected = repo_root / "projects" / SLUG
    if project != expected or any(part.is_symlink() for part in (repo_root, repo_root / "projects", expected)):
        raise ValueError("this narrow migrator accepts only the canonical non-symlink project path")
    return project


def verify(project: Path, baseline: dict[str, str]) -> None:
    analysis = project / "business-analysis"
    for relative in ("README.md", "project-manifest.json"):
        snapshot = analysis / "history/snapshots/first-live-migration" / relative
        if not snapshot.is_file() or hashlib.sha256(snapshot.read_bytes()).hexdigest() != baseline[relative]:
            raise ValueError("legacy root snapshot mismatch")
    research = migration.digest_tree(analysis / "market_research")
    expected = {key.removeprefix("market_research/"): value for key, value in baseline.items()
                if key.startswith("market_research/")}
    if research != expected:
        raise ValueError("research bytes changed during migration")
    root = cases.read_project(project)
    if root.get("controller_kind") != "umbrella" or root.get("selection") is not None:
        raise ValueError("invalid migrated project controller")
    if (analysis / "market_research/manifest.json").exists():
        raise ValueError("legacy aggregate manifest became active")


def rollback(project: Path, *, repo_root: Path = ROOT) -> None:
    """Restore the legacy tree from an incomplete narrow migration, fail closed on ambiguity."""
    project = canonical_project(project, repo_root)
    with migration.lock(SLUG, root=repo_root, exclusive=True):
        entry = migration.journal(SLUG, root=repo_root)
        if not entry or entry["state"] in {"verified", "rolled_back"}:
            raise ValueError("no incomplete first migration to roll back")
        analysis = project / "business-analysis"
        snapshots = analysis / "history/snapshots/first-live-migration"
        research = analysis / "market_research"
        baseline = entry.get("baseline_files")
        if not isinstance(baseline, dict) or hashlib.sha256(json.dumps(baseline, sort_keys=True).encode()).hexdigest() != entry["baseline_digest"]:
            raise ValueError("cannot prove rollback baseline; manual recovery required")
        expected_phase = entry.get("phase_files")
        if not isinstance(expected_phase, dict):
            raise ValueError("migration phase record is invalid; refusing rollback")
        if entry["state"] == "original_move_intent":
            after_move = expected_after_research_move(expected_phase)
            if same_tree(project, expected_phase):
                entry["state"] = "snapshotted"
            elif same_tree(project, after_move):
                entry["state"] = "original_moved"
                entry["phase_files"] = after_move
            else:
                raise ValueError("project changed during research move; refusing rollback")
            migration.write_journal(SLUG, entry, root=repo_root)
            expected_phase = entry["phase_files"]
        if entry["state"] == "legacy_retire_intent":
            removed_readme = retired_file(expected_phase, "README.md")
            removed_both = retired_file(removed_readme, "project-manifest.json")
            if same_tree(project, expected_phase):
                entry["state"] = "original_moved"
            elif same_tree(project, removed_readme):
                entry["state"] = "legacy_readme_removed"
                entry["phase_files"] = removed_readme
            elif same_tree(project, removed_both):
                entry["state"] = "legacy_retired"
                entry["phase_files"] = removed_both
            else:
                raise ValueError("project changed during legacy retirement; refusing rollback")
            migration.write_journal(SLUG, entry, root=repo_root)
            expected_phase = entry["phase_files"]
        if entry["state"] == "legacy_readme_removed":
            removed_manifest = retired_file(expected_phase, "project-manifest.json")
            if same_tree(project, expected_phase):
                pass
            elif same_tree(project, removed_manifest):
                entry["state"] = "legacy_retired"
                entry["phase_files"] = removed_manifest
                migration.write_journal(SLUG, entry, root=repo_root)
                expected_phase = removed_manifest
            else:
                raise ValueError("project changed during legacy retirement; refusing rollback")
        if entry["state"] == "replacement_intent" and not same_tree(project, expected_phase):
            if recover_partial_replacement(project, expected_phase, repo_root=repo_root):
                entry["state"] = "legacy_retired"
                migration.write_journal(SLUG, entry, root=repo_root)
            else:
                raise ValueError("project changed during root replacement; refusing rollback")
        if entry["state"] != "rollback_started" and not same_tree(project, expected_phase):
            # Before the research rename, a crash can leave a partial analysis
            # initializer, case manifest, or snapshot.  The legacy root is
            # still byte-identical, so retain the partial work outside the
            # project and restore that exact baseline.
            current = migration.digest_tree(project)
            legacy_names = {name for name in baseline if not name.startswith("business-analysis/")}
            legacy_intact = all(current.get(name) == baseline[name] for name in legacy_names)
            extra = set(current) - legacy_names
            pre_move = {"prepared", "analysis_started", "snapshot_intent", "snapshotted"}
            if entry["state"] in pre_move and legacy_intact and all(name.startswith("business-analysis/") for name in extra):
                analysis = project / "business-analysis"
                quarantine = migration.directory(SLUG, root=repo_root) / f"partial-analysis-{entry['state']}"
                # A crash after the atomic quarantine rename but before the
                # journal update leaves an exact legacy tree.  Recognize that
                # completed boundary and finish the durable state transition.
                if not analysis.exists() and same_tree(project, baseline) and quarantine.is_dir() and not quarantine.is_symlink():
                    entry["state"] = "rolled_back"
                    entry["replacement_backup"] = str(quarantine.relative_to(repo_root))
                    migration.write_journal(SLUG, entry, root=repo_root)
                    return
                if not analysis.is_dir() or analysis.is_symlink():
                    raise ValueError("incomplete analysis recovery is ambiguous")
                if quarantine.exists() or quarantine.is_symlink():
                    raise ValueError("incomplete analysis quarantine already exists")
                os.replace(analysis, quarantine)
                if not same_tree(project, baseline):
                    raise ValueError("incomplete analysis recovery did not restore baseline")
                entry["state"] = "rolled_back"
                entry["replacement_backup"] = str(quarantine.relative_to(repo_root))
                migration.write_journal(SLUG, entry, root=repo_root)
                return
            raise ValueError("project changed after migration phase; refusing rollback")
        if entry["state"] != "rollback_started":
            entry["rollback_files"] = migration.digest_tree(project)
            entry["state"] = "rollback_started"
            migration.write_journal(SLUG, entry, root=repo_root)
        before_rollback = entry.get("rollback_files")
        if not isinstance(before_rollback, dict) or not compatible_tree(project, baseline, before_rollback):
            raise ValueError("project changed during rollback; refusing overwrite")
        if not analysis.is_dir() or analysis.is_symlink():
            if same_tree(project, baseline):
                entry["state"] = "rolled_back"
                migration.write_journal(SLUG, entry, root=repo_root)
                return
            raise ValueError("cannot prove rollback inputs; manual recovery required")
        for name in ("README.md", "project-manifest.json"):
            safe_file(project / name, missing=True)
        source_is_needed = not ((project / "README.md").exists() and (project / "project-manifest.json").exists()
                                and (project / "market_research").exists())
        if source_is_needed:
            if snapshots.is_symlink() or not snapshots.is_dir():
                raise ValueError("rollback snapshots are unavailable")
            for name in ("README.md", "project-manifest.json"):
                safe_file(snapshots / name)
                if hashlib.sha256((snapshots / name).read_bytes()).hexdigest() != baseline.get(name):
                    raise ValueError("rollback snapshot is corrupt")
        if research.exists() and research.is_symlink():
            raise ValueError("rollback research source is a symlink")
        if (project / "market_research").exists() and (project / "market_research").is_symlink():
            raise ValueError("rollback research destination is a symlink")
        replacement = migration.directory(SLUG, root=repo_root) / "replaced-analysis"
        if replacement.exists() or replacement.is_symlink():
            raise ValueError("rollback destination already exists; manual recovery required")
        root_history = project / "history"
        if root_history.exists():
            history_backup = migration.directory(SLUG, root=repo_root) / "replaced-root-history"
            if history_backup.exists() or history_backup.is_symlink():
                raise ValueError("rollback history destination already exists; manual recovery required")
            os.replace(root_history, history_backup)
        root_lock = project / "project.lock"
        if root_lock.exists():
            lock_backup = migration.directory(SLUG, root=repo_root) / "replaced-root-project.lock"
            if lock_backup.exists() or lock_backup.is_symlink():
                raise ValueError("rollback lock destination already exists; manual recovery required")
            os.replace(root_lock, lock_backup)
        root_backup = migration.directory(SLUG, root=repo_root) / "replaced-root-files"
        if root_backup.is_symlink() or (root_backup.exists() and not root_backup.is_dir()):
            raise ValueError("rollback root-file backup is unsafe; manual recovery required")
        root_backup.mkdir(exist_ok=True)
        for name in ("README.md", "project-manifest.json"):
            target = project / name
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == baseline[name]:
                continue
            backup = root_backup / name
            if target.exists():
                if target.is_symlink() or backup.exists() or backup.is_symlink():
                    raise ValueError("rollback root-file backup conflicts; manual recovery required")
                # Capture the just-observed replacement (including a late
                # outside edit) before restoring a legacy root document.
                os.replace(target, backup)
            cases.atomic(target, (snapshots / name).read_bytes())
        if research.exists():
            if (project / "market_research").exists():
                raise ValueError("rollback has two research roots")
            os.replace(research, project / "market_research")
        os.replace(analysis, replacement)
        if not same_tree(project, baseline):
            raise ValueError("rollback did not exactly restore the baseline")
        entry["state"] = "rolled_back"
        entry["replacement_backup"] = str(replacement.relative_to(repo_root))
        migration.write_journal(SLUG, entry, root=repo_root)


def execute(project: Path, *, repo_root: Path = ROOT) -> dict:
    repo_root = Path(repo_root).absolute()
    project = canonical_project(project, repo_root)
    if not project.is_dir():
        raise ValueError("first migration source project does not exist")
    for unexpected in ("business-analysis", "history", "project.lock", "market_research/manifest.json"):
        if (project / unexpected).exists():
            raise ValueError("first migration precondition failed; use the full migrator/recovery path")
    with migration.lock(SLUG, root=repo_root, exclusive=True):
        if migration.journal(SLUG, root=repo_root) is not None:
            raise ValueError("migration journal already exists; recover or inspect it first")
        baseline = migration.digest_tree(project)
        baseline_hash = hashlib.sha256(json.dumps(baseline, sort_keys=True).encode()).hexdigest()
        entry = payload(project, "first-live-migration", "prepared", baseline_hash,
                        baseline_files=baseline, phase_files=baseline)
        migration.write_journal(SLUG, entry, root=repo_root)
        try:
            def legacy_root_is_unchanged(current: dict[str, str]) -> bool:
                return (all(current.get(name) == value for name, value in baseline.items())
                        and all(name in baseline or name.startswith("business-analysis/") for name in current))

            def replacement_shape(current: dict[str, str], previous: dict[str, str]) -> bool:
                if any(current.get(name) != value for name, value in previous.items()):
                    return False
                return all(name in previous or name in {"README.md", "project-manifest.json", "project.lock"}
                           or name.startswith("history/") for name in current)

            def phase(state: str) -> None:
                previous = entry["phase_files"]
                current = migration.digest_tree(project)
                intents = {"snapshot_intent", "original_move_intent", "legacy_retire_intent", "replacement_intent"}
                expected_removals = {
                    "original_moved": expected_after_research_move,
                    "legacy_readme_removed": lambda files: retired_file(files, "README.md"),
                    "legacy_retired": lambda files: retired_file(files, "project-manifest.json"),
                }
                if state in intents and current != previous:
                    raise ValueError(f"project changed before {state}; refusing migration")
                if state == "analysis_started" and not legacy_root_is_unchanged(current):
                    raise ValueError("legacy root changed during analysis initialization")
                if state == "snapshotted" and not legacy_root_is_unchanged(current):
                    raise ValueError("legacy root changed during snapshot")
                if state in expected_removals and current != expected_removals[state](previous):
                    raise ValueError(f"project changed during {state}; refusing migration")
                if state == "replacement_installed" and not replacement_shape(current, previous):
                    raise ValueError("project changed during root replacement")
                entry["state"] = state
                entry["phase_files"] = current
                migration.write_journal(SLUG, entry, root=repo_root)
            with migration.permit(SLUG):
                result = transition(project, migration_id="first-live-migration", phase=phase)
                entry["replacement_files"] = migration.digest_tree(project)
                entry["snapshot_path"] = "business-analysis/history/snapshots/first-live-migration"
                migration.write_journal(SLUG, entry, root=repo_root)
                verify(project, baseline)
        except Exception:
            # Keep the prepared/replacement journal for explicit fail-closed recovery.
            raise
        entry["state"] = "verified"
        migration.write_journal(SLUG, entry, root=repo_root)
        return {"project": str(project), "baseline_digest": baseline_hash, "result": result,
                "journal": str(migration.directory(SLUG, root=repo_root) / "journal.json")}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.root.resolve()
    project = repo_root / "projects" / SLUG
    if args.rollback:
        rollback(project, repo_root=repo_root)
        return 0
    print(json.dumps(execute(project, repo_root=repo_root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
