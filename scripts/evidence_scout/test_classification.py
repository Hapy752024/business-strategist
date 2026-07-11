#!/usr/bin/env python3
"""Lightweight regression tests for German PKV/BU research heuristics."""

from __future__ import annotations

import unittest

from analyze_competitor_marketing import classify_page_type, classify_pricing_posture, extract_price_tokens, normalize_price_tokens
from collect import demand_expansion_terms, infer_comment_intent, infer_evidence_type, infer_geo_language, infer_source_intent, quality_summary, selected_providers
from discover_competitors import CANONICAL_KNOWN_URLS, classify_candidate, known_lookup_relevant


class EvidenceClassificationTests(unittest.TestCase):
    def test_decision_uncertainty_beats_spend_terms(self) -> None:
        text = "Ich bin bei PKV oder GKV komplett ueberfragt. Die Beitraege kosten viel und ich habe Angst vor der falschen Entscheidung."
        self.assertEqual(infer_evidence_type(text), "decision_uncertainty")

    def test_social_decision_question_is_user_pain(self) -> None:
        self.assertEqual(
            infer_source_intent("reddit", "https://www.reddit.com/r/Finanzen/x", "PKV oder GKV?", "decision_uncertainty"),
            "user_pain",
        )
        self.assertEqual(infer_comment_intent("reddit", "PKV oder GKV?", "decision_uncertainty"), "decision_question")

    def test_source_intent_registry_classifies_forums_and_editorials(self) -> None:
        self.assertEqual(
            infer_source_intent("forum", "https://community.finanztip.de/thread/pkv", "PKV Entscheidung", "community"),
            "forum_discussion",
        )
        self.assertEqual(
            infer_source_intent("web_search", "https://www.finanztip.de/pkv/", "PKV Ratgeber", "community"),
            "editorial_content",
        )

    def test_demand_expansion_terms_include_layperson_and_competitor_terms(self) -> None:
        terms = demand_expansion_terms("digital insurance advice for PKV BU Germany", "DE", "de")
        self.assertIn("Private Krankenversicherung", terms)
        self.assertIn("PKV Rechner", terms)
        self.assertIn("CHECK24 PKV", terms)

    def test_quality_flags_weak_and_unknown_heavy_runs(self) -> None:
        records = [
            {"source": "forum", "source_intent": "unknown", "strength": "weak"},
            {"source": "web_search", "source_intent": "unknown", "strength": "weak"},
            {"source": "reddit", "source_intent": "user_pain", "strength": "weak"},
            {"source": "google_trends", "source_intent": "search_demand", "strength": "weak", "text": '"value": 0'},
        ]
        flags = " ".join(quality_summary(records, {"reddit": {"status": "ok", "record_count": 1}}))
        self.assertIn("Most relevant records are weak", flags)
        self.assertIn("Many records have unknown source intent", flags)

    def test_china_markers_infer_geo_language(self) -> None:
        self.assertEqual(
            infer_geo_language("xiaohongshu reviews for skincare app", "Chinese consumers"),
            ("CN", "zh"),
        )

    def test_chinese_pain_and_decision_language(self) -> None:
        self.assertEqual(infer_evidence_type("这个工具太难用了，手动整理表格很麻烦"), "workaround")
        self.assertEqual(infer_evidence_type("小红书上这个服务靠谱吗？值得买吗？"), "decision_uncertainty")
        self.assertEqual(infer_comment_intent("xiaohongshu", "这个服务靠谱吗？", "decision_uncertainty"), "decision_question")
        self.assertEqual(
            infer_source_intent("bilibili", "https://www.bilibili.com/video/BV1", "踩坑避雷", "pain"),
            "user_pain",
        )

    def test_china_provider_aliases_expand(self) -> None:
        self.assertEqual(
            selected_providers("china_public"),
            ["china_bilibili", "china_v2ex", "china_web"],
        )
        self.assertEqual(
            selected_providers("china_social"),
            ["china_xiaohongshu"],
        )


class CompetitorClassificationTests(unittest.TestCase):
    def test_known_lookup_rejects_cancellation_noise(self) -> None:
        self.assertFalse(
            known_lookup_relevant(
                "digital insurance broker for PKV Germany",
                "Getsafe Versicherung kuendigen",
                "Cancel your insurance contract online",
                "https://www.smartkuendigen.de/getsafe-kuendigen",
            )
        )

    def test_known_competitor_registry_loaded(self) -> None:
        self.assertEqual(CANONICAL_KNOWN_URLS["getsafe"], "https://www.hellogetsafe.com/de-de/p/privatekrankenversicherung-de")

    def test_broad_getsafe_page_is_future_threat_not_direct_broker(self) -> None:
        candidate = classify_candidate(
            {
                "name": "Getsafe",
                "domain": "hellogetsafe.com",
                "url": "https://www.hellogetsafe.com/de-de",
                "evidence_snippets": ["Digital insurance app to manage policies online."],
                "sources": [{"query": "Getsafe insurance Germany"}],
            },
            "digital insurance broker for PKV BU Germany",
            "high-income employees and self-employed professionals in Germany",
        )
        self.assertEqual(candidate["business_model_hint"], "insurance_app")
        self.assertEqual(candidate["competitor_type_hint"], "future_threat_candidate")
        self.assertEqual(candidate["entity_type_hint"], "future_threat_candidate")
        self.assertEqual(candidate["source_page_type_hint"], "adjacent_app_homepage")


class MarketingExtractionTests(unittest.TestCase):
    def test_structured_price_tokens_extract_insurance_terms(self) -> None:
        tokens = extract_price_tokens("Private Krankenversicherung ab 653 EUR monatlich, Jahresgrenze €77,400, mit 600 Euro Selbstbeteiligung und Tarif Premium.")
        self.assertIn("653 EUR", tokens["currency_amounts"])
        self.assertIn("€77,400", tokens["currency_amounts"])
        normalized = normalize_price_tokens(tokens)
        self.assertIn({"raw": "€77,400", "currency": "EUR", "value": 77400.0}, normalized["currency_amounts"])
        self.assertIn("monatlich", [item.lower() for item in tokens["monthly_terms"]])
        self.assertTrue(tokens["deductible_terms"])
        self.assertTrue(tokens["tariff_terms"])

    def test_pricing_language_only_is_not_transparent_pricing(self) -> None:
        self.assertEqual(classify_pricing_posture("Wir bieten transparente Tarife und faire Beiträge."), "pricing_language_only")

    def test_page_type_distinguishes_product_from_blog(self) -> None:
        self.assertEqual(
            classify_page_type("https://example.com/private-krankenversicherung", "PKV", "Private Krankenversicherung Angebot"),
            "product_page",
        )
        self.assertEqual(
            classify_page_type("https://example.com/de-de/p/privatekrankenversicherung-de", "PKV", "Private Krankenversicherung Angebot"),
            "product_page",
        )
        self.assertEqual(
            classify_page_type("https://example.com/blog/pkv-guide", "PKV Guide", "Ratgeber"),
            "blog_article",
        )


if __name__ == "__main__":
    unittest.main()
