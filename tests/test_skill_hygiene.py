import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'


def test_reference_files_have_no_frontmatter():
    offenders = [p for p in SKILLS.glob('*/references/*.md') if p.read_text().lstrip().startswith('---\nname:')]
    assert offenders == [], f'reference files must not carry skill frontmatter: {offenders}'


def test_no_copy_pasted_success_criteria_boilerplate():
    offenders = [p for p in SKILLS.rglob('*.md') if 'Triggers on >=90%' in p.read_text()]
    assert offenders == [], offenders


def test_no_nested_imported_workflow_headings():
    offenders = [p for p in SKILLS.glob('*/references/workflow.md') if '# Imported workflow' in p.read_text()]
    assert offenders == [], offenders


def test_skill_descriptions_are_compact():
    for skill in SKILLS.glob('*/SKILL.md'):
        text = skill.read_text()
        desc = re.search(r'^description:\s*(.+)$', text, re.M).group(1)
        assert len(desc) <= 240, f'{skill.parent.name}: description is {len(desc)} chars'


def test_no_skill_requires_approval_for_pre_authorized_customer_evidence_apis():
    offenders = [p for p in SKILLS.rglob('*.md')
                 if re.search(r'approval before paid providers|approve.{0,40}paid (evidence|customer)', p.read_text(), re.I)]
    assert offenders == [], offenders


def test_agents_md_stays_within_instruction_budget():
    text = (ROOT / 'AGENTS.md').read_text()
    assert len(text.splitlines()) <= 200
    assert 'references/operating-guide.md' in text


def test_paid_campaign_reference_exists_and_is_linked():
    skill = SKILLS / 'social-digital-marketing-planner'
    ref = skill / 'references/paid-campaign-planning.md'
    assert ref.exists()
    assert 'paid-campaign-planning.md' in (skill / 'SKILL.md').read_text()
    text = ref.read_text()
    for needle in ['Performance Max', 'learning', '50', 'consent', 'stop rule']:
        assert needle in text


def test_keyword_research_is_owned_by_marketing_and_consumed_by_website():
    ref = SKILLS / 'marketing-strategy-builder/references/keyword-research.md'
    assert ref.exists() and 'serper_fetch.py' in ref.read_text()
    assert 'keyword-research.md' in (SKILLS / 'marketing-strategy-builder/SKILL.md').read_text()
    assert 'keyword-map.json' in (SKILLS / 'brand-website-designer-builder/references/content-and-conversion.md').read_text()
