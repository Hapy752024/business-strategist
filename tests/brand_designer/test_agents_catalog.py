from __future__ import annotations
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"


def test_catalog_lists_brand_motion_designer() -> None:
    catalog = json.loads((ROOT / "config/skill-catalog.json").read_text())["skills"]
    assert "brand-motion-designer" in catalog
    assert (ROOT / ".agents/skills/brand-motion-designer/SKILL.md").is_file()


def test_catalog_lists_brand_ui_component_producer() -> None:
    catalog = json.loads((ROOT / "config/skill-catalog.json").read_text())["skills"]
    assert "brand-ui-component-producer" in catalog
    assert (ROOT / ".agents/skills/brand-ui-component-producer/SKILL.md").is_file()


def test_root_links_canonical_catalog_and_pipeline() -> None:
    text = AGENTS.read_text(encoding="utf-8")
    for path in ("config/skill-catalog.json", ".agents/skills/business-strategist/references/routing.md"):
        assert path in text
        assert (ROOT / path).is_file()
    # Pipeline order belongs to the specialist; test_orchestrator_routing checks it.
