import json
import subprocess
from pathlib import Path

import pytest

from scripts import enforce_skill_route as hook, route_workflow as router, case_workspace as cases, validate_skill_routes
from scripts.evidence_scout import workspace as research_workspace
from problem_assessment_fixtures import prepare as prepare_problem_assessment

ROOT = Path(__file__).resolve().parents[1]


def event(project='', standalone=True):
    return {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1', 'tool_use_id': 't1',
            'cwd': str(ROOT), 'tool_input': {'skill': 'brand-website-designer-builder', 'args': json.dumps({
                'route': {'request': 'build a landing page', 'intent': 'website-build', 'task_scope': 'execution',
                          'project': project, 'standalone': standalone}, 'input': 'The page brief'})}}


def test_valid_dispatch_keeps_normal_permissions():
    output = hook.check_dispatch(event())['hookSpecificOutput']
    assert output['updatedInput']['args'] == 'The page brief'
    assert 'permissionDecision' not in output


def test_dispatch_persists_selected_workspace_for_repo_root_compaction(tmp_path, monkeypatch):
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    project = tmp_path / 'projects' / 'selected'
    from scripts import subprojects
    subprojects.initialize(project, 'Selected project')
    payload = event('selected')
    result = hook.check_dispatch(payload)
    assert result['hookSpecificOutput']['updatedInput']['args'] == 'The page brief'
    state = json.loads((tmp_path / '.claude/plans/resume/s1.json').read_text())
    assert state['active_selection']['project'] == 'selected'
    assert state['active_selection']['module'] == 'website'
    assert state['active_selection']['request'] == 'build a landing page'


@pytest.mark.parametrize('field,value', [('intent', 'competitor-discovery'), ('task_scope', ''),
                                        ('standalone', 'true'), ('override_gate', 'false')])
def test_invalid_routes_block(field, value):
    payload = event()
    args = json.loads(payload['tool_input']['args'])
    args['route'][field] = value
    payload['tool_input']['args'] = json.dumps(args)
    with pytest.raises(ValueError):
        hook.check_dispatch(payload)


def test_gate_rechecked_on_each_call_and_override_is_replay_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    root = tmp_path / 'projects/venture'
    cases.initialize(root, 'Venture')
    scope = cases.add_case(root, 'a', 'A')
    cases.select(root, 'a', 'Test', 'select-fixture', 'Explicit fixture selection')
    path = scope / 'market_research/manifest.json'
    data = cases.case_manifest(root, 'a')
    evidence, _, _ = prepare_problem_assessment(scope, research_workspace, monkeypatch, case_id='a')
    research_workspace.update_stage(scope, 'problem_validation', expected_assessment_revision=1,
        status='passed', gate_result='pass', artifacts=evidence)
    payload = event('venture', False)
    packet = json.loads(payload['tool_input']['args'])
    packet['route'].update(request='Create a social media plan', intent='social-marketing')
    payload['tool_input'].update(skill='marketing', args=json.dumps(packet))
    hook.check_dispatch(payload)
    data['stages'] = {}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='pain-first'):
        hook.check_dispatch(payload)
    args = json.loads(payload['tool_input']['args'])
    args['route']['override_gate'] = True
    args['route']['override_stages'] = ['problem_validation']
    args['route']['override_reason'] = 'Founder: "skip validation, I accept the risk"'
    payload['tool_input']['args'] = json.dumps(args)
    hook.check_dispatch(payload)
    before = path.read_bytes()
    hook.check_dispatch(payload)
    assert path.read_bytes() == before
    events = json.loads(before)['events']
    assert len(events) == 1
    assert events[0]['source'] == 'agent_envelope'
    assert events[0]['override_reason'] == 'Founder: "skip validation, I accept the risk"'


@pytest.mark.parametrize('reason', [None, '', '   ', 7])
def test_envelope_override_requires_nonempty_reason(tmp_path, monkeypatch, reason):
    """I2: an agent-authored override_gate needs the user's words; otherwise it is refused, nothing is recorded."""
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    root = tmp_path / 'projects/venture'
    cases.initialize(root, 'Venture')
    scope = cases.add_case(root, 'a', 'A')
    cases.select(root, 'a', 'Test', 'select-fixture', 'Explicit fixture selection')
    path = scope / 'market_research/manifest.json'
    payload = event('venture', False)
    packet = json.loads(payload['tool_input']['args'])
    packet['route'].update(request='Create a social media plan', intent='social-marketing', override_gate=True,
                           override_stages=['problem_validation'])
    if reason is not None:
        packet['route']['override_reason'] = reason
    payload['tool_input'].update(skill='marketing', args=json.dumps(packet))
    before = path.read_bytes()
    with pytest.raises(ValueError, match='override_reason'):
        hook.check_dispatch(payload)
    assert path.read_bytes() == before


def test_cwd_prevents_silent_standalone_bypass(tmp_path, monkeypatch):
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    path = tmp_path / 'projects/venture/market_research/manifest.json'
    path.parent.mkdir(parents=True)
    path.write_text('{}')
    payload = event()
    payload['cwd'] = str(path.parent)
    assert hook.check_dispatch(payload)['hookSpecificOutput']['updatedInput']['args'] == 'The page brief'
    payload['tool_input']['skill'] = 'marketing'
    with pytest.raises(ValueError, match='Standalone bypass'):
        hook.check_dispatch(payload)


def test_direct_slash_command_is_checked():
    payload = event()
    payload.update(hook_event_name='UserPromptExpansion', command_name=payload['tool_input']['skill'],
                   command_args=payload['tool_input']['args'])
    assert 'additionalContext' in hook.check_dispatch(payload)
    payload['command_args'] = '{}'
    with pytest.raises(ValueError):
        hook.check_dispatch(payload)


def test_checked_route_packet_requires_selected_module_guidance():
    research = router.route_request('Understand the customer problem', intent='market-problem-discovery', task_scope='strategy')
    assert research['module'] == 'research'
    assert research['module_reference'] == 'references/modules/research.md'
    assert research['quality_reference'] == 'references/modules/quality/research.md'
    assert research['module_reference'] not in research['required_references']
    marketing = router.route_request('Build a social marketing plan', intent='social-marketing', task_scope='strategy')
    assert marketing['module'] == 'marketing'
    assert marketing['module_reference'] == 'references/modules/marketing.md'
    assert marketing['quality_reference'] == 'references/modules/quality/marketing.md'
    assert marketing['module_reference'] not in marketing['required_references']
    venture = router.route_request('Plan the business', intent='startup-business-builder')
    assert venture['specialist_owner'] == 'venture_strategy'
    assert 'module' not in venture


def test_every_skill_has_one_checked_module_or_specialist_owner():
    assert validate_skill_routes.validate(ROOT) == []


def test_hook_malformed_input_is_denied_not_a_nonblocking_error():
    for raw in ['{invalid', '[]', json.dumps({'tool_name': 'Skill', 'tool_input': {'skill': 'opportunity-risk-designer', 'args': 'plain task'}})]:
        result = subprocess.run(['python3', str(ROOT / 'scripts/enforce_skill_route.py')], input=raw,
                                text=True, capture_output=True, check=True)
        assert json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'] == 'deny'


def test_unrelated_tools_and_foreign_skills_are_not_hijacked():
    assert hook.check_dispatch({'tool_name': 'Read'}) == {}
    assert hook.check_dispatch({'tool_name': 'Skill', 'tool_input': {'skill': 'foreign:tool'}}) == {}


def test_plain_text_args_get_an_actionable_envelope_hint():
    hook_path = ROOT / 'scripts/enforce_skill_route.py'
    event = {"hook_event_name": "PreToolUse", "tool_name": "Skill",
             "tool_input": {"skill": "opportunity-risk-designer", "args": "rank my dog grooming risks"}}
    out = subprocess.run(["python3", str(hook_path)], input=json.dumps(event), text=True, capture_output=True, check=True)
    decision = json.loads(out.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    reason = decision["permissionDecisionReason"]
    assert "JSON route envelope" in reason
    assert '"intent": "opportunity-risk-designer"' in reason
    assert "references/runtime-routing.md" in reason
    assert "JSONDecodeError" not in reason


def test_configured_hook_commands_block_invalid_dispatch_from_nested_cwd(tmp_path):
    import os
    settings = json.loads((ROOT / '.claude/settings.json').read_text())
    env = {**os.environ, 'CLAUDE_PROJECT_DIR': str(ROOT)}
    for name in ['PreToolUse', 'UserPromptExpansion']:
        group = next(g for g in settings['hooks'][name]
                     if any('enforce_skill_route.py' in h['command'] for h in g['hooks']))
        command = group['hooks'][0]['command']
        payload = {'hook_event_name': name, 'tool_name': 'Skill',
                   'tool_input': {'skill': 'idea-grill', 'args': '{}'},
                   'command_name': 'idea-grill', 'command_args': '{}'}
        result = subprocess.run(command, shell=True, cwd=tmp_path, env=env,
                                input=json.dumps(payload), text=True, capture_output=True, check=True)
        output = json.loads(result.stdout)
        if name == 'PreToolUse':
            assert output['hookSpecificOutput']['permissionDecision'] == 'deny'
        else:
            assert output['decision'] == 'block'
        # If the referenced adapter is missing, the shell wrapper still blocks.
        broken = subprocess.run(command, shell=True, cwd=tmp_path,
                                env={**env, 'CLAUDE_PROJECT_DIR': str(tmp_path)},
                                input='{}', text=True, capture_output=True)
        assert broken.returncode == 2


def _plain_event(text, cwd, skill='earned-media-builder'):
    return {'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1', 'tool_use_id': 't1',
            'cwd': str(cwd), 'tool_input': {'skill': skill, 'args': text}}


def _gated_workspace(tmp_path, monkeypatch, gate_result):
    from test_workspace_gates import _write_manifest
    monkeypatch.setattr(router, 'ROOT', tmp_path)
    monkeypatch.setattr(hook, 'ROOT', tmp_path)
    _write_manifest(tmp_path, 'venture', gate_result, monkeypatch)
    return tmp_path / 'projects' / 'venture'


def test_plain_text_multi_mode_infers_route(tmp_path, monkeypatch):
    cwd = _gated_workspace(tmp_path, monkeypatch, 'pass')
    text = 'discover backlink opportunities for my site'
    out = hook.check_dispatch(_plain_event(text, cwd))['hookSpecificOutput']
    assert out['updatedInput']['args'] == text
    assert '"route_id": "earned-media-discovery"' in out['additionalContext']
    assert 'permissionDecision' not in out


def test_plain_text_ambiguous_lists_route_ids(tmp_path, monkeypatch):
    cwd = _gated_workspace(tmp_path, monkeypatch, 'pass')
    with pytest.raises(ValueError) as excinfo:
        hook.check_dispatch(_plain_event('discover backlinks and verify backlinks', cwd))
    for route_id in ('earned-media-discovery', 'earned-media-verification'):
        assert route_id in str(excinfo.value)


def test_plain_text_gated_route_outside_workspace_still_blocked(tmp_path):
    with pytest.raises(ValueError, match='JSON route envelope'):
        hook.check_dispatch(_plain_event('discover backlink opportunities for my site', tmp_path))


def test_gate_still_blocks_plain_text(tmp_path, monkeypatch):
    cwd = _gated_workspace(tmp_path, monkeypatch, 'not_run')
    with pytest.raises(ValueError, match='pain-first'):
        hook.check_dispatch(_plain_event('discover backlink opportunities for my site', cwd))


def test_infer_mode_scores_match_phrases():
    assert router.infer_mode('earned-media-builder', 'Verify backlinks please') == ('earned-media-verification', [])
    mode, candidates = router.infer_mode('earned-media-builder', 'something unrelated')
    assert mode is None and 'earned-media-preparation' in candidates


def _packet_with_reference(tmp_path, monkeypatch, words):
    import json
    from scripts import route_workflow
    (tmp_path / 'config').mkdir(exist_ok=True)
    (tmp_path / 'ref.md').write_text('# Inline Heading\n' + 'word ' * words)
    catalog = route_workflow.load_catalog()
    catalog['evidence-scout']['required_references'] = ['ref.md']
    path = tmp_path / 'config/skill-catalog.json'
    path.write_text(json.dumps({'skills': catalog}))
    monkeypatch.setattr(route_workflow, 'CATALOG_PATH', path)
    return route_workflow.route_request('customer feedback', intent='evidence-scout',
                                        task_scope='focused', check_skill='evidence-scout')


def test_packet_inlines_short_required_references(tmp_path, monkeypatch):
    packet = _packet_with_reference(tmp_path, monkeypatch, 300)
    assert '--- ref.md ---' in packet['reference_text']
    assert '# Inline Heading' in packet['reference_text']
    assert packet['required_references'] == ['ref.md']


def test_packet_lists_long_references_with_word_counts(tmp_path, monkeypatch):
    packet = _packet_with_reference(tmp_path, monkeypatch, 1600)
    assert 'reference_text' not in packet
    assert packet['required_reference_words']['ref.md'] > 1500


# Task 21: the gate is evaluated for every matched route, not only the winner, because the specialist receives the
# whole request. A request that also names a gated route is blocked by that route's gate as if it had won.
def _not_passed_project(tmp_path, monkeypatch):
    return _gated_workspace(tmp_path, monkeypatch, 'not_run')


@pytest.mark.parametrize('request_text', [
    pytest.param('Build a new pricing page, then do a pre-release check', marks=pytest.mark.xfail(
        strict=True, reason='no website-build match phrase covers "pricing page"; only "pre-release check" matches. '
                            'Match phrases are out of scope for Task 21 (reported).')),
    'Do a pre-release check of the landing page and fix the hero',
])
def test_request_naming_a_gated_website_route_is_blocked_by_its_gate(tmp_path, monkeypatch, request_text):
    _not_passed_project(tmp_path, monkeypatch)
    alone = router.route_request('Build a landing page', project='venture', entry_mode='business_linked')
    assert alone['route_id'] == 'website-build' and alone['gate_blocked']
    packet = router.route_request(request_text, project='venture', entry_mode='business_linked')
    assert packet['route_id'] == 'pre-release-regression'
    assert 'website-build' in packet['matched_route_ids']
    assert packet['gate_blocked'] is True and packet['gate'] == alone['gate']
    assert packet['gate_route_id'] == 'website-build' and 'website-build' in packet['reason']


def test_hook_envelope_naming_a_gated_route_is_denied(tmp_path, monkeypatch):
    cwd = _not_passed_project(tmp_path, monkeypatch)
    payload = _plain_event('', cwd, skill='site-testing')
    payload['tool_input']['args'] = json.dumps({'route': {
        'request': 'Do a pre-release check of the landing page and fix the hero', 'intent': 'pre-release-regression',
        'task_scope': 'execution', 'project': 'venture', 'standalone': False}, 'input': 'check and fix'})
    with pytest.raises(ValueError, match='website-build'):
        hook.check_dispatch(payload)


PAIN_GATED_EXTRA = 'Do a pre-release regression of the content calendar'


def test_request_naming_a_pain_gated_route_is_blocked_by_the_pain_gate(tmp_path, monkeypatch):
    _not_passed_project(tmp_path, monkeypatch)
    packet = router.route_request(PAIN_GATED_EXTRA, project='venture')
    assert packet['route_id'] == 'pre-release-regression'
    assert packet['gate_blocked'] is True and packet['gate'] == 'pain_first'
    assert packet['gate_route_id'] == 'social-marketing' and 'social-marketing' in packet['reason']
    cwd = tmp_path / 'projects' / 'venture'
    with pytest.raises(ValueError, match='pain-first'):
        hook.check_dispatch(_plain_event(PAIN_GATED_EXTRA, cwd, skill='site-testing'))


def test_one_audited_override_per_request_covers_the_matched_gated_route(tmp_path, monkeypatch):
    manifest = _not_passed_project(tmp_path, monkeypatch) / 'cases/venture/market_research/manifest.json'
    assert manifest.is_file()
    with pytest.raises(ValueError, match='problem_validation'):
        router.route_request(PAIN_GATED_EXTRA, project='venture', override_gate=True)
    assert json.loads(manifest.read_text())['events'] == []
    for _ in range(2):  # replay-safe: the same request records one event
        packet = router.route_request(PAIN_GATED_EXTRA, project='venture', override_gate=True,
                                      override_stages=['problem_validation'], override_reason='Founder: "skip it"')
        assert not packet.get('gate_blocked') and packet['gate_override'] is True
        assert packet['route_id'] == 'pre-release-regression'
    events = json.loads(manifest.read_text())['events']
    assert [e['event'] for e in events] == ['routing_gate_override:social-marketing']


@pytest.mark.parametrize('project', ['', 'venture'])
def test_request_matching_only_ungated_routes_is_unchanged(tmp_path, monkeypatch, project):
    _not_passed_project(tmp_path, monkeypatch)
    packet = router.route_request('Run a Playwright pre-release check of the app', project=project)
    assert packet['route_id'] == 'pre-release-regression' and 'gate_blocked' not in packet
    assert packet['matched_route_ids'] == ['webapp-testing', 'pre-release-regression']


def test_standalone_brand_entry_without_project_keeps_todays_behaviour():
    for text in ('Create a logo for my bakery', 'Create a brand identity for my landing page'):
        packet = router.route_request(text)
        assert packet['route_id'] == 'standalone-brand' and packet['entry_mode'] == 'standalone'
        assert 'gate_blocked' not in packet


def test_matched_routes_lists_every_phrase_match_once():
    ids = [route['id'] for route in router.matched_routes('Do a pre-release check of the landing page, landing page')]
    assert ids == ['website-build', 'pre-release-regression']
    assert router.matched_routes("Don't build a landing page; run a pre-release check")[0]['id'] == 'pre-release-regression'


def test_plugin_namespaced_skill_is_routed_like_the_bare_name():
    def dispatch(skill):
        return hook.check_dispatch({'hook_event_name': 'PreToolUse', 'tool_name': 'Skill', 'session_id': 's1',
                                    'tool_use_id': 't1', 'cwd': str(ROOT), 'tool_input': {
                                        'skill': skill, 'args': 'Research pain points of freelance translators'}})
    plugin = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())['name']
    bare = dispatch('evidence-scout')['hookSpecificOutput']
    namespaced = dispatch(f'{plugin}:evidence-scout')['hookSpecificOutput']
    assert namespaced['additionalContext'] == bare['additionalContext']
    assert '"route_id": "evidence-scout"' in namespaced['additionalContext']
    assert dispatch('other-plugin:evidence-scout') == {}
    with pytest.raises(ValueError, match='merged into'):
        dispatch(f'{plugin}:interview-bridge')


@pytest.mark.parametrize('intent', ['', 'smoke-test-design'])
def test_phrase_inside_the_winners_phrase_is_not_a_second_request(tmp_path, monkeypatch, intent):
    """"landing page" inside "landing page test" is the smoke test's own wording; a separate "landing page" is not."""
    _not_passed_project(tmp_path, monkeypatch)
    kwargs = dict(intent=intent, project='venture', entry_mode='business_linked')
    packet = router.route_request('Design a landing page test', **kwargs)
    assert packet['route_id'] == 'smoke-test-design' and not packet.get('gate_blocked')
    assert packet['matched_route_ids'] == ['website-build', 'smoke-test-design']
    packet = router.route_request('Design a landing page test for the landing page', **kwargs)
    assert packet['gate_blocked'] and packet['gate_route_id'] == 'website-build'


def test_a_phrase_both_routes_claim_verbatim_does_not_shadow_the_gated_route(tmp_path, monkeypatch):
    """"validation page" is a phrase of ungated smoke-test-design (wins the tie) and gated validation-page."""
    _not_passed_project(tmp_path, monkeypatch)
    packet = router.route_request('Build a validation page', project='venture', entry_mode='business_linked')
    assert packet['route_id'] == 'smoke-test-design'
    assert packet['gate_blocked'] is True and packet['gate_route_id'] == 'validation-page'


def test_override_does_not_record_when_a_co_matched_route_blocks_without_override(tmp_path, monkeypatch):
    """Winner social-marketing (pain gate, lifted by the override) + website-build (strategy plan, not overridable)."""
    manifest = _not_passed_project(tmp_path, monkeypatch) / 'cases/venture/market_research/manifest.json'
    request = 'Create a social media plan for the landing page'
    kwargs = dict(project='venture', entry_mode='business_linked', task_scope='execution', override_gate=True,
                  override_stages=['problem_validation'], override_reason='Founder: "skip it"')
    alone = router.route_request('Create a social media plan', **{**kwargs, 'override_gate': False})
    assert alone['route_id'] == 'social-marketing' and alone['gate'] == 'pain_first'
    packet = router.route_request(request, **kwargs)
    assert packet['route_id'] == 'social-marketing'
    assert packet['gate_blocked'] is True and packet['gate'] == 'strategy_plan_required'
    assert packet['gate_route_id'] == 'website-build' and 'gate_override' not in packet
    assert json.loads(manifest.read_text())['events'] == []


def test_plain_text_outside_a_workspace_needs_an_envelope_when_any_matched_route_is_gated(tmp_path):
    with pytest.raises(ValueError, match='JSON route envelope'):
        hook.check_dispatch(_plain_event('Do a pre-release regression of the content calendar', tmp_path,
                                         skill='site-testing'))
    out = hook.check_dispatch(_plain_event('Run the pre-release regression for v2', tmp_path, skill='site-testing'))
    assert '"route_id": "pre-release-regression"' in out['hookSpecificOutput']['additionalContext']


@pytest.mark.parametrize('content', [None, '{not json', '[]', '{"name": 7}', '{"name": ""}', '{}'])
def test_missing_or_malformed_plugin_manifest_strips_no_namespace(tmp_path, monkeypatch, content):
    if content is not None:
        (tmp_path / '.claude-plugin').mkdir()
        (tmp_path / '.claude-plugin/plugin.json').write_text(content)
    name = hook.plugin_name(tmp_path)
    assert name == hook.NO_PLUGIN
    monkeypatch.setattr(hook, 'PLUGIN_NAME', name)
    assert hook.repository_skill_name('evidence-scout-agent-set:evidence-scout') == 'evidence-scout-agent-set:evidence-scout'
    assert hook.repository_skill_name(':evidence-scout') == ':evidence-scout'
    assert hook.repository_skill_name('evidence-scout') == 'evidence-scout'


@pytest.mark.parametrize('skill,text', [
    ('opportunity-risk-designer', 'Design a landing page test'),
    ('opportunity-risk-designer', 'falsify claims'),
    ('competitor-research', 'Analyze these three competitor landing pages and their pricing CTAs.'),
])
def test_plain_text_outside_a_workspace_dispatches_when_the_router_would(tmp_path, skill, text):
    """The hook uses the router's own matcher and shadowing, so it refuses only what the router would gate."""
    out = hook.check_dispatch(_plain_event(text, tmp_path, skill=skill))
    assert out['hookSpecificOutput']['updatedInput']['args'] == text


def test_plain_text_outside_a_workspace_refuses_a_non_shadowed_gated_co_match(tmp_path):
    with pytest.raises(ValueError, match='JSON route envelope'):
        hook.check_dispatch(_plain_event('Design a smoke test for the landing page', tmp_path,
                                         skill='opportunity-risk-designer'))


@pytest.mark.parametrize('phrase,text,expected', [
    ('FAL', 'falsify claims in the draft', False),
    ('FAL', 'generate the hero with fal', True),
    ('landing page', 'build two landing pages', True),
    ('landing page', 'landing pagesx', False),
    ('A/B test', 'run an a/b test on pricing', True),
    ('A/B test', 'run a/b testing and a/b tests', True),
    ('A/B test', 'a/b testers', False),
    ('marketing website', 'two marketing websites', True),
    ('integrate GA4', 'integrate ga4s', False),
    ('go-to-market', 'a go to market plan', True),
    ("competitor's website", "review my competitor's website", True),
])
def test_phrase_matching_is_whole_word(phrase, text, expected):
    assert router.phrase_in(phrase, router._normalized(text)) is expected


def test_falsify_is_not_a_brand_asset_request(tmp_path, monkeypatch):
    _not_passed_project(tmp_path, monkeypatch)
    assert [r['id'] for r in router.matched_routes('Falsify claims in the draft')] == ['claim-falsification']
    packet = router.route_request('Find competitors, then falsify claims', project='venture', entry_mode='business_linked')
    assert packet['route_id'] == 'competitor-discovery' and not packet.get('gate_blocked')


def test_plural_landing_pages_still_meets_the_website_gate(tmp_path, monkeypatch):
    _not_passed_project(tmp_path, monkeypatch)
    packet = router.route_request('Do a pre-release check of the landing pages', project='venture',
                                  entry_mode='business_linked')
    assert packet['gate_blocked'] is True and packet['gate_route_id'] == 'website-build'


INFLECTED_GATED_REQUESTS = [
    ('opportunity-risk-designer', 'Design a smoke test for the waitlist pages'),
    ('opportunity-risk-designer', 'Design a smoke test for the validation pages'),
    ('site-testing', 'Do a pre-release check of the marketing websites'),
    ('competitor-research', 'Find competitors and write two social campaigns'),
    ('evidence-scout', 'Find customer pain, then build A/B tests'),
    ('opportunity-risk-designer', 'Rank assumptions, then design fintech pilots'),
]


@pytest.mark.parametrize('skill,text', INFLECTED_GATED_REQUESTS)
def test_inflected_gated_phrase_still_needs_an_envelope_outside_a_workspace(tmp_path, skill, text):
    with pytest.raises(ValueError, match='JSON route envelope'):
        hook.check_dispatch(_plain_event(text, tmp_path, skill=skill))


@pytest.mark.parametrize('skill,text', INFLECTED_GATED_REQUESTS)
def test_inflected_gated_phrase_is_gated_in_a_not_passed_project(tmp_path, monkeypatch, skill, text):
    _not_passed_project(tmp_path, monkeypatch)
    packet = router.route_request(text, project='venture', entry_mode='business_linked')
    assert packet['route_id'] == 'clarify' or packet.get('gate_blocked'), packet['route_id']
