import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/evidence_scout'))
collect = importlib.import_module('collect')
common = importlib.import_module('common')


def test_partial_run_preserves_evidence_and_lists_remaining_providers(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['collect.py', '--topic', 'task scheduling', '--customer-segment', 'operators',
                                     '--providers', 'hn,github', '--max-http-requests', '1'])
    monkeypatch.setattr(collect, 'resolve_run_dir', lambda **kwargs: (tmp_path, None))
    monkeypatch.setattr(collect, 'load_provider_routing', lambda: {})
    def provider(*args):
        common.http_get('https://example.test/first')
        common.http_get('https://example.test/blocked')
        record = collect.normalize_record(source='reddit', source_url='https://www.reddit.com/r/test/comments/1',
                query='task scheduling', customer_segment='operators', hypothesis='H1',
                text='I waste hours manually coordinating schedules in spreadsheets.', strength='weak')
        return [record], {'status': 'ok'}
    monkeypatch.setattr(collect, 'collect_hn', provider)
    monkeypatch.setattr(collect, 'collect_github', lambda *a: pytest.fail('Provider started after exhaustion'))
    with patch.object(common.urllib.request, 'urlopen', side_effect=OSError('synthetic failure')) as network:
        assert collect.main() == 2
        assert network.call_count == 1
    summary = json.loads((tmp_path / 'summary.json').read_text())
    assert summary['record_count'] == 1
    assert not summary['collection_complete']
    assert summary['request_budget']['requests'] == 1
    assert {t['provider'] for t in summary['remaining_tasks']} >= {'hn', 'github'}
    assert len((tmp_path / 'evidence.jsonl').read_text().splitlines()) == 1
    assert 'Remaining Tasks' in (tmp_path / 'report.md').read_text()
    manifest = json.loads((tmp_path / 'run-manifest.json').read_text())
    assert manifest['gate_result'] == 'fail'
    assert manifest['stage_status'] == 'blocked'


def test_budget_validation_precedes_any_workspace_write(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['collect.py', '--topic', 'test', '--max-http-requests', '0'])
    monkeypatch.setattr(collect, 'resolve_run_dir', lambda **kw: pytest.fail('Unexpected workspace write'))
    with pytest.raises(SystemExit) as exc:
        collect.main()
    assert exc.value.code == 2


def test_credit_and_unknown_statuses_remain_explicit():
    tasks = collect.remaining_tasks({'social': {'status': 'insufficient_credits'}, 'unknown': {}}, [])
    assert 'do not retry automatically' in tasks[0]['action']
    assert tasks[1]['status'] == 'unknown'
