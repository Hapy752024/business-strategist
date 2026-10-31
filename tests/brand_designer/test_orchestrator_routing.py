from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".agents/skills/brand-identity"
ORCHESTRATION = SKILL_DIR / "references/orchestration.md"


def test_orchestration_assigns_ui_stages_to_brand_ui_system() -> None:
    text = ORCHESTRATION.read_text(encoding="utf-8")
    assert "brand-ui-system" in text
    for mode in ("`kit`", "`motion`", "`components`", "`app`"):
        assert mode in text, f"orchestration.md missing {mode} owner"


def test_stage_gate_pipeline_order_is_correct() -> None:
    order = next(line for line in ORCHESTRATION.read_text(encoding="utf-8").splitlines() if "Default order:" in line)
    steps = ["imagery style", "motion concept", "-> imagery ->", "UI tokens", "motion tokens", "components", "app screens"]
    positions = [order.find(step) for step in steps]
    assert -1 not in positions, dict(zip(steps, positions))
    assert positions == sorted(positions), (
        "pipeline order must be: imagery-style gate -> motion-concept gate -> imagery -> "
        "UI tokens -> motion tokens/impls -> components -> app screens"
    )


def test_stage_gates_are_a_numbered_checklist() -> None:
    text = ORCHESTRATION.read_text(encoding="utf-8")
    for gate in ("Discovery before anything else", "Strategy approval before final assets",
                 "Paid generation needs approval", "Promote only approved artifacts",
                 "Review before finalization", "Finalization gate before"):
        assert gate in text, gate


def test_skill_md_mentions_ui_system_and_critic() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "brand-ui-system" in skill
    assert "brand-critic" in skill


def test_finalization_gate_includes_motion_and_components() -> None:
    gate = (SKILL_DIR / "references/finalization-gate.md").read_text(encoding="utf-8")
    assert "motion/" in gate
    assert "components/" in gate
    assert "motion-guidelines.md" in gate


def test_guided_journey_has_motion_and_components_stages() -> None:
    journey = ORCHESTRATION.read_text(encoding="utf-8")
    assert "Motion" in journey
    assert "Components" in journey
