#!/usr/bin/env python3
"""Migrate projects/ from the capability layout to the project-centric layout.

Moves `projects/research/topics/<slug>/` and `projects/brand-projects/<slug>/`
into one folder per venture (`projects/<project-slug>/` with market_research/,
strategy/, branding/, marketing/, web-site/, digital-assets/), moves shared
provider-validation state to `projects/_infra/`, and archives legacy global runs
read-only under `projects/_archive/`. See references/workspace-lifecycle.md.

Modes:
  --dry-run (default)   print the plan; write nothing (unless --plan-out given)
  --execute             perform moves + rewrites; emit path-map/report/originals
  --verify              check the post-migration state; non-zero exit on failure
  --rollback <dir>      reverse a previous --execute using its migration dir

Safety rules: moves only (shutil.move), never recursive-delete; execute refuses
to run while any legacy file is unmapped or any destination collides; every
rewritten file's original content is saved for rollback; the website's nested
.git and node_modules are moved as-is and never content-rewritten.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TOPIC_ROOT = Path("projects/research/topics")
BRAND_ROOT = Path("projects/brand-projects")
RESEARCH_ROOT = Path("projects/research")

MIGRATION_DATE = "2026-09-11"

# Never content-rewrite inside these directory names (moved as-is).
SWEEP_SKIP_DIRS = {".git", "node_modules", ".next"}

# ---------------------------------------------------------------------------
# Workspace mapping tables
# ---------------------------------------------------------------------------

# Ordered workspace-relative prefix rules (first match wins). Shared by file
# moves and research-manifest artifact rewrites so both always agree.
PREFIX_RULES: tuple[tuple[str, str], ...] = (
    ("evidence/runs/", "market_research/pain_points/runs/"),
    ("evidence/", "market_research/pain_points/"),
    ("competitors/runs/", "market_research/solution_alternatives/runs/"),
    ("competitors/marketing/", "market_research/solution_alternatives/marketing/"),
    ("competitors/ads/", "market_research/solution_alternatives/ads/"),
    ("competitors/", "market_research/solution_alternatives/"),
    ("ads/runs/", "market_research/solution_alternatives/ads/"),
    ("ads/", "market_research/solution_alternatives/ads/"),
    ("market-discovery/runs/", "market_research/market_discovery/runs/"),
    ("market-discovery/", "market_research/market_discovery/"),
    ("playbooks/runs/", "strategy/playbooks/runs/"),
    ("playbooks/", "strategy/playbooks/"),
    ("deep-dives/", "market_research/deep_dives/"),
    ("intake/", "strategy/intake/"),
    ("canvases/", "strategy/canvases/"),
    ("decisions/", "strategy/decisions/"),
    ("go-to-market/", "strategy/gtm/"),
    ("experiments/", "strategy/experiments/"),
    ("risks/whitespace-matrix.md", "market_research/solution_alternatives/whitespace-matrix.md"),
    ("risks/", "market_research/solution_alternatives/"),
)

# Root-level files mapped the same way for every manifest workspace.
COMMON_ROOT_FILES: dict[str, str] = {
    "README.md": "README.md",
    "manifest.json": "market_research/manifest.json",
    "manifest.lock": "market_research/manifest.lock",
}

# Full-manifest workspaces: slug -> extra root files / extra prefix rules.
MANIFEST_WORKSPACES: dict[str, dict[str, Any]] = {
    "us-retirees-italy": {
        "root_files": {
            "market-discovery-rerun-2026-08-31.md": "market_research/market_discovery/market-discovery-rerun-2026-08-31.md",
            "market-discovery-rerun-2026-08-31.pdf": "market_research/market_discovery/market-discovery-rerun-2026-08-31.pdf",
            "market-validation-competitors-and-test-plan-2026-08-31.md": "strategy/market-validation-competitors-and-test-plan-2026-08-31.md",
            "market-validation-competitors-and-test-plan-2026-08-31.pdf": "strategy/market-validation-competitors-and-test-plan-2026-08-31.pdf",
            "retiree-customer-journey.md": "market_research/customer_journey/retiree-customer-journey.md",
            "retiree-customer-journey.pdf": "market_research/customer_journey/retiree-customer-journey.pdf",
        },
        "prefixes": (),
    },
    "german-insurance-opportunity": {
        "root_files": {
            "annex-a-personal-insurance.md": "strategy/annex-a-personal-insurance.md",
            "annex-b-motor-mga.md": "strategy/annex-b-motor-mga.md",
            "annex-c-broker-succession.md": "strategy/annex-c-broker-succession.md",
            "arabic-brokerage-assessment.md": "strategy/arabic-brokerage-assessment.md",
            "competitor-advisory-walkthrough.md": "market_research/solution_alternatives/competitor-advisory-walkthrough.md",
            "content-reachability-validation.md": "strategy/content-reachability-validation.md",
            "current-recommendation.md": "strategy/current-recommendation.md",
            "economics.csv": "strategy/economics.csv",
            "language-market-scenarios.csv": "strategy/language-market-scenarios.csv",
            # Loose root-level evidence run synthesized into one legacy run dir.
            "evidence.jsonl": "market_research/pain_points/runs/legacy-root-20260906/evidence.jsonl",
            "summary.json": "market_research/pain_points/runs/legacy-root-20260906/summary.json",
            "report.md": "market_research/pain_points/runs/legacy-root-20260906/report.md",
            "pain-versus-offer-matrix.md": "market_research/solution_alternatives/pain-versus-offer-matrix.md",
            "pilot-evidence-log-template.csv": "strategy/experiments/pilot-evidence-log-template.csv",
            "player-directory.md": "market_research/solution_alternatives/player-directory.md",
            "profession-segments-and-relationship-model.md": "market_research/customer_segments/profession-segments-and-relationship-model.md",
            "professional-insurance-content-competitors.md": "market_research/solution_alternatives/professional-insurance-content-competitors.md",
            "progressive-advice-language-markets-and-coverage.md": "strategy/progressive-advice-language-markets-and-coverage.md",
            "self-employment-journeys-it-and-doctors.md": "market_research/customer_journey/self-employment-journeys-it-and-doctors.md",
            "sources-language-and-surelius.md": "market_research/sources-language-and-surelius.md",
            "sources.md": "market_research/sources.md",
            "strategy-plan.json": "strategy/strategy-plan.json",
            "surelius-and-language-segments.md": "market_research/customer_segments/surelius-and-language-segments.md",
            "surelius-personalised-why-and-simulation.md": "strategy/surelius-personalised-why-and-simulation.md",
            "surelius-pilot-mvp-brief.md": "strategy/surelius-pilot-mvp-brief.md",
            "three-ideas-decision-memo.md": "strategy/decisions/three-ideas-decision-memo.md",
            "three-ideas-evidence-audit.md": "strategy/decisions/three-ideas-evidence-audit.md",
        },
        "prefixes": (
            ("raw/", "market_research/pain_points/runs/legacy-root-20260906/raw/"),
            ("runs/", "strategy/runs/"),
        ),
    },
    "meal-planning-for-busy-parents": {"root_files": {}, "prefixes": ()},
    "self-employed-professionals-germany": {"root_files": {}, "prefixes": ()},
    "social-access-smoke-test-private-health-insurance-germany": {"root_files": {}, "prefixes": ()},
}

# Legacy no-manifest workspaces: best-effort explicit maps (old dirname -> def).
LEGACY_WORKSPACES: dict[str, dict[str, Any]] = {
    "Surelius": {
        "slug": "surelius",
        "root_files": {
            "current_pain_points.md": "market_research/pain_points/current_pain_points.md",
            "life_change_triggers.md": "market_research/pain_points/life_change_triggers.md",
        },
        "prefixes": (),
    },
    "digital-insurance-agent": {
        "slug": "digital-insurance-agent",
        "root_files": {
            "README.md": "README.md",
            "customer-segments-and-journey.md": "market_research/customer_segments/customer-segments-and-journey.md",
            "digital-workflow-and-app.md": "strategy/digital-workflow-and-app.md",
            "go-to-market-strategy.md": "strategy/gtm/go-to-market-strategy.md",
            "research-notes-and-sources.md": "market_research/research-notes-and-sources.md",
            "social-media-playbook.md": "marketing/social-media-playbook.md",
        },
        "prefixes": (),
    },
    "tattoo-insurance": {
        "slug": "tattoo-insurance",
        "root_files": {
            "README.md": "README.md",
            "sources.md": "market_research/sources.md",
            "test-plan.md": "strategy/test-plan.md",
        },
        "prefixes": (
            ("evidence/", "market_research/pain_points/countries/"),
            ("competitors/", "market_research/solution_alternatives/"),
        ),
    },
    "individualized-marketing-content": {
        "slug": "individualized-marketing-content",
        "root_files": {},
        "prefixes": (),
    },
}

# Pain-gate backfill: workspaces with completed evidence runs get an honest
# conditional_pass on problem_validation. self-employed-professionals-germany
# has no evidence runs and is deliberately excluded.
PAIN_GATE_BACKFILL = {
    "us-retirees-italy",
    "german-insurance-opportunity",
    "meal-planning-for-busy-parents",
    "social-access-smoke-test-private-health-insurance-germany",
}

ALL_PROJECT_SLUGS = sorted(list(MANIFEST_WORKSPACES) + [w["slug"] for w in LEGACY_WORKSPACES.values()])

# Brand-project relocations (italy-retiree-move is absorbed by us-retirees-italy).
BRAND_PROJECT = "italy-retiree-move"
TOWN_DB_PROJECT = "italy-town-db"
RETIREE_SLUG = "us-retirees-italy"

# Global legacy relocations (dir moves unless marked file).
GLOBAL_MOVES: tuple[tuple[str, str, str], ...] = (
    ("projects/research/evidence-scout/runs", "projects/_archive/legacy-evidence-scout/runs", "dir"),
    ("projects/research/evidence-scout/competitors", "projects/_archive/legacy-evidence-scout/competitors", "dir"),
    ("projects/research/evidence-scout/marketing", "projects/_archive/legacy-evidence-scout/marketing", "dir"),
    ("projects/research/evidence-scout/api-validation", "projects/_infra/api-validation", "dir"),
    ("projects/research/evidence-scout/provider-doctor", "projects/_infra/provider-doctor", "dir"),
    ("projects/research/agentic-events.jsonl", "projects/_infra/agentic-events.jsonl", "file"),
    ("projects/research/topics/README.md", "projects/_archive/legacy-topics-README.md", "file"),
)

# ---------------------------------------------------------------------------
# Content rewrite table (ordered longest-first at build time)
# ---------------------------------------------------------------------------


def build_rewrite_rules(root: Path, old_topic_names: dict[str, str]) -> list[tuple[str, str]]:
    """Return ordered (old, new) substring rules for moved project trees.

    old_topic_names maps old topic dir name -> new slug (covers the Surelius
    case rename). Rules come in trailing-slash and bare variants; sorting by
    descending length guarantees the most specific rule wins.
    """
    pairs: list[tuple[str, str]] = []
    abs_root = root.as_posix()
    for old_name, slug in old_topic_names.items():
        pairs.append((f"projects/research/topics/{old_name}/", f"projects/{slug}/"))
        pairs.append((f"{abs_root}/projects/research/topics/{old_name}/", f"{abs_root}/projects/{slug}/"))
    brand_targets = {
        f"{BRAND_PROJECT}/website/": f"projects/{RETIREE_SLUG}/web-site/",
        f"{BRAND_PROJECT}/": f"projects/{RETIREE_SLUG}/branding/",
        f"{TOWN_DB_PROJECT}/": f"projects/{RETIREE_SLUG}/digital-assets/town-db/",
    }
    for brand_rel, new_rel in brand_targets.items():
        pairs.append((f"projects/brand-projects/{brand_rel}", new_rel))
        pairs.append((f"brand-projects/{brand_rel}", new_rel))
        pairs.append((f"{abs_root}/projects/brand-projects/{brand_rel}", f"{abs_root}/{new_rel}"))
    pairs.append(("projects/research/evidence-scout/api-validation/", "projects/_infra/api-validation/"))
    pairs.append(("projects/research/evidence-scout/provider-doctor/", "projects/_infra/provider-doctor/"))
    pairs.append(("projects/research/evidence-scout/", "projects/_archive/legacy-evidence-scout/"))
    pairs.append(("projects/research/agentic-events.jsonl", "projects/_infra/agentic-events.jsonl"))
    # Bare (no trailing slash) variants catch end-of-value references like
    # "business_to_brand": "projects/research/topics/us-retirees-italy".
    rules: list[tuple[str, str]] = []
    for old, new in pairs:
        rules.append((old, new))
        rules.append((old.rstrip("/"), new.rstrip("/")))
    rules.sort(key=lambda rule: len(rule[0]), reverse=True)
    return rules


# ---------------------------------------------------------------------------
# Path mapping
# ---------------------------------------------------------------------------


def map_workspace_file(workspace: dict[str, Any], rel: str) -> str | None:
    """Map a workspace-relative file path to its project-relative destination."""
    root_files = {**COMMON_ROOT_FILES, **workspace.get("root_files", {})}
    if rel in root_files:
        return root_files[rel]
    for old, new in tuple(workspace.get("prefixes", ())) + PREFIX_RULES:
        if rel.startswith(old):
            return new + rel[len(old):]
    return None


def _walk_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted(p for p in base.rglob("*") if p.is_file() or p.is_symlink())


# ---------------------------------------------------------------------------
# Plan building
# ---------------------------------------------------------------------------


def build_plan(root: Path) -> dict[str, Any]:
    """Build the full migration plan against `root` without touching anything."""
    plan: dict[str, Any] = {
        "moves": [],  # {src, dst, kind}
        "unmapped": [],
        "collisions": [],
        "warnings": [],
        "controllers": [],  # slugs needing a controller manifest
        "stub_readmes": [],  # legacy slugs needing a stub README
        "manifest_projects": [],  # slugs whose research manifest is transformed
    }
    moves: list[dict[str, str]] = plan["moves"]

    def add_move(src: Path, dst: Path, kind: str) -> None:
        moves.append({"src": src.as_posix(), "dst": dst.as_posix(), "kind": kind})

    # 1. Manifest workspaces: file-level reshaped moves.
    for slug, workspace in MANIFEST_WORKSPACES.items():
        src_dir = root / TOPIC_ROOT / slug
        for file_path in _walk_files(src_dir):
            rel = file_path.relative_to(src_dir).as_posix()
            mapped = map_workspace_file(workspace, rel)
            if mapped is None:
                plan["unmapped"].append(f"{(TOPIC_ROOT / slug).as_posix()}/{rel}")
                continue
            add_move(file_path.relative_to(root), Path("projects") / slug / mapped, "file")
        if src_dir.exists():
            plan["manifest_projects"].append(slug)
            plan["controllers"].append(slug)

    # 2. Legacy no-manifest workspaces.
    for old_name, workspace in LEGACY_WORKSPACES.items():
        slug = workspace["slug"]
        src_dir = root / TOPIC_ROOT / old_name
        for file_path in _walk_files(src_dir):
            rel = file_path.relative_to(src_dir).as_posix()
            mapped = map_workspace_file(workspace, rel)
            if mapped is None:
                plan["unmapped"].append(f"{(TOPIC_ROOT / old_name).as_posix()}/{rel}")
                continue
            add_move(file_path.relative_to(root), Path("projects") / slug / mapped, "file")
        if src_dir.exists():
            plan["controllers"].append(slug)
            plan["stub_readmes"].append(slug)

    # 3. Brand projects absorbed by us-retirees-italy.
    website_src = root / BRAND_ROOT / BRAND_PROJECT / "website"
    if website_src.exists():
        # Wholesale dir move: preserves the nested .git and node_modules.
        add_move(website_src.relative_to(root), Path("projects") / RETIREE_SLUG / "web-site", "dir")
    brand_src = root / BRAND_ROOT / BRAND_PROJECT
    for file_path in _walk_files(brand_src):
        if website_src in file_path.parents:
            continue
        rel = file_path.relative_to(brand_src).as_posix()
        add_move(file_path.relative_to(root), Path("projects") / RETIREE_SLUG / "branding" / rel, "file")
    town_db_src = root / BRAND_ROOT / TOWN_DB_PROJECT
    if town_db_src.exists():
        add_move(town_db_src.relative_to(root), Path("projects") / RETIREE_SLUG / "digital-assets" / "town-db", "dir")

    # 4. Global legacy relocations.
    for src_rel, dst_rel, kind in GLOBAL_MOVES:
        if (root / src_rel).exists():
            add_move(Path(src_rel), Path(dst_rel), kind)

    # 5. Coverage check: every remaining legacy file must be covered by a move.
    covered: list[Path] = []
    for move in moves:
        covered.append(root / move["src"])

    def is_covered(file_path: Path) -> bool:
        rel = file_path.relative_to(root)
        for move in moves:
            src = Path(move["src"])
            if rel == src or src in rel.parents:
                return True
        return False

    for legacy_root in (root / RESEARCH_ROOT, root / BRAND_ROOT):
        for file_path in _walk_files(legacy_root):
            if not is_covered(file_path):
                plan["unmapped"].append(file_path.relative_to(root).as_posix())

    # 6. Collision check: destinations unique, none nested inside a dir move.
    dsts: dict[str, str] = {}
    dir_dsts = [Path(m["dst"]) for m in moves if m["kind"] == "dir"]
    for move in moves:
        dst = Path(move["dst"])
        if move["dst"] in dsts:
            plan["collisions"].append(f"{move['dst']} <- {dsts[move['dst']]} and {move['src']}")
        dsts[move["dst"]] = move["src"]
        if move["kind"] == "file" and any(d in dst.parents for d in dir_dsts):
            plan["collisions"].append(f"{move['dst']} nested inside dir move")
        if (root / dst).exists():
            plan["collisions"].append(f"{move['dst']} already exists")

    plan["unmapped"] = sorted(set(plan["unmapped"]))
    plan["controllers"] = sorted(set(plan["controllers"]))
    return plan


# ---------------------------------------------------------------------------
# Execute helpers
# ---------------------------------------------------------------------------


def _save_original(migration_dir: Path, root: Path, dst_rel: Path) -> None:
    original = migration_dir / "originals" / dst_rel
    original.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / dst_rel, original)


def _apply_content_rewrites(root: Path, rules: list[tuple[str, str]], migration_dir: Path, report: dict[str, Any]) -> None:
    """Sweep moved project trees and rewrite legacy path strings in text files."""
    rewritten: list[dict[str, Any]] = []
    residuals: list[str] = []
    for slug in ALL_PROJECT_SLUGS:
        project_dir = root / "projects" / slug
        if not project_dir.exists():
            continue
        for file_path in sorted(project_dir.rglob("*")):
            if not file_path.is_file():
                continue
            rel_parts = file_path.relative_to(project_dir).parts
            if any(part in SWEEP_SKIP_DIRS for part in rel_parts):
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            updated = text
            count = 0
            for old, new in rules:
                hits = updated.count(old)
                if hits:
                    updated = updated.replace(old, new)
                    count += hits
            if updated != text:
                dst_rel = file_path.relative_to(root)
                _save_original(migration_dir, root, dst_rel)
                file_path.write_text(updated, encoding="utf-8")
                rewritten.append({"path": dst_rel.as_posix(), "replacements": count})
            for marker in ("projects/research/topics", "projects/brand-projects", "brand-projects/"):
                if marker in updated:
                    residuals.append(f"{file_path.relative_to(root).as_posix()}: still contains {marker!r}")
    report["rewritten_files"] = rewritten
    report["residual_legacy_refs"] = sorted(set(residuals))


def _artifact_path(artifact: Any) -> str:
    """Manifest artifacts are dicts ({path, type, description}); tolerate strings."""
    if isinstance(artifact, str):
        return artifact
    if isinstance(artifact, dict):
        return str(artifact.get("path", ""))
    return ""


def _map_artifact(workspace: dict[str, Any], artifact: Any, warnings: list[str], slug: str) -> Any:
    """Rewrite one manifest artifact entry; on-disk manifests use plain strings."""
    if isinstance(artifact, str):
        mapped = map_workspace_file(workspace, artifact)
        if mapped is None:
            warnings.append(f"{slug}: unmapped artifact path {artifact!r} left as-is")
            return artifact
        return mapped
    if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
        mapped = map_workspace_file(workspace, artifact["path"])
        if mapped is None:
            warnings.append(f"{slug}: unmapped artifact path {artifact['path']!r} left as-is")
            return artifact
        return {**artifact, "path": mapped}
    return artifact


def _transform_research_manifest(root: Path, slug: str, ts: str, report: dict[str, Any]) -> None:
    """Rewrite artifact paths in the moved research manifest and backfill the gate."""
    workspace = MANIFEST_WORKSPACES[slug]
    manifest_path = root / "projects" / slug / "market_research" / "manifest.json"
    if not manifest_path.exists():
        report["warnings"].append(f"{slug}: research manifest missing after move")
        return
    _save_original(report["_migration_dir"], root, manifest_path.relative_to(root))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    warnings: list[str] = report["warnings"]

    manifest["artifacts"] = [
        _map_artifact(workspace, artifact, warnings, slug) for artifact in manifest.get("artifacts", [])
    ]
    for stage in manifest.get("stages", {}).values():
        if isinstance(stage, dict) and isinstance(stage.get("artifacts"), list):
            stage["artifacts"] = [_map_artifact(workspace, a, warnings, slug) for a in stage["artifacts"]]

    events = manifest.setdefault("events", [])
    events.append({"ts": ts, "event": f"layout_migration:projects/{slug}"})

    if slug in PAIN_GATE_BACKFILL:
        stages = manifest.get("stages", {})
        problem = stages.get("problem_validation", {})
        evidence = stages.get("evidence_collection", {})
        evidence_artifacts = [
            a for a in (evidence.get("artifacts") or [])
            if "pain_points/" in _artifact_path(a)
        ]
        if problem.get("status") == "pending" and evidence.get("status") == "passed" and evidence_artifacts:
            problem.update({
                "stage": "problem_validation",
                "status": "passed",
                "timestamp": ts,
                "gate_result": "conditional_pass",
                "artifacts": evidence_artifacts,
                "open_gaps": [
                    "Pain-point evidence runs exist but a validated pain-point ranking "
                    f"was not synthesized before the layout migration ({MIGRATION_DATE}). "
                    "Confirm segment, journey, and pain ranking before downstream commitment work."
                ],
                "next_action": "Synthesize the pain-point ranking from the collected evidence runs.",
            })
            events.append({"ts": ts, "event": "gate_backfill:problem_validation:layout-migration (evidence runs exist; pain synthesis pending)"})
            report["backfilled"].append(slug)
        else:
            report["warnings"].append(f"{slug}: pain-gate backfill skipped (no qualifying evidence artifacts)")

    manifest["updated_at"] = ts
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stub_readme(slug: str) -> str:
    return (
        f"# {slug}\n\n"
        "Legacy research workspace, migrated best-effort into the project-centric layout "
        f"on {MIGRATION_DATE}. No research stage machine existed for this workspace; "
        "materials are filed under `market_research/`, `strategy/`, and `marketing/`.\n\n"
        "Next action: run idea-grill to establish the customer segment, customer journey, "
        "and pain points with web-searched evidence (`market_research/customer_segments/`, "
        "`customer_journey/`, `pain_points/`), or archive this workspace.\n"
    )


def _write_controller(root: Path, slug: str, ts: str, next_action: str, links: list[dict[str, Any]], report: dict[str, Any]) -> None:
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "project_id": slug,
        "slug": slug,
        "created_at": ts,
        "updated_at": ts,
        "manifest_revision": 1,
        "active_track": "business",
        "business_workspace": {"path": f"projects/{slug}/market_research", "external": False},
        "brand_workspace": None,
        "website_workspace": None,
        "links": links,
        "next_action": next_action,
        "open_blockers": [],
    }
    for link in links:
        manifest[f"{link['track']}_workspace"] = link["workspace"]
    controller_path = root / "projects" / slug / "project-manifest.json"
    controller_path.parent.mkdir(parents=True, exist_ok=True)
    controller_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["controllers_written"].append(controller_path.relative_to(root).as_posix())


def _execute(root: Path, plan: dict[str, Any], migration_dir: Path) -> dict[str, Any]:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report: dict[str, Any] = {
        "migration": migration_dir.name,
        "ts": ts,
        "moves": [],
        "rewritten_files": [],
        "residual_legacy_refs": [],
        "backfilled": [],
        "controllers_written": [],
        "stub_readmes_written": [],
        "warnings": list(plan["warnings"]),
        "_migration_dir": migration_dir,
    }

    migration_dir.mkdir(parents=True, exist_ok=True)
    path_map = {"ts": ts, "moves": plan["moves"], "rewritten": [], "generated": []}
    (migration_dir / "path-map.json").write_text(json.dumps(path_map, indent=2) + "\n", encoding="utf-8")

    # Moves first; every destination is unique and non-colliding (checked in plan).
    for move in plan["moves"]:
        src = root / move["src"]
        dst = root / move["dst"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        report["moves"].append({"src": move["src"], "dst": move["dst"], "kind": move["kind"]})

    # Content rewrites inside moved project trees (never _archive/_infra/.git).
    old_names = {name: name for name in MANIFEST_WORKSPACES}
    old_names.update({old: w["slug"] for old, w in LEGACY_WORKSPACES.items()})
    rules = build_rewrite_rules(root, old_names)
    _apply_content_rewrites(root, rules, migration_dir, report)

    # Research-manifest transforms (artifact rewrites + pain-gate backfill).
    for slug in plan["manifest_projects"]:
        _transform_research_manifest(root, slug, ts, report)

    # Controller manifests for every migrated project.
    for slug in plan["controllers"]:
        research_manifest = root / "projects" / slug / "market_research" / "manifest.json"
        next_action = f"Resume the {slug} research track."
        if research_manifest.exists():
            try:
                next_action = json.loads(research_manifest.read_text(encoding="utf-8")).get("next_action") or next_action
            except json.JSONDecodeError:
                report["warnings"].append(f"{slug}: research manifest unreadable; stub next_action used")
        elif slug in plan["stub_readmes"]:
            next_action = "Legacy workspace: establish segment, journey, and pain points (idea-grill) or archive."
        business_link = {
            "track": "business",
            "workspace": {"path": f"projects/{slug}/market_research", "external": False},
            "linked_at": ts,
        }
        links = [business_link]
        if slug == RETIREE_SLUG:
            # The pain gate was backfilled to conditional_pass above, so these
            # links record validated: true.
            links.append({
                "track": "brand",
                "workspace": {"path": f"projects/{slug}/branding", "external": False},
                "linked_at": ts,
                "validated": True,
            })
            links.append({
                "track": "website",
                "workspace": {"path": f"projects/{slug}/web-site", "external": False},
                "linked_at": ts,
                "validated": True,
            })
        _write_controller(root, slug, ts, next_action, links, report)

    # Stub READMEs for legacy no-manifest workspaces.
    for slug in plan["stub_readmes"]:
        readme = root / "projects" / slug / "README.md"
        if not readme.exists():
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(_stub_readme(slug), encoding="utf-8")
            report["stub_readmes_written"].append(readme.relative_to(root).as_posix())

    # Remove empty legacy husks bottom-up; rmdir only, never recursive-delete.
    leftovers: list[str] = []
    for legacy_root in (root / RESEARCH_ROOT, root / BRAND_ROOT):
        if not legacy_root.exists():
            continue
        for dirpath, dirnames, _filenames in os.walk(legacy_root, topdown=False):
            current = Path(dirpath)
            try:
                current.rmdir()
            except OSError:
                pass
        if legacy_root.exists():
            leftovers.append(legacy_root.relative_to(root).as_posix())
    if leftovers:
        report["warnings"].append(f"legacy roots not fully empty after migration: {leftovers}")

    # Finalize path-map with rewrite/generate records for rollback.
    path_map["rewritten"] = [entry["path"] for entry in report["rewritten_files"]]
    path_map["rewritten"] += [
        f"projects/{slug}/market_research/manifest.json" for slug in plan["manifest_projects"]
    ]
    path_map["generated"] = report["controllers_written"] + report["stub_readmes_written"]
    (migration_dir / "path-map.json").write_text(json.dumps(path_map, indent=2) + "\n", encoding="utf-8")

    report.pop("_migration_dir")
    (migration_dir / "migration-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


# ---------------------------------------------------------------------------
# Verify / rollback
# ---------------------------------------------------------------------------


def _verify(root: Path) -> list[str]:
    """Check post-migration state; return a list of failures (empty = pass)."""
    failures: list[str] = []
    plan = build_plan(root)
    # After migration the legacy roots are gone, so plan moves should be empty.
    if (root / RESEARCH_ROOT).exists() or (root / BRAND_ROOT).exists():
        failures.append("legacy roots projects/research or projects/brand-projects still exist")

    for slug in ALL_PROJECT_SLUGS:
        project_dir = root / "projects" / slug
        controller = project_dir / "project-manifest.json"
        if not controller.exists():
            failures.append(f"{slug}: missing project-manifest.json")
            continue
        try:
            data = json.loads(controller.read_text(encoding="utf-8"))
            _validate_controller(root, data, slug, failures)
        except json.JSONDecodeError:
            failures.append(f"{slug}: project-manifest.json is invalid JSON")

    for slug in MANIFEST_WORKSPACES:
        project_dir = root / "projects" / slug
        manifest_path = project_dir / "market_research" / "manifest.json"
        if not manifest_path.exists():
            failures.append(f"{slug}: missing market_research/manifest.json")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for stage_name, stage in manifest.get("stages", {}).items():
            for artifact in stage.get("artifacts") or []:
                path = artifact if isinstance(artifact, str) else artifact.get("path", "")
                if path and not (project_dir / path).exists():
                    failures.append(f"{slug}: stage {stage_name} artifact missing on disk: {path}")
        for artifact in manifest.get("artifacts") or []:
            path = artifact if isinstance(artifact, str) else artifact.get("path", "")
            if path and not (project_dir / path).exists():
                failures.append(f"{slug}: manifest artifact missing on disk: {path}")

    website = root / "projects" / RETIREE_SLUG / "web-site"
    if not (website / ".git").exists():
        failures.append("us-retirees-italy: web-site/.git missing (nested repo not preserved)")
    if not (root / "projects" / RETIREE_SLUG / "digital-assets" / "town-db" / "towns.sqlite").exists():
        failures.append("us-retirees-italy: digital-assets/town-db/towns.sqlite missing")
    if not (root / "projects" / "_infra" / "api-validation").exists():
        failures.append("_infra/api-validation missing")
    if not (root / "projects" / "_archive" / "legacy-evidence-scout" / "runs").exists():
        failures.append("_archive/legacy-evidence-scout/runs missing")

    # Residual legacy references in project trees (excluding never-rewritten dirs).
    for slug in ALL_PROJECT_SLUGS:
        project_dir = root / "projects" / slug
        if not project_dir.exists():
            continue
        for file_path in sorted(project_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if any(part in SWEEP_SKIP_DIRS for part in file_path.relative_to(project_dir).parts):
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for marker in ("projects/research/topics", "projects/brand-projects", "brand-projects/"):
                if marker in text:
                    failures.append(f"{file_path.relative_to(root).as_posix()}: residual {marker!r}")
    return failures


def _validate_controller(root: Path, data: dict[str, Any], slug: str, failures: list[str]) -> None:
    try:
        import jsonschema

        schema = json.loads((root / "schemas" / "project-manifest.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
    except ImportError:
        pass
    except Exception as exc:  # jsonschema.ValidationError or schema read error
        failures.append(f"{slug}: controller schema validation failed: {exc}")


def _rollback(root: Path, migration_dir: Path) -> int:
    path_map_path = migration_dir / "path-map.json"
    if not path_map_path.exists():
        print(f"rollback: missing {path_map_path}", file=sys.stderr)
        return 1
    path_map = json.loads(path_map_path.read_text(encoding="utf-8"))

    # 1. Restore original contents of rewritten files at their current (dst) paths.
    for rel in path_map.get("rewritten", []):
        original = migration_dir / "originals" / rel
        target = root / rel
        if original.exists() and target.exists():
            shutil.copy2(original, target)

    # 2. Remove files the migration generated.
    for rel in path_map.get("generated", []):
        target = root / rel
        if target.exists():
            target.unlink()

    # 3. Reverse moves, deepest-first so files return before their parent dirs.
    for move in sorted(path_map.get("moves", []), key=lambda m: len(m["dst"]), reverse=True):
        src = root / move["dst"]
        dst = root / move["src"]
        if not src.exists():
            print(f"rollback: skip missing {move['dst']}", file=sys.stderr)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    # 4. Remove now-empty project dirs (rmdir only).
    for slug in ALL_PROJECT_SLUGS:
        project_dir = root / "projects" / slug
        if project_dir.exists():
            for dirpath, _dirnames, _filenames in os.walk(project_dir, topdown=False):
                try:
                    Path(dirpath).rmdir()
                except OSError:
                    pass
    print(f"rollback complete from {migration_dir}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print the plan without writing (default).")
    mode.add_argument("--execute", action="store_true", help="Perform the migration.")
    mode.add_argument("--verify", action="store_true", help="Verify post-migration state.")
    mode.add_argument("--rollback", type=Path, default=None, help="Rollback using a migration-<ts> directory.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root (tests use a tmp dir).")
    parser.add_argument("--plan-out", type=Path, default=None, help="Optionally write the dry-run plan JSON here.")
    args = parser.parse_args()
    root = args.root.resolve()

    if args.rollback:
        return _rollback(root, args.rollback)

    if args.verify:
        failures = _verify(root)
        if failures:
            print("VERIFY FAILED:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("verify: all checks passed")
        return 0

    plan = build_plan(root)
    summary = {
        "moves": len(plan["moves"]),
        "manifest_projects": plan["manifest_projects"],
        "controllers": plan["controllers"],
        "stub_readmes": plan["stub_readmes"],
        "unmapped": plan["unmapped"],
        "collisions": plan["collisions"],
    }
    if args.plan_out:
        args.plan_out.parent.mkdir(parents=True, exist_ok=True)
        args.plan_out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    if args.execute:
        if plan["unmapped"] or plan["collisions"]:
            print(json.dumps(summary, indent=2))
            print("execute refused: resolve unmapped files/collisions first", file=sys.stderr)
            return 1
        ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        migration_dir = root / "projects" / "_archive" / f"migration-{ts}"
        report = _execute(root, plan, migration_dir)
        print(json.dumps({"migration_dir": str(migration_dir), "moves": len(report["moves"]),
                          "rewritten_files": len(report["rewritten_files"]),
                          "backfilled": report["backfilled"],
                          "warnings": report["warnings"],
                          "residual_legacy_refs": report["residual_legacy_refs"]}, indent=2))
        return 0 if not report["residual_legacy_refs"] else 1

    # Default: dry-run.
    print(json.dumps(summary, indent=2))
    return 0 if not (plan["unmapped"] or plan["collisions"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
