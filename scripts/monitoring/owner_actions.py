"""Lossless accepted-owner-action rows inside the existing next_action string.

This module does not write manifests or accept actions on an owner's behalf.
Callers stage its returned manifest through the active track's publication flow.
"""
import copy
import json
import re

PREFIX = 'Owner action: '
STATES = ('proposed', 'accepted', 'deferred', 'completed')
FIELDS = ('id', 'action', 'reason_owner', 'cadence', 'effort', 'review_at',
          'completion', 'outcome', 'stop_rule', 'details')


def accepted_actions(manifest):
    rows = []
    for line in manifest.get('next_action', '').splitlines():
        if line.startswith(PREFIX):
            row = json.loads(line[len(PREFIX):])
            if row.get('state') != 'accepted':
                raise ValueError('active owner-action row must be accepted')
            rows.append(row)
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('duplicate active owner-action ID')
    return rows


def update_action(manifest, action):
    """Merge a user-decided state; preserve unrelated text, tasks and blockers."""
    if action.get('state') not in STATES:
        raise ValueError('unsupported owner-action state')
    for field in FIELDS:
        if not isinstance(action.get(field), str) or not action[field].strip():
            raise ValueError(f'owner action {field}: nonempty string required')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', action['id']):
        raise ValueError('owner action ID: letters, digits, underscore and hyphen only')
    existing = accepted_actions(manifest)
    if action['state'] == 'proposed' and any(r['id'] == action['id'] for r in existing):
        raise ValueError('a proposal cannot silently replace an accepted commitment')
    result = copy.deepcopy(manifest)
    lines = []
    for line in result.get('next_action', '').splitlines():
        if line.startswith(PREFIX) and json.loads(line[len(PREFIX):])['id'] == action['id']:
            continue
        lines.append(line)
    if action['state'] == 'accepted':
        lines.append(PREFIX + json.dumps({k: action[k] for k in FIELDS + ('state',)}, ensure_ascii=False, sort_keys=True))
    result['next_action'] = '\n'.join(lines)
    return result
