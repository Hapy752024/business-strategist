"""Post-deploy SEO probe of the live production host.

Checks what local tests cannot: that robots, sitemap and every page's canonical/og:url
point at the production host and answer 200 there without a redirect, and that every
other registered domain has a recorded redirect or lapse decision. Also warns about
long titles, thin indexable pages and article pages without a visible date or sources.

`analyze()` is pure over observations; `collect()` performs read-only GET requests that
never follow redirects. The probe proves host/indexing signals only, not rankings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from scripts.brand.seo_checks import canonical_key, is_noindex, sitemap_urls

TITLE_MAX = 60
THIN_WORDS = 250
MAX_PAGES = 200
MAX_BYTES = 2_000_000
DOMAIN_DECISIONS = {'redirect', 'lapse'}


class PageMeta(HTMLParser):
    """Collect the head signals and visible word count the probe needs."""

    def __init__(self):
        super().__init__()
        self.title, self.canonicals, self.og_urls, self.robots = '', [], [], []
        self.words, self.has_time, self.has_sources, self.article_schema = 0, False, False, False
        self._skip, self._in_title, self._json = 0, False, []

    def handle_starttag(self, tag, attrs):
        d = {k: v or '' for k, v in attrs}
        if tag in {'script', 'style', 'noscript', 'template'}:
            self._skip += 1
            if tag == 'script' and d.get('type') == 'application/ld+json':
                self._json.append('')
        if tag == 'title':
            self._in_title = True
        if tag == 'link' and 'canonical' in d.get('rel', '').lower().split():
            self.canonicals.append(d.get('href', ''))
        if tag == 'meta' and d.get('property') == 'og:url':
            self.og_urls.append(d.get('content', ''))
        if tag == 'meta' and d.get('name', '').lower() in {'robots', 'googlebot'}:
            self.robots.append(d.get('content', ''))
        if tag == 'time' and d.get('datetime'):
            self.has_time = True
        if d.get('id') == 'sources':
            self.has_sources = True

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript', 'template'} and self._skip:
            self._skip -= 1
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._skip and self._json:
            self._json[-1] += data
        elif not self._skip:
            self.words += len(data.split())

    def close(self):
        super().close()
        for raw in self._json:
            if re.search(r'"@type"\s*:\s*"(Article|BlogPosting|NewsArticle)"', raw):
                self.article_schema = True


def _host(url: str) -> str:
    return urlsplit(url).netloc.lower()


def analyze(origin: str, obs: dict, *, domains: dict[str, str] | None = None,
            article_prefixes: tuple[str, ...] = ()) -> dict:
    """Evaluate observations. obs: {'robots': {status, body}, 'sitemap': {status, body},
    'pages': {url: {status, location, body}}, 'domains': {host: {status, location}}}."""
    origin = origin.rstrip('/')
    prod = _host(origin)
    errors, warnings, limits = [], [], []
    robots = obs.get('robots') or {}
    if robots.get('status') != 200:
        errors.append(f'robots.txt: expected 200 on {prod}, got {robots.get("status")}')
    declared = [line.split(':', 1)[1].strip() for line in (robots.get('body') or '').splitlines()
                if line.lower().startswith('sitemap:')]
    for url in declared:
        if _host(url) != prod:
            errors.append(f'robots.txt sitemap points at {_host(url)}, not production host {prod}: {url}')
    sitemap = obs.get('sitemap') or {}
    urls: list[str] = []
    if sitemap.get('status') != 200:
        errors.append(f'sitemap: expected 200 on {prod}, got {sitemap.get("status")}')
    else:
        try:
            urls, children = sitemap_urls(sitemap.get('body', ''))
            if children:
                limits.append('sitemap index children are not probed; run against each child sitemap')
        except Exception as exc:  # malformed XML is a reported defect, not a crash
            errors.append(f'sitemap: {exc}')
    if len(urls) > MAX_PAGES:
        limits.append(f'sitemap has {len(urls)} URLs; only the first {MAX_PAGES} were probed')
    pages = obs.get('pages', {})
    for url in urls[:MAX_PAGES]:
        if _host(url) != prod:
            errors.append(f'sitemap URL on {_host(url)}, not production host {prod}: {url}')
        page = pages.get(url)
        if page is None:
            limits.append(f'{url}: not fetched')
            continue
        status = page.get('status')
        if status in {301, 302, 303, 307, 308}:
            errors.append(f'{url}: sitemap URL redirects ({status}) to {page.get("location")}')
            continue
        if status != 200:
            errors.append(f'{url}: sitemap URL returned {status}')
            continue
        meta = PageMeta(); meta.feed(page.get('body', '')); meta.close()
        path = urlsplit(url).path or '/'
        canon = [canonical_key(urljoin(url, c)) for c in meta.canonicals]
        if len(canon) != 1:
            errors.append(f'{path}: expected exactly one canonical, found {len(canon)}')
        elif canon[0] != canonical_key(url):
            errors.append(f'{path}: canonical {canon[0]} differs from its sitemap URL {url}')
        for og in meta.og_urls:
            if _host(urljoin(url, og)) != prod:
                errors.append(f'{path}: og:url on {_host(urljoin(url, og))}, not production host {prod}')
        if is_noindex(meta.robots):
            errors.append(f'{path}: listed in the sitemap but marked noindex')
            continue
        title = ' '.join(meta.title.split())
        if len(title) > TITLE_MAX:
            warnings.append(f'{path}: title is {len(title)} characters (over {TITLE_MAX}, likely truncated): {title}')
        if meta.words < THIN_WORDS:
            warnings.append(f'{path}: about {meta.words} visible words; thin indexable page, consider noindex or more content')
        if any(path.startswith(p) for p in article_prefixes):
            if not meta.has_time:
                warnings.append(f'{path}: article page shows no visible updated date (<time datetime>)')
            if not meta.has_sources:
                warnings.append(f'{path}: article page has no sources section (id="sources")')
            if not meta.article_schema:
                warnings.append(f'{path}: article page has no Article structured data')
    for url, page in pages.items():
        if url in urls:
            continue
        status = page.get('status')
        if status in {301, 302, 303, 307, 308}:
            errors.append(f'{url}: canonical URL redirects ({status}) to {page.get("location")}')
    domain_obs = obs.get('domains', {})
    for host, decision in (domains or {}).items():
        seen = domain_obs.get(host, {})
        if decision not in DOMAIN_DECISIONS:
            errors.append(f'{host}: domain decision must be one of {sorted(DOMAIN_DECISIONS)}, got {decision!r}')
        elif decision == 'redirect':
            loc = seen.get('location') or ''
            if seen.get('status') not in {301, 308} or _host(urljoin(f'https://{host}/', loc)) != prod:
                errors.append(f'{host}: recorded as redirect but returned {seen.get("status")} '
                              f'{loc or "(no location)"}; expected 301/308 to {prod}')
        elif seen.get('status') not in {None, 'unreachable'}:
            warnings.append(f'{host}: recorded as lapse but still answers {seen.get("status")}')
    return {'origin': origin, 'errors': sorted(set(errors)), 'warnings': sorted(set(warnings)),
            'limits': sorted(set(limits)), 'sitemap_urls': len(urls),
            'boundary': 'production host/indexing signals only; not rankings or Search Console status'}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _fetch(url: str, timeout: float) -> dict:
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={'User-Agent': 'production-seo-probe/1'})
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read(MAX_BYTES + 1)
            return {'status': resp.status, 'body': body[:MAX_BYTES].decode('utf-8', 'replace')}
    except urllib.error.HTTPError as exc:
        return {'status': exc.code, 'location': exc.headers.get('Location', '')}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {'status': 'unreachable'}


def collect(origin: str, *, domains: dict[str, str] | None = None, timeout: float = 20) -> dict:
    origin = origin.rstrip('/')
    obs = {'robots': _fetch(origin + '/robots.txt', timeout), 'pages': {}, 'domains': {}}
    declared = [line.split(':', 1)[1].strip() for line in (obs['robots'].get('body') or '').splitlines()
                if line.lower().startswith('sitemap:')]
    obs['sitemap'] = _fetch(origin + '/sitemap.xml', timeout)
    urls: list[str] = []
    if obs['sitemap'].get('status') == 200:
        try:
            urls = sitemap_urls(obs['sitemap']['body'])[0][:MAX_PAGES]
        except Exception:
            urls = []
    for url in urls:
        obs['pages'][url] = _fetch(url, timeout)
    for url in declared:  # a robots sitemap on another host must also be probed for redirects
        if _host(url) != _host(origin):
            obs['pages'][url] = _fetch(url, timeout)
    for url, page in list(obs['pages'].items()):
        meta = PageMeta(); meta.feed(page.get('body', '') or ''); meta.close()
        for c in meta.canonicals[:1]:
            target = urljoin(url, c)
            if canonical_key(target) != canonical_key(url) and target not in obs['pages']:
                obs['pages'][target] = _fetch(target, timeout)
    for host in domains or {}:
        obs['domains'][host] = _fetch(f'https://{host}/', timeout)
    return obs


def search_console_owner_action(origin: str, date: str) -> str:
    """Owner-actions table row for Search Console/Bing onboarding (owner-only: needs the
    owner's Google account and DNS access)."""
    host = _host(origin)
    domain = host[4:] if host.startswith('www.') else host
    return (f'| search-console / proposed {date} | In Google Search Console add a **Domain** property for '
            f'`{domain}` and verify it with the DNS TXT record Google shows. Submit `{origin.rstrip("/")}/sitemap.xml` '
            f'under Sitemaps, then use URL inspection → Request indexing for the home page and key guides. In Bing '
            f'Webmaster Tools choose "Import from Google Search Console". Owner-only: needs your Google account and '
            f'DNS access. | One-off; about 20 minutes, then review Indexing → Pages after 1–2 weeks. | Right after '
            f'the first production deploy; shows whether pages are indexed. | Property verified, sitemap shows '
            f'"Success", indexed/not-indexed counts recorded; close after the first coverage review. |')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('origin', help='production origin, e.g. https://www.example.com')
    parser.add_argument('--domain', action='append', default=[], metavar='HOST=redirect|lapse',
                        help='every other registered domain with its recorded decision')
    parser.add_argument('--article-prefix', action='append', default=[], help='path prefix of article pages, e.g. /guide/')
    parser.add_argument('--observations', type=Path, help='analyze saved observations instead of fetching')
    parser.add_argument('--owner-action', metavar='YYYY-MM-DD', help='also print the Search Console owner-actions row')
    args = parser.parse_args()
    try:
        domains = dict(item.split('=', 1) for item in args.domain)
    except ValueError:
        parser.error('--domain must be HOST=redirect or HOST=lapse')
    obs = json.loads(args.observations.read_text()) if args.observations else collect(args.origin, domains=domains)
    result = analyze(args.origin, obs, domains=domains, article_prefixes=tuple(args.article_prefix))
    if args.owner_action:
        result['owner_action_row'] = search_console_owner_action(args.origin, args.owner_action)
    result['status'] = 'fail' if result['errors'] else 'pass'
    json.dump(result, sys.stdout, indent=2)
    print()
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
