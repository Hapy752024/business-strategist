#!/usr/bin/env python3
"""Turn subreddits discovered with the Dialog MCP into Reddit query-plan rows.

Dialog is used only to find communities; it is never an evidence source. The rows
produced here send collection back through the existing Reddit API collector
(`collect.py --query-plan`), which captures, hashes and reviews posts under the
normal evidence contracts. Reddit search treats `subreddit:<Name>` as a filter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_]{1,20}$')


def _clean(name: str) -> str:
    name = name.strip()
    name = re.sub(r'^/?r/', '', name)
    if not NAME.fullmatch(name):
        raise ValueError(f'invalid subreddit name: {name!r}')
    return name


def names_from_dialog(payload: dict, min_confidence: float = 0.0) -> list[str]:
    """Read subreddit names from a saved Dialog discover_subreddits result."""
    rows = payload.get('results') or payload.get('subreddits') or []
    out = []
    for row in rows:
        name = row.get('name') if isinstance(row, dict) else row
        score = row.get('confidence', 1.0) if isinstance(row, dict) else 1.0
        if name and score >= min_confidence:
            out.append(str(name))
    return out


def build_rows(subreddits: list[str], keywords: list[str], locale: str, intent: str) -> list[dict]:
    seen, rows = set(), []
    for raw in subreddits:
        name = _clean(raw)
        for keyword in keywords:
            keyword = ' '.join(keyword.split())
            if not keyword:
                continue
            query = f'{keyword} subreddit:{name}'
            key = query.casefold()
            if key in seen:
                continue
            seen.add(key)
            ident = 'dialog-' + hashlib.sha256(key.encode()).hexdigest()[:10]
            rows.append({'query_id': ident, 'candidate_id': ident, 'query': query, 'provider': 'reddit',
                         'locale': locale, 'intent': intent, 'source_family': 'reddit',
                         'seed_origin': 'source_derived', 'seed_locators': [f'dialog:discover_subreddits:{name}'],
                         'rationale': f'Community r/{name} found by Dialog semantic discovery; posts are collected and reviewed through the Reddit API route.'})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--subreddits', help='Comma-separated names, with or without r/')
    src.add_argument('--dialog-json', type=Path, help='Saved discover_subreddits output')
    ap.add_argument('--min-confidence', type=float, default=0.0)
    ap.add_argument('--keywords', required=True, help='Comma-separated customer-language phrases')
    ap.add_argument('--locale', required=True, help='COUNTRY:language, e.g. DE:de')
    ap.add_argument('--intent', default='pain')
    ap.add_argument('--plan', type=Path, help='Existing query plan to append to')
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args(argv)
    names = a.subreddits.split(',') if a.subreddits else names_from_dialog(json.loads(a.dialog_json.read_text()), a.min_confidence)
    rows = build_rows(names, a.keywords.split(','), a.locale, a.intent)
    plan = json.loads(a.plan.read_text()) if a.plan else {'schema_version': 1, 'revision': 'dialog', 'queries': []}
    existing = {r['query'].casefold() for r in plan['queries']}
    plan['queries'] += [r for r in rows if r['query'].casefold() not in existing]
    if a.plan:
        plan['revision'] = f"{plan['revision']}+dialog-subreddits"
    schema = json.loads((ROOT / 'schemas/pain-query-plan.schema.json').read_text())
    errors = [e.message for e in Draft202012Validator(schema).iter_errors(plan)]
    if errors:
        raise SystemExit('invalid query plan: ' + errors[0])
    if a.out.exists():
        raise SystemExit('choose a fresh output file')
    a.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')
    print(a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
