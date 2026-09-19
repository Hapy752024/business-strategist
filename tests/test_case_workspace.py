import json
from pathlib import Path

import pytest

from scripts import case_workspace as c


def topic(tmp_path):
    p = tmp_path / 'topic'
    c.initialize(p, 'Topic')
    c.add_case(p, 'a', 'A')
    c.add_case(p, 'b', 'B')
    return p


def test_selection_generation_and_corrections(tmp_path):
    p = topic(tmp_path)
    c.select(p, 'a', 'one workflow', 'decision-a', 'user selected A')
    first = c.binding(p, 'a')
    c.correct(p, ['b'], 'B interpretation changed', 'correction-b')
    assert c.binding(p, 'a') == first
    c.correct(p, ['a'], 'A interpretation changed with identical source bytes', 'correction-a')
    with pytest.raises(ValueError, match='stale'):
        c.check_binding(p, first)
    c.select(p, 'b', 'other workflow', 'decision-b', 'user selected B')
    c.select(p, 'a', 'one workflow', 'decision-a-again', 'user selected A again')
    assert c.binding(p, 'a')['selection_generation'] == 3
    with pytest.raises(ValueError, match='stale'):
        c.check_binding(p, first)


@pytest.mark.parametrize('point', ['pending', 'replace', 'commit'])
def test_interrupted_publication_recovery(tmp_path, point):
    p = topic(tmp_path)
    before = (p / 'cases/a/README.md').read_bytes()
    rev = c.read_project(p)['manifest_revision']
    def stop(where):
        if where == point:
            raise RuntimeError('simulated crash')
    with pytest.raises(RuntimeError):
        c.publish(p, {'cases/a/README.md': '# Replacement\n'}, expected_revision=rev,
                  decision_id='update-a', reason='A changed', affected=['a'], fault=stop)
    with pytest.raises(ValueError, match='pending'):
        c.read_project(p)
    c.recover(p)
    assert not (p / 'history/pending.json').exists()
    assert (p / 'cases/a/README.md').read_bytes() == (b'# Replacement\n' if point == 'commit' else before)
    c.recover(p)  # idempotent


def test_conflict_and_escape_make_no_current_changes(tmp_path):
    p = topic(tmp_path)
    rev = c.read_project(p)['manifest_revision']
    c.correct(p, ['b'], 'changed', 'b-change')
    with pytest.raises(ValueError, match='conflict'):
        c.publish(p, {'cases/a/README.md': 'old'}, expected_revision=rev, decision_id='old', reason='old')
    with pytest.raises(ValueError):
        c.publish(p, {'../escape': 'bad'}, expected_revision=c.read_project(p)['manifest_revision'], decision_id='escape', reason='bad')
    assert not (tmp_path / 'escape').exists()


def test_recovery_preserves_outside_edits(tmp_path):
    p = topic(tmp_path)
    def stop(where):
        if where == 'replace':
            raise RuntimeError('crash')
    with pytest.raises(RuntimeError):
        c.publish(p, {'cases/a/README.md': 'new'}, expected_revision=c.read_project(p)['manifest_revision'],
                  decision_id='update', reason='update', fault=stop)
    (p / 'cases/a/README.md').write_text('outside change')
    with pytest.raises(ValueError, match='outside'):
        c.recover(p)
    assert (p / 'cases/a/README.md').read_text() == 'outside change'


def test_rename_and_clear_are_not_new_execution_choices(tmp_path):
    p=topic(tmp_path)
    c.select(p,'a','Chosen scope','choose-a','User selection')
    before=c.binding(p,'a')
    c.rename_case(p,'a','New display title','rename-a','Spelling and naming only')
    assert c.binding(p,'a') == before
    assert c.read_project(p)['cases']['a']['path'] == 'cases/a'
    c.select(p,'','','clear','User cleared selection')
    first=c.read_project(p)
    c.correct(p,['b'],'Unrelated follow-up','followup-b')
    c.select(p,'','','clear','Duplicate user decision')
    assert c.read_project(p)['selection_generation'] == first['selection_generation']
