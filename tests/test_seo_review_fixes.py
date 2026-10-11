"""Regression reproductions from the SEO implementation review."""
import json
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from scripts import case_workspace as cases, subprojects
from scripts.brand.compare_seo_audits import compare
from scripts.marketing import execution, public_fetch, link_observations as links
from scripts.marketing.verify_links import inspect
from test_link_observations import packet

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/marketing/earned-media'


def publish(root, files, ident):
    subprojects.publish_marketing_workstream(root, files,
        expected_manifest_revision=cases.read_project(root)['manifest_revision'],
        decision_id=ident, reason='Reviewed regression fixture publication', status='complete')


def test_inert_templates_cannot_complete_and_cannot_override_base(tmp_path):
    plan, files = packet(b'<template><template><a href="https://asset.example/guide">Hidden</a></template></template>')
    assert not execution.scope_complete(plan, tmp_path, files)
    plan, files = packet(b'<template/><a href="https://asset.example/guide">Still inert</a>')
    assert not execution.scope_complete(plan, tmp_path, files)
    raw = b'<template><base href="https://wrong.example/"></template><base href="https://asset.example/"><a href="guide">Live</a>'
    plan, files = packet(raw)
    assert execution.scope_complete(plan, tmp_path, files)


@pytest.mark.parametrize('field', ['source', 'target'])
def test_sensitive_url_is_rejected_without_artifacts_or_diagnostics(tmp_path, field):
    source, target = 'https://publisher.example/', 'https://asset.example/guide'
    bad = 'https://example.test/?token=SYNTHETIC_SECRET'
    if field == 'source': source = bad
    else: target = bad
    with pytest.raises(ValueError, match='sensitive'):
        inspect(source, target, ident='one', capture_path='capture.html')
    out = tmp_path / 'capture'
    result = subprocess.run([sys.executable, 'scripts/marketing/verify_links.py', '--source', source,
        '--target', target, '--id', 'one', '--out', str(out)], capture_output=True, text=True)
    assert result.returncode != 0
    assert not out.exists()
    assert 'SYNTHETIC_SECRET' not in result.stdout + result.stderr


def test_failed_or_unknown_audit_coverage_cannot_resolve_defects():
    before = {'schema_version':1,'checker_version':'seo-audit-v2','site_identity':'site',
        'inventory_sha256':'a','config_sha256':'b','source_revision':'one',
        'checked_at':'2026-10-01T00:00:00Z','errors':['canonical'],
        'coverage':{'complete':True,'routes':['/']}}
    after = {**before, 'source_revision':'two','checked_at':'2026-10-02T00:00:00Z',
        'errors':['browser failed'],'coverage':{'complete':False,'routes':[]}}
    assert compare(before, after)['status'] == 'non_comparable'
    del after['coverage']
    assert compare(before, after)['status'] == 'non_comparable'
    after.update(errors=[], coverage={'complete':True,'routes':['/']})
    assert compare(before, after)['resolved'] == ['canonical']
    after['seo_limits'] = ['/: robots policy requires review (missing or extended syntax)']
    assert compare(before, after)['status'] == 'non_comparable'


def test_opportunity_provenance_checked_on_publication_source_change_and_resume(tmp_path):
    root=tmp_path/'workspace';subprojects.start(root,'marketing','Test','Discover opportunities')
    raw=(FIXTURE/'publisher.txt').read_bytes()
    row=json.loads((FIXTURE/'opportunity.json').read_text())
    publish(root, {'earned-media/opportunities.json':json.dumps([row]), 'publisher.txt':raw}, 'initial')
    revision=cases.read_project(root)['manifest_revision']
    with pytest.raises(ValueError, match='digest changed'):
        publish(root, {'publisher.txt':b'Eligibility revoked'}, 'stale')
    assert cases.read_project(root)['manifest_revision'] == revision
    destination=subprojects.path(root,'marketing')
    (destination/'publisher.txt').write_bytes(b'Eligibility revoked')
    status=subprojects.validate_marketing_workstream(root)
    assert not status['valid_for_use']
    assert any('marketing artifact earned-media/opportunities.json' in e for e in status['stale_bindings'])
    publish(root, {'publisher.txt':raw}, 'restore')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']


@pytest.mark.parametrize('damaged', ['capture.html', 'observation.json'])
@pytest.mark.parametrize('missing', [False, True])
def test_restore_original_evidence_without_rewriting_history(tmp_path, damaged, missing):
    root=tmp_path/'workspace';subprojects.start(root,'marketing','Test','Verify placement')
    plan, files=packet()
    publish(root, files | {'execution-plan.json':json.dumps(plan)}, 'initial')
    destination=subprojects.path(root,'marketing')
    if missing: (destination/damaged).unlink()
    else: (destination/damaged).write_bytes(b'corrupted')
    assert not subprojects.validate_marketing_workstream(root)['valid_for_use']
    publish(root, {damaged:files[damaged]}, 'restore')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    with pytest.raises(ValueError, match='immutable'):
        publish(root, {damaged:b'different history'}, 'rewrite')


def test_trickled_headers_obey_total_deadline(monkeypatch):
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.recv(8192)
            try:
                self.request.sendall(b'HTTP/1.1 200 OK\r\n')
                for _ in range(40):
                    time.sleep(.025)
                    self.request.sendall(b'X-Filler: a\r\n')
                self.request.sendall(b'Content-Length: 0\r\n\r\n')
            except OSError:
                pass
    with socketserver.TCPServer(('127.0.0.1',0), Handler) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        monkeypatch.setattr(public_fetch,'TIMEOUT',.15)
        start=time.monotonic()
        try:
            with pytest.raises(TimeoutError):
                public_fetch.fetch(f'http://127.0.0.1:{server.server_address[1]}/',fixture=True)
            assert time.monotonic()-start < .6
        finally:
            server.shutdown();thread.join()
