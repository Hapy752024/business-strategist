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
