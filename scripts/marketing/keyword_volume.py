"""Google Ads keyword volumes via DataForSEO Keywords Data `google_ads/search_volume/live`.

Volumes are bucketed Google Ads estimates and a demand proxy, not customer pain. Unknown stays null.
Cost is estimated and printed before any call; `--max-keywords` (default 200) refuses larger requests
before touching the network. One task holds up to 1000 keywords and is billed per task.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.validate_apis.common import get_secret

ENDPOINT = 'https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live'
MAX_PER_TASK = 1000
# Observed live cost per task (USD, 2026-10-30 check); the real cost is read from each response.
ASSUMED_COST_PER_TASK = 0.09
DEFAULT_CAP = 200


class MissingCredentials(RuntimeError):
    status = 'missing_credentials'


class CapExceeded(RuntimeError):
    status = 'cap_exceeded'


def credentials() -> tuple[str | None, str | None]:
    return get_secret('DATAFORSEO_LOGIN', 'DATAFORSEO_USERNAME')[1], get_secret('DATAFORSEO_PASSWORD')[1]


def estimate_cost(count: int) -> float:
    return round(math.ceil(count / MAX_PER_TASK) * ASSUMED_COST_PER_TASK, 4)


def _post(url: str, payload: list, auth: tuple[str, str]) -> dict:
    token = base64.b64encode(f'{auth[0]}:{auth[1]}'.encode()).decode()
    req = urllib.request.Request(url, json.dumps(payload).encode(), {'Authorization': 'Basic ' + token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _dedupe(keywords: list[str]) -> list[str]:
    seen, out = set(), []
    for k in keywords:
        key = ' '.join(k.split()).casefold()
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def fetch_volumes(keywords: list[str], location_code: int, language_code: str, *,
                  max_keywords: int = DEFAULT_CAP, post=None) -> list[dict]:
    """Return one row per distinct keyword: keyword, volume, cpc, competition (0-100 index), source, fetched_at, cost."""
    terms = _dedupe(keywords)
    if len(terms) > max_keywords:
        raise CapExceeded(f'{len(terms)} keywords exceed --max-keywords {max_keywords}; nothing was sent')
    login, password = credentials()
    if not login or not password:
        raise MissingCredentials('DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD are required')
    post = post or _post
    found: dict[str, dict] = {}
    for i in range(0, len(terms), MAX_PER_TASK):
        batch = terms[i:i + MAX_PER_TASK]
        body = post(ENDPOINT, [{'keywords': batch, 'location_code': location_code, 'language_code': language_code}], (login, password))
        for task in body.get('tasks') or []:
            if task.get('status_code') != 20000:
                raise RuntimeError(f"DataForSEO task failed: {task.get('status_code')} {task.get('status_message')}")
            cost = task.get('cost')
            for item in task.get('result') or []:
                found[' '.join(str(item.get('keyword', '')).split()).casefold()] = {**item, '_cost': cost}
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    rows = []
    for term in terms:
        item = found.get(term, {})
        rows.append({'keyword': term, 'volume': item.get('search_volume'), 'cpc': item.get('cpc'),
                     'competition': item.get('competition_index'), 'source': 'dataforseo', 'fetched_at': now,
                     'location_code': location_code, 'language_code': language_code, 'task_cost': item.get('_cost')})
    return rows


def apply_to_map(document: dict, volumes: list[dict]) -> int:
    """Write volume fields into matching rows (by primary_term, case-insensitive); returns rows touched."""
    by_term = {v['keyword'].casefold(): v for v in volumes}
    touched = 0
    for row in document['rows']:
        v = by_term.get(' '.join(row['primary_term'].split()).casefold())
        if not v:
            continue
        row.update(volume=v['volume'], cpc=v['cpc'], competition=v['competition'], source='dataforseo', fetched_at=v['fetched_at'],
                   volume_provider='dataforseo', volume_checked_at=v['fetched_at'][:10])
        touched += 1
    return touched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', type=Path, help='keyword-map.json whose primary terms get volumes (updated in place)')
    ap.add_argument('--keyword', action='append', default=[])
    ap.add_argument('--location-code', type=int, required=True)
    ap.add_argument('--language-code', required=True)
    ap.add_argument('--max-keywords', type=int, default=DEFAULT_CAP)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    doc = json.loads(args.map.read_text()) if args.map else None
    terms = args.keyword + ([r['primary_term'] for r in doc['rows']] if doc else [])
    count = len(_dedupe(terms))
    print(json.dumps({'keywords': count, 'estimated_cost_usd': estimate_cost(count), 'cap': args.max_keywords,
                      'note': 'estimate from an assumed per-task price; volumes are bucketed Google Ads estimates'}), flush=True)
    if args.dry_run:
        return 0
    try:
        rows = fetch_volumes(terms, args.location_code, args.language_code, max_keywords=args.max_keywords)
    except (MissingCredentials, CapExceeded) as exc:
        print(json.dumps({'status': exc.status, 'message': str(exc)}))
        return 1
    if doc is not None:
        apply_to_map(doc, rows)
        args.map.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
    costs = {r['task_cost'] for r in rows if r['task_cost'] is not None}
    print(json.dumps({'status': 'ok', 'rows': rows, 'returned_task_cost_usd': sorted(costs)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
