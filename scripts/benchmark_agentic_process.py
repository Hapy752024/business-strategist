#!/usr/bin/env python3
"""Compare auditable agent/skill process contracts at a Git baseline and now."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "agentic-process-eval.json"


def git_files(ref: str) -> set[str]:
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git baseline {ref} is unavailable in this checkout")
    return set(result.stdout.splitlines())


def git_text(ref: str, path: str) -> str:
    result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True, capture_output=True)
    return result.stdout if result.returncode == 0 else ""


def current_files() -> set[str]:
    ignored = {".git", "node_modules", ".next", "__pycache__", ".pytest_cache", "test-results"}
    found: set[str] = set()
    for directory, names, files in os.walk(ROOT):
        names[:] = [name for name in names if name not in ignored]
        base = Path(directory)
        found.update((base / name).relative_to(ROOT).as_posix() for name in files)
    return found


def snapshot(files: set[str], read_text) -> dict[str, object]:
    skill_entries = sorted(path for path in files if path.startswith(".agents/skills/") and path.endswith("/SKILL.md"))
    eval_entries = sorted(path for path in files if path.startswith(".agents/skills/") and path.endswith("/evals/evals.json"))
    brand_entries = [path for path in skill_entries if Path(path).parts[2].startswith("brand-")]
    workflow = read_text("config/workflow-routes.json")
    ci = read_text(".github/workflows/validate.yml")
    experiment = read_text("fixtures/website/stellar-repair/lib/flags.ts") + read_text("fixtures/website/stellar-repair/app/experiment-cta.tsx")
    promoter = read_text("scripts/brand/promote_artifact.py")
    claim_builder = read_text("scripts/evidence_scout/build_claim_ledger.py")
    contracts = {
        "brand-skills": len(brand_entries) >= 10,
        "website-skill": ".agents/skills/brand-website-designer-builder/SKILL.md" in files and "brand-website-designer-builder" in workflow,
        "server-experiment": "flags/next" in experiment and "Math.random" not in experiment and '"use client"' not in experiment,
        "browser-qa": "playwright" in ci.lower() and "@axe-core/playwright" in read_text("fixtures/website/stellar-repair/package.json"),
        "brand-state-cli": ".agents/skills/brand-workspace-manager/scripts/workspace_cli.py" in files,
        "safe-promotion": "refusing to overwrite a different artifact" in promoter,
        "fal-finalization": "scripts/brand/finalize_fal_assets.py" in files,
        "claim-fail-closed": "unknown evidence IDs" in claim_builder and "if str(item) in by_id" not in claim_builder,
    }
    return {
        "skill_count": len(skill_entries),
        "skills_with_evals": len(eval_entries),
        "brand_skill_count": len(brand_entries),
        "contract_passes": sum(contracts.values()),
        "contract_total": len(contracts),
        "contracts": contracts,
    }


def resolve_baseline(config: dict[str, object]) -> tuple[dict[str, object], str]:
    baseline_ref = str(config["baseline_ref"])
    try:
        files = git_files(baseline_ref)
    except RuntimeError:
        embedded = config.get("baseline_snapshot")
        if not isinstance(embedded, dict):
            raise
        return embedded, "embedded-audited-snapshot"
    return snapshot(files, lambda path: git_text(baseline_ref, path)), "git-tree"


def write_run(root: Path, name: str, prompt: str, metrics: dict[str, object], elapsed: float) -> None:
    run = root / name
    outputs = run / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    (run / "eval_metadata.json").write_text(json.dumps({"eval_id": 1 if name == "baseline" else 2, "prompt": prompt}, indent=2) + "\n")
    lines = [f"# {name.title()} structural snapshot", "", "| Contract | Result |", "| --- | --- |"]
    lines.extend(f"| `{key}` | {'PASS' if value else 'MISSING'} |" for key, value in metrics["contracts"].items())
    lines.extend(["", f"Skills: {metrics['skill_count']}", f"Skills with eval definitions: {metrics['skills_with_evals']}", f"Brand skills: {metrics['brand_skill_count']}", "", "This is a structural snapshot. It does not establish LLM or visual quality.", ""])
    (outputs / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (run / "grading.json").write_text(json.dumps({
        "summary": {"pass_rate": metrics["contract_passes"] / metrics["contract_total"], "passed": metrics["contract_passes"], "failed": metrics["contract_total"] - metrics["contract_passes"], "total": metrics["contract_total"]},
        "timing": {"total_duration_seconds": round(elapsed, 4)},
        "execution_metrics": {"total_tool_calls": 0, "output_chars": len("\n".join(lines)), "errors_encountered": 0},
        "expectations": [{"text": key, "passed": value, "evidence": "repository contract inspection"} for key, value in metrics["contracts"].items()],
    }, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval-workspaces" / "agentic-process")
    parser.add_argument("--static-review", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    baseline_ref = config["baseline_ref"]

    started = time.perf_counter()
    baseline, baseline_source = resolve_baseline(config)
    baseline_elapsed = time.perf_counter() - started
    started = time.perf_counter()
    current = snapshot(current_files(), lambda path: (ROOT / path).read_text(encoding="utf-8") if (ROOT / path).is_file() else "")
    current_elapsed = time.perf_counter() - started

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_run(args.output_dir, "baseline", config["baseline_label"], baseline, baseline_elapsed)
    write_run(args.output_dir, "current", config["comparison_label"], current, current_elapsed)
    benchmark = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "structural-contract-comparison",
        "baseline_ref": baseline_ref,
        "baseline_source": baseline_source,
        "limitations": config["limitations"],
        "baseline": baseline,
        "current": current,
        "delta": {key: current[key] - baseline[key] for key in ("skill_count", "skills_with_evals", "brand_skill_count", "contract_passes")},
    }
    benchmark_path = args.output_dir / "benchmark.json"
    benchmark_path.write_text(json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.static_review:
        viewer = Path(os.environ.get("SKILL_CREATOR_VIEWER", "/home/habib/.agents/skills/skill-creator/eval-viewer/generate_review.py"))
        if not viewer.is_file():
            parser.error("skill-creator eval viewer not found; set SKILL_CREATOR_VIEWER")
        subprocess.run(["python3", str(viewer), str(args.output_dir), "--skill-name", "agentic-process", "--benchmark", str(benchmark_path), "--static", str(args.output_dir / "review.html")], check=True)
    print(json.dumps({"workspace": str(args.output_dir), "benchmark": str(benchmark_path), "baseline_source": baseline_source, "baseline": baseline, "current": current}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
