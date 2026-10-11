import json
from pathlib import Path

import pytest

from scripts.marketing import execution, link_observations as links
from scripts import case_workspace, subprojects


def packet(raw=b'<a href="https://asset.example/guide" rel="nofollow">Guide</a>'):
    observation = links.observe(raw, source_url='https://publisher.example/resources',
        final_url='https://publisher.example/resources', target_url='https://asset.example/guide',
        capture_path='capture.html', ident='link-1')
    body = json.dumps(observation).encode()
    plan = {'schema_version': 2, 'scope': 'Verify a placement', 'revision': 1, 'actions': [{
        'id': 'placement', 'objective': 'Observe public anchor', 'actor': 'agent',
        'action_kind': 'verify_placement', 'intended_result': 'Public link to guide',
        'source_url': observation['source_url'], 'target_url': observation['target_url'],
        'dependencies': [], 'prepared_materials': [], 'next_step': 'Review outcome',
        'completion_criterion': 'Capture has matching anchor', 'commitment_state': 'completed',
        'execution_status': 'verified', 'required_for_scope': True,
        'observation': {'path': 'observation.json', 'sha256': links.sha(body)}}]}
    return plan, {'capture.html': raw, 'observation.json': body}


def test_positive_reply_cannot_complete_placement(tmp_path):
    plan, files = packet()
    plan['actions'][0].pop('observation')
    plan['actions'][0]['verification'] = 'Publisher said yes'
    assert not execution.scope_complete(plan, tmp_path, files)
    assert any('captured observation' in e for e in execution.validate(plan, tmp_path, files))


def test_same_transaction_completion_and_capture_tamper(tmp_path):
    plan, files = packet()
    assert execution.scope_complete(plan, tmp_path, files)
    assert not execution.scope_complete(plan)
    files['capture.html'] = b'changed'
    assert not execution.scope_complete(plan, tmp_path, files)


@pytest.mark.parametrize('change', ['wrong_target', 'wrong_anchor', 'no_anchor', 'malformed', 'escape'])
def test_bad_evidence_rejected(tmp_path, change):
    plan, files = packet()
    obs = json.loads(files['observation.json'])
    if change == 'wrong_target':
        plan['actions'][0]['target_url'] = 'https://asset.example/other'
    elif change == 'wrong_anchor':
        obs['anchors'][0]['rel'] = []
    elif change == 'no_anchor':
        files['capture.html'] = b'<p>Publisher said yes</p>'
        obs['capture']['sha256'] = links.sha(files['capture.html'])
    elif change == 'escape':
        obs['capture']['path'] = '../capture.html'
    files['observation.json'] = b'bad JSON' if change == 'malformed' else json.dumps(obs).encode()
    plan['actions'][0]['observation']['sha256'] = links.sha(files['observation.json'])
    assert not execution.scope_complete(plan, tmp_path, files)


def test_relative_base_and_symlink(tmp_path):
    raw = b'<base href="https://asset.example/"><a href="guide">Our guide</a>'
    plan, files = packet(raw)
    assert execution.scope_complete(plan, tmp_path, files)
    (tmp_path/'capture.html').symlink_to(tmp_path/'outside')
    assert not execution.scope_complete(plan, tmp_path, files)


def test_evidence_root_cannot_hide_symlink_ancestor(tmp_path):
    real = tmp_path/'real'; (real/'marketing').mkdir(parents=True)
    alias = tmp_path/'alias'; alias.symlink_to(real, target_is_directory=True)
    plan, files = packet()
    assert not execution.scope_complete(plan, alias/'marketing', files)


def test_publication_resume_and_revision_conflict(tmp_path):
    root = tmp_path/'project'
    subprojects.start(root, 'marketing', 'Demo', 'Verify a placement')
    plan, files = packet()
    files['execution-plan.json'] = json.dumps(plan)
    revision = case_workspace.read_project(root)['manifest_revision']
    subprojects.publish_marketing_workstream(root, files, expected_manifest_revision=revision,
        decision_id='placement-1', reason='Publish dated capture and verified observation.', status='complete')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    with pytest.raises(ValueError, match='revision conflict'):
        subprojects.publish_marketing_workstream(root, files, expected_manifest_revision=revision,
            decision_id='stale', reason='Attempt stale publication.', status='complete')
    (subprojects.path(root,'marketing')/'capture.html').write_bytes(b'changed')
    assert not subprojects.validate_marketing_workstream(root)['valid_for_use']


def test_draft_change_preserves_historical_link_but_source_change_invalidates():
    plan, _ = packet()
    old = plan['actions'][0]
    changed = {**old, 'prepared_materials': [{'path':'new.md','sha256':'a'*64}]}
    execution.invalidate_changed_action(old, changed)
    assert changed['execution_status'] == 'verified'
    changed['target_url'] = 'https://asset.example/other'
    execution.invalidate_changed_action(old, changed)
    assert changed['execution_status'] == 'prepared'
    assert 'observation' not in changed


def test_changed_recipient_revokes_authorization():
    old = {'action_kind':'send_pitch','recipient':'editor@example.test','prepared_materials':[],
           'commitment_state':'completed','execution_status':'verified','verification':'send receipt'}
    changed = {**old,'recipient':'other@example.test','authorization_digest':'a'*64}
    execution.invalidate_changed_action(old, changed)
    assert changed['execution_status'] == 'prepared'
    assert 'authorization_digest' not in changed
