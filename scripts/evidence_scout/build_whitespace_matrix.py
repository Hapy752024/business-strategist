#!/usr/bin/env python3
"""Scaffold a pains × competitors whitespace matrix.

Demand-side rows come from an evidence run (`evidence.jsonl`: user-pain and
decision records); supply-side columns come from competitor discovery
(`competitors.json`). Cells start as `unknown` — the analyst fills them with
evidence-backed ratings (`covered`, `partial`, `gap`). A column full of
`unknown` means unscored, not unserved.

Usage:
  python3 scripts/evidence_scout/build_whitespace_matrix.py \
      --topic "<topic>" --evidence-jsonl <path> --competitors-json <path> \
      [--out <path>] [--pains 8] [--competitors 10]

Default output: projects/<project-slug>/market_research/solution_alternatives/whitespace-matrix.md
No network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    safe = "-".join(part for part in safe.split("-") if part)
    return safe[:80] or "topic"


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


def select_pains(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    relevant = [
        record
        for record in records
        if record.get("relevance") != "irrelevant" and record.get("evidence_type") != "irrelevant"
    ]
    pain = [record for record in relevant if record.get("source_intent") == "user_pain"]
    decisions = [
        record
        for record in relevant
        if record.get("comment_intent") == "decision_question" and record not in pain
    ]
    rest = [record for record in relevant if record not in pain and record not in decisions]

    selected: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for record in pain + decisions + rest:
        text = " ".join(str(record.get("text") or "").lower().split())[:120]
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)
        selected.append(record)
        if len(selected) >= limit:
            break
    return selected


def load_competitors(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    items = data if isinstance(data, list) else []
    competitors: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        lane = item.get("primary_lane")
        if lane is not None and (lane != "competitive_market" or item.get("verification_status") != "verified"):
            continue
        name = str(item.get("name") or item.get("domain") or item.get("url") or "").strip()
        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())
        competitors.append(
            {
                "name": name,
                "url": str(item.get("url", "")),
                "type": str(item.get("competitor_type_hint", "unclassified")),
                "lane": str(item.get("primary_lane", "competitive_market")),
            }
        )
        if len(competitors) >= limit:
            break
    return competitors


def pain_label(record: dict[str, Any], index: int) -> str:
    return f"P{index}"


def pain_summary(record: dict[str, Any]) -> str:
    text = " ".join(str(record.get("verbatim_quote") or record.get("text") or "").split())
    return text[:160] + ("…" if len(text) > 160 else "")


def render_matrix(topic: str, pains: list[dict[str, Any]], competitors: list[dict[str, Any]]) -> str:
    header = ["| Pain (from evidence) | Strength | Source |"]
    separator = ["|---|---|---|"]
    for competitor in competitors:
        header[0] += f" {competitor['name']} |"
        separator[0] += "---|"

    lines = [
        f"# Whitespace Matrix — {topic}",
        "",
        "Pains (rows, from public evidence) × competitors (columns, from discovery). Rate each cell from evidence you can point to:",
        "",
        "- `covered` — the competitor explicitly addresses this pain (cite the page/ad)",
        "- `partial` — adjacent coverage only; the pain's trigger or segment is not addressed",
        "- `gap` — no evidence this competitor addresses the pain",
        "- `unknown` — not assessed yet. **A column of `unknown` means unscored, not unserved.**",
        "",
        "Rules: never infer coverage from a competitor's existence or category label; a white spot requires recurring evidence-backed pain (row) plus `gap` across the direct competitors (columns), and it remains a *candidate* until tested.",
        "",
        *header,
        *separator,
    ]
    for index, record in enumerate(pains, start=1):
        row = f"| {pain_label(record, index)}: {pain_summary(record)} | {record.get('strength', '?')} | {record.get('source_url', '')} |"
        row += " unknown |" * len(competitors)
        lines.append(row)

    lines.extend(
        [
            "",
            "## Candidate White Spots",
            "",
            "List only rows rated `gap` for every direct competitor, each with the pain's severity × frequency score and the cheapest test to confirm the spot is real (not just unscored):",
            "",
            "1. ",
            "",
            "## Coverage Notes",
            "",
            "- Competitors without a full marketing analysis default to `unknown` — run `competitor-marketing-analyzer` before rating their column.",
            "- Rows with weak single-source pain stay in the matrix but cannot support a white-spot claim alone.",
        ]
    )
    return "\n".join(lines) + "\n"


from workspace import prepare_research_output, resolve_run_dir, cases, research_input_bindings, capture_run_scope


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a pains × competitors whitespace matrix.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--evidence-jsonl", required=True, help="Path to an evidence run's evidence.jsonl.")
    parser.add_argument("--competitors-json", required=True, help="Path to competitors.json from discover_competitors.py.")
    parser.add_argument("--out", default="", help="Output path. Defaults to projects/<project-slug>/market_research/solution_alternatives/whitespace-matrix.md.")
    parser.add_argument('--workspace', default='')
    parser.add_argument('--case', default='')
    parser.add_argument('--source-bindings', default='')
    parser.add_argument("--pains", type=int, default=8, help="Maximum pain rows.")
    parser.add_argument("--competitors", type=int, default=10, help="Maximum competitor columns.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = read_jsonl(Path(args.evidence_jsonl).expanduser().resolve())
    pains = select_pains(records, args.pains)
    if not pains:
        print("error: no relevant evidence records to use as pain rows", file=sys.stderr)
        return 1

    competitors = load_competitors(Path(args.competitors_json).expanduser().resolve(), args.competitors)
    if not competitors:
        print("error: no competitors found; run discover_competitors.py first", file=sys.stderr)
        return 1

    out_path = (
        Path(args.out).expanduser().absolute()
        if args.out
        else ROOT / "projects" / slugify(args.topic) / "market_research" / "solution_alternatives" / "whitespace-matrix.md"
    )
    source_root = cases.locate(Path(args.evidence_jsonl))
    if not args.out and (source_root or args.workspace or args.case):
        case_id = args.case
        if source_root and not case_id and not args.workspace:
            for cid, entry in cases.read_project(source_root)['cases'].items():
                if not entry.get('retired') and Path(args.evidence_jsonl).absolute().is_relative_to(cases.resolve(source_root, cid)):
                    case_id = cid
                    break
        root = cases.locate(Path(args.workspace)) if args.workspace else source_root
        scope = cases.resolve(root, case_id) if root else None
        bindings = research_input_bindings(root, scope, [args.evidence_jsonl, args.competitors_json], args.source_bindings) if root else []
        run, _ = resolve_run_dir(topic=args.topic, workspace_arg=args.workspace or str(source_root or ''),
            case_id=case_id, out_dir='', legacy_output=False, workspace_subdir='market_research/solution_alternatives/runs')
        out_path = run / 'whitespace-matrix.md'
        if root:
            capture_run_scope(run, scope, bindings)
    else:
        prepare_research_output(out_path, workspace_arg=args.workspace, case_id=args.case, is_file=True,
            input_paths=[args.evidence_jsonl, args.competitors_json], source_bindings_file=args.source_bindings)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_matrix(args.topic, pains, competitors), encoding="utf-8")

    print(
        json.dumps(
            {
                "topic": args.topic,
                "pains": len(pains),
                "competitors": len(competitors),
                "output": str(out_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
