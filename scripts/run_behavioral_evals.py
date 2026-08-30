#!/usr/bin/env python3
"""Run deterministic routing/contract scenarios and emit review artifacts.

This offline harness does not claim to benchmark model quality. It catches
route and safety-contract drift before a separately authorized LLM/human run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [
    ("standalone-brand", "Independently develop a brand identity without research", "brand-designer"),
    ("business-linked-brand", "Turn my validated business workspace into a segment-informed brand", "brand-designer"),
    ("logo-only", "Create a logo only; do not make a website", "brand-designer"),
    ("brand-research", "Research visual codes for a luxury skincare brand", "brand-guideline-researcher"),
    ("standalone-website", "Build a unique Next.js landing page", "brand-website-designer-builder"),
    ("approved-brand-website", "Build a marketing website from our approved brand", "brand-website-designer-builder"),
    ("app-ui", "Design product dashboard UI screens", "brand-frontend-app-designer"),
    ("competitor-website", "Analyze a competitor's website positioning and CTA", "competitor-marketing-analyzer"),
    ("experiment", "Run a simple A/B test on the homepage CTA", "brand-website-designer-builder"),
    ("fal-asset", "Generate a brand hero image using FAL", "brand-asset-producer"),
    ("vercel-release", "Prepare a GitHub to Vercel Preview release", "brand-website-designer-builder"),
    ("market-discovery", "Find customer problems in independent elder care", "market-problem-discovery"),
    ("idea-validation", "Pressure-test this idea: software for independent care homes to schedule staff", "idea-grill"),
]


def run(repeat: int) -> dict:
    results = []
    for name, prompt, expected in SCENARIOS:
        observations = []
        for _ in range(repeat):
            started = time.perf_counter()
            output = subprocess.check_output(["python3", str(ROOT / "scripts/route_workflow.py"), prompt], text=True)
            routed = json.loads(output)
            observations.append({
                "route": routed["skill"],
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "tool_calls": 1,
                "reference_files_opened": 0,
            })
        passed = all(item["route"] == expected for item in observations)
        results.append({"name": name, "prompt": prompt, "expected_skill": expected, "observations": observations, "passed": passed})
    return {
        "schema_version": "1.1",
        "mode": "offline-contract",
        "limitations": "No LLM was invoked. Run an authorized LLM/human benchmark before claiming behavioral or visual quality.",
        "repeat": repeat,
        "passed": all(item["passed"] for item in results),
        "scenarios": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    if args.repeat < 1 or args.repeat > 20:
        parser.error("repeat must be between 1 and 20")
    report = run(args.repeat)
    serialized = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    if args.markdown_output:
        rows = ["# Offline behavioral-contract evaluation", "", "This is a deterministic routing/contract check, not an LLM or visual-quality benchmark.", "", "| Scenario | Expected | Result | Repeats |", "| --- | --- | --- | ---: |"]
        rows.extend(f"| {item['name']} | `{item['expected_skill']}` | {'PASS' if item['passed'] else 'FAIL'} | {len(item['observations'])} |" for item in report["scenarios"])
        rows.extend(["", f"Overall: **{'PASS' if report['passed'] else 'FAIL'}**", "", "Next gate: authorized LLM/human review with token, tool-call, and screenshot evidence.", ""])
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(rows), encoding="utf-8")
    print(serialized, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
