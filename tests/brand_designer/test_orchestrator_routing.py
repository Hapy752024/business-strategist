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
    kit = routing.find("brand-ui-kit-producer")
    motion = routing.find("brand-motion-designer")
    components = routing.find("brand-ui-component-producer")
    frontend = routing.find("brand-frontend-app-designer")
    assert kit < motion < components < frontend, (
        "pipeline order must be: ui-kit-producer -> motion-designer -> "
        "ui-component-producer -> frontend-app-designer"
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
