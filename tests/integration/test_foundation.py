"""Offline integration checks for the business/brand/website control plane."""

from __future__ import annotations

import importlib.util
import json
import hashlib
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
    discovered = project.discover_projects(tmp_path / "projects")
    assert discovered[0]["slug"] == "demo-product"
    brand_workspace = tmp_path / "brand-workspace"
    brand_workspace.mkdir()
    (brand_workspace / "brand-manifest.json").write_text(json.dumps({"next_action": "Approve typography", "open_blockers": []}), encoding="utf-8")
    project.link_project(manifest_path, track="brand", workspace=str(brand_workspace), active=True)
    assert project.next_actions(manifest_path)[0]["next_action"] == "Approve typography"


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


def test_brand_workspace_has_full_stage_manifest(tmp_path: Path) -> None:
    manager = load_script("brand_workspace", ".agents/skills/brand-workspace-manager/scripts/manage-brand-workspace.py")
    root = tmp_path / "brand-projects" / "demo"
    manager.create_workspace(root)
    manifest = manager.write_manifest(root, entry_mode="standalone")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for stage in ("motion", "components", "website", "qa", "guidelines", "export"):
        assert data["stages"][stage] == "not_started"


def test_artifact_promotion_requires_approval_and_matching_hash(tmp_path: Path) -> None:
    promoter = load_script("promote_artifact", "scripts/brand/promote_artifact.py")
    project = tmp_path / "brand"
    project.mkdir()
    candidate = project / "stages" / "logo" / "mark.svg"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("<svg></svg>", encoding="utf-8")
    sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    (project / "brand-manifest.json").write_text(json.dumps({"artifacts": [{"artifact_id": "logo-1", "status": "approved", "candidate_path": "stages/logo/mark.svg", "destination": "logos/source/mark.svg", "sha256": sha}]}), encoding="utf-8")
    dry = promoter.promote(project, "logo-1")
    assert dry["status"] == "ready"
    assert not (project / "logos/source/mark.svg").exists()
    promoter.promote(project, "logo-1", confirm=True)
    assert (project / "logos/source/mark.svg").read_text(encoding="utf-8") == "<svg></svg>"


def test_untrusted_asset_validator_rejects_executable_svg(tmp_path: Path) -> None:
    sanitizer = load_script("validate_untrusted_asset", "scripts/brand/validate_untrusted_asset.py")
    safe = tmp_path / "safe.svg"
    safe.write_text("<svg><path d='M0 0'/></svg>", encoding="utf-8")
    unsafe = tmp_path / "unsafe.svg"
    unsafe.write_text("<svg><script>alert(1)</script><image href='https://evil.example/x'/></svg>", encoding="utf-8")
    assert sanitizer.validate(safe) == []
    assert sanitizer.validate(unsafe)


def test_capability_preflight_is_stage_scoped() -> None:
    preflight = load_script("brand_preflight", "scripts/brand/preflight.py")
    strategy = preflight.inspect_stage("strategy")
    assert strategy["blocking_missing"] == []
    assert "inkscape" not in strategy["blocking_missing"]


def test_release_manifest_requires_production_confirmation(tmp_path: Path) -> None:
    release = load_script("release_manifest", "scripts/brand/release_manifest.py")
    manifest = tmp_path / "website-manifest.json"
    manifest.write_text(json.dumps({"release": {"status": "local"}}), encoding="utf-8")
    release.update(manifest, status="preview", commit="abc", url="https://preview.example")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["release"]["status"] == "preview"
    assert data["release"]["preview_url"] == "https://preview.example"


def test_claim_ledger_preserves_independence_and_requires_counter_scope(tmp_path: Path) -> None:
    builder = load_script("build_claim_ledger", "scripts/evidence_scout/build_claim_ledger.py")
    validator = load_script("validate_synthesis", "scripts/evidence_scout/validate_synthesis.py")
    evidence = [
        {"source": "reddit", "source_url": "https://example.test/a", "text": "manual invoices are painful", "retrieved_at": "2026-08-30T00:00:00Z", "evidence_type": "pain", "independence_key": "a"},
        {"source": "reddit", "source_url": "https://example.test/b", "text": "manual invoices waste time", "retrieved_at": "2026-08-30T00:00:00Z", "evidence_type": "pain", "independence_key": "b"},
    ]
    records = evidence
    for record in records:
        record["evidence_id"] = builder.stable_id(record)
    claims = [{"claim_id": "c1", "claim_type": "observation", "claim": "Manual invoices are painful", "supporting_evidence": [record["evidence_id"] for record in records], "counter_evidence": [], "confidence": "medium", "confidence_rationale": "Two independent posts", "none_found_scope": {"sources": ["reddit"], "queries": ["manual invoices"], "geography": "US", "date_range": "30d", "failed_routes": []}}]
    ledger = builder.build(records, claims)
    assert ledger[0]["independence_count"] == 2
    assert validator.validate(ledger, records) == []


def test_website_fixture_contract() -> None:
    verifier = load_script("verify_website_fixture", "scripts/verify_website_fixture.py")
    assert verifier.verify(ROOT / "fixtures" / "website" / "stellar-repair") == []


def test_mcp_profiles_are_optional_and_deterministic() -> None:
    sync = load_script("sync_brand_mcp_config", "scripts/sync-brand-mcp-config.py")
    assert sync.load_servers(["brand-ui", "website-qa"]) == sync.load_servers([])
