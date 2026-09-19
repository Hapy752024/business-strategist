#!/usr/bin/env python3
"""Spec-driven migration of a legacy project into the case/subproject layout.

This is deliberately conservative: it moves only paths named by the project
spec, archives legacy controllers/manifests, creates review-required cases, and
keeps an external byte-for-byte rollback copy.  It does not synthesize current
business conclusions.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import case_workspace as cases
from scripts import layout_migration as migration
from scripts import subprojects

SPECS = {
    "tattoo-insurance": {
        "title": "Tattoo insurance",
        "cases": [
            ("direct-consumer-cover", "Direct consumer cover"),
            ("studio-embedded-protection", "Studio-embedded protection"),
        ],
        "shared": ["market_research"],
        "history": ["strategy"],
        "reviews": [],
        "assets": [],
    },
    "credit-cards-enhanced-payments": {
        "title": "Credit cards and enhanced payments",
        "cases": [
            ("card-funded-bill-payment", "Card-funded bill payment"),
            ("rewards-assistance", "Rewards assistance"),
            ("contractor-cash-workflow", "Contractor cash workflow"),
        ],
        "shared": ["market_research"], "history": ["strategy", "reviews"], "reviews": [], "assets": [],
    },
    "german-insurance-opportunity": {
        "title": "German insurance opportunity",
        "cases": [
            ("personal-decision-service", "Personal insurance decision service"),
            ("professional-transition-brokerage", "Professional transition brokerage"),
            ("cyber-readiness-brokerage", "Cyber readiness brokerage"),
            ("motor-mga", "Discount motor MGA"),
            ("broker-succession", "Broker succession"),
        ],
        "shared": ["market_research"], "history": ["strategy", "marketing"], "reviews": [], "assets": [],
    },
    "us-retirees-italy": {
        "title": "English-speaking retirees in Italy",
        "cases": [
            ("relocation-advice", "Relocation advice"),
            ("resident-support", "Resident support"),
            ("village-housing-community", "Village housing community"),
        ],
        "shared": ["market_research"], "history": ["strategy"], "reviews": [],
        "assets": ["branding", "digital-assets", "web-site"],
    },
}


def digest(root: Path, *, allow_symlinks: bool = False) -> dict[str, str]:
    if not allow_symlinks:
        return migration.digest_tree(root)
    import hashlib
    result = {}
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        if path.is_symlink():
            result[rel] = "symlink:" + os.readlink(path)
        elif path.is_file():
            result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def sha_map(value: dict[str, str]) -> str:
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def spec_for(slug: str) -> dict:
    if slug not in SPECS:
        raise ValueError(f"no reviewed migration spec for {slug}")
    return SPECS[slug]


def write_state(slug: str, root: Path, entry: dict, state: str) -> None:
    entry["state"] = state
    entry["phase_files"] = digest(root, allow_symlinks=slug == "us-retirees-italy")
    migration.write_journal(slug, entry, root=root.parents[1])


def archive_file(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if source.is_symlink() or (source.exists() and not source.is_file()):
        raise ValueError(f"unsupported source path: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError(f"migration destination already exists: {destination}")
    shutil.copy2(source, destination)


def move_dir(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"unsupported source directory: {source}")
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"migration destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)

def move_contents(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for child in list(source.iterdir()):
        target = destination / child.name
        if target.exists() or target.is_symlink():
            raise ValueError(f"migration destination already exists: {target}")
        os.replace(child, target)
    source.rmdir()


def transition(project: Path, slug: str, spec: dict, entry: dict, repo_root: Path) -> None:
    analysis = project / "business-analysis"
    if analysis.exists():
        raise ValueError("business-analysis already exists; explicit recovery required")
    old_manifest = project / "project-manifest.json"
    old_readme = project / "README.md"
    if not old_manifest.is_file() or not old_readme.is_file():
        raise ValueError("legacy project controller is incomplete")

    with migration.permit(slug):
        cases.initialize(analysis, spec["title"], project_id=slug)
        for case_id, title in spec["cases"]:
            cases.add_case(analysis, case_id, title,
                           open_blockers=["Legacy findings require case-specific review; no inherited passes."],
                           next_action="Review source applicability and write current segment, journey, pain, feasibility and business case.")
        write_state(slug, project, entry, "cases_initialized")

        snapshot = analysis / "history" / "snapshots" / entry["migration_id"]
        archive_file(old_readme, snapshot / "README.md")
        archive_file(old_manifest, snapshot / "project-manifest.json")
        for relative in spec["shared"]:
            legacy = project / relative
            if legacy.is_dir():
                legacy_manifest = legacy / "manifest.json"
                archive_file(legacy_manifest, snapshot / relative / "manifest.json")
                archive_file(legacy / "manifest.lock", snapshot / relative / "manifest.lock")
                legacy_manifest.unlink(missing_ok=True)
                (legacy / "manifest.lock").unlink(missing_ok=True)
                move_dir(legacy, analysis / relative)
        write_state(slug, project, entry, "shared_research_moved")

        history = analysis / "history" / "legacy"
        for relative in spec["history"]:
            move_dir(project / relative, history / relative)
        for relative in spec["reviews"]:
            move_dir(project / relative, analysis / "history" / "reviews" / relative)
        write_state(slug, project, entry, "legacy_archived")

        for relative in spec["assets"]:
            if relative == "web-site":
                move_dir(project / relative, project / "digital-assets" / "website")
            elif relative == "digital-assets":
                move_contents(project / relative, project / "digital-assets" / "others")
            else:
                if relative != "branding":
                    move_dir(project / relative, project / relative)
        old_readme.unlink()
        old_manifest.unlink()
        write_state(slug, project, entry, "legacy_controller_retired")

        subprojects.initialize(project, spec["title"])
        write_state(slug, project, entry, "replacement_installed")


def verify(project: Path, slug: str, spec: dict, entry: dict, repo_root: Path) -> None:
    baseline = entry["baseline_files"]
    analysis = project / "business-analysis"
    for name in ("README.md", "project-manifest.json"):
        archived = analysis / "history/snapshots" / entry["migration_id"] / name
        if not archived.is_file() or migration.digest_tree(archived.parent).get(name) != baseline[name]:
            raise ValueError(f"legacy {name} snapshot mismatch")
    for relative in spec["shared"]:
        source = analysis / relative
        expected = {k.removeprefix(relative + "/"): v for k, v in baseline.items()
                    if k.startswith(relative + "/") and k not in {relative + "/manifest.json", relative + "/manifest.lock"}}
        if migration.digest_tree(source) != expected:
            raise ValueError(f"shared research changed: {relative}")
        snapshot = analysis / "history/snapshots" / entry["migration_id"] / relative
        for manifest in ("manifest.json", "manifest.lock"):
            original = baseline.get(f"{relative}/{manifest}")
            if original is not None and migration.digest_tree(snapshot).get(manifest) != original:
                raise ValueError(f"legacy research manifest snapshot mismatch: {relative}/{manifest}")
        if (source / "manifest.json").exists() or (source / "manifest.lock").exists():
            raise ValueError("legacy aggregate research manifest remains active")
    for relative in spec["assets"]:
        source = project / relative
        destination = project / ("digital-assets/website" if relative == "web-site" else ("digital-assets/others" if relative == "digital-assets" else relative))
        if relative == "branding":
            destination = source
        expected = {k.removeprefix(relative + "/"): v for k, v in baseline.items() if k.startswith(relative + "/")}
        if relative == "digital-assets":
            actual = digest(destination, allow_symlinks=True)
            actual = {k.removeprefix("digital-assets/others/"): v for k, v in actual.items() if k.startswith("digital-assets/others/")}
        else:
            actual = digest(destination, allow_symlinks=True)
        if actual != expected:
            raise ValueError(f"asset tree changed: {relative}")
    root = cases.read_project(project)
    if root.get("controller_kind") != "umbrella":
        raise ValueError("migrated root is not an umbrella controller")
    if (analysis / "market_research/manifest.json").exists() or (analysis / "market_research/manifest.lock").exists():
        raise ValueError("legacy aggregate research authority remains active")
    for case_id, _title in spec["cases"]:
        case = cases.case_manifest(analysis, case_id)
        if case.get("stages") != {} or case.get("selection") is not None or not case.get("open_blockers"):
            raise ValueError(f"case authority was inherited: {case_id}")


def rollback(slug: str, *, repo_root: Path = ROOT) -> None:
    repo_root = Path(repo_root).absolute()
    project = repo_root / "projects" / slug
    with migration.lock(slug, root=repo_root, exclusive=True):
        entry = migration.journal(slug, root=repo_root)
        if not entry or entry["state"] in {"verified", "rolled_back"}:
            raise ValueError("no incomplete generic migration to roll back")
        project = repo_root / "projects" / slug
        expected_backup = migration.directory(slug, root=repo_root) / "original-tree"
        if entry.get("backup_path") != str(expected_backup.relative_to(repo_root)):
            raise ValueError("migration rollback backup path is invalid")
        import hashlib
        if not isinstance(entry.get("baseline_files"), dict) or sha_map(entry["baseline_files"]) != entry.get("baseline_digest"):
            raise ValueError("migration rollback baseline is invalid")
        backup = expected_backup
        if not backup.is_dir() or backup.is_symlink() or project.is_symlink() or digest(backup, allow_symlinks=slug == "us-retirees-italy") != entry["baseline_files"]:
            raise ValueError("migration rollback backup is unavailable")
        current = digest(project, allow_symlinks=slug == "us-retirees-italy") if project.exists() else {}
        baseline = entry["baseline_files"]
        # Only migration-owned partial trees are recoverable.  Any edit to a
        # legacy file outside a moved source root is treated as an external
        # modification and refused rather than silently archived.
        spec = spec_for(slug)
        moved_prefixes = {"README.md", "project-manifest.json"}
        moved_prefixes.update(f"{p}/" for p in spec["shared"] + spec["history"] + spec["reviews"] + spec["assets"])
        generated_prefixes = ("business-analysis/", "history/", "digital-assets/")
        relocation = {}
        for rel in spec["shared"]:
            relocation[rel] = f"business-analysis/{rel}"
        for rel in spec["history"]:
            relocation[rel] = f"business-analysis/history/legacy/{rel}"
        for rel in spec["reviews"]:
            relocation[rel] = f"business-analysis/history/reviews/{rel}"
        for rel in spec["assets"]:
            relocation[rel] = "digital-assets/website" if rel == "web-site" else ("digital-assets/others" if rel == "digital-assets" else rel)
        mapped_targets = set()
        for source, destination in relocation.items():
            for original in baseline:
                if original == source or original.startswith(source + "/"):
                    suffix = original[len(source):].lstrip("/")
                    mapped_targets.add(destination + ("/" + suffix if suffix else ""))
        for path in ("README.md", "project-manifest.json"):
            known_replacement = entry.get("replacement_files", {}).get(path)
            if path in current and current[path] not in {baseline.get(path), known_replacement}:
                raise ValueError("migration rollback refused: external modification detected")
        for path, digest_value in baseline.items():
            if path in {"README.md", "project-manifest.json"}:
                continue
            if any(path.startswith(prefix) for prefix in moved_prefixes):
                for source, destination in relocation.items():
                    if path == source or path.startswith(source + "/"):
                        suffix = path[len(source):].lstrip("/")
                        target = destination + ("/" + suffix if suffix else "")
                        if path in current and current[path] != digest_value:
                            raise ValueError("migration rollback refused: external modification detected")
                        if target in current and current[target] != digest_value:
                            raise ValueError("migration rollback refused: external modification detected")
                        break
                continue
            if current.get(path) != digest_value:
                raise ValueError("migration rollback refused: external modification detected")
        for path in current:
            if path in baseline or path == "project.lock" or any(path.startswith(prefix) for prefix in generated_prefixes):
                continue
            raise ValueError("migration rollback refused: unexpected external file detected")
        allowed_generated = {"business-analysis/README.md", "business-analysis/project-manifest.json", "business-analysis/project.lock"}
        for case_id, _title in spec["cases"]:
            allowed_generated.update({f"business-analysis/cases/{case_id}/README.md", f"business-analysis/cases/{case_id}/market_research/manifest.json"})
        allowed_dirs = tuple(
            f"{root}history/{kind}/{prefix}"
            for root in ("", "business-analysis/")
            for kind in ("decisions", "snapshots", "staging")
            for prefix in ([f"register-{cid}/" for cid, _ in spec["cases"]] + [f"register-{cid}" for cid, _ in spec["cases"]] + [f"case-layout-{slug}/"])
        )
        allowed_generated.update({"history/evolution.md", "history/project.lock"})
        allowed_generated.add("business-analysis/history/evolution.md")
        allowed_dirs += ("history/decisions/independent-subprojects", "history/snapshots/independent-subprojects/", "history/staging/independent-subprojects/")
        for path in current:
            if path.startswith("business-analysis/") or path.startswith("digital-assets/") or path.startswith("history/"):
                if path in allowed_generated or path.startswith(allowed_dirs) or \
                   any(f"business-analysis/history/snapshots/register-{cid}/" in path for cid, _ in spec["cases"]):
                    continue
                if path in baseline:
                    continue
                if path in mapped_targets:
                    continue
                raise ValueError("migration rollback refused: unexpected generated file detected")
        # Validate generated controller/case manifests even when no final
        # replacement snapshot exists (the crash window before completion).
        analysis = project / "business-analysis"
        controller = analysis / "project-manifest.json"
        if controller.exists():
            try:
                data = json.loads(controller.read_text())
            except (OSError, ValueError) as exc:
                raise ValueError("migration rollback refused: invalid generated controller") from exc
            if data.get("layout_version") != 2 or set(data.get("cases", {})) - {c[0] for c in spec["cases"]}:
                raise ValueError("migration rollback refused: invalid generated controller")
        for case_id, title in spec["cases"]:
            manifest = analysis / "cases" / case_id / "market_research/manifest.json"
            if not manifest.exists():
                continue
            try:
                data = json.loads(manifest.read_text())
            except (OSError, ValueError) as exc:
                raise ValueError("migration rollback refused: invalid generated case manifest") from exc
            if data.get("case_id") != case_id or data.get("topic") != title or data.get("stages") != {} or not data.get("open_blockers"):
                raise ValueError("migration rollback refused: invalid generated case manifest")
        known = entry.get("replacement_files")
        if isinstance(known, dict):
            for path, digest_value in current.items():
                if (path.startswith(generated_prefixes) or path in {"README.md", "project-manifest.json"}) and path != "project.lock":
                    if known.get(path) != digest_value:
                        raise ValueError("migration rollback refused: external modification detected")
        prior_recorded = entry.get("rollback_files")
        entry["state"] = "rollback_started"
        if not isinstance(prior_recorded, dict):
            entry["rollback_files"] = current
        migration.write_journal(slug, entry, root=repo_root)
        replaced = migration.directory(slug, root=repo_root) / "replaced-tree"
        recorded = prior_recorded if isinstance(prior_recorded, dict) else entry.get("rollback_files")
        if replaced.exists() and isinstance(recorded, dict):
            if digest(replaced, allow_symlinks=slug == "us-retirees-italy") != recorded:
                raise ValueError("rollback replacement archive does not match recorded tree")
        if project.exists():
            if replaced.exists() or replaced.is_symlink():
                replaced = migration.directory(slug, root=repo_root) / "replaced-tree-resume"
                if replaced.exists() or replaced.is_symlink():
                    raise ValueError("rollback replacement archive already exists")
            os.replace(project, replaced)
        elif not replaced.is_dir() or replaced.is_symlink():
            raise ValueError("rollback replacement archive is unavailable")
        shutil.copytree(backup, project, symlinks=(slug == "us-retirees-italy"))
        if digest(project, allow_symlinks=slug == "us-retirees-italy") != entry["baseline_files"]:
            raise ValueError("rollback did not restore the exact baseline")
        entry["state"] = "rolled_back"
        entry["replacement_backup"] = str(replaced.relative_to(repo_root)) if replaced.exists() else None
        migration.write_journal(slug, entry, root=repo_root)


def execute(slug: str, *, repo_root: Path = ROOT) -> dict:
    repo_root = Path(repo_root).absolute()
    project = repo_root / "projects" / slug
    spec = spec_for(slug)
    if project.is_symlink() or not project.is_dir():
        raise ValueError("canonical project directory is missing or symlinked")
    with migration.lock(slug, root=repo_root, exclusive=True):
        if migration.journal(slug, root=repo_root) is not None:
            raise ValueError("migration journal already exists; recover it first")
        baseline = digest(project, allow_symlinks=slug == "us-retirees-italy")
        coordination = migration.directory(slug, root=repo_root)
        backup = coordination / "original-tree"
        if backup.exists() or backup.is_symlink():
            raise ValueError("migration backup already exists")
        shutil.copytree(project, backup, symlinks=(slug == "us-retirees-italy"))
        entry = {"project_id": slug, "migration_id": f"case-layout-{slug}", "state": "prepared",
                 "project_path": f"projects/{slug}", "baseline_digest": sha_map(baseline),
                 "baseline_files": baseline, "phase_files": baseline, "backup_path": str(backup.relative_to(repo_root))}
        migration.write_journal(slug, entry, root=repo_root)
        try:
            with migration.permit(slug):
                transition(project, slug, spec, entry, repo_root)
                entry["replacement_files"] = digest(project, allow_symlinks=slug == "us-retirees-italy")
                verify(project, slug, spec, entry, repo_root)
            entry["state"] = "verified"
            migration.write_journal(slug, entry, root=repo_root)
            return {"project": str(project), "state": "verified", "journal": str(coordination / "journal.json")}
        except Exception:
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, choices=sorted(SPECS))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    if args.execute == args.rollback:
        parser.error("choose exactly one of --execute or --rollback")
    if args.rollback:
        rollback(args.project, repo_root=args.root)
        return 0
    print(json.dumps(execute(args.project, repo_root=args.root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
