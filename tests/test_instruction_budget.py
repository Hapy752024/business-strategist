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


def test_agents_md_word_budget():
    assert len(AGENTS.read_text(encoding="utf-8").split()) <= 600


def test_each_skill_md_word_budget():
    over = {
        str(p.relative_to(ROOT)): len(p.read_text(encoding="utf-8").split())
        for p in sorted((ROOT / ".agents/skills").glob("*/SKILL.md"))
        if len(p.read_text(encoding="utf-8").split()) > 450
    }
    assert not over, over


def _words(root: Path, pattern: str) -> int:
    return sum(len(p.read_text(encoding="utf-8").split()) for p in root.glob(pattern) if p.is_file())


def test_skill_reference_word_total_phase1():
    assert _words(ROOT / ".agents/skills", "*/references/**/*.md") <= 90_000


def test_root_reference_word_total_phase1():
    assert _words(ROOT / "references", "**/*.md") <= 30_000


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


ROUTING = "references/runtime-routing.md"
# Distinct skill-specific carve-outs: (skill, distinguishing substring of the line).
PAIN_GATE_CARVE_OUTS = [
    ("idea-grill", "Recruitment planning is allowed before the pain gate"),
    ("idea-grill", "Pain-first back-track"),
    ("startup-business-builder", "no selection or passed pain gate"),
    ("startup-business-builder", "waive the pain-first gate"),
    ("market-problem-discovery", "It runs before the pain gate"),
    ("opportunity-risk-designer", "A passed pain gate or selection is not required"),
    ("evidence-scout", "None waits for review, synthesis, a claim ledger, the pain-first gate"),
]


def _prose_files(*dirs):
    for d in dirs:
        yield from (p for p in (ROOT / d).rglob("*") if p.is_file() and p.suffix in {".md", ".py"})


def test_rule_prose_lives_in_one_place():
    """Generic rule prose has one home; scripts enforce the rest."""
    boilerplate, promote, criteria, strays = set(), set(), [], []
    files = list(ROOT.glob("*.md")) + list(_prose_files("references", "templates", ".agents", ".claude/rules", "scripts"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        flat = _normalized(text)
        if "load only the additional references" in flat:
            boilerplate.add(rel)
        if "never promote unapproved" in flat:
            promote.add(rel)
        if path.name != "SKILL.md":
            continue
        if re.search(r"triggers on[^\n]*\d\s*%", text, re.I):
            criteria.append(rel)
        skill = path.parent.name
        if skill == "business-strategist":
            continue
        for line in text.splitlines():
            if re.search(r"pain-first|pain gate|problem_validation", line, re.I):
                if not any(skill == s and sub in line for s, sub in PAIN_GATE_CARVE_OUTS):
                    strays.append(f"{skill}: {line.strip()[:80]}")
    assert boilerplate == {ROUTING}, sorted(boilerplate)
    assert promote == {ROUTING}, sorted(promote)
    assert not criteria, criteria
    assert not strays, strays
