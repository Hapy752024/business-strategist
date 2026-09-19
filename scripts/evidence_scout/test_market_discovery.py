#!/usr/bin/env python3
"""Deterministic tests for the market-problem discovery artifact contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import collect  # noqa: E402
import discover_market_problems as discovery  # noqa: E402


class MarketDiscoveryTests(unittest.TestCase):
    def test_discovery_query_plan_is_problem_first(self) -> None:
        queries = collect.query_plan("pet care", "", geo="US", language="en", research_mode="discovery")
        self.assertEqual(queries[0], "pet care problems")
        self.assertTrue(any("workaround" in query for query in queries[:7]))
        self.assertTrue(any("worked well" in query or "satisfied" in query or "successful" in query for query in queries[:7]))
        self.assertNotIn("best way to pet care", queries)

    def test_discovery_artifacts_are_market_generic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            args = argparse.Namespace(
                topic="pet care",
                customer_segment="",
                problem_keywords="",
                workaround_keywords="",
                geo="US",
                language="en",
                research_mode="discovery",
            )
            collect.write_assumptions(run_dir, args, ["pet care problems"])
            collect.write_user_review_plan(run_dir, args, [], [])
            assumptions = (run_dir / "assumptions.md").read_text(encoding="utf-8")
            review_plan = (run_dir / "user_review_plan.md").read_text(encoding="utf-8")
            self.assertIn("market scope", assumptions)
            self.assertIn("Candidate [X]", review_plan)
            self.assertNotIn("PKV", assumptions)
            self.assertNotIn("insurance advisor", review_plan)

    def test_scaffold_and_finalize_update_market_discovery_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            start_args = argparse.Namespace(
                topic="pet care",
                focus="I wonder whether owners struggle with care coordination",
                problem_keywords="",
                workaround_keywords="",
                providers="default",
                days=30,
                limit=20,
                geo="US",
                language="en",
                workspace=str(workspace),
                out_dir="",
                legacy_output=False,
                collect=False,
            )
            self.assertEqual(discovery.start_discovery(start_args), 0)
            workspace = workspace / "business-analysis"
            runs = list((workspace / "market_research" / "market_discovery" / "runs").iterdir())
            self.assertEqual(len(runs), 1)
            run_dir = runs[0]
            self.assertTrue((run_dir / "research_plan.md").exists())
            self.assertTrue((run_dir / "market-discovery-report.md").exists())

            report = "\n".join(
                [
                    "# Market Problem Discovery — pet care",
                    "## Executive Summary\nOne candidate warrants a focused test.",
                    "## Scope and Source Coverage\nUS English public sources.\n- Reachability bias: Reddit-heavy coverage; blind spots: medium.",
                    "## Candidate Problem-Segment Pockets\nPet owners coordinating care.",
                    "## Detailed Findings\nRepeated coordination complaints appear in a source sample.",
                    "## Cross-Cutting Patterns\nManual messages and spreadsheets recur.",
                    "## Counter-Evidence and Coverage Gaps\nNo payment signal yet.",
                    "## Questions for Your Decision\nChoose whether to validate the candidate.",
                    "## Recommended Next Investigations\nInterview recent pet-care coordinators.",
                    "## Handoff\nUse Idea Grill only after user selection.",
                    "",
                ]
            )
            (run_dir / "market-discovery-report.md").write_text(report, encoding="utf-8")
            evidence_dir = run_dir / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "summary.json").write_text(
                json.dumps(
                    {
                        "record_count": 3,
                        "providers": {"reddit": {"status": "ok", "record_count": 3}},
                        "needs_user_attention": [],
                        "quality_flags": [],
                    }
                ),
                encoding="utf-8",
            )
            (evidence_dir / "report.md").write_text("# Evidence\n", encoding="utf-8")
            (evidence_dir / "evidence.jsonl").write_text("{}\n", encoding="utf-8")

            finalize_args = argparse.Namespace(run_dir=str(run_dir), candidate_count=1)
            with self.assertRaisesRegex(ValueError, "research pack required"):
                discovery.finalize_discovery(finalize_args)
            pack = run_dir / "customer-feedback"
            pack.mkdir()
            (pack / "evidence.jsonl").write_text("")
            (pack / "source-review.json").write_text(json.dumps({"evidence_sha256": hashlib.sha256(b"").hexdigest(), "target_segment": "unresolved discovery", "reviews": []}))
            (pack / "customer-feedback-coverage.json").write_text(json.dumps({"status": "insufficient_evidence", "synthesis_allowed": False, "coverage_status": "partial", "topic_led_voc": {"accepted_evidence_ids": []}, "source_matrix": []}))
            (pack / "customer-voc-synthesis.json").write_text(json.dumps({"schema_version": 2, "status": "insufficient_evidence", "topic_led_evidence_ids": [], "entity_led_evidence_ids": [], "customer_needs": [], "solution_requirements": [], "codebook": {"version": 1, "codes": []}, "next_investigations": [{"question": "Where are recent customer accounts?", "method": "local source discovery", "reason": "No reviewed voice", "decision_change": "Whether candidate formation is possible"}]}))
            finalize_args.candidate_count = 0
            self.assertEqual(discovery.finalize_discovery(finalize_args), 0)
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            manifest = json.loads((workspace / "market_research" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "complete")
            self.assertEqual(summary["gate_result"], "conditional_pass")
            self.assertEqual(manifest["current_stage"], "market_discovery")
            self.assertEqual(manifest["stages"]["market_discovery"]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
