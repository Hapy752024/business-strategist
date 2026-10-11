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
import hashlib
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate_apis"))
from common import get_secret, http_get, with_query, redact_sensitive  # noqa: E402


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
    body = {str(key)[:1].lower() + str(key)[1:]: value for key, value in body.items()}
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
        return max(1, math.ceil(record_count * 0.25 * (1 + 0.25 * len(EXPANDS))))


def normalize_signal(value):
    """The live API uses PascalCase; retain the internal camelCase contract."""
    if isinstance(value, dict):
        return {key[:1].lower() + key[1:]: normalize_signal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_signal(item) for item in value]
    return value


def _records(body: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [normalize_signal(row) if 'signals' in keys else row for row in body if isinstance(row, dict)]
    if isinstance(body, dict):
        for key in keys:
            for candidate in (key, key[:1].upper() + key[1:]):
                value = body.get(candidate)
                if isinstance(value, list):
                    return [normalize_signal(row) if 'signals' in keys else row for row in value if isinstance(row, dict)]
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


def _query_signals(key: str, topic: str, country: str | None, period: tuple[date, date], signal_type: str, limit: int, cursor: str | None = None) -> dict[str, Any]:
    params = {
        "cursor": cursor,
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
        "next_cursor": body.get("nextCursor") if isinstance(body, dict) else None,
        "response": redact_sensitive(response),
        "credits_charged": _credit_charge(response, len(rows)),
        "signals": rows,
        "request": {"endpoint": f"{API_BASE}/signals", "parameters": params},
    }


def unique_rounds(signals):
    """Corrections and syndicated copies of the same provider round collapse."""
    rounds = {}
    unresolved = []
    for row in signals:
        identity = (row.get('object') or {}).get('id')
        if not identity:
            unresolved.append(row)
            continue
        old = rounds.get(identity)
        if not old or str(row.get('detectedAt', '')) >= str(old.get('detectedAt', '')):
            rounds[identity] = row
    return list(rounds.values()), unresolved


def investor_identity(row):
    """Only explicitly identified investor entities qualify as investor names."""
    for value in (row.get('investor'), row.get('subject'), row.get('object')):
        if isinstance(value, dict) and str(value.get('type', '')).lower() in {'investor', 'fund', 'vc', 'venture_capital'}:
            return value
    return None


def summarize(topic, queries):
    periods = {}
    for period in ('current', 'previous'):
        rounds_query = queries.get(topic + '|' + period + '|round.recorded', {})
        investor_query = queries.get(topic + '|' + period + '|investor.joined_round', {})
        signals = [normalize_signal(row) for page in rounds_query.get('pages', []) for row in page['signals']]
        rounds, unresolved = unique_rounds(signals)
        amounts = [row['amount'] for row in rounds if type(row.get('amount')) in (int, float) and math.isfinite(row['amount']) and row['amount'] >= 0]
        investors = [normalize_signal(row) for page in investor_query.get('pages', []) for row in page['signals']]
        pairs = {((row.get('object') or {}).get('id'), (investor_identity(row) or {}).get('id')) for row in investors}
        stages = {}
        for row in rounds:
            label = row.get('series') or row.get('label') or 'unknown'
            stages[label] = stages.get(label, 0) + 1
        periods[period] = {'round_signal_count': len(rounds), 'unresolved_round_identity_count': len(unresolved),
            'investor_join_signal_count': len({row.get('id') for row in investors if row.get('id')}),
            'unique_investor_round_pairs': len({pair for pair in pairs if all(pair)}),
            'unresolved_investor_identity_count': sum(investor_identity(row) is None for row in investors),
            'unique_companies': len({(row.get('subject') or {}).get('id') for row in rounds if (row.get('subject') or {}).get('id')}),
            'disclosed_amount_sum_usd_sample': sum(amounts) if amounts else None,
            'amount_disclosure_count': len(amounts), 'round_query_capped': not rounds_query.get('complete', False),
            'investor_query_capped': not investor_query.get('complete', False), 'stage_counts': stages,
            'largest_round_share_of_disclosed_sample': max(amounts) / sum(amounts) if amounts and sum(amounts) else None,
            'rounds': rounds, 'queries': [rounds_query, investor_query]}
    current, previous = periods['current'], periods['previous']
    censored = any(p['round_query_capped'] or p['investor_query_capped'] or p['unresolved_round_identity_count'] for p in periods.values())
    a, b = current['round_signal_count'], previous['round_signal_count']
    growth = (a - b) / b if b and not censored else None
    hint = ('inconclusive_due_to_sample_cap' if censored else 'emerging_activity_from_zero_baseline' if not b and a
            else 'rising_activity_heuristic' if growth is not None and growth >= .25 and a >= 3
            else 'cooling_activity_heuristic' if growth is not None and growth <= -.25 and b >= 3
            else 'activity_observed_no_clear_acceleration' if a or b else 'no_activity_observed_in_sample')
    return {'industry_tag': topic, 'current_rounds': a, 'previous_rounds': b,
            'round_count_change_fraction': growth, 'current_investor_join_signals': current['investor_join_signal_count'],
            'previous_investor_join_signals': previous['investor_join_signal_count'],
            'current_disclosed_amount_sum_usd_sample': current['disclosed_amount_sum_usd_sample'],
            'previous_disclosed_amount_sum_usd_sample': previous['disclosed_amount_sum_usd_sample'],
            'activity_hint': hint, 'sample_capped': censored, 'periods': periods}


def scan(args: argparse.Namespace) -> dict[str, Any]:
    _name, key = get_secret('PARSERSVC_API_KEY')
    if not key:
        raise RuntimeError('Missing PARSERSVC_API_KEY. Set it in the environment or ~/.secrets.')
    usage = http_get(USAGE_URL, headers=_headers(key), timeout=20)
    remaining = _remaining(usage) if usage.get('ok') else None
    if remaining is None or remaining < 1:
        raise RuntimeError('Could not establish a positive Parsers VC credit balance; no metered queries made.')
    pricing = http_get(API_BASE + '/pricing', headers=_headers(key), timeout=20)
    if not pricing.get('ok'):
        raise RuntimeError('Cannot check current VC pricing; no metered queries made.')
    rates = pricing.get('body', {}).get('endpoints', [])
    rate = next((row for row in rates if str(row.get('endpoint', '')).lower() in {'get v2/signals', 'get /v2/signals'}), None)
    if not rate:
        raise RuntimeError('Current pricing does not declare the signals rate; no metered query made.')
    base_rate, per_record_rate = float(rate['base_credits']), float(rate['credits_per_record'])
    if not math.isfinite(base_rate) or not math.isfinite(per_record_rate) or base_rate < 0 or per_record_rate < 0:
        raise RuntimeError('Invalid signal pricing; no metered query made.')
    categories = http_get(with_query(API_BASE + '/categories/industry', {'entity': 'startups', 'top': 100}), headers=_headers(key), timeout=30)
    if not categories.get('ok'):
        raise RuntimeError('Could not load provider industry tags.')
    available = _records(categories.get('body'), 'categories', 'items', 'results', 'data', 'values')
    if not available:
        raise RuntimeError('Empty industry catalogue; refusing to guess filters.')
    topics = _match_topics(args.topic, available) if args.topic else list(dict.fromkeys(_topic_label(row) for row in available if _topic_label(row)))[:args.max_topics]
    resume = getattr(args, 'resume', None)
    state = json.loads(resume.read_text()) if resume else {}
    as_of = date.fromisoformat(getattr(args, 'as_of', None) or state.get('as_of_date_utc') or datetime.now(timezone.utc).date().isoformat())
    windows = {name: {'from': bounds[0].isoformat(), 'through': bounds[1].isoformat()} for name, bounds in _windows(as_of, args.window_days).items()}
    scope = {'country': args.country, 'industry_tags': topics, 'window_days': args.window_days,
             'windows': windows, 'signals_per_query': args.signals_per_query}
    signature = hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest()
    if state and state.get('query_signature') != signature:
        raise ValueError('Resume scope changed; topic, geography, periods and page size must match.')
    queries = state.get('queries', {})
    category_headers = {k.lower(): v for k, v in categories.get('headers', {}).items()}
    spent = int(category_headers.get('x-credits-charged', 1))
    balance = remaining - spent
    max_pages = getattr(args, 'max_pages', 1)
    checkpoint = getattr(args, 'checkpoint', None)
    stop_reason = None
    for topic in topics:
        for period, bounds in windows.items():
            for signal_type in SIGNAL_TYPES:
                ident = topic + '|' + period + '|' + signal_type
                query = queries.setdefault(ident, {'pages': [], 'complete': False})
                if query['complete']:
                    continue
                while len(query['pages']) < max_pages:
                    reserve = max(1, math.ceil(base_rate + args.signals_per_query * per_record_rate * (1 + .25 * len(EXPANDS))))
                    if spent + reserve > args.max_credits or reserve > balance:
                        stop_reason = 'credit_budget_or_balance'
                        break
                    cursor = query['pages'][-1].get('next_cursor') if query['pages'] else None
                    try:
                        page = _query_signals(key, topic, args.country,
                            (date.fromisoformat(bounds['from']), date.fromisoformat(bounds['through'])), signal_type, args.signals_per_query, cursor)
                    except RuntimeError as exc:
                        stop_reason = str(redact_sensitive(str(exc)))
                        break
                    # A missing charge header is not sufficient to certify the cost.
                    charge_headers = {k.lower(): v for k, v in page['response'].get('headers', {}).items()}
                    charged = int(charge_headers['x-credits-charged']) if 'x-credits-charged' in charge_headers else reserve
                    spent += charged
                    balance -= charged
                    query['pages'].append(page)
                    query['complete'] = not page['capped']
                    state = {'query_signature': signature, 'as_of_date_utc': as_of.isoformat(), 'queries': queries, 'scope': scope}
                    if checkpoint:
                        checkpoint.parent.mkdir(parents=True, exist_ok=True)
                        temporary = checkpoint.with_suffix(checkpoint.suffix + '.tmp')
                        temporary.write_text(json.dumps(redact_sensitive(state), indent=2))
                        temporary.replace(checkpoint)
                    if query['complete']:
                        break
                    if not page['next_cursor'] or page['next_cursor'] == cursor:
                        query['coverage_gap'] = 'Capped page has no advancing cursor'
                        break
                    if spent > args.max_credits or balance < 0:
                        stop_reason = 'actual_charge_exceeded_reservation'
                        break
                if stop_reason:
                    break
            if stop_reason:
                break
        if stop_reason:
            break
    return {'schema_version': '2.0', 'provider': 'Parsers VC', 'collected_at': datetime.now(timezone.utc).isoformat(),
            'as_of_date_utc': as_of.isoformat(), 'query_scope': scope, 'query_signature': signature, 'queries': queries,
            'window_days': args.window_days, 'windows': windows, 'topics': [summarize(topic, queries) for topic in topics],
            'credits': {'remaining_before_queries': remaining, 'reported_or_reserved_spent': spent, 'max_credits': args.max_credits},
            'pricing_capture': redact_sensitive(pricing), 'stop_reason': stop_reason,
            'evidence_limits': ['Provider coverage is incomplete; capped counts are lower bounds and change is suppressed.',
                'Amounts include disclosed sampled rounds only; overlapping tags must not be summed.',
                'Event dates define the windows; detection dates preserve reporting lag.',
                'The scan deduplicates returned round records; later correction events outside the queried feeds are not audited.',
                'Funding does not establish customer demand, profitability or fundraising fit.',
                'Verify material rounds from company/fund announcements or filings.'], 'provider_docs': DOCS_URL}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan VC funding activity by topic using Parsers VC signals.")
    parser.add_argument("--topic", action="append", default=[], help="Provider industry tag to check; repeat. Without this, scan top startup industry tags.")
    parser.add_argument("--country", help="Optional Parsers VC country filter, e.g. Germany or United States.")
    parser.add_argument("--max-topics", type=int, default=12, help="Topics in automatic scan (1-50).")
    parser.add_argument("--window-days", type=int, default=365, help="Length of each adjacent period (30-1095 days).")
    parser.add_argument("--signals-per-query", type=int, default=20, help="Maximum returned signals per topic, period and signal type (1-200).")
    parser.add_argument("--max-credits", type=int, default=400, help="Hard estimated/observed Parsers VC credit ceiling for this run.")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum pages per topic/window/type; capped results stay lower bounds.")
    parser.add_argument("--as-of", help="Explicit market date, YYYY-MM-DD")
    parser.add_argument("--resume", type=Path, help="Resume a matching saved checkpoint")
    parser.add_argument("--checkpoint", type=Path, help="Persist each completed page atomically")
    parser.add_argument("--out", type=Path, help="Optional JSON output path; defaults to stdout.")
    args = parser.parse_args()
    if not 1 <= args.max_topics <= 50:
        parser.error("--max-topics must be between 1 and 50")
    if not 30 <= args.window_days <= 1095:
        parser.error("--window-days must be between 30 and 1095")
    if not 1 <= args.signals_per_query <= 200:
        parser.error("--signals-per-query must be between 1 and 200")
    if not 1 <= args.max_pages <= 100:
        parser.error("--max-pages must be 1..100")
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
