#!/usr/bin/env python3
"""Deterministic tests for topic workspaces and credential routing."""

from __future__ import annotations

import json
import os
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
    def test_scaffold_and_manifest_update(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = create_topic_workspace("Accounting document SaaS", temporary, "small accounting firms")
            expected = [
                "manifest.json",
                "README.md",
                "intake/startup-thesis.md",
                "canvases/business-model-canvas.md",
                "canvases/value-proposition-small-accounting-firms.md",
                "market-discovery/runs",
            ]
            for relative in expected:
                self.assertTrue((workspace / relative).exists(), relative)
            update_stage(
                workspace,
                "evidence_collection",
                status="passed",
                gate_result="conditional_pass",
                artifacts=[workspace / "README.md"],
                open_gaps=["payment evidence missing"],
                next_action="Run interviews",
            )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["current_stage"], "evidence_collection")
            self.assertEqual(manifest["stages"]["evidence_collection"]["gate_result"], "conditional_pass")
            self.assertIn("README.md", manifest["artifacts"])
            self.assertIn("market_discovery", manifest["stages"])

    def test_explicit_output_preserves_compatibility(self) -> None:
        run_dir, workspace = resolve_run_dir(
            topic="Example",
            workspace_arg="",
            out_dir="/tmp/explicit-evidence-output",
            legacy_output=False,
            workspace_subdir="evidence/runs",
            legacy_subdir="runs",
        )
        self.assertEqual(run_dir, Path("/tmp/explicit-evidence-output"))
        self.assertIsNone(workspace)

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
