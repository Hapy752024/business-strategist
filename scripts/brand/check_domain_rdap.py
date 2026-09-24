#!/usr/bin/env python3
"""Preliminary domain availability via public RDAP. A registrar confirms availability."""
from __future__ import annotations
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def check(name: str, tlds: list[str]) -> list[dict]:
    rows = []
    for tld in tlds:
        domain = f"{name.lower()}.{tld.strip().lstrip('.')}"
        url = f"https://rdap.org/domain/{domain}"
        status = 'unknown'
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                status = 'registered' if resp.status == 200 else 'unknown'
        except urllib.error.HTTPError as exc:
            status = 'available' if exc.code == 404 else 'unknown'
        except (urllib.error.URLError, TimeoutError):
            status = 'unknown'
        rows.append({'domain': domain, 'status': status, 'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'source': url})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('name')
    ap.add_argument('--tlds', default='com,de,io,co')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    rows = check(args.name, [t.strip() for t in args.tlds.split(',') if t.strip()])
    text = json.dumps(rows, indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
