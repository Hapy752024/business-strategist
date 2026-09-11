import json
import shutil
from pathlib import Path

import pytest

from scripts import route_workflow, validate_skill_routes

ROOT = Path(__file__).resolve().parents[1]


def test_every_installed_skill_is_catalogued_and_reachable():
    assert validate_skill_routes.validate() == []
    for route in route_workflow.load_routes():
        packet = route_workflow.route_request('explicit specialist task', intent=route['id'], check_skill=route['skill'])
        assert packet['skill'] == route['skill']


@pytest.mark.parametrize('defect', ['orphan', 'missing-catalog', 'stale-catalog', 'duplicate', 'unknown-target', 'self-forbidden'])
def test_coverage_fails_closed(tmp_path, defect):
    (tmp_path / 'config').mkdir()
    for name in ['workflow-routes.json', 'skill-catalog.json']:
        shutil.copyfile(ROOT / 'config' / name, tmp_path / 'config' / name)
    for path in (ROOT / '.agents/skills').glob('*/SKILL.md'):
        target = tmp_path / '.agents/skills' / path.parent.name / 'SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_text('fixture')
    routes_path = tmp_path / 'config/workflow-routes.json'
    routes = json.loads(routes_path.read_text())
    if defect in {'orphan', 'missing-catalog'}:
        target = tmp_path / '.agents/skills/new-skill/SKILL.md'
        target.parent.mkdir()
        target.write_text('fixture')
        if defect == 'orphan':
            path = tmp_path / 'config/skill-catalog.json'
            data = json.loads(path.read_text())
            data['skills']['new-skill'] = {}
            path.write_text(json.dumps(data))
    elif defect == 'stale-catalog':
        (tmp_path / '.agents/skills/idea-grill/SKILL.md').unlink()
    elif defect == 'duplicate':
        routes['routes'].append(routes['routes'][0])
    elif defect == 'unknown-target':
        routes['routes'][0]['skill'] = 'missing'
    else:
        routes['routes'][0]['forbidden'].append(routes['routes'][0]['skill'])
    routes_path.write_text(json.dumps(routes))
    assert validate_skill_routes.validate(tmp_path)


def test_dispatch_rejects_mismatch_and_ambiguity():
    with pytest.raises(ValueError, match='Dispatch rejected'):
        route_workflow.route_request('find competitors', check_skill='brand-designer')
    with pytest.raises(ValueError, match='Dispatch rejected'):
        route_workflow.route_request('unclassified', check_skill='business-strategist')


@pytest.mark.parametrize('intent', ['standalone-brand', 'social-marketing', 'saas-fintech-pilot-designer'])
def test_commitment_routes_do_not_bypass_pain_gate(tmp_path, monkeypatch, intent):
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    route = next(r for r in route_workflow.load_routes() if r['id'] == intent)
    packet = route_workflow.route_request('venture task', intent=intent, project='missing', check_skill=route['skill'])
    assert packet['gate_blocked']


def test_precise_typography_and_town_requests():
    assert route_workflow.route_request('font research')['skill'] == 'brand-typography-researcher'
    assert route_workflow.route_request('refresh town data')['skill'] == 'town-db-curator'
