from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"


def test_catalog_lists_brand_motion_designer() -> None:
    text = AGENTS.read_text(encoding="utf-8")
    assert "- `brand-motion-designer`:" in text


def test_catalog_lists_brand_ui_component_producer() -> None:
    text = AGENTS.read_text(encoding="utf-8")
    assert "- `brand-ui-component-producer`:" in text


def test_catalog_pipeline_order() -> None:
    text = AGENTS.read_text(encoding="utf-8")
    kit = text.find("`brand-ui-kit-producer`")
    motion = text.find("`brand-motion-designer`")
    components = text.find("`brand-ui-component-producer`")
    frontend = text.find("`brand-frontend-app-designer`")
    assert 0 < kit < motion < components < frontend, (
        "AGENTS.md catalog must list skills in pipeline order: "
        "ui-kit-producer -> motion-designer -> ui-component-producer -> frontend-app-designer"
    )
