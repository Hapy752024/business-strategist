#!/usr/bin/env python3
"""Research data-source health for the founder: what works, what needs funding, what needs a key.

Joins the provider validators (`scripts/validate_apis/run_all.py`, live by default or `--cached`) with
`config/provider-billing.json` (where to top up or get a key) and `config/source-capabilities.json` (which
research capabilities a provider feeds). Prints key names only, never values. A validator failure is a
coverage gap to fix, never evidence about the market.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / 'scripts/validate_apis'
sys.path.insert(0, str(VALIDATORS))
from common import OUTPUT_DIR as CACHE, redact_sensitive  # noqa: E402
from readiness import load_latest  # noqa: E402

# Validator status -> (action, priority). Lower priority sorts first.
ACTIONS = {
    'insufficient_credits': ('fund', 0), 'billing_required': ('fund', 0), 'request_budget_exhausted': ('fund', 0),
    'missing_credentials': ('add_key', 1), 'permission_denied': ('renew_key', 1), 'token_expired': ('renew_key', 1),
    'scope_denied': ('renew_key', 1),
    'account_verification_required': ('verify_account', 1), 'missing_cli': ('install', 3),
    'optional_unavailable': ('optional', 4), 'rate_limited': ('wait', 2), 'network_blocked_or_sandboxed': ('network', 2),
    'ok': ('ready', 5),
}


def load_config(name: str) -> dict:
    return json.loads((ROOT / 'config' / name).read_text(encoding='utf-8'))


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def capabilities_by_provider() -> dict[str, list[str]]:
    feeds: dict[str, list[str]] = {}
    for cap in load_config('source-capabilities.json')['capabilities']:
        for provider in cap.get('validation_providers') or []:
            feeds.setdefault(provider, []).append(cap['id'])
    return feeds


def _env_names(result: dict, billing: dict) -> list[str]:
    # The billing file names keys reliably; validator fields vary (a dict of sources, or "none (keyless)").
    names = billing.get('env') or result.get('required_env') or result.get('credential_source') or []
    names = [names] if isinstance(names, str) else names if isinstance(names, list) else []
    return [n for n in names if isinstance(n, str) and not n.startswith('none')]


def advise(result: dict, billing: dict, feeds: list[str]) -> dict:
    """One founder-facing row for one validator result."""
    stale = result.get('status') == 'stale'
    status = result.get('observed_status', 'failed') if stale else result.get('status', 'failed')
    action, priority = ACTIONS.get(status, ('check', 2))
    if status == 'missing_credentials' and billing.get('optional_when_missing'):
        action, priority = ACTIONS['optional_unavailable']
    env = _env_names(result, billing)
    fund_url, keys_url = billing.get('fund_url'), billing.get('keys_url') or result.get('docs')
    todo = {
        'fund': f"Top up or upgrade at {fund_url or keys_url or 'the provider dashboard'}",
        'add_key': f"Add {', '.join(env) or 'the key'} to ~/.secrets" + (f" (get it at {keys_url})" if keys_url else ''),
        'renew_key': f"Replace {', '.join(env) or 'the key'} in ~/.secrets" + (f" (new one at {keys_url})" if keys_url else ''),
        'verify_account': f"Complete account verification at {keys_url or fund_url or 'the provider dashboard'}",
        'install': 'Install the CLI (optional local extractor)',
        'optional': 'Optional; nothing to do unless this source is needed',
        'wait': 'Rate limited; rerun later',
        'network': 'Network blocked from this machine; rerun from a normal connection',
        'ready': '',
        'check': f"Validator reported {status}; inspect {_rel(CACHE)}/{result.get('provider')}.json",
    }[action]
    if billing.get('note') and action != 'ready':
        todo += f" ({billing['note']})"
    row = {'provider': result.get('provider'), 'label': billing.get('label', result.get('provider')),
           'status': status, 'stale': stale, 'action': action, 'todo': todo, 'billing': billing.get('billing', 'unknown'), 'feeds': feeds,
           'checked_at': result.get('validated_at'), 'priority': priority}
    for key in ('balance_usd', 'balance', 'credits_remaining', 'remaining'):
        if isinstance(result.get(key), (int, float)):
            row['balance'] = {'field': key, 'value': result[key]}
    return row


def collect(providers: list[str], cached: bool) -> list[dict]:
    if cached:
        latest = load_latest(CACHE)
        return [r for name, r in sorted(latest.items()) if not providers or name in providers]
    command = [sys.executable, str(VALIDATORS / 'run_all.py')] + [a for p in providers for a in ('--provider', p)]
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, list):
        raise SystemExit(f'run_all.py produced no result list (exit {proc.returncode}): {redact_sensitive(proc.stderr[-500:])}')
    return [r for r in parsed if isinstance(r, dict)]


def report(results: list[dict]) -> list[dict]:
    billing = load_config('provider-billing.json')['providers']
    feeds = capabilities_by_provider()
    rows = [advise(r, billing.get(r.get('provider', ''), {}), feeds.get(r.get('provider', ''), [])) for r in results]
    return sorted(rows, key=lambda r: (r['priority'], r['provider'] or ''))


def _status(row: dict, text: str | None = None) -> str:
    text = row['status'] if text is None else text
    return f"{text} (as of {(row['checked_at'] or 'unknown')[:10]})" if row['stale'] else text


def render(rows: list[dict]) -> str:
    acting = [r for r in rows if r['action'] not in {'ready', 'optional', 'install'}]
    lines = ['# Research data-source health', '',
             f"{sum(r['action'] == 'ready' for r in rows)} ready, {len(acting)} need you, "
             f"{sum(r['action'] in {'optional', 'install'} for r in rows)} optional of {len(rows)} checked.", '']
    if acting:
        lines += ['## What to do', '', '| Source | Status | Do this | Blocks |', '|---|---|---|---|']
        lines += [f"| {r['label']} | {_status(r)} | {r['todo']} | {', '.join(r['feeds']) or '-'} |" for r in acting]
        lines.append('')
    funded = [r for r in rows if r.get('balance')]
    if funded:
        lines += ['## Reported balances', '']
        lines += [f"- {r['label']}: {r['balance']['value']} ({r['balance']['field']})" for r in funded]
        lines.append('')
    lines += ['## Ready', '', ', '.join(_status(r, r['label']) for r in rows if r['action'] == 'ready') or 'none', '']
    if any(r['stale'] for r in rows):
        lines += ['Results marked "as of" are older than 24 hours; run without `--cached` for a live check.', '']
    lines += [
              'A failing source is a coverage gap, not evidence about the market. Paid research spend is pre-authorized; '
              'funding an account is the founder\'s step.']
    return '\n'.join(lines) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--provider', action='append', default=[], help='validator provider name (repeatable)')
    ap.add_argument('--cached', action='store_true', help='use the latest saved validator results instead of live checks')
    ap.add_argument('--json', action='store_true', help='print JSON rows instead of Markdown')
    ap.add_argument('--out', type=Path, help='also write the Markdown report here')
    args = ap.parse_args()
    rows = report(collect(args.provider, args.cached))
    text = render(rows)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding='utf-8')
    print(json.dumps(rows, indent=2) if args.json else text)
    return 0 if all(r['action'] in {'ready', 'optional', 'install'} for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
