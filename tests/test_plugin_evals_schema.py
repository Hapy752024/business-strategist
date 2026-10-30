"""Structure checks for the `claude plugin eval` skill-trigger suite (no model calls)."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'evals/plugin-triggers'
SKILLS = ROOT / '.agents/skills'
NO_TRIGGER = {'no-skill-factual-question', 'no-skill-copy-rewrite', 'no-skill-git-question'}


def cases():
    return sorted(p.parent for p in SUITE.glob('*/prompt.md'))


def frontmatter(path: Path) -> dict:
    m = re.match(r'---\n(.*?)\n---\n?', path.read_text(), re.S)
    assert m, f'{path} has no frontmatter'
    return yaml.safe_load(m.group(1)) or {}


def test_manifest_exists_and_names_plugin():
    import json
    manifest = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
    assert manifest['name']


def test_suite_has_trigger_and_no_trigger_cases():
    names = {c.name for c in cases()}
    assert len(names) >= 15
    assert NO_TRIGGER <= names


def test_every_case_has_prompt_and_parsable_graders():
    for case in cases():
        body = re.sub(r'\A---\n.*?\n---\n?', '', (case / 'prompt.md').read_text(), flags=re.S).strip()
        assert body, case
        frontmatter(case / 'prompt.md')
        graders = sorted((case / 'graders').glob('*.md'))
        assert graders, f'{case.name} has no graders'
        for g in graders:
            assert frontmatter(g).get('type') in {'regex', 'tool_used', 'tool_order', 'file_exists', 'llm', 'baseline'}, g


def test_prompts_do_not_name_skills():
    skills = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    for case in cases():
        text = (case / 'prompt.md').read_text().lower()
        assert not [s for s in skills if s in text], case.name


def test_expected_skills_exist():
    for case in cases():
        for g in (case / 'graders').glob('*.md'):
            fm = frontmatter(g)
            if fm.get('type') != 'tool_used' or fm.get('tool') != 'Skill' or fm.get('max') == 0:
                continue
            m = re.search(r'\[\\w-\]\+:\)\?([a-z0-9-]+)"', fm['input_match'])
            assert m, f'{g}: cannot read expected skill'
            assert (SKILLS / m.group(1) / 'SKILL.md').is_file(), m.group(1)
        if case.name not in NO_TRIGGER:
            assert any(frontmatter(g).get('tool') == 'Skill' and frontmatter(g).get('max') != 0
                       for g in (case / 'graders').glob('*.md')), case.name
