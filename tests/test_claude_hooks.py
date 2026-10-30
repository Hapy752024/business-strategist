import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_hook(path: Path, root: Path, payload: dict) -> dict:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(root)
    result = subprocess.run(["python3", str(path)], cwd=root, env=env,
                            input=json.dumps(payload), text=True,
                            capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout or "{}")


def test_compaction_state_is_session_scoped_and_restore_flags_stale_manifests(tmp_path):
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    assert settings["hooks"]["SessionStart"][0]["matcher"] == "compact"
    for event in ("PreCompact", "PostCompact", "SessionStart"):
        command = settings["hooks"][event][0]["hooks"][0]["command"]
        assert "$CLAUDE_PROJECT_DIR/.claude/hooks/" in command

    project_root = tmp_path / "fixture"
    paths = [project_root / "projects" / slug / "business-analysis" / "market_research" for slug in ("alpha", "beta")]
    for path in paths:
        path.mkdir(parents=True)
        (path / "manifest.json").write_text(json.dumps({"current_stage": "discovery", "next_action": path.parts[-4]}))
    for sid, path in zip(("session-a", "session-b"), paths):
        run_hook(ROOT / ".claude/hooks/precompact.py", project_root,
                 {"session_id": sid, "cwd": str(path), "session_hint": sid})
        run_hook(ROOT / ".claude/hooks/postcompact.py", project_root,
                 {"session_id": sid, "compact_summary": f"summary-{sid}"})

    state_a = json.loads((project_root / ".claude/plans/resume/session-a.json").read_text())
    state_b = json.loads((project_root / ".claude/plans/resume/session-b.json").read_text())
    assert state_a["workspace"]["project_slug"] == "alpha"
    assert state_b["workspace"]["project_slug"] == "beta"
    assert state_a["compact_summary"] == "summary-session-a"
    assert state_b["compact_summary"] == "summary-session-b"

    restored_a = run_hook(ROOT / ".claude/hooks/session_start.py", project_root, {"session_id": "session-a", "source": "compact"})
    context_a = restored_a["hookSpecificOutput"]["additionalContext"]
    assert "alpha" in context_a and "beta" not in context_a and "summary-session-a" in context_a
    manifest = paths[0] / "manifest.json"
    manifest.write_text(json.dumps({"current_stage": "validation", "next_action": "changed"}))
    restored_stale = run_hook(ROOT / ".claude/hooks/session_start.py", project_root, {"session_id": "session-a", "source": "compact"})
    assert "STALE CHECKPOINT" in restored_stale["hookSpecificOutput"]["additionalContext"]


def test_compaction_resolver_prefers_selected_case_and_registered_module(tmp_path):
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("compaction_state_test", ROOT / ".claude/hooks/compaction_state.py")
    helper = module_from_spec(spec)
    spec.loader.exec_module(helper)
    project = tmp_path / "projects" / "legacy"
    case_manifest = project / "business-analysis/cases/selected/market_research/manifest.json"
    shared_manifest = project / "business-analysis/market_research/manifest.json"
    case_manifest.parent.mkdir(parents=True)
    shared_manifest.parent.mkdir(parents=True)
    case_manifest.write_text(json.dumps({"next_action": "selected case action"}))
    shared_manifest.write_text(json.dumps({"next_action": "shared unrelated action"}))
    case = helper.active_workspace(tmp_path, str(case_manifest.parent))
    assert case["case_id"] == "selected"
    assert case["next_action"] == "selected case action"
    assert case["manifest_path"].endswith("cases/selected/market_research/manifest.json")
    assert helper.active_workspace(tmp_path, str(tmp_path)) is None
    marketing = project / "custom-marketing"
    marketing.mkdir(parents=True)
    (project / "project-manifest.json").write_text(json.dumps({"controller_kind": "umbrella", "subprojects": {"marketing": {"path": "custom-marketing"}}}))
    (marketing / "workstream.json").write_text(json.dumps({"status": "active", "next_action": "review campaign"}))
    restored = helper.active_workspace(tmp_path, str(marketing))
    assert restored["module"] == "marketing"
    assert restored["manifest_path"].endswith("custom-marketing/workstream.json")


def test_subagent_stop_uses_documented_input_and_block_contract() -> None:
    hook = ROOT / ".claude/hooks/subagent_stop.py"
    blocked = subprocess.run(
        ["python3", str(hook)], input=json.dumps({"agent_type": "researcher", "last_assistant_message": ""}),
        text=True, capture_output=True, check=True,
    )
    result = json.loads(blocked.stdout)
    assert result["decision"] == "block"
    assert "continue" not in result
    allowed = subprocess.run(
        ["python3", str(hook)],
        input=json.dumps({"agent_type": "researcher", "last_assistant_message": "Evidence: https://example.com/report"}),
        text=True, capture_output=True, check=True,
    )
    assert "decision" not in json.loads(allowed.stdout)


def test_hook_timeouts_are_seconds_and_bounded():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    for event, entries in settings["hooks"].items():
        for entry in entries:
            for hook in entry["hooks"]:
                assert 1 <= hook["timeout"] <= 60, f"{event}: timeout {hook['timeout']} is not a sane number of seconds"


def test_subagent_stop_does_not_flag_word_choice():
    hook = ROOT / ".claude/hooks/subagent_stop.py"
    out = subprocess.run(["python3", str(hook)],
        input=json.dumps({"agent_type": "researcher",
                          "last_assistant_message": "This is definitely sourced: https://example.com/a and artifacts/evidence.jsonl"}),
        text=True, capture_output=True, check=True)
    assert json.loads(out.stdout) == {}


def test_read_only_and_preauthorized_scripts_are_allowlisted():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    allow = set(settings["permissions"]["allow"])
    for rule in [
        "Bash(python3 scripts/route_workflow.py *)",
        "Bash(python3 scripts/validate_skill_routes.py)",
        "Bash(python3 scripts/run_evals.py *)",
        "Bash(python3 -m pytest *)",
        "Bash(bash scripts/validate_setup.sh)",
        "Bash(python3 scripts/case_economics.py *)",
        "Bash(python3 scripts/strategy_review.py *)",
        "Bash(python3 scripts/serper_fetch.py *)",
        "Bash(python3 scripts/evidence_scout/collect.py *)",
        "Bash(python3 scripts/evidence_scout/discover_market_problems.py *)",
        "Bash(python3 scripts/evidence_scout/plan_customer_feedback.py *)",
        "Bash(python3 scripts/evidence_scout/build_interview_kit.py *)",
    ]:
        assert rule in allow, rule
    assert "Bash(python3 scripts/brand/website_launch.py *)" not in allow
    assert "Bash(python3 scripts/fal_assets.py *)" not in allow


def test_project_subagents_exist_with_restricted_tools():
    import re
    agents = ROOT / ".claude/agents"
    for name, must_have, must_not in [
        ("evidence-researcher", "Bash", "Write"),
        ("competitor-researcher", "Bash", "Write"),
        ("brand-critic", "Read", "Bash"),
    ]:
        text = (agents / f"{name}.md").read_text()
        front = text.split("---")[1]
        assert re.search(rf"^name:\s*{name}\s*$", front, re.M)
        tools = re.search(r"^tools:\s*(.+)$", front, re.M).group(1)
        assert must_have in tools and must_not not in tools, f"{name}: tools={tools}"
    assert not (ROOT / "agent-modes").exists(), "agent-modes/ is superseded by .claude/agents/"


def test_enabled_mcp_servers_are_defined():
    local = ROOT / ".claude/settings.local.json"
    if not local.exists():  # gitignored, per-machine file
        import pytest
        pytest.skip("no settings.local.json on this machine")
    enabled = json.loads(local.read_text()).get("enabledMcpjsonServers", [])
    defined = json.loads((ROOT / ".mcp.json").read_text())["mcpServers"]
    assert [name for name in enabled if name not in defined] == []
    assert "apify" in defined and defined["apify"]["type"] == "http"


def test_subagent_stop_docstring_matches_behavior():
    import ast
    doc = ast.get_docstring(ast.parse((ROOT / ".claude/hooks/subagent_stop.py").read_text()))
    assert "fabricat" not in doc.lower()
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    commands = [h["command"] for groups in settings["hooks"].values()
                for g in groups for h in g["hooks"]]
    assert commands and not [c for c in commands if "|| exit 2" in c]


def _skill_event(skill, args, cwd=None):
    return {"hook_event_name": "PreToolUse", "tool_name": "Skill", "session_id": "s1", "tool_use_id": "t1",
            "cwd": str(cwd or ROOT), "tool_input": {"skill": skill, "args": args}}


def test_bare_single_mode_skill_passes():
    from scripts import enforce_skill_route as hook
    out = hook.check_dispatch(_skill_event("idea-grill", "Pressure test my dog-walking app"))
    hso = out["hookSpecificOutput"]
    assert hso.get("permissionDecision") != "deny"
    assert hso["updatedInput"]["args"] == "Pressure test my dog-walking app"


def test_bare_multi_mode_skill_still_requires_envelope():
    import pytest
    from scripts import enforce_skill_route as hook
    with pytest.raises(ValueError, match="JSON route envelope"):
        hook.check_dispatch(_skill_event("opportunity-risk-designer", "rank my risks"))


def test_bare_single_mode_skill_still_gated(tmp_path, monkeypatch):
    import pytest
    from scripts import enforce_skill_route as hook, route_workflow
    from test_workspace_gates import _write_manifest
    monkeypatch.setattr(route_workflow, "ROOT", tmp_path)
    monkeypatch.setattr(hook, "ROOT", tmp_path)
    _write_manifest(tmp_path, "gated", "not_run", monkeypatch)
    cwd = tmp_path / "projects" / "gated"
    with pytest.raises(ValueError, match="pain-first"):
        hook.check_dispatch(_skill_event("social-digital-marketing-planner", "Create paid social", cwd))
    # An ungated single-mode skill in a gated project is still allowed.
    out = hook.check_dispatch(_skill_event("idea-grill", "Pressure test my idea", cwd))
    assert out["hookSpecificOutput"].get("permissionDecision") != "deny"


def test_single_mode_flag_matches_derived_route_count():
    from scripts import validate_skill_routes
    assert validate_skill_routes.validate() == []


def test_bare_gated_single_mode_skill_outside_workspace_requires_envelope():
    import pytest
    from scripts import enforce_skill_route as hook
    for skill in ("strategy-draft-tournament", "company-operating-system", "social-digital-marketing-planner"):
        with pytest.raises(ValueError, match="JSON route envelope"):
            hook.check_dispatch(_skill_event(skill, "Pick our GTM strategy for the dog-walking venture"))


def test_malformed_json_envelope_is_denied_not_treated_as_text():
    import pytest
    from scripts import enforce_skill_route as hook
    with pytest.raises(ValueError, match="Malformed JSON route envelope"):
        hook.check_dispatch(_skill_event("idea-grill", '{"route": {"request": "x", "project": "foo"'))


# --- Stop hook: delivery claims -------------------------------------------

import sys as _sys
_sys.path.insert(0, str(ROOT / ".claude/hooks"))
import stop_delivery_check as stop_hook  # noqa: E402
import compaction_state  # noqa: E402


def _transcript(tmp_path, text):
    path = tmp_path / "t.jsonl"
    path.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "go"}}) + "\n"
                    + json.dumps({"type": "assistant", "message": {"role": "assistant",
                                  "content": [{"type": "text", "text": text}]}}) + "\n")
    return str(path)


def _case_checkpoint(root, session="s1"):
    case_root = root / "projects/p/business-analysis/cases/c1"
    (case_root / "market_research/pain_points/runs/r1").mkdir(parents=True)
    manifest = case_root / "market_research/manifest.json"
    manifest.write_text("{}")
    compaction_state.write_state(compaction_state.resume_path(root, session), {
        "session_id": session, "active_selection": {"project": "p", "case": "c1"},
        "workspace": {"case_id": "c1", "run_id": "r1", "manifest_path": manifest.relative_to(root).as_posix()}})


def test_stop_hook_ignores_non_delivery_turn(tmp_path):
    _case_checkpoint(tmp_path)
    for text in ("Here is a progress snapshot of the research.", "The case is not yet delivered.",
                 "Research is not complete."):
        event = {"session_id": "s1", "transcript_path": _transcript(tmp_path, text)}
        assert stop_hook.stop_delivery_check(event, tmp_path) == {}


def test_stop_hook_blocks_unvalidated_delivery_claim(tmp_path):
    for name in ("scripts",):
        (tmp_path / name).symlink_to(ROOT / name)
    _case_checkpoint(tmp_path)
    event = {"session_id": "s1", "transcript_path": _transcript(tmp_path, "The case was fully delivered.")}
    out = stop_hook.stop_delivery_check(event, tmp_path)
    assert out["decision"] == "block"
    assert len(out["reason"]) <= 600 + 100 and "progress snapshot" in out["reason"]
    # Same event through the real hook entry point.
    assert run_hook(ROOT / ".claude/hooks/stop_delivery_check.py", tmp_path, event)["decision"] == "block"
    # No loop, and no block when the case cannot be resolved.
    assert stop_hook.stop_delivery_check({**event, "stop_hook_active": True}, tmp_path) == {}
    assert stop_hook.stop_delivery_check({**event, "session_id": "other"}, tmp_path) == {}
    assert stop_hook.stop_delivery_check({**event, "transcript_path": "/nonexistent"}, tmp_path) == {}


def test_stop_hook_registered_without_onfailure():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    entry = settings["hooks"]["Stop"][0]["hooks"][0]
    assert entry["command"].endswith(".claude/hooks/stop_delivery_check.py\"") and entry["timeout"] == 60

