from __future__ import annotations
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_claude_skills_symlink_exists() -> None:
    link = ROOT / ".claude/skills"
    assert link.exists() or link.is_symlink(), ".claude/skills is missing or not a symlink"


def test_claude_skills_points_to_agents_skills() -> None:
    link = ROOT / ".claude/skills"
    if link.is_symlink():
        target = os.readlink(link)
        assert target.endswith(".agents/skills") or target.endswith(".agents/skills/"), (
            f".claude/skills -> {target} (expected ../.agents/skills)"
        )


def test_new_skills_visible_via_claude_skills() -> None:
    base = ROOT / ".claude/skills"
    assert (base / "brand-motion-designer/SKILL.md").exists()
    assert (base / "brand-ui-component-producer/SKILL.md").exists()


def test_catalog_exposes_imported_skills() -> None:
    catalog = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "brand-motion-designer" in catalog
    assert "brand-ui-component-producer" in catalog
