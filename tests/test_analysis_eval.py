import json
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_analysis_eval import MANIFEST, summarize, validate


def _pair(task_id="dev-discovery", a=3, b=3):
    manifest = json.loads(MANIFEST.read_text())
    dims = manifest["dimensions"]
    return manifest, {"ratings": [
        {"task_id": task_id, "variant": variant, "critical_failure": False,
         "ratings": {dimension: (a if variant == "A" else b) for dimension in dims},
         "rationale": "Fixture rating."}
        for variant in ("A", "B")
    ]}


def test_empty_evaluation_never_reports_quality_pass():
    manifest = json.loads(MANIFEST.read_text())
    result = summarize({"ratings": []}, manifest)
    assert result["valid"] is False
    assert "overall_quality_pass" not in result


def test_unknown_task_is_rejected():
    manifest, scores = _pair("invented-task")
    result = summarize(scores, manifest, allow_subset=True)
    assert result["valid"] is False
    assert any("unknown evaluation task" in error for error in result["errors"])


def test_subset_is_descriptive_and_not_complete_or_adoption_ready():
    manifest, scores = _pair()
    result = summarize(scores, manifest, allow_subset=True)
    assert result["valid"] is True
    assert result["comparison_complete"] is False
    assert result["evaluation_ready_for_decision"] is False
    assert "overall_quality_pass" not in result


def test_dimension_regression_is_not_compensated_by_other_dimensions():
    manifest, scores = _pair()
    dims = manifest["dimensions"]
    by_variant = {row["variant"]: row for row in scores["ratings"]}
    by_variant["A"]["ratings"].update({dimension: 4 for dimension in dims})
    by_variant["B"]["ratings"].update({dimension: 1 for dimension in dims})
    by_variant["A"]["ratings"]["source_fidelity"] = 1
    by_variant["B"]["ratings"]["source_fidelity"] = 2
    result = summarize(scores, manifest, allow_subset=True)
    assert result["task_outcomes"]["A_wins"] == 0
    assert result["task_outcomes"]["B_wins"] == 0
    assert result["task_outcomes"]["ties"] == 1
    assert result["dimension_outcomes"]["source_fidelity"]["B_better"] == 1


def test_manifest_remains_explicitly_design_only():
    manifest = json.loads(MANIFEST.read_text())
    assert validate(manifest) == []
    assert manifest["status"] == "design_only_packets_and_scores_pending"


def test_reviewed_source_packet_does_not_need_fictional_paired_examples(tmp_path):
    (tmp_path / "packet.json").write_text(json.dumps({"task_id":"source-1", "packet_kind":"reviewed_source",
        "source_locators":["https://source.example/thread#post-2"], "source_sha256":"a" * 64,
        "generation_input":{"question":"What happened?", "passage":"I tried this."}}))
    manifest = {"status":"design_only_packets_and_scores_pending", "split_counts":{"development":1,"held_out":0},
        "tasks":[{"id":"source-1", "group":"source-1", "split":"development", "packet":"packet.json"}],
        "dimensions":["fidelity"], "critical_failures":["fabrication"]}
    assert validate(manifest, tmp_path) == []


def test_saved_rating_requires_hash_bound_outputs_traces_and_blind_review(tmp_path):
    task_id = 'one-task'
    def save(path, value):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, sort_keys=True))
        return hashlib.sha256(target.read_bytes()).hexdigest()
    packet = {'task_id': task_id, 'synthetic_only': True, 'generation_input': {'evidence': 'source'}}
    packet_hash = save('packets/input.json', packet)
    save('packets/key.json', {'task_id': task_id, 'synthetic_only': True})
    save('packets/examples.json', {'task_id': task_id, 'synthetic_only': True})
    manifest = {'status': 'comparison_ready', 'split_counts': {'development': 1, 'held_out': 0},
        'tasks': [{'id': task_id, 'group': 'one', 'split': 'development', 'packet': 'packets/input.json',
                   'review_key': 'packets/key.json', 'paired_examples': 'packets/examples.json'}],
        'dimensions': ['fidelity'], 'critical_failures': ['fabrication'], 'criteria_version': '1',
        'packets_reviewed': True, 'criteria_frozen': True, 'reviewer_calibration': 'complete',
        'adoption_rule': 'No critical failures and no fidelity regression.'}
    artifact_rows = {}
    for variant in ('A', 'B'):
        output_hash = save(f'outputs/{variant}.json', {'variant': variant, 'text': 'fixture output'})
        trace_hash = save(f'traces/{variant}.json', {'calls': []})
        artifact_rows[variant] = {'path': f'outputs/{variant}.json', 'sha256': output_hash,
            'tool_trace_path': f'traces/{variant}.json', 'tool_trace_sha256': trace_hash,
            'source_sha256': packet_hash, 'model_id': 'fixture-model', 'prompt_sha256': 'a' * 64,
            'latency_ms': 1, 'usage': {'input_tokens': 10, 'output_tokens': 5}}
    output_manifest = {'schema_version': 1, 'tasks': [{'task_id': task_id, 'variants': artifact_rows}]}
    output_hash = save('outputs/index.json', output_manifest)
    ratings = [{'task_id': task_id, 'variant': variant, 'critical_failure': False,
                'ratings': {'fidelity': 3}, 'rationale': 'Compared with source.'} for variant in ('A', 'B')]
    review = {'blind': True, 'reviewer_ids': ['reviewer-hash'], 'criteria_version': '1',
              'ratings_sha256': hashlib.sha256(json.dumps(ratings, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}
    review_hash = save('outputs/review.json', review)
    scores = {'ratings': ratings, 'paired_output_manifest_path': 'outputs/index.json',
              'paired_output_manifest_sha256': output_hash, 'review_record_path': 'outputs/review.json',
              'review_record_sha256': review_hash, '_manifest_dir': str(tmp_path)}
    assert validate(manifest, tmp_path) == []
    result = summarize(scores, manifest)
    assert result['evaluation_ready_for_decision'] is True
    scores['paired_output_manifest_sha256'] = '0' * 64
    result = summarize(scores, manifest)
    assert result['evaluation_ready_for_decision'] is False
    assert 'overall_quality_pass' not in result
