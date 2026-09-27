"""An unregistered collection must remain an actionable, nonterminal case."""
from pathlib import Path
from unittest.mock import patch
import sys

from scripts.evidence_scout import build_case_closeout


def test_unregistered_case_reports_bootstrap_work(tmp_path: Path):
    case = tmp_path / "cases" / "sample" / "market_research"
    case.mkdir(parents=True)
    (case / "manifest.json").write_text("{}", encoding="utf-8")
    run = case / "pain_points" / "runs" / "capture"
    run.mkdir(parents=True)
    for name in ("query_plan.json", "summary.json", "evidence.jsonl", "irrelevant.jsonl"):
        (run / name).write_text("{}", encoding="utf-8")
    with patch.object(build_case_closeout, "case_manifest", return_value={}), patch.object(
        build_case_closeout.checks, "validate_collection",
        return_value={"status": "complete", "missing_requirements": []},
    ):
        result = build_case_closeout.build(tmp_path, "sample")
    assert result["outcome"] == "work_in_progress"
    assert result["checks"] == {"collection": "complete", "assignment": "partial", "delivery": "partial"}
    assert result["items"][0]["kind"] == "register_assignment"
    assert result["captured_runs"][0]["collection_status"] == "complete"


def test_closure_flag_fails_on_unfinished_case(tmp_path: Path, monkeypatch, capsys):
    packet = {"case_id": "sample", "checks": {"assignment": "partial"},
              "outcome": "work_in_progress", "closure_status": "in_progress", "items": [], "input_fingerprint": "digest"}
    monkeypatch.setattr(sys, "argv", ["build_case_closeout.py", "--workspace", str(tmp_path),
                                   "--case", "sample", "--require-terminal"])
    with patch.object(build_case_closeout, "build", return_value=packet):
        assert build_case_closeout.main() == 1
    assert '"outcome": "work_in_progress"' in capsys.readouterr().out


def test_closure_flag_rejects_interim_publication_and_targeted_research(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["build_case_closeout.py", "--workspace", str(tmp_path),
                                   "--case", "sample", "--require-terminal"])
    for outcome in ("provisional_plan_published", "more_targeted_research_required"):
        packet = {"case_id": "sample", "checks": {"assignment": "complete", "delivery": "partial"},
                  "outcome": outcome, "closure_status": "interim", "items": [{"blocking": True}],
                  "input_fingerprint": "digest"}
        with patch.object(build_case_closeout, "build", return_value=packet):
            assert build_case_closeout.main() == 1
    packet.update(checks={"assignment": "complete", "delivery": "complete"},
                  closure_status="closed", items=[])
    with patch.object(build_case_closeout, "build", return_value=packet):
        assert build_case_closeout.main() == 0
