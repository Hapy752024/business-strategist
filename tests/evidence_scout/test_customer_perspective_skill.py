#!/usr/bin/env python3
"""Deterministic structural tests for challenge-review customer-perspective mode."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "challenge-review"
MODE = SKILL / "references" / "customer-perspective.md"


class CustomerPerspectiveSkillTests(unittest.TestCase):
    def test_entry_budget_and_resources(self) -> None:
        entry = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(entry.splitlines()), 40)
        self.assertIn("name: challenge-review", entry)
        for relative in (
            "references/customer-perspective.md",
            "references/regional-lenses.md",
            "references/decision-lenses.md",
            "references/customer-evidence-base.md",
            "assets/customer-perspective-review-template.md",
            "evals/evals.json",
        ):
            self.assertTrue((SKILL / relative).is_file(), relative)

    def test_regions_and_safety_rules(self) -> None:
        regions = (SKILL / "references" / "regional-lenses.md").read_text(encoding="utf-8")
        for heading in ("## Europe", "## Germany", "## United States"):
            self.assertIn(heading, regions)
        rules = MODE.read_text(encoding="utf-8").lower()
        for term in ("do not infer personality from nationality", "synthetic customer voice", "cannot predict an individual"):
            self.assertIn(term, rules)

    def test_challenge_and_behavioral_validation(self) -> None:
        protocol = MODE.read_text(encoding="utf-8").lower()
        for term in ("total price", "cancellation", "data and safety", "behavioral validation", "do not scale"):
            self.assertIn(term, protocol)
        for term in ("primary likely buyer", "skeptical near-fit buyer", "evidence ledger", "observed behavior"):
            self.assertIn(term, protocol)

    def test_sources_and_evals(self) -> None:
        evidence = (SKILL / "references" / "customer-evidence-base.md").read_text(encoding="utf-8")
        self.assertIn("European Commission", evidence)
        self.assertIn("German", evidence)
        self.assertIn("US FTC", evidence)
        self.assertIn("## Transfer limits", evidence)
        evals = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len([e for e in evals["evals"] if e.get("mode") == "customer-perspective"]), 6)


if __name__ == "__main__":
    unittest.main()
