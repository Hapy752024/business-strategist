import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'
REF = re.compile(r'(?<![\w./-])((?:\.\./|\./)*(?:[\w.-]+/)*references/(?:[\w.-]+/)*[\w.-]+\.md)')


EXCEPTIONS = json.loads((Path(__file__).parent / 'reference_depth_exceptions.json').read_text(encoding='utf-8'))


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


def test_exceptions_have_reasons():
    bad = [(k, e.get('target')) for k, v in EXCEPTIONS.items() for e in v if not str(e.get('reason', '')).strip()]
    assert bad == [], f'exceptions need a reason: {bad}'


def test_reference_depth_le_one():
    failures = {}
    for skill_md in sorted(SKILLS.glob('*/SKILL.md')):
        skill_dir = skill_md.parent
        depth1 = _links(skill_md, skill_dir)
        allowed = {e['target'] for e in EXCEPTIONS.get(skill_dir.name, [])}
        missing = set()
        for ref in depth1:
            missing |= _links(ref, skill_dir) - depth1 - {ref}
        names = {str(p.relative_to(ROOT)) for p in missing} - allowed
        if names:
            failures[skill_dir.name] = sorted(names)
    report = '\n'.join(f'{k}:\n  ' + '\n  '.join(v) for k, v in failures.items())
    assert not failures, f'{sum(map(len, failures.values()))} depth-2 references:\n{report}'


def test_exception_reasons_do_not_call_a_skills_own_reference_outside_its_stage():
    false = [(skill, e['target']) for skill, entries in EXCEPTIONS.items() for e in entries
             if e['target'].startswith(f'.agents/skills/{skill}/') and 'outside' in e.get('reason', '')]
    assert false == [], f'own-skill references described as outside the stage: {false}'
