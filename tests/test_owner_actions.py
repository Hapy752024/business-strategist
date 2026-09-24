import copy
import pytest
from scripts.monitoring.owner_actions import accepted_actions, update_action

ROW = {'id': 'terms', 'action': 'Confirm cancellation terms', 'reason_owner': 'commercial decision',
       'cadence': 'one-off', 'effort': '10 minutes', 'review_at': 'before publication',
       'completion': 'exact terms confirmed', 'outcome': 'accurate purchase expectations',
       'stop_rule': 'close after confirmation', 'details': 'owner-actions.md#terms', 'state': 'accepted'}


def test_resume_keeps_only_accepted_and_preserves_unrelated_state():
    start = {'next_action': 'Review the local website diff.', 'open_blockers': ['Existing identity blocker']}
    original = copy.deepcopy(start)
    updated = update_action(start, ROW)
    updated = update_action(updated, {**ROW, 'id': 'weekly', 'action': 'Write weekly', 'state': 'proposed'})
    updated = update_action(updated, {**ROW, 'id': 'later', 'state': 'deferred'})
    assert accepted_actions(updated) == [ROW]
    assert updated['next_action'].startswith(start['next_action'])
    assert updated['open_blockers'] == start['open_blockers'] and start == original
    assert update_action(updated, ROW) == updated
    completed = update_action(updated, {**ROW, 'state': 'completed'})
    assert completed == start


def test_defer_one_task_preserves_other_accepted_tasks():
    m = {'next_action': 'Agent task', 'open_blockers': []}
    m = update_action(update_action(m, ROW), {**ROW, 'id': 'identity'})
    m = update_action(m, {**ROW, 'state': 'deferred'})
    assert [r['id'] for r in accepted_actions(m)] == ['identity']
    assert m['open_blockers'] == []


def test_reproposal_does_not_cancel_acceptance():
    with pytest.raises(ValueError, match='proposal'):
        update_action(update_action({'next_action': ''}, ROW), {**ROW, 'state': 'proposed'})
