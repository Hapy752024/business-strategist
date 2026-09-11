import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lifecycle_hooks_are_project_anchored_and_precompact_runs_nested(tmp_path):
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    for event in ("PreCompact", "PostCompact", "SubagentStop"):
        command = settings["hooks"][event][0]["hooks"][0]["command"]
        assert "$CLAUDE_PROJECT_DIR/.claude/hooks/" in command

    fixture_root = tmp_path / "business-strategist"
    (fixture_root / ".claude/hooks").mkdir(parents=True)
    shutil.copy2(ROOT / ".claude/hooks/precompact.py", fixture_root / ".claude/hooks/precompact.py")
    nested = fixture_root / "projects" / "example" / "web-site"
    nested.mkdir(parents=True)
    topic = fixture_root / "projects" / "resume-test" / "market_research"
    topic.mkdir(parents=True)
    (topic / "manifest.json").write_text(json.dumps({"current_stage": "synthesis", "next_action": "review evidence"}))
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(fixture_root)
    command = settings["hooks"]["PreCompact"][0]["hooks"][0]["command"]
    completed = subprocess.run(
        command, shell=True, cwd=nested, env=env, input="{}", text=True,
        capture_output=True, timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["continue"] is True
    state = json.loads((fixture_root / ".claude/plans/resume.json").read_text())
    assert state["active_workspaces"][0]["slug"] == "resume-test"
    assert state["active_workspaces"][0]["current_stage"] == "synthesis"


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
