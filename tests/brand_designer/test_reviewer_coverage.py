from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEWER = ROOT / ".agents/skills/brand-quality-reviewer/SKILL.md"


def test_reviewer_checks_motion_coherence() -> None:
    text = REVIEWER.read_text(encoding="utf-8")
    assert "motion coherence" in text.lower() or "motion-guidelines.md" in text


def test_reviewer_checks_component_coverage() -> None:
    text = REVIEWER.read_text(encoding="utf-8")
    assert "component coverage" in text.lower() or "scope.json" in text


def test_reviewer_references_both_validation_scripts() -> None:
    text = REVIEWER.read_text(encoding="utf-8")
    assert "validate-motion-tokens.py" in text
    assert "validate-component.py" in text
