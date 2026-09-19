#!/usr/bin/env python3
"""Build an interview kit from a collected evidence run.

Public evidence needs semantic source review before it can ground interviews.
This script converts accepted firsthand customer records into artifacts under
<run>/interview/:

  - interview-screener.md  — who to recruit, where, and disqualifiers
  - interview-guide.md     — non-leading probe questions traced to evidence
  - interview-tracker.md   — confirmation/refutation log per evidence item

Usage:
  python3 scripts/evidence_scout/build_interview_kit.py --run-dir <run path> [--limit 8]

For market-discovery runs, pass the run root; the script looks for
evidence/evidence.jsonl automatically. No network access. --source-review defaults
to <run>/source-review.json. The review binds evidence_sha256 and target_segment
to reviews containing evidence_id, source_url, status (accepted/rejected/unresolved),
reviewed_segment, segment_relation (target/adjacent/unresolved), journey_stage,
relevance_rationale, voice (customer/operator/context) and firsthand (boolean).
Accepted records require every field. Only target-segment records ground probes. No review means
no output; collection labels alone never authorize interview probes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from build_claim_ledger import stable_id
from reviewed_voice import review_voice, reviewed_view

SOURCE_LABELS = {
    "reddit": "Reddit threads/comments",
    "youtube": "YouTube sources",
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
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError("evidence rows must be JSON objects")
        record["evidence_id"] = stable_id(record)
        records.append(record)
    return records


def resolve_evidence_path(run_dir: Path) -> Path:
    direct = run_dir / "evidence.jsonl"
    if direct.exists():
        return direct
    return run_dir / "evidence" / "evidence.jsonl"


def apply_source_review(
    records: list[dict[str, Any]], evidence_path: Path, review_path: Path, segment: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Validate a source-review sidecar without changing the collected evidence."""
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if not isinstance(review, dict):
        raise ValueError("source review must be an object")
    if review.get("evidence_sha256") != hashlib.sha256(evidence_path.read_bytes()).hexdigest():
        raise ValueError("source review is stale: evidence_sha256 does not match evidence.jsonl")
    if not segment.strip() or review.get("target_segment") != segment:
        raise ValueError("source review target_segment must match the requested customer segment")
    entries = review.get("reviews")
    if not isinstance(entries, list):
        raise ValueError("source review requires a reviews list")
    by_id = {record["evidence_id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate evidence_id values prevent unambiguous source review")
    accepted = []
    seen = set()
    counts = {"accepted": 0, "rejected": 0, "unresolved": 0, "unreviewed": 0}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each source review must be an object")
        evidence_id = entry.get("evidence_id")
        if not isinstance(evidence_id, str) or evidence_id not in by_id or evidence_id in seen:
            raise ValueError("source review has unknown or duplicate evidence_id")
        seen.add(evidence_id)
        record = by_id[evidence_id]
        if not entry.get("source_url") or entry["source_url"] != record.get("source_url"):
            raise ValueError(f"source review URL mismatch for {evidence_id}")
        status = entry.get("status")
        if not isinstance(status, str) or status not in {"accepted", "rejected", "unresolved"}:
            raise ValueError(f"invalid source review status for {evidence_id}")
        if not isinstance(entry.get("relevance_rationale"), str) or not entry["relevance_rationale"].strip():
            raise ValueError(f"source review requires relevance_rationale for {evidence_id}")
        counts[status] += 1
        if status != "accepted":
            continue
        if entry.get("reviewed_segment") != segment:
            raise ValueError(f"reviewed_segment mismatch for {evidence_id}")
        if entry.get("segment_relation") not in ("target", "adjacent", "unresolved"):
            raise ValueError(f"accepted review requires segment_relation target/adjacent/unresolved for {evidence_id}")
        if not isinstance(entry.get("journey_stage"), str) or not entry["journey_stage"].strip():
            raise ValueError(f"accepted review requires journey_stage for {evidence_id}")
        if entry.get("voice") not in ("customer", "former_customer", "prospective_user", "nonadopter", "operator", "context") or type(entry.get("firsthand")) is not bool:
            raise ValueError(f"accepted review requires voice and boolean firsthand for {evidence_id}")
        problems = review_voice(record, entry, segment)
        if problems:
            raise ValueError(f"{evidence_id}: {'; '.join(problems)}")
        accepted.append(reviewed_view(record, entry))
    counts["unreviewed"] = len(records) - len(seen)
    return accepted, counts


def select_interview_items(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Only reviewed firsthand target-segment customer voice can ground an E probe."""
    relevant = [
        record
        for record in records
        if record.get("_source_review", {}).get("status") == "accepted"
        and record["_source_review"].get("voice") in {"customer", "former_customer", "prospective_user", "nonadopter"}
        and record["_source_review"].get("firsthand") is True
        and record["_source_review"].get("segment_relation") == "target"
    ]
    # Reviewed recommendation-changing cases cannot disappear behind a record cap.
    selected = [r for r in relevant if r["_source_review"].get("material_counterexample") is True]
    seen: set[tuple[str, str]] = set()
    def dimensions(record):
        review = record["_source_review"]
        return {(key, str(value)) for key, value in {
            "voice": review.get("voice"), "stage": review.get("journey_stage"),
            "outcome": review.get("outcome_status") or record.get("evidence_type"),
            "job": review.get("job"), "alternative": review.get("current_alternative"),
        }.items() if value}
    for record in selected:
        seen |= dimensions(record)
    remaining = [r for r in relevant if r not in selected]
    while remaining and len(selected) < limit:
        record = max(remaining, key=lambda r: len(dimensions(r) - seen))
        selected.append(record); seen |= dimensions(record); remaining.remove(record)
    return selected


def recruitment_pools(records: list[dict[str, Any]]) -> list[str]:
    pools: list[str] = []
    seen: set[str] = set()
    for record in records:
        review = record.get("_source_review", {})
        if review.get("status") != "accepted":
            continue
        source = str(record.get("source", ""))
        url = str(record.get("source_url", ""))
        key = f"{source}|{url}"
        if key in seen or not url:
            continue
        seen.add(key)
        label = SOURCE_LABELS.get(source, source or "unknown source")
        relation_label = {
            "target": "target segment",
            "adjacent": "adjacent segment; comparator context only",
            "unresolved": "segment unresolved; discovery context only",
        }[review["segment_relation"]]
        pools.append(f"- {label} ({review['voice']} voice; {relation_label}; discovery lead only): {url}")
    return pools[:10]


def item_label(index: int) -> str:
    return f"E{index}"


def item_summary(record: dict[str, Any]) -> str:
    text = str(record.get("verbatim_quote") or record.get("text") or "").strip()
    text = " ".join(text.split())
    return text[:220] + ("…" if len(text) > 220 else "")


def review_limits(counts: dict[str, int], items_traced: int) -> str:
    return (
        f"Source-review coverage: {counts['accepted']} accepted; {counts['rejected']} rejected; "
        f"{counts['unresolved']} unresolved; {counts['unreviewed']} unreviewed. "
        f"Only {items_traced} accepted firsthand target-segment customer records are traced into probes. "
        "Rejected, unresolved and unreviewed records are excluded from probes and discovery leads. "
        "Other accepted voices and adjacent or unresolved segments are discovery context only; "
        "they cannot establish target-segment pain or sentiment. Review acceptance establishes relevance, "
        "not truth, representativeness, customer demand or permission to contact anyone."
    )


def write_screener(out_dir: Path, records: list[dict[str, Any]], topic: str, segment: str, limits: str) -> None:
    lines = [
        "# Interview Screener",
        "",
        f"- Topic: {topic}",
        f"- Segment under test: {segment}",
        f"- {limits}",
        "",
        "## Who To Recruit",
        "",
        "Recruit people who have *experienced* the job recently, including those who solved it without difficulty. Screen for the target segment and incident, not agreement with the proposed pain.",
        "",
        "## Discovery Leads From Accepted Evidence",
        "",
        "These sources suggest places to investigate; they do not establish reachable or eligible participants or permission to message, post, scrape contacts or advertise. Verify access and local/community rules before outreach; request opt-in introductions where suitable.",
        "",
        *recruitment_pools(records),
        "",
        "## Screening Questions",
        "",
        "1. When did you last face [the job from the evidence]? (Disqualify: outside a recency window selected for this job before recruitment; record the reason.)",
        "2. What did you do about it at the time? If nothing: was there no need, or were you blocked by cost, eligibility, access or another constraint? Do not automatically disqualify someone without a workaround.",
        "3. Are you the person who would decide and pay for a fix? (Disqualify: no, when the buyer matters for this hypothesis.)",
        "",
        "## Quotas",
        "",
        "- Choose an initial learning batch and contrasting cases before recruitment; record segment and channel bias.",
        "- Review new information and counterexamples after each batch. Interview count alone does not validate demand or justify stopping.",
    ]
    (out_dir / "interview-screener.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_guide(out_dir: Path, items: list[dict[str, Any]], topic: str, segment: str, limits: str) -> None:
    lines = [
        "# Interview Guide",
        "",
        f"- Topic: {topic}",
        f"- Segment under test: {segment}",
        f"- {limits}",
        "",
        "## Rules",
        "",
        "- Ask about past behavior, not future intentions. `Tell me about the last time…` beats `Would you use…`.",
        "- Never pitch the solution. The moment you describe your idea, the answer stops being evidence.",
        "- Start with the participant's own incident. Use reviewed public sources privately to identify gaps after their unaided account; do not read quotes and ask them to agree.",
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
        review = record["_source_review"]
        lines.extend(
            [
                f"### {label} — verify this public signal ({strength} evidence)",
                "",
                f"> {item_summary(record)}",
                "",
                f"- Source: {url}",
                f"- Evidence ID: {record['evidence_id']}; reviewed voice: {review['voice']}; firsthand: true; segment relation: target.",
                f"- Reviewed journey stage: {review['journey_stage']}",
                f"- Relevance rationale: {review['relevance_rationale']}",
                "- Probe: `What happened next at this stage in your own incident? What, if anything, was difficult?`",
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


def write_tracker(out_dir: Path, items: list[dict[str, Any]], limits: str) -> None:
    lines = [
        "# Interview Tracker",
        "",
        limits,
        "",
        "One row per interview per evidence item tested. Record independent incidents, segment fit, severity, alternatives and counterexamples. Agree decision criteria for each hypothesis before evaluating results; no fixed confirmation count automatically validates a claim. A refutation may reveal a segment boundary rather than erase other experiences.",
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


from workspace import prepare_research_output, cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build interview screener, guide, and tracker from an evidence run.")
    parser.add_argument("--run-dir", required=True, help="Evidence run directory (or market-discovery run root).")
    parser.add_argument("--source-bindings", default="", help="Explicit shared-input applicability bindings.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum evidence items to trace into the guide.")
    parser.add_argument("--topic", default="", help="Override topic label (otherwise read from summary.json).")
    parser.add_argument("--segment", default="", help="Override segment label (otherwise read from summary.json).")
    parser.add_argument("--source-review", help="Review JSON path (default: <run>/source-review.json), bound to evidence SHA256 and target segment.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().absolute()
    if not run_dir.is_dir():
        print(f"error: run directory does not exist: {run_dir}", file=sys.stderr)
        return 1

    evidence_path = resolve_evidence_path(run_dir)
    try:
        records = read_jsonl(evidence_path)
    except (OSError, ValueError) as error:
        print(f"error: invalid evidence: {error}", file=sys.stderr)
        return 1
    if not records:
        print(f"error: no evidence records found at {evidence_path}", file=sys.stderr)
        return 1

    summary_path = None
    summary = {}
    for candidate in (run_dir / "summary.json", run_dir / "evidence" / "summary.json"):
        if candidate.exists():
            summary_path = candidate
            try:
                summary = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                summary = {}
            if not isinstance(summary, dict):
                summary = {}
            break

    topic = args.topic or str(summary.get("topic", run_dir.parent.name))
    segment = args.segment or str(summary.get("customer_segment", "")) or "[unresolved: market discovery]"

    if args.limit < 1:
        print("error: --limit must be positive", file=sys.stderr)
        return 1
    review_path = Path(args.source_review).expanduser().absolute() if args.source_review else run_dir / "source-review.json"
    try:
        accepted, review_counts = apply_source_review(records, evidence_path, review_path, segment)
    except (OSError, ValueError) as error:
        print(f"error: source review required and must be valid: {error}", file=sys.stderr)
        return 1
    items = select_interview_items(accepted, args.limit)
    if not items:
        print(
            "error: no accepted firsthand customer records to trace into interviews; "
            + review_limits(review_counts, 0), file=sys.stderr,
        )
        return 1

    limits = review_limits(review_counts, len(items))
    out_dir = run_dir / "interview"
    if cases.locate(run_dir):
        import uuid
        out_dir = run_dir / ("interview-" + uuid.uuid4().hex)
    prepare_research_output(out_dir, input_paths=[evidence_path, review_path, summary_path], source_bindings_file=args.source_bindings)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_screener(out_dir, accepted, topic, segment, limits)
    write_guide(out_dir, items, topic, segment, limits)
    write_tracker(out_dir, items, limits)
    selected_ids = {record["evidence_id"] for record in items}
    selection = {
        "requested_limit": args.limit, "selected_count": len(items),
        "policy": "Preserve all reviewed material counterexamples, then maximize distinct perspectives, jobs, stages, alternatives and outcomes; count is not validation.",
        "decisions": [{"evidence_id": record["evidence_id"],
                       "selected": record["evidence_id"] in selected_ids,
                       "reason": "material counterexample" if record["_source_review"].get("material_counterexample") and record["evidence_id"] in selected_ids else "context/perspective coverage" if record["evidence_id"] in selected_ids else "not eligible or lower incremental diversity within requested limit; remains in research ledger"}
                      for record in accepted],
    }
    (out_dir / "interview-selection.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "interview_dir": str(out_dir),
                "records_total": len(records),
                "items_traced": len(items),
                "source_review": str(review_path),
                "source_review_counts": review_counts,
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
