from __future__ import annotations
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"


def test_catalog_lists_brand_ui_system_motion_mode() -> None:
    catalog = json.loads((ROOT / "config/skill-catalog.json").read_text())["skills"]
    assert "motion" in catalog["brand-ui-system"]["modes"]
    assert (ROOT / ".agents/skills/brand-ui-system/SKILL.md").is_file()


def test_catalog_lists_brand_ui_system_components_mode() -> None:
    catalog = json.loads((ROOT / "config/skill-catalog.json").read_text())["skills"]
    assert "components" in catalog["brand-ui-system"]["modes"]
    assert (ROOT / ".agents/skills/brand-ui-system/references/components.md").is_file()


def test_root_links_canonical_catalog_and_pipeline() -> None:
    text = AGENTS.read_text(encoding="utf-8")
    for path in ("config/skill-catalog.json", "references/runtime-routing.md"):
        assert path in text
        assert (ROOT / path).is_file()
    # Pipeline order belongs to the specialist; test_orchestrator_routing checks it.
