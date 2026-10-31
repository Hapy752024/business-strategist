"""Phase 4 skill-family merges: merged skills keep every former route ID and old names still resolve."""
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts import route_workflow

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'

# merged skill -> former skills it absorbed. Later family merges add one entry.
FAMILIES = {
    'brand-identity': [
        'brand-designer', 'brand-discovery-interviewer', 'brand-workspace-manager', 'brand-guideline-researcher',
        'brand-typography-researcher', 'brand-strategy-director', 'brand-guidelines-writer', 'brand-exporter',
        'brand-quality-reviewer',
    ],
    'brand-ui-system': [
        'brand-ui-kit-producer', 'brand-ui-component-producer', 'brand-motion-designer', 'brand-frontend-app-designer',
    ],
}
FORMER = [(merged, former) for merged, formers in FAMILIES.items() for former in formers]
# Paths stay in git history; docs/ and .superpowers/ are dated records of that history.
HISTORY_PREFIXES = ('docs/', '.superpowers/')


def _routes():
    return {route['id']: route for route in route_workflow.load_routes()}


def _words(path):
    return len(path.read_text(encoding='utf-8').split())


@pytest.mark.parametrize('merged', sorted(FAMILIES))
def test_merged_skill_has_one_skill_md_and_a_reference_per_mode(merged):
    skill_md = SKILLS / merged / 'SKILL.md'
    assert skill_md.is_file(), f'{merged} missing'
    assert _words(skill_md) <= 450
    modes = [route.get('mode') for route in _routes().values() if route['skill'] == merged]
    assert None not in modes and len(modes) == len(set(modes)), modes
    assert len(modes) >= len(FAMILIES[merged])
    for mode in modes:
        assert (SKILLS / merged / 'references' / f'{mode}.md').is_file(), f'{merged}: references/{mode}.md missing'


@pytest.mark.parametrize('merged,former', FORMER)
def test_former_skill_directory_is_gone_and_its_route_is_repointed(merged, former):
    assert not (SKILLS / former).exists()
    assert not (ROOT / '.claude/skills' / former).exists()
    route_id = route_workflow.SKILL_ALIASES[former]
    route = _routes()[route_id]
    assert route['skill'] == merged and route.get('mode'), route


@pytest.mark.parametrize('merged,former', FORMER)
def test_former_name_resolves_to_its_route_and_names_the_new_skill(merged, former):
    packet = route_workflow.route_request('explicit specialist task', intent=former, check_skill=merged)
    assert packet['route_id'] == route_workflow.SKILL_ALIASES[former]
    assert packet['skill'] == merged
    assert merged in packet['alias_note'] and former in packet['alias_note']


@pytest.mark.parametrize('merged,former', FORMER)
def test_dispatch_check_with_a_former_name_explains_the_merge(merged, former):
    with pytest.raises(ValueError, match=f'merged into {merged}'):
        route_workflow.route_request('explicit specialist task', intent=former, check_skill=former)


@pytest.mark.parametrize('merged', sorted(FAMILIES))
def test_bare_merged_skill_intent_lists_its_route_ids(merged):
    with pytest.raises(ValueError) as excinfo:
        route_workflow.route_request('explicit specialist task', intent=merged)
    for route_id in (route['id'] for route in _routes().values() if route['skill'] == merged):
        assert route_id in str(excinfo.value)


def test_catalog_lists_only_merged_skills():
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text(encoding='utf-8'))
    text = json.dumps(catalog)
    for merged, former in FORMER:
        assert former not in catalog['skills']
        assert f'"{former}"' not in text, former
    for merged in FAMILIES:
        assert len(catalog['skills'][merged]['required_references']) <= 3


def test_no_file_outside_history_mentions_former_skill_directories():
    names = '|'.join(re.escape(former) for _, former in FORMER)
    pattern = re.compile(rf'(?:skills/|\.\./)(?:{names})(?![\w-])')
    files = subprocess.run(['git', 'ls-files'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.split()
    offenders = []
    for rel in files:
        if rel.startswith(HISTORY_PREFIXES) or not (ROOT / rel).is_file():
            continue
        try:
            text = (ROOT / rel).read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        offenders += [f'{rel}: {m.group(0)}' for m in pattern.finditer(text)]
    assert offenders == [], '\n'.join(offenders)


BRAND_ROUTE_IDS = [
    'standalone-brand', 'brand-research', 'app-ui', 'brand-discovery-interviewer', 'brand-exporter',
    'brand-guidelines-writer', 'brand-motion-designer', 'brand-quality-reviewer', 'brand-strategy-director',
    'brand-typography-researcher', 'brand-ui-component-producer', 'brand-ui-kit-producer', 'brand-workspace-manager',
]


def test_brand_route_ids_unchanged():
    routes = _routes()
    assert len(BRAND_ROUTE_IDS) == 13
    for route_id in BRAND_ROUTE_IDS:
        assert route_id in routes, route_id
        assert routes[route_id]['skill'] in FAMILIES
