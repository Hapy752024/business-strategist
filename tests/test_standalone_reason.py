import json
from pathlib import Path

import pytest

from scripts import enforce_skill_route as hook, route_workflow as router, subprojects


def dispatch(tmp_path, monkeypatch, *, request='build a landing page', intent='website-build',
             skill='brand-website-designer-builder', **route):
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    if not (tmp_path / 'projects/venture').exists():
        subprojects.initialize(tmp_path / 'projects/venture', 'Venture')
    payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1', 'tool_use_id': 't1',
               'cwd': str(tmp_path), 'tool_input': {'skill': skill, 'args': json.dumps({'route': {
                   'request': request, 'intent': intent, 'task_scope': 'execution', 'project': 'venture', **route},
                   'input': 'brief'})}}
    return hook.check_dispatch(payload)


def packet(result):
    context = result['hookSpecificOutput']['additionalContext']
    return json.loads(context.split(': ', 1)[1])


def test_agent_standalone_in_project_needs_the_users_words(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='standalone_reason'):
        dispatch(tmp_path, monkeypatch, standalone=True)
    with pytest.raises(ValueError, match='standalone_reason'):
        dispatch(tmp_path, monkeypatch, standalone=True, standalone_reason='   ')
    with pytest.raises(ValueError, match='must be text'):
        dispatch(tmp_path, monkeypatch, standalone=True, standalone_reason=['x'])
    result = packet(dispatch(tmp_path, monkeypatch, standalone=True,
                             standalone_reason='"build it independent of the business case"'))
    assert result['entry_mode'] == 'standalone' and result['default_entry_mode'] == 'business_linked'
    assert result['standalone_reason'] == '"build it independent of the business case"'
    assert result['standalone_source'] == 'agent_envelope'


def test_ungated_brand_research_needs_no_reason(tmp_path, monkeypatch):
    result = packet(dispatch(tmp_path, monkeypatch, request='research brand references', intent='brand-research',
                             skill='brand-identity', standalone=True))
    assert result['default_entry_mode'] == 'standalone' and 'standalone_source' not in result


def test_outside_a_project_standalone_needs_no_reason():
    result = router.route_request('build a landing page', intent='website-build', task_scope='execution',
                                  entry_mode='standalone')
    assert result['default_entry_mode'] == 'standalone' and 'standalone_reason' not in result


def test_router_cli_records_the_reason_without_requiring_it(tmp_path, monkeypatch):
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    subprojects.initialize(tmp_path / 'projects/venture', 'Venture')
    result = router.route_request('build a landing page', intent='website-build', task_scope='execution',
                                  project='venture', entry_mode='standalone', standalone_reason='founder asked')
    assert result['entry_mode'] == 'standalone' and result['standalone_reason'] == 'founder asked'
