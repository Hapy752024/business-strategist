#!/usr/bin/env python3
"""Collect operator evidence for a business-archetype playbook."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from workspace import create_topic_workspace, slugify, update_stage


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Research validation, launch, first-customer, and scaling playbooks from founder/operator sources.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--archetype", required=True, help="For example B2B SaaS, marketplace, local service, or regulated insurance broker.")
    parser.add_argument("--customer-segment", default="")
    parser.add_argument("--stage", default="idea", choices=["idea", "interviews", "prototype", "mvp", "pilots", "revenue", "scale"])
    parser.add_argument("--geo", default="AUTO")
    parser.add_argument("--language", default="AUTO")
    parser.add_argument("--days", type=int, default=3650)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--providers", default="default")
    parser.add_argument("--workspace", default="")
    args = parser.parse_args()

    workspace = create_topic_workspace(args.topic, args.workspace, args.customer_segment)
    run_dir = workspace / "playbooks" / "runs" / f"{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{slugify(args.archetype)}"
    evidence_dir = run_dir / "evidence"
    run_dir.mkdir(parents=True, exist_ok=True)
    plan = f"""# Founder / Operator Playbook Research Plan

- Topic: {args.topic}
- Archetype: {args.archetype}
- Customer segment: {args.customer_segment or '[UNRESOLVED]'}
- Company stage: {args.stage}
- Geography / language: {args.geo} / {args.language}

## Questions

1. How did comparable operators choose their first segment?
2. What did they do before building, and what evidence changed their plan?
3. How did they acquire the first ten paying customers with limited spend?
4. Which offers, prices, partnerships, and channels worked or failed?
5. What retention, economics, compliance, and hiring gates preceded scaling?

## Interpretation rules

- Founder anecdotes are operator evidence, not proof of customer demand.
- Preserve failures, context, dates, and selection bias.
- Triangulate material tactics before recommending transfer.
"""
    (run_dir / "research_plan.md").write_text(plan, encoding="utf-8")
    update_stage(workspace, "operator_playbook", status="in_progress", gate_result="not_run", artifacts=[run_dir / "research_plan.md"], next_action="Collect and synthesize comparable operator evidence.")

    research_topic = f"{args.archetype} founders validating launching finding first customers and scaling {args.topic}"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "evidence_scout" / "collect.py"),
        "--topic", research_topic,
        "--customer-segment", args.customer_segment or f"founders and operators of {args.archetype} businesses",
        "--problem-keywords", "customer validation,first paying customers,pricing,launch,churn,failed acquisition",
        "--workaround-keywords", "founder-led sales,concierge MVP,manual outreach,community marketing,partnerships",
        "--hypothesis-id", "OP1",
        "--days", str(args.days),
        "--limit", str(args.limit),
        "--providers", args.providers,
        "--geo", args.geo,
        "--language", args.language,
        "--out-dir", str(evidence_dir),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    result = {
        "topic": args.topic,
        "archetype": args.archetype,
        "workspace": str(workspace),
        "run_dir": str(run_dir),
        "evidence_dir": str(evidence_dir),
        "collector_exit_code": completed.returncode,
        "next_artifact": str(workspace / "playbooks" / f"{slugify(args.archetype)}.md"),
    }
    (run_dir / "run_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = "pass" if completed.returncode == 0 else "fail"
    update_stage(
        workspace,
        "operator_playbook",
        status="passed" if completed.returncode == 0 else "failed",
        gate_result=gate,
        artifacts=[run_dir / "research_plan.md", run_dir / "run_summary.json", evidence_dir / "report.md", evidence_dir / "evidence.jsonl"],
        open_gaps=[] if completed.returncode == 0 else ["Collector returned no strong/relevant operator evidence; inspect provider alerts and broaden sources."],
        next_action="Synthesize sourced operator patterns into the archetype playbook without treating anecdotes as demand proof.",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
