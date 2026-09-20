import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from scripts.brand import website_launch as launch
from scripts.brand import release_manifest as release
from scripts.brand.init_website import initialize
from scripts.brand.check_lighthouse import errors as lighthouse_errors
from scripts.route_workflow import route_request

ROOT = Path(__file__).resolve().parents[1]
SHA = 'a' * 40
URL = 'https://example.test'


def ready():
    d = launch.pending()
    d.update(commit=SHA, url=URL, deployment_id='deployment-42/config-3')
    for row in d['checks'].values():
        row.update(status='pass', evidence='qa/review.md: inspected fixture, all routes, reviewer 2026-09-14')
    return d


def manifest(tmp_path):
    initialize(tmp_path, SimpleNamespace(website_id='test', entry_mode='standalone', next_version='16.3.3', preferences='website-preferences.json'))
    p = tmp_path / 'website-manifest.json'
    d = json.loads(p.read_text())
    d['qa'] = {k: 'pass' for k in d['qa']}
    d['launch'] = ready()
    p.write_text(json.dumps(d))
    return p


def promote(path, **overrides):
    args = dict(status='production', commit=SHA, url=URL, deployment_id='deployment-42/config-3', confirm_production=True, github_repo='owner/site', github_branch='main', vercel_project='site')
    args.update(overrides)
    return release.update(path, **args)


def test_pending_complete_schema_and_no_pass():
    data = launch.pending()
    assert len(data['checks']) == 26
    assert all(r['status'] == 'pending' for r in data['checks'].values())
    assert launch.errors(data, commit=SHA, url=URL, deployment_id='config')
    schema = json.loads((ROOT / 'schemas/website-manifest.schema.json').read_text())
    Draft202012Validator(schema['properties']['launch']).validate(data)
    assert not launch.errors(ready(), commit=SHA, url=URL, deployment_id='deployment-42/config-3')


@pytest.mark.parametrize('key', launch.CHECKS)
def test_every_requirement_blocks_without_write(tmp_path, key):
    p = manifest(tmp_path)
    d = json.loads(p.read_text()); del d['launch']['checks'][key]; p.write_text(json.dumps(d))
    before = p.read_bytes()
    with pytest.raises(ValueError, match='launch'):
        promote(p)
    assert p.read_bytes() == before


@pytest.mark.parametrize('bad', [None, [], {}, {'version': True}, {'version': 1, 'checks': []}])
def test_malformed_assessment_rejected(bad):
    assert launch.errors(bad, commit=SHA, url=URL, deployment_id='config')


@pytest.mark.parametrize('change', [{'url': 'https://preview.example.test'}, {'commit': 'b'*40}, {'commit': SHA[:7]}, {'deployment_id': 'new-config'}, {'deployment_id': ''}])
def test_binding_mismatch_no_write(tmp_path, change):
    p = manifest(tmp_path); before = p.read_bytes()
    with pytest.raises(ValueError, match='launch'):
        promote(p, **change)
    assert p.read_bytes() == before


@pytest.mark.parametrize('row', [{'status': 'fail', 'evidence': 'failure'}, {'status': 'pass', 'evidence': ' '}, {'status': 'pass', 'evidence': []}, 'pass'])
def test_false_or_empty_evidence(row):
    d = ready(); d['checks']['cookie_consent'] = row
    assert launch.errors(d, commit=SHA, url=URL, deployment_id=d['deployment_id'])


def test_legacy_preview_rollback_and_production_block(tmp_path):
    p = manifest(tmp_path); d = json.loads(p.read_text()); del d['launch']; p.write_text(json.dumps(d))
    release.update(p, status='preview', commit=SHA[:7], url='https://preview.example.test')
    before = p.read_bytes()
    with pytest.raises(ValueError, match='launch'):
        promote(p)
    assert p.read_bytes() == before
    release.update(p, status='rolled_back', commit=SHA[:7], rollback_commit='b'*7)


def test_production_record(tmp_path):
    p = manifest(tmp_path)
    assert promote(p)['deployment_id'] == 'deployment-42/config-3'
    d = json.loads(p.read_text())
    Draft202012Validator(json.loads((ROOT / 'schemas/website-manifest.schema.json').read_text())).validate(d)


@pytest.mark.parametrize('prompt', ['Fix website SEO', 'Improve website performance', 'Plan website maintenance', 'Run a GEO audit', 'Create a Next.js website', 'Implement campaign tracking', 'Integrate GA4', 'Set up PostHog analytics'])
def test_website_routes(prompt):
    assert route_request(prompt)['skill'] == 'brand-website-designer-builder'


@pytest.mark.parametrize('prompt,expected', [('Analyze competitor website','competitor-marketing-analyzer'), ('Create favicon set','brand-asset-producer'), ('Build dashboard UI','brand-frontend-app-designer')])
def test_scope_boundaries(prompt, expected):
    assert route_request(prompt)['skill'] == expected


@pytest.mark.parametrize('prompt,expected', [
    ('Run an AEO audit', 'brand-website-designer-builder'),
    ('Structured data audit', 'brand-website-designer-builder'),
    ('Track brand mentions', 'competitor-monitoring'),
    ('Set up AI citation tracking', 'competitor-monitoring'),
])
def test_visibility_routes(prompt, expected):
    assert route_request(prompt)['skill'] == expected


def test_lighthouse_budget():
    r = {'audits': {k: {'numericValue': v} for k,v in [('largest-contentful-paint',2400),('cumulative-layout-shift',.05),('total-blocking-time',100)]}, 'categories': {'performance': {'score': .95}, 'seo': {'score': 1}}}
    assert lighthouse_errors(r) == []
    for value in [None, True, float('nan'), 3000]:
        bad = copy.deepcopy(r); bad['audits']['largest-contentful-paint']['numericValue'] = value
        assert lighthouse_errors(bad)
    assert lighthouse_errors({})


def test_optional_analytics_requires_explicit_disposition():
    d = ready(); d['checks']['analytics'] = {'status': 'not_requested', 'evidence': 'Owner chose no analytics; browser network trace verifies no collection.'}
    assert not launch.errors(d, commit=SHA, url=URL, deployment_id=d['deployment_id'])
    d['checks']['cookie_consent']['status'] = 'not_requested'
    assert launch.errors(d, commit=SHA, url=URL, deployment_id=d['deployment_id'])
    d = ready(); d['checks']['analytics'] = {'status': 'not_requested', 'evidence': ''}
    assert launch.errors(d, commit=SHA, url=URL, deployment_id=d['deployment_id'])
