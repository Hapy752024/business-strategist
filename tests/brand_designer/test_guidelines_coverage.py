from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
WRITER = ROOT / ".agents/skills/brand-guidelines-writer/SKILL.md"


def test_guidelines_include_motion_section() -> None:
    text = WRITER.read_text(encoding="utf-8")
    assert "Motion" in text
    assert "motion-guidelines.md" in text


def test_guidelines_include_component_section() -> None:
    text = WRITER.read_text(encoding="utf-8")
    assert "UI components" in text or "component library" in text.lower()
    assert "components/README.md" in text
