import pytest
from scripts.route_workflow import route_request as route


@pytest.mark.parametrize('prompt,intent,skill,mode', [
    ('Plan backlink acquisition','earned-media-discovery','earned-media-builder','discovery'),
    ('Research SEO keywords and build a keyword-to-page map','seo-page-planning','marketing-strategy-builder','page_planning'),
    ('Run a technical SEO audit','seo-technical-audit','brand-website-designer-builder','technical_audit'),
    ('Prepare backlink pitches','earned-media-preparation','earned-media-builder','preparation'),
    ('Verify backlink placement','earned-media-verification','earned-media-builder','verification'),
])
def test_mode_ownership_and_bounded_artifacts(prompt,intent,skill,mode):
    for explicit in ['',intent]:
        result=route(prompt,intent=explicit,task_scope='focused')
        assert result['skill']==skill and result['mode']==mode
        assert result['expected_artifacts']
        assert 'Next.js site' not in result['expected_artifacts']


def test_negation_and_near_miss():
    assert route('write supplied copy', intent='marketing-strategy-builder', task_scope='execution')['route_id'] == 'marketing-strategy'
    assert route('Analyze competitor landing pages, do not plan backlink acquisition')['skill']=='competitor-marketing-analyzer'
    assert route('Create a logo only; do not run a technical SEO audit')['skill']=='brand-designer'
    assert route('What is SEO?')['ask_question']
    with pytest.raises(ValueError,match='Unknown route intent'):
        route('Prepare a packet',intent='earned-media-builder')


@pytest.mark.parametrize('intent', ['seo-page-planning', 'earned-media-discovery',
                                  'earned-media-preparation', 'earned-media-verification'])
def test_business_gate_and_explicit_standalone_brief(tmp_path, monkeypatch, intent):
    from scripts import route_workflow
    from test_workspace_gates import _write_manifest
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    _write_manifest(tmp_path, 'fixture-business', 'not_run', monkeypatch)
    assert route('Selected task', intent=intent, project='fixture-business')['gate_blocked']
    with pytest.raises(ValueError, match='standalone-brief'):
        route('Selected task', intent=intent, project='fixture-business', entry_mode='standalone')
    packet = route('Selected task', intent=intent, project='fixture-business', entry_mode='standalone',
                   standalone_brief='Established workshop; improve relevant public guide visibility')
    assert 'gate_blocked' not in packet
