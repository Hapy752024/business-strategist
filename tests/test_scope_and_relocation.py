"""Regressions for scope preservation and the projects/ relocation."""
from pathlib import Path
import json
import subprocess
import pytest

from scripts.route_workflow import route_request
from scripts import project_workspace
from scripts.evidence_scout import workspace


@pytest.mark.parametrize("prompt,expected", [
    ("Do not run a competitive landscape. Only find competitors.", "competitor-scout"),
    ("Keep the marketing strategy unchanged. Create a paid social plan.", "social-digital-marketing-planner"),
    ("Leave the marketing strategy intact; create a content calendar.", "social-digital-marketing-planner"),
    ("Don't build a competitive landscape; find competitors.", "competitor-scout"),
    ("Write two ad-copy options", "marketing-strategy-builder"),
    ("Create a logo only; do not make a website", "brand-designer"),
])
def test_scope_routing(prompt, expected):
    assert route_request(prompt)["skill"] == expected


@pytest.mark.parametrize("intent", ["", "standalone-brand"])
def test_unrelated_brand_ignores_active_website(intent):
    packet = route_request("Create a new brand identity for an unrelated business",
                           intent=intent, active_manifest={"active_track": "website"})
    assert packet["skill"] == "brand-designer"
    assert packet["route_id"] == "standalone-brand"


def test_only_continuation_inherits_state():
    active = {"active_track": "website"}
    packet = route_request("continue", active_manifest=active)
    assert packet["route_id"] == "website-build"
    assert packet["skill"] == "brand-website-designer-builder"
    assert route_request("Help me with a different business", active_manifest=active)["ask_question"]


def test_narrow_artifacts_and_explicit_scope():
    packet = route_request("Write two ad copy options")
    assert packet["task_scope"] == "execution"
    assert packet["expected_artifacts"] != ["marketing strategy"]
    assert route_request("Explain our marketing strategy", task_scope="focused")["task_scope"] == "focused"
    assert route_request("Build a marketing strategy")["task_scope"] == "strategy"
    with pytest.raises(ValueError):
        route_request("hello", task_scope="enormous")


def test_distinct_requested_workflows_need_resolution():
    assert route_request("Build a marketing strategy. Create a brand identity.")["ask_question"]
    assert not route_request("Build a marketing strategy. Create a brand identity.", intent="standalone-brand")["ask_question"]


def test_research_default_and_old_root_rejection(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "ROOT", tmp_path)
    root = workspace.create_topic_workspace("Scope test")
    assert root == tmp_path / "projects/research/topics/scope-test"
    assert workspace.create_topic_workspace("Scope test") == root
    assert workspace.find_existing_workspaces()[0]["path"] == str(root)
    with pytest.raises(ValueError, match="relocated"):
        workspace.create_topic_workspace("Old", "research/topics/old")
    assert not (tmp_path / "research").exists()


@pytest.mark.parametrize("slug", ["research", "brand-projects"])
def test_reserved_controller_names(slug):
    with pytest.raises(ValueError, match="reserved"):
        project_workspace.create_project(slug)


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / ".agents/skills/setup-multiharness-project/scripts"


def test_setup_target_dry_run_and_bootstrap(tmp_path):
    target = tmp_path / "target with spaces"
    target.mkdir()
    other = tmp_path / "caller"
    other.mkdir()
    command = ["bash", str(SETUP / "setup.sh"), "bootstrap", "--target", str(target)]
    dry = subprocess.run(command + ["--dry-run"], cwd=other, capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert f"TARGET {target}" in dry.stdout
    assert not list(target.iterdir())
    result = subprocess.run(command, cwd=other, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    instructions = (target / "AGENTS.md").read_text()
    assert "uvicorn" not in instructions and "Spawn review subagents" not in instructions
    before = (target / "AGENTS.md").read_bytes()
    assert subprocess.run(command, cwd=other, capture_output=True).returncode == 0
    assert (target / "AGENTS.md").read_bytes() == before
    assert not list(other.iterdir())
    audit = subprocess.run(["bash", str(SETUP / "setup.sh"), "audit", "--target", str(target)], cwd=other, capture_output=True, text=True)
    assert audit.returncode == 0, audit.stdout + audit.stderr


@pytest.mark.parametrize("script", ["setup.sh", "bootstrap.sh", "audit.sh", "apply.sh"])
def test_setup_rejects_broad_or_missing_target(script, tmp_path):
    for target in ("/", str(tmp_path / "missing")):
        result = subprocess.run(["bash", str(SETUP / script), "--target", target], capture_output=True)
        assert result.returncode == 2


def test_capability_benchmark_allows_consolidation():
    from scripts.benchmark_agentic_process import snapshot
    routes = {"routes": [{"id": route, "skill": "one-brand-skill"} for route in
                         ("standalone-brand", "brand-research", "brand-asset", "app-ui", "website-build")]}
    files = {".agents/skills/one-brand-skill/SKILL.md"}
    values = {"config/workflow-routes.json": json.dumps(routes)}
    assert snapshot(files, lambda path: values.get(path, ""))["contracts"]["brand-capability-routing"]
    routes["routes"].pop()
    values["config/workflow-routes.json"] = json.dumps(routes)
    assert not snapshot(files, lambda path: values.get(path, ""))["contracts"]["brand-capability-routing"]


def test_short_skill_paths_resolve():
    for name in ("marketing-strategy-builder", "social-digital-marketing-planner"):
        folder = ROOT / ".agents/skills" / name
        assert (ROOT / "references/task-scope.md").is_file()
        entry = (folder / "SKILL.md").read_text()
        assert "compatibility: Requires the business-strategist repository" in entry
        assert "repo-root `references/task-scope.md`" in entry
        assert "focused" in entry.lower() and "execution" in entry.lower()
