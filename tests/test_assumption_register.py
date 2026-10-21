"""Assumption register lifecycle in the case workspace."""
import json

import pytest

from scripts import case_workspace as c


def topic(tmp_path):
    p = tmp_path / 'topic'
    c.initialize(p, 'Topic')
    c.add_case(p, 'a', 'A')
    return p


def test_add_case_creates_empty_register(tmp_path):
    p = topic(tmp_path)
    reg = c.assumption_register(p, 'a')
    assert reg['entries'] == [] and reg['revision'] == 1 and reg['case_id'] == 'a'
    assert c.register_adopted(p, 'a')


def test_initial_insights_has_v3_sections(tmp_path):
    text = (topic(tmp_path) / 'cases/a/case_insights.md').read_text()
    assert '## What would change this recommendation' in text
    assert text.index('## What we could not check') < text.index('## Sources')


def test_legacy_case_without_register_not_adopted(tmp_path):
    p = topic(tmp_path)
    (p / 'cases/a/assumptions.json').unlink()
    assert not c.register_adopted(p, 'a')
    with pytest.raises(FileNotFoundError):
        c.assumption_register(p, 'a')
