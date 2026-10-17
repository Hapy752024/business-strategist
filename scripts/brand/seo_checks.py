"""Deterministic declared-scope SEO checks over browser/HTTP observations."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from xml.etree import ElementTree as ET
from urllib.robotparser import RobotFileParser


def sitemap_urls(raw: str) -> tuple[list[str], list[str]]:
    if len(raw.encode()) > 2_000_000 or '<!DOCTYPE' in raw.upper() or '<!ENTITY' in raw.upper():
        raise ValueError('sitemap is oversized or contains declarations')
    root = ET.fromstring(raw)
    name = root.tag.rsplit('}', 1)[-1]
    if name not in {'urlset', 'sitemapindex'}:
        raise ValueError('invalid sitemap root')
    urls = [el.text.strip() for el in root.iter() if el.tag.rsplit('}', 1)[-1] == 'loc' and el.text]
    return (urls, []) if name == 'urlset' else ([], urls)


class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots, self.canonicals = [], []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'meta' and d.get('name', '').lower() in {'robots', 'googlebot'}:
            self.robots.append(d.get('content', ''))
        if tag == 'link' and 'canonical' in d.get('rel', '').lower().split():
            self.canonicals.append(d.get('href', ''))


def is_noindex(values):
    return any({'noindex', 'none'} & set(re.split(r'[\s,:]+', v.lower())) for v in values)


def canonical_key(value):
    """Normalize only an origin's empty path, preserving paths and queries."""
    if not value:
        return value
    parts = urlsplit(value)
    return parts._replace(path=parts.path or '/').geturl()


def check(payload: dict) -> dict:
    inventory, pages = payload['inventory'], payload['pages']
    errors, limits, sitemap = [], [], set()
    for doc in payload.get('sitemaps', []):
        try:
            urls, children = sitemap_urls(doc['body'])
            sitemap.update(canonical_key(url) for url in urls)
            captured = {item.get('url') for item in payload.get('sitemaps', [])}
            if children and not all(url in captured for url in children):
                limits.append('sitemap-index children were not fully checked')
        except (ValueError, ET.ParseError) as exc:
            errors.append('sitemap: ' + str(exc))
    declared = {r['path']: r for r in inventory}
    observed = {p['path']: p for p in pages}
    canonical_paths = {canonical_key(r.get('expectedCanonical')): r for r in inventory if r.get('expectedCanonical')}
    for path, row in declared.items():
        if row.get('redirect'):
            continue
        p = observed.get(path)
        if not p:
            errors.append(path + ': declared page unmeasured')
            continue
        parser = Meta(); parser.feed(p.get('raw_html', ''))
        expected = canonical_key(row.get('expectedCanonical'))
        if expected:
            http_can = [canonical_key(urljoin(p.get('final_url', payload['base']), v)) for v in parser.canonicals]
            if canonical_key(p.get('canonical')) != expected or http_can != [expected]:
                errors.append(path + ': canonical differs between expected, HTTP or DOM')
        else:
            limits.append(path + ': intended canonical undeclared')
        directives = parser.robots + p.get('robots', []) + [p.get('x_robots_tag', '')]
        if 'expectedCrawlable' in row:
            raw_robots = payload.get('robots', '')
            if not raw_robots or any(re.search(r'(?i)^(?:allow|disallow):.*[\*$]', line) for line in raw_robots.splitlines()):
                limits.append(path + ': robots policy requires review (missing or extended syntax)')
            else:
                robot = RobotFileParser(); robot.parse(raw_robots.splitlines())
                if robot.can_fetch('Googlebot', urljoin(payload['base'], path)) != row['expectedCrawlable']:
                    errors.append(path + ': robots access conflicts with intended policy')
        if 'expectedIndexable' in row:
            if is_noindex(directives) == row['expectedIndexable']:
                errors.append(path + ': indexing directive conflicts with intended policy')
        else:
            limits.append(path + ': intended indexing policy undeclared')
        if row.get('sitemapExpected') is True and expected not in sitemap:
            errors.append(path + ': expected canonical missing from sitemap')
        if row.get('sitemapExpected') is False and expected in sitemap:
            errors.append(path + ': excluded page appears in sitemap')
        if row.get('entry') is False and row.get('expectedIndexable') is True:
            allowed_hosts = {urlsplit(payload['base']).netloc, urlsplit(expected or '').netloc}
            incoming = [other for other in pages if other['path'] != path and any(
                urlsplit(href).netloc in allowed_hosts and urlsplit(href).path == path for href in other.get('links', []))]
            if not incoming:
                errors.append(path + ': no incoming link within declared inventory')
        if row.get('alternates') is not None and p.get('alternates', {}) != row['alternates']:
            errors.append(path + ': language alternates differ from configuration')
        for language, href in row.get('alternates', {}).items():
            peer = canonical_paths.get(canonical_key(href))
            if peer is not None and expected not in {canonical_key(url) for url in peer.get('alternates', {}).values()}:
                errors.append(path + ': language alternate is not reciprocal: ' + language)
    for url in sorted(sitemap):
        row = canonical_paths.get(url)
        if row and (row.get('redirect') or row.get('sitemapExpected') is False):
            errors.append('sitemap contains redirected/excluded URL: ' + url)
        elif row is None:
            intended = [r for r in inventory if r.get('expectedCanonical')]
            if intended and any(urlsplit(url).path == r['path'] for r in intended):
                errors.append('sitemap has noncanonical URL: ' + url)
            else:
                limits.append('sitemap URL outside declared canonical coverage: ' + url)
    return {'errors': sorted(set(errors)), 'limits': sorted(set(limits)), 'sitemap_urls': sorted(sitemap)}


if __name__ == '__main__':
    import sys
    print(json.dumps(check(json.load(sys.stdin))))
