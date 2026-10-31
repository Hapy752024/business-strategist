import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'
REF = re.compile(r'(?<![\w./-])((?:\.\./|\./)*(?:[\w.-]+/)*references/[\w.-]+\.md)')


def _skill_root(path):
    for parent in path.parents:
        if parent.parent == SKILLS:
            return parent
    return None


def test_markdown_reference_links_resolve():
    files = list(SKILLS.rglob('*.md')) + list((ROOT / 'references').glob('*.md'))
    failures = []
    for md in sorted(files):
        for match in REF.finditer(md.read_text(encoding='utf-8')):
            target = match.group(1)
            bases = [md.parent, ROOT, SKILLS]
            if _skill_root(md):
                bases.append(_skill_root(md))
            if not any((b / target).resolve().exists() for b in bases):
                failures.append(f'{md.relative_to(ROOT)}: {target}')
    assert failures == [], '\n'.join(failures)


BARE_REF = re.compile(r'(?<![\w./-])references/[\w.-]+\.md')
LINK_REF = re.compile(r'\]\((references/[\w.-]+\.md)')
REPO_ROOT_PREFIX = re.compile(r'repo-root\s+`?$')


def test_skill_reference_paths_are_unambiguous():
    failures = []
    for skill_md in sorted(SKILLS.glob('*/SKILL.md')):
        skill = skill_md.parent
        text = skill_md.read_text(encoding='utf-8')
        rel = skill_md.relative_to(ROOT)
        for m in LINK_REF.finditer(text):
            if not (skill / m.group(1)).exists():
                failures.append(f'{rel}: link {m.group(1)} missing in skill')
        for m in BARE_REF.finditer(text):
            target = m.group(0)
            if text[m.start() - 2:m.start()] == '](':
                continue
            prefixed = REPO_ROOT_PREFIX.search(text[max(0, m.start() - 20):m.start()])
            if prefixed:
                if not (ROOT / target).exists():
                    failures.append(f'{rel}: repo-root {target} missing at repo root')
            elif not (skill / target).exists():
                line = text.count('\n', 0, m.start()) + 1
                failures.append(f'{rel}:{line}: ambiguous {target}')
    assert failures == [], '\n'.join(failures)
