import json
import shutil
from pathlib import Path

import pytest

from scripts import layout_migration as migration
from scripts import migrate_project_cases as generic


ROOT = Path(__file__).resolve().parents[1]


def tattoo_copy(tmp_path):
    source = tmp_path / "projects" / "tattoo-insurance"
    source.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "projects/tattoo-insurance", source, symlinks=True)
    analysis = source / "business-analysis"
    snapshot = analysis / "history/snapshots/case-layout-tattoo-insurance"
    shutil.copy2(snapshot / "README.md", source / "README.md")
    shutil.copy2(snapshot / "project-manifest.json", source / "project-manifest.json")
    shutil.move(str(analysis / "market_research"), str(source / "market_research"))
    shutil.move(str(analysis / "history/legacy/strategy"), str(source / "strategy"))
    shutil.rmtree(analysis)
    shutil.rmtree(source / "history")
    (source / "project.lock").unlink(missing_ok=True)
    (source / "project-manifest.json").write_bytes((ROOT / "projects/tattoo-insurance/business-analysis/history/snapshots/case-layout-tattoo-insurance/project-manifest.json").read_bytes())
    return source


def test_generic_tattoo_rehearsal_preserves_sources_and_resets_case_authority(tmp_path):
    project = tattoo_copy(tmp_path)
    before = migration.digest_tree(project)
    generic.execute("tattoo-insurance", repo_root=tmp_path)
    current = migration.digest_tree(project)
    assert current
    journal = migration.journal("tattoo-insurance", root=tmp_path)
    assert journal["state"] == "verified"
    assert json.loads((project / "project-manifest.json").read_text())["controller_kind"] == "umbrella"
    analysis = project / "business-analysis"
    assert not (analysis / "market_research/manifest.json").exists()
    for case_id, _ in generic.SPECS["tattoo-insurance"]["cases"]:
        manifest = json.loads((analysis / "project-manifest.json").read_text())
        assert manifest["cases"][case_id]["retired"] is False
        case = json.loads((analysis / "cases" / case_id / "market_research/manifest.json").read_text())
        assert case["stages"] == {}
        assert case["open_blockers"]
    assert all(value in current.values() for name, value in before.items() if name.startswith("market_research/"))


def test_generic_tattoo_rollback_restores_exact_baseline(tmp_path):
    project = tattoo_copy(tmp_path)
    before = migration.digest_tree(project)
    generic.execute("tattoo-insurance", repo_root=tmp_path)
    journal = migration.journal("tattoo-insurance", root=tmp_path)
    journal["state"] = "replacement_installed"
    migration.write_journal("tattoo-insurance", journal, root=tmp_path)
    generic.rollback("tattoo-insurance", repo_root=tmp_path)
    assert migration.journal("tattoo-insurance", root=tmp_path)["state"] == "rolled_back"
    assert migration.digest_tree(project) == before


def test_generic_rollback_recovers_crash_before_phase_journal(tmp_path, monkeypatch):
    project = tattoo_copy(tmp_path)
    before = migration.digest_tree(project)
    original_add = generic.cases.add_case
    raised = False

    def interrupt_after_first_case(*args, **kwargs):
        nonlocal raised
        result = original_add(*args, **kwargs)
        if not raised:
            raised = True
            raise RuntimeError("interrupted before phase journal")
        return result

    monkeypatch.setattr(generic.cases, "add_case", interrupt_after_first_case)
    with pytest.raises(RuntimeError, match="interrupted before phase journal"):
        generic.execute("tattoo-insurance", repo_root=tmp_path)
    monkeypatch.setattr(generic.cases, "add_case", original_add)
    generic.rollback("tattoo-insurance", repo_root=tmp_path)
    assert migration.digest_tree(project) == before


def test_generic_rollback_refuses_external_edit(tmp_path):
    project = tattoo_copy(tmp_path)
    original_add = generic.cases.add_case

    def interrupt(*args, **kwargs):
        result = original_add(*args, **kwargs)
        raise RuntimeError("stop")

    # Leave a prepared journal and a partial generated tree.
    import pytest
    with pytest.raises(RuntimeError):
        generic.cases.add_case = interrupt
        generic.execute("tattoo-insurance", repo_root=tmp_path)
    generic.cases.add_case = original_add
    (project / "README.md").write_text("external edit\n")
    with pytest.raises(ValueError, match="external modification"):
        generic.rollback("tattoo-insurance", repo_root=tmp_path)


def test_generic_rollback_resumes_after_replace_crash(tmp_path, monkeypatch):
    project = tattoo_copy(tmp_path)
    generic.execute("tattoo-insurance", repo_root=tmp_path)
    journal = migration.journal("tattoo-insurance", root=tmp_path)
    journal["state"] = "replacement_installed"
    migration.write_journal("tattoo-insurance", journal, root=tmp_path)
    original_copytree = generic.shutil.copytree

    def crash(*args, **kwargs):
        raise RuntimeError("copy interrupted")

    monkeypatch.setattr(generic.shutil, "copytree", crash)
    with pytest.raises(RuntimeError, match="copy interrupted"):
        generic.rollback("tattoo-insurance", repo_root=tmp_path)
    monkeypatch.setattr(generic.shutil, "copytree", original_copytree)
    generic.rollback("tattoo-insurance", repo_root=tmp_path)
    assert migration.digest_tree(project) == migration.journal("tattoo-insurance", root=tmp_path)["baseline_files"]
