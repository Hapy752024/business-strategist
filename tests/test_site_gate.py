"""Site gate: one pre-launch command that fails closed on any check failure or missing tool."""
import json
import shutil
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from scripts.brand import site_gate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'fixtures/website/site-gate-static'
CANONICAL = 'https://stellar-repair.example'
TOOLING = ROOT / 'scripts/brand'


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def serve():
    servers = []

    def start(directory: Path) -> str:
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(directory)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f'http://127.0.0.1:{server.server_port}'

    yield start
    for server in servers:
        server.shutdown(); server.server_close()


def site_copy(tmp_path: Path) -> Path:
    site = tmp_path / 'site'
    shutil.copytree(FIXTURE, site)
    return site


def green_lighthouse(urls, out_dir, tooling_dir):
    reports = {}
    for i, url in enumerate(urls):
        path = Path(out_dir) / f'lh-{i}.json'
        path.write_text(json.dumps({
            'lighthouseVersion': '13.5.0',
            'categories': {'performance': {'score': 0.99}, 'accessibility': {'score': 1},
                           'agentic-browsing': {'score': 1, 'auditRefs': [{'id': 'agent-accessibility-tree'}]}},
            'audits': {'agent-accessibility-tree': {'score': 1, 'scoreDisplayMode': 'binary', 'title': 'tree'}}}))
        reports[url] = str(path)
    return {'version': '13.5.0', 'reports': reports, 'errors': {}}


def green_browser(base, routes, out_dir, tooling_dir):
    return {'axe': {'routes': [{'path': r, 'status': 200, 'violations': []} for r in routes]},
            'guidelines': {'routes': [{'path': r, 'status': 200, 'issues': []} for r in routes]}}


GREEN = {'lighthouse': green_lighthouse, 'browser': green_browser}


def by_id(result):
    return {check['id']: check for check in result['checks']}


def test_gate_passes_fixture_site_orchestration(tmp_path, serve):
    base = serve(FIXTURE)
    result = site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'out', runners=GREEN)
    checks = by_id(result)
    assert set(checks) == set(site_gate.CHECKS)
    assert all(c['status'] == 'pass' for c in checks.values()), checks
    assert result['verdict'] == 'pass' and site_gate.exit_code(result) == 0
    written = json.loads((tmp_path / 'out/site-gate.json').read_text())
    assert written['verdict'] == 'pass'
    for check in written['checks']:
        assert set(check) >= {'id', 'status', 'details', 'evidence_path'}
    assert written['budgets'] == {'performance': 85, 'accessibility': 95}


def test_site_gate_fails_on_canonical_mismatch(tmp_path, serve):
    site = site_copy(tmp_path)
    index = site / 'index.html'
    index.write_text(index.read_text().replace(f'href="{CANONICAL}/"', f'href="{CANONICAL}/wrong"'))
    base = serve(site)
    result = site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'out', runners=GREEN)
    seo = by_id(result)['seo_signals']
    assert seo['status'] == 'fail'
    assert any('canonical' in e and '/wrong' in e for e in seo['details']['errors'])
    assert by_id(result)['lighthouse_budgets']['status'] == 'pass'
    assert result['verdict'] == 'fail' and site_gate.exit_code(result) == 1
    # Through the CLI as well: exit 1, with the remaining checks skipped for a recorded reason.
    cli = subprocess.run([sys.executable, '-m', 'scripts.brand.site_gate', base, '--canonical-origin', CANONICAL,
                          '--out-dir', str(tmp_path / 'cli'),
                          *[arg for check in ('lighthouse_budgets', 'agentic_browsing', 'axe', 'interface_guidelines')
                            for arg in ('--skip', f'{check}=covered by the mocked run above')]],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert cli.returncode == 1, cli.stderr
    assert by_id(json.loads((tmp_path / 'cli/site-gate.json').read_text()))['seo_signals']['status'] == 'fail'


def test_tool_unavailable_fails_gate(tmp_path, serve):
    base = serve(FIXTURE)
    empty = tmp_path / 'no-tooling'
    empty.mkdir()
    result = site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'out', tooling_dir=empty)
    checks = by_id(result)
    for check in ('lighthouse_budgets', 'agentic_browsing', 'axe', 'interface_guidelines'):
        assert checks[check]['status'] == 'tool_unavailable', checks[check]
    assert checks['seo_signals']['status'] == 'pass'
    assert result['verdict'] == 'fail' and site_gate.exit_code(result) == 1


def test_agentic_category_unavailable_fails(tmp_path, serve):
    def old_lighthouse(urls, out_dir, tooling_dir):
        run = green_lighthouse(urls, out_dir, tooling_dir)
        for path in run['reports'].values():
            report = json.loads(Path(path).read_text())
            report['lighthouseVersion'] = '12.8.2'
            del report['categories']['agentic-browsing']
            Path(path).write_text(json.dumps(report))
        return {**run, 'version': '12.8.2'}
    base = serve(FIXTURE)
    result = site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'out',
                                runners={**GREEN, 'lighthouse': old_lighthouse})
    agentic = by_id(result)['agentic_browsing']
    assert agentic['status'] == 'fail'
    assert agentic['details']['reason'] == 'category_unavailable'
    assert '12.8.2' in agentic['details']['message']
    assert result['verdict'] == 'fail'


def test_budget_miss_fails(tmp_path, serve):
    def slow(urls, out_dir, tooling_dir):
        run = green_lighthouse(urls, out_dir, tooling_dir)
        path = Path(next(iter(run['reports'].values())))
        report = json.loads(path.read_text()); report['categories']['performance']['score'] = 0.84
        path.write_text(json.dumps(report))
        return run
    base = serve(FIXTURE)
    result = site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'out',
                                runners={**GREEN, 'lighthouse': slow})
    assert by_id(result)['lighthouse_budgets']['status'] == 'fail'
    assert site_gate.exit_code(result) == 1


def test_skip_requires_reason(tmp_path, serve):
    base = serve(FIXTURE)
    with pytest.raises(ValueError, match='reason'):
        site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'a', skips={'axe': '  '}, runners=GREEN)
    with pytest.raises(ValueError, match='unknown'):
        site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'b', skips={'nope': 'x'}, runners=GREEN)
    cli = subprocess.run([sys.executable, '-m', 'scripts.brand.site_gate', base, '--canonical-origin', CANONICAL,
                          '--out-dir', str(tmp_path / 'c'), '--skip', 'axe'], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert cli.returncode == 2 and 'reason' in cli.stderr
    result = site_gate.run_gate(base, canonical_origin=CANONICAL, out_dir=tmp_path / 'd',
                                skips={'axe': 'axe covered by the design-system suite'}, runners=GREEN)
    axe = by_id(result)['axe']
    assert axe['status'] == 'skipped' and axe['details']['reason'] == 'axe covered by the design-system suite'
    assert result['verdict'] == 'pass' and result['skipped'] == ['axe']


def test_llms_txt_presence_only(tmp_path, serve):
    site = site_copy(tmp_path)
    (site / 'llms.txt').write_text('anything at all, not validated')
    result = site_gate.run_gate(serve(site), canonical_origin=CANONICAL, out_dir=tmp_path / 'a', runners=GREEN)
    llms = by_id(result)['llms_txt']
    assert llms['status'] == 'pass'
    assert 'presence' in llms['details']['scope']
    (site / 'llms.txt').unlink()
    missing = by_id(site_gate.run_gate(serve(site), canonical_origin=CANONICAL, out_dir=tmp_path / 'b', runners=GREEN))['llms_txt']
    assert missing['status'] == 'fail'
    for check in (llms, missing):
        text = json.dumps(check).lower()
        assert 'rank' not in text and 'citation' not in text.replace('no citation', '')


def test_check_lighthouse_accepts_gate_json(tmp_path, serve):
    from scripts.brand import check_lighthouse
    result = site_gate.run_gate(serve(FIXTURE), canonical_origin=CANONICAL, out_dir=tmp_path / 'out', runners=GREEN)
    assert check_lighthouse.errors(result) == []
    result['checks'][0]['status'] = 'tool_unavailable'
    assert check_lighthouse.errors(result)


def _toolchain_ready() -> str | None:
    if not (TOOLING / 'node_modules/.bin/lighthouse').exists():
        return 'scripts/brand tooling not installed (npm ci in scripts/brand)'
    if not (TOOLING / 'node_modules/playwright/package.json').exists():
        return 'Playwright not installed in scripts/brand'
    if not site_gate.find_chrome():
        return 'no Chrome/Chromium executable for Lighthouse'
    return None


def test_gate_passes_fixture_site(tmp_path, serve):
    reason = _toolchain_ready()
    if reason:
        pytest.skip(reason)
    result = site_gate.run_gate(serve(FIXTURE), canonical_origin=CANONICAL, out_dir=tmp_path / 'out')
    if any(c['status'] == 'tool_unavailable' for c in result['checks']):
        pytest.skip(f'live toolchain unavailable: {by_id(result)}')
    assert result['verdict'] == 'pass', json.dumps(result['checks'], indent=2)


def test_browser_step_detects_guideline_and_axe_defects(tmp_path, serve):
    if not (TOOLING / 'node_modules/@axe-core/playwright/package.json').exists():
        pytest.skip('Playwright/axe not installed in scripts/brand')
    site = tmp_path / 'bad'
    site.mkdir()
    (site / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width, user-scalable=no">'
        '<title>Bad</title></head><body><main><h1>Bad</h1><img src="x.png"><input id="q" style="font-size:12px">'
        '<button tabindex="3"></button><div style="width:900px">wide</div></main></body></html>')
    run = site_gate.run_browser(serve(site), ['/'], tmp_path, TOOLING)
    if run.get('tool_unavailable'):
        pytest.skip(run['tool_unavailable'])
    checks = {c['id']: c for c in site_gate.evaluate_browser(run, skip_axe=False, skip_guidelines=False)}
    rules = ' '.join(checks['interface_guidelines']['details']['failures'])
    for rule in ('named-controls', 'labels-everywhere', 'images-alt', 'no-positive-tabindex', 'respect-zoom',
                 'mobile-input-size', 'no-horizontal-overflow'):
        assert rule in rules, rules
    assert checks['axe']['status'] == 'fail'


def _rewrite_reports(run, mutate):
    for path in run['reports'].values():
        report = json.loads(Path(path).read_text())
        mutate(report)
        Path(path).write_text(json.dumps(report))
    return run


@pytest.mark.parametrize('case', ['errored', 'all_not_applicable', 'runtime_error', 'missing_audit'])
def test_agentic_errored_or_untested_audits_fail(tmp_path, serve, case):
    def mutate(report):
        refs = report['categories']['agentic-browsing']['auditRefs']
        if case == 'errored':
            report['audits']['agent-accessibility-tree'] = {'score': None, 'scoreDisplayMode': 'error',
                                                            'errorMessage': 'protocol timeout'}
        elif case == 'all_not_applicable':
            report['audits']['agent-accessibility-tree'] = {'score': None, 'scoreDisplayMode': 'notApplicable'}
        elif case == 'runtime_error':
            report['runtimeError'] = {'code': 'NO_FCP'}
        else:
            refs.append({'id': 'webmcp-registered-tools'})

    def lighthouse(urls, out_dir, tooling_dir):
        return _rewrite_reports(green_lighthouse(urls, out_dir, tooling_dir), mutate)
    result = site_gate.run_gate(serve(FIXTURE), canonical_origin=CANONICAL, out_dir=tmp_path / 'out',
                                runners={**GREEN, 'lighthouse': lighthouse})
    agentic = by_id(result)['agentic_browsing']
    assert agentic['status'] == 'fail', agentic
    assert 'experimental' in agentic['details']['experimental']
    assert site_gate.exit_code(result) == 1


def test_missing_sitemap_records_coverage_limit(tmp_path, serve):
    site = site_copy(tmp_path)
    (site / 'sitemap.xml').unlink()
    result = site_gate.run_gate(serve(site), canonical_origin=CANONICAL, out_dir=tmp_path / 'out', runners=GREEN)
    checks = by_id(result)
    assert checks['seo_signals']['status'] == 'fail'
    for check in ('lighthouse_budgets', 'agentic_browsing', 'axe', 'interface_guidelines'):
        assert site_gate.NO_SITEMAP_LIMIT in checks[check]['details']['limits'], checks[check]
    with_sitemap = by_id(site_gate.run_gate(serve(FIXTURE), canonical_origin=CANONICAL, out_dir=tmp_path / 'b', runners=GREEN))
    assert 'limits' not in with_sitemap['axe']['details']


def test_sitemap_query_strings_are_kept(tmp_path, serve):
    site = site_copy(tmp_path)
    sitemap = site / 'sitemap.xml'
    sitemap.write_text(sitemap.read_text().replace('/services/</loc>', '/services/?lang=en</loc>'))
    seen = {}

    def browser(base, routes, out_dir, tooling_dir):
        seen['routes'] = routes
        return green_browser(base, routes, out_dir, tooling_dir)
    site_gate.run_gate(serve(site), canonical_origin=CANONICAL, out_dir=tmp_path / 'out',
                       runners={**GREEN, 'browser': browser})
    assert '/services/?lang=en' in seen['routes']


def test_default_out_dir_is_outside_the_repo(tmp_path, serve):
    site_dir = tmp_path / 'my-site'
    target = site_gate.default_out_dir(site_dir)
    assert target.is_absolute() and target == (site_dir / 'qa/site-gate').resolve()
    assert ROOT not in target.parents
    temp = site_gate.default_out_dir(None)
    assert temp.is_absolute() and ROOT not in temp.parents
    cli = subprocess.run([sys.executable, '-m', 'scripts.brand.site_gate', serve(FIXTURE), '--canonical-origin', CANONICAL,
                          '--site-dir', str(site_dir),
                          *[arg for check in ('lighthouse_budgets', 'agentic_browsing', 'axe', 'interface_guidelines')
                            for arg in ('--skip', f'{check}=not under test here')]],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert cli.returncode == 0, cli.stdout + cli.stderr
    assert (site_dir / 'qa/site-gate/site-gate.json').exists()
    assert not (ROOT / 'site-gate').exists()


def test_timeouts_are_recorded_and_report_written(tmp_path, serve, monkeypatch):
    tooling = tmp_path / 'tooling'
    (tooling / 'node_modules/.bin').mkdir(parents=True)
    (tooling / 'node_modules/.bin/lighthouse').write_text('')
    monkeypatch.setattr(site_gate, 'find_chrome', lambda: '/usr/bin/true')
    monkeypatch.setattr(site_gate.shutil, 'which', lambda name: '/usr/bin/node')

    def timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get('timeout'))
    monkeypatch.setattr(site_gate.subprocess, 'run', timeout)
    result = site_gate.run_gate(serve(FIXTURE), canonical_origin=CANONICAL, out_dir=tmp_path / 'out', tooling_dir=tooling)
    checks = by_id(result)
    for check in ('lighthouse_budgets', 'agentic_browsing', 'axe', 'interface_guidelines'):
        assert checks[check]['status'] in {'fail', 'tool_unavailable'}, checks[check]
    assert 'timed out' in json.dumps(checks['axe'])
    assert json.loads((tmp_path / 'out/site-gate.json').read_text())['verdict'] == 'fail'
