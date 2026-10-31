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


def test_restored_standing_rules_present():
    text = _normalized(AGENTS.read_text(encoding="utf-8"))
    for phrase in ("required_references", "precedent", "official statistics", "skill tool"):
        assert phrase in text, f"{phrase!r} missing from AGENTS.md"
    assert "research-data-and-precedents.md" in text
    assert "opportunity-research-approaches.md" in text


def test_pain_first_gate_sentence_shared_across_its_three_homes():
    """The gate is stated in AGENTS.md, the router skill and the path rule; one shared sentence prevents drift."""
    phrase = _normalized("Business commitments (business model, offer and GTM) stay gated until `problem_validation` "
                         "passes or an explicit override is recorded")
    for path in (AGENTS, ROOT / ".agents/skills/business-strategist/SKILL.md", ROOT / ".claude/rules/business-gate.md"):
        assert phrase in _normalized(path.read_text(encoding="utf-8")), path.relative_to(ROOT)


def test_rule_prose_lives_in_one_place():
    """Generic rule prose has one home; scripts enforce the rest."""
    pain_homes = {
        "AGENTS.md",
        ".claude/rules/business-gate.md",
        ".agents/skills/business-strategist/SKILL.md",
    }
    pain, boilerplate, criteria = set(), set(), []
    for path in list(ROOT.glob("*.md")) + [
        p for d in ("references", "templates", ".agents", ".claude/rules", "scripts")
        for p in (ROOT / d).rglob("*") if p.is_file() and p.suffix in {".md", ".py"}
    ]:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        flat = _normalized(text)
        if "until problem_validation passes" in flat:
            pain.add(rel)
        if "load only the additional references" in flat:
            boilerplate.add(rel)
        if path.name == "SKILL.md" and re.search(r"triggers on[^\n]*\d\s*%", text, re.I):
            criteria.append(rel)
    assert pain <= pain_homes, sorted(pain - pain_homes)
    assert len(boilerplate) <= 1, sorted(boilerplate)
    assert not criteria, criteria
