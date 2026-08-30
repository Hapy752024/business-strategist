from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPORTER = ROOT / ".agents/skills/brand-exporter/SKILL.md"


def test_exporter_includes_motion_tokens() -> None:
    text = EXPORTER.read_text(encoding="utf-8")
    assert "motion/motion-tokens.css" in text
    assert "motion/motion-tokens.ts" in text
    assert "motion-guidelines.md" in text


def test_exporter_includes_component_library() -> None:
    text = EXPORTER.read_text(encoding="utf-8")
    assert "components/" in text
    assert "components/README.md" in text


def test_exporter_manifest_section_lists_motion_and_components() -> None:
    text = EXPORTER.read_text(encoding="utf-8")
    assert "PACKAGE-MANIFEST.md" in text
    assert "Motion" in text
    assert "Components" in text
