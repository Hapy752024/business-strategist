#!/usr/bin/env python3
"""Offline contract tests for the business-specific three-lane model."""

import unittest

from entity_landscape import classify_entity, legacy_hint, normalize_evidence_quality, normalize_social_presence, stable_entity_id


class EntityLandscapeTests(unittest.TestCase):
    def test_same_offer_segment_market_is_competitive(self):
        result = classify_entity(
            offer_job_overlap="strong", target_segment_overlap="strong", buyer_overlap="strong",
            geography_overlap="strong", purchase_substitutability="strong", official_service_evidence=True,
        )
        self.assertEqual(result["primary_lane"], "competitive_market")
        self.assertEqual(result["competitive_role"], "direct")

    def test_same_service_different_country_is_similar_not_competitor(self):
        result = classify_entity(
            offer_job_overlap="strong", target_segment_overlap="none", buyer_overlap="partial",
            geography_overlap="none", purchase_substitutability="partial", official_service_evidence=True,
        )
        self.assertEqual(result["primary_lane"], "similar_company")
        self.assertEqual(result["competitive_role"], "none")
        self.assertEqual(legacy_hint("none", "similar_company"), "similar_company_analog")

    def test_capability_reference_is_not_market_pressure(self):
        result = classify_entity(
            offer_job_overlap="none", target_segment_overlap="none", official_service_evidence=False,
            supplied_as_reference=True, reference_observation_evidence=True,
        )
        self.assertEqual(result["primary_lane"], "capability_reference")
        self.assertEqual(result["competitive_role"], "none")

    def test_capability_reference_without_observed_pattern_stays_uncertain(self):
        result = classify_entity(
            offer_job_overlap="none", target_segment_overlap="none", supplied_as_reference=True,
            reference_observation_evidence=False,
        )
        self.assertEqual(result["primary_lane"], "uncertain")

    def test_unverified_evidence_stays_uncertain(self):
        result = classify_entity(
            offer_job_overlap="strong", target_segment_overlap="strong", buyer_overlap="unknown",
            geography_overlap="unknown", purchase_substitutability="unknown", official_service_evidence=False,
        )
        self.assertEqual(result["primary_lane"], "uncertain")
        self.assertEqual(result["competitive_role"], "unknown")

    def test_social_not_found_is_not_no_presence(self):
        result = normalize_social_presence(
            platform="instagram", url="", status="not_found_in_checked_sources",
            retrieved_at="2026-08-30T00:00:00Z",
        )
        self.assertEqual(result["status"], "not_found_in_checked_sources")
        self.assertTrue(result["metrics_are_public_proxies"])

    def test_discovery_quality_is_normalized(self):
        self.assertEqual(normalize_evidence_quality("strong"), "high")
        self.assertEqual(normalize_evidence_quality("weak"), "low")

    def test_entity_id_is_stable_across_ordering(self):
        self.assertEqual(
            stable_entity_id(url="https://www.example.com/pricing", name="Ignored"),
            stable_entity_id(url="https://example.com", name="Different"),
        )


if __name__ == "__main__":
    unittest.main()
