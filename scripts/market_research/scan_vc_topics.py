#!/usr/bin/env python3
"""Compare recent Parsers VC funding activity across startup industry tags.

This is investor-activity context, not customer-demand evidence. Each topic is
queried in two equal time windows for round.recorded and investor.joined_round
signals. Output keeps provider signals and caps visible so counts are not
mistaken for complete market totals.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate_apis"))
from common import get_secret, http_get, with_query  # noqa: E402


API_BASE = "https://vcapi.parsers.vc/v2"
USAGE_URL = "https://parsers.vc/api/v1/usage"
DOCS_URL = "https://parsers.vc/api_page/reference/"
SIGNAL_TYPES = ("round.recorded", "investor.joined_round")
EXPANDS = ("subject", "object")


def _headers(key: str) -> dict[str, str]:
    return {"X-Api-Key": key}


def _remaining(response: dict[str, Any]) -> int | None:
    headers = {str(key).lower(): value for key, value in (response.get("headers") or {}).items()}
    for name in ("x-ratelimit-remaining", "x-rate-limit-remaining"):
        try:
            if headers.get(name) is not None:
                return int(headers[name])
        except (TypeError, ValueError):
            pass
    body = response.get("body")
    if not isinstance(body, dict):
        return None
    for path in (("credits", "remaining"), ("rateLimit", "remaining"), ("usage", "remaining")):
        value: Any = body
        for part in path:
            value = value.get(part) if isinstance(value, dict) else None
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            pass
    for name in ("remaining", "creditsRemaining", "rateLimitRemaining"):
        try:
            if body.get(name) is not None:
                return int(body[name])
        except (TypeError, ValueError):
            pass
    return None


def _credit_charge(response: dict[str, Any], record_count: int = 0) -> int:
    headers = {str(key).lower(): value for key, value in (response.get("headers") or {}).items()}
    try:
        return int(headers["x-credits-charged"])
    except (KeyError, TypeError, ValueError):
        return math.ceil(record_count * 0.25 * (1 + 0.25 * len(EXPANDS)))


def _records(body: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [row for row in body if isinstance(row, dict)]
    if isinstance(body, dict):
        for key in keys:
            for candidate in (key, key[:1].upper() + key[1:]):
                value = body.get(candidate)
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
    return []


def _topic_label(row: dict[str, Any]) -> str:
    return str(row.get("value") or row.get("Value") or row.get("label") or row.get("Label") or row.get("Name") or row.get("name") or "").strip()


def _token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _match_topics(requested: list[str], available: list[dict[str, Any]]) -> list[str]:
    labels = [_topic_label(row) for row in available]
    selected: list[str] = []
    for query in requested:
        normalized = _token(query)
        matches = [label for label in labels if _token(label) == normalized]
        if not matches:
            matches = [label for label in labels if normalized in _token(label) or _token(label) in normalized]
        if not matches:
            raise ValueError(f"No Parsers VC industry tag matched {query!r}; use one of: {', '.join(labels[:30])}")
        for label in matches:
            if label not in selected:
                selected.append(label)
    return selected


def _windows(as_of: date, days: int) -> dict[str, tuple[date, date]]:
    current_start = as_of - timedelta(days=days - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return {
        "current": (current_start, as_of),
        "previous": (previous_start, previous_end),
    }


def _query_signals(key: str, topic: str, country: str | None, period: tuple[date, date], signal_type: str, limit: int) -> dict[str, Any]:
    params = {
        "types": signal_type,
        "industry": topic,
        "country": country,
        "occurredSince": period[0].isoformat(),
        "occurredUntil": period[1].isoformat(),
        "order": "desc",
        "limit": limit,
        "expand": ",".join(EXPANDS),
    }
    url = with_query(f"{API_BASE}/signals", params)
    response = http_get(url, headers=_headers(key), timeout=30)
    body = response.get("body")
    if not response.get("ok"):
        detail = body.get("error") if isinstance(body, dict) else response.get("error")
        raise RuntimeError(f"Parsers VC request failed ({response.get('status_code')}): {detail or response.get('error')}")
    rows = _records(body, "signals", "items", "results", "data")
    more = bool(body.get("hasMore")) if isinstance(body, dict) else False
    return {
        "type": signal_type,
        "window": {"from": period[0].isoformat(), "through": period[1].isoformat()},
        "limit": limit,
        "returned": len(rows),
        "capped": more or len(rows) >= limit,
        "next_cursor_available": bool(body.get("nextCursor")) if isinstance(body, dict) else False,
        "credits_charged": _credit_charge(response, len(rows)),
        "signals": rows,
        "request": {"endpoint": f"{API_BASE}/signals", "parameters": params},
    }


def scan(args: argparse.Namespace) -> dict[str, Any]:
    _name, key = get_secret("PARSERSVC_API_KEY")
    if not key:
        raise RuntimeError("Missing PARSERSVC_API_KEY. Set it in the environment, project .secrets, or ~/.secrets.")

    usage = http_get(USAGE_URL, headers=_headers(key), timeout=20)
    if not usage.get("ok"):
        body = usage.get("body")
        detail = body.get("error") if isinstance(body, dict) else usage.get("error")
        raise RuntimeError(f"Could not read Parsers VC credit balance ({usage.get('status_code')}): {detail or usage.get('error')}")
    remaining = _remaining(usage)
    if remaining is None:
        raise RuntimeError("Parsers VC did not report remaining credits; refusing to make metered topic queries without a balance.")
    if remaining < 1:
        raise RuntimeError("No Parsers VC credits remain; no topic queries were made.")

    categories_url = with_query(f"{API_BASE}/categories/industry", {"entity": "startups", "top": 100})
    categories_response = http_get(categories_url, headers=_headers(key), timeout=30)
    if not categories_response.get("ok"):
        body = categories_response.get("body")
        detail = body.get("error") if isinstance(body, dict) else categories_response.get("error")
        raise RuntimeError(f"Could not load industry tags ({categories_response.get('status_code')}): {detail or categories_response.get('error')}")
    available = _records(categories_response.get("body"), "categories", "items", "results", "data")
    if not available:
        raise RuntimeError("Parsers VC returned no industry-tag catalogue; refusing to guess topic filters.")
    category_charge = 1
    if args.topic:
        topics = _match_topics(args.topic, available)
        discovery = "user-specified topics matched to provider industry tags"
    else:
        topics = []
        for row in available:
            label = _topic_label(row)
            if label and label not in topics:
                topics.append(label)
            if len(topics) >= args.max_topics:
                break
        discovery = "top startup industry tags by provider catalogue count"

    if not topics:
        raise RuntimeError("No topics selected after resolving the Parsers VC industry catalogue.")
    # Two event types x two equal-length periods. The estimate includes the
    # API's documented 0.25 per signal and 25% per expand, rounded per call.
    estimated = category_charge + len(topics) * 4 * math.ceil(args.signals_per_query * 0.25 * (1 + 0.25 * len(EXPANDS)))
    if estimated > args.max_credits:
        raise RuntimeError(f"Estimated spend {estimated} credits exceeds --max-credits {args.max_credits}; reduce topics or per-query limit.")
    if estimated > remaining:
        raise RuntimeError(f"Estimated spend {estimated} credits exceeds the reported remaining balance ({remaining}); no signal queries were made.")

    today = datetime.now(timezone.utc).date()
    windows = _windows(today, args.window_days)
    topics_out = []
    credits = category_charge
    for topic in topics:
        periods: dict[str, dict[str, Any]] = {}
        for period_name, period in windows.items():
            calls = []
            for signal_type in SIGNAL_TYPES:
                result = _query_signals(key, topic, args.country, period, signal_type, args.signals_per_query)
                credits += result["credits_charged"]
                calls.append(result)
                if credits > args.max_credits:
                    raise RuntimeError("Actual reported credits exceeded --max-credits; stopped before remaining queries.")
            rounds = next((item for item in calls if item["type"] == "round.recorded"), {})
            investor_events = next((item for item in calls if item["type"] == "investor.joined_round"), {})
            amounts = [row.get("amount") for row in rounds.get("signals", []) if isinstance(row.get("amount"), (int, float))]
            periods[period_name] = {
                "round_signal_count": rounds.get("returned", 0),
                "investor_join_signal_count": investor_events.get("returned", 0),
                "disclosed_amount_sum_usd_sample": sum(amounts) if amounts else None,
                "round_query_capped": rounds.get("capped", False),
                "investor_query_capped": investor_events.get("capped", False),
                "queries": calls,
            }
        current = periods["current"]
        previous = periods["previous"]
        current_count = current["round_signal_count"]
        previous_count = previous["round_signal_count"]
        censored = any(period[f"{kind}_query_capped"] for period in periods.values() for kind in ("round", "investor"))
        growth = None if previous_count == 0 else round((current_count - previous_count) / previous_count, 3)
        if censored:
            signal = "inconclusive_due_to_sample_cap"
        elif previous_count == 0 and current_count >= 2:
            signal = "emerging_activity_from_zero_baseline"
        elif previous_count > 0 and current_count >= 3 and growth is not None and growth >= 0.25:
            signal = "rising_activity_heuristic"
        elif previous_count >= 3 and growth is not None and growth <= -0.25:
            signal = "cooling_activity_heuristic"
        elif current_count or previous_count:
            signal = "activity_observed_no_clear_acceleration"
        else:
            signal = "no_activity_observed_in_sample"
        topics_out.append({
            "industry_tag": topic,
            "current_rounds": current_count,
            "previous_rounds": previous_count,
            "round_count_change_fraction": growth,
            "current_investor_join_signals": current["investor_join_signal_count"],
            "previous_investor_join_signals": previous["investor_join_signal_count"],
            "current_disclosed_amount_sum_usd_sample": current["disclosed_amount_sum_usd_sample"],
            "previous_disclosed_amount_sum_usd_sample": previous["disclosed_amount_sum_usd_sample"],
            "activity_hint": signal,
            "sample_capped": censored,
            "periods": periods,
        })
    topics_out.sort(key=lambda row: (row["current_rounds"], row["current_investor_join_signals"]), reverse=True)
    return {
        "schema_version": "1.0",
        "provider": "Parsers VC",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "as_of_date_utc": today.isoformat(),
        "query_scope": {"country": args.country, "industry_tags": topics, "discovery": discovery},
        "window_days": args.window_days,
        "windows": {name: {"from": bounds[0].isoformat(), "through": bounds[1].isoformat()} for name, bounds in windows.items()},
        "credits": {"remaining_before_queries": remaining, "estimated_maximum": estimated, "reported_or_estimated_spent": credits, "max_credits": args.max_credits},
        "ranking_method": "Descending current round-recorded signal count, then investor-joined-round signal count. Activity hints use explicit 25%/minimum-count heuristics; they are not a validated definition of a hot market.",
        "topics": topics_out,
        "evidence_limits": [
            "Provider coverage and industry tagging may be incomplete or inconsistent; this scan only covers the returned topic tags and queried periods.",
            "A capped signal query is a lower bound; activity hints are suppressed when any topic-period query hits its sample cap.",
            "Amounts are disclosed amounts in sampled round-recorded signals only; undisclosed or missing amounts are excluded.",
            "VC attention/funding is a capital-market signal, not customer pain, willingness to pay, market size, or evidence that this founder can raise.",
            "Verify material rounds and investor participation against company/investor announcements or filings before making claims.",
        ],
        "provider_docs": DOCS_URL,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan VC funding activity by topic using Parsers VC signals.")
    parser.add_argument("--topic", action="append", default=[], help="Provider industry tag to check; repeat. Without this, scan top startup industry tags.")
    parser.add_argument("--country", help="Optional Parsers VC country filter, e.g. Germany or United States.")
    parser.add_argument("--max-topics", type=int, default=12, help="Topics in automatic scan (1-50).")
    parser.add_argument("--window-days", type=int, default=365, help="Length of each adjacent period (30-1095 days).")
    parser.add_argument("--signals-per-query", type=int, default=20, help="Maximum returned signals per topic, period and signal type (1-200).")
    parser.add_argument("--max-credits", type=int, default=400, help="Hard estimated/observed Parsers VC credit ceiling for this run.")
    parser.add_argument("--out", type=Path, help="Optional JSON output path; defaults to stdout.")
    args = parser.parse_args()
    if not 1 <= args.max_topics <= 50:
        parser.error("--max-topics must be between 1 and 50")
    if not 30 <= args.window_days <= 1095:
        parser.error("--window-days must be between 30 and 1095")
    if not 1 <= args.signals_per_query <= 200:
        parser.error("--signals-per-query must be between 1 and 200")
    if args.max_credits < 1:
        parser.error("--max-credits must be positive")
    try:
        result = scan(args)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
