import json
from pathlib import Path
import urllib.error
from scripts.brand import check_domain_rdap as rdap

ROOT = Path(__file__).resolve().parents[2]


def test_status_mapping(monkeypatch):
    def fake_open(url, timeout=10):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
        if url.endswith('taken.com'):
            return Response()
        raise urllib.error.HTTPError(url, 404, 'nf', {}, None)
    monkeypatch.setattr(rdap.urllib.request, 'urlopen', fake_open)
    assert rdap.check('taken', ['com'])[0]['status'] == 'registered'
    assert rdap.check('free-name-xyz', ['com'])[0]['status'] == 'available'


def test_naming_stage_and_reviewer_checks_exist():
    for script in ['manage-brand-workspace.py', 'workspace_cli.py']:
        assert '"naming"' in (ROOT / '.agents/skills/brand-workspace-manager/scripts' / script).read_text()
    checklist = (ROOT / '.agents/skills/brand-quality-reviewer/references/review-checklist.md').read_text().lower()
    for needle in ['trademark', 'human vector', '16px', 'monochrome']:
        assert needle in checklist
