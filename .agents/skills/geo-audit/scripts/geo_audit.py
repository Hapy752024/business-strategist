#!/usr/bin/env python3
"""Thin wrapper around the pinned GEO Optimizer CLI (`geo audit`) for a public URL.

Never installs anything. Reports `tool_unavailable` when the CLI is missing, `needs_public_url` for
local/private targets (the upstream tool refuses them), and never replaces an existing output file.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

UPSTREAM = 'https://github.com/Auriti-Labs/geo-optimizer-skill'
PINNED_COMMIT = '7ecec864690ee430e954a95352130cf47e2c92cc'
PINNED_VERSION = '4.19.9'
HYGIENE = ('llms', 'ai_discovery', 'schema')
BOUNDARY = ('Readiness rubric from GEO Optimizer; not a ranking, citation rate or traffic forecast. '
            'llms.txt, AI discovery files and JSON-LD are hygiene: Google says Search ignores AI text files '
            'and needs no special schema; Ahrefs (2026-05) found schema effects on AI citations within noise.')


def emit(status: str, code: int, **extra) -> int:
    print(json.dumps({'status': status, 'pinned_commit': PINNED_COMMIT, **extra}))
    return code


def public_url(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    if parts.scheme not in ('http', 'https') or not host or parts.username or parts.password:
        return False
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')) or '.' not in host:
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True


def find_tool() -> str | None:
    configured = os.environ.get('GEO_AUDIT_BIN')
    if configured:
        return configured if Path(configured).is_file() and os.access(configured, os.X_OK) else None
    return shutil.which('geo')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url', required=True, help='Public URL (production or deployed preview)')
    ap.add_argument('--out', type=Path, required=True, help='New JSON file; existing paths are never replaced')
    ap.add_argument('--max-pages', type=int, help='Audit up to N sitemap pages (upstream range 2-500)')
    ap.add_argument('--timeout', type=int, default=600)
    args = ap.parse_args()
    if not public_url(args.url):
        return emit('needs_public_url', 2, message='Upstream audits public URLs only; deploy a preview or use production.')
    tool = find_tool()
    if not tool:
        return emit('tool_unavailable', 2, message='geo CLI not found; see .agents/skills/geo-audit/VENDOR.md. Nothing was audited.')
    if args.out.exists() or args.out.is_symlink():
        return emit('fail', 1, message='--out exists; choose a new path')
    command = [tool, 'audit', '--url', args.url, '--format', 'json', '--no-plugins']
    if args.max_pages:
        command += ['--max-pages', str(args.max_pages)]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
        raw = json.loads(proc.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return emit('audit_failed', 1, message=type(exc).__name__)
    if proc.returncode != 0 or not isinstance(raw, dict) or raw.get('error'):
        return emit('audit_failed', 1, message=str(raw.get('error') if isinstance(raw, dict) else 'unexpected output')[:300],
                    exit_code=proc.returncode)
    try:
        version = subprocess.run([tool, '--version'], capture_output=True, text=True, timeout=30).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        version = None
    record = {'schema_version': 1, 'audited_url': args.url,
              'collected_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'tool': {'name': 'geo-optimizer', 'upstream': UPSTREAM, 'pinned_commit': PINNED_COMMIT,
                       'expected_version': PINNED_VERSION, 'reported_version': version},
              'boundary': BOUNDARY, 'hygiene_categories': list(HYGIENE), 'raw': raw}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.out.open('x', encoding='utf-8') as handle:
            handle.write(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    except OSError as exc:
        return emit('fail', 1, message=type(exc).__name__)
    return emit('ok', 0, out=str(args.out), score=raw.get('score'), band=raw.get('band'),
                score_version=raw.get('score_version'), reported_version=version)


if __name__ == '__main__':
    raise SystemExit(main())
