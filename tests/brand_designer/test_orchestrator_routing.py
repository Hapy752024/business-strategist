from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".agents/skills/brand-designer"


def test_routing_lists_both_new_skills() -> None:
    routing = (SKILL_DIR / "references/routing.md").read_text(encoding="utf-8")
    assert "brand-motion-designer" in routing, "routing.md missing brand-motion-designer"
    assert "brand-ui-component-producer" in routing, "routing.md missing brand-ui-component-producer"


def test_routing_pipeline_order_is_correct() -> None:
    routing = (SKILL_DIR / "references/routing.md").read_text(encoding="utf-8")
    imagery_style = routing.find("Imagery art direction")
    motion_concept = routing.find("Motion concept")
    imagery = routing.find("Imagery assets")
    kit = routing.find("UI tokens")
    motion_tokens = routing.find("Motion tokens and reference implementations")
    components = routing.find("UI component library")
    frontend = routing.find("Frontend apps/flows")
    assert -1 not in (imagery_style, motion_concept, imagery, kit, motion_tokens, components, frontend), (
        "routing.md must list imagery-style, motion-concept, imagery, tokens, motion, components, frontend lines"
    )
    assert imagery_style < motion_concept < imagery < kit < motion_tokens < components < frontend, (
        "pipeline order must be: imagery-style gate -> motion-concept gate -> imagery -> "
        "ui-kit-producer -> motion-designer (tokens/impls) -> ui-component-producer -> frontend-app-designer"
    )


def test_skill_md_mentions_both_new_skills() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "brand-motion-designer" in skill
    assert "brand-ui-component-producer" in skill


def test_finalization_gate_includes_motion_and_components() -> None:
    gate = (SKILL_DIR / "references/finalization-gate.md").read_text(encoding="utf-8")
    assert "motion/" in gate
    assert "components/" in gate
    assert "motion-guidelines.md" in gate


def test_guided_journey_has_motion_and_components_stages() -> None:
    journey = (SKILL_DIR / "references/guided-user-journey.md").read_text(encoding="utf-8")
    assert "Motion" in journey
    assert "Components" in journey
