import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'
REF = re.compile(r'(?<![\w./-])((?:\.\./|\./)*(?:[\w.-]+/)*references/(?:[\w.-]+/)*[\w.-]+\.md)')


def _links(md, skill_dir):
    found = set()
    for match in REF.finditer(md.read_text(encoding='utf-8')):
        target = match.group(1)
        if target.split('/')[0] in {'evals', 'templates', 'schemas', 'config', 'scripts'}:
            continue
        for base in (md.parent, skill_dir, ROOT, SKILLS):
            path = (base / target).resolve()
            if path.is_file():
                found.add(path)
                break
    return found


def test_reference_depth_le_one():
    failures = {}
    for skill_md in sorted(SKILLS.glob('*/SKILL.md')):
        skill_dir = skill_md.parent
        depth1 = _links(skill_md, skill_dir)
        missing = set()
        for ref in depth1:
            missing |= _links(ref, skill_dir) - depth1 - {ref}
        if missing:
            failures[skill_dir.name] = sorted(str(p.relative_to(ROOT)) for p in missing)
    report = '\n'.join(f'{k}:\n  ' + '\n  '.join(v) for k, v in failures.items())
    assert not failures, f'{sum(map(len, failures.values()))} depth-2 references:\n{report}'
