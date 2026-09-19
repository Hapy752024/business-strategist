import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collector", ROOT / "scripts/evidence_scout/collect.py")
collector = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(collector)


def args(**extra):
    base = dict(customer_segment="families", hypothesis_id="H1", limit=10, days=365, language="de", geo="DE", trustpilot_domains="", trustpilot_max_pages=2, google_place_ids="", segment_keywords="families", problem_keywords="paperwork", workaround_keywords="help", topic="support")
    base.update(extra); return argparse.Namespace(**base)


def accepted_plan(tmp_path, entries):
    rows = []
    for entry in entries:
        entity_id, lane, locator = entry[:3]
        locale = entry[3] if len(entry) > 3 else "DE:de"
        rows.append({"entity_id": entity_id, "locale": locale, "source_lane": lane, "applicable": True, "reviewed_locators": [{"locator": locator, "review_reason": "verified fixture"}]})
    path = tmp_path / "source-plan.json"; path.write_text(__import__("json").dumps({"source_matrix": rows}))
    return str(path)


def test_trustpilot_keeps_customer_review_and_company_reply_roles_separate(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "get_secret", lambda *names: (names[0], "key"))
    def fake_get(url, **_kwargs):
        if "/find?" in url: return {"ok": True, "status_code": 200, "body": {"id": "bu1"}}
        return {"ok": True, "status_code": 200, "body": {"reviews": [{"id": "r1", "stars": 2, "title": "Slow", "text": "I needed help and waited", "language": "en", "createdAt": "2026-09-01T12:00:00Z", "isVerified": True, "consumer": {"displayName": "A"}, "companyReply": {"text": "Please contact support", "createdAt": "2026-09-02T12:00:00Z"}}]}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    plan = accepted_plan(tmp_path, [("e1", "independent_review_platforms", "example.test")])
    records, summary = collector.collect_trustpilot_reviews(args(trustpilot_domains="e1=example.test", customer_feedback_source_plan=plan), [], tmp_path)
    assert summary["status"] == "ok" and summary["entity_ledger"][0]["retrieved_count"] == 1
    assert [row["source_role"] for row in records] == ["customer_review", "competitor_context"]
    assert not collector.accepted_records(records)[1]


def test_favorable_established_reviews_are_customer_feedback_not_editorial():
    for source in ("trustpilot_review", "google_places_review", "itunes_reviews", "app_review"):
        row = collector.normalize_record(source=source, source_url="https://reviews.example/item", query="q", customer_segment="families", hypothesis="H1", text="Best service I have used. It helped me finish paperwork on time.")
        assert row["source_role"] == "customer_review"
        assert row["source_intent"] == "customer_feedback"


def test_google_places_reports_subset_denominator_and_exact_entity_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "get_secret", lambda *names: (names[0], "key"))
    monkeypatch.setattr(collector, "http_get", lambda *_args, **_kwargs: {"ok": True, "status_code": 200, "body": {"id": "p1", "rating": 4.2, "userRatingCount": 120, "googleMapsUri": "https://maps.google.com/example", "reviews": [{"name": "places/p1/reviews/r1", "rating": 4, "publishTime": "2026-09-01T12:00:00Z", "text": {"text": "They helped with paperwork", "languageCode": "en"}, "authorAttribution": {"displayName": "B"}}]}})
    plan = accepted_plan(tmp_path, [("e1", "google_business_reviews", "ChIJ123")])
    records, summary = collector.collect_google_places_reviews(args(google_place_ids="e1=ChIJ123", customer_feedback_source_plan=plan), [], tmp_path)
    assert summary["sampling_frame"] == "provider_selected_api_subset"
    assert summary["entity_ledger"][0]["returned_review_count"] == 1
    assert summary["entity_ledger"][0]["user_rating_count"] == 120
    assert records[0]["subject_entity_id"] == "e1" and records[0]["source_role"] == "customer_review"
    assert not collector.accepted_records(records)[1]


def test_itunes_attempts_every_entity_storefront_with_per_lane_limit(tmp_path, monkeypatch):
    calls = []
    def fake_get(url, **_kwargs):
        calls.append(url)
        review_id = f"r{len(calls)}"
        return {"ok": True, "status_code": 200, "body": {"feed": {"entry": [{"id": {"label": review_id}, "updated": {"label": "2026-09-01T12:00:00Z"}, "title": {"label": "Useful"}, "content": {"label": "The app helped with paperwork"}, "im:rating": {"label": "5"}, "author": {"name": {"label": "A"}}}]}}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    plan = accepted_plan(tmp_path, [(entity, "apple_app_store_reviews", app, locale) for entity, app in (("e1", "111"), ("e2", "222")) for locale in ("DE:de", "FR:fr")])
    run_args = args(limit=1, itunes_entity_apps="e1=111,e2=222", itunes_app_ids="", itunes_locales="DE:de,FR:fr", itunes_countries="", itunes_max_pages=1, customer_feedback_source_plan=plan)
    records, summary = collector.collect_itunes_reviews(run_args, [], tmp_path)
    assert len(calls) == 4 and len(summary["entity_ledger"]) == 4
    assert {row["subject_entity_id"] for row in records} == {"e1", "e2"}
    assert all(row["sampling_frame"] == "entity_led_feedback" for row in records)


def test_itunes_does_not_silently_truncate_storefronts(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda url, **_kwargs: calls.append(url) or {"ok": True, "status_code": 200, "body": {"feed": {}}})
    locales = ("DE:de", "FR:fr", "CH:de", "AT:de")
    plan = accepted_plan(tmp_path, [("e1", "apple_app_store_reviews", "111", locale) for locale in locales])
    run_args = args(itunes_entity_apps="e1=111", itunes_app_ids="", itunes_locales=",".join(locales), itunes_countries="", itunes_max_pages=1, customer_feedback_source_plan=plan)
    _records, summary = collector.collect_itunes_reviews(run_args, [], tmp_path)
    assert len(calls) == 4 and len(summary["entity_ledger"]) == 4


def test_sonar_review_failure_is_not_hidden_by_keyword_records_and_keeps_positive_reviews(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "get_secret", lambda *_names: ("SONAR_API_KEY", "key"))
    review_calls = 0
    def fake_get(url, **_kwargs):
        nonlocal review_calls
        if "/apps/reviews" in url:
            review_calls += 1
            if review_calls == 1:
                return {"ok": True, "status_code": 200, "body": {"data": [{"id": "r1", "title": "Great", "text": "This solved our paperwork", "score": 5}]}}
            return {"ok": False, "status_code": 402, "body": {"error": "credits"}}
        if "/keywords/suggestions" in url:
            return {"ok": True, "status_code": 200, "body": {"data": ["support"]}}
        return {"ok": True, "status_code": 200, "body": {"data": [{"keyword": "support", "difficulty": 1}]}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    plan = accepted_plan(tmp_path, [("e1", "apple_app_store_reviews", "ios:111"), ("e2", "google_play_store_reviews", "android:pkg")])
    run_args = args(sonar_stores="ios", sonar_keyword_limit=1, sonar_entity_apps="e1=ios:111,e2=android:pkg", sonar_apps="", sonar_review_max_rating=5, sonar_include_revenue=False, customer_feedback_source_plan=plan)
    records, summary = collector.collect_sonar(run_args, ["support"], tmp_path)
    reviews = [row for row in records if row["source"] == "app_review"]
    assert reviews[0]["author_context"].find("score=5") >= 0
    assert reviews[0]["subject_entity_id"] == "e1"
    assert summary["status"] == "partial" and len(summary["review_ledger"]) == 2


def test_apple_storefront_requires_matching_reviewed_locale_before_http(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda *a, **k: calls.append(a) or {"ok": True, "body": {}})
    plan = accepted_plan(tmp_path, [("e1", "apple_app_store_reviews", "111", "DE:de")])
    run_args = args(itunes_entity_apps="e1=111", itunes_app_ids="", itunes_locales="DE:de,FR:fr", itunes_countries="", itunes_max_pages=1, customer_feedback_source_plan=plan)
    _records, summary = collector.collect_itunes_reviews(run_args, [], tmp_path)
    assert summary["status"] == "capture_gate_blocked"
    assert "FR:fr" in summary["reason"] and not calls


def test_instagram_company_profile_requires_reviewed_entity_locator_before_http(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda *a, **k: calls.append(a) or {"ok": True, "body": {}})
    run_args = argparse.Namespace(ig_handles="e1=example", customer_feedback_source_plan="", fb_groups="", fb_pages="", community_capture_authorization="", community_verified_sources="", community_review_receipt="")
    records, summary = collector.collect_scrapecreators(run_args, [], tmp_path)
    assert not records and summary["status"] == "capture_gate_blocked" and not calls


def test_reviewed_instagram_profile_is_supplier_context_and_entity_bound(tmp_path, monkeypatch):
    source = {"id": "e1", "name": "Example", "domain": "example.test", "lane": "similar_company", "sources": {"company_instagram_comments": [{"locator": "example", "locales": ["DE:de"], "review_status": "accepted", "review_reason": "Official link"}]}}
    plan_module_spec = importlib.util.spec_from_file_location("planner_for_ig", ROOT / "scripts/evidence_scout/plan_customer_feedback.py")
    planner = importlib.util.module_from_spec(plan_module_spec); assert plan_module_spec.loader; plan_module_spec.loader.exec_module(planner)
    plan_path = tmp_path / "plan.json"; plan_path.write_text(__import__("json").dumps(planner.build_plan("support", "families", ["DE:de"], [source])))
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *_names: ("SCRAPE_CREATORS_API_KEY", "key"))
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 20}}
        if "instagram/user/posts" in url: return {"ok": True, "status_code": 200, "body": {"items": [{"id": "p1", "caption": "Our service helps with paperwork", "url": "https://instagram.com/p/p1"}]}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    run_args = args(ig_handles="e1=example", customer_feedback_source_plan=str(plan_path), fb_groups="", fb_pages="", community_capture_authorization="", community_verified_sources="", community_review_receipt="", x_handles="", ig_hashtags="", social_per_endpoint=2, fb_max_posts=3, social_comments=False, comments_max=2)
    records, summary = collector.collect_scrapecreators(run_args, [], tmp_path)
    profile = next(row for row in records if row.get("source_entity_type") == "instagram_profile")
    assert profile["source_role"] == "competitor_context"
    assert profile["author_voice_status"] == "supplier_context"
    assert profile["subject_entity_id"] == "e1"


def test_instagram_profiles_are_not_truncated_and_comment_failure_is_visible(tmp_path, monkeypatch):
    mappings = [(f"e{i}", "company_instagram_comments", f"handle{i}") for i in range(11)]
    plan = accepted_plan(tmp_path, mappings)
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *_names: ("SCRAPE_CREATORS_API_KEY", "key"))
    post_calls = []
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 100}}
        if "instagram/user/posts" in url:
            post_calls.append(url); number = len(post_calls)
            return {"ok": True, "status_code": 200, "body": {"items": [{"id": f"p{number}", "caption": "Paperwork help", "url": f"https://instagram.com/p/p{number}"}]}}
        if "instagram/post/comments" in url: return {"ok": False, "status_code": 403, "body": {"error": "denied"}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    handles = ",".join(f"e{i}=handle{i}" for i in range(11))
    run_args = args(ig_handles=handles, customer_feedback_source_plan=plan, fb_groups="", fb_pages="", community_capture_authorization="", community_verified_sources="", community_review_receipt="", x_handles="", ig_hashtags="", social_per_endpoint=1, fb_max_posts=3, social_comments=True, comments_max=1)
    _records, summary = collector.collect_scrapecreators(run_args, [], tmp_path)
    assert len(post_calls) == 11
    assert summary["status"] == "partial"
    assert any("permission_denied" in alert for alert in summary["coverage_alerts"])


def test_facebook_company_page_comments_are_entity_bound_and_owner_comment_is_supplier(tmp_path, monkeypatch):
    page = "https://facebook.com/example"
    plan = accepted_plan(tmp_path, [("e1", "company_facebook_comments", page)])
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *_names: ("SCRAPE_CREATORS_API_KEY", "key"))
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 20}}
        if "facebook/profile/posts" in url: return {"ok": True, "status_code": 200, "body": {"posts": [{"id": "p1", "text": "Our service", "url": "https://facebook.com/p1", "author": {"name": "Example Page"}}]}}
        if "facebook/profile/reels" in url: return {"ok": True, "status_code": 200, "body": {"reels": []}}
        if "facebook/post/comments" in url: return {"ok": True, "status_code": 200, "body": {"comments": [{"id": "c1", "text": "Contact us", "user": {"name": "Example Page"}}]}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    run_args = args(fb_entity_pages=f"e1={page}", fb_groups="", fb_pages="", customer_feedback_source_plan=plan, community_capture_authorization="", community_verified_sources="", community_review_receipt="", ig_handles="", x_handles="", ig_hashtags="", social_per_endpoint=1, fb_max_posts=3, social_comments=True, comments_max=1)
    records, summary = collector.collect_scrapecreators(run_args, [], tmp_path)
    entity_records = [row for row in records if row.get("subject_entity_id") == "e1"]
    assert entity_records and all(row["sampling_frame"] == "entity_led_feedback" for row in entity_records)
    owner_comment = next(row for row in entity_records if row.get("source_entity_type") == "facebook_supplier_comment")
    assert owner_comment["source_role"] == "competitor_context" and owner_comment["author_voice_status"] == "supplier_context"
    assert summary["status"] in {"ok", "partial"}


def test_supplier_page_context_route_also_keeps_owner_comments_supplier(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *_names: ("SCRAPE_CREATORS_API_KEY", "key"))
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 20}}
        if "facebook/profile/posts" in url: return {"ok": True, "status_code": 200, "body": {"posts": [{"id": "p1", "text": "Our service", "url": "https://facebook.com/p1", "author": {"name": "Example Page"}}]}}
        if "facebook/profile/reels" in url: return {"ok": True, "status_code": 200, "body": {"reels": []}}
        if "facebook/post/comments" in url: return {"ok": True, "status_code": 200, "body": {"comments": [{"id": "c1", "text": "Contact us", "user": {"name": "Example Page"}}]}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    run_args = args(fb_entity_pages="", fb_groups="", fb_pages="https://facebook.com/example", community_capture_authorization="", community_verified_sources="", community_review_receipt="", ig_handles="", x_handles="", ig_hashtags="", social_per_endpoint=1, fb_max_posts=3, social_comments=True, comments_max=1)
    records, _summary = collector.collect_scrapecreators(run_args, [], tmp_path)
    owner_comment = next(row for row in records if row.get("source_entity_type") == "facebook_supplier_comment")
    assert owner_comment["source_role"] == "competitor_context" and owner_comment["author_voice_status"] == "supplier_context"


def test_entity_review_collectors_block_unreviewed_locator_before_http(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda *a, **k: calls.append(a) or {"ok": True, "body": {}})
    _records, summary = collector.collect_trustpilot_reviews(args(trustpilot_domains="e1=example.test", customer_feedback_source_plan=""), [], tmp_path)
    assert summary["status"] == "capture_gate_blocked" and not calls


def test_legacy_app_flags_cannot_be_relabelled_entity_led_without_review(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda *a, **k: calls.append(a) or {"ok": True, "body": {}})
    apple = args(itunes_entity_apps="", itunes_app_ids="111", itunes_countries="de", itunes_max_pages=1, sampling_frame="entity_led_feedback", subject_entity_id="e1")
    _records, apple_summary = collector.collect_itunes_reviews(apple, [], tmp_path)
    sonar = args(sonar_entity_apps="", sonar_apps="ios:111", sampling_frame="entity_led_feedback", subject_entity_id="e1")
    _records, sonar_summary = collector.collect_sonar(sonar, [], tmp_path)
    assert apple_summary["status"] == sonar_summary["status"] == "capture_gate_blocked"
    assert not calls


def test_legacy_app_flags_are_blocked_even_when_caller_labels_them_topic_led(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda *a, **k: calls.append(a) or {"ok": True, "body": {}})
    _records, apple = collector.collect_itunes_reviews(args(itunes_entity_apps="", itunes_app_ids="111", sampling_frame="topic_led_voc"), [], tmp_path)
    _records, sonar = collector.collect_sonar(args(sonar_entity_apps="", sonar_apps="ios:111", sampling_frame="topic_led_voc"), [], tmp_path)
    assert apple["status"] == sonar["status"] == "capture_gate_blocked" and not calls


def test_ambiguous_social_and_forum_authors_are_not_customer_voice():
    for source in ("reddit", "hn", "github", "youtube_comment", "x", "facebook"):
        row = collector.normalize_record(source=source, source_url="https://example.test/post", query="q", customer_segment="families", hypothesis="H1", text="We are a vendor and customers struggle with paperwork")
        assert row["source_role"] == "community_context"


def test_comment_by_verified_instagram_company_handle_is_supplier_context():
    context = collector.social_comment_context({"id": "c1", "text": "Contact us", "user": {"username": "Example"}}, "instagram", "@example")
    assert context["source_role"] == "competitor_context"
    assert context["source_intent"] == "competitor_content"
    assert context["source_entity_type"] == "instagram_supplier_comment"


def test_instagram_pagination_uses_documented_next_max_id_parameter(monkeypatch):
    calls = []
    def fake_get(url, **_kwargs):
        calls.append(url)
        if len(calls) == 1:
            return {"ok": True, "status_code": 200, "body": {"items": [{"id": "p1"}], "next_max_id": "next-page"}}
        return {"ok": True, "status_code": 200, "body": {"items": [{"id": "p2"}]}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    items, status = collector.scrapecreators_paginate("https://api.test/posts", {"handle": "example"}, "key", "items", "next_max_id", 2, [], "instagram")
    assert [item["id"] for item in items] == ["p1", "p2"] and status == "ok"
    assert "next_max_id=next-page" in calls[1] and "cursor=" not in calls[1]


def test_firecrawl_credit_exhaustion_after_success_remains_visible_and_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "get_secret", lambda *_names: ("FIRECRAWL_API_KEY_HGINVESTOR", "key"))
    calls = []
    def fake_post(*_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            return {"ok": True, "status_code": 200, "body": {"data": [{"url": "https://forum.test/1", "title": "Paperwork", "description": "I need help"}]}}
        return {"ok": False, "status_code": 402, "body": {"error": "insufficient credits"}}
    monkeypatch.setattr(collector, "http_post", fake_post)
    run_args = args(limit=8)
    records, summary = collector.collect_firecrawl(run_args, ["q1", "q2", "q3", "q4"], tmp_path)
    assert records and len(calls) == 2
    assert summary["status"] == "insufficient_credits"
    assert summary["top_up_url"] and len(summary["query_ledger"]) == 4
    assert collector.provider_alerts({"firecrawl": summary})


def test_generic_firecrawl_vendor_result_is_not_counted_as_forum(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "get_secret", lambda *names: (names[0], "key"))
    monkeypatch.setattr(collector, "http_post", lambda *_args, **_kwargs: {"ok": True, "status_code": 200, "body": {"data": [{"url": "https://vendor.test/service", "title": "Get a quote", "description": "Our broker helps with hard paperwork", "markdown": "Get a free quote from our service"}]}})
    run_args = argparse.Namespace(limit=5, geo="DE", language="de", topic="paperwork", customer_segment="families", hypothesis_id="H1", problem_keywords="paperwork", workaround_keywords="help", segment_keywords="families")
    records, summary = collector.collect_firecrawl(run_args, ["paperwork help"], tmp_path)
    assert summary["status"] == "ok"
    assert records[0]["source"] == "web_search"
    assert records[0]["source_role"] != "community_context"
