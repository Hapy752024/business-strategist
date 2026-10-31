"""GEO audit mode of the website skill: vendored provenance, thin wrapper behaviour and route reachability."""
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.route_workflow import route_request

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/brand-website-designer-builder'
VENDOR = SKILL / 'geo'
WRAPPER = VENDOR / 'geo_audit.py'
MODE = SKILL / 'references/geo-audit.md'
PIN = '7ecec864690ee430e954a95352130cf47e2c92cc'


def run(tmp_path, *args, env=None):
    base = {'PATH': str(tmp_path / 'empty-bin'), 'HOME': str(tmp_path)}
    result = subprocess.run([sys.executable, str(WRAPPER), *args], capture_output=True, text=True,
                            env={**base, **(env or {})}, timeout=60)
    return result.returncode, json.loads(result.stdout)


def test_mode_reference_budget_and_skill_pointer():
    text = MODE.read_text(encoding='utf-8')
    lines = text.splitlines()
    assert len(lines) <= 500
    assert statistics.median(len(line) for line in lines) <= 100
    assert 'references/geo-audit.md' in (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    assert '.agents/skills/brand-website-designer-builder/geo/geo_audit.py' in text


def test_vendored_license_and_pinned_commit():
    license_text = (VENDOR / 'LICENSE').read_text(encoding='utf-8')
    assert 'MIT License' in license_text and 'Juan Camilo Auriti' in license_text
    provenance = (VENDOR / 'VENDOR.md').read_text(encoding='utf-8')
    assert PIN in provenance and 'Auriti-Labs/geo-optimizer-skill' in provenance
    assert PIN in WRAPPER.read_text(encoding='utf-8')
    skill = MODE.read_text(encoding='utf-8')
    assert 'Auriti' in skill and 'MIT' in skill


def test_skill_treats_llms_txt_and_schema_as_hygiene():
    skill = MODE.read_text(encoding='utf-8').lower()
    assert 'hygiene' in skill and 'llms.txt' in skill
    assert 'ahrefs' in skill and 'google' in skill
    assert '--apply' not in skill.replace('never run `geo fix --apply`', '')


def test_missing_tool_reports_tool_unavailable(tmp_path):
    rc, out = run(tmp_path, '--url', 'https://example.com', '--out', str(tmp_path / 'audit.json'),
                  env={'GEO_AUDIT_BIN': str(tmp_path / 'absent-geo')})
    assert rc == 2 and out['status'] == 'tool_unavailable'
    assert out['pinned_commit'] == PIN
    assert not (tmp_path / 'audit.json').exists()


@pytest.mark.parametrize('url', ['http://127.0.0.1:3000/', 'http://localhost/', 'file:///tmp/site/index.html', 'ftp://example.com'])
def test_non_public_target_needs_public_url(tmp_path, url):
    rc, out = run(tmp_path, '--url', url, '--out', str(tmp_path / 'audit.json'))
    assert rc == 2 and out['status'] == 'needs_public_url'


def fake_geo(tmp_path, payload, code=0):
    tool = tmp_path / 'fake-geo'
    tool.write_text(f'#!{sys.executable}\nimport sys\n'
                    f'print({json.dumps(json.dumps(payload))})\nsys.exit({code})\n')
    tool.chmod(0o755)
    return tool


def test_audit_result_written_with_hygiene_annotations(tmp_path):
    payload = {'url': 'https://example.com', 'score': 40, 'band': 'foundation', 'score_version': 2,
               'score_breakdown': {'llms': 0, 'schema': 2, 'robots': 10}, 'recommendations': ['Add llms.txt']}
    tool = fake_geo(tmp_path, payload)
    out_path = tmp_path / 'audit.json'
    rc, out = run(tmp_path, '--url', 'https://example.com', '--out', str(out_path), env={'GEO_AUDIT_BIN': str(tool)})
    assert rc == 0 and out['status'] == 'ok'
    saved = json.loads(out_path.read_text())
    assert saved['raw'] == payload
    assert saved['tool']['pinned_commit'] == PIN
    assert set(saved['hygiene_categories']) >= {'llms', 'schema'}
    assert 'not a ranking' in saved['boundary'].lower()


def test_existing_output_never_replaced(tmp_path):
    out_path = tmp_path / 'audit.json'
    out_path.write_text('keep')
    tool = fake_geo(tmp_path, {'score': 1})
    rc, out = run(tmp_path, '--url', 'https://example.com', '--out', str(out_path), env={'GEO_AUDIT_BIN': str(tool)})
    assert rc == 1 and out['status'] == 'fail' and out_path.read_text() == 'keep'


def test_tool_failure_is_reported_not_scored(tmp_path):
    tool = fake_geo(tmp_path, {'error': 'boom'}, code=3)
    rc, out = run(tmp_path, '--url', 'https://example.com', '--out', str(tmp_path / 'a.json'), env={'GEO_AUDIT_BIN': str(tool)})
    assert rc == 1 and out['status'] == 'audit_failed'


@pytest.mark.parametrize('prompt', ['Run an AI citability audit on https://example.com',
                                    'Check AI search citability of our live site',
                                    'Run a GEO audit on https://www.example.com',
                                    'Do an AEO audit of our website',
                                    'Run an AI search visibility audit for our site'])
def test_geo_audit_route_reachable(prompt):
    assert route_request(prompt)['route_id'] == 'geo-audit'


def test_geo_audit_explicit_intent_and_contract():
    packet = route_request('audit https://example.com', intent='geo-audit')
    assert packet['skill'] == 'brand-website-designer-builder' and packet['route_id'] == 'geo-audit'
    assert packet['mode'] == 'geo-audit'
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text())['skills']['brand-website-designer-builder']
    assert [c['artifact'] for c in catalog['modes']['geo-audit']['consumes']] == ['website_build']


@pytest.mark.parametrize('prompt', ['Build my website for AEO/GEO', 'Fix my website for AEO/GEO', 'Improve LLM-EO on our landing page'])
def test_aeo_geo_content_work_stays_with_website_builder(prompt):
    assert route_request(prompt)['skill'] == 'brand-website-designer-builder'


def test_routing_evals_cover_geo_cases():
    pairs = json.loads((ROOT / 'config/routing-evals.json').read_text())['pairs']
    cases = {e['prompt']: (e['expected_skill'], e.get('expected_route'))
             for p in pairs if p['pair'].startswith('geo-audit') for e in p['evals']}
    assert cases['Run a GEO audit on https://www.example.com'] == ('brand-website-designer-builder', 'geo-audit')
    assert cases['Fix my website for AEO/GEO so answer engines can use our content.'][1] == 'website-build'
    assert cases['Is my site visible in ChatGPT?'][0] == 'competitor-monitoring'
    for prompt, (skill, route_id) in cases.items():
        packet = route_request(prompt)
        assert packet['skill'] == skill and packet['route_id'] == (route_id or packet['route_id']), prompt
