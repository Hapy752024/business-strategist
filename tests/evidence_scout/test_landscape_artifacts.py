#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class LandscapeArtifactTests(unittest.TestCase):
    def landscape(self, rows, gaps=None):
        complete = []
        for index, row in enumerate(rows):
            social = [{"platform": "unknown", "url": "", "retrieved_at": "2026-08-30T00:00:00Z", "posts_sampled": 0, "metrics_are_public_proxies": True, **observation} for observation in row.get("social_presence", [])]
            complete.append({
                "id": f"entity-{index}", "classification_reason": "fixture evidence", "evidence_quality": "high",
                "inspiration_roles": [], "services": [], **row, "social_presence": social,
            })
        return {"schema_version": "1.0", "brief": {"service": "care scheduling", "job": "schedule staff", "target_segment": "clinics", "buyer": "manager", "geography": "Germany", "price_tier": ""}, "entities": complete, "sources": [], "coverage": {"lanes_checked": ["competitive_market", "similar_company"], "gaps": gaps or [], "retrieved_at": "2026-08-30T00:00:00Z"}}

    def run_builder(self, entities: Path, out: Path, *, check: bool = True):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run(["python3", "scripts/evidence_scout/build_landscape_artifacts.py", "--entities-json", str(entities), "--out-dir", str(out)], check=check, capture_output=True, text=True, env=env)

    def test_builder_keeps_analogs_out_of_competitive_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            entities.write_text(json.dumps(self.landscape([
                {"name": "DirectCo", "url": "https://direct.example", "primary_lane": "competitive_market", "competitive_role": "direct", "verification_status": "verified", "social_presence": [{"status": "not_found_in_checked_sources"}]},
                {"name": "AnalogCo", "url": "https://analog.example", "primary_lane": "similar_company", "competitive_role": "none", "verification_status": "verified", "inspiration_roles": ["website"], "marketing_observation": {"positioning_headline": "Fast care scheduling for clinics"}, "social_presence": [{"status": "not_found_in_checked_sources"}]},
            ])), encoding="utf-8")
            out = root / "out"
            self.run_builder(entities, out)
            matrix = (out / "competitive-market-matrix.md").read_text(encoding="utf-8")
            self.assertIn("DirectCo", matrix)
            self.assertNotIn("AnalogCo", matrix)
            handoff = json.loads((out / "competitive-insight-handoff.json").read_text(encoding="utf-8"))
            self.assertFalse(handoff["approved_for_branding"])
            self.assertTrue(json.loads((out / "quality-gate.json").read_text(encoding="utf-8"))["passed"])

    def test_builder_blocks_unverified_and_placeholder_free_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            entities.write_text(json.dumps(self.landscape([
                {"name": "CandidateCo", "url": "https://candidate.example", "primary_lane": "uncertain", "competitive_role": "unknown", "verification_status": "uncertain"},
            ], ["official page missing"])), encoding="utf-8")
            out = root / "out"
            result = self.run_builder(entities, out, check=False)
            self.assertEqual(result.returncode, 2)
            matrix = (out / "competitive-market-matrix.md").read_text(encoding="utf-8")
            self.assertNotIn("CandidateCo", matrix)
            combined = "\n".join(path.read_text(encoding="utf-8") for path in out.glob("*.md"))
            self.assertNotIn("[analyst to specify", combined)

    def test_builder_rejects_malformed_landscape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            entities.write_text(json.dumps({"entities": [{"name": "Malformed"}]}), encoding="utf-8")
            result = self.run_builder(entities, root / "out", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid entity landscape", result.stderr)

    def test_coverage_gap_blocks_quality_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            entities.write_text(json.dumps(self.landscape([
                {"name": "DirectCo", "url": "https://direct.example", "primary_lane": "competitive_market", "competitive_role": "direct", "verification_status": "verified", "social_presence": [{"status": "not_found_in_checked_sources"}]},
            ], ["Lane B provider failed"])), encoding="utf-8")
            out = root / "out"
            result = self.run_builder(entities, out, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads((out / "quality-gate.json").read_text(encoding="utf-8"))["passed"])

    def test_offer_matrix_uses_canonical_entity_prices_without_marketing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            services = [{"observed_text": "Team plan EUR 49 per month", "price_status": "structured_price_found", "prices": {"currency_amounts": [{"currency": "EUR", "value": 49}]}}]
            entities.write_text(json.dumps(self.landscape([
                {"name": "DirectCo", "url": "https://direct.example", "primary_lane": "competitive_market", "competitive_role": "direct", "verification_status": "verified", "services": services, "social_presence": [{"status": "not_found_in_checked_sources"}]},
            ])), encoding="utf-8")
            out = root / "out"
            self.run_builder(entities, out)
            matrix = json.loads((out / "offer-price-matrix.json").read_text(encoding="utf-8"))
            self.assertEqual(matrix[0]["pricing_status"], "structured_price_found")
            self.assertEqual(matrix[0]["pricing"][0]["currency_amounts"][0]["value"], 49)


if __name__ == "__main__":
    unittest.main()
