"""Tests for scripts/migrate_project_layout.py (project-centric layout migration).

Fixtures mirror the real legacy tree: 5 manifest workspaces, 4 legacy
no-manifest workspaces, the absorbed brand project (3 on-disk path shapes in
the website manifests), the town DB, and the legacy global dirs.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import migrate_project_layout as mig

REPO_ROOT = Path(__file__).resolve().parents[1]


def _manifest(slug: str, stages: dict) -> dict:
    return {
        "schema_version": "1.0",
        "topic": slug,
        "topic_slug": slug,
        "created_at": "2026-08-01T00:00:00Z",
        "updated_at": "2026-08-01T00:00:00Z",
        "current_stage": "evidence_collection",
        "stages": stages,
        "events": [],
        "open_blockers": [],
        "artifacts": [],
    }


def _evidence_stage(paths: list[str]) -> dict:
    # Production manifests store artifacts as {path, type, description} dicts.
    return {
        "stage": "evidence_collection",
        "status": "passed",
        "timestamp": "2026-08-30T00:00:00Z",
        "gate_result": "conditional_pass",
        "artifacts": [{"path": p, "type": p.rsplit(".", 1)[-1], "description": "evidence_collection artifact"}
                      for p in paths],
    }


def _pending_stage(name: str) -> dict:
    return {"stage": name, "status": "pending", "timestamp": "2026-08-01T00:00:00Z", "artifacts": []}


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def build_fixture(root: Path) -> None:
    topics = root / "projects/research/topics"

    # 1. us-retirees-italy: standard manifest workspace with evidence runs.
    base = topics / "us-retirees-italy"
    _write(base / "README.md", "# US retirees Italy\n")
    _write(base / "manifest.json", json.dumps(_manifest("us-retirees-italy", {
        "evidence_collection": _evidence_stage(["evidence/runs/r1/report.md", "evidence/runs/r1/evidence.jsonl"]),
        "problem_validation": _pending_stage("problem_validation"),
        "customer_profile": {**_pending_stage("customer_profile"), "status": "passed",
                             "gate_result": "conditional_pass",
                             "artifacts": [{"path": "retiree-customer-journey.md", "type": "md",
                                            "description": "journey"}]},
    })))
    _write(base / "evidence/runs/r1/report.md", "evidence report\n")
    _write(base / "evidence/runs/r1/evidence.jsonl", '{"evidence_id": "e1"}\n')
    _write(base / "evidence/runs/r1/raw/reddit.json", "{}")
    _write(base / "retiree-customer-journey.md", "journey\n")
    _write(base / "canvases/business-model-canvas.md", "canvas\n")
    _write(base / "intake/startup-thesis.md", "thesis\n")
    _write(base / "competitors/runs/crun-1/competitors.json", "[]")
    _write(base / "competitors/other-country-pricing.md", "pricing\n")
    (base / "reviews").mkdir(parents=True)  # empty dir: must vanish, not migrate

    # 2. german-insurance-opportunity: loose root evidence run + extra dirs.
    base = topics / "german-insurance-opportunity"
    _write(base / "README.md", "# German insurance\n")
    _write(base / "manifest.json", json.dumps(_manifest("german-insurance-opportunity", {
        "evidence_collection": _evidence_stage(["evidence.jsonl", "sources.md", "summary.json"]),
        "problem_validation": _pending_stage("problem_validation"),
        "segment_selection": {**_pending_stage("segment_selection"), "status": "in_progress",
                              "artifacts": [{"path": "three-ideas-decision-memo.md", "type": "md",
                                             "description": "memo"}]},
    })))
    _write(base / "manifest.lock", "")
    _write(base / "evidence.jsonl", '{"evidence_id": "g1"}\n')
    _write(base / "summary.json", "{}")
    _write(base / "report.md", "root run report\n")
    _write(base / "sources.md", "sources\n")
    _write(base / "raw/serp.json", "{}")
    _write(base / "runs/2026-09-06-positioning/run-manifest.json", "{}")
    _write(base / "deep-dives/2026-09-06-three-idea-reassessment.md", "deep dive\n")
    _write(base / "three-ideas-decision-memo.md", "memo\n")
    _write(base / "pain-versus-offer-matrix.md", "matrix\n")
    _write(base / "profession-segments-and-relationship-model.md", "segments\n")
    _write(base / "self-employment-journeys-it-and-doctors.md", "journeys\n")
    _write(base / "strategy-plan.json", "{}")
    _write(base / "playbooks/runs/pb-1/run_summary.json", "{}")
    _write(base / "evidence/idea-1-personal/run-2026-09-06/evidence.jsonl", "{}\n")
    _write(base / "evidence/runs/2026-09-06-refresh-mga-v2/evidence.jsonl", "{}\n")

    # 3. meal-planning: evidence passed -> backfill applies.
    base = topics / "meal-planning-for-busy-parents"
    _write(base / "README.md", "# Meal planning\n")
    _write(base / "manifest.json", json.dumps(_manifest("meal-planning-for-busy-parents", {
        "evidence_collection": _evidence_stage(["evidence/runs/m1/report.md"]),
        "problem_validation": _pending_stage("problem_validation"),
    })))
    _write(base / "evidence/runs/m1/report.md", "report\n")

    # 4. self-employed-professionals-germany: NO evidence runs -> no backfill.
    base = topics / "self-employed-professionals-germany"
    _write(base / "README.md", "# Self-employed\n")
    _write(base / "manifest.json", json.dumps(_manifest("self-employed-professionals-germany", {
        "evidence_collection": _pending_stage("evidence_collection"),
        "problem_validation": _pending_stage("problem_validation"),
    })))
    _write(base / "ads/runs/a1/ads.jsonl", "{}\n")

    # 5. social-access smoke test: evidence passed -> backfill applies.
    slug5 = "social-access-smoke-test-private-health-insurance-germany"
    base = topics / slug5
    _write(base / "README.md", "# Smoke test\n")
    _write(base / "manifest.json", json.dumps(_manifest(slug5, {
        "evidence_collection": _evidence_stage(["evidence/runs/s1/report.md"]),
        "problem_validation": _pending_stage("problem_validation"),
    })))
    _write(base / "evidence/runs/s1/report.md", "report\n")

    # 6-9. Legacy no-manifest workspaces.
    _write(topics / "Surelius/current_pain_points.md", "pains\n")
    _write(topics / "Surelius/life_change_triggers.md", "triggers\n")
    dia = topics / "digital-insurance-agent"
    for name in ("README.md", "customer-segments-and-journey.md", "digital-workflow-and-app.md",
                 "go-to-market-strategy.md", "research-notes-and-sources.md", "social-media-playbook.md"):
        _write(dia / name, f"{name}\n")
    _write(topics / "tattoo-insurance/README.md", "# Tattoo\n")
    _write(topics / "tattoo-insurance/sources.md", "sources\n")
    _write(topics / "tattoo-insurance/test-plan.md", "plan\n")
    _write(topics / "tattoo-insurance/evidence/france/evidence.jsonl", "{}\n")
    _write(topics / "tattoo-insurance/competitors/competitors.json", "[]")
    _write(topics / "individualized-marketing-content/evidence/runs/001/evidence.jsonl", "{}\n")
    _write(topics / "individualized-marketing-content/evidence/runs/002/interview/guide.md", "guide\n")

    # Stray topics README + global legacy dirs.
    _write(topics / "README.md", "# topics index\n")
    _write(root / "projects/research/agentic-events.jsonl", "{}\n")
    _write(root / "projects/research/evidence-scout/runs/legacy-run-1/evidence.jsonl", "{}\n")
    _write(root / "projects/research/evidence-scout/competitors/legacy-c1/competitors.json", "[]")
    _write(root / "projects/research/evidence-scout/marketing/legacy-m1/report.md", "report\n")
    _write(root / "projects/research/evidence-scout/api-validation/status.json", "{}")
    _write(root / "projects/research/evidence-scout/provider-doctor/doctor.json", "{}")

    # Brand project absorbed by us-retirees-italy (website has nested .git).
    brand = root / "projects/brand-projects/italy-retiree-move"
    _write(brand / "brand-manifest.json", json.dumps({
        "brand_id": "italy-retiree-move",
        "business_to_brand": "projects/research/topics/us-retirees-italy",
    }))
    _write(brand / "tokens/tokens.css", ":root {}\n")
    _write(brand / "imagery/imagery-manifest.json", json.dumps({
        "images": [{"file": "projects/brand-projects/italy-retiree-move/imagery/hero.png"}]
    }))
    _write(brand / "website/.git/HEAD", "ref: refs/heads/main\n")
    _write(brand / "website/app/page.tsx", "export default function Page() { return null }\n")
    _write(brand / "website/node_modules/some-pkg/index.js", "module.exports = {}\n")
    _write(brand / "website/website-manifest.json", json.dumps({
        "website_id": "italy-retiree-move",
        "brand_refs": ["projects/brand-projects/italy-retiree-move/tokens/tokens.css"],
        "fal_assets": [{"provenance": "brand-projects/italy-retiree-move/imagery/imagery-manifest.json"}],
        "absolute_ref": f"{root.as_posix()}/projects/brand-projects/italy-retiree-move/tokens/tokens.css",
    }))
    _write(root / "projects/brand-projects/italy-town-db/towns.sqlite", b"\x00sqlite-binary\xff")
    _write(root / "projects/brand-projects/italy-town-db/README.md", "# town db\n")

    # Schema needed by controller validation.
    (root / "schemas").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "schemas/project-manifest.schema.json",
                 root / "schemas/project-manifest.schema.json")


def _snapshot(root: Path) -> dict[str, bytes]:
    projects = root / "projects"
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(projects.rglob("*"))
        if p.is_file()
    }


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    build_fixture(tmp_path)
    return tmp_path


def test_dry_run_writes_nothing(repo: Path) -> None:
    before = _snapshot(repo)
    plan = mig.build_plan(repo)
    assert plan["unmapped"] == []
    assert plan["collisions"] == []
    assert set(plan["controllers"]) == set(mig.ALL_PROJECT_SLUGS)
    assert _snapshot(repo) == before


def test_unmapped_file_blocks_execute(repo: Path) -> None:
    _write(repo / "projects/research/topics/us-retirees-italy/mystery-folder/notes.txt", "?\n")
    plan = mig.build_plan(repo)
    assert any("mystery-folder" in entry for entry in plan["unmapped"])


def test_prefix_rule_ordering() -> None:
    workspace = {"root_files": {}, "prefixes": ()}
    assert mig.map_workspace_file(workspace, "competitors/marketing/m1/report.md") == \
        "market_research/solution_alternatives/marketing/m1/report.md"
    assert mig.map_workspace_file(workspace, "competitors/runs/c1/competitors.json") == \
        "market_research/solution_alternatives/runs/c1/competitors.json"
    assert mig.map_workspace_file(workspace, "evidence/runs/r1/evidence.jsonl") == \
        "market_research/pain_points/runs/r1/evidence.jsonl"
    assert mig.map_workspace_file(workspace, "go-to-market/plan.md") == "strategy/gtm/plan.md"
    assert mig.map_workspace_file(workspace, "customer-discovery/notes.md") is None


def test_execute_then_verify(repo: Path) -> None:
    plan = mig.build_plan(repo)
    assert plan["unmapped"] == [] and plan["collisions"] == []
    migration_dir = repo / "projects/_archive/migration-20260911-000000"
    report = mig._execute(repo, plan, migration_dir)
    assert report["residual_legacy_refs"] == []

    projects = repo / "projects"
    # Research reshapes.
    assert (projects / "us-retirees-italy/market_research/manifest.json").exists()
    assert (projects / "us-retirees-italy/market_research/pain_points/runs/r1/evidence.jsonl").exists()
    assert (projects / "us-retirees-italy/market_research/solution_alternatives/runs/crun-1/competitors.json").exists()
    assert (projects / "us-retirees-italy/market_research/solution_alternatives/other-country-pricing.md").exists()
    assert (projects / "us-retirees-italy/market_research/customer_journey/retiree-customer-journey.md").exists()
    assert (projects / "us-retirees-italy/strategy/canvases/business-model-canvas.md").exists()
    # German specials: synthesized legacy run, strategy runs, deep dives, lock file.
    assert (projects / "german-insurance-opportunity/market_research/pain_points/runs/legacy-root-20260906/evidence.jsonl").exists()
    assert (projects / "german-insurance-opportunity/market_research/pain_points/runs/legacy-root-20260906/raw/serp.json").exists()
    assert (projects / "german-insurance-opportunity/strategy/runs/2026-09-06-positioning/run-manifest.json").exists()
    assert (projects / "german-insurance-opportunity/market_research/deep_dives/2026-09-06-three-idea-reassessment.md").exists()
    assert (projects / "german-insurance-opportunity/market_research/manifest.lock").exists()
    # Legacy workspaces.
    assert (projects / "surelius/market_research/pain_points/current_pain_points.md").exists()
    assert (projects / "digital-insurance-agent/marketing/social-media-playbook.md").exists()
    assert (projects / "tattoo-insurance/market_research/pain_points/countries/france/evidence.jsonl").exists()
    assert (projects / "individualized-marketing-content/market_research/pain_points/runs/002/interview/guide.md").exists()
    # Brand absorption + nested repo + node_modules preserved, town DB moved.
    assert (projects / "us-retirees-italy/branding/brand-manifest.json").exists()
    assert (projects / "us-retirees-italy/web-site/.git/HEAD").read_text() == "ref: refs/heads/main\n"
    assert (projects / "us-retirees-italy/web-site/node_modules/some-pkg/index.js").exists()
    assert (projects / "us-retirees-italy/digital-assets/town-db/towns.sqlite").read_bytes() == b"\x00sqlite-binary\xff"
    # Global relocations.
    assert (projects / "_infra/api-validation/status.json").exists()
    assert (projects / "_infra/agentic-events.jsonl").exists()
    assert (projects / "_archive/legacy-evidence-scout/runs/legacy-run-1/evidence.jsonl").exists()
    assert (projects / "_archive/legacy-topics-README.md").exists()
    # Legacy roots removed (empty husks rmdir'd).
    assert not (projects / "research").exists()
    assert not (projects / "brand-projects").exists()

    # Manifest artifact rewrite + pain-gate backfill.
    manifest = json.loads((projects / "us-retirees-italy/market_research/manifest.json").read_text())
    evidence = [a["path"] for a in manifest["stages"]["evidence_collection"]["artifacts"]]
    assert evidence == [
        "market_research/pain_points/runs/r1/report.md",
        "market_research/pain_points/runs/r1/evidence.jsonl",
    ]
    problem = manifest["stages"]["problem_validation"]
    assert problem["status"] == "passed" and problem["gate_result"] == "conditional_pass"
    assert all("pain_points/" in a["path"] for a in problem["artifacts"])
    assert problem["open_gaps"]
    assert any(e["event"].startswith("gate_backfill:problem_validation") for e in manifest["events"])

    german = json.loads((projects / "german-insurance-opportunity/market_research/manifest.json").read_text())
    german_evidence = [a["path"] for a in german["stages"]["evidence_collection"]["artifacts"]]
    assert "market_research/pain_points/runs/legacy-root-20260906/evidence.jsonl" in german_evidence
    assert "market_research/sources.md" in german_evidence
    assert german["stages"]["problem_validation"]["gate_result"] == "conditional_pass"
    assert [a["path"] for a in german["stages"]["segment_selection"]["artifacts"]] == \
        ["strategy/decisions/three-ideas-decision-memo.md"]

    # No backfill where no evidence runs exist.
    self_employed = json.loads((projects / "self-employed-professionals-germany/market_research/manifest.json").read_text())
    assert self_employed["stages"]["problem_validation"]["status"] == "pending"
    assert not any(e["event"].startswith("gate_backfill") for e in self_employed["events"])

    # Cross-link rewrites: all three on-disk path shapes.
    website_manifest = json.loads((projects / "us-retirees-italy/web-site/website-manifest.json").read_text())
    assert website_manifest["brand_refs"] == ["projects/us-retirees-italy/branding/tokens/tokens.css"]
    assert website_manifest["fal_assets"][0]["provenance"] == \
        "projects/us-retirees-italy/branding/imagery/imagery-manifest.json"
    assert website_manifest["absolute_ref"] == \
        f"{repo.as_posix()}/projects/us-retirees-italy/branding/tokens/tokens.css"
    brand_manifest = json.loads((projects / "us-retirees-italy/branding/brand-manifest.json").read_text())
    assert brand_manifest["business_to_brand"] == "projects/us-retirees-italy"
    # Nested .git never content-rewritten.
    assert (projects / "us-retirees-italy/web-site/.git/HEAD").read_text() == "ref: refs/heads/main\n"

    # Controllers for all 9 projects, schema-valid, retiree project fully linked.
    for slug in mig.ALL_PROJECT_SLUGS:
        assert (projects / slug / "project-manifest.json").exists()
    controller = json.loads((projects / "us-retirees-italy/project-manifest.json").read_text())
    tracks = {link["track"]: link for link in controller["links"]}
    assert set(tracks) == {"business", "brand", "website"}
    assert tracks["brand"]["validated"] is True and tracks["website"]["validated"] is True
    # Legacy workspaces get stub READMEs; manifest workspaces keep theirs.
    assert "Legacy research workspace" in (projects / "surelius/README.md").read_text()
    assert (projects / "meal-planning-for-busy-parents/README.md").read_text() == "# Meal planning\n"

    # Originals + path-map saved for rollback.
    assert (migration_dir / "path-map.json").exists()
    assert (migration_dir / "originals/projects/us-retirees-italy/web-site/website-manifest.json").exists()

    assert mig._verify(repo) == []


def test_rollback_restores_original_tree(repo: Path) -> None:
    before = _snapshot(repo)
    plan = mig.build_plan(repo)
    migration_dir = repo / "projects/_archive/migration-20260911-000000"
    mig._execute(repo, plan, migration_dir)
    assert mig._rollback(repo, migration_dir) == 0
    after = _snapshot(repo)
    # The migration archive dir is new; everything else must be identical.
    extra = {p for p in after if p.startswith("projects/_archive/migration-")}
    assert {p: after[p] for p in after if p not in extra} == before
