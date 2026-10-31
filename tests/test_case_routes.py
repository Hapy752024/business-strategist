import json
import pytest
from scripts import case_workspace as c, route_workflow as routing
from scripts.evidence_scout import workspace
from problem_assessment_fixtures import prepare as prepare_problem_assessment


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(routing, 'ROOT', tmp_path)
    p = tmp_path / 'projects/topic'
    c.initialize(p, 'Topic'); scope = c.add_case(p, 'a', 'A')
    for name in ('customer_segments', 'customer_journey', 'pain_points'):
        target = scope / 'market_research' / name / 'current.md'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Synthetic sourced baseline https://evidence.example/source 2026-09-23; unknown demand.')
    return p, scope


def test_appraisal_without_selection_does_not_allow_commitment(tmp_path, monkeypatch):
    p, scope = setup(tmp_path, monkeypatch)
    packet = routing.route_request('Assess this case', intent='case-appraisal', project='topic', case_id='a', task_scope='strategy', check_skill='opportunity-risk-designer')
    assert packet['gate_blocked'] and packet['gate'] == 'initial_research'
    assert packet['missing_initial_research'] == ['reviewed_case_evidence']
    assert packet['case_context']['execution_binding'] is None
    assert packet['mode'] == 'appraisal'
    with pytest.raises(ValueError, match='selected'):
        routing.route_request('Launch it', intent='gtm-strategy', project='topic', case_id='a', override_gate=True)
    with pytest.raises(ValueError, match='selected'):
        workspace.update_stage(scope, 'business_model_draft', expected_assessment_revision=1, status='in_progress', gate_result='not_run', override='explicit pain override')


def test_case_insights_route_accepts_early_registered_case(tmp_path, monkeypatch):
    monkeypatch.setattr(routing, 'ROOT', tmp_path)
    root = tmp_path / 'projects/topic'
    c.initialize(root, 'Topic')
    c.add_case(root, 'a', 'A')
    packet = routing.route_request('Consolidate case insights', intent='case-insights', project='topic',
                                   case_id='a', task_scope='focused', check_skill='opportunity-risk-designer')
    assert packet['mode'] == 'insights' and not packet.get('gate_blocked')
    assert packet['case_context']['insights_status']['status'] == 'draft'
    assert packet['case_context']['current_concept'].endswith('case_insights.md')
    assert 'references/case-insights.md' in packet['required_references']


def test_case_plan_routes_before_selection_and_keeps_research_gate(tmp_path, monkeypatch):
    p, scope = setup(tmp_path, monkeypatch)
    packet = routing.route_request('Prepare a provisional case business plan', intent='case-business-plan',
                                   project='topic', case_id='a', task_scope='strategy', check_skill='startup-business-builder')
    assert packet['mode'] == 'case_plan'
    assert packet['case_context']['execution_binding'] is None
    assert packet['gate_blocked'] and packet['gate'] == 'case_insights_current'


def test_case_pain_pass_and_interpretation_correction(tmp_path, monkeypatch):
    p, scope = setup(tmp_path, monkeypatch)
    artifacts, _, _ = prepare_problem_assessment(scope, workspace, monkeypatch, case_id='a')
    pain = scope / 'market_research/pain_points/current.md'
    workspace.update_stage(scope, 'problem_validation', expected_assessment_revision=1, status='passed', gate_result='pass', artifacts=artifacts)
    assert routing.pain_gate_state('topic', 'a')[0]
    original = pain.read_bytes()
    c.correct(p, ['a'], 'Original interpretation was wrong', 'correction')
    assert pain.read_bytes() == original
    assert not routing.pain_gate_state('topic', 'a')[0]


def test_case_output_path_and_new_topic_defaults(tmp_path, monkeypatch):
    p, scope = setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='conflicts'):
        workspace.resolve_run_dir(topic='x', workspace_arg=str(p), case_id='a', out_dir=str(p / 'market_research/pain_points/runs/wrong'),
                                  legacy_output=False, workspace_subdir='market_research/pain_points/runs')
    new = workspace.create_project_workspace('new', str(tmp_path / 'new'))
    assert not (new / 'strategy').exists()
    assert c.read_project(new)['selection'] is None


def test_relative_workspace_commands_use_registered_case_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Explicit CLI-style relative paths exercise the public APIs, not just absolute fixtures.
    from pathlib import Path
    relative = Path('relative')
    c.initialize(relative, 'Relative topic')
    c.add_case(relative, 'a', 'A')
    c.select(relative, 'a', 'One scope', 'choose-a', 'Explicit user choice')
    assert c.case_manifest(relative, 'a')['case_id'] == 'a'
    assert c.binding(relative, 'a')['selection_generation'] == 1
    c.correct(relative, ['a'], 'Reinterpret evidence', 'correct-a')
    assert c.case_manifest(relative, 'a')['assessment_revision'] == 2


def test_whitespace_default_follows_evidence_case_not_topic_label(tmp_path, monkeypatch, capsys):
    import sys
    from scripts.evidence_scout import build_whitespace_matrix as builder
    p, scope = setup(tmp_path, monkeypatch)
    evidence = scope / 'market_research/pain_points/evidence.jsonl'
    evidence.write_text('{}\n')
    monkeypatch.setattr(builder, 'read_jsonl', lambda path: [{'synthetic':True}])
    monkeypatch.setattr(builder, 'select_pains', lambda records, limit: records)
    monkeypatch.setattr(builder, 'load_competitors', lambda path, limit: [{'synthetic':True}])
    monkeypatch.setattr(builder, 'render_matrix', lambda *args: '# Synthetic matrix\n')
    monkeypatch.setattr(sys, 'argv', ['build_whitespace_matrix.py','--topic','Different label','--evidence-jsonl',str(evidence),'--competitors-json',str(evidence)])
    assert builder.main() == 0
    from pathlib import Path
    output = Path(json.loads(capsys.readouterr().out)['output'])
    assert output.is_relative_to(scope / 'market_research/solution_alternatives/runs')
    assert output.is_file()


def test_router_errors_name_the_documented_fix(tmp_path, monkeypatch):
    """Task 7.2a: the acceptance agent could not tell from the errors what to run."""
    monkeypatch.setattr(routing, 'ROOT', tmp_path)
    monkeypatch.setattr(workspace, 'ROOT', tmp_path)
    gtm = dict(intent='gtm-strategy', task_scope='strategy', check_skill='archetype-gtm-strategist')
    # A nested path is still rejected, and the error says what --project takes.
    for bad in ('_eval/topic', 'projects/topic', 'Topic'):
        with pytest.raises(ValueError, match=r'top-level directory name under projects/'):
            routing.route_request('GTM', project=bad, case_id='a', **gtm)
    # --case on a project that does not exist is not a migration problem.
    with pytest.raises(ValueError, match=r'no project at projects/missing-topic.*init_project\.py --project .* --workspace projects/missing-topic --case a'):
        routing.route_request('GTM', project='missing-topic', case_id='a', **gtm)
    # A registered but unselected case names the selection command.
    business = workspace.create_project_workspace('Topic', 'projects/topic', 'Seg')
    c.add_case(business, 'a', 'A')
    with pytest.raises(ValueError, match=r'case is not selected for execution.*case_workspace\.py select --workspace projects/topic --case a'):
        routing.route_request('GTM', project='topic', case_id='a', **gtm)
    # A legacy (unversioned) project keeps the migration error.
    legacy = tmp_path / 'projects/legacy-topic/market_research'
    legacy.mkdir(parents=True)
    (legacy / 'manifest.json').write_text('{"stages": {}}')
    with pytest.raises(ValueError, match='migrat'):
        routing.route_request('GTM', project='legacy-topic', case_id='a', intent='idea-validation', task_scope='focused')
