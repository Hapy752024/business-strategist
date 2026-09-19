"""Regression coverage for skipped prerequisites and durable coaching contracts."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import route_workflow, case_workspace as cases
from scripts.evidence_scout import workspace


def setup_project(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, 'ROOT', tmp_path)
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    root = workspace.create_project_workspace('Workflow repairs')
    case_id = cases.read_project(root)['slug']
    scope = cases.add_case(root, case_id, 'Reviewed test case')
    cases.select(root, case_id, 'Test scope', 'select-fixture', 'Explicit fixture selection')
    (scope / 'market_research/pain_points').mkdir(parents=True)
    (scope / 'strategy/intake').mkdir(parents=True)
    return scope


def test_explicit_specialist_alias_and_ambiguous_modes():
    assert route_workflow.route_request('grill', intent='idea-grill')['skill'] == 'idea-grill'
    with pytest.raises(ValueError, match='Unknown route intent'):
        route_workflow.route_request('website', intent='brand-website-designer-builder')


def test_strategy_requires_reviewed_intake_and_risk_even_with_pain_pass(tmp_path, monkeypatch):
    ws = setup_project(tmp_path, monkeypatch)
    artifact = ws / 'market_research/pain_points/evidence.jsonl'
    artifact.write_text('{"evidence_id":"record-1"}\n')
    workspace.update_stage(ws, 'problem_validation', expected_assessment_revision=1, status='passed', gate_result='pass', artifacts=[artifact])
    packet = route_workflow.route_request('GTM strategy', intent='business-positioning', task_scope='strategy', project=ws.name)
    assert packet['gate_blocked'] and packet['first_skill'] == 'idea-grill'
    assert packet['missing_stages'] == ['intake', 'segment_selection', 'customer_profile', 'opportunity_risk', 'operator_playbook']
    # A perfectly named document without a passed checkpoint cannot satisfy intake.
    (ws / 'strategy/intake/idea-grill-passed.md').write_text('Intake passed; founder approved.')
    assert 'intake' in route_workflow.route_request('GTM strategy', intent='business-positioning', task_scope='strategy', project=ws.name)['missing_stages']


def test_interview_and_provisional_risk_not_deadlocked_by_missing_pain(tmp_path, monkeypatch):
    ws = setup_project(tmp_path, monkeypatch)
    for skill in ['interview-bridge', 'opportunity-risk-designer', 'evidence-scout']:
        packet = route_workflow.route_request('repair and investigate', intent="opportunity-prioritization" if skill == "opportunity-risk-designer" else skill, task_scope='focused', project=ws.name, check_skill=skill)
        assert not packet.get('gate_blocked')
    assert not route_workflow.route_request('build a landing page', project=ws.name).get('gate_blocked')
    assert route_workflow.route_request('Create a social media plan', project=ws.name)['gate_blocked']


def test_completed_prerequisites_are_reused_and_stale_files_block(tmp_path, monkeypatch):
    ws = setup_project(tmp_path, monkeypatch)
    required = ['intake', 'segment_selection', 'customer_profile', 'problem_validation', 'opportunity_risk', 'operator_playbook']
    for stage in required:
        file = ws / 'market_research/pain_points' / f'{stage}.md'
        file.write_text('Reviewed current scope artifact.')
        workspace.update_stage(ws, stage, expected_assessment_revision=1, status='passed', gate_result='pass', artifacts=[file])
    def route():
        return route_workflow.route_request('GTM strategy', intent='business-positioning', task_scope='strategy', project=ws.name)
    assert not route().get('gate_blocked')
    (ws / 'market_research/pain_points/opportunity_risk.md').write_text('')
    with pytest.raises(ValueError, match='stale source'):
        route()
    # An override cannot bless stale source bytes; explicit review must refresh them.
    with pytest.raises(ValueError, match='stale source'):
        route_workflow.route_request('GTM strategy', intent='business-positioning', task_scope='strategy', project=ws.name, override_gate=True, override_stages=['opportunity_risk'])
    file = ws / 'market_research/pain_points/opportunity_risk.md'
    file.write_text('New explicit review of corrected scope.')
    workspace.update_stage(ws, 'opportunity_risk', expected_assessment_revision=1, status='passed', gate_result='pass', artifacts=[file])
    assert not route().get('gate_blocked')


def test_produced_manifest_revision_and_coaching_schema(tmp_path, monkeypatch):
    ws = setup_project(tmp_path, monkeypatch)
    manifest = workspace.read_manifest(ws)
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas/research-manifest.schema.json').read_text())
    # Validate new local properties directly; stage refs are covered by setup schema checks.
    Draft202012Validator(schema['properties']['manifest_revision']).validate(manifest['manifest_revision'])
    coaching = {'known_answers':[{'field':'languages','value':'French and Spanish','provenance':'user_confirmed'}, {'field':'network','value':'No target-customer contacts','provenance':'user_confirmed'}], 'unresolved_inputs':['affordable downside'], 'pending_question':'What initial learning budget can you lose?'}
    validator=Draft202012Validator(schema['properties']['coaching'])
    validator.validate(coaching)
    with pytest.raises(Exception):
        validator.validate({**coaching,'pending_question':['Choose a segment?','Choose a country?']})
    with pytest.raises(Exception):
        validator.validate({**coaching,'known_answers':[{'field':'budget','value':'invented','provenance':'user_approved_by_silence'}]})


def test_one_override_event_for_multiple_blocked_prerequisites(tmp_path, monkeypatch):
    ws = setup_project(tmp_path, monkeypatch)
    packet = route_workflow.route_request('GTM strategy', intent='business-positioning', task_scope='strategy', project=ws.name, override_gate=True, override_stages=['intake','segment_selection','customer_profile','problem_validation','opportunity_risk','operator_playbook'])
    assert not packet['gate_blocked']
    events = workspace.read_manifest(ws)['events']
    assert sum(e['event']=='routing_gate_override:business-positioning' for e in events)==1


def test_validation_queries_keep_target_terms_and_discovery_can_be_broad():
    from scripts.evidence_scout.collect import query_plan
    queries = query_plan('supplier payment timing', 'French retail shop owners', problem_keywords='supplier invoice due', segment_keywords='commerçant,boutique')
    assert queries and all(q.endswith((' commerçant', ' boutique')) for q in queries)
    assert not any('contractor' in q for q in queries)
    discovery = query_plan('retail operations', '', research_mode='discovery')
    assert discovery


def test_cli_requires_target_before_validation(monkeypatch):
    import sys
    from scripts.evidence_scout.collect import parse_args
    monkeypatch.setattr(sys, 'argv', ['collect.py', '--topic', 'payment timing'])
    with pytest.raises(SystemExit) as exc:
        parse_args()
    assert exc.value.code == 2
    monkeypatch.setattr(sys, 'argv', ['collect.py', '--topic', 'payment timing', '--research-mode', 'discovery'])
    assert parse_args().research_mode == 'discovery'
    monkeypatch.setattr(sys, 'argv', ['collect.py', '--topic', 'payment timing', '--customer-segment', 'retail shop owners', '--segment-keywords', 'commerçant'])
    assert parse_args().segment_keywords == 'commerçant'


def test_keyword_matches_cannot_be_reported_as_reviewed_target_pain():
    from scripts.evidence_scout.collect import quality_summary
    records=[{'source':'reddit','source_intent':'user_pain','strength':'weak','segment_relation':'adjacent'}]
    flags=' '.join(quality_summary(records, {}))
    assert 'candidate user-pain' in flags and 'require semantic source and target-segment review' in flags
    assert 'Only 1 direct user-pain' not in flags


@pytest.mark.parametrize('segment',['unknown','unspecified','unresolved','TBD'])
def test_placeholder_segment_cannot_become_narrow_validation(segment, monkeypatch):
    import sys
    from scripts.evidence_scout.collect import parse_args
    monkeypatch.setattr(sys, 'argv', ['collect.py', '--topic', 'supplier bills', '--customer-segment', segment, '--segment-keywords', 'merchant'])
    with pytest.raises(SystemExit) as exc:
        parse_args()
    assert exc.value.code == 2
