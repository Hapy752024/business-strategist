"""AGENTS.md holds always-true facts; procedures live in the owning skills."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "")).lower()


def test_agents_md_under_budget():
    text = AGENTS.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 150
    assert len(text.split()) <= 1200


def test_no_rule_duplicated_more_than_once():
    text = _normalized(AGENTS.read_text(encoding="utf-8"))
    for phrase in ("update case_insights", "pain-first"):
        assert text.count(phrase) <= 1, f"{phrase!r} appears {text.count(phrase)} times"


def test_rehomed_rules_present_in_destinations():
    skills = ROOT / ".agents/skills"
    anchors = [
        (skills / "opportunity-risk-designer/SKILL.md", "served-versus-entrant", False),
        (skills / "evidence-scout/SKILL.md", "entity-led", False),
        (skills / "startup-business-builder/SKILL.md", "Provisional plans do not select execution", False),
        (AGENTS, "credit failures are coverage gaps", True),
        (AGENTS, "task-scope.md", False),
    ]
    for path, phrase, ignore_case in anchors:
        text = path.read_text(encoding="utf-8")
        if ignore_case:
            text, phrase = text.lower(), phrase.lower()
        assert phrase in text, f"{phrase!r} missing from {path.relative_to(ROOT)}"
