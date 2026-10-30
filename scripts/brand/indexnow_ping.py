"""Notify IndexNow of changed URLs after an authorized production deploy.

Run only after the owner authorized and completed a deploy. The ping refuses unless
`--confirm-deployed` is passed and https://<host>/<key>.txt already serves the key, which
proves the key file shipped with the deploy. It never runs from the site gate. IndexNow
tells participating search engines a URL changed; it does not guarantee crawling or indexing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ENDPOINT = 'https://api.indexnow.org/indexnow'
KEY_RE = re.compile(r'^[A-Za-z0-9-]{8,128}$')
MAX_URLS = 10_000


def _http(method: str, url: str, body: str | None = None, timeout: float = 20) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body.encode() if body is not None else None, method=method,
                                 headers={'Content-Type': 'application/json; charset=utf-8',
                                          'User-Agent': 'indexnow-ping/1'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(4096).decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        return exc.code, ''
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ''


def ping(host: str, urls: list[str], key: str, *, confirm_deployed: bool = False) -> int:
    """POST the URL list to IndexNow and return the HTTP status (200/202 accepted)."""
    host = host.strip().lower()
    if not host or '/' in host or ':' in host:
        raise ValueError(f'host must be a bare hostname, got {host!r}')
    if not KEY_RE.match(key or ''):
        raise ValueError('IndexNow key must be 8-128 characters of a-z, A-Z, 0-9 or "-"')
    if not urls or len(urls) > MAX_URLS:
        raise ValueError(f'provide 1-{MAX_URLS} URLs')
    for url in urls:
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.netloc.lower() != host:
            raise ValueError(f'URL is not an https URL on {host}: {url}')
    if not confirm_deployed:
        raise PermissionError('refusing to ping: pass --confirm-deployed only after an authorized production deploy')
    key_location = f'https://{host}/{key}.txt'
    status, body = _http('GET', key_location)
    if status != 200 or body.strip() != key:
        raise PermissionError(f'refusing to ping: key file {key_location} returned {status} without the key; '
                              'deploy the key file first')
    payload = json.dumps({'host': host, 'key': key, 'keyLocation': key_location, 'urlList': list(urls)})
    status, _ = _http('POST', ENDPOINT, payload)
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('host', help='production hostname, e.g. www.example.com')
    parser.add_argument('--key', required=True, help='IndexNow key; https://<host>/<key>.txt must serve it')
    parser.add_argument('--url', action='append', default=[], help='changed URL (repeatable)')
    parser.add_argument('--confirm-deployed', action='store_true',
                        help='confirm the owner authorized and completed the production deploy')
    args = parser.parse_args(argv)
    try:
        status = ping(args.host, args.url, args.key, confirm_deployed=args.confirm_deployed)
    except (ValueError, PermissionError) as exc:
        print(json.dumps({'status': 'refused', 'error': str(exc)}))
        return 2
    accepted = status in {200, 202}
    print(json.dumps({'status': 'accepted' if accepted else 'rejected', 'http_status': status, 'urls': len(args.url),
                      'boundary': 'change notification only; not proof of crawling or indexing'}))
    return 0 if accepted else 1


if __name__ == '__main__':
    sys.exit(main())
