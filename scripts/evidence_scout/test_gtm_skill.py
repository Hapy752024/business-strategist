#!/usr/bin/env python3
"""Deterministic structural tests for archetype-gtm-strategist."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "archetype-gtm-strategist"


class GtmSkillTests(unittest.TestCase):
    def test_entry_budget_and_resources(self) -> None:
        entry = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(entry.splitlines()), 30)
        self.assertIn("name: archetype-gtm-strategist", entry)
        for relative in (
            "references/workflow.md",
            "references/archetypes.md",
            "references/regions.md",
            "references/experiments.md",
            "references/evidence-base.md",
            "assets/gtm-strategy-template.md",
            "evals/evals.json",
        ):
            self.assertTrue((SKILL / relative).is_file(), relative)

    def test_archetype_and_region_coverage(self) -> None:
        archetypes = (SKILL / "references" / "archetypes.md").read_text(encoding="utf-8")
        for heading in ("## B2B SaaS", "## B2C SaaS", "## B2C Fintech and Insurtech", "## B2C Professional Services"):
            self.assertIn(heading, archetypes)
        regions = (SKILL / "references" / "regions.md").read_text(encoding="utf-8")
        for heading in ("## Europe", "## United States", "## China"):
            self.assertIn(heading, regions)

    def test_decision_gates_and_partnership_economics(self) -> None:
        workflow = (SKILL / "references" / "workflow.md").read_text(encoding="utf-8").lower()
        for term in ("pass, repeat, pivot, and stop", "value exchange", "attribution", "contribution margin", "one primary"):
            self.assertIn(term, workflow)
        experiments = (SKILL / "references" / "experiments.md").read_text(encoding="utf-8").lower()
        for term in ("activation", "retention", "partnership pilot", "paid channel test", "scale gate"):
            self.assertIn(term, experiments)

    def test_sources_and_evals(self) -> None:
        registry = ROOT / "research" / "topics" / "founder-gtm-playbooks" / "source_registry.csv"
        with registry.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreaterEqual(len(rows), 20)
        self.assertEqual(len({row["source_id"] for row in rows}), len(rows))
        self.assertGreaterEqual(sum(row["region"] == "Europe" for row in rows), 10)
        self.assertGreaterEqual(sum(row["region"] == "China" for row in rows), 2)
        self.assertTrue(all(row["limitations"] for row in rows))
        evals = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(len(evals["evals"]), 6)


if __name__ == "__main__":
    unittest.main()
