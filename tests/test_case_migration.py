import json
import pytest
from scripts import case_workspace as c, route_workflow as routing
from scripts.evidence_scout import workspace as w


@pytest.mark.parametrize('stop_at', ['pending', 'replace', 'commit'])
def test_migration_recovers_complete_state_without_inheriting_passes(tmp_path, stop_at):
    root = w.create_project_workspace('Legacy', str(tmp_path / 'legacy'), layout_version=1)
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def stop(point):
        if point == stop_at:
            raise RuntimeError('Injected interruption')
    with pytest.raises(RuntimeError):
        c.migrate(root, {'a': {'title': 'A'}}, 'migrate', 'Explicit rehearsal', fault=stop)
    with pytest.raises(ValueError, match='pending'):
        w.create_project_workspace('Legacy', str(root))
    assert c.recover(root) == ('completed' if stop_at == 'commit' else 'rolled_back')
    assert c.recover(root) == 'clean'
    if stop_at != 'commit':
        for name, body in before.items():
            assert (root / name).read_bytes() == body
        assert not (root / 'cases/a/README.md').exists()
        c.migrate(root, {'a': {'title': 'A'}}, 'migrate-again', 'Retry explicit rehearsal')
    assert c.read_project(root)['selection'] is None
    assert c.case_manifest(root, 'a')['stages'] == {}
    for name, body in before.items():
        if name.startswith('market_research/'):
            assert (root / name).read_bytes() == body


def test_legacy_continuation_and_rejected_new_execution_write_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(routing, 'ROOT', tmp_path)
    root = w.create_project_workspace('Legacy', str(tmp_path / 'projects/legacy'), layout_version=1)
    before = (root / w.RESEARCH_MANIFEST_REL).read_bytes()
    packet = routing.route_request('Build page', intent='website-build', project='legacy', entry_mode='business_linked', override_gate=True)
    assert packet['gate'] == 'migration_required'
    with pytest.raises(ValueError, match='migration'):
        w.resolve_run_dir(topic='Legacy', workspace_arg=str(root), case_id='a', out_dir='', legacy_output=False, workspace_subdir='market_research/pain_points/runs')
    assert (root / w.RESEARCH_MANIFEST_REL).read_bytes() == before
    w.update_stage(root, 'evidence_collection', status='in_progress', gate_result='not_run')
    assert w.read_manifest(root)['current_stage'] == 'evidence_collection'
