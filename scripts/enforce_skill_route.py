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
    try:
        envelope = json.loads(args) if isinstance(args, str) and args.strip() else None
    except json.JSONDecodeError:
        envelope = None
    if not isinstance(envelope, dict) or not isinstance(envelope.get('route'), dict):
        raise ValueError(envelope_hint(name, args if isinstance(args, str) else ''))
    route = envelope['route']
    for key in ('request', 'intent', 'task_scope'):
        if not isinstance(route.get(key), str) or not route[key].strip():
            raise ValueError(f'Route requires a nonempty {key}')
    if route['task_scope'] not in {'focused', 'execution', 'strategy'}:
        raise ValueError('Invalid task_scope')
    project = route.get('project', '')
    if not isinstance(project, str):
        raise ValueError('Project must be a slug')
    case_id = route.get('case', '')
    if not isinstance(case_id, str):
        raise ValueError('Case must be a registered identifier')
    standalone = route.get('standalone', False)
    if type(standalone) is not bool or not (project or standalone):
        raise ValueError('Declare a project slug or standalone=true')
    # Context may strengthen the caller's declaration, never silently weaken it.
    cwd = Path(event.get('cwd', str(ROOT))).resolve()
    try:
        parts = cwd.relative_to(ROOT / 'projects').parts
    except ValueError:
        parts = ()
    if parts and ((ROOT / 'projects' / parts[0] / 'market_research/manifest.json').is_file() or (ROOT / 'projects' / parts[0] / 'project-manifest.json').is_file()):
        if project and project != parts[0]:
            raise ValueError('Route project conflicts with the current business workspace')
        has_independent_marketing_brief = (name in {'marketing-strategy-builder', 'social-digital-marketing-planner'}
                                           and isinstance(route.get('standalone_brief'), str)
                                           and bool(route.get('standalone_brief').strip()))
        if standalone and not name.startswith('brand-') and not has_independent_marketing_brief:
            raise ValueError('Standalone bypass within a business workspace is limited to independent design work')
        project = parts[0]
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
    entry_mode = route.get('entry_mode')
    if entry_mode is None and 'standalone' in route:
        entry_mode = 'standalone' if route['standalone'] else 'business_linked'
    packet = route_request(route['request'], intent=route['intent'], task_scope=route['task_scope'],
                           project=project, case_id=case_id, entry_mode=entry_mode, standalone_brief=route.get('standalone_brief', ''), subproject=route.get('subproject', ''), override_gate=route.get('override_gate', False), override_stages=route.get('override_stages', []), check_skill=name, override_id=override_id)
    if packet.get('gate_blocked'):
        raise ValueError(packet['reason'])
    if isinstance(event.get('session_id'), str) and event['session_id'] and project:
        hooks_dir = Path(__file__).resolve().parents[1] / '.claude/hooks'
        sys.path.insert(0, str(hooks_dir))
        from compaction_state import active_workspace, load_state, resume_path, write_state
        module = packet.get('module') or 'business'
        case_context = packet.get('case_context') or {}
        selected_case = case_context.get('case_id') or case_id or None
        workspace = active_workspace(ROOT, str(cwd), selected_project=project,
                                     selected_module=module, selected_case=selected_case)
        checkpoint_path = resume_path(ROOT, event['session_id'])
        checkpoint = load_state(checkpoint_path, event['session_id']) or {'schema_version': 1, 'session_id': event['session_id']}
        checkpoint['active_selection'] = {'project': project, 'module': module,
            'case': selected_case, 'run': None, 'request': route['request'][:2000]}
        if workspace is not None:
            checkpoint['workspace'] = workspace
        checkpoint['compact_summary'] = ''
        write_state(checkpoint_path, checkpoint)
    context = 'Route checked against current policy: ' + json.dumps(packet, sort_keys=True)
    if expansion:
        return {'additionalContext': context}
    output = {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': context}}
    # Pass the actual task to the specialist, not our routing envelope.
    output['hookSpecificOutput']['updatedInput'] = {**tool_input, 'args': task}
    # No permissionDecision=allow: normal permission checks still run.
    return output


def envelope_hint(skill: str, raw_args: str) -> str:
    request = raw_args.strip().replace('"', "'")[:160] or '<one-sentence request>'
    template = ('{"route": {"request": "%s", "intent": "%s", "task_scope": "focused|execution|strategy", '
                '"project": "<slug>" | "standalone": true}, "input": "<specialist brief>"}') % (request, skill)
    return ('Repository skill dispatch requires a JSON route envelope in args. Re-invoke the skill with: '
            + template + ' . See references/runtime-routing.md. Plain text was received.')


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
