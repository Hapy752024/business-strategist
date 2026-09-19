import json
import pytest
from scripts import case_workspace as c, route_workflow as routing
from scripts.evidence_scout import workspace


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(routing, 'ROOT', tmp_path)
    p = tmp_path / 'projects/topic'
    c.initialize(p, 'Topic'); scope = c.add_case(p, 'a', 'A')
    for name in ('customer_segments', 'customer_journey', 'pain_points'):
        target = scope / 'market_research' / name / 'current.md'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Synthetic sourced baseline; unknown demand.')
    return p, scope


def test_appraisal_without_selection_does_not_allow_commitment(tmp_path, monkeypatch):
    p, scope = setup(tmp_path, monkeypatch)
    packet = routing.route_request('Assess this case', intent='case-appraisal', project='topic', case_id='a', task_scope='strategy', check_skill='opportunity-risk-designer')
    assert not packet.get('gate_blocked')
    assert packet['case_context']['execution_binding'] is None
    assert packet['mode'] == 'appraisal'
    with pytest.raises(ValueError, match='selected'):
        routing.route_request('Launch it', intent='gtm-strategy', project='topic', case_id='a', override_gate=True)
    with pytest.raises(ValueError, match='selected'):
        workspace.update_stage(scope, 'business_model_draft', expected_assessment_revision=1, status='in_progress', gate_result='not_run', override='explicit pain override')


def test_case_pain_pass_and_interpretation_correction(tmp_path, monkeypatch):
    p, scope = setup(tmp_path, monkeypatch)
    pain = scope / 'market_research/pain_points/current.md'
    workspace.update_stage(scope, 'problem_validation', expected_assessment_revision=1, status='passed', gate_result='pass', artifacts=[pain])
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
