import json
import subprocess
from pathlib import Path

import pytest

from scripts import enforce_skill_route as hook, route_workflow as router

ROOT = Path(__file__).resolve().parents[1]


def event(project='', standalone=True):
    return {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1', 'tool_use_id': 't1',
            'cwd': str(ROOT), 'tool_input': {'skill': 'brand-website-designer-builder', 'args': json.dumps({
                'route': {'request': 'build a landing page', 'intent': 'website-build', 'task_scope': 'execution',
                          'project': project, 'standalone': standalone}, 'input': 'The page brief'})}}


def test_valid_dispatch_keeps_normal_permissions():
    output = hook.check_dispatch(event())['hookSpecificOutput']
    assert output['updatedInput']['args'] == 'The page brief'
    assert 'permissionDecision' not in output


@pytest.mark.parametrize('field,value', [('intent', 'competitor-discovery'), ('task_scope', ''),
                                        ('standalone', 'true'), ('override_gate', 'false')])
def test_invalid_routes_block(field, value):
    payload = event()
    args = json.loads(payload['tool_input']['args'])
    args['route'][field] = value
    payload['tool_input']['args'] = json.dumps(args)
    with pytest.raises(ValueError):
        hook.check_dispatch(payload)


def test_gate_rechecked_on_each_call_and_override_is_replay_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    path = tmp_path / 'projects/venture/market_research/manifest.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'stages': {'problem_validation': {'status': 'passed', 'gate_result': 'pass'}}, 'events': []}))
    payload = event('venture', False)
    hook.check_dispatch(payload)
    path.write_text(json.dumps({'stages': {}, 'events': []}))
    with pytest.raises(ValueError, match='pain-first'):
        hook.check_dispatch(payload)
    args = json.loads(payload['tool_input']['args'])
    args['route']['override_gate'] = True
    payload['tool_input']['args'] = json.dumps(args)
    hook.check_dispatch(payload)
    before = path.read_bytes()
    hook.check_dispatch(payload)
    assert path.read_bytes() == before
    assert len(json.loads(before)['events']) == 1


def test_cwd_prevents_silent_standalone_bypass(tmp_path, monkeypatch):
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    path = tmp_path / 'projects/venture/market_research/manifest.json'
    path.parent.mkdir(parents=True)
    path.write_text('{}')
    payload = event()
    payload['cwd'] = str(path.parent)
    with pytest.raises(ValueError, match='conflicts'):
        hook.check_dispatch(payload)


def test_direct_slash_command_is_checked():
    payload = event()
    payload.update(hook_event_name='UserPromptExpansion', command_name=payload['tool_input']['skill'],
                   command_args=payload['tool_input']['args'])
    assert 'additionalContext' in hook.check_dispatch(payload)
    payload['command_args'] = '{}'
    with pytest.raises(ValueError):
        hook.check_dispatch(payload)


def test_hook_malformed_input_is_denied_not_a_nonblocking_error():
    for raw in ['{invalid', '[]', json.dumps({'tool_name': 'Skill', 'tool_input': {'skill': 'idea-grill', 'args': 'plain task'}})]:
        result = subprocess.run(['python3', str(ROOT / 'scripts/enforce_skill_route.py')], input=raw,
                                text=True, capture_output=True, check=True)
        assert json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'] == 'deny'


def test_unrelated_tools_and_foreign_skills_are_not_hijacked():
    assert hook.check_dispatch({'tool_name': 'Read'}) == {}
    assert hook.check_dispatch({'tool_name': 'Skill', 'tool_input': {'skill': 'foreign:tool'}}) == {}


def test_configured_hook_commands_block_invalid_dispatch_from_nested_cwd(tmp_path):
    import os
    settings = json.loads((ROOT / '.claude/settings.json').read_text())
    env = {**os.environ, 'CLAUDE_PROJECT_DIR': str(ROOT)}
    for name in ['PreToolUse', 'UserPromptExpansion']:
        group = next(g for g in settings['hooks'][name]
                     if any('enforce_skill_route.py' in h['command'] for h in g['hooks']))
        command = group['hooks'][0]['command']
        assert '|| exit 2' in command
        payload = {'hook_event_name': name, 'tool_name': 'Skill',
                   'tool_input': {'skill': 'idea-grill', 'args': '{}'},
                   'command_name': 'idea-grill', 'command_args': '{}'}
        result = subprocess.run(command, shell=True, cwd=tmp_path, env=env,
                                input=json.dumps(payload), text=True, capture_output=True, check=True)
        output = json.loads(result.stdout)
        if name == 'PreToolUse':
            assert output['hookSpecificOutput']['permissionDecision'] == 'deny'
        else:
            assert output['decision'] == 'block'
        # If the referenced adapter is missing, the shell wrapper still blocks.
        broken = subprocess.run(command, shell=True, cwd=tmp_path,
                                env={**env, 'CLAUDE_PROJECT_DIR': str(tmp_path)},
                                input='{}', text=True, capture_output=True)
        assert broken.returncode == 2
