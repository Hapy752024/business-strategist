import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'
HIDDEN = [
    'brand-exporter',
    'brand-workspace-manager',
    'setup-multiharness-project',
    'marketing-campaign-operator',
    'pre-release-regression',
]


def _frontmatter(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    assert lines and lines[0] == '---', f'{path}: missing frontmatter'
    data = {}
    for line in lines[1:]:
        if line == '---':
            break
        if ':' in line and not line.startswith((' ', '\t')):
            key, _, value = line.partition(':')
            data[key.strip()] = value.strip()
    return data


def test_only_expected_skills_hidden():
    hidden = {
        md.parent.name for md in SKILLS.glob('*/SKILL.md')
        if _frontmatter(md).get('disable-model-invocation') == 'true'
    }
    assert hidden == set(HIDDEN)


def test_side_effect_skills_hidden_from_model():
    bad = [
        name for name in HIDDEN
        if _frontmatter(SKILLS / name / 'SKILL.md').get('disable-model-invocation') != 'true'
    ]
    assert bad == [], f'skills must set disable-model-invocation: true: {bad}'


def test_settings_listing_budget_fraction():
    settings = json.loads((ROOT / '.claude/settings.json').read_text(encoding='utf-8'))
    assert settings.get('skillListingBudgetFraction') == 0.03
