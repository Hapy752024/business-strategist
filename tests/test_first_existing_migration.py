"""First legacy-project migration rehearsal: preservation and state authority."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
import pytest

from scripts import case_workspace as cases
from scripts import layout_migration as migration
from scripts.rehearse_existing_migration import CASE_ID, SLUG, transition
from scripts import migrate_first_project as first


ROOT = Path(__file__).resolve().parents[1]
LEGACY_SOURCE = ROOT / "projects/_infra/layout-migrations/individualized-marketing-content/original-tree"


def legacy_fixture(tmp_path):
    source = tmp_path / "legacy-source"
    live = ROOT / "projects" / SLUG
    shutil.copytree(live, source, symlinks=True)
    analysis = source / "business-analysis"
    snapshot = analysis / "history/snapshots/first-live-migration"
    shutil.copy2(snapshot / "README.md", source / "README.md")
    shutil.copy2(snapshot / "project-manifest.json", source / "project-manifest.json")
    shutil.move(str(analysis / "market_research"), str(source / "market_research"))
    legacy_strategy = analysis / "history/legacy/strategy"
    if legacy_strategy.exists():
        shutil.move(str(legacy_strategy), str(source / "strategy"))
    shutil.rmtree(analysis)
    shutil.rmtree(source / "history")
    (source / "project.lock").unlink(missing_ok=True)
    return source


def test_research_only_transition_preserves_evidence_and_resets_case_state(tmp_path):
    source = legacy_fixture(tmp_path)
    project = tmp_path / SLUG
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)

    result = transition(project, migration_id="test-migration")

    analysis = project / "business-analysis"
    assert result["before"] == before
    assert result["after_research_files"] == {
        key.removeprefix("market_research/"): value
        for key, value in before.items() if key.startswith("market_research/")
    }
    assert (analysis / "history/snapshots/test-migration/README.md").is_file()
    assert (analysis / "history/snapshots/test-migration/project-manifest.json").is_file()
    root = cases.read_project(project)
    assert root["controller_kind"] == "umbrella"
    case = cases.case_manifest(analysis, CASE_ID)
    assert case["stages"] == {}
    assert case["open_blockers"] == ["Legacy research requires case-specific review."]
    assert root.get("selection") is None
    assert not (analysis / "market_research/manifest.json").exists()


def test_external_journal_refuses_incomplete_migration(tmp_path):
    project_id = "example-project"
    payload = {"project_id": project_id, "migration_id": "test", "state": "prepared",
               "project_path": "projects/example-project", "baseline_digest": "0" * 64}
    migration.write_journal(project_id, payload, root=tmp_path)
    try:
        migration.assert_available(project_id, root=tmp_path)
    except ValueError as exc:
        assert "migration in progress" in str(exc)
    else:
        raise AssertionError("incomplete migration must block a supported consumer")
    payload["state"] = "verified"
    migration.write_journal(project_id, payload, root=tmp_path)
    migration.assert_available(project_id, root=tmp_path)


def test_rehearsal_report_cannot_overwrite_source(tmp_path):
    source = legacy_fixture(tmp_path)
    project = tmp_path / SLUG
    shutil.copytree(source, project, symlinks=True)
    from scripts.rehearse_existing_migration import main
    before = (project / "README.md").read_bytes()
    try:
        main_args = ["--source", str(project), "--report", str(project / "README.md")]
        import sys
        old = sys.argv
        sys.argv = ["rehearse", *main_args]
        try:
            main()
        finally:
            sys.argv = old
    except ValueError as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("source-internal report must be rejected")
    assert (project / "README.md").read_bytes() == before


def test_journal_rejects_symlinked_coordination_directory(tmp_path):
    project_id = "example-project"
    base = tmp_path / "projects/_infra/layout-migrations"
    base.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (base / project_id).symlink_to(outside, target_is_directory=True)
    payload = {"project_id": project_id, "migration_id": "test", "state": "prepared",
               "project_path": "projects/example-project", "baseline_digest": "0" * 64}
    try:
        migration.write_journal(project_id, payload, root=tmp_path)
    except ValueError as exc:
        assert "symlink" in str(exc)
    else:
        raise AssertionError("symlinked coordination path must be rejected")
    assert not (outside / "journal.json").exists()


def test_first_cutover_is_journaled_and_preserves_legacy_source(tmp_path):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    result = first.execute(project, repo_root=tmp_path)
    journal = migration.journal(SLUG, root=tmp_path)
    assert journal and journal["state"] == "verified"
    assert result["baseline_digest"] == hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    assert cases.read_project(project)["controller_kind"] == "umbrella"
    assert not (project / "market_research").exists()
    assert (project / "business-analysis/cases/individualized-content/README.md").is_file()


def test_first_cutover_rollback_restores_legacy_tree(tmp_path):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    baseline = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    entry = first.payload(project, "first-live-migration", "prepared", baseline,
                          baseline_files=before, phase_files=before)
    migration.write_journal(SLUG, entry, root=tmp_path)
    def phase(state):
        entry["state"] = state
        entry["phase_files"] = migration.digest_tree(project)
        migration.write_journal(SLUG, entry, root=tmp_path)
    with migration.permit(SLUG):
        transition(project, migration_id="first-live-migration", phase=phase)
    first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rolled_back"
    assert migration.digest_tree(project) == before


def test_rollback_refuses_post_install_edit_or_symlink(tmp_path):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    first.execute(project, repo_root=tmp_path)
    entry = migration.journal(SLUG, root=tmp_path)
    entry["state"] = "replacement_installed"
    migration.write_journal(SLUG, entry, root=tmp_path)
    (project / "README.md").write_text("external edit")
    try:
        first.rollback(project, repo_root=tmp_path)
    except ValueError as exc:
        assert "changed" in str(exc)
    else:
        raise AssertionError("rollback must not overwrite external edits")
    assert (project / "README.md").read_text() == "external edit"


def test_cutover_refuses_an_external_edit_between_recorded_phases(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    original_transition = first.transition

    def external_edit_after_move(target, *, migration_id, phase):
        def inject(state):
            phase(state)
            if state == "original_moved":
                (target / "README.md").write_text("outside edit", encoding="utf-8")
        return original_transition(target, migration_id=migration_id, phase=inject)

    monkeypatch.setattr(first, "transition", external_edit_after_move)
    with pytest.raises(ValueError, match="changed before legacy_retire_intent"):
        first.execute(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "original_moved"
    assert (project / "README.md").read_text(encoding="utf-8") == "outside edit"
    with pytest.raises(ValueError, match="changed"):
        first.rollback(project, repo_root=tmp_path)


def test_cutover_preserves_then_refuses_edit_after_retirement_intent(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    original_transition = first.transition

    def external_edit_after_intent(target, *, migration_id, phase):
        def inject(state):
            phase(state)
            if state == "legacy_retire_intent":
                (target / "README.md").write_text("late outside edit", encoding="utf-8")
        return original_transition(target, migration_id=migration_id, phase=inject)

    monkeypatch.setattr(first, "transition", external_edit_after_intent)
    with pytest.raises(ValueError, match="legacy_readme_removed"):
        first.execute(project, repo_root=tmp_path)
    archived = project / "business-analysis/history/snapshots/first-live-migration/retired-root/README.md"
    assert archived.read_text(encoding="utf-8") == "late outside edit"
    assert migration.journal(SLUG, root=tmp_path)["state"] == "legacy_retire_intent"


def test_cutover_refuses_late_root_file_before_umbrella_initialization(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    original_transition = first.transition

    def create_late_root_readme(target, *, migration_id, phase):
        def inject(state):
            phase(state)
            if state == "replacement_intent":
                (target / "README.md").write_text("late root edit", encoding="utf-8")
        return original_transition(target, migration_id=migration_id, phase=inject)

    monkeypatch.setattr(first, "transition", create_late_root_readme)
    with pytest.raises(ValueError, match="unmanaged root content"):
        first.execute(project, repo_root=tmp_path)
    assert (project / "README.md").read_text(encoding="utf-8") == "late root edit"
    assert migration.journal(SLUG, root=tmp_path)["state"] == "replacement_intent"


def test_rollback_preserves_a_late_root_edit_before_restoration(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    first.execute(project, repo_root=tmp_path)
    entry = migration.journal(SLUG, root=tmp_path)
    entry["state"] = "replacement_installed"
    migration.write_journal(SLUG, entry, root=tmp_path)
    original_compatible = first.compatible_tree

    def inject_after_compatibility(*args, **kwargs):
        result = original_compatible(*args, **kwargs)
        (project / "README.md").write_text("late rollback edit", encoding="utf-8")
        return result

    monkeypatch.setattr(first, "compatible_tree", inject_after_compatibility)
    first.rollback(project, repo_root=tmp_path)
    backup = migration.directory(SLUG, root=tmp_path) / "replaced-root-files/README.md"
    assert backup.read_text(encoding="utf-8") == "late rollback edit"
    assert migration.digest_tree(project) == before


@pytest.mark.parametrize("stop_at", ["analysis_started", "snapshot_intent", "snapshotted", "original_moved", "legacy_readme_removed", "legacy_retired", "replacement_intent", "replacement_installed"])
def test_every_recorded_transition_phase_rolls_back_exactly(tmp_path, stop_at):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    baseline = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    entry = first.payload(project, "first-live-migration", "prepared", baseline,
                          baseline_files=before, phase_files=before)
    migration.write_journal(SLUG, entry, root=tmp_path)
    def phase(state):
        entry["state"] = state
        entry["phase_files"] = migration.digest_tree(project)
        migration.write_journal(SLUG, entry, root=tmp_path)
        if state == stop_at:
            raise RuntimeError("interrupted")
    with migration.permit(SLUG), pytest.raises(RuntimeError):
        transition(project, migration_id="first-live-migration", phase=phase)
    first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rolled_back"
    assert migration.digest_tree(project) == before


def test_replacement_publication_interruption_recovers_only_generated_root_files(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    original_initialize = first.transition.__globals__["subprojects"].initialize

    def interrupt_after_initialize(*args, **kwargs):
        original_initialize(*args, **kwargs)
        raise RuntimeError("interrupted root publication")

    monkeypatch.setattr(first.transition.__globals__["subprojects"], "initialize", interrupt_after_initialize)
    with pytest.raises(RuntimeError, match="interrupted root publication"):
        first.execute(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "replacement_intent"
    first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rolled_back"
    assert migration.digest_tree(project) == before


def test_partial_analysis_initialization_is_quarantined_and_legacy_tree_is_unchanged(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    original_atomic = cases.atomic

    def interrupt_after_analysis_manifest(destination_path, data, *args, **kwargs):
        result = original_atomic(destination_path, data, *args, **kwargs)
        if Path(destination_path) == project / "business-analysis/project-manifest.json":
            raise RuntimeError("interrupted analysis initialization")
        return result

    monkeypatch.setattr(first.cases, "atomic", interrupt_after_analysis_manifest)
    with pytest.raises(RuntimeError, match="interrupted analysis initialization"):
        first.execute(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "prepared"
    monkeypatch.setattr(first.cases, "atomic", original_atomic)
    first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rolled_back"
    assert migration.digest_tree(project) == before


def test_partial_snapshot_is_quarantined_and_legacy_tree_is_unchanged(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    original_copy2 = first.transition.__globals__["shutil"].copy2

    def interrupt_after_snapshot_readme(source_path, destination_path, *args, **kwargs):
        result = original_copy2(source_path, destination_path, *args, **kwargs)
        if Path(destination_path).name == "README.md" and "snapshots" in str(destination_path):
            raise RuntimeError("interrupted snapshot")
        return result

    monkeypatch.setattr(first.transition.__globals__["shutil"], "copy2", interrupt_after_snapshot_readme)
    with pytest.raises(RuntimeError, match="interrupted snapshot"):
        first.execute(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "snapshot_intent"
    monkeypatch.setattr(first.transition.__globals__["shutil"], "copy2", original_copy2)
    first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rolled_back"
    assert migration.digest_tree(project) == before


def test_partial_analysis_quarantine_recovery_resumes_after_journal_write_crash(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    original_copy2 = first.transition.__globals__["shutil"].copy2

    def interrupt_snapshot(source_path, destination_path, *args, **kwargs):
        result = original_copy2(source_path, destination_path, *args, **kwargs)
        if "snapshots" in str(destination_path):
            raise RuntimeError("partial snapshot")
        return result

    monkeypatch.setattr(first.transition.__globals__["shutil"], "copy2", interrupt_snapshot)
    with pytest.raises(RuntimeError):
        first.execute(project, repo_root=tmp_path)
    monkeypatch.setattr(first.transition.__globals__["shutil"], "copy2", original_copy2)
    original_write = first.migration.write_journal

    def interrupt_rollback_journal(project_id, value, **kwargs):
        if value.get("state") == "rolled_back":
            raise RuntimeError("after quarantine rename")
        return original_write(project_id, value, **kwargs)

    monkeypatch.setattr(first.migration, "write_journal", interrupt_rollback_journal)
    with pytest.raises(RuntimeError, match="after quarantine rename"):
        first.rollback(project, repo_root=tmp_path)
    assert migration.digest_tree(project) == before
    monkeypatch.setattr(first.migration, "write_journal", original_write)
    first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rolled_back"


def test_execute_rejects_symlinked_project_root_before_writing_a_journal(tmp_path):
    source = legacy_fixture(tmp_path)
    outside = tmp_path / "outside-project"
    shutil.copytree(source, outside, symlinks=True)
    expected = tmp_path / "projects" / SLUG
    expected.parent.mkdir(parents=True)
    expected.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="canonical non-symlink"):
        first.execute(expected, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path) is None
    assert migration.digest_tree(outside) == migration.digest_tree(source)


def test_publication_lookup_refuses_an_active_migration_without_a_root_manifest(tmp_path, monkeypatch):
    project = tmp_path / "projects" / SLUG
    project.mkdir(parents=True)
    payload = {"project_id": SLUG, "migration_id": "first-live-migration", "state": "legacy_retired",
               "project_path": f"projects/{SLUG}", "baseline_digest": "0" * 64}
    migration.write_journal(SLUG, payload, root=tmp_path)
    original_root, original_lock, original_available = cases.ROOT, migration.lock, migration.assert_available
    monkeypatch.setattr(cases, "ROOT", tmp_path)
    monkeypatch.setattr(migration, "lock", lambda project_id, **_kwargs: original_lock(project_id, root=tmp_path))
    monkeypatch.setattr(migration, "assert_available", lambda project_id, **_kwargs: original_available(project_id, root=tmp_path))
    with pytest.raises(ValueError, match="migration in progress"):
        cases.locate_publication(project / "branding")


def test_interrupted_rollback_resumes_without_losing_the_barrier(tmp_path, monkeypatch):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    before = migration.digest_tree(project)
    first.execute(project, repo_root=tmp_path)
    entry = migration.journal(SLUG, root=tmp_path)
    entry["state"] = "replacement_installed"
    migration.write_journal(SLUG, entry, root=tmp_path)
    original_atomic = cases.atomic
    raised = False
    def interrupt(destination_path, data, *args, **kwargs):
        nonlocal raised
        result = original_atomic(destination_path, data, *args, **kwargs)
        if Path(destination_path).name == "README.md" and not raised:
            raised = True
            raise RuntimeError("interrupted rollback")
        return result
    monkeypatch.setattr(first.cases, "atomic", interrupt)
    with pytest.raises(RuntimeError):
        first.rollback(project, repo_root=tmp_path)
    assert migration.journal(SLUG, root=tmp_path)["state"] == "rollback_started"
    monkeypatch.setattr(first.cases, "atomic", original_atomic)
    first.rollback(project, repo_root=tmp_path)
    assert migration.digest_tree(project) == before


def test_guard_blocks_reader_and_writer_when_manifest_is_temporarily_absent(tmp_path, monkeypatch):
    project = tmp_path / "projects" / SLUG
    project.mkdir(parents=True)
    payload = {"project_id": SLUG, "migration_id": "first-live-migration", "state": "legacy_retired",
               "project_path": f"projects/{SLUG}", "baseline_digest": "0" * 64}
    migration.write_journal(SLUG, payload, root=tmp_path)
    original_lock, original_available = migration.lock, migration.assert_available
    monkeypatch.setattr(cases, "ROOT", tmp_path)
    monkeypatch.setattr(migration, "lock", lambda project_id, **_kwargs: original_lock(project_id, root=tmp_path))
    monkeypatch.setattr(migration, "assert_available", lambda project_id, **_kwargs: original_available(project_id, root=tmp_path))
    with pytest.raises(ValueError, match="migration in progress"):
        cases.read_project(project, allow_legacy=True)
    with pytest.raises(ValueError, match="migration in progress"):
        cases.initialize(project, "Blocked")


def test_rollback_rejects_symlink_substitution_without_touching_target(tmp_path):
    source = legacy_fixture(tmp_path)
    project = tmp_path / "projects" / SLUG
    project.parent.mkdir(parents=True)
    shutil.copytree(source, project, symlinks=True)
    first.execute(project, repo_root=tmp_path)
    entry = migration.journal(SLUG, root=tmp_path)
    entry["state"] = "replacement_installed"
    migration.write_journal(SLUG, entry, root=tmp_path)
    victim = tmp_path / "victim.md"
    victim.write_text("outside")
    (project / "README.md").unlink()
    (project / "README.md").symlink_to(victim)
    with pytest.raises(ValueError, match="symlink"):
        first.rollback(project, repo_root=tmp_path)
    assert victim.read_text() == "outside"
