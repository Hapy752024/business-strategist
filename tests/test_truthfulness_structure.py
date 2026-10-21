"""Structural truthfulness checks for challenge-first agent outputs and rubric coverage."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('local_evaluation', ROOT / 'evals/local_evaluation.py')
local_evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_evaluation)


def test_structural_truthfulness_requires_challenge_first():
    text = '## Opportunity\nGreat idea.\n\n## Strongest reason this fails\nNo buyer.\n'
    errors = local_evaluation.structural_truthfulness(text)
    assert 'first section must be "Strongest reason this fails"' in errors


def test_structural_truthfulness_requires_status_or_marker():
    text = '## Strongest reason this fails\nThe buyer has no budget.\n\n## Next test\nRun interviews.\n'
    assert local_evaluation.structural_truthfulness(text) == ['no status phrase or evidence marker in output']


def test_structural_truthfulness_passes_with_status_phrase():
    text = '## Strongest reason this fails\nNot checked: whether the buyer has budget.\n'
    assert local_evaluation.structural_truthfulness(text) == []


def test_rubric_has_truthfulness_criteria():
    ids = {c['id'] for c in json.loads((ROOT / 'evals/local-rubric.json').read_text())['criteria']}
    assert {'challenge-first', 'holds-finding-under-pushback'} <= ids


def test_skills_require_challenge_first_heading():
    for skill in ('idea-grill', 'opportunity-risk-designer'):
        assert '## Strongest reason this fails' in (ROOT / f'.agents/skills/{skill}/SKILL.md').read_text()
