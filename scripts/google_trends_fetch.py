#!/usr/bin/env python3
"""Fetch Google Trends interest-over-time data with pytrends."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OPTIONAL_VENV_PYTHON = PROJECT_ROOT / ".venvs" / "value-charting" / "bin" / "python"
OPTIONAL_VENV_ROOT = OPTIONAL_VENV_PYTHON.parent.parent


class TrendsError(RuntimeError):
    pass


def maybe_reexec_optional_venv() -> None:
    if not OPTIONAL_VENV_PYTHON.exists():
        return
    try:
        current_prefix = Path(sys.prefix).resolve()
        target_prefix = OPTIONAL_VENV_ROOT.resolve()
    except OSError:
        return
    if current_prefix != target_prefix:
        os.execv(str(OPTIONAL_VENV_PYTHON), [str(OPTIONAL_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])


def import_pytrends():
    try:
        from pytrends.request import TrendReq
    except ImportError as exc:
        maybe_reexec_optional_venv()
        raise TrendsError(
            "Missing dependency: pytrends. Install it in the skill venv with "
            "`pip install pytrends` (optional dependency, see requirements.txt)."
        ) from exc
    return TrendReq


def clean_records(df) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    out = df.reset_index()
    records: list[dict[str, Any]] = []
    for row in out.to_dict(orient="records"):
        cleaned: dict[str, Any] = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                cleaned[str(key)] = value.isoformat()
            elif value != value:
                cleaned[str(key)] = None
            else:
                cleaned[str(key)] = value
        records.append(cleaned)
    return records


def summarize_interest(records: list[dict[str, Any]], keywords: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for keyword in keywords:
        values = [row.get(keyword) for row in records if isinstance(row.get(keyword), (int, float))]
        if not values:
            summary[keyword] = {"status": "no_data"}
            continue
        recent = values[-4:] if len(values) >= 4 else values
        early = values[: max(1, min(4, len(values)))]
        baseline = sum(values) / len(values)
        recent_avg = sum(recent) / len(recent)
        early_avg = sum(early) / len(early)
        summary[keyword] = {
            "points": len(values),
            "average": round(baseline, 2),
            "recent_average": round(recent_avg, 2),
            "early_average": round(early_avg, 2),
            "max": max(values),
            "min": min(values),
            "recent_vs_average_pct": None if baseline == 0 else round((recent_avg / baseline - 1) * 100, 2),
            "recent_vs_early_pct": None if early_avg == 0 else round((recent_avg / early_avg - 1) * 100, 2),
        }
    return summary


def build_payload(keywords: list[str], geo: str, timeframe: str, category: int, gprop: str):
    TrendReq = import_pytrends()
    trends = TrendReq(hl="en-US", tz=360)
    trends.build_payload(keywords, cat=category, timeframe=timeframe, geo=geo, gprop=gprop)
    return trends


def compare(args: argparse.Namespace) -> dict[str, Any]:
    trends = build_payload(args.keyword, args.geo, args.timeframe, args.category, args.gprop)
    records = clean_records(trends.interest_over_time())
    return {
        "type": "google_trends_compare",
        "keywords": args.keyword,
        "geo": args.geo,
        "timeframe": args.timeframe,
        "category": args.category,
        "gprop": args.gprop,
        "summary": summarize_interest(records, args.keyword),
        "records": records,
        "caveat": "Google Trends values are relative search interest, not absolute demand or revenue.",
    }


def related(args: argparse.Namespace) -> dict[str, Any]:
    trends = build_payload([args.keyword], args.geo, args.timeframe, args.category, args.gprop)
    related_queries = trends.related_queries()
    related_topics = trends.related_topics()
    payload = {
        "type": "google_trends_related",
        "keyword": args.keyword,
        "geo": args.geo,
        "timeframe": args.timeframe,
        "category": args.category,
        "gprop": args.gprop,
        "related_queries": {},
        "related_topics": {},
        "caveat": "Related items are discovery leads and require interpretation and verification.",
    }
    for keyword, value in related_queries.items():
        payload["related_queries"][keyword] = {
            "top": clean_records(value.get("top")),
            "rising": clean_records(value.get("rising")),
        }
    for keyword, value in related_topics.items():
        payload["related_topics"][keyword] = {
            "top": clean_records(value.get("top")),
            "rising": clean_records(value.get("rising")),
        }
    return payload


def write_output(result: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
        print(path)
    else:
        print(rendered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Google Trends data.")
    sub = parser.add_subparsers(dest="command", required=True)
    compare_parser = sub.add_parser("compare", help="Fetch interest over time for up to five keywords.")
    compare_parser.add_argument("--keyword", action="append", required=True, help="Keyword to compare. Repeat up to five times.")
    compare_parser.add_argument("--geo", default="", help="Google Trends geo code, e.g. US, SG, DE. Empty means worldwide.")
    compare_parser.add_argument("--timeframe", default="today 3-m", help='Timeframe, e.g. "today 1-m", "today 3-m", "today 12-m".')
    compare_parser.add_argument("--category", type=int, default=0)
    compare_parser.add_argument("--gprop", default="", help="Google property, e.g. news, images, youtube. Empty means web search.")
    compare_parser.add_argument("--output")
    related_parser = sub.add_parser("related", help="Fetch related queries/topics for one keyword.")
    related_parser.add_argument("--keyword", required=True)
    related_parser.add_argument("--geo", default="")
    related_parser.add_argument("--timeframe", default="today 3-m")
    related_parser.add_argument("--category", type=int, default=0)
    related_parser.add_argument("--gprop", default="")
    related_parser.add_argument("--output")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "compare" and len(args.keyword) > 5:
        parser.error("Google Trends supports a maximum of five compared keywords per request.")
    try:
        result = compare(args) if args.command == "compare" else related(args)
        write_output(result, args.output)
        return 0
    except TrendsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: Google Trends request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
