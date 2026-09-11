#!/usr/bin/env python3
"""Deterministic tests for topic workspaces and credential routing."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
VALIDATORS = HERE.parent / "validate_apis"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(VALIDATORS))

from common import get_secret  # noqa: E402
from workspace import create_topic_workspace, resolve_run_dir, update_stage  # noqa: E402


class WorkspaceTests(unittest.TestCase):
    def test_resume_preserves_reader_document_state_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = create_topic_workspace("Repair service", temporary, "local homeowners")
            readme = workspace / "README.md"
            for target in re.findall(r"\]\(([^)]+)\)", readme.read_text()):
                self.assertTrue((workspace / target).exists(), target)
            self.assertEqual([p.name for p in workspace.glob("*.md")], ["README.md"])
            readme.write_text("# Current decision\nTest quotes before launch.\n")
            evidence = workspace / "market_research" / "pain_points" / "frozen.jsonl"
            evidence.write_bytes(b'{"evidence_id":"fixture"}\n')
            protected = [readme, evidence, workspace / "market_research" / "manifest.json"]
            before = {p: p.read_bytes() for p in protected}
            create_topic_workspace("Repair service", temporary, "local homeowners")
            self.assertEqual(before, {p: p.read_bytes() for p in protected})

    def test_scaffold_and_manifest_update(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = create_topic_workspace("Accounting document SaaS", temporary, "small accounting firms")
            expected = [
                "market_research/manifest.json",
                "README.md",
                "strategy/intake/startup-thesis.md",
                "market_research/deep_dives",
                "market_research/customer_segments",
                "market_research/customer_journey",
                "market_research/pain_points/runs",
                "market_research/solution_alternatives/runs",
                "strategy/canvases/business-model-canvas.md",
                "strategy/canvases/value-proposition-small-accounting-firms.md",
                "market_research/market_discovery/runs",
            ]
            for relative in expected:
                self.assertTrue((workspace / relative).exists(), relative)
            readme = (workspace / "README.md").read_text(encoding="utf-8")
            thesis = (workspace / "strategy" / "intake" / "startup-thesis.md").read_text(encoding="utf-8")
            self.assertIn("Current recommendation", readme)
            self.assertIn("Acquisition and relationship feasibility", readme)
            self.assertIn("pain-first", readme)
            self.assertIn("Founder decision context", thesis)
            update_stage(
                workspace,
                "evidence_collection",
                status="passed",
                gate_result="conditional_pass",
                artifacts=[workspace / "README.md"],
                open_gaps=["payment evidence missing"],
                next_action="Run interviews",
            )
            manifest = json.loads((workspace / "market_research" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["current_stage"], "evidence_collection")
            self.assertEqual(manifest["stages"]["evidence_collection"]["gate_result"], "conditional_pass")
            self.assertIn("README.md", manifest["artifacts"])
            self.assertIn("market_discovery", manifest["stages"])
            self.assertEqual(manifest["manifest_revision"], 2)

    def test_passed_stage_rejects_missing_artifacts_but_preserves_explicit_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = create_topic_workspace("Example", temporary)
            with self.assertRaisesRegex(ValueError, "does not exist"):
                update_stage(
                    workspace, "evidence_collection", status="passed", gate_result="pass",
                    artifacts=[workspace / "missing.md"],
                )
            external = Path(temporary).parent / "outside.md"
            external.write_text("external", encoding="utf-8")
            update_stage(
                workspace, "evidence_collection", status="passed", gate_result="pass",
                artifacts=[external],
            )

    def test_explicit_output_preserves_compatibility(self) -> None:
        run_dir, workspace = resolve_run_dir(
            topic="Example",
            workspace_arg="",
            out_dir="/tmp/explicit-evidence-output",
            legacy_output=False,
            workspace_subdir="market_research/pain_points/runs",
        )
        self.assertEqual(run_dir, Path("/tmp/explicit-evidence-output"))
        self.assertIsNone(workspace)

    def test_legacy_output_layout_removed(self) -> None:
        with self.assertRaisesRegex(ValueError, "legacy-output layout removed"):
            resolve_run_dir(
                topic="Example",
                workspace_arg="",
                out_dir="",
                legacy_output=True,
                workspace_subdir="market_research/pain_points/runs",
            )

    def test_hginvestor_firecrawl_key_is_canonical(self) -> None:
        previous_hg = os.environ.get("FIRECRAWL_API_KEY_HGINVESTOR")
        previous_generic = os.environ.get("FIRECRAWL_API_KEY")
        try:
            os.environ["FIRECRAWL_API_KEY_HGINVESTOR"] = "expected-key"
            os.environ["FIRECRAWL_API_KEY"] = "wrong-account"
            name, value = get_secret("FIRECRAWL_API_KEY")
            self.assertEqual(name, "FIRECRAWL_API_KEY_HGINVESTOR")
            self.assertEqual(value, "expected-key")
        finally:
            if previous_hg is None:
                os.environ.pop("FIRECRAWL_API_KEY_HGINVESTOR", None)
            else:
                os.environ["FIRECRAWL_API_KEY_HGINVESTOR"] = previous_hg
            if previous_generic is None:
                os.environ.pop("FIRECRAWL_API_KEY", None)
            else:
                os.environ["FIRECRAWL_API_KEY"] = previous_generic


if __name__ == "__main__":
    unittest.main()
