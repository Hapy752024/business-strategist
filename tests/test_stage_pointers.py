"""Each stage names the new capabilities at the moment of use (Task 7.4A).

A pointer counts when it is in the skill's SKILL.md (what the agent reads first);
skills in ONE_HOP may instead name it in a reference file their SKILL.md links directly.
Every script path a pointer names must exist.
"""
import re
from pathlib import Path

import pytest

from scripts.route_workflow import route_request

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents/skills"

POINTERS = {
    "archetype-gtm-strategist": [
        "case_insights.md", "build_decision_memo", "search_journey", "--content-inventory",
        "social_topics", "keyword_map.py merge", "brand-website-designer-builder", "site_gate",
        "geo-audit", "first-campaign-runbook", "marketing-campaign-operator",
    ],
    "evidence-scout": [
        "search_journey", "build_decision_memo", "build_voc_table", "research-data-and-precedents.md",
    ],
    "opportunity-risk-designer": [
        "build_voc_table", "build_decision_memo", "falsify.md", "claim-falsification",
    ],
    "marketing": [
        "keyword_map.py merge", "search_journey", "site_gate", "verify_tracking",
    ],
    "brand-website-designer-builder": ["site_gate", "geo-audit", "verify_tracking"],
    "idea-grill": ["Skill tool", "evidence-scout", "precedent"],
}


ONE_HOP = {"archetype-gtm-strategist"}


def skill_text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def one_hop_text(name: str) -> str:
    text = skill_text(name)
    parts = [text]
    for ref in sorted(set(re.findall(r"(?<![\w/.-])((?:\.\./[\w-]+/)?references/[\w-]+\.md)", text))):
        for base in (SKILLS / name, ROOT):
            if (base / ref).is_file():
                parts.append((base / ref).read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_gtm_points_to_handoffs_at_top():
    head = skill_text("archetype-gtm-strategist").split("## Success Criteria")[0]
    assert "references/handoffs.md" in head


@pytest.mark.parametrize("skill,needles", POINTERS.items())
def test_stage_pointer_present(skill, needles):
    text = one_hop_text(skill) if skill in ONE_HOP else skill_text(skill)
    missing = [n for n in needles if n not in text]
    assert not missing, f"{skill}/SKILL.md lacks {missing}"


@pytest.mark.parametrize("skill", POINTERS)
def test_named_scripts_exist(skill):
    text = one_hop_text(skill)
    for path in re.findall(r"scripts/[\w/.-]+\.py", text):
        assert (ROOT / path).is_file(), f"{skill} names missing {path}"
    for ref in re.findall(r"`(\.agents/skills/[\w/.-]+\.md)`", text):
        assert (ROOT / ref).is_file(), f"{skill} names missing {ref}"


def test_campaign_operator_stays_founder_invoked():
    text = skill_text("marketing-campaign-operator")
    assert "disable-model-invocation: true" in text


@pytest.mark.parametrize("prompt,skill", [
    ("Assess this business idea and research customers", "idea-grill"),
    ("Plan our SEO content", "marketing"),
    ("What will customers search for?", "evidence-scout"),
])
def test_new_routing_phrases(prompt, skill):
    assert route_request(prompt)["skill"] == skill
