#!/usr/bin/env python3
"""Deterministic structural tests for the interview-bridge kit generator."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "evidence_scout" / "build_interview_kit.py"

RECORDS = [
    {"source": "reddit", "source_url": "https://reddit.com/r/x/1", "retrieved_at": "2026-08-01", "evidence_type": "pain", "text": "I spend hours reconciling invoices every month", "strength": "weak", "relevance": "relevant", "source_intent": "user_pain"},
    {"source": "reddit", "source_url": "https://reddit.com/r/x/2", "retrieved_at": "2026-08-01", "evidence_type": "pain", "text": "Should I switch accountants?", "strength": "medium", "relevance": "relevant", "comment_intent": "decision_question"},
    {"source": "youtube", "source_url": "https://youtube.com/watch?v=3", "retrieved_at": "2026-08-01", "evidence_type": "workaround", "text": "I built a spreadsheet for this", "strength": "strong", "relevance": "relevant"},
    {"source": "reddit", "source_url": "https://reddit.com/r/x/4", "retrieved_at": "2026-08-01", "evidence_type": "noise", "text": "spam", "strength": "weak", "relevance": "irrelevant"},
]


def run_kit(run_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--run-dir", str(run_dir)],
        capture_output=True,
        text=True,
    )


class InterviewKitTests(unittest.TestCase):
    def _write_run(self, run_dir: Path, nested: bool = False) -> Path:
        target = run_dir / "evidence" if nested else run_dir
        target.mkdir(parents=True, exist_ok=True)
        (target / "evidence.jsonl").write_text(
            "\n".join(json.dumps({**record, "source_role": "community_context" if record["source"] == "reddit" else "creator_statement"}) for record in RECORDS) + "\n", encoding="utf-8"
        )
        (run_dir / "summary.json").write_text(
            json.dumps({"topic": "invoice reconciliation", "customer_segment": "owner-managed businesses"}), encoding="utf-8"
        )
        from scripts.evidence_scout.build_claim_ledger import stable_id
        reviews = []
        for index, record in enumerate(RECORDS):
            reviews.append({
                "evidence_id": stable_id(record), "source_url": record["source_url"],
                "status": "rejected" if index == 3 else "accepted",
                "reviewed_segment": "owner-managed businesses", "segment_relation": "target",
                "journey_stage": "invoice reconciliation",
                "relevance_rationale": "Business invoice incident" if index != 3 else "Unrelated spam",
                "voice": "customer" if index < 2 else "operator",
                "firsthand": index < 2,
                "author_relationship": "firsthand_customer" if index < 2 else "operator_or_supplier",
            })
        (run_dir / "source-review.json").write_text(json.dumps({
            "evidence_sha256": hashlib.sha256((target / "evidence.jsonl").read_bytes()).hexdigest(),
            "target_segment": "owner-managed businesses", "reviews": reviews,
        }))
        return run_dir

    def test_generates_kit_from_weak_medium_items(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self._write_run(Path(temporary))
            result = run_kit(run_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = json.loads(result.stdout)
            # operator voice and irrelevant records are excluded from tracing
            self.assertEqual(out["items_traced"], 2)

            guide = (run_dir / "interview" / "interview-guide.md").read_text(encoding="utf-8")
            self.assertIn("### E1", guide)
            self.assertIn("### E2", guide)
            self.assertIn("reconciling invoices", guide)
            self.assertNotIn("spreadsheet", guide)

            screener = (run_dir / "interview" / "interview-screener.md").read_text(encoding="utf-8")
            self.assertIn("https://reddit.com/r/x/1", screener)
            self.assertIn("Disqualify", screener)

            tracker = (run_dir / "interview" / "interview-tracker.md").read_text(encoding="utf-8")
            self.assertIn("| E1 | 0 | 0 | open |", tracker)

    def test_discovery_run_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self._write_run(Path(temporary), nested=True)
            result = run_kit(run_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((run_dir / "interview" / "interview-guide.md").exists())

    def test_empty_run_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            result = run_kit(run_dir)
            self.assertEqual(result.returncode, 1)
            self.assertIn("no evidence records", result.stderr)

    def test_skill_structure(self) -> None:
        skill = ROOT / ".agents" / "skills" / "interview-bridge"
        entry = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(entry.splitlines()), 30)
        self.assertIn("name: interview-bridge", entry)
        self.assertTrue((skill / "references" / "workflow.md").is_file())
        self.assertTrue((skill / "evals" / "evals.json").is_file())


if __name__ == "__main__":
    unittest.main()
