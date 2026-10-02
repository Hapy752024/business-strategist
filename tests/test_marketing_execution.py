import importlib.util
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("marketing_execution", ROOT / "scripts/marketing/execution.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def action(**overrides):
    return {"id":"pitch", "objective":"Pitch a relevant publisher", "actor":"owner", "dependencies":[],
            "prepared_materials":[], "next_step":"send prepared pitch", "completion_criterion":"publisher confirms placement",
            "commitment_state":"accepted", "execution_status":"awaiting_owner", "required_for_scope":True} | overrides


def test_owner_send_does_not_complete_required_publisher_outcome_and_optional_ideas_do_not_block():
    doc = {"schema_version":1, "scope":"earn a relevant mention", "revision":1, "actions":[action(), action(id="optional", required_for_scope=False)]}
    assert not module.validate(doc)
    assert not module.scope_complete(doc)
    doc["actions"][0].update(commitment_state="completed", execution_status="submitted")
    assert not module.scope_complete(doc)
    doc["actions"][0].update(execution_status="verified", verification="public page checked")
    assert module.scope_complete(doc)


def test_unknown_dependency_and_cycle_are_rejected():
    doc = {"schema_version":1, "scope":"test", "revision":1,
           "actions":[action(dependencies=["second"]), action(id="second", dependencies=["pitch"])]}
    assert any("cycle" in issue for issue in module.validate(doc))


def test_renderer_outputs_precise_owner_steps():
    doc = {"schema_version":1, "scope":"test", "revision":1,
           "actions":[action(destination="https://publisher.example/submit", user_step="Open and submit this pitch") ]}
    _, owner = module.render(doc)
    assert "Open and submit this pitch" in owner
    assert "https://publisher.example/submit" in owner


def test_platform_action_needs_destination_rules_fee_and_owner_step():
    doc = {"schema_version":1, "scope":"submit listing", "revision":1,
           "actions":[action(destination="https://listing.example", fee="none")]}
    errors = module.validate(doc)
    assert any("eligibility_checked_at" in issue for issue in errors)
    assert any("user_step" in issue for issue in errors)


def test_workstream_binds_execution_and_invalidates_changed_material_verification(tmp_path):
    from scripts import case_workspace, subprojects
    root = tmp_path / "project"
    subprojects.start(root, "marketing", "Demo", "Selected marketing execution")
    material = "Draft pitch v1\n"
    digest = hashlib.sha256(material.encode()).hexdigest()
    doc = {"schema_version":1, "scope":"earn a mention", "revision":1,
           "actions":[action(actor="agent", commitment_state="completed", execution_status="verified",
             verification="publisher page checked", prepared_materials=[{"path":"pitch.md", "sha256":digest}])]}
    manifest_revision = case_workspace.read_project(root)["manifest_revision"]
    state = subprojects.publish_marketing_workstream(root, {"pitch.md":material, "execution-plan.json":json.dumps(doc)},
        expected_manifest_revision=manifest_revision, decision_id="marketing-test", reason="Bind the tested execution artifact.")
    assert "execution-plan.json" in {item["path"] for item in state["artifact_refs"]}
    doc["revision"] = 2
    doc["actions"][0]["prepared_materials"] = [{"path":"pitch.md", "sha256":hashlib.sha256(b"Draft pitch v2").hexdigest()}]
    manifest_revision = case_workspace.read_project(root)["manifest_revision"]
    state = subprojects.publish_marketing_workstream(root, {"pitch.md":"Draft pitch v2", "execution-plan.json":json.dumps(doc)},
        expected_manifest_revision=manifest_revision, decision_id="marketing-refresh", reason="Replace the changed pitch and recheck publication.")
    output = json.loads((subprojects.path(root, "marketing") / "execution-plan.json").read_text())
    assert output["actions"][0]["verification"] is None
    assert output["actions"][0]["execution_status"] == "prepared"
    assert output["actions"][0]["commitment_state"] == "accepted"
