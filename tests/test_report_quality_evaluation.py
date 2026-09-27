import hashlib
import json

import pytest

from scripts.evidence_scout.score_report_review import score


def write(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True) + "\n")


def test_planted_wrong_claim_blocks_evaluator_fitness(tmp_path):
    gold = tmp_path / "gold.json"
    assessment = tmp_path / "assessment.json"
    write(gold, {"items": [
        {"id": "wrong-role", "expected": "unsupported", "material": True, "planted_error": True},
        {"id": "firsthand", "expected": "supported", "material": True, "planted_error": False}]})
    bound = hashlib.sha256(gold.read_bytes()).hexdigest()
    write(assessment, {"reviewer": "Independent reviewer", "gold_sha256": bound, "items": [
        {"id": "wrong-role", "observed": "supported", "rationale": "Incorrectly accepted creator as customer."},
        {"id": "firsthand", "observed": "supported", "rationale": "Original passage reports the author's own behavior."}]})
    result = score(gold, assessment)
    assert result["planted_false_accepts"] == ["wrong-role"]
    assert result["evaluator_ready_for_live_scoring"] is False
    packet = json.loads(assessment.read_text())
    packet["items"][0]["observed"] = "unsupported"
    write(assessment, packet)
    assert score(gold, assessment)["evaluator_ready_for_live_scoring"] is True
    packet["gold_sha256"] = "0" * 64
    write(assessment, packet)
    with pytest.raises(ValueError, match="not bound"):
        score(gold, assessment)
