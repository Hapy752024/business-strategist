import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("feedback_plan", ROOT / "scripts/evidence_scout/plan_customer_feedback.py")
feedback = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(feedback)


def test_topic_led_is_required_when_no_entities_exist() -> None:
    plan = feedback.build_plan("bereavement support", "families", ["CH:de"], [])
    assert plan["analysis_contract"]["topic_led_voc"] == "required"
    assert plan["analysis_contract"]["entity_led_feedback"] == "pending_entity_discovery"


def test_every_entity_locale_gets_every_feedback_lane() -> None:
    entities = [{"id": "e1", "name": "Example", "domain": "example.test", "lane": "competitive_market", "sources": {"company_facebook_comments": ["https://facebook.com/example"]}, "not_applicable": {"apple_app_store_reviews": "No customer app.", "google_play_store_reviews": "No customer app."}}]
    plan = feedback.build_plan("support", "families", ["DE:de", "FR:fr"], entities)
    assert len(plan["source_matrix"]) == len(feedback.LANES) * 2
    page = next(row for row in plan["source_matrix"] if row["source_lane"] == "company_facebook_comments")
    assert page["locator_status"] == "locator_supplied" and page["planned"] is True
    app = next(row for row in plan["source_matrix"] if row["source_lane"] == "apple_app_store_reviews")
    assert app["locator_status"] == "not_applicable" and app["not_applicable_reason"]
    trustpilot = next(row for row in plan["source_matrix"] if row["source_lane"] == "independent_review_platforms")
    assert trustpilot["locator_status"] == "discovery_required" and trustpilot["applicable"] is True


def test_entity_validation_rejects_ambiguous_or_conflicting_source_state(tmp_path: Path) -> None:
    path = tmp_path / "entities.json"; path.write_text(json.dumps([{"id": "e1", "name": "Example", "domain": "example.test", "lane": "supplier"}]))
    with pytest.raises(ValueError, match="invalid lane"):
        feedback.load_entities(str(path))
    entity = {"id": "e1", "name": "Example", "domain": "example.test", "lane": "similar_company", "sources": {"apple_app_store_reviews": ["ios:1"]}, "not_applicable": {"apple_app_store_reviews": "No app"}}
    with pytest.raises(ValueError, match="both locators"):
        feedback.build_plan("support", "families", ["FR:fr"], [entity])


def test_reviewed_source_objects_are_preserved_separately_from_plain_locators() -> None:
    entity = {"id": "e1", "name": "Example", "domain": "example.test", "lane": "similar_company", "sources": {"company_instagram_comments": [{"locator": "example", "locales": ["FR:fr"], "review_status": "accepted", "review_reason": "Official profile linked from domain."}]}}
    plan = feedback.build_plan("support", "families", ["FR:fr"], [entity])
    row = next(row for row in plan["source_matrix"] if row["source_lane"] == "company_instagram_comments")
    assert row["locators"] == ["example"]
    assert row["reviewed_locators"] == [{"locator": "example", "review_reason": "Official profile linked from domain."}]


def test_accepted_locator_is_not_copied_into_an_unreviewed_locale() -> None:
    entity = {"id": "e1", "name": "Example", "domain": "example.test", "lane": "similar_company", "sources": {"apple_app_store_reviews": [{"locator": "111", "locales": ["DE:de"], "review_status": "accepted", "review_reason": "Verified German listing."}]}}
    plan = feedback.build_plan("support", "families", ["DE:de", "FR:fr"], [entity])
    german = next(row for row in plan["source_matrix"] if row["source_lane"] == "apple_app_store_reviews" and row["locale"] == "DE:de")
    french = next(row for row in plan["source_matrix"] if row["source_lane"] == "apple_app_store_reviews" and row["locale"] == "FR:fr")
    assert german["reviewed_locators"] and not french["reviewed_locators"]
    assert french["locator_status"] == "discovery_required"


def test_topic_matrix_covers_every_requested_locale_without_entity_names():
    plan = feedback.build_plan("coordinate care", "families", ["CH:fr", "CH:de", "IT:it"], [])
    assert plan["schema_version"] == 2
    assert {row["locale"] for row in plan["topic_matrix"]} == {"CH:fr", "CH:de", "IT:it"}
    assert all(row["job"] == "coordinate care" and row["role"] == "families" for row in plan["topic_matrix"])
    assert all(row["sampling_detail_status"] == "initial_broad_scope" for row in plan["topic_matrix"])


def test_topic_sampling_can_refine_relevant_roles_sources_and_intents_without_losing_locales():
    cells = [{"locale": "CH:fr", "job": "coordinate care", "role": "adult child", "source_family": "local_forums", "query_intent": "successful_alternatives"},
             {"locale": "CH:fr", "job": "coordinate care", "role": "partner", "source_family": "facebook", "query_intent": "nonadoption"}]
    plan = feedback.build_plan("care", "families", ["CH:fr", "CH:de"], [], cells)
    assert len(plan["topic_matrix"]) == 3
    assert plan["topic_matrix"][0]["query_intent"] == "successful_alternatives"
    assert plan["topic_matrix"][1]["role"] == "partner"
    assert plan["topic_matrix"][2]["locale"] == "CH:de"
    assert plan["topic_matrix"] == feedback.build_plan("care", "families", ["CH:fr", "CH:de"], [], cells)["topic_matrix"]


def test_topic_cell_duplicate_ids_and_unrequested_market_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        feedback.build_plan("care", "families", ["CH:fr"], [], [{"cell_id": "same", "locale": "CH:fr"}] * 2)
    with pytest.raises(ValueError, match="requested locale"):
        feedback.build_plan("care", "families", ["CH:fr"], [], [{"locale": "FR:fr"}])


def test_source_inapplicability_can_be_locale_specific():
    entity = {"id": "e1", "name": "Example", "domain": "example.test", "lane": "similar_company",
              "sources": {"apple_app_store_reviews": [{"locator": "111", "locales": ["DE:de"], "review_status": "accepted", "review_reason": "German listing checked"}]},
              "not_applicable": {"apple_app_store_reviews": {"FR:fr": "Verified app is not offered in this storefront"}}}
    plan = feedback.build_plan("support", "families", ["DE:de", "FR:fr"], [entity])
    rows = [row for row in plan["source_matrix"] if row["source_lane"] == "apple_app_store_reviews"]
    assert rows[0]["applicable"] is True and rows[1]["applicable"] is False
