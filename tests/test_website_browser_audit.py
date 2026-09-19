"""Execute the real optional browser auditor against a controlled HTTP fixture."""
import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'fixtures/website/stellar-repair'


@pytest.mark.parametrize('broken,redirect', [(False, None), (True, None), (False, '/'), (True, '/wrong')])
def test_browser_audit(tmp_path, broken, redirect):
    if not (PROJECT / 'node_modules/playwright/package.json').exists():
        pytest.skip('optional site Playwright dependency not installed')
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, mime = 200, 'text/html'
            if self.path == '/old':
                self.send_response(301); self.send_header('Location', redirect or '/'); self.end_headers(); return
            if self.path == '/robots.txt':
                content = b'User-agent: *\nAllow: /'
                mime = 'text/plain'
            elif self.path == '/sitemap.xml':
                content = b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
                mime = 'application/xml'
            elif self.path == '/og.svg':
                content = b'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"></svg>'
                mime = 'image/svg+xml'
            elif self.path == '/':
                content = ('<html><head><title>Test garden</title>' + ('' if broken and not redirect else '<meta name="description" content="A useful garden">') + '<meta property="og:image" content="https://example.com/og.svg"><link rel="canonical" href="https://example.com/"></head><body><a id="cta" href="/">Start</a><div style="height:2000px"></div><a id="sticky" href="/" style="position:fixed;bottom:0">Start</a></body></html>').encode()
            else:
                status, content = 404, b'<h1>Not found</h1><a href="/">Home</a>'
            self.send_response(status); self.send_header('Content-Type',mime); self.end_headers(); self.wfile.write(content)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    routes = tmp_path / 'routes.json'
    inventory = [{'path':'/','conversion':True,'cta':'#cta','stickyCta':'#sticky'}]
    if redirect: inventory.append({'path':'/old', 'conversion':False, 'redirect':{'status':301, 'to':'/'}})
    routes.write_text(json.dumps(inventory))
    try:
        result = subprocess.run(['node', str(ROOT/'scripts/brand/audit_web_pages.mjs'), str(PROJECT), f'http://127.0.0.1:{server.server_port}', str(routes)], capture_output=True, text=True, timeout=90)
        report = json.loads(result.stdout)
        if any('Executable doesn' in e for e in report['errors']):
            pytest.skip('optional Chromium browser not installed')
        assert result.returncode == int(broken), report
        assert bool(report['errors']) == broken
        assert 'no launch assessment promotion' in report['boundary']
    finally:
        server.shutdown(); server.server_close(); thread.join()


def test_browser_audit_never_fetches_uninventoried_or_query_links(tmp_path):
    if not (PROJECT / 'node_modules/playwright/package.json').exists():
        pytest.skip('optional site Playwright dependency not installed')

    requested = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requested.append(self.path)
            status, mime = 200, 'text/html'
            if self.path == '/robots.txt':
                content, mime = b'User-agent: *\nAllow: /', 'text/plain'
            elif self.path == '/sitemap.xml':
                content, mime = b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', 'application/xml'
            elif self.path == '/og.svg':
                content, mime = b'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"></svg>', 'image/svg+xml'
            elif self.path == '/':
                content = (
                    '<html><head><title>Safe links</title><meta name="description" content="A safe fixture">'
                    '<meta property="og:image" content="https://example.com/og.svg">'
                    '<link rel="canonical" href="https://example.com/"></head><body>'
                    '<a href="/danger?token=secret-value">Query</a>'
                    '<a href="/unlisted">Unknown</a></body></html>'
                ).encode()
            else:
                status, content = 404, b'<h1>Not found</h1>'
            self.send_response(status); self.send_header('Content-Type', mime); self.end_headers(); self.wfile.write(content)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    routes = tmp_path / 'routes.json'
    routes.write_text(json.dumps([{'path': '/', 'conversion': False}]))
    try:
        result = subprocess.run(
            ['node', str(ROOT/'scripts/brand/audit_web_pages.mjs'), str(PROJECT), f'http://127.0.0.1:{server.server_port}', str(routes)],
            capture_output=True, text=True, timeout=90,
        )
        report = json.loads(result.stdout)
        if any('Executable doesn' in e for e in report['errors']):
            pytest.skip('optional Chromium browser not installed')
        assert result.returncode == 1
        assert any('query parameters and was not fetched: /danger' in error for error in report['errors'])
        assert any('not inventoried and was not fetched: /unlisted' in error for error in report['errors'])
        assert 'secret-value' not in result.stdout
        assert not any(path.startswith('/danger') for path in requested)
        assert '/unlisted' not in requested
    finally:
        server.shutdown(); server.server_close(); thread.join()
