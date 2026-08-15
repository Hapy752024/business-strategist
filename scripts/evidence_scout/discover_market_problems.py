#!/usr/bin/env python3
"""Scaffold, collect, and close an exploratory market-problem discovery run.

The script deliberately does not synthesize opportunity claims. It creates a
durable artifact contract and can call the existing collector in discovery
mode; an agent must inspect the sources and write the final Markdown report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from workspace import create_run_manifest, resolve_run_dir, update_run_manifest, update_stage, write_json


ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts" / "evidence_scout" / "collect.py"
TEMPLATE = ROOT / "templates" / "research-topic" / "market-discovery-report.md"
REQUIRED_HEADINGS = (
    "## Executive Summary",
    "## Scope and Source Coverage",
    "## Candidate Problem-Segment Pockets",
    "## Detailed Findings",
    "## Cross-Cutting Patterns",
    "## Counter-Evidence and Coverage Gaps",
    "## Questions for Your Decision",
    "## Recommended Next Investigations",
    "## Handoff",
)

# A finished report must carry these standing line-items, not just headings.
REQUIRED_LINE_ITEMS = (
    "Reachability bias:",
)


def read_json(path: Path, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback or {}
    return value if isinstance(value, dict) else (fallback or {})


def render_report_template(topic: str, focus: str, geo: str, language: str) -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "TOPIC": topic,
        "FOCUS": focus or "[No specific hunch supplied]",
        "GEO": geo,
        "LANGUAGE": language,
    }
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def write_research_plan(run_dir: Path, args: argparse.Namespace) -> None:
    lines = [
        "# Market Discovery Research Plan",
        "",
        "## Objective",
        "",
        f"Explore publicly visible customer problems, workarounds, and possible segments in `{args.topic}` before choosing a problem hypothesis.",
        "",
        "## Scope",
        "",
        f"- Market/domain: `{args.topic}`",
        f"- Rough hunch: `{args.focus or 'none supplied'}`",
        f"- Geography/language requested: `{args.geo}/{args.language}`",
        f"- Provider set: `{args.providers}`",
        f"- Lookback days: `{args.days}`",
        "",
        "## Questions This Run Can Explore",
        "",
        "- Which jobs, trigger events, and frustrations recur in the public evidence?",
        "- Which people appear to have distinct versions of the job or pain?",
        "- What manual workarounds, competing products, services, or do-nothing alternatives appear?",
        "- Which signals suggest a gap, and which suggest the area is already solved or crowded?",
        "",
        "## Limits",
        "",
        "- This run discovers hypotheses and interview leads; it does not prove willingness to pay or an underserved market.",
        "- Provider/editorial/competitor pages are context about alternatives, not customer-demand proof.",
        "- A failed or unavailable provider reduces coverage and must be disclosed in the final report.",
        "",
        "## Required User Checkpoint",
        "",
        "After synthesis, ask one question: `Which path should we take next: validate Candidate [X], broaden/narrow the market scope, extend a named source gap, or stop?`",
    ]
    (run_dir / "research_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def collector_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(COLLECTOR),
        "--topic",
        args.topic,
        "--customer-segment",
        "",
        "--hypothesis-id",
        "D1",
        "--days",
        str(args.days),
        "--limit",
        str(args.limit),
        "--providers",
        args.providers,
        "--geo",
        args.geo,
        "--language",
        args.language,
        "--out-dir",
        str(run_dir / "evidence"),
        "--research-mode",
        "discovery",
    ]
    if args.problem_keywords:
        command.extend(["--problem-keywords", args.problem_keywords])
    if args.workaround_keywords:
        command.extend(["--workaround-keywords", args.workaround_keywords])
    return command


def provider_failures(evidence_summary: dict[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for provider, detail in (evidence_summary.get("providers") or {}).items():
        if not isinstance(detail, dict):
            continue
        status = str(detail.get("status", "failed"))
        if status not in {"ok", "not_run"}:
            failures.append(
                {
                    "provider": provider,
                    "failure_class": status,
                    "confidence_impact": "high",
                }
            )
    return failures


def start_discovery(args: argparse.Namespace) -> int:
    run_dir, workspace = resolve_run_dir(
        topic=args.topic,
        workspace_arg=args.workspace,
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="market-discovery/runs",
        legacy_subdir="market-discovery",
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "market-discovery-report.md"
    if not report_path.exists():
        report_path.write_text(render_report_template(args.topic, args.focus, args.geo, args.language), encoding="utf-8")
    write_research_plan(run_dir, args)

    if workspace:
        update_stage(
            workspace,
            "market_discovery",
            status="in_progress",
            gate_result="not_run",
            artifacts=[run_dir / "research_plan.md", report_path],
            next_action="Collect public evidence, synthesize candidate problems, then ask the user to choose a path.",
        )
    create_run_manifest(
        run_dir,
        subject=args.topic,
        run_type="market_discovery",
        stage="market_discovery",
        sources=args.providers.split(","),
        next_action="Collect public evidence, synthesize candidate problems, then ask the user to choose a path.",
    )

    summary: dict[str, Any] = {
        "mode": "market_discovery",
        "status": "planned",
        "topic": args.topic,
        "focus": args.focus,
        "geo": args.geo,
        "language": args.language,
        "providers_requested": args.providers,
        "run_dir": str(run_dir),
        "workspace": str(workspace) if workspace else "",
        "outputs": {
            "research_plan": str(run_dir / "research_plan.md"),
            "report": str(report_path),
            "evidence_dir": str(run_dir / "evidence"),
            "summary": str(run_dir / "summary.json"),
        },
        "next_action": "Inspect source outputs and replace the report template with evidence-backed findings before finalizing.",
    }

    if args.collect:
        command = collector_command(args, run_dir)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        (run_dir / "collector.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "collector.stderr.log").write_text(completed.stderr, encoding="utf-8")
        evidence_summary = read_json(run_dir / "evidence" / "summary.json")
        summary.update(
            {
                "status": "awaiting_synthesis",
                "collector_exit_code": completed.returncode,
                "evidence": {
                    "record_count": evidence_summary.get("record_count", 0),
                    "needs_user_attention": evidence_summary.get("needs_user_attention", []),
                    "quality_flags": evidence_summary.get("quality_flags", []),
                    "provider_failures": provider_failures(evidence_summary),
                },
            }
        )
        summary["next_action"] = "Inspect evidence/, synthesize the report, then run this command: python3 scripts/evidence_scout/discover_market_problems.py --finalize --run-dir \"%s\" --candidate-count <0-7>" % run_dir

    write_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def finalize_discovery(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        raise ValueError(f"Discovery run directory does not exist: {run_dir}")
    if args.candidate_count is None or not 0 <= args.candidate_count <= 7:
        raise ValueError("--candidate-count is required and must be between 0 and 7")

    report_path = run_dir / "market-discovery-report.md"
    if not report_path.exists():
        raise ValueError(f"Missing report: {report_path}")
    report = report_path.read_text(encoding="utf-8")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in report]
    missing_items = [item for item in REQUIRED_LINE_ITEMS if item not in report]
    placeholders = [token for token in ("{{", "<!--", "[name]") if token in report]
    if missing or missing_items or placeholders:
        details = []
        if missing:
            details.append("missing headings: " + ", ".join(missing))
        if missing_items:
            details.append("missing line-items: " + ", ".join(item.rstrip(":") for item in missing_items))
        if placeholders:
            details.append("unreplaced placeholders: " + ", ".join(placeholders))
        raise ValueError("Report is not ready to finalize (" + "; ".join(details) + ")")

    evidence_summary = read_json(run_dir / "evidence" / "summary.json")
    if not evidence_summary:
        raise ValueError("Missing evidence/summary.json; run collection and disclose its source coverage before finalizing")

    summary = read_json(run_dir / "summary.json")
    failures = provider_failures(evidence_summary)
    quality_flags = list(evidence_summary.get("quality_flags") or [])
    alerts = list(evidence_summary.get("needs_user_attention") or [])
    record_count = int(evidence_summary.get("record_count") or 0)
    gate_result = "pass"
    if failures or quality_flags or alerts or record_count == 0:
        gate_result = "conditional_pass"
    next_action = (
        "Ask the user to choose one candidate for focused validation, change the market scope, extend a named source gap, or stop."
        if args.candidate_count
        else "Ask the user whether to broaden or narrow the scope, extend a named source gap, or stop; no candidate should enter validation automatically."
    )

    summary.update(
        {
            "mode": "market_discovery",
            "status": "complete",
            "candidate_count": args.candidate_count,
            "gate_result": gate_result,
            "evidence": {
                "record_count": record_count,
                "needs_user_attention": alerts,
                "quality_flags": quality_flags,
                "provider_failures": failures,
            },
            "next_action": next_action,
        }
    )
    write_json(run_dir / "summary.json", summary)

    workspace_value = summary.get("workspace") or ""
    workspace = Path(workspace_value) if workspace_value else None
    if workspace and (workspace / "manifest.json").exists():
        artifacts = [run_dir / "research_plan.md", report_path, run_dir / "summary.json"]
        for relative in ("evidence/report.md", "evidence/evidence.jsonl", "evidence/summary.json"):
            artifact = run_dir / relative
            if artifact.exists():
                artifacts.append(artifact)
        update_stage(
            workspace,
            "market_discovery",
            status="passed",
            gate_result=gate_result,
            artifacts=artifacts,
            provider_failures=failures,
            open_gaps=[*quality_flags, *alerts],
            next_action=next_action,
        )
    update_run_manifest(
        run_dir,
        stage="market_discovery",
        stage_status="passed",
        gate_result=gate_result,
        artifacts=[run_dir / "research_plan.md", report_path, run_dir / "summary.json"],
        open_gaps=[*quality_flags, *alerts],
        next_action=next_action,
        event="market_discovery_finalized",
        record_count=record_count,
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover market problems and candidate customer segments before validation.")
    parser.add_argument("--topic", default="", help="Rough market, category, domain, or problem space to explore.")
    parser.add_argument("--focus", default="", help="Optional hunch or boundary. It is a search seed, not a claim.")
    parser.add_argument("--problem-keywords", default="", help="Optional comma-separated user-problem language for a broader discovery query set.")
    parser.add_argument("--workaround-keywords", default="", help="Optional comma-separated workaround language for discovery queries.")
    parser.add_argument("--providers", default="default", help="Collector provider set. Default excludes paid social enrichment.")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--geo", default="AUTO")
    parser.add_argument("--language", default="AUTO")
    parser.add_argument("--workspace", default="", help="Optional topic workspace path.")
    parser.add_argument("--out-dir", default="", help="Optional explicit discovery-run directory.")
    parser.add_argument("--legacy-output", action="store_true")
    parser.add_argument("--collect", action="store_true", help="Run the existing collector in discovery mode into this run's evidence/ directory.")
    parser.add_argument("--finalize", action="store_true", help="Validate the synthesized report and close the market-discovery stage.")
    parser.add_argument("--run-dir", default="", help="Existing discovery run directory; required with --finalize.")
    parser.add_argument("--candidate-count", type=int, default=None, help="Number of source-backed candidates in the finished report (0-7).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.finalize:
            if not args.run_dir:
                raise ValueError("--run-dir is required with --finalize")
            return finalize_discovery(args)
        if not args.topic.strip():
            raise ValueError("--topic is required when starting a discovery run")
        return start_discovery(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
