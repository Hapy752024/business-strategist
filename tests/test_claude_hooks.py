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
