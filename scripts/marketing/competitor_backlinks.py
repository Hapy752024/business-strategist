"""Competitor backlink prospects via DataForSEO `backlinks/backlinks/live`.

Search Console shows links only for a verified property, so competitor prospecting uses the
DataForSEO Backlinks API (one request per competitor, one row per linking domain). Rows are
link *candidates* for `earned-media-builder`, never qualified opportunities: a competitor link
is a prospecting clue, not a reason a publisher owes inclusion. Domains already linking to the
own property are excluded; obvious scraper/whois pages are kept but flagged, not silently dropped.

Cost is estimated and printed before any call. Paid research spend is pre-authorized, so there is no default
cap; an optional `--max-cost-usd` refuses larger runs before touching the network. The real cost is read
from each response.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing.keyword_volume import MissingCredentials, ProviderError, _post, credentials  # noqa: E402
from scripts.marketing.link_observations import sha, url_key  # noqa: E402

ENDPOINT = 'https://api.dataforseo.com/v3/backlinks/backlinks/live'
# Observed live cost (USD, 2026-10-31 check): about 0.02 per task plus a small per-row charge.
ASSUMED_COST_PER_TASK = 0.03
DEFAULT_LIMIT = 100
DEFAULT_MAX_COST = None  # no cap unless the caller sets one
SCRAPER_TITLE = re.compile(r'whois|find backlinks|domain list|backlink checker|site stats', re.I)
LINK_SELLER = re.compile(r'\bPBN\b|link ?building|buy .*backlinks|aged domains|dofollow backlink|guest post service|'
                         r'high (da|dr|authority) backlinks|niche edit|outreach backlinks|seo links|link profile|domain authority|casino', re.I)


class CapExceeded(RuntimeError):
    status = 'cap_exceeded'


def estimate_cost(targets: int) -> float:
    return round((targets + 1) * ASSUMED_COST_PER_TASK, 4)  # +1 for the own-property exclusion call


def _domain(value: str) -> str:
    host = url_key(value if '://' in value else 'https://' + value).split('/')[2]
    return host[4:] if host.startswith('www.') else host


def _task(target: str, *, limit: int, language: str | None, auth: tuple[str, str], post) -> tuple[list[dict], float | None]:
    filters: list = [['dofollow', '=', True], 'and', ['is_lost', '=', False]]
    if language:
        filters += ['and', ['page_from_language', '=', language]]
    body = post(ENDPOINT, [{'target': target, 'limit': limit, 'mode': 'one_per_domain', 'filters': filters,
                            'order_by': ['domain_from_rank,desc']}], auth)
    task = (body.get('tasks') or [{}])[0]
    if task.get('status_code') != 20000:
        raise ProviderError('task_failed', f"DataForSEO task failed: {task.get('status_code')} {task.get('status_message')}")
    items = [i for r in task.get('result') or [] for i in r.get('items') or []]
    return items, task.get('cost')


def flags(item: dict) -> list[str]:
    out = []
    if SCRAPER_TITLE.search(item.get('page_from_title') or ''):
        out.append('scraper_or_whois_page')
    if LINK_SELLER.search((item.get('page_from_title') or '') + ' ' + (item.get('anchor') or '')):
        out.append('link_seller_page')
    if item.get('item_type') not in (None, 'anchor'):
        out.append(f"non_text_link:{item.get('item_type')}")
    if not (item.get('anchor') or '').strip():
        out.append('empty_anchor')
    if item.get('is_sponsored') or item.get('is_ugc'):
        out.append('sponsored_or_ugc')
    return out


def prospect(competitors: list[str], own: str, *, limit: int = DEFAULT_LIMIT, language: str | None = 'en',
             max_cost_usd: float | None = DEFAULT_MAX_COST, post=None) -> dict:
    """Return candidate linking domains for the competitors, minus domains already linking to `own`."""
    targets = sorted({_domain(c) for c in competitors})
    own_domain = _domain(own)
    if max_cost_usd is not None and estimate_cost(len(targets)) > max_cost_usd:
        raise CapExceeded(f'{len(targets)} competitors estimate {estimate_cost(len(targets))} USD, above --max-cost-usd {max_cost_usd}; nothing was sent')
    login, password = credentials()
    if not login or not password:
        raise MissingCredentials('DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD are required')
    auth, post = (login, password), post or _post
    costs: list[float] = []
    own_items, cost = _task(own_domain, limit=1000, language=None, auth=auth, post=post)
    costs.append(cost or 0)
    already = {i.get('domain_from') for i in own_items if i.get('domain_from')}
    raw: dict[str, list[dict]] = {own_domain: own_items}
    by_domain: dict[str, dict] = {}
    excluded = {'already_linking': 0, 'own_or_competitor_domain': 0}
    for target in targets:
        items, cost = _task(target, limit=limit, language=language, auth=auth, post=post)
        costs.append(cost or 0)
        raw[target] = items
        for item in items:
            source_domain = item.get('domain_from') or ''
            if not source_domain or not item.get('url_from'):
                continue
            if source_domain in already:
                excluded['already_linking'] += 1
                continue
            if source_domain in targets or source_domain == own_domain:
                excluded['own_or_competitor_domain'] += 1
                continue
            row = by_domain.setdefault(source_domain, {
                'source_url': item['url_from'], 'source_domain': source_domain, 'page_title': item.get('page_from_title'),
                'links_to': [], 'anchor': item.get('anchor'), 'domain_rank': item.get('domain_from_rank'),
                'page_rank': item.get('page_from_rank'), 'first_seen': item.get('first_seen'), 'last_seen': item.get('last_seen'),
                'flags': flags(item), 'qualification': 'candidate', 'link_inclusion': 'unknown'})
            row['links_to'].append({'competitor': target, 'target_url': item.get('url_to')})
    rows = sorted(by_domain.values(), key=lambda r: (-len(r['links_to']), -(r['domain_rank'] or 0), r['source_domain']))
    for row in rows:
        row['competitor_count'] = len(row['links_to'])
    return {'schema_version': 1, 'property': own_domain, 'competitors': targets, 'source': 'dataforseo_backlinks',
            'retrieved_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'language': language,
            'candidates': rows, 'excluded': excluded, 'already_linking_domains': sorted(already),
            'returned_cost_usd': round(sum(costs), 4), 'raw': raw,
            'limits': ('Index sample, not Google\'s view; dofollow/rank are provider observations. Candidates need audience-fit '
                       'review and a live-page check (earned-media-builder qualification) before any pitch. Flagged rows are '
                       'kept so the exclusion is reviewable.')}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--competitor', action='append', required=True, help='competitor domain or URL (repeatable)')
    ap.add_argument('--own', required=True, help='own property domain; its linking domains are excluded')
    ap.add_argument('--out', type=Path, required=True, help='new directory for candidates.json and raw/')
    ap.add_argument('--limit', type=int, default=DEFAULT_LIMIT, help='linking domains per competitor')
    ap.add_argument('--language', default='en', help="page language filter; '' for none")
    ap.add_argument('--max-cost-usd', type=float, default=DEFAULT_MAX_COST, help='optional cap; none by default')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    targets = len({_domain(c) for c in args.competitor})
    print(json.dumps({'competitors': targets, 'estimated_cost_usd': estimate_cost(targets), 'cap_usd': args.max_cost_usd,
                      'note': 'estimate from an assumed per-task price; real cost is read from the responses'}), flush=True)
    if args.dry_run:
        return 0
    try:
        doc = prospect(args.competitor, args.own, limit=args.limit, language=args.language or None, max_cost_usd=args.max_cost_usd)
    except (MissingCredentials, CapExceeded, ProviderError) as exc:
        print(json.dumps({'status': exc.status, 'message': str(exc)}))
        return 1
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'raw').mkdir()
    raw = doc.pop('raw')
    provenance = []
    for target, items in raw.items():
        path = args.out / 'raw' / f'{target}.json'
        data = (json.dumps(items, indent=2, ensure_ascii=False) + '\n').encode()
        path.write_bytes(data)
        provenance.append({'path': f'raw/{target}.json', 'sha256': sha(data)})
    doc['provenance'] = provenance
    (args.out / 'candidates.json').write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'ok', 'candidates': len(doc['candidates']), 'excluded': doc['excluded'],
                      'returned_cost_usd': doc['returned_cost_usd'], 'out': str(args.out)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
