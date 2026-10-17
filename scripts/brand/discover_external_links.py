#!/usr/bin/env python3
"""Offline external anchor inventory from an explicit set of HTML captures.

No requests are made. Query-bearing/credential-bearing URLs are redacted and
excluded; candidates still require review before any network checker runs.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.base = None
        self.inert = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'template':
            self.inert += 1
        if self.inert:
            return
        attrs = dict(attrs)
        if tag == 'base' and self.base is None and attrs.get('href'):
            self.base = attrs['href']
        if tag in {'a', 'area'} and attrs.get('href'):
            self.links.append((attrs['href'], self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == 'template' and self.inert:
            self.inert -= 1

    def handle_startendtag(self, tag, attrs):
        # HTML ignores the self-closing slash on non-void template elements.
        self.handle_starttag(tag, attrs)
        if tag != 'template':
            self.handle_endtag(tag)


def origin(p):
    return p.scheme.lower(), p.hostname, p.port or (443 if p.scheme == 'https' else 80)


def inventory(pages, root):
    found = defaultdict(list)
    skipped = []
    for page in pages:
        page_url = urlsplit(page['url'])
        if page_url.scheme not in {'http', 'https'} or not page_url.hostname or page_url.query or page_url.fragment or page_url.username or page_url.password:
            raise ValueError('capture URL must be credential-free HTTP(S), without query or fragment')
        relative = Path(page['file'])
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root.resolve()):
            raise ValueError('capture path must stay within inventory directory')
        parser = Anchors()
        parser.feed(path.read_text(encoding='utf-8'))
        try:
            base = urljoin(page['url'], parser.base or '')
            parsed_base = urlsplit(base)
            if parsed_base.scheme not in {'http', 'https'} or not parsed_base.hostname:
                raise ValueError('invalid base')
            origin(parsed_base)  # Validate malformed ports, too.
        except ValueError:
            raise ValueError('invalid HTML base; repair capture before discovery') from None
        for href, line in parser.links:
            occurrence = {'page': page['url'], 'file': relative.as_posix(), 'line': line}
            try:
                if any(ord(c) < 32 or ord(c) == 127 for c in href):
                    raise ValueError('control character')
                p = urlsplit(urljoin(base, href))
                if p.scheme not in {'http', 'https'} or not p.hostname:
                    skipped.append({**occurrence, 'reason': 'non_http_or_invalid'})
                    continue
                if p.query or p.username or p.password:
                    skipped.append({**occurrence, 'reason': 'query_or_credentials_requires_review'})
                    continue
                if origin(p) == origin(page_url):
                    continue
                host = p.hostname.lower().encode('idna').decode('ascii')
                if ':' in host:
                    host = '[' + host + ']'
                if p.port and p.port != (443 if p.scheme == 'https' else 80):
                    host += ':' + str(p.port)
                url = urlunsplit((p.scheme.lower(), host, p.path or '/', '', ''))
                found[url].append({**occurrence, 'fragment_present': bool(p.fragment)})
            except ValueError:
                skipped.append({**occurrence, 'reason': 'invalid_url'})
    return {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'pages_inspected': len(pages), 'network_checked': False,
            'links': [{'url': url, 'occurrences': rows} for url, rows in sorted(found.items())],
            'skipped': skipped,
            'limitations': ['Only supplied HTML captures; no JavaScript execution or route discovery.',
                            'No HTTP, fragment, content-freshness or destination-safety validation.',
                            'Review action URLs and public destinations before requesting candidates.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path, help='JSON array of {url,file}; files relative to this JSON')
    args = parser.parse_args()
    pages = json.loads(args.captures.read_text())
    if not isinstance(pages, list) or not pages:
        parser.error('nonempty capture array required')
    print(json.dumps(inventory(pages, args.captures.parent), indent=2))


if __name__ == '__main__':
    main()
