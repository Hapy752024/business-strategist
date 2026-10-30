"""Pre-launch site gate: one command that checks a built, served website and fails closed.

Checks, in order, against a base URL (a local preview or the live host):
  seo_signals          robots, sitemap and one matching canonical per sitemap URL
                       (reuses production_seo_probe; `--canonical-origin` maps a preview)
  llms_txt             /llms.txt presence only; no claim about search or AI-answer effects
  lighthouse_budgets   every sitemap URL (up to --max-urls) meets performance/accessibility
                       budgets (defaults: performance >= 85, accessibility >= 95)
  agentic_browsing     Lighthouse 'agentic-browsing' category present and its applicable
                       audits pass; category_unavailable on an older Lighthouse is a failure
  axe                  axe-core on the top routes (first 5 sitemap paths): no serious or
                       critical violations
  interface_guidelines a deterministic SUBSET of the Vercel web interface guidelines read
                       from the rendered DOM (see site_gate.mjs); rules are local, not fetched

Writes <out-dir>/site-gate.json with per-check {id, status, details, evidence_path} and
exits 1 when any check fails or a tool is unavailable. `--skip CHECK=REASON` records a skip;
a skip without a reason is refused. The gate never deploys, pings search engines or edits
the site; IndexNow lives in indexnow_ping.py and runs only after an authorized deploy.
Install the pinned tooling with `npm ci` in scripts/brand.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from scripts.brand import production_seo_probe as probe
from scripts.brand.seo_checks import sitemap_urls

HERE = Path(__file__).resolve().parent
CHECKS = ('seo_signals', 'llms_txt', 'lighthouse_budgets', 'agentic_browsing', 'axe', 'interface_guidelines')
STATUSES = {'pass', 'fail', 'tool_unavailable', 'skipped'}
DEFAULT_BUDGETS = {'performance': 85, 'accessibility': 95}
AXE_ROUTES = 5
AXE_BLOCKING = {'serious', 'critical'}
MAX_URLS = 50
CHROME_CANDIDATES = ('/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium',
                     '/usr/bin/chromium-browser', '/snap/bin/chromium')


def _check(check_id: str, status: str, details: dict, evidence: Path | str | None = None) -> dict:
    assert status in STATUSES
    return {'id': check_id, 'status': status, 'details': details,
            'evidence_path': str(evidence) if evidence else None}


def _origin(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in {'http', 'https'} or not parts.netloc or parts.username or parts.password \
            or parts.query or parts.fragment or parts.path not in {'', '/'}:
        raise ValueError(f'expected a credential-free http(s) origin, got {url!r}')
    return f'{parts.scheme}://{parts.netloc}'


def find_chrome() -> str | None:
    env = os.environ.get('CHROME_PATH')
    if env and Path(env).exists():
        return env
    return next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)


# ---- tool runners (replaceable in tests) ---------------------------------------------------

def run_lighthouse(urls: list[str], out_dir: Path, tooling_dir: Path) -> dict:
    """Run Lighthouse once per URL with the three gate categories; returns report paths."""
    binary = Path(tooling_dir) / 'node_modules/.bin/lighthouse'
    if not binary.exists():
        return {'unavailable': f'lighthouse not installed at {binary} (run npm ci in scripts/brand)'}
    chrome = find_chrome()
    if not chrome:
        return {'unavailable': 'no Chrome/Chromium executable found (set CHROME_PATH)'}
    version = subprocess.run([str(binary), '--version'], capture_output=True, text=True, timeout=60).stdout.strip()
    out = (Path(out_dir) / 'lighthouse').resolve()
    out.mkdir(parents=True, exist_ok=True)
    reports, errors = {}, {}
    for i, url in enumerate(urls):
        path = out / f'{i:03d}.json'
        proc = subprocess.run([str(binary), url, '--only-categories=agentic-browsing,accessibility,performance',
                               '--output=json', f'--output-path={path}', '--quiet',
                               '--chrome-flags=--headless=new --no-sandbox'],
                              capture_output=True, text=True, timeout=300, env={**os.environ, 'CHROME_PATH': chrome},
                              cwd=out)  # chrome-launcher on WSL writes profile dirs relative to cwd
        if proc.returncode == 0 and path.exists():
            reports[url] = str(path)
        else:
            errors[url] = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or [f'exit {proc.returncode}']
    return {'version': version or None, 'reports': reports, 'errors': errors}


def run_browser(base: str, routes: list[str], out_dir: Path, tooling_dir: Path) -> dict:
    """Run site_gate.mjs (axe + guideline subset) and return its parsed JSON."""
    node = shutil.which('node')
    if not node:
        return {'tool_unavailable': 'node is not on PATH'}
    routes_file, out_file = Path(out_dir) / 'routes.json', Path(out_dir) / 'browser.json'
    routes_file.write_text(json.dumps(routes))
    proc = subprocess.run([node, str(HERE / 'site_gate.mjs'), base, str(routes_file), str(out_file), str(tooling_dir)],
                          capture_output=True, text=True, timeout=600)
    if not out_file.exists():
        return {'error': f'browser step exited {proc.returncode} without output: {proc.stderr.strip()[-300:]}'}
    return {**json.loads(out_file.read_text()), 'evidence_path': str(out_file)}


# ---- check evaluation ----------------------------------------------------------------------

def check_seo(base: str, canonical: str, out_dir: Path) -> tuple[dict, list[str]]:
    obs = probe.collect(canonical, fetch_origin=base if base != canonical else None)
    result = probe.analyze(canonical, obs)
    evidence = out_dir / 'seo-probe.json'
    evidence.write_text(json.dumps(result, indent=2))
    try:
        urls = sitemap_urls(obs['sitemap'].get('body') or '')[0] if obs['sitemap'].get('status') == 200 else []
    except Exception:
        urls = []
    paths = list(dict.fromkeys(urlsplit(u).path or '/' for u in urls if probe._host(u) == probe._host(canonical)))
    details = {'errors': result['errors'], 'warnings': result['warnings'], 'limits': result['limits'],
               'sitemap_urls': result['sitemap_urls'], 'boundary': result['boundary']}
    return _check('seo_signals', 'fail' if result['errors'] else 'pass', details, evidence), paths or ['/']


def check_llms_txt(base: str) -> dict:
    seen = probe._fetch(base + '/llms.txt', 20)
    present = seen.get('status') == 200 and bool((seen.get('body') or '').strip())
    return _check('llms_txt', 'pass' if present else 'fail', {
        'status_code': seen.get('status'), 'present': present,
        'scope': 'presence only: /llms.txt answers 200 with a non-empty body; content is not validated '
                 'and no search or AI-answer effect is claimed'})


def evaluate_lighthouse(run: dict, budgets: dict, *, skip_budgets: bool, skip_agentic: bool) -> list[dict]:
    if run.get('unavailable'):
        return [_check(cid, 'tool_unavailable', {'message': run['unavailable']})
                for cid, skip in (('lighthouse_budgets', skip_budgets), ('agentic_browsing', skip_agentic)) if not skip]
    reports = {url: json.loads(Path(path).read_text()) for url, path in run.get('reports', {}).items()}
    version = run.get('version') or next((r.get('lighthouseVersion') for r in reports.values()), None)
    run_errors = {url: msg for url, msg in run.get('errors', {}).items()}
    evidence = str(Path(next(iter(run['reports'].values()))).parent) if run.get('reports') else None
    out = []
    if not skip_budgets:
        misses = [f'{url}: Lighthouse did not complete ({" ".join(msg)})' for url, msg in run_errors.items()]
        scores = {}
        for url, report in reports.items():
            if report.get('runtimeError'):
                misses.append(f'{url}: runtime error {report["runtimeError"].get("code")}')
            scores[url] = {}
            for cat, floor in budgets.items():
                score = (report.get('categories', {}).get(cat) or {}).get('score')
                scores[url][cat] = None if score is None else round(score * 100)
                if score is None or score * 100 < floor:
                    misses.append(f'{url}: {cat} {scores[url][cat]} below budget {floor}')
        out.append(_check('lighthouse_budgets', 'fail' if misses or not reports else 'pass',
                          {'budgets': budgets, 'scores': scores, 'failures': misses, 'lighthouse_version': version,
                           'boundary': 'lab runs (mobile emulation); not field Core Web Vitals'}, evidence))
    if not skip_agentic:
        failing, per_url, missing = [], {}, []
        for url, report in reports.items():
            category = report.get('categories', {}).get('agentic-browsing')
            if not category:
                missing.append(url)
                continue
            audits = {}
            for ref in category.get('auditRefs', []):
                audit = report.get('audits', {}).get(ref['id'], {})
                audits[ref['id']] = audit.get('score') if audit.get('score') is not None else audit.get('scoreDisplayMode')
                if audit.get('score') is not None and audit['score'] < 0.9:
                    failing.append(f'{url}: {ref["id"]} ({audit.get("title", "")}) score {audit["score"]}')
            per_url[url] = {'category_score': category.get('score'), 'audits': audits}
        if missing or (not reports and not run_errors):
            out.append(_check('agentic_browsing', 'fail', {
                'reason': 'category_unavailable',
                'message': f'installed Lighthouse {version} produced no agentic-browsing category '
                           f'(introduced in Lighthouse 13.3); upgrade the pinned version', 'urls': missing}, evidence))
        else:
            failing += [f'{url}: Lighthouse did not complete' for url in run_errors]
            out.append(_check('agentic_browsing', 'fail' if failing else 'pass', {
                'failures': failing, 'results': per_url, 'lighthouse_version': version,
                'rule': 'every applicable (scored) audit in the category scores >= 0.9; not-applicable audits are recorded',
                'boundary': 'Lighthouse marks this category as under development'}, evidence))
    return out


def evaluate_browser(run: dict, *, skip_axe: bool, skip_guidelines: bool) -> list[dict]:
    wanted = [cid for cid, skip in (('axe', skip_axe), ('interface_guidelines', skip_guidelines)) if not skip]
    evidence = run.get('evidence_path')
    if run.get('tool_unavailable'):
        return [_check(cid, 'tool_unavailable', {'message': run['tool_unavailable']}, evidence) for cid in wanted]
    out = []
    if 'axe' in wanted:
        routes = run.get('axe', {}).get('routes', [])
        blocking = [f'{r["path"]}: {v["id"]} ({v["impact"]}, {v["nodes"]} nodes) {v["help"]}'
                    for r in routes for v in r['violations'] if v.get('impact') in AXE_BLOCKING]
        advisory = [f'{r["path"]}: {v["id"]} ({v["impact"]})' for r in routes for v in r['violations']
                    if v.get('impact') not in AXE_BLOCKING]
        failures = blocking + [f'{r["path"]}: HTTP {r["status"]}' for r in routes if r.get('status') != 200]
        if run.get('error'):
            failures.append(f'browser step aborted: {run["error"]}')
        out.append(_check('axe', 'fail' if failures or not routes else 'pass', {
            'routes': [r['path'] for r in routes], 'failures': failures, 'advisory': advisory,
            'rule': 'no serious or critical axe violations on the top routes'}, evidence))
    if 'interface_guidelines' in wanted:
        routes = run.get('guidelines', {}).get('routes', [])
        issues = [f'{r["path"]}: {i["rule"]} {i["target"]}' for r in routes for i in r['issues']]
        if run.get('error'):
            issues.append(f'browser step aborted: {run["error"]}')
        out.append(_check('interface_guidelines', 'fail' if issues or not routes else 'pass', {
            'failures': issues, 'routes': [r['path'] for r in routes],
            'subset': sorted((run.get('guidelines') or {}).get('subset', {})),
            'source': 'https://github.com/vercel-labs/web-interface-guidelines',
            'boundary': 'deterministic DOM-observable subset only; not a full guideline review'}, evidence))
    return out


# ---- orchestration -------------------------------------------------------------------------

def run_gate(base: str, *, out_dir: Path, canonical_origin: str | None = None, skips: dict[str, str] | None = None,
             budgets: dict | None = None, tooling_dir: Path = HERE, max_urls: int = MAX_URLS,
             runners: dict | None = None) -> dict:
    skips = dict(skips or {})
    for check_id, reason in skips.items():
        if check_id not in CHECKS:
            raise ValueError(f'unknown check {check_id!r}; choose from {", ".join(CHECKS)}')
        if not (reason or '').strip():
            raise ValueError(f'--skip {check_id} needs a reason (CHECK=REASON)')
    base, canonical = _origin(base), _origin(canonical_origin or base)
    budgets = {**DEFAULT_BUDGETS, **(budgets or {})}
    runners = {'lighthouse': run_lighthouse, 'browser': run_browser, **(runners or {})}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}

    seo, paths = check_seo(base, canonical, out_dir)
    results['seo_signals'] = seo
    results['llms_txt'] = check_llms_txt(base)
    urls = [base + p for p in paths]
    limits = [f'{len(urls)} sitemap URLs; Lighthouse ran on the first {max_urls}'] if len(urls) > max_urls else []
    if not ({'lighthouse_budgets', 'agentic_browsing'} <= skips.keys()):
        run = runners['lighthouse'](urls[:max_urls], out_dir, tooling_dir)
        for check in evaluate_lighthouse(run, budgets, skip_budgets='lighthouse_budgets' in skips,
                                         skip_agentic='agentic_browsing' in skips):
            if limits:
                check['details']['limits'] = limits
            results[check['id']] = check
    if not ({'axe', 'interface_guidelines'} <= skips.keys()):
        run = runners['browser'](base, paths[:AXE_ROUTES], out_dir, tooling_dir)
        for check in evaluate_browser(run, skip_axe='axe' in skips, skip_guidelines='interface_guidelines' in skips):
            results[check['id']] = check
    for check_id, reason in skips.items():
        results[check_id] = _check(check_id, 'skipped', {'reason': reason.strip()})

    checks = [results[cid] for cid in CHECKS]
    blocking = [c['id'] for c in checks if c['status'] in {'fail', 'tool_unavailable'}]
    gate = {'schema': 'site-gate/v1', 'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'base_url': base, 'canonical_origin': canonical, 'budgets': budgets,
            'verdict': 'fail' if blocking else 'pass', 'blocking': blocking,
            'skipped': [c['id'] for c in checks if c['status'] == 'skipped'], 'checks': checks,
            'boundary': 'automated pre-launch checks only; not rankings, field performance or a full accessibility audit'}
    (out_dir / 'site-gate.json').write_text(json.dumps(gate, indent=2))
    return gate


def exit_code(gate: dict) -> int:
    return 1 if gate['verdict'] != 'pass' or any(c['status'] in {'fail', 'tool_unavailable'} for c in gate['checks']) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('base_url', help='served site origin, e.g. http://127.0.0.1:3000 or https://www.example.com')
    parser.add_argument('--canonical-origin', help='production origin the canonicals/sitemap name (defaults to base_url)')
    parser.add_argument('--out-dir', type=Path, default=Path('site-gate'), help='evidence directory (site-gate.json lands here)')
    parser.add_argument('--skip', action='append', default=[], metavar='CHECK=REASON')
    parser.add_argument('--min-performance', type=int, default=DEFAULT_BUDGETS['performance'])
    parser.add_argument('--min-accessibility', type=int, default=DEFAULT_BUDGETS['accessibility'])
    parser.add_argument('--max-urls', type=int, default=MAX_URLS, help='Lighthouse URL cap (sitemap order)')
    parser.add_argument('--tooling-dir', type=Path, default=HERE, help='directory whose node_modules holds the pinned tools')
    args = parser.parse_args(argv)
    skips = {}
    for item in args.skip:
        check_id, _, reason = item.partition('=')
        if not reason.strip():
            parser.error(f'--skip {check_id} needs a reason: --skip {check_id}="why this check does not apply"')
        skips[check_id.strip()] = reason
    try:
        gate = run_gate(args.base_url, out_dir=args.out_dir, canonical_origin=args.canonical_origin, skips=skips,
                        budgets={'performance': args.min_performance, 'accessibility': args.min_accessibility},
                        tooling_dir=args.tooling_dir, max_urls=args.max_urls)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({'verdict': gate['verdict'], 'checks': {c['id']: c['status'] for c in gate['checks']},
                      'report': str(args.out_dir / 'site-gate.json')}, indent=2))
    return exit_code(gate)


if __name__ == '__main__':
    sys.exit(main())
