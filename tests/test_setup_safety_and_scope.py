"""Adversarial setup safety and outcome-first routing regressions."""
import json
import os
import subprocess
import tomllib
from pathlib import Path

import pytest

from scripts.route_workflow import route_request

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/setup-multiharness-project/scripts"


def run(target, *args, entry="setup.sh"):
    return subprocess.run(["bash", str(SCRIPTS / entry), "--target", str(target), *args],
                          cwd=target, text=True, capture_output=True, timeout=15)


def test_dry_run_never_executes_destination_code(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Existing project\n")
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {}}')
    (tmp_path / "scripts/sync-mcp-config.py").write_text(
        "from pathlib import Path\nPath('EXECUTED').write_text('bad')\n")
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run(tmp_path, "--dry-run")
    after = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("options", [[], ["--harness", "codex", "--mcp"]])
def test_bootstrap_does_not_follow_scripts_symlink(tmp_path, options):
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    target.mkdir(); outside.mkdir()
    (target / "scripts").symlink_to(outside, target_is_directory=True)
    result = run(target, "bootstrap", *options)
    assert result.returncode != 0
    assert not list(outside.iterdir())
    assert not (target / "AGENTS.md").exists(), "preflight must precede all mutation"


def test_minimal_bootstrap_has_no_integrations(tmp_path):
    result = run(tmp_path, "bootstrap")
    assert result.returncode == 0, result.stdout + result.stderr
    assert {p.name for p in tmp_path.iterdir()} == {"AGENTS.md"}
    assert run(tmp_path, "audit").returncode == 0


@pytest.mark.parametrize("prompt", [
    "Build a full marketing strategy including paid social and a content calendar",
    "Develop a comprehensive marketing strategy with ad copy examples",
    "Create a social media strategy including a content calendar",
])
def test_strategy_outcome_beats_execution_components(prompt):
    packet = route_request(prompt)
    assert packet["task_scope"] == "strategy"
    assert not packet["ask_question"]


@pytest.mark.parametrize("joiner", [". ", " and ", "; ", ", then ", "\n"])
def test_independent_requests_are_punctuation_independent(joiner):
    packet = route_request("Build a marketing strategy" + joiner + "create a brand identity")
    assert packet["ask_question"]


@pytest.mark.parametrize("prompt", [
    "Create a marketing strategy. Include paid social.",
    "Create a marketing strategy and include paid social.",
    "Build a full marketing strategy including paid social and a content calendar.",
])
def test_strategy_components_are_not_separate_workflows(prompt):
    packet = route_request(prompt)
    assert packet["skill"] == "marketing-strategy-builder"
    assert packet["task_scope"] == "strategy"
    assert not packet["ask_question"]


@pytest.mark.parametrize("entry", ["setup.sh", "bootstrap.sh", "audit.sh", "apply.sh"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_no_entrypoint_executes_target_python(tmp_path, entry, dry_run, monkeypatch):
    (tmp_path / "AGENTS.md").write_text("# Existing project\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {}}')
    source = "from pathlib import Path\nPath('EXECUTED').write_text('bad')\n"
    for relative in ("scripts/sync-mcp-config.py", "json.py", "sitecustomize.py"):
        (tmp_path / relative).write_text(source)
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    result = run(tmp_path, "--harness", "codex", "--mcp", *(["--dry-run"] if dry_run else []), entry=entry)
    assert result.returncode in (0, 1), result.stdout + result.stderr
    assert not (tmp_path / "EXECUTED").exists()
    assert not (tmp_path / "__pycache__").exists()
    assert (tmp_path / ".codex").exists() == (not dry_run and entry != "audit.sh")


@pytest.mark.parametrize("relative,is_dir", [
    ("scripts", True), (".claude", True), (".agents", True), (".codex", True),
    ("AGENTS.md", False), (".mcp.json", False), (".gitignore", False),
    ("opencode.json", False), (".codex/config.toml", False),
])
@pytest.mark.parametrize("dangling", [False, True])
def test_all_linked_destinations_fail_before_mutation(tmp_path, relative, is_dir, dangling):
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    target.mkdir(); outside.mkdir()
    destination = outside / "destination"
    if not dangling:
        if is_dir:
            destination.mkdir()
        else:
            destination.write_text("keep")
    link = target / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(destination, target_is_directory=is_dir)
    for entry in ("bootstrap.sh", "apply.sh", "audit.sh"):
        result = run(target, "--harness", "claude", "--harness", "codex", "--harness", "opencode", "--mcp", entry=entry)
        assert result.returncode == 2, result.stdout + result.stderr
    assert link.is_symlink()
    assert not (outside / "sync-mcp-config.py").exists()
    if not dangling and not is_dir:
        assert destination.read_text() == "keep"
    assert set(p.relative_to(target) for p in target.rglob("*") if p.is_symlink() or p.is_file()) == {Path(relative)}


@pytest.mark.parametrize("harness", ["claude", "codex", "opencode"])
def test_harnesses_are_independent_opt_ins(tmp_path, harness):
    result = run(tmp_path, "bootstrap", "--harness", harness)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "CLAUDE.md").exists() == (harness == "claude")
    assert (tmp_path / ".codex").exists() == (harness == "codex")
    assert (tmp_path / "opencode.json").exists() == (harness == "opencode")
    assert not (tmp_path / ".mcp.json").exists()
    assert not (tmp_path / "scripts").exists()
    if harness == "claude":
        assert os.readlink(tmp_path / ".claude/skills") == "../.agents/skills"
    assert run(tmp_path, "audit").returncode == 0


def test_mcp_rendering_is_trusted_and_preserves_other_settings(tmp_path):
    server_name = 'a.name"quoted'
    config = {"mcpServers": {server_name: {"command": 'C:\\tools\\runner', "args": ['a\nb'], "env": {"odd.key": 'quoted"value'}}}}
    (tmp_path / ".mcp.json").write_text(json.dumps(config))
    (tmp_path / "opencode.json").write_text('{"theme": "keep"}')
    result = run(tmp_path, "bootstrap", "--harness", "codex", "--harness", "opencode", "--mcp")
    assert result.returncode == 0, result.stdout + result.stderr
    parsed = tomllib.loads((tmp_path / ".codex/config.toml").read_text())
    assert parsed["mcp_servers"][server_name] == config["mcpServers"][server_name]
    assert json.loads((tmp_path / "opencode.json").read_text())["theme"] == "keep"
    assert not (tmp_path / "scripts").exists()
    assert run(tmp_path, "audit").returncode == 0


def test_invalid_config_has_no_partial_bootstrap(tmp_path):
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {"remote": {"url": "https://example.invalid"}}}')
    result = run(tmp_path, "bootstrap", "--mcp", "--harness", "codex")
    assert result.returncode == 2
    assert {p.name for p in tmp_path.iterdir()} == {".mcp.json"}


def test_explicit_scope_is_authoritative():
    packet = route_request("Build a full marketing strategy including paid social", task_scope="focused")
    assert packet["task_scope"] == "focused"
