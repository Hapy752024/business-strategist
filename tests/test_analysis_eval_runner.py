import importlib.util
import json
import sys
from pathlib import Path
import importlib.util as import_util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_analysis_evals", ROOT / "scripts/run_analysis_evals.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
blind_spec = import_util.spec_from_file_location("prepare_blinded_eval", ROOT / "scripts/prepare_blinded_eval.py")
blind = import_util.module_from_spec(blind_spec); blind_spec.loader.exec_module(blind)


def test_workflow_manifest_has_frozen_balanced_connected_splits():
    path = ROOT / "evals/workflow-quality/manifest.json"
    manifest = json.loads(path.read_text())
    assert module.validate_manifest(manifest, path.parent) == []
    assert len([x for x in manifest["tasks"] if x["split"] == "development"]) == 8
    assert len([x for x in manifest["tasks"] if x["split"] == "held_out"]) == 4


def test_reviewed_source_input_omits_expectations_and_keys():
    manifest = json.loads((ROOT / "evals/workflow-quality/manifest.json").read_text())
    source = json.loads((ROOT / "evals/voc/live/cases.json").read_text())
    task = next(x for x in manifest["tasks"] if x["kind"] == "reviewed_source")
    result = module.task_input(task, source)
    serialized = json.dumps(result)
    assert "expected_concepts" not in serialized and "must_not_conclude" not in serialized
    assert result["passages"][0]["quote"]


def test_codex_jsonl_events_extract_answer_usage_and_tool_trace():
    raw = "\n".join([
        json.dumps({"type":"item.completed", "item":{"type":"agent_message", "text":"final answer"}}),
        json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"cat snapshot/file", "aggregated_output":"contents"}}),
        json.dumps({"type":"turn.completed", "usage":{"input_tokens":12,"output_tokens":3}}),
    ])
    answer, trace, usage, model = module.parse_runtime_output(raw)
    assert answer == "final answer"
    assert '"cat snapshot/file"' in trace and '"contents"' in trace
    assert usage == {"input_tokens":12,"output_tokens":3}
    assert model is None


def test_runner_writes_separate_trial_records_and_keeps_failures(tmp_path):
    manifest_path = ROOT / "evals/workflow-quality/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    task = {"id":"fixture", "kind":"synthetic", "split":"development", "group":"g", "prompt":"hello",
            "snapshot_paths":["scripts/run_analysis_evals.py"]}
    out = module.run({"source_dataset":manifest["source_dataset"], "tasks":[task]}, manifest_path,
                     [sys.executable, "-c", "import sys; print(open(sys.argv[1]).read())", "{input}"],
                     tmp_path, "current", 2)
    assert len(out["trials"]) == 2 and out["failed_trials"] == 0
    assert out["trials"][0]["input_sha256"] == out["trials"][1]["input_sha256"]
    assert all(Path(row["workspace"], "trial.json").is_file() for row in out["trials"])
    assert all(Path(row["workspace"], "tool-trace.txt").is_file() for row in out["trials"])
    assert all(Path(row["workspace"], "answer.txt").is_file() for row in out["trials"])
    assert out["trials"][0]["skill_hashes"]["scripts/run_analysis_evals.py"]
    assert (Path(out["trials"][0]["workspace"]) / "prompt.txt").is_file()


def test_blinded_pair_outputs_and_coordinator_key_are_separate(tmp_path):
    def make_arm(name, answer):
        root = tmp_path / name; trial = root / "task-r1"; trial.mkdir(parents=True)
        (trial / "answer.txt").write_text(answer)
        (trial / "input.json").write_text('{"request":"same"}')
        (trial / "trial.json").write_text(json.dumps({"task_id":"task", "repeat":1, "arm":name, "split":"development", "status":"ok", "error":None, "workspace":str(trial)}))
        return root
    baseline = make_arm("baseline", "pre-change answer")
    current = make_arm("current", "post-change answer")
    result = blind.prepare(baseline, current, tmp_path / "blind", seed=7)
    review = Path(result["review_directory"])
    coordinator = Path(result["key_directory"])
    assert (review / "outputs/task-r1-A.txt").is_file()
    assert (review / "outputs/task-r1-B.txt").is_file()
    assert (review / "task-inputs/task-r1.json").is_file()
    assert (review / "ratings-template.json").is_file()
    ratings = json.loads((review / "ratings-template.json").read_text())
    assert ratings["reviewer_id"] is None
    assert ratings["ratings"][0]["repeat"] == 1
    assert not (review / "blind-key.json").exists()
    assert (coordinator / "blind-key.json").is_file()
    assert {path.read_text() for path in (review / "outputs").iterdir()} == {"pre-change answer", "post-change answer"}
