"""Executable reference delivery, scope preservation and missing-binding failures."""
import json

import pytest

from scripts import enforce_skill_route, route_workflow, validate_skill_routes


@pytest.mark.parametrize('skill', [
    'evidence-scout', 'competitive-landscape-builder', 'competitor-marketing-analyzer',
    'service-customer-perspective-challenger', 'opportunity-risk-designer', 'interview-bridge',
])
def test_customer_voice_reference_is_delivered_without_forcing_strategy(skill):
    packet = route_workflow.route_request('separate customer desired outcomes from solution-use requirements using known sources', intent="opportunity-prioritization" if skill == "opportunity-risk-designer" else skill,
                                         task_scope='focused', check_skill=skill)
    assert packet['required_references'] == ['references/customer-voice.md']
    assert packet['task_scope'] == 'focused'
    assert not packet.get('gate_blocked')
    assert not packet.get('required_stages')


def test_unrelated_execution_does_not_load_customer_voice():
    packet = route_workflow.route_request('write supplied copy', intent='marketing-strategy-builder',
                                         task_scope='execution')
    assert packet['required_references'] == []


@pytest.mark.parametrize('reference', ['missing.md', '../outside.md', '/tmp/outside.md', 'empty.md'])
def test_invalid_reference_blocks_dispatch(reference, tmp_path, monkeypatch):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'empty.md').touch()
    catalog = route_workflow.load_catalog()
    catalog['evidence-scout']['required_references'] = [reference]
    path = tmp_path / 'config/skill-catalog.json'
    path.write_text(json.dumps({'skills': catalog}))
    monkeypatch.setattr(route_workflow, 'CATALOG_PATH', path)
    with pytest.raises(ValueError, match='Required reference'):
        route_workflow.route_request('customer feedback', intent='evidence-scout',
                                     task_scope='focused', check_skill='evidence-scout')


def test_reference_is_present_in_host_context():
    event = {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'tool_input': {
        'skill': 'evidence-scout', 'args': json.dumps({
            'route': {'request': 'review customer feedback', 'intent': 'evidence-scout',
                      'task_scope': 'focused', 'standalone': True},
            'input': 'Review the supplied entities and sources',
        })}}
    output = enforce_skill_route.check_dispatch(event)['hookSpecificOutput']
    assert 'references/customer-voice.md' in output['additionalContext']
    assert output['updatedInput']['args'] == 'Review the supplied entities and sources'
    assert 'permissionDecision' not in output


def test_route_validator_rejects_missing_bound_reference(tmp_path):
    (tmp_path / 'config').mkdir()
    skill_dir = tmp_path / '.agents/skills/business-strategist'
    skill_dir.mkdir(parents=True)
    (skill_dir / 'SKILL.md').write_text('test skill')
    (tmp_path / 'config/skill-catalog.json').write_text(json.dumps({'skills': {
        'business-strategist': {'required_references': ['missing.md']}}}))
    (tmp_path / 'config/workflow-routes.json').write_text('{"routes": []}')
    assert any('Required reference' in error for error in validate_skill_routes.validate(tmp_path))


def test_reference_cannot_escape_through_symlink_or_parent(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    outside = tmp_path / 'outside.md'
    outside.write_text('Existing external instructions')
    (root / 'linked.md').symlink_to(outside)
    for reference in ['../outside.md', 'linked.md', str(outside)]:
        with pytest.raises(ValueError, match='outside repository'):
            route_workflow.checked_references({'required_references': [reference]}, root)


@pytest.mark.parametrize('references', ['references/customer-voice.md', [None], [''], {'path': 'x'}])
def test_malformed_reference_binding_is_rejected(references, tmp_path):
    with pytest.raises(ValueError, match='list of nonempty relative paths'):
        route_workflow.checked_references({'required_references': references}, tmp_path)
