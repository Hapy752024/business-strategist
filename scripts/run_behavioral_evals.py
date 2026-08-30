#!/usr/bin/env python3
"""Run deterministic routing/contract scenarios and emit a reviewable report.

This offline harness does not claim to benchmark model quality; it catches route
drift and contract regressions before human/LLM behavioral evaluation.
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
    ("standalone-website", "Build a unique Next.js landing page", "brand-website-designer-builder"),
    ("app-ui", "Design product dashboard UI screens", "brand-frontend-app-designer"),
    ("experiment", "Run a simple A/B test on the homepage CTA", "brand-website-designer-builder"),
    ("market-discovery", "Find customer problems in independent elder care", "market-problem-discovery"),
]


def run(repeat: int) -> dict:
    results = []
    for name, prompt, expected in SCENARIOS:
        observations = []
        for _ in range(repeat):
            started = time.perf_counter()
            output = subprocess.check_output(["python3", str(ROOT / "scripts/route_workflow.py"), prompt], text=True)
            observations.append({"route": json.loads(output)["skill"], "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
        passed = all(item["route"] == expected for item in observations)
        results.append({"name": name, "prompt": prompt, "expected_skill": expected, "observations": observations, "passed": passed})
    return {"schema_version": "1.0", "mode": "offline-contract", "repeat": repeat, "passed": all(item["passed"] for item in results), "scenarios": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeat < 1 or args.repeat > 20:
        parser.error("repeat must be between 1 and 20")
    report = run(args.repeat)
    serialized = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
