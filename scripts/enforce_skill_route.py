#!/usr/bin/env python3
"""Claude skill-dispatch adapter. Recompute policy; never trust a saved route packet.

Covers Skill and UserPromptExpansion, not arbitrary shell/file access.
"""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

try:
    from scripts.route_workflow import load_catalog, route_request
except ModuleNotFoundError:
    from route_workflow import load_catalog, route_request

ROOT = Path(__file__).resolve().parents[1]


def check_dispatch(event: dict) -> dict:
    expansion = event.get('hook_event_name') == 'UserPromptExpansion'
    tool_input = event.get('tool_input', {})
    if not expansion and event.get('tool_name') != 'Skill':
        return {}
    name = event.get('command_name', '') if expansion else tool_input.get('skill', '')
    # Foreign plugin skills belong to their own router; do not hijack them.
    if name not in load_catalog():
        if isinstance(name, str) and '/' not in name and (ROOT / '.agents/skills' / name / 'SKILL.md').is_file():
            raise ValueError('Installed repository skill is missing from the catalog')
        return {}
    if name == 'business-strategist':
        return {}
    args = event.get('command_args', '') if expansion else tool_input.get('args', '')
    envelope = json.loads(args)
    if not isinstance(envelope, dict) or not isinstance(envelope.get('route'), dict):
        raise ValueError('Repository skill dispatch requires a route envelope; see references/runtime-routing.md')
    route = envelope['route']
    for key in ('request', 'intent', 'task_scope'):
        if not isinstance(route.get(key), str) or not route[key].strip():
            raise ValueError(f'Route requires a nonempty {key}')
    if route['task_scope'] not in {'focused', 'execution', 'strategy'}:
        raise ValueError('Invalid task_scope')
    project = route.get('project', '')
    if not isinstance(project, str):
        raise ValueError('Project must be a slug')
    standalone = route.get('standalone', False)
    if type(standalone) is not bool or bool(project) == standalone:
        raise ValueError('Declare exactly one project slug or standalone=true')
    # Context may strengthen the caller's declaration, never silently weaken it.
    cwd = Path(event.get('cwd', str(ROOT))).resolve()
    try:
        parts = cwd.relative_to(ROOT / 'projects').parts
    except ValueError:
        parts = ()
    if parts and (ROOT / 'projects' / parts[0] / 'market_research/manifest.json').is_file():
        if standalone or project != parts[0]:
            raise ValueError('Route project conflicts with the current business workspace')
    if type(route.get('override_gate', False)) is not bool:
        raise ValueError('override_gate must be boolean')
    task = envelope.get('input', route['request'])
    if not isinstance(task, str):
        raise ValueError('Specialist input must be text')
    override_id = ''
    if route.get('override_gate'):
        if not isinstance(event.get('session_id'), str) or not event['session_id']:
            raise ValueError('Audited override requires a session ID')
        override_id = hashlib.sha256((event['session_id'] + ':' + str(event.get('tool_use_id', args))).encode()).hexdigest()
    packet = route_request(route['request'], intent=route['intent'], task_scope=route['task_scope'],
                           project=project, override_gate=route.get('override_gate', False), check_skill=name, override_id=override_id)
    if packet.get('gate_blocked'):
        raise ValueError(packet['reason'])
    context = 'Route checked against current policy: ' + json.dumps(packet, sort_keys=True)
    if expansion:
        return {'additionalContext': context}
    output = {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': context}}
    # Pass the actual task to the specialist, not our routing envelope.
    output['hookSpecificOutput']['updatedInput'] = {**tool_input, 'args': task}
    # No permissionDecision=allow: normal permission checks still run.
    return output


def main() -> int:
    event = {}
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('Hook input must be an object')
        result = check_dispatch(event)
    except Exception as exc:
        # Hook exceptions must not become a non-blocking host error.
        message = f'Skill route rejected: {type(exc).__name__}: {exc}'
        if isinstance(event, dict) and event.get('hook_event_name') == 'UserPromptExpansion':
            print(json.dumps({'decision': 'block', 'reason': message}))
        else:
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                              'permissionDecision': 'deny', 'permissionDecisionReason': message}}))
        return 0
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
