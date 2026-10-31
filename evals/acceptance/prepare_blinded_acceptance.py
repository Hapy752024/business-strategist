#!/usr/bin/env python3
"""Blind two acceptance runs for an independent grader (equivalent of prepare_blinded_eval.py for run dirs).

scripts/prepare_blinded_eval.py expects trial.json/answer.txt trial directories; acceptance runs produce project
artifact trees, so this copies the same role-mapped document set from each run into A/ and B/ (random assignment),
scrubs run-identifying strings, and writes the key to <out>/.key.json (gitignored).
Usage: prepare_blinded_acceptance.py --baseline RUN --current RUN --out DIR --seed N
"""
import argparse, json, random, re, shutil, sys
from pathlib import Path

ROLES = [  # (output name, glob relative to business-analysis/cases/*/ ; first match per slot, sorted)
    ("case-insights.md", "case_insights.md"),
    ("business-case.md", "business-case.md"),
    ("business-case.md", "provisional/business-case.md"),
    ("gtm-plan.md", "gtm-plan.md"),
    ("gtm-plan.md", "provisional/gtm-plan.md"),
    ("campaign-guidance.md", "first-campaigns.md"),
    ("campaign-guidance.md", "provisional/campaign-guidance.md"),
    ("recruitment-plan.md", "market_research/interviews/recruitment-plan.md"),
    ("research-notes.md", "market_research/research-summary-*.md"),
    ("research-notes.md", "market_research/desk-research-progress-*.md"),
    ("competitor-scan.md", "market_research/competitor-scan-*.md"),
]
SCRUB = [
    (re.compile(r"eval-hybrid-insurance-advisor-\d{8}-\d{6}"), "project"),
    (re.compile(r"hybrid-insurance-advisor-\d{8}-\d{6}"), "project"),
    (re.compile(r"\b\d{8}-\d{6}-[\w\-äöüß]+?-[0-9a-f]{12}\b"), "run"),
    (re.compile(r"\b[0-9a-f]{40}\b"), "[hash]"),
    (re.compile(r"`?(?:python3? )?(?:\./)?scripts/[\w/\.\-]+`?"), "[tool]"),
    (re.compile(r"\bevidence-review-queue\b|\bprovisional\b", re.I), "interim"),
    (re.compile(r"\b(?:claude|Claude|Opus|Sonnet|Haiku)[\w\- .]*\b(?:code|model)?"), "[agent]"),
    (re.compile(r"\b20261031-\d{6}\b"), "[run-id]"),
    (re.compile(r"/home/\S+"), "[path]"),
]

def scrub(text: str) -> str:
    for rx, rep in SCRUB:
        if rep is not None:
            text = rx.sub(rep, text)
    return text

def collect(run: Path) -> dict[str, str]:
    cases = list(run.glob("artifacts/projects/*/business-analysis/cases/*"))
    if len(cases) != 1:
        sys.exit(f"{run}: expected exactly one case dir, found {len(cases)}")
    case, out = cases[0], {}
    for name, pattern in ROLES:
        for p in sorted(case.glob(pattern)):
            out.setdefault(name, "")
            out[name] += ("\n\n" if out[name] else "") + p.read_text(encoding="utf-8")
    reports = sorted(case.glob("market_research/pain_points/runs/*/report.md"))
    for i, p in enumerate(reports, 1):
        out[f"customer-voice-report-{i}.md"] = p.read_text(encoding="utf-8")
    return {k: scrub(v) for k, v in out.items()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--current", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=int)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    swap = rng.randrange(2) == 1
    mapping = {"A": "current", "B": "baseline"} if swap else {"A": "baseline", "B": "current"}
    src = {"baseline": a.baseline, "current": a.current}
    a.out.mkdir(parents=True, exist_ok=True)
    for blind, arm in mapping.items():
        d = a.out / blind
        if d.exists(): shutil.rmtree(d)
        d.mkdir()
        for name, text in collect(src[arm]).items():
            (d / name).write_text(text, encoding="utf-8")
    (a.out / ".key.json").write_text(json.dumps({"seed": a.seed, "mapping": mapping}, indent=2) + "\n")

if __name__ == "__main__":
    main()
