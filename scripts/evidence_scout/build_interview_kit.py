#!/usr/bin/env python3
"""Build an interview kit from a collected evidence run.

Public evidence is mostly weak; its best use is recruiting and grounding real
customer interviews. This script converts a run's weak/medium user-pain and
decision records into three artifacts under <run>/interview/:

  - interview-screener.md  — who to recruit, where, and disqualifiers
  - interview-guide.md     — non-leading probe questions traced to evidence
  - interview-tracker.md   — confirmation/refutation log per evidence item

Usage:
  python3 scripts/evidence_scout/build_interview_kit.py --run-dir <run path> [--limit 8]

For market-discovery runs, pass the run root; the script looks for
evidence/evidence.jsonl automatically. No network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STRENGTHS_FOR_INTERVIEW = {"weak", "medium"}
SOURCE_LABELS = {
    "reddit": "Reddit threads/comments",
    "youtube": "YouTube comments",
    "serper": "Google search results",
    "brave": "Brave search results",
    "firecrawl": "Scraped pages",
    "scrapecreators": "Facebook/Instagram posts",
    "trends": "Google Trends",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def resolve_evidence_path(run_dir: Path) -> Path:
    direct = run_dir / "evidence.jsonl"
    if direct.exists():
        return direct
    return run_dir / "evidence" / "evidence.jsonl"


def select_interview_items(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Pick records worth verifying in interviews: weak/medium user pain and
    decision questions first, then any remaining weak/medium relevant record."""
    relevant = [
        record
        for record in records
        if record.get("relevance") != "irrelevant"
        and record.get("evidence_type") != "irrelevant"
        and record.get("strength") in STRENGTHS_FOR_INTERVIEW
    ]
    pain = [record for record in relevant if record.get("source_intent") == "user_pain"]
    decisions = [record for record in relevant if record.get("comment_intent") == "decision_question" and record not in pain]
    rest = [record for record in relevant if record not in pain and record not in decisions]
    return (pain + decisions + rest)[:limit]


def recruitment_pools(records: list[dict[str, Any]]) -> list[str]:
    pools: list[str] = []
    seen: set[str] = set()
    for record in records:
        source = str(record.get("source", ""))
        url = str(record.get("source_url", ""))
        key = f"{source}|{url}"
        if key in seen or not url:
            continue
        seen.add(key)
        label = SOURCE_LABELS.get(source, source or "unknown source")
        pools.append(f"- {label}: {url}")
    return pools[:10]


def item_label(index: int) -> str:
    return f"E{index}"


def item_summary(record: dict[str, Any]) -> str:
    text = str(record.get("verbatim_quote") or record.get("text") or "").strip()
    text = " ".join(text.split())
    return text[:220] + ("…" if len(text) > 220 else "")


def write_screener(out_dir: Path, records: list[dict[str, Any]], topic: str, segment: str) -> None:
    lines = [
        "# Interview Screener",
        "",
        f"- Topic: {topic}",
        f"- Segment under test: {segment}",
        "",
        "## Who To Recruit",
        "",
        "Recruit people who have *experienced* the problem recently, not people who find the idea interesting. Prioritize the authors and audiences visible in the evidence below.",
        "",
        "## Recruitment Pools From The Evidence",
        "",
        *recruitment_pools(records),
        "",
        "## Screening Questions",
        "",
        "1. When did you last face [the painful job from the evidence]? (Disqualify: never, or more than 12 months ago.)",
        "2. What did you do about it at the time? (Disqualify: nothing — no workaround means weak pain.)",
        "3. Are you the person who would decide and pay for a fix? (Disqualify: no, when the buyer matters for this hypothesis.)",
        "",
        "## Quotas",
        "",
        "- Target 5–8 completed interviews before drawing any conclusion.",
        "- Stop recruiting from a pool when two consecutive interviews add no new information.",
    ]
    (out_dir / "interview-screener.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_guide(out_dir: Path, items: list[dict[str, Any]], topic: str, segment: str) -> None:
    lines = [
        "# Interview Guide",
        "",
        f"- Topic: {topic}",
        f"- Segment under test: {segment}",
        "",
        "## Rules",
        "",
        "- Ask about past behavior, not future intentions. `Tell me about the last time…` beats `Would you use…`.",
        "- Never pitch the solution. The moment you describe your idea, the answer stops being evidence.",
        "- Public posts behind each probe are leads, not claims — treat every item as unverified until a real user confirms it.",
        "- Record verbatim phrases; they feed positioning later.",
        "",
        "## Opening",
        "",
        "1. Walk me through the last time you dealt with [the job]. What triggered it?",
        "2. What was the hardest part? What did it cost you in time, money, or risk?",
        "",
        "## Evidence-Traced Probes",
        "",
    ]
    for index, record in enumerate(items, start=1):
        label = item_label(index)
        url = record.get("source_url", "")
        strength = record.get("strength", "weak")
        lines.extend(
            [
                f"### {label} — verify this public signal ({strength} evidence)",
                "",
                f"> {item_summary(record)}",
                "",
                f"- Source: {url}",
                "- Probe: `Does this match anything you've experienced? Tell me about the last time.`",
                "- If confirmed: `What did you do about it? What did that workaround cost you?`",
                "- If refuted: `What actually happened in your case?`",
                "- Capture: does their language match the public phrasing, and is there spend, risk, or lost time attached?",
                "",
            ]
        )
    lines.extend(
        [
            "## Closing",
            "",
            "1. If you could change one thing about how you handle this today, what would it be?",
            "2. Who else do you know who struggles with this? (Recruitment chain.)",
        ]
    )
    (out_dir / "interview-guide.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tracker(out_dir: Path, items: list[dict[str, Any]]) -> None:
    lines = [
        "# Interview Tracker",
        "",
        "One row per interview per evidence item tested. A signal needs at least 3 independent confirmations before it can be treated as more than a lead, and one clear refutation demotes it below the public post that produced it.",
        "",
        "| Interview | Date | Participant fits segment? | Evidence item | Result (confirmed / refuted / unclear) | Verbatim / notes |",
        "|---|---|---|---|---|---|",
    ]
    for index, record in enumerate(items, start=1):
        lines.append(f"|  |  |  | {item_label(index)} |  |  |")
    lines.extend(
        [
            "",
            "## Tally",
            "",
            "| Evidence item | Confirmations | Refutations | Verdict |",
            "|---|---|---|---|",
        ]
    )
    for index, record in enumerate(items, start=1):
        lines.append(f"| {item_label(index)} | 0 | 0 | open |")
    (out_dir / "interview-tracker.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build interview screener, guide, and tracker from an evidence run.")
    parser.add_argument("--run-dir", required=True, help="Evidence run directory (or market-discovery run root).")
    parser.add_argument("--limit", type=int, default=8, help="Maximum evidence items to trace into the guide.")
    parser.add_argument("--topic", default="", help="Override topic label (otherwise read from summary.json).")
    parser.add_argument("--segment", default="", help="Override segment label (otherwise read from summary.json).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        print(f"error: run directory does not exist: {run_dir}", file=sys.stderr)
        return 1

    evidence_path = resolve_evidence_path(run_dir)
    records = read_jsonl(evidence_path)
    if not records:
        print(f"error: no evidence records found at {evidence_path}", file=sys.stderr)
        return 1

    summary = {}
    for candidate in (run_dir / "summary.json", run_dir / "evidence" / "summary.json"):
        if candidate.exists():
            try:
                summary = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                summary = {}
            break

    topic = args.topic or str(summary.get("topic", run_dir.parent.name))
    segment = args.segment or str(summary.get("customer_segment", "")) or "[unresolved: market discovery]"

    items = select_interview_items(records, args.limit)
    if not items:
        print("error: no weak/medium relevant records to trace into interviews", file=sys.stderr)
        return 1

    out_dir = run_dir / "interview"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_screener(out_dir, records, topic, segment)
    write_guide(out_dir, items, topic, segment)
    write_tracker(out_dir, items)

    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "interview_dir": str(out_dir),
                "records_total": len(records),
                "items_traced": len(items),
                "outputs": {
                    "screener": str(out_dir / "interview-screener.md"),
                    "guide": str(out_dir / "interview-guide.md"),
                    "tracker": str(out_dir / "interview-tracker.md"),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
