#!/usr/bin/env python3
"""Deterministic structural tests for the whitespace matrix scaffolder."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "evidence_scout" / "build_whitespace_matrix.py"

RECORDS = [
    {"source": "reddit", "source_url": "https://reddit.com/r/x/1", "retrieved_at": "2026-08-01", "evidence_type": "pain", "text": "I spend hours reconciling invoices every month", "strength": "weak", "relevance": "relevant", "source_intent": "user_pain"},
    {"source": "reddit", "source_url": "https://reddit.com/r/x/2", "retrieved_at": "2026-08-01", "evidence_type": "pain", "text": "Should I switch accountants?", "strength": "medium", "relevance": "relevant", "comment_intent": "decision_question"},
    {"source": "reddit", "source_url": "https://reddit.com/r/x/3", "retrieved_at": "2026-08-01", "evidence_type": "noise", "text": "spam", "strength": "weak", "relevance": "irrelevant"},
]

COMPETITORS = [
    {"name": "Acme Books", "url": "https://acme.example", "competitor_type_hint": "direct_broker_candidate"},
    {"name": "Ledgerly", "url": "https://ledgerly.example", "competitor_type_hint": "direct_broker_candidate"},
]


def run_script(out_path: Path, evidence: Path, competitors: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--topic", "pet care",
            "--evidence-jsonl", str(evidence),
            "--competitors-json", str(competitors),
            "--out", str(out_path),
        ],
        capture_output=True,
        text=True,
    )


class WhitespaceMatrixTests(unittest.TestCase):
    def test_matrix_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            evidence = base / "evidence.jsonl"
            evidence.write_text("\n".join(json.dumps(r) for r in RECORDS) + "\n", encoding="utf-8")
            competitors = base / "competitors.json"
            competitors.write_text(json.dumps(COMPETITORS), encoding="utf-8")
            out_path = base / "whitespace-matrix.md"

            result = run_script(out_path, evidence, competitors)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["pains"], 2)  # irrelevant record excluded
            self.assertEqual(summary["competitors"], 2)

            matrix = out_path.read_text(encoding="utf-8")
            self.assertIn("| Pain (from evidence) | Strength | Source | Acme Books | Ledgerly |", matrix)
            self.assertIn("P1: I spend hours reconciling invoices every month", matrix)
            self.assertIn("unknown | unknown |", matrix)
            self.assertIn("## Candidate White Spots", matrix)
            self.assertIn("unscored, not unserved", matrix)

    def test_missing_competitors_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            evidence = base / "evidence.jsonl"
            evidence.write_text(json.dumps(RECORDS[0]) + "\n", encoding="utf-8")
            result = run_script(base / "out.md", evidence, base / "missing.json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("no competitors", result.stderr)


if __name__ == "__main__":
    unittest.main()
