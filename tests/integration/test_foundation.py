"""Offline integration checks for the business/brand/website control plane."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_routes_keep_branding_independent_and_website_specific() -> None:
    route = load_script("route_workflow", "scripts/route_workflow.py")
    standalone = route.route_request("Develop a brand identity and logo without research")
    assert standalone["skill"] == "brand-designer"
    website = route.route_request("Build a visually stunning unique Next.js landing page")
    assert website["skill"] == "brand-website-designer-builder"
    app = route.route_request("Design product dashboard UI screens")
    assert app["skill"] == "brand-frontend-app-designer"


def test_project_manifest_revision_and_cas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = load_script("project_workspace", "scripts/project_workspace.py")
    monkeypatch.setattr(project, "PROJECTS_ROOT", tmp_path / "projects")
    manifest_path = project.create_project("Demo Product")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["manifest_revision"] == 1
    revision = project.link_project(manifest_path, track="brand", workspace="/tmp/brand-workspace", active=True)
    assert revision == 2
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["active_track"] == "brand"
    with pytest.raises(RuntimeError, match="revision conflict"):
        project.write_json_atomic(manifest_path, data, expected_revision=1)


def test_business_to_brand_snapshot_preserves_gaps(tmp_path: Path) -> None:
    builder = load_script("build_handoff", "scripts/brand/build_business_to_brand_handoff.py")
    validator = load_script("validate_handoff", "scripts/brand/validate_business_to_brand_handoff.py")
    source = tmp_path / "business-manifest.json"
    source.write_text(json.dumps({"schema_version": "1.0", "segment": {"name": "operators"}, "coverage_gaps": ["pricing"]}), encoding="utf-8")
    snapshot = builder.build_snapshot(source)
    output = tmp_path / "brand" / "business-to-brand.json"
    output.parent.mkdir()
    output.write_text(json.dumps(snapshot), encoding="utf-8")
    assert validator.validate(output) == []
    assert snapshot["coverage_gaps"] == ["pricing"]
    assert snapshot["field_provenance"]["positioning"] == "unresolved"


def test_fal_adapter_defaults_to_redacted_dry_run() -> None:
    fal = load_script("fal_assets", "scripts/fal_assets.py")
    args = type("Args", (), {"endpoint": "fal-ai/flux/schnell", "prompt": "test", "negative_prompt": "", "variants": 1, "width": 512, "height": 512, "seed": 7, "estimated_cost": 0.0, "max_cost": 0.0, "approval_id": "TEST", "retention_seconds": 60})()
    request = fal.build_request(args)
    assert request["store_io"] is False
    assert "FAL_AI_API_KEY" not in json.dumps(request)
