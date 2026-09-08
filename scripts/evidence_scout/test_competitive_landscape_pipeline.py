#!/usr/bin/env python3
"""End-to-end offline checks for the three-lane production path."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from discover_competitors import add_candidate, classify_candidate, merge_candidate_maps, query_plan
from collect_social_presence import normalize_entities
from analyze_competitor_marketing import analyze_text
from workspace import create_topic_workspace


ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


class DiscoveryLaneTests(unittest.TestCase):
    def test_cached_snippet_cannot_become_official_service_evidence(self):
        body = {"data": {"metadata": {"title": "Scheduling service"}, "markdown": "A scheduling service plan for small business teams. Get started."}}
        cached = analyze_text("https://example.com", [{"url": "https://example.com", "body": body, "fallback_source": "competitors_json_snippet"}])
        official = analyze_text("https://example.com", [{"url": "https://example.com", "body": body, "retrieval_source": "fixture_official"}])
        self.assertFalse(cached["official_service_evidence"])
        self.assertTrue(official["official_service_evidence"])
    def test_query_sets_are_independent_and_bounded_by_lane(self):
        plan = query_plan("care scheduling", "independent clinics", "", ["France"], ["website"])
        self.assertGreaterEqual(len(plan["competitive_market"]), 4)
        self.assertEqual(len(plan["similar_company"]), 3)
        self.assertEqual(len(plan["capability_reference"]), 1)
        self.assertFalse(any("ANALOG:" in row["query"] or "REFERENCE:" in row["query"] for rows in plan.values() for row in rows))

    def test_cross_lane_domain_merge_preserves_provenance_not_classification(self):
        competitive = {}
        reference = {}
        add_candidate(competitive, url="https://example.com", title="Care scheduling", description="Scheduling service for independent clinics", query="care scheduling competitors", source="test", lane_scope="competitive_market")
        add_candidate(reference, url="https://example.com/design", title="Example design", description="A strong website", query="best company website", source="test", lane_scope="capability_reference", scope_value="website")
        merge_candidate_maps(competitive, reference)
        row = classify_candidate(competitive["example.com"], "care scheduling", "independent clinics")
        self.assertEqual(row["primary_lane"], "uncertain")
        self.assertEqual(row["lane_observations"], ["capability_reference", "competitive_market"])
        schema = json.loads(Path("schemas/competitor.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(row)

    def test_sampled_social_observation_overrides_unverified_link_hint(self):
        entities = [{"name": "ClinicFlow", "url": "https://clinicflow.example.com"}]
        marketing = {"https://clinicflow.example.com": {"social_presence": [{"platform": "youtube", "url": "https://youtube.com/@clinicflow", "status": "unverified"}]}}
        sampled = {"https://clinicflow.example.com": {"social_presence": [{"platform": "youtube", "url": "https://youtube.com/@clinicflow", "status": "verified_active", "posts_sampled": 8, "sample_window": "2026-07-01/2026-08-30", "formats": ["tutorial"], "cadence": "weekly", "cta": ["book demo"]}]}}
        result = normalize_entities(entities, "2026-08-30T00:00:00Z", marketing, sampled)
        observation = result[0]["social_presence"][0]
        self.assertEqual(observation["status"], "verified_active")
        self.assertEqual(observation["formats"], ["tutorial"])
        self.assertEqual(observation["cadence"], "weekly")

    def test_newer_unverified_social_record_does_not_replace_verified_evidence(self):
        url = "https://clinicflow.example.com"
        entities = [{"name": "ClinicFlow", "url": url, "social_presence": [{"platform": "youtube", "url": "https://youtube.com/@clinicflow", "status": "verified_active", "retrieved_at": "2026-08-20T00:00:00Z", "posts_sampled": 4}]}]
        sampled = {url: {"social_presence": [{"platform": "youtube", "url": "https://youtube.com/@clinicflow", "status": "unverified", "retrieved_at": "2026-08-30T00:00:00Z"}]}}
        result = normalize_entities(entities, "2026-08-30T00:00:00Z", {}, sampled)
        self.assertEqual(result[0]["social_presence"][0]["status"], "verified_active")


class LandscapePipelineTests(unittest.TestCase):
    def test_empty_social_observation_file_does_not_claim_sampling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            observations = root / "observations.json"
            out = root / "social.json"
            entities.write_text(json.dumps([{"name": "ClinicFlow", "url": "https://clinicflow.example.com"}]), encoding="utf-8")
            observations.write_text(json.dumps({"entities": [{"url": "https://clinicflow.example.com", "social_presence": []}]}), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/collect_social_presence.py", "--entities-json", str(entities), "--observations-json", str(observations), "--out", str(out)], check=True, capture_output=True, text=True, env=ENV)
            self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["coverage_gaps"])

    def test_invalid_social_observation_does_not_claim_sampling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entities = root / "entities.json"
            observations = root / "observations.json"
            out = root / "social.json"
            entities.write_text(json.dumps([{"name": "ClinicFlow", "url": "https://clinicflow.example.com"}]), encoding="utf-8")
            observations.write_text(json.dumps({"entities": [{"url": "https://clinicflow.example.com", "social_presence": [{}]}]}), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/collect_social_presence.py", "--entities-json", str(entities), "--observations-json", str(observations), "--out", str(out)], check=True, capture_output=True, text=True, env=ENV)
            self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["coverage_gaps"])

    def test_capability_reference_with_only_cta_remains_uncertain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_topic_workspace("onboarding reference", workspace=str(root / "workspace"))
            candidates = root / "competitors.json"
            page_fixture = root / "pages.json"
            marketing_dir = root / "marketing"
            marketing = marketing_dir / "marketing_analysis.json"
            landscape = root / "landscape.json"
            candidates.write_text(json.dumps([{"name": "CTAOnly", "url": "https://ctaonly.example.com", "competitor_type_hint": "uncertain_candidate", "competitive_role_hint": "unknown", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "medium", "sources": [{"source": "test", "query": "onboarding example", "url": "https://ctaonly.example.com", "lane_scope": "capability_reference", "scope_value": "onboarding"}]}]), encoding="utf-8")
            page_fixture.write_text(json.dumps({"https://ctaonly.example.com": [{"url": "https://ctaonly.example.com", "body": {"data": {"metadata": {"title": "Welcome to CTAOnly"}, "markdown": "Welcome to CTAOnly. Book a demo today."}}}]}), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/analyze_competitor_marketing.py", "--topic", "onboarding reference", "--competitors-json", str(candidates), "--fixture-pages-json", str(page_fixture), "--out-dir", str(marketing_dir)], check=True, capture_output=True, text=True, env=ENV)
            self.assertEqual(json.loads(marketing.read_text(encoding="utf-8"))[0]["capability_patterns"], [])
            subprocess.run(["python3", "scripts/evidence_scout/build_entity_landscape.py", "--competitors-json", str(candidates), "--marketing-json", str(marketing), "--service", "care scheduling", "--job", "schedule care", "--target-segment", "small business", "--geography", "Germany", "--workspace", str(workspace), "--out", str(landscape)], check=True, capture_output=True, text=True, env=ENV)
            entity = json.loads(landscape.read_text(encoding="utf-8"))["entities"][0]
            self.assertEqual(entity["verification_status"], "uncertain")
            checkpoint = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))["stages"]["competitive_landscape"]
            self.assertNotEqual(checkpoint["status"], "passed")

    def test_unsampled_social_gap_propagates_to_canonical_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / "competitors.json"
            marketing = root / "marketing.json"
            social = root / "social.json"
            landscape = root / "landscape.json"
            candidates.write_text(json.dumps([{"name": "ClinicFlow", "url": "https://clinicflow.example.com", "competitor_type_hint": "direct_candidate", "competitive_role_hint": "direct", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "strong", "purchase_substitutability": "strong", "sources": [{"source": "test", "query": "care scheduling", "url": "https://clinicflow.example.com", "lane_scope": "competitive_market", "scope_value": "small business"}]}]), encoding="utf-8")
            marketing.write_text(json.dumps([{"url": "https://clinicflow.example.com", "retrieved_at": "2026-08-30T01:00:00Z", "official_service_evidence": True, "detected_audiences": ["small business"], "first_party_source_pages": [{"url": "https://clinicflow.example.com", "retrieval_source": "fixture_official"}], "service_offers": [{"observed_text": "Care scheduling service for small business care teams", "price_status": "not_found"}], "social_presence": [{"platform": "youtube", "url": "https://youtube.com/@clinicflow", "status": "unverified", "retrieved_at": "2026-08-30T01:00:00Z"}]}]), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/collect_social_presence.py", "--entities-json", str(candidates), "--marketing-json", str(marketing), "--out", str(social)], check=True, capture_output=True, text=True, env=ENV)
            subprocess.run(["python3", "scripts/evidence_scout/build_entity_landscape.py", "--competitors-json", str(candidates), "--marketing-json", str(marketing), "--social-json", str(social), "--service", "care scheduling", "--job", "schedule care teams", "--target-segment", "small business", "--geography", "Germany", "--out", str(landscape)], check=True, capture_output=True, text=True, env=ENV)
            gaps = json.loads(landscape.read_text(encoding="utf-8"))["coverage"]["gaps"]
            self.assertTrue(any("Social coverage gap" in gap for gap in gaps))

    def test_builder_keeps_lifecycle_conditional_when_entity_is_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_topic_workspace("care scheduling", workspace=str(root / "workspace"), customer_segment="small business")
            candidates = root / "competitors.json"
            marketing = root / "marketing.json"
            candidates.write_text(json.dumps([
                {"name": "ClinicFlow", "url": "https://clinicflow.example.com", "competitor_type_hint": "direct_candidate", "competitive_role_hint": "direct", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "strong", "purchase_substitutability": "strong", "sources": [{"source": "test", "query": "care scheduling", "url": "https://clinicflow.example.com", "lane_scope": "competitive_market", "scope_value": "small business"}]},
                {"name": "UnknownCo", "url": "https://unknown.example.com", "competitor_type_hint": "uncertain_candidate", "competitive_role_hint": "unknown", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "weak", "purchase_substitutability": "unknown", "sources": [{"source": "test", "query": "care scheduling", "url": "https://unknown.example.com", "lane_scope": "competitive_market", "scope_value": "small business"}]},
            ]), encoding="utf-8")
            marketing.write_text(json.dumps([{"url": "https://clinicflow.example.com", "retrieved_at": "2026-08-30T01:00:00Z", "official_service_evidence": True, "detected_audiences": ["small business"], "first_party_source_pages": [{"url": "https://clinicflow.example.com", "retrieval_source": "fixture_official"}], "service_offers": [{"observed_text": "Care scheduling service for small business care teams", "price_status": "not_found"}]}]), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/build_entity_landscape.py", "--competitors-json", str(candidates), "--marketing-json", str(marketing), "--service", "care scheduling", "--job", "schedule care teams", "--target-segment", "small business", "--geography", "Germany", "--workspace", str(workspace), "--out", str(root / "landscape.json")], check=True, capture_output=True, text=True, env=ENV)
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            checkpoint = manifest["stages"]["competitive_landscape"]
            self.assertEqual(checkpoint["status"], "in_progress")
            self.assertEqual(checkpoint["gate_result"], "conditional_pass")

    def test_production_builder_uses_canonical_classifier_and_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / "competitors.json"
            marketing = root / "marketing.json"
            social = root / "social.json"
            landscape = root / "entity-landscape.json"
            artifacts = root / "artifacts"
            candidates.write_text(json.dumps([
                {
                    "name": "ClinicFlow", "url": "https://clinicflow.example.com", "competitor_type_hint": "direct_candidate", "competitive_role_hint": "direct", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "strong", "job_fit_hint": "explicit", "segment_fit_hint": "explicit", "purchase_substitutability": "strong", "sources": [{"source": "test", "query": "clinic scheduling", "url": "https://clinicflow.example.com", "lane_scope": "competitive_market", "scope_value": "independent clinics"}],
                },
                {
                    "name": "CabinetPlan", "url": "https://cabinetplan.example.com", "competitor_type_hint": "direct_candidate", "competitive_role_hint": "direct", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "medium", "job_fit_hint": "explicit", "segment_fit_hint": "explicit", "purchase_substitutability": "strong", "sources": [{"source": "test", "query": "care scheduling France", "url": "https://cabinetplan.example.com", "lane_scope": "similar_company", "scope_value": "France"}],
                },
                {
                    "name": "FormCraft", "url": "https://formcraft.example.com", "competitor_type_hint": "uncertain_candidate", "competitive_role_hint": "unknown", "first_seen_at": "2026-08-30T00:00:00Z", "evidence_quality": "medium", "job_fit_hint": "unknown", "segment_fit_hint": "unknown", "purchase_substitutability": "unknown", "sources": [{"source": "test", "query": "best onboarding website", "url": "https://formcraft.example.com", "lane_scope": "capability_reference", "scope_value": "onboarding"}],
                },
            ]), encoding="utf-8")
            marketing.write_text(json.dumps([
                {"url": "https://clinicflow.example.com", "retrieved_at": "2026-08-30T01:00:00Z", "official_service_evidence": True, "detected_audiences": ["independent clinics"], "source_pages": [{"url": "https://clinicflow.example.com", "retrieval_source": "fixture_official"}], "first_party_source_pages": [{"url": "https://clinicflow.example.com", "retrieval_source": "fixture_official"}], "service_offers": [{"observed_text": "Care scheduling service to schedule clinic staff", "price_status": "not_found"}], "positioning_headline": "Confident scheduling for independent clinics", "social_presence": []},
                {"url": "https://cabinetplan.example.com", "retrieved_at": "2026-08-30T01:00:00Z", "official_service_evidence": True, "detected_audiences": ["clinics"], "source_pages": [{"url": "https://cabinetplan.example.com", "retrieval_source": "fixture_official"}], "first_party_source_pages": [{"url": "https://cabinetplan.example.com", "retrieval_source": "fixture_official"}], "service_offers": [{"observed_text": "Care scheduling service for clinic teams", "price_status": "not_found"}], "positioning_headline": "Planning for French clinics", "social_presence": []},
                {"url": "https://formcraft.example.com", "retrieved_at": "2026-08-30T01:00:00Z", "official_service_evidence": False, "detected_audiences": [], "source_pages": [{"url": "https://formcraft.example.com", "retrieval_source": "fixture_official"}], "first_party_source_pages": [{"url": "https://formcraft.example.com", "retrieval_source": "fixture_official"}], "service_offers": [], "positioning_headline": "One-step onboarding", "capability_patterns": [{"capability": "onboarding", "observed_pattern": "A one-step guided product tour"}], "social_presence": []},
            ]), encoding="utf-8")
            social.write_text(json.dumps({"entities": [
                {"url": "https://clinicflow.example.com", "social_presence": [{"platform": "linkedin", "url": "https://linkedin.com/company/clinicflow", "status": "verified_active", "retrieved_at": "2026-08-30T01:00:00Z", "posts_sampled": 6, "sample_window": "2026-07-01/2026-08-30", "formats": ["case study"], "cadence": "weekly", "cta": ["book demo"]}]},
                {"url": "https://cabinetplan.example.com", "social_presence": [{"platform": "instagram", "url": "", "status": "not_found_in_checked_sources", "retrieved_at": "2026-08-30T01:00:00Z", "posts_sampled": 0}]},
                {"url": "https://formcraft.example.com", "social_presence": [{"platform": "youtube", "url": "https://youtube.com/@formcraft", "status": "verified_active", "retrieved_at": "2026-08-30T01:00:00Z", "posts_sampled": 5, "formats": ["tutorial"], "cadence": "monthly", "cta": ["try template"]}]},
            ]}), encoding="utf-8")
            subprocess.run([
                "python3", "scripts/evidence_scout/build_entity_landscape.py", "--competitors-json", str(candidates), "--marketing-json", str(marketing), "--social-json", str(social), "--service", "care scheduling", "--job", "schedule clinic staff", "--target-segment", "independent clinics", "--geography", "Germany", "--out", str(landscape),
            ], check=True, capture_output=True, text=True, env=ENV)
            data = json.loads(landscape.read_text(encoding="utf-8"))
            by_name = {row["name"]: row for row in data["entities"]}
            self.assertEqual(by_name["ClinicFlow"]["primary_lane"], "competitive_market")
            self.assertEqual(by_name["CabinetPlan"]["primary_lane"], "similar_company")
            self.assertEqual(by_name["FormCraft"]["primary_lane"], "capability_reference")
            self.assertEqual(by_name["ClinicFlow"]["evidence_quality"], "high")
            subprocess.run([
                "python3", "scripts/evidence_scout/build_landscape_artifacts.py", "--entities-json", str(landscape), "--marketing-json", str(marketing), "--out-dir", str(artifacts),
            ], check=True, capture_output=True, text=True, env=ENV)
            gate = json.loads((artifacts / "quality-gate.json").read_text(encoding="utf-8"))
            self.assertTrue(gate["passed"])
            matrix = (artifacts / "competitive-market-matrix.md").read_text(encoding="utf-8")
            self.assertIn("ClinicFlow", matrix)
            self.assertNotIn("CabinetPlan", matrix)

    def test_full_cli_replay_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            discovery_fixture = root / "discovery-fixture.json"
            page_fixture = root / "page-fixture.json"
            social_fixture = root / "social-fixture.json"
            discovery_dir = root / "discovery"
            marketing_dir = root / "marketing"
            social_out = root / "social.json"
            landscape = root / "landscape.json"
            artifacts = root / "artifacts"
            discovery_fixture.write_text(json.dumps({
                "competitive_market": [{"url": "https://clinicflow.example.com", "title": "Care scheduling software for small business", "description": "Service plan for small business teams"}],
                "similar_company": [{"url": "https://cabinetplan.example.com", "title": "Care scheduling software France", "description": "Service plan for small business teams", "scope_value": "France"}],
                "capability_reference": [{"url": "https://formcraft.example.com", "title": "Onboarding design", "description": "Distinctive onboarding examples", "scope_value": "onboarding"}],
            }), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/discover_competitors.py", "--topic", "care scheduling", "--customer-segment", "small business", "--analog-market", "France", "--reference-capability", "onboarding", "--fixture-results-json", str(discovery_fixture), "--out-dir", str(discovery_dir)], check=True, capture_output=True, text=True, env=ENV)
            urls = ["https://clinicflow.example.com", "https://cabinetplan.example.com", "https://formcraft.example.com"]
            page_fixture.write_text(json.dumps({url: [{"url": url, "body": {"data": {"metadata": {"title": "Care scheduling service for small business" if "formcraft" not in url else "One-step onboarding"}, "markdown": "Care scheduling service plan for small business teams. Get started." if "formcraft" not in url else "A crisp onboarding pattern and product tour."}}}] for url in urls}), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/analyze_competitor_marketing.py", "--topic", "care scheduling", "--competitors-json", str(discovery_dir / "competitors.json"), "--fixture-pages-json", str(page_fixture), "--out-dir", str(marketing_dir)], check=True, capture_output=True, text=True, env=ENV)
            social_fixture.write_text(json.dumps({"entities": [{"url": url, "social_presence": [{"platform": "linkedin", "url": "", "status": "not_found_in_checked_sources", "retrieved_at": "2026-08-30T00:00:00Z", "posts_sampled": 0}]} for url in urls]}), encoding="utf-8")
            subprocess.run(["python3", "scripts/evidence_scout/collect_social_presence.py", "--entities-json", str(discovery_dir / "competitors.json"), "--marketing-json", str(marketing_dir / "marketing_analysis.json"), "--observations-json", str(social_fixture), "--out", str(social_out)], check=True, capture_output=True, text=True, env=ENV)
            subprocess.run(["python3", "scripts/evidence_scout/build_entity_landscape.py", "--competitors-json", str(discovery_dir / "competitors.json"), "--discovery-summary-json", str(discovery_dir / "summary.json"), "--marketing-json", str(marketing_dir / "marketing_analysis.json"), "--social-json", str(social_out), "--service", "care scheduling", "--job", "schedule care teams", "--target-segment", "small business", "--geography", "Germany", "--out", str(landscape)], check=True, capture_output=True, text=True, env=ENV)
            subprocess.run(["python3", "scripts/evidence_scout/build_landscape_artifacts.py", "--entities-json", str(landscape), "--marketing-json", str(marketing_dir / "marketing_analysis.json"), "--out-dir", str(artifacts)], check=True, capture_output=True, text=True, env=ENV)
            self.assertTrue(json.loads((artifacts / "quality-gate.json").read_text(encoding="utf-8"))["passed"])


if __name__ == "__main__":
    unittest.main()
