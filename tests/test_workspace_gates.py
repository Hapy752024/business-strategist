"""Pain-first gate tests: stage machine enforcement and routing gate.

The pain-first rule: customer segment -> customer journey -> validated pain
points (with web-searched evidence) come before commitment work. The stage
gate is ``problem_validation``; downstream commitment stages require it.
"""
from pathlib import Path
import json

import pytest

from scripts.evidence_scout import workspace
from scripts import route_workflow, case_workspace as cases


def _pass_pain_gate(root: Path) -> Path:
    ws = workspace.create_project_workspace("Gate test", layout_version=1)
    evidence = ws / "market_research" / "pain_points" / "runs" / "run-1" / "evidence.jsonl"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text('{"evidence_id": "e1"}\n', encoding="utf-8")
    workspace.update_stage(
        ws,
        "problem_validation",
        status="passed",
        gate_result="pass",
        artifacts=[evidence],
        next_action="Segment, journey, and pains validated with web-searched evidence.",
    )
    return ws


def test_pain_gate_requires_pain_point_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "ROOT", tmp_path)
    ws = workspace.create_project_workspace("Gate test", layout_version=1)
    with pytest.raises(ValueError, match="pain_points"):
        workspace.update_stage(
            ws,
            "problem_validation",
            status="passed",
            gate_result="pass",
            artifacts=[ws / "README.md"],
        )


def test_downstream_stage_blocked_before_pain_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "ROOT", tmp_path)
    ws = workspace.create_project_workspace("Gate test", layout_version=1)
    for stage in sorted(workspace.PAIN_GATE_DOWNSTREAM):
        with pytest.raises(ValueError, match="pain-first gate"):
            workspace.update_stage(ws, stage, status="in_progress", gate_result="not_run")


def test_downstream_stage_unblocked_after_evidence_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "ROOT", tmp_path)
    ws = _pass_pain_gate(tmp_path)
    manifest = workspace.read_manifest(ws)
    assert manifest["stages"]["problem_validation"]["gate_result"] == "pass"
    workspace.update_stage(ws, "business_model_draft", status="in_progress", gate_result="not_run")
    assert workspace.read_manifest(ws)["stages"]["business_model_draft"]["status"] == "in_progress"


def test_override_is_recorded_in_manifest_events(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "ROOT", tmp_path)
    ws = workspace.create_project_workspace("Gate test", layout_version=1)
    workspace.update_stage(
        ws,
        "business_model_draft",
        status="in_progress",
        gate_result="not_run",
        override="founder directive",
    )
    manifest = workspace.read_manifest(ws)
    assert any(event["event"] == "gate_override:business_model_draft:founder directive" for event in manifest["events"])


def _write_manifest(tmp_path: Path, slug: str, gate_result: str) -> Path:
    root = tmp_path / 'projects' / slug
    cases.initialize(root, slug)
    scope = cases.add_case(root, slug, slug)
    if not cases.read_project(root)['selection']:
        cases.select(root, slug, 'Test configuration', 'select-fixture', 'Explicit fixture selection')
    manifest_path = scope / 'market_research/manifest.json'
    data = cases.case_manifest(root, slug)
    evidence = scope / 'market_research/pain_points/current.md'
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text('Synthetic evidence')
    data['stages'] = {'problem_validation': {'status': 'passed' if gate_result == 'pass' else 'pending', 'gate_result': gate_result,
        'reviewed_revision': 1, 'artifacts': [{'path': 'market_research/pain_points/current.md'}]}}
    data['events'] = []
    manifest_path.write_text(json.dumps(data))
    return manifest_path


def test_routing_gate_blocks_downstream_routes(tmp_path, monkeypatch):
    monkeypatch.setattr(route_workflow, "ROOT", tmp_path)
    _write_manifest(tmp_path, "gate-test", "not_run")
    packet = route_workflow.route_request("Create paid social", project="gate-test")
    assert packet["route_id"] == "social-marketing"
    assert packet["gate_blocked"] is True
    assert packet["first_skill"] == "idea-grill"
    assert packet["gate_concepts"] == ["customer_segments", "customer_journey", "pain_points"]


def test_routing_gate_ignores_ungated_routes_and_missing_project(tmp_path, monkeypatch):
    monkeypatch.setattr(route_workflow, "ROOT", tmp_path)
    _write_manifest(tmp_path, "gate-test", "not_run")
    assert "gate_blocked" not in route_workflow.route_request("find competitors", project="gate-test")
    assert "gate_blocked" not in route_workflow.route_request("Create paid social")
    # Unknown project (no manifest on disk) is treated as not passed.
    packet = route_workflow.route_request("Create paid social", project="missing-project")
    assert packet["gate_blocked"] is True


def test_routing_gate_passes_after_gate_and_override_is_audited(tmp_path, monkeypatch):
    monkeypatch.setattr(route_workflow, "ROOT", tmp_path)
    manifest_path = _write_manifest(tmp_path, "gate-test", "pass")
    packet = route_workflow.route_request("Create paid social", project="gate-test")
    assert "gate_blocked" not in packet

    manifest_path = _write_manifest(tmp_path, "gate-test", "not_run")
    packet = route_workflow.route_request("Create paid social", project="gate-test", override_gate=True, override_stages=["problem_validation"])
    assert packet["gate_blocked"] is False
    assert packet["gate_override"] is True
    events = json.loads(manifest_path.read_text(encoding="utf-8"))["events"]
    assert any(event["event"] == "routing_gate_override:social-marketing" for event in events)


@pytest.mark.parametrize('slug', ['../escape', '/tmp/escape', 'one/two', '_archive'])
def test_router_rejects_project_paths(tmp_path, monkeypatch, slug):
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='slug'):
        route_workflow.route_request('Create paid social', project=slug, override_gate=True)


@pytest.mark.parametrize('component', ['project', 'research', 'manifest', 'lock'])
def test_router_rejects_symlinked_gate_paths(tmp_path, monkeypatch, component):
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    target = tmp_path / 'other'
    target.mkdir()
    manifest = _write_manifest(tmp_path, 'gate-test', 'not_run')
    path = {'project': manifest.parent.parent, 'research': manifest.parent,
            'manifest': manifest, 'lock': manifest.parent / 'manifest.lock'}[component]
    if path.exists():
        path.rename(target / path.name)
        path.symlink_to(target / path.name)
    else:
        path.symlink_to(target / 'lock')
    with pytest.raises(ValueError, match='symlinks'):
        route_workflow.route_request('Create paid social', project='gate-test', override_gate=True)


@pytest.mark.parametrize('payload', [[], None, {'stages': []}, {'stages': {'problem_validation': []}},
                                     {'stages': {'problem_validation': {'status': 'blocked', 'gate_result': 'conditional_pass'}}}])
def test_malformed_or_unpassed_gate_stays_blocked(tmp_path, monkeypatch, payload):
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    manifest = _write_manifest(tmp_path, 'gate-test', 'not_run')
    manifest.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='invalid case'):
        route_workflow.route_request('Create paid social', project='gate-test')


def test_override_requires_auditable_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='requires --project'):
        route_workflow.route_request('Create paid social', override_gate=True)
    with pytest.raises(ValueError, match='missing'):
        route_workflow.route_request('Create paid social', project='missing', override_gate=True)
    manifest = _write_manifest(tmp_path, 'gate-test', 'not_run')
    for text in ['{broken', '[]', '{"events": "invalid"}']:
        manifest.write_text(text)
        with pytest.raises(ValueError, match='invalid case'):
            route_workflow.route_request('Create paid social', project='gate-test', override_gate=True)
        assert manifest.read_text() == text


@pytest.mark.parametrize('kind', ['substring', 'outside', 'directory', 'empty', 'symlink'])
def test_pain_artifacts_require_nonempty_file_inside_pain_directory(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(workspace, 'ROOT', tmp_path)
    ws = workspace.create_project_workspace('Gate test', layout_version=1)
    pain = ws / 'market_research' / 'pain_points'
    artifact = pain / 'evidence.jsonl'
    if kind == 'substring':
        artifact = ws / 'not_pain_points.txt'
    elif kind == 'outside':
        artifact = tmp_path / 'pain_points.txt'
    elif kind == 'directory':
        artifact = pain
    elif kind == 'symlink':
        outside = tmp_path / 'outside.jsonl'
        outside.write_text('{"evidence_id": "e1"}\n')
        artifact.symlink_to(outside)
    if kind not in {'directory', 'symlink'}:
        artifact.write_text('' if kind == 'empty' else 'placeholder')
    before = (ws / workspace.RESEARCH_MANIFEST_REL).read_bytes()
    with pytest.raises(ValueError, match='pain_points'):
        workspace.update_stage(ws, 'problem_validation', status='passed', gate_result='pass', artifacts=[artifact])
    assert (ws / workspace.RESEARCH_MANIFEST_REL).read_bytes() == before


def test_conditional_pass_cannot_bypass_stage_status(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, 'ROOT', tmp_path)
    ws = workspace.create_project_workspace('Gate test', layout_version=1)
    with pytest.raises(ValueError, match="status='passed'"):
        workspace.update_stage(ws, 'problem_validation', status='blocked', gate_result='conditional_pass')


def test_blocked_router_cli_returns_nonzero(tmp_path, monkeypatch, capsys):
    import sys
    monkeypatch.setattr(route_workflow, 'ROOT', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['route_workflow.py', 'Create paid social', '--project', 'missing'])
    assert route_workflow.main() == 2
    assert json.loads(capsys.readouterr().out)['gate_blocked'] is True
