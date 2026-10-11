"""Inspect one known public placement; save immutable capture and observation."""
from __future__ import annotations

import argparse
import json
import sys
import http.client
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.marketing import link_observations as links
from scripts.marketing.public_fetch import fetch, validate_public_url


def inspect(source: str, target: str, *, ident: str, capture_path: str, fixture: bool = False) -> tuple[dict, bytes]:
    # Reject before constructing even a failure record or creating output files.
    validate_public_url(source)
    validate_public_url(target)
    try:
        result = fetch(source, fixture=fixture)
        if result['status'] == 200 and 'html' not in result['content_type'].lower():
            raise ValueError('placement response is not HTML')
        raw = result['raw']
        observation = links.observe(raw, source_url=source, final_url=result['final_url'], target_url=target,
            capture_path=capture_path, ident=ident, status=result['status'], redirects=result['redirects'])
    except (OSError, ValueError, http.client.HTTPException) as exc:
        # No URL or remote body in an error string; failed fetches never prove absence.
        raw = b''
        observation = links.observe(raw, source_url=source, final_url=source, target_url=target,
            capture_path=capture_path, ident=ident, status=None, reason=type(exc).__name__ + ': fetch unavailable')
    return observation, raw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True); ap.add_argument('--target', required=True)
    ap.add_argument('--id', required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--evidence-root', type=Path, help='capture binding relative to this Marketing root')
    ap.add_argument('--fixture-loopback', action='store_true', help='isolated fixture tests only')
    args = ap.parse_args()
    root = (args.evidence_root or args.out).absolute()
    try:
        capture_path = (args.out.absolute() / 'capture.html').relative_to(root).as_posix()
    except ValueError:
        ap.error('output must belong to evidence root')
    try:
        observation, raw = inspect(args.source, args.target, ident=args.id, capture_path=capture_path, fixture=args.fixture_loopback)
    except ValueError:
        ap.error('source and target must be public URLs without credentials or sensitive query parameters')
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'capture.html').write_bytes(raw)
    (args.out / 'observation.json').write_text(json.dumps(observation, indent=2) + '\n')
    print(json.dumps({'outcome': observation['outcome'], 'out': str(args.out)}))
    return 0 if observation['outcome'] in {'present', 'absent'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
