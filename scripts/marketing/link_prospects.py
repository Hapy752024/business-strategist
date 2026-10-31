"""Automated inputs for earned-media qualification: page pre-checks, unlinked mentions, link-gap diff.

prequalify: for ledger prospects, fetch the source page (public fetch, no cookies or JS), keep the
  sentence around any competitor link, list public contact routes (mailto, /contact, author meta)
  and, with --check-indexed, ask Google (via Serper) whether the page is indexed. Report-only: the
  fit judgment and any rejection stay with the agent and the ledger's `set` command.
mentions: search for the brand name outside the own site and fetch each hit to see whether it
  already links to the property; unlinked mentions become ledger prospects.
diff: new and gone clean domains between two competitor_backlinks runs (monthly link gap).

Every network step is bounded (--max) and the Serper step is optional because it is metered.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing import link_ledger as ledger  # noqa: E402
from scripts.marketing.link_observations import anchors, url_key  # noqa: E402
from scripts.marketing.public_fetch import fetch, validate_public_url  # noqa: E402

SEARCH_HOSTS = ('google.', 'bing.com', 'duckduckgo.com', 'yahoo.com', 'facebook.com', 'x.com', 'twitter.com', 'linkedin.com')
CONTACT_PATH = re.compile(r'/(contact|about|write-for-us|contribute|submit|pitch|team|author|editor)', re.I)


class Text(HTMLParser):
    """Visible text with the anchor hrefs embedded as markers, so the sentence around a link can be cut out."""
    SKIP = {'script', 'style', 'noscript', 'template', 'svg', 'head'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.meta = [], 0, {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
        if tag == 'meta' and (attrs.get('name') or attrs.get('property') or '').lower() in {'author', 'article:author'} and attrs.get('content'):
            self.meta['author'] = attrs['content'].strip()
        if tag == 'a' and attrs.get('href') and not self.skip:
            self.parts.append(f" \x00{attrs['href']}\x00 ")
        if tag in {'p', 'li', 'br', 'div', 'h1', 'h2', 'h3', 'h4', 'tr'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def _text(raw: bytes) -> tuple[str, dict]:
    parser = Text()
    parser.feed(raw.decode('utf-8', errors='replace'))
    return re.sub(r'[ \t]+', ' ', ''.join(parser.parts)), parser.meta


def context(raw: bytes, final_url: str, domains: set[str], width: int = 240) -> list[dict]:
    """Sentence-ish window around each link whose host is in `domains`."""
    text, _ = _text(raw)
    out = []
    for match in re.finditer(r'\x00([^\x00]+)\x00', text):
        try:
            href = url_key(match.group(1) if '://' in match.group(1) else final_url.rstrip('/') + '/' + match.group(1).lstrip('/'))
        except ValueError:
            continue
        host = href.split('/')[2].removeprefix('www.')
        if host not in domains:
            continue
        start, end = max(0, match.start() - width), min(len(text), match.end() + width)
        window = re.sub(r'\x00[^\x00]*\x00', '', text[start:end])
        out.append({'href': href, 'context': ' '.join(window.split())})
    return out


def contacts(raw: bytes, final_url: str) -> dict:
    rows = anchors(raw, final_url)
    _, meta = _text(raw)
    mailto = sorted({'mailto:' + m.decode('ascii', 'ignore').lower() for m in re.findall(rb'href=["\']mailto:([^"\'?]+)', raw, re.I)})
    pages = sorted({r['href'] for r in rows if r['href'].startswith('http') and CONTACT_PATH.search(r['href'])})[:8]
    return {'mailto': mailto[:5], 'contact_pages': pages, 'author': meta.get('author')}


def prequalify_row(row: dict, competitor_domains: set[str], *, fetcher=fetch) -> dict:
    url = row['source_url']
    result = {'source_url': url, 'source_domain': row['source_domain'], 'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        validate_public_url(url)
        got = fetcher(url)
    except Exception as exc:  # noqa: BLE001 - any fetch failure is a coverage gap, recorded as such
        return {**result, 'page': 'fetch_error', 'reason': type(exc).__name__, 'suggested': 'recheck'}
    status = got['status']
    if status != 200:
        page = 'dead' if status in {404, 410} else 'access_limited' if status in {401, 403, 429} else f'http_{status}'
        return {**result, 'page': page, 'http_status': status, 'suggested': 'reject_dead' if page == 'dead' else 'recheck'}
    raw = got['raw']
    title = re.search(rb'<title[^>]*>(.*?)</title>', raw, re.I | re.S)
    links = context(raw, got['final_url'], competitor_domains)
    return {**result, 'page': 'live', 'http_status': 200, 'final_url': got['final_url'],
            'title': ' '.join(title.group(1).decode('utf-8', 'replace').split()) if title else None,
            'competitor_links': links, 'contacts': contacts(raw, got['final_url']),
            'suggested': 'review' if links else 'review_no_competitor_link_found'}


def check_indexed(url: str, *, searcher=None) -> bool | None:
    """Google-indexed per a `site:` query through Serper; None when the route is unavailable."""
    if searcher is None:
        from scripts import serper_fetch as sf
        def searcher(q):
            sf.load_local_env(); sf.require_key()
            return sf.request_json(sf.SERPER_ENDPOINTS['search'], {'q': q, 'num': 5})
    try:
        body = searcher(f'site:{url}')
    except Exception:  # noqa: BLE001
        return None
    key = url_key(url).rstrip('/')
    return any(url_key(r['link']).rstrip('/') == key for r in body.get('organic', []) if r.get('link'))


def prequalify(doc: dict, competitor_domains: set[str], *, max_rows: int, check_index: bool = False, fetcher=fetch, searcher=None) -> list[dict]:
    rows = [r for r in doc['rows'] if r['stage'] == 'prospect'][:max_rows]
    out = []
    for row in rows:
        rep = prequalify_row(row, competitor_domains, fetcher=fetcher)
        if check_index and rep['page'] == 'live':
            rep['indexed'] = check_indexed(row['source_url'], searcher=searcher)
        out.append(rep)
    return out


def find_mentions(brand: str, own_domain: str, *, num: int = 30, max_fetch: int = 30, ignore_case: bool = False, searcher=None, fetcher=fetch) -> dict:
    """Pages naming the brand outside the own site, split into linked and unlinked.

    The match is case-sensitive by default: a brand like 'Italy for Retirees' is also an ordinary phrase, and
    'cost of living in Italy for retirees' is not a mention. Search-engine and social hosts are skipped."""
    own = own_domain.removeprefix('www.')
    if searcher is None:
        from scripts import serper_fetch as sf
        def searcher(q):
            sf.load_local_env(); sf.require_key()
            return sf.request_json(sf.SERPER_ENDPOINTS['search'], {'q': q, 'num': min(num, 100)})
    body = searcher(f'"{brand}" -site:{own}')
    hits = [r for r in body.get('organic', []) if r.get('link') and not any(h in r['link'].split('/')[2].lower() for h in SEARCH_HOSTS)]
    linked, unlinked, unchecked = [], [], []
    for hit in hits[:max_fetch]:
        url = hit['link']
        try:
            validate_public_url(url)
            got = fetcher(url)
        except Exception as exc:  # noqa: BLE001
            unchecked.append({'source_url': url, 'reason': type(exc).__name__}); continue
        if got['status'] != 200:
            unchecked.append({'source_url': url, 'reason': f"http_{got['status']}"}); continue
        text, _ = _text(got['raw'])
        hay, needle = (text.lower(), brand.lower()) if ignore_case else (text, brand)
        if needle not in hay:
            unchecked.append({'source_url': url, 'reason': 'brand_not_in_visible_text'}); continue
        has_link = any(a['href'].split('/')[2].removeprefix('www.') == own for a in anchors(got['raw'], got['final_url']) if a['href'].startswith('http'))
        pos = hay.find(needle)
        snippet = ' '.join(re.sub(r'\x00[^\x00]*\x00', '', text[max(0, pos - 200):pos + 200]).split())
        (linked if has_link else unlinked).append({'source_url': url, 'title': hit.get('title'), 'mention': snippet, 'contacts': contacts(got['raw'], got['final_url'])})
    return {'brand': brand, 'property': own, 'query': f'"{brand}" -site:{own}', 'retrieved_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'results': len(hits), 'linked': linked, 'unlinked': unlinked, 'unchecked': unchecked,
            'limits': 'One Google sample via Serper; a mention is a prospecting clue and the page owner owes no link.'}


def add_mentions(doc: dict, mentions: dict, *, at: str | None = None) -> int:
    added = 0
    for m in mentions['unlinked']:
        if ledger._row(doc, m['source_url']):
            continue
        doc['rows'].append(ledger._new_row(m['source_url'], stage='prospect', origin='unlinked_mention', at=at or ledger._today(),
                                           note='brand named without a link: ' + m['mention'][:160]))
        added += 1
    return added


def diff(previous: dict, current: dict) -> dict:
    def clean(doc):
        return {r['source_domain']: r for r in doc['candidates'] if not r.get('flags')}
    before, after = clean(previous), clean(current)
    return {'previous_retrieved_at': previous.get('retrieved_at'), 'current_retrieved_at': current.get('retrieved_at'),
            'new_domains': [after[d] for d in sorted(set(after) - set(before), key=lambda d: -(after[d]['domain_rank'] or 0))],
            'gone_domains': sorted(set(before) - set(after)), 'unchanged': len(set(before) & set(after))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='command', required=True)
    pq = sub.add_parser('prequalify'); pq.add_argument('--base', type=Path, required=True); pq.add_argument('--max', type=int, default=30)
    pq.add_argument('--competitor', action='append', default=[], help='competitor domain whose links to quote (repeatable)')
    pq.add_argument('--check-indexed', action='store_true', help='one Serper site: query per live page (metered)')
    pq.add_argument('--out', type=Path, required=True, help='new directory for prequalified.json')
    me = sub.add_parser('mentions'); me.add_argument('--base', type=Path, required=True); me.add_argument('--brand', required=True)
    me.add_argument('--num', type=int, default=30); me.add_argument('--max-fetch', type=int, default=30)
    me.add_argument('--out', type=Path, required=True); me.add_argument('--add-to-ledger', action='store_true')
    me.add_argument('--ignore-case', action='store_true', help='only for brand names that are not ordinary phrases')
    df = sub.add_parser('diff'); df.add_argument('--previous', type=Path, required=True); df.add_argument('--current', type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.command == 'diff':
            print(json.dumps(diff(json.loads(args.previous.read_text()), json.loads(args.current.read_text())), indent=2, ensure_ascii=False)); return 0
        path = args.base / ledger.RELATIVE
        doc = ledger.load(path)
        args.out.mkdir(parents=True, exist_ok=False)
        if args.command == 'prequalify':
            rows = prequalify(doc, {c.removeprefix('www.') for c in args.competitor}, max_rows=args.max, check_index=args.check_indexed)
            (args.out / 'prequalified.json').write_text(json.dumps({'rows': rows, 'limits': 'Report only; qualification and rejection are ledger decisions.'}, indent=2, ensure_ascii=False) + '\n')
            summary = {}
            for r in rows:
                summary[r['suggested']] = summary.get(r['suggested'], 0) + 1
            print(json.dumps({'status': 'ok', 'checked': len(rows), 'suggested': summary, 'out': str(args.out)})); return 0
        found = find_mentions(args.brand, doc['property'], num=args.num, max_fetch=args.max_fetch, ignore_case=args.ignore_case)
        (args.out / 'mentions.json').write_text(json.dumps(found, indent=2, ensure_ascii=False) + '\n')
        added = 0
        if args.add_to_ledger:
            added = add_mentions(doc, found)
            ledger.save(path, doc)
        print(json.dumps({'status': 'ok', 'results': found['results'], 'linked': len(found['linked']), 'unlinked': len(found['unlinked']),
                          'unchecked': len(found['unchecked']), 'added_to_ledger': added, 'out': str(args.out)})); return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status': 'unavailable', 'reason': str(exc)})); return 1


if __name__ == '__main__':
    raise SystemExit(main())
