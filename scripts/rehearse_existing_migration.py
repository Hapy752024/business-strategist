#!/usr/bin/env python3
"""Rehearse the first legacy research-only migration on an isolated copy.

This deliberately supports only individualized-marketing-content.  It proves
the first narrow conversion before a generic cutover writer is introduced.
It never changes the live project unless a later, separately implemented
cutover command invokes the same transition under the external migration lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import case_workspace as cases
from scripts import subprojects
from scripts import layout_migration as migration
SLUG = "individualized-marketing-content"
CASE_ID = "individualized-content"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transition(project: Path, *, migration_id: str, phase=lambda _state: None) -> dict:
    """Perform the narrow migration on a disposable project copy."""
    if (project / "business-analysis").exists():
        raise ValueError("analysis destination already exists")
    original_readme = project / "README.md"
    original_manifest = project / "project-manifest.json"
    research = project / "market_research"
    if not original_readme.is_file() or not original_manifest.is_file() or not research.is_dir():
        raise ValueError("expected legacy research-only project structure")
    before = migration.digest_tree(project)
    analysis = project / "business-analysis"
    cases.initialize(analysis, "Individualized marketing content", project_id=SLUG)
    cases.add_case(analysis, CASE_ID, "Individualized marketing content",
                   open_blockers=["Legacy research requires case-specific review."],
                   next_action="Review legacy evidence applicability; establish segment, journey and pain.")
    phase("analysis_started")
    phase("snapshot_intent")
    snapshot = analysis / "history" / "snapshots" / migration_id
    snapshot.mkdir(parents=True)
    shutil.copy2(original_readme, snapshot / "README.md")
    shutil.copy2(original_manifest, snapshot / "project-manifest.json")
    phase("snapshotted")
    phase("original_move_intent")
    shutil.move(str(research), str(analysis / "market_research"))
    phase("original_moved")
    phase("legacy_retire_intent")
    case = cases.case_manifest(analysis, CASE_ID)
    assert case["stages"] == {}
    assert case["open_blockers"]
    retired = snapshot / "retired-root"
    retired.mkdir()
    # Preserve the live file rather than unlinking it: an edit after the
    # retirement intent is retained and its unexpected digest aborts cutover.
    os.replace(original_readme, retired / "README.md")
    phase("legacy_readme_removed")
    os.replace(original_manifest, retired / "project-manifest.json")
    phase("legacy_retired")
    # The root replacement is a multi-file publication.  Record its intent
    # before it creates any new root files so rollback can distinguish a
    # normal interrupted publication from an outside edit.
    phase("replacement_intent")
    subprojects.initialize(project, "Individualized marketing content")
    root_manifest = cases.read_project(project)
    root_manifest["next_action"] = "Review the individualized-content case before continuing research."
    root_manifest["open_blockers"] = ["Legacy research requires case-specific review."]
    cases.publish(project, {}, expected_revision=root_manifest["manifest_revision"], project=root_manifest,
                  decision_id="migrate-legacy-research-only", reason="Rehearse legacy research-only layout migration")
    phase("replacement_installed")
    current = cases.read_project(project)
    assert current["controller_kind"] == "umbrella"
    assert not (analysis / "market_research" / "manifest.json").exists()
    return {"before": before, "analysis": str(analysis), "case": CASE_ID,
            "snapshot": str(snapshot.relative_to(project)),
            "after_research_files": migration.digest_tree(analysis / "market_research")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "projects" / SLUG)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    report = args.report.resolve()
    if report == source or source in report.parents:
        raise ValueError("rehearsal report must be outside the source project")
    if report.exists():
        raise ValueError("rehearsal report path already exists")
    source_before = migration.digest_tree(source)
    with tempfile.TemporaryDirectory(prefix="business-analysis-rehearsal-") as temporary:
        rehearsal_root = Path(temporary) / SLUG
        shutil.copytree(source, rehearsal_root, symlinks=True)
        result = transition(rehearsal_root, migration_id="rehearsal")
        result["source_unchanged"] = source_before == migration.digest_tree(source)
        result["mode"] = "disposable-copy"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
