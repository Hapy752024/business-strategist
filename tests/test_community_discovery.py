from __future__ import annotations

import argparse
import base64
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator, FormatChecker

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "evidence_scout"
sys.path.insert(0, str(SCRIPT_DIR))
communities = importlib.import_module("discover_communities")
reviews = importlib.import_module("review_community_candidates")
collector = importlib.import_module("collect")
rechecks = importlib.import_module("recheck_community_source")

DISCOVERY_PRIVATE = base64.b64encode(bytes(range(1, 33))).decode()
REVIEW_PRIVATE = reviews.TEST_PRIVATE_KEY_B64
def public_key(private_b64: str) -> str:
    private = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_b64))
    return base64.b64encode(private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
DISCOVERY_PUBLIC = public_key(DISCOVERY_PRIVATE)
REVIEW_PUBLIC = public_key(REVIEW_PRIVATE)


def forum_observation(**overrides):
    row = {
        "provider": "fixture", "query_id": "GB:en:forum", "query": "widow navigation forum", "query_kind": "forum",
        "country": "GB", "language": "en", "url": "https://community.example.org/forum/widow-navigation",
        "title": "Widow navigation community", "description": "Members discuss widow navigation questions and answers.",
        "markdown": "Forum topic. Members post questions and replies about widow navigation. I need guidance. " * 8,
        "result_rank": 1, "fetched_at": "2026-09-14T10:00:00+00:00", "http_status": 200, "response_id": "r1",
    }
    row.update(overrides)
    return row


def classify_observation(observation, topic="widow navigation", keywords="widow navigation", segment="recently widowed adults", sensitivity="standard"):
    candidates = {}
    communities.add_observation(candidates, observation)
    return communities.classify(next(iter(candidates.values())), topic, keywords, segment, sensitivity)


def test_query_plan_is_generic_multilocale_source_language_and_seed_complete() -> None:
    locales = communities.parse_locales(["CH:de", "CA:fr"], "", "")
    local_terms = communities.parse_locale_keywords(["CH:de=Nachlass Hilfe|Erbschaft Frage", "CA:fr=aide succession|question héritage"], locales)
    plan = communities.query_plan("estate paperwork", "", locales, local_terms)
    assert len(plan) == 12
    assert {item["locale_id"] for item in plan} == {"CH:de", "CA:fr"}
    assert {item["kind"] for item in plan} == {"forum", "facebook_group", "facebook_page"}
    assert {item["seed"] for item in plan if item["locale_id"] == "CH:de"} == {"Nachlass Hilfe", "Erbschaft Frage"}
    assert {item["seed"] for item in plan if item["locale_id"] == "CA:fr"} == {"aide succession", "question héritage"}
    assert all("estate paperwork" not in item["query"] for item in plan)
    assert all("aide succession" not in item["query"] for item in plan if item["locale_id"] == "CH:de")
    assert all("Nachlass Hilfe" not in item["query"] for item in plan if item["locale_id"] == "CA:fr")
    assert all("site:facebook.com/groups" in item["query"] for item in plan if item["kind"] == "facebook_group")
    assert all("-site:facebook.com/groups" in item["query"] for item in plan if item["kind"] == "facebook_page")
    assert any("Erfahrungen" in item["query"] for item in plan)
    assert any("temoignage" in item["query"] for item in plan)


def test_locale_contract_rejects_ambiguous_lists_and_unsupported_language() -> None:
    with pytest.raises(ValueError, match="repeatable --locale"):
        communities.parse_locales([], "DE,FR", "de,fr")
    with pytest.raises(ValueError, match="Invalid locale"):
        communities.parse_locales(["ES:x"], "", "")
    with pytest.raises(ValueError, match="ISO 3166"):
        communities.parse_locales(["ZZ:qqq"], "", "")
    assert communities.parse_locales(["AE:ar"], "", "")[0]["language"] == "ar"
    assert communities.parse_locales(["ES:es"], "", "")[0]["language"] == "es"
    with pytest.raises(ValueError, match="undeclared locale"):
        communities.parse_locale_keywords(["FR:fr=aide"], communities.parse_locales(["CH:de"], "", ""))


def test_multilocale_cli_requires_locale_specific_or_attested_seed_language(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["discover_communities.py", "--topic", "paperwork", "--customer-segment", "families", "--community-keywords", "paperwork", "--locale", "GB:en", "--locale", "CH:de"])
    with pytest.raises(SystemExit):
        communities.parse_args()


def test_unsupported_language_requires_explicit_local_source_terms(monkeypatch) -> None:
    base = ["discover_communities.py", "--topic", "inheritance", "--customer-segment", "families", "--locale", "ES:es", "--locale-keywords", "ES:es=ayuda herencia"]
    monkeypatch.setattr(sys, "argv", base)
    with pytest.raises(SystemExit): communities.parse_args()
    monkeypatch.setattr(sys, "argv", base + ["--locale-source-terms", "ES:es=foro experiencias|grupo Facebook|página Facebook"])
    args = communities.parse_args(); plan = communities.query_plan(args.topic, args.community_keywords, args.locales, args.locale_keyword_map, args.locale_source_term_map)
    assert any("foro experiencias" in row["query"] for row in plan)
    assert all("forum community" not in row["query"] for row in plan)


def test_query_limit_exposes_each_seed_lane_and_rejects_incomplete_run() -> None:
    plan = communities.query_plan("tax filing", "freelancer tax,late filing", communities.parse_locales(["US:en", "CH:de"], "", ""))
    selected, skipped = communities.provider_queries(plan, 3)
    assert len(selected) == 3 and len(skipped) == 9
    assert {item["kind"] for item in selected} == {"forum", "facebook_group", "facebook_page"}
    assert {(item["locale_id"], item["seed"], item["kind"]) for item in selected + skipped} == {
        (locale, seed, kind) for locale in ("US:en", "CH:de") for seed in ("freelancer tax", "late filing") for kind in ("forum", "facebook_group", "facebook_page")
    }
    assert all(item.get("skip_reason") == "query_limit" for item in skipped)
    with pytest.raises(ValueError, match="every forum/Facebook locale lane"):
        communities.require_complete_locale_coverage(plan, 11)


def test_firecrawl_discovery_requests_search_metadata_not_page_markdown(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(communities, "get_secret", lambda *args: ("FIRECRAWL_API_KEY_HGINVESTOR", "key"))
    monkeypatch.setattr(communities, "http_post", lambda endpoint, headers, data: calls.append(data) or {"ok": True, "status": 200, "body": {"data": []}})
    plan = communities.query_plan("paperwork", "", communities.parse_locales(["GB:en"], "", ""), {"GB:en": ["estate paperwork"]})
    args = argparse.Namespace(query_limit=3, limit=5)
    communities.collect_provider("firecrawl", plan, args, {})
    assert len(calls) == 3
    assert all("scrapeOptions" not in payload for payload in calls)
    assert all(payload["country"] == "GB" and payload["location"] == "GB" for payload in calls)


def test_http_status_uses_shared_client_status_code() -> None:
    audit = communities.response_audit({"ok": True, "status_code": 200, "body": {}}, {"query_id": "ES:es:forum:s1", "query": "q", "kind": "forum", "country": "ES", "language": "es"})
    assert audit["http_status"] == 200


def test_failed_provider_response_discards_body_results(monkeypatch) -> None:
    monkeypatch.setattr(communities, "get_secret", lambda *args: ("key", "secret"))
    monkeypatch.setattr(communities, "http_post", lambda *args, **kwargs: {"ok": False, "status_code": 500, "body": {"organic": [{"link": "https://forum.example/topic", "title": "Should not survive"}]}})
    plan = communities.query_plan("estate", "", communities.parse_locales(["GB:en"], "", ""), {"GB:en": ["estate help"]})
    rows, summary = communities.collect_provider("serper_search", plan, argparse.Namespace(query_limit=3, limit=5), {})
    assert rows == [] and summary["result_count"] == 0


def test_facebook_page_owned_or_unknown_post_is_not_customer_voice() -> None:
    context = collector.facebook_item_context({"author": {"name": "Example Page"}, "created_time": "2026-09-14T12:00:00Z"}, "ScrapeCreators fb-page:https://facebook.com/example")
    record = collector.normalize_record(source="facebook", source_url="https://facebook.com/example/posts/1", query="q", customer_segment="families", hypothesis="H1", text="This is hard", author_context=context["author_label"], source_role_override=context["source_role"], source_intent_override=context["source_intent"], published_at=context["published_at"], source_entity_type=context["source_entity_type"], author_relationship=context["author_relationship"])
    assert record["source_role"] == "competitor_context"
    assert record["source_intent"] == "competitor_content"
    assert record["source_entity_type"] == "facebook_page"
    assert record["author_relationship"] == "page_or_supplier_author"

    reels = collector.facebook_item_context({"author": {"name": "Example Page"}}, "ScrapeCreators fb-page-reels:https://facebook.com/example")
    assert reels["source_role"] == "competitor_context" and reels["source_entity_type"] == "facebook_page"


def test_facebook_group_post_and_comments_remain_unverified_community_context() -> None:
    context = collector.facebook_item_context({"author": {"name": "Vendor Admin"}}, "ScrapeCreators fb-group:https://facebook.com/groups/example")
    assert context["source_role"] == "community_context"
    assert context["source_intent"] == "forum_discussion"
    assert context["author_relationship"] == "group_participant_unverified"
    comment = collector.normalize_record(source="facebook", source_url="https://facebook.com/posts/1", query="q", customer_segment="families", hypothesis="H1", text="Buy our service", source_role_override="community_context", source_intent_override="social_comment", source_entity_type="facebook_comment", author_relationship="commenter_unverified")
    assert comment["source_role"] == "community_context" and comment["author_relationship"] == "commenter_unverified"
    supplier_comment = collector.social_comment_context({"author": {"name": "Vendor", "type": "Page"}}, "facebook")
    assert supplier_comment["source_role"] == "competitor_context"


def test_direct_recheck_rejects_login_wall_and_requires_semantic_activity() -> None:
    response = {"ok": True, "status_code": 200, "headers": {"Content-Type": "text/html"}, "body_size_bytes": 500, "body": {"text": "Log in to continue. post today " * 20}}
    result = rechecks.semantic_assessment("https://facebook.com/groups/example", response)
    assert result["access_status"] == "not_verified_public"
    assert result["activity_status"] == "not_verified_active"
    assert "login_or_challenge" in result["semantic_markers"]
    spanish = rechecks.semantic_assessment("https://facebook.com/groups/example", {**response, "body": {"text": "Iniciar sesión para continuar. publicación hoy " * 20}})
    assert spanish["access_status"] == "not_verified_public"
    personal = rechecks.semantic_assessment("https://facebook.com/john.smith", {**response, "body": {"text": "Public post today " * 20}})
    assert personal["entity_type_observed"] == "unresolved"
    stale = rechecks.semantic_assessment("https://facebook.com/groups/example", {**response, "body": {"text": "Public post 99 days ago " * 20}})
    assert stale["activity_status"] == "not_verified_active"
    portuguese = rechecks.semantic_assessment("https://facebook.com/groups/example", {**response, "body": {"text": "Entrar para continuar. post today " * 20}})
    assert portuguese["access_status"] == "not_verified_public"
    navigation = rechecks.semantic_assessment("https://facebook.com/groups/feed", {**response, "body": {"text": '\"group_id\":\"12345\", <article data-post=\"1\"><time datetime=\"2026-09-15\">'}})
    assert navigation["entity_type_observed"] == "unresolved"
    verified = rechecks.semantic_assessment("https://facebook.com/groups/example", {**response, "body": {"text": '\"group_id\":\"12345\", \"post_id\":\"88\", \"created_time\":\"2026-09-15\" ' * 10}})
    assert verified["entity_type_observed"] == "facebook_group" and verified["activity_status"] == "active_recent"


def test_editorial_and_named_forum_false_positives_are_rejected() -> None:
    for url in ("https://publisher.example/guides/forum-about-widows", "https://weekly-forum.example/news/42"):
        row = classify_observation(forum_observation(url=url, markdown="Editorial article. " * 30))
        assert row["verification_status"] == "rejected"
        assert row["eligible_for_targeted_collection"] is False


def test_one_generic_token_and_wrong_segment_do_not_verify_customer_fit() -> None:
    row = classify_observation(
        forum_observation(url="https://vendor.example/forum/support", title="Support forum", description="Product support community", markdown="Support forum member post reply. " * 20),
        topic="small business tax filing", keywords="tax filing", segment="independent restaurant owners",
    )
    assert row["verification_status"] == "rejected"
    assert row["customer_segment_fit"] == "unverified"
    assert row["eligible_for_recruitment_review"] is False


def test_source_shape_is_not_customer_or_recruitment_verification() -> None:
    row = classify_observation(forum_observation())
    assert row["verification_status"] == "source_shape_verified"
    assert row["community_shape"] == "verified"
    assert row["customer_segment_fit"] == "unverified"
    assert row["geography_fit"] == "unverified"
    assert row["language_fit"] == "unverified"
    assert row["eligible_for_recruitment_review"] is False
    assert row["voice_status"] == "firsthand_signal_requires_review"
    assert "voice_excerpts" not in row


def test_archived_forum_and_explicit_sensitivity_still_require_manual_source_review() -> None:
    archived = classify_observation(forum_observation(markdown="Read-only archive. Widow navigation topic reply. " * 20))
    sensitive = classify_observation(forum_observation(), topic="bereavement navigation", keywords="widow navigation", sensitivity="sensitive")
    assert archived["activity_status"] == "inactive_archive"
    assert archived["eligible_for_targeted_collection"] is False
    assert sensitive["sensitivity"] == "sensitive"
    assert sensitive["capture_gate"]["status"] == "manual_source_review_required"
    assert sensitive["eligible_for_targeted_collection"] is False


def test_facebook_indexing_never_implies_access_or_recruitment() -> None:
    for url, expected_type in (("https://facebook.com/groups/widowsupport/posts/44", "facebook_group"), ("https://facebook.com/some-slug/posts/9", "facebook_entity_candidate")):
        row = classify_observation(forum_observation(url=url, markdown="", description="Widow navigation community"))
        assert row["community_type"] == expected_type
        assert row["verification_status"] == "indexed_candidate"
        assert row["public_access"] == "unverified"
        assert row["capture_gate"]["public_or_legitimately_accessible_route"] == "unverified"
        assert row["capture_gate"]["no_credential_or_technical_bypass"] == "required"
        assert row["capture_gate"]["status"] == "manual_source_review_required"
        assert row["eligible_for_recruitment_review"] is False


def test_canonical_key_preserves_distinct_original_observation_locators() -> None:
    candidates = {}
    communities.add_observation(candidates, forum_observation(url="https://m.facebook.com/groups/123/posts/9?utm_source=x", result_rank=1))
    communities.add_observation(candidates, forum_observation(url="https://www.facebook.com/groups/123/posts/10?fbclid=y", result_rank=2))
    assert list(candidates) == ["https://facebook.com/groups/123"]
    originals = {source["original_url"] for source in next(iter(candidates.values()))["sources"]}
    assert len(originals) == 2
    assert all(source["result_rank"] in {1, 2} for source in next(iter(candidates.values()))["sources"])
    assert communities.canonical_url("https://shia-forum.example/index.php?/topic/44/#reply") == "https://shia-forum.example/index.php?/topic/44/"


def test_classified_output_retains_digest_and_status_not_copied_personal_text() -> None:
    secret_text = "Jane Doe @janedoe jane@example.com +41 79 123 45 67 has a medical diagnosis and lives at 12 Exact Street."
    row = classify_observation(forum_observation(title=secret_text, description=secret_text, markdown=(secret_text + " Widow navigation forum post reply. I need help. ") * 8))
    payload = json.dumps(row)
    for value in ("Jane Doe", "@janedoe", "jane@example.com", "+41 79", "Exact Street", "medical diagnosis"):
        assert value not in payload
    assert row["exact_text_retained"] is False
    assert len(row["content_digest"]) == 64
    assert row["retention_review_due"]
    assert row["deleted_or_private"] == "unverified"


def test_offline_run_writes_metadata_only_auditable_outputs(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "fixture.json"; output = tmp_path / "run"
    personal = "Jane Doe jane@example.com +41 79 123 45 67 at 12 Exact Street"
    fixture.write_text(json.dumps({"results": [forum_observation(markdown=(personal + " Widow navigation topic post reply. I need help. ") * 8), forum_observation(provider="serper_search", url="https://facebook.com/groups/widowsupport/posts/44", markdown="", description="Widow navigation Facebook group")]}), encoding="utf-8")
    monkeypatch.setenv("COMMUNITY_DISCOVERY_PRIVATE_KEY_B64", DISCOVERY_PRIVATE)
    monkeypatch.setattr(sys, "argv", ["discover_communities.py", "--topic", "widow navigation", "--customer-segment", "recently widowed adults", "--community-keywords", "widow navigation", "--seed-language", "en", "--locale", "GB:en", "--sensitivity", "sensitive", "--fixture-results-json", str(fixture), "--out-dir", str(output)])
    assert communities.main() == 0
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    candidates = json.loads((output / "review_candidates.json").read_text(encoding="utf-8"))
    all_output = "\n".join(path.read_text(encoding="utf-8") for path in output.iterdir() if path.is_file())
    assert summary["raw_user_text_retained"] is False
    assert summary["paid_api_spend_authorization"] == "standing_authorized_no_cap"
    assert summary["capture_review_status"] == "not_run"
    assert summary["source_shape_verified_count"] == 1
    assert {row["verification_status"] for row in candidates} == {"source_shape_verified", "indexed_candidate"}
    for value in ("Jane Doe", "jane@example.com", "+41 79", "Exact Street"):
        assert value not in all_output
    assert "verified_communities.json" not in summary["outputs"]
    for name in ("community_candidates.json", "review_candidates.json", "community_discovery_receipt.json", "rejected_candidates.json", "report.md", "research_plan.md", "raw.json", "run-manifest.json"):
        assert (output / name).is_file()


def accepted_decision(candidate: dict, *, private: bool = False, reviewed_at: datetime | None = None) -> dict:
    reviewed_at = reviewed_at or datetime.now(timezone.utc).replace(microsecond=0)
    valid_until = reviewed_at + timedelta(days=7)
    url = candidate["url"]
    locator = candidate["sources"][0]["original_url"]
    source_digest = candidate["sources"][0]["content_digest"]
    observed_at = candidate["sources"][0]["fetched_at"]
    dimensions = {}
    for name, status in reviews.REQUIRED_DIMENSIONS.items():
        dimensions[name] = {"status": status, "locator": locator, "observed_at": observed_at, "content_digest": source_digest, "note": f"Reviewed {name}."}
    dimensions["public_access"] = {"status": "legitimate_member_access" if private else "public", "locator": locator, "observed_at": observed_at, "content_digest": source_digest, "note": "Access route checked."}
    return {
        "url": url, "status": "accepted", "reviewer": "analyst-1", "reviewed_at": reviewed_at.isoformat(),
        "valid_until": valid_until.isoformat(), "reason": "Audience and current activity checked at the source.",
        "candidate_digest": candidate["content_digest"], "research_use": "internal", "dimensions": dimensions,
        "access": {"method": "user_supplied_legitimate_access" if private else "paid_public_api", "no_credential_or_technical_bypass": True},
        "ownership_cluster": "community-owner-1", "independence_status": "shared_or_unknown",
        "verified_entity_type": "facebook_group" if candidate["community_type"] == "facebook_group" else "facebook_page" if candidate["community_type"] == "facebook_entity_candidate" else "forum",
        "reviewed_locale_ids": [next((lane["locale_id"] for lane in candidate.get("lane_assessments", []) if lane.get("qualified")), f"{candidate['sources'][0]['country']}:{candidate['sources'][0]['language']}")],
    }


def discovery_audit() -> dict:
    plan = {"query_id": "GB:en:forum:s1", "query": "widow navigation forum", "kind": "forum", "country": "GB", "language": "en"}
    observation = {"query_id": plan["query_id"], "status": "ok", "http_status": 200}
    outcome = {"status": "ok", "result_count": 1, "result_counts_by_query": {plan["query_id"]: 1}, "executed_queries": [plan["query_id"]], "skipped_queries": []}
    return {"collector_version": "community-discovery-v2", "query_plan": [plan], "requested_providers": ["serper_search"], "provider_outcomes": {"serper_search": outcome}, "serper_search": [observation], "raw_content_retained": False}


def signed_recheck(candidate: dict, observed_at: str | None = None) -> dict:
    observed_at = observed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    entity = "facebook_group" if candidate["community_type"] == "facebook_group" else "facebook_page" if candidate["community_type"] == "facebook_entity_candidate" else "forum"
    receipt = {"artifact_type": "community_direct_recheck", "schema_version": 2, "recheck_id": "12345678-1234-4234-8234-123456789abc", "url": candidate["url"], "locator": candidate["sources"][0]["original_url"], "final_url": candidate["url"], "entity_type": entity, "provider": "direct_http", "http_status": 200, "status": "retrieved", "observed_at": observed_at, "content_digest": "a" * 64, "response_body_retained": False, "content_type": "text/html", "body_size_bytes": 1000, "access_status": "public_content", "entity_type_observed": entity, "activity_status": "active_recent", "semantic_markers": ["interaction", "recent_time"], "signature_algorithm": "ed25519", "key_id": reviews.public_key_id(DISCOVERY_PRIVATE)}
    receipt["signature"] = reviews.sign(receipt, DISCOVERY_PRIVATE)
    return receipt


def packet_with_rechecks(candidates: list[dict], decisions: list[dict]) -> tuple[dict, set[str]]:
    receipts = []
    for candidate, decision in zip(candidates, decisions):
        if decision.get("access", {}).get("method") not in reviews.PUBLIC_METHODS:
            continue
        receipt = signed_recheck(candidate)
        for name in ("community_shape", "activity_status", "public_access"):
            decision["dimensions"][name].update(locator=receipt["locator"], observed_at=receipt["observed_at"], content_digest=receipt["content_digest"])
        receipts.append(receipt)
    return {"decisions": decisions, "known_misses": [], "query_adjustments": [], "direct_rechecks": receipts}, {row["signature"] for row in receipts}


def test_review_stage_does_not_promote_until_every_dimension_passes() -> None:
    candidate = classify_observation(forum_observation())
    no_decision = reviews.review([candidate], {"decisions": []})
    bad = accepted_decision(candidate); bad["dimensions"]["geography_fit"]["status"] = "unverified"
    rejected = reviews.review([candidate], {"decisions": [bad]})
    packet, trusted = packet_with_rechecks([candidate], [accepted_decision(candidate)])
    accepted = reviews.review([candidate], packet, trusted_rechecks=trusted)
    assert not no_decision["verified"]
    assert not rejected["verified"] and "geography_fit.status must be matched" in rejected["review_log"][0]["errors"]
    assert accepted["verified"][0]["eligible_for_targeted_collection"] is True
    assert accepted["authorization"]["status"] == "no_public_api_targets"
    assert accepted["metrics"]["decision_acceptance_rate"] == 1.0
    assert accepted["metrics"]["precision"] is None and accepted["metrics"]["recall"] is None
    assert accepted["metrics"]["independent_customer_observation_count"] is None


def test_search_index_observation_alone_cannot_authorize_public_capture() -> None:
    candidate = classify_observation(forum_observation(url="https://facebook.com/groups/allowed", markdown="", query_kind="facebook_group", kind="facebook_group"))
    result = reviews.review([candidate], {"decisions": [accepted_decision(candidate)], "known_misses": [], "query_adjustments": []})
    assert not result["verified"]
    assert "signed direct target recheck" in " ".join(result["review_log"][0]["errors"])


def test_review_stage_records_changed_and_unobserved_prior_sources() -> None:
    current = classify_observation(forum_observation())
    prior = [{"url": current["url"], "content_digest": "old"}, {"url": "https://forum.example/missing", "content_digest": "x"}]
    result = reviews.review([current], {"decisions": []}, prior)
    statuses = {row["current_status"] for row in result["lifecycle"]}
    assert statuses == {"changed_since_capture", "not_observed_in_rerun"}
    assert any(row["action"] == "direct_recheck_required" for row in result["lifecycle"])


def test_review_command_writes_verified_authorization_metrics_and_lifecycle(tmp_path: Path, monkeypatch) -> None:
    candidate = classify_observation(forum_observation()); candidates = tmp_path / "candidates.json"; discovery_receipt = tmp_path / "discovery-receipt.json"; decisions = tmp_path / "decisions.json"; output = tmp_path / "review"
    candidates.write_text(json.dumps([candidate]), encoding="utf-8")
    audit = tmp_path / "audit.json"; audit.write_text(json.dumps(discovery_audit()))
    discovery_receipt.write_text(json.dumps(communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)), encoding="utf-8")
    packet, _ = packet_with_rechecks([candidate], [accepted_decision(candidate)]); packet["known_misses"] = [{"locale": "GB:en", "provider": "fixture", "locator": "https://known.example", "note": "Known forum omitted."}]; packet["query_adjustments"] = [{"locale": "GB:en", "provider": "fixture", "change": "added synonym", "reason": "Known-positive miss."}]
    decisions.write_text(json.dumps(packet), encoding="utf-8")
    monkeypatch.setenv("COMMUNITY_REVIEW_PRIVATE_KEY_B64", REVIEW_PRIVATE)
    monkeypatch.setenv("COMMUNITY_DISCOVERY_PUBLIC_KEY_B64", DISCOVERY_PUBLIC)
    monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(discovery_receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(output)])
    assert reviews.main() == 0
    for name in ("verified_communities.json", "capture_authorization.json", "community_review_current.json", "community_review_log.json", "community_review_metrics.json", "community_lifecycle.json"):
        assert (output / name).is_file()
    metrics = json.loads((output / "community_review_metrics.json").read_text(encoding="utf-8"))
    assert metrics["by_locale"]["GB:en"]["accepted_source_memberships"] == 1
    assert metrics["known_misses"] and metrics["query_adjustments"]


def test_discovery_receipt_lineage_is_stable_while_run_id_changes() -> None:
    candidate = classify_observation(forum_observation())
    first = communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)
    second = communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)
    assert first["discovery_run_id"] != second["discovery_run_id"]
    assert first["review_lineage_id"] == second["review_lineage_id"]


def test_tampered_discovery_audit_is_rejected() -> None:
    candidate = classify_observation(forum_observation())
    receipt = communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)
    errors = reviews.validate_discovery([candidate], receipt, {**discovery_audit(), "query_plan": [{"forged": True}]}, DISCOVERY_PUBLIC)
    assert "audit digest" in " ".join(errors)


def test_correctly_signed_but_incomplete_discovery_audit_is_rejected() -> None:
    candidate = classify_observation(forum_observation()); audit = discovery_audit()
    audit["provider_outcomes"]["serper_search"] = {"status": "ok", "result_count": 0, "result_counts_by_query": {}, "executed_queries": [], "skipped_queries": []}
    audit["serper_search"] = []
    receipt = communities.signed_discovery_receipt([candidate], audit, DISCOVERY_PRIVATE)
    errors = reviews.validate_discovery([candidate], receipt, audit, DISCOVERY_PUBLIC)
    assert "account for every planned query" in " ".join(errors)


def test_facebook_collector_fails_before_http_without_fresh_matching_review(tmp_path: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(collector, "http_get", lambda *args, **kwargs: calls.append(args) or {"ok": True, "body": {"creditCount": 10}})
    base = argparse.Namespace(fb_groups="https://facebook.com/groups/allowed", fb_pages="", community_capture_authorization="", community_verified_sources="", community_review_receipt="")
    records, summary = collector.collect_scrapecreators(base, [], tmp_path)
    assert not records and summary["status"] == "capture_gate_blocked" and not calls
    authorization = tmp_path / "auth.json"; verified = tmp_path / "verified.json"
    authorization.write_text(json.dumps({"status": "valid", "purpose": "internal_voice_of_customer_research", "valid_until": "2099-01-01T00:00:00+00:00", "authorized_urls": ["https://facebook.com/groups/allowed"], "no_credential_or_technical_bypass": True}), encoding="utf-8")
    verified.write_text("[]", encoding="utf-8")
    base.community_capture_authorization = str(authorization)
    base.community_verified_sources = str(verified)
    records, summary = collector.collect_scrapecreators(base, [], tmp_path)
    assert not records and summary["status"] == "capture_gate_blocked" and not calls


def test_requested_facebook_failure_is_not_hidden_by_unrelated_social_records(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *names: (names[0], "key"))
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 20}}
        if "tiktok" in url: return {"ok": True, "status_code": 200, "body": {"items": [{"id": "1", "text": "Estate paperwork help is difficult", "url": "https://tiktok.example/1"}]}}
        if "facebook/group/posts" in url: return {"ok": False, "status_code": 404, "body": {"error": "not accessible"}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    args = argparse.Namespace(topic="estate paperwork", problem_keywords="paperwork", workaround_keywords="help", geo="GB", language="en", social_per_endpoint=1, fb_max_posts=3, x_handles="", fb_groups="https://facebook.com/groups/allowed", fb_pages="", ig_handles="", ig_hashtags="", social_comments=True, comments_max=3, customer_segment="families", hypothesis_id="H1")
    records, summary = collector.collect_scrapecreators(args, [], tmp_path)
    assert records and summary["status"] == "partial"
    assert summary["coverage_alerts"] and any("fb-group" in item for item in summary["coverage_alerts"])
    assert summary["endpoint_statuses"]["ScrapeCreators fb-group:https://facebook.com/groups/allowed"].startswith("http_404:")
    assert summary["endpoint_statuses"]["ScrapeCreators fb-comments"] == "not_attempted:no_accessible_posts"


def test_comment_ledger_preserves_each_expected_request_after_credit_exhaustion(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *names: (names[0], "key"))
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 20}}
        if "facebook/group/posts" in url:
            return {"ok": True, "status_code": 200, "body": {"posts": [
                {"id": "p1", "text": "Estate paperwork is difficult", "url": "https://facebook.com/posts/p1"},
                {"id": "p2", "text": "Estate paperwork needs help", "url": "https://facebook.com/posts/p2"},
            ]}}
        if "facebook/post/comments" in url: return {"ok": False, "status_code": 402, "body": {"error": "insufficient credits"}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    args = argparse.Namespace(topic="estate paperwork", problem_keywords="paperwork", workaround_keywords="help", geo="GB", language="en", social_per_endpoint=1, fb_max_posts=3, x_handles="", fb_groups="https://facebook.com/groups/allowed", fb_pages="", ig_handles="", ig_hashtags="", social_comments=True, comments_max=3, customer_segment="families", hypothesis_id="H1")
    records, summary = collector.collect_scrapecreators(args, [], tmp_path)
    assert summary["status"] == "insufficient_credits"
    assert len(summary["comment_request_ledger"]) == 2
    assert summary["comment_request_ledger"][0]["attempted"] is True
    assert summary["comment_request_ledger"][1]["status"] == "skipped:insufficient_credits"


def test_facebook_comment_lane_gets_priority_over_generic_instagram_when_cap_is_one(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(collector, "validate_facebook_capture_authorization", lambda _args: (True, "authorized", {}))
    monkeypatch.setattr(collector, "get_secret", lambda *names: (names[0], "key"))
    def fake_get(url, **_kwargs):
        if "credit-balance" in url: return {"ok": True, "status_code": 200, "body": {"creditCount": 20}}
        if "instagram/reels/search" in url: return {"ok": True, "status_code": 200, "body": {"items": [{"id": "i1", "text": "Paperwork help", "url": "https://instagram.com/p/i1"}]}}
        if "facebook/group/posts" in url: return {"ok": True, "status_code": 200, "body": {"posts": [{"id": "f1", "text": "Paperwork help", "url": "https://facebook.com/posts/f1"}]}}
        if "facebook/post/comments" in url: return {"ok": True, "status_code": 200, "body": {"comments": [{"id": "c1", "text": "I used this after a death"}]}}
        return {"ok": True, "status_code": 200, "body": {"items": []}}
    monkeypatch.setattr(collector, "http_get", fake_get)
    args = argparse.Namespace(topic="paperwork", problem_keywords="paperwork", workaround_keywords="help", geo="GB", language="en", social_per_endpoint=1, fb_max_posts=3, x_handles="", fb_groups="https://facebook.com/groups/allowed", fb_pages="", ig_handles="", ig_hashtags="", social_comments=True, comments_max=1, customer_segment="families", hypothesis_id="H1")
    records, summary = collector.collect_scrapecreators(args, [], tmp_path)
    facebook = [row for row in summary["comment_request_ledger"] if row["source"] == "facebook"]
    instagram = [row for row in summary["comment_request_ledger"] if row["source"] == "instagram"]
    assert facebook[0]["attempted"] is True
    assert instagram[0]["status"] == "skipped:comments_max"
    assert any(row.get("source_entity_type") == "facebook_comment" and "used this" in row.get("text", "") for row in records)


def generated_capture_files(tmp_path: Path, *, private: bool = False, reviewed_at: datetime | None = None):
    candidate = classify_observation(forum_observation(url="https://facebook.com/groups/allowed", markdown="", description="Widow navigation group", query_kind="facebook_group", kind="facebook_group"))
    packet, trusted = packet_with_rechecks([candidate], [accepted_decision(candidate, private=private, reviewed_at=reviewed_at)])
    result = reviews.review([candidate], packet, trusted_rechecks=trusted)
    auth, verified, receipt = tmp_path / "auth.json", tmp_path / "verified.json", tmp_path / "receipt.json"
    auth.write_text(json.dumps(result["authorization"]), encoding="utf-8"); verified.write_text(json.dumps(result["verified"]), encoding="utf-8"); receipt.write_text(json.dumps(result["receipt"]), encoding="utf-8")
    state = tmp_path / "state"; state.mkdir(exist_ok=True); (state / "unit-test-state.json").write_text(json.dumps(result["receipt"]), encoding="utf-8")
    return candidate, result, auth, verified, receipt


def test_facebook_authorization_accepts_only_fresh_digest_bound_public_target(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PUBLIC_KEY_B64", REVIEW_PUBLIC)
    monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    _, _, auth, verified, receipt = generated_capture_files(tmp_path)
    args = argparse.Namespace(fb_groups="https://facebook.com/groups/allowed/", fb_pages="", community_capture_authorization=str(auth), community_verified_sources=str(verified), community_review_receipt=str(receipt), geo="GB", language="en")
    allowed, reason, audit = collector.validate_facebook_capture_authorization(args)
    assert allowed is True and reason == "authorized" and all(audit["checks"].values())
    args.geo = "FR"; args.language = "fr"
    assert collector.validate_facebook_capture_authorization(args)[0] is False
    args.geo = "GB"; args.language = "en"
    rows = json.loads(verified.read_text()); rows[0]["content_digest"] = "0" * 64; verified.write_text(json.dumps(rows))
    assert collector.validate_facebook_capture_authorization(args)[0] is False


def test_private_user_supplied_source_never_enters_facebook_api_allowlist(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PUBLIC_KEY_B64", REVIEW_PUBLIC)
    monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    _, result, auth, verified, receipt = generated_capture_files(tmp_path, private=True)
    assert not result["authorization"]["targets"] and result["user_supplied"]
    args = argparse.Namespace(fb_groups="https://facebook.com/groups/allowed", fb_pages="", community_capture_authorization=str(auth), community_verified_sources=str(verified), community_review_receipt=str(receipt))
    assert collector.validate_facebook_capture_authorization(args)[0] is False


def test_review_rejects_future_or_overlong_authorization() -> None:
    candidate = classify_observation(forum_observation())
    future = accepted_decision(candidate, reviewed_at=datetime.now(timezone.utc) + timedelta(days=1))
    overlong = accepted_decision(candidate); overlong["valid_until"] = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    assert "future" in " ".join(reviews.review([candidate], {"decisions": [future]})["review_log"][0]["errors"])
    assert "maximum TTL" in " ".join(reviews.review([candidate], {"decisions": [overlong]})["review_log"][0]["errors"])


def test_locale_coverage_uses_qualified_lane_not_a_match_from_another_locale() -> None:
    candidates = {}
    communities.add_observation(candidates, forum_observation(seed="widow navigation", locale_id="GB:en"))
    communities.add_observation(candidates, forum_observation(country="FR", language="fr", locale_id="FR:fr", seed="aide veuvage", title="Unrelated directory", description="Business listings", markdown="Directory listing. " * 20))
    row = communities.classify(next(iter(candidates.values())), "widow navigation", "", "recently widowed adults", "standard")
    lanes = {lane["locale_id"]: lane["qualified"] for lane in row["lane_assessments"]}
    assert lanes == {"GB:en": True, "FR:fr": False}


def test_review_metrics_keep_unreviewed_qualified_locale_candidate_membership() -> None:
    candidates = {}
    communities.add_observation(candidates, forum_observation(seed="widow navigation", locale_id="GB:en"))
    communities.add_observation(candidates, forum_observation(country="FR", language="fr", locale_id="FR:fr", seed="aide veuvage", title="Aide veuvage", description="Forum aide veuvage discussion", markdown="Forum aide veuvage membre discussion réponse. " * 20))
    candidate = communities.classify(next(iter(candidates.values())), "widow navigation", "", "recently widowed adults", "standard")
    decision = accepted_decision(candidate); decision["reviewed_locale_ids"] = ["GB:en"]
    packet, trusted = packet_with_rechecks([candidate], [decision])
    result = reviews.review([candidate], packet, trusted_rechecks=trusted)
    assert result["metrics"]["by_locale"]["FR:fr"] == {"candidate_source_memberships": 1, "reviewed_source_memberships": 0, "accepted_source_memberships": 0}


def test_rejected_candidate_counts_as_reviewed_in_each_qualified_locale() -> None:
    candidate = classify_observation(forum_observation(seed="widow navigation", locale_id="GB:en"))
    packet = {"decisions": [{"url": candidate["url"], "status": "rejected", "reason": "Supplier-run source, not a peer community."}], "known_misses": [], "query_adjustments": []}
    result = reviews.review([candidate], packet)
    assert result["metrics"]["by_locale"]["GB:en"] == {"candidate_source_memberships": 1, "reviewed_source_memberships": 1, "accepted_source_memberships": 0}


def test_review_rejects_stale_dimension_and_shared_cluster_distinct_claim() -> None:
    first = classify_observation(forum_observation())
    second = classify_observation(forum_observation(url="https://second.example/forum/widow-navigation"))
    old = accepted_decision(first); old["dimensions"]["activity_status"]["observed_at"] = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    assert "stale" in " ".join(reviews.review([first], {"decisions": [old]})["review_log"][0]["errors"])
    decisions = [accepted_decision(first), accepted_decision(second)]
    for decision in decisions: decision["independence_status"] = "distinct_source"
    packet, trusted = packet_with_rechecks([first, second], decisions)
    result = reviews.review([first, second], packet, trusted_rechecks=trusted)
    assert not result["verified"]
    assert all("ownership_cluster" in row["reason"] for row in result["review_log"])


def test_tampered_or_wrong_endpoint_signed_bundle_is_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PUBLIC_KEY_B64", REVIEW_PUBLIC)
    monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    _, _, auth, verified, receipt = generated_capture_files(tmp_path)
    args = argparse.Namespace(fb_groups="", fb_pages="https://facebook.com/groups/allowed", community_capture_authorization=str(auth), community_verified_sources=str(verified), community_review_receipt=str(receipt))
    assert collector.validate_facebook_capture_authorization(args)[0] is False
    args.fb_groups, args.fb_pages = "https://facebook.com/groups/allowed", ""
    packet = json.loads(auth.read_text()); packet["targets"][0]["reviewer"] = "forged"; auth.write_text(json.dumps(packet))
    assert collector.validate_facebook_capture_authorization(args)[0] is False


def test_duplicate_group_page_target_is_rejected_before_http(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PUBLIC_KEY_B64", REVIEW_PUBLIC); monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    _, _, auth, verified, receipt = generated_capture_files(tmp_path)
    args = argparse.Namespace(fb_groups="https://facebook.com/groups/allowed", fb_pages="https://facebook.com/groups/allowed", community_capture_authorization=str(auth), community_verified_sources=str(verified), community_review_receipt=str(receipt))
    assert collector.validate_facebook_capture_authorization(args)[0] is False


def test_review_cli_rejects_candidates_not_bound_to_discovery_receipt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PRIVATE_KEY_B64", REVIEW_PRIVATE); monkeypatch.setenv("COMMUNITY_DISCOVERY_PUBLIC_KEY_B64", DISCOVERY_PUBLIC); monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    original = classify_observation(forum_observation()); forged = dict(original); forged["url"] = "https://facebook.com/groups/forged"; forged["community_type"] = "facebook_group"
    candidates = tmp_path / "candidates.json"; receipt = tmp_path / "receipt.json"; decisions = tmp_path / "decisions.json"; out = tmp_path / "out"
    audit = tmp_path / "audit.json"; audit.write_text(json.dumps(discovery_audit()))
    candidates.write_text(json.dumps([forged])); receipt.write_text(json.dumps(communities.signed_discovery_receipt([original], discovery_audit(), DISCOVERY_PRIVATE))); decisions.write_text(json.dumps({"decisions": [], "known_misses": [], "query_adjustments": []}))
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(out)])
    assert reviews.main() == 2
    assert json.loads((out / "community_review_current.json").read_text())["status"] == "revoked_invalid_packet"


def test_old_source_timestamp_cannot_be_laundered_as_current() -> None:
    candidate = classify_observation(forum_observation(fetched_at=(datetime.now(timezone.utc) - timedelta(days=120)).isoformat()))
    decision = accepted_decision(candidate)
    for record in decision["dimensions"].values(): record["observed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = reviews.review([candidate], {"decisions": [decision], "known_misses": [], "query_adjustments": []})
    assert not result["verified"]
    assert "immutable retrieval record" in " ".join(result["review_log"][0]["errors"])


def test_packet_recheck_cannot_launder_signed_source_locator_for_public_api() -> None:
    fetched = (datetime.now(timezone.utc) - timedelta(days=20)).replace(microsecond=0).isoformat()
    candidate = classify_observation(forum_observation(url="https://facebook.com/groups/allowed", markdown="", fetched_at=fetched, query_kind="facebook_group", kind="facebook_group"))
    decision = accepted_decision(candidate); fresh = datetime.now(timezone.utc).replace(microsecond=0).isoformat(); invented = "f" * 64
    for name in ("activity_status", "public_access"):
        decision["dimensions"][name].update(observed_at=fresh, content_digest=invented)
    packet = {"decisions": [decision], "known_misses": [], "query_adjustments": [], "direct_rechecks": [{"url": candidate["url"], "locator": candidate["sources"][0]["original_url"], "observed_at": fresh, "status": "retrieved", "content_digest": invented, "note": "Packet-authored recheck."}]}
    result = reviews.review([candidate], packet)
    assert not result["verified"]
    assert "signed direct target recheck" in " ".join(result["review_log"][0]["errors"])


def test_valid_signed_direct_recheck_can_refresh_activity_and_public_access() -> None:
    fetched = (datetime.now(timezone.utc) - timedelta(days=20)).replace(microsecond=0).isoformat()
    candidate = classify_observation(forum_observation(url="https://facebook.com/groups/allowed", markdown="", fetched_at=fetched, query_kind="facebook_group", kind="facebook_group"))
    fresh = datetime.now(timezone.utc).replace(microsecond=0).isoformat(); digest = "a" * 64
    receipt = {
        "artifact_type": "community_direct_recheck", "schema_version": 2,
        "recheck_id": "12345678-1234-4234-8234-123456789abc",
        "url": candidate["url"], "locator": candidate["sources"][0]["original_url"],
        "final_url": candidate["url"], "entity_type": "facebook_group",
        "provider": "direct_http", "http_status": 200, "status": "retrieved",
        "observed_at": fresh, "content_digest": digest, "response_body_retained": False,
        "content_type": "text/html", "body_size_bytes": 1000, "access_status": "public_content",
        "entity_type_observed": "facebook_group", "activity_status": "active_recent", "semantic_markers": ["interaction", "recent_time"],
        "signature_algorithm": "ed25519",
        "key_id": reviews.public_key_id(DISCOVERY_PRIVATE),
    }
    receipt["signature"] = reviews.sign(receipt, DISCOVERY_PRIVATE)
    decision = accepted_decision(candidate)
    for name in ("community_shape", "activity_status", "public_access"):
        decision["dimensions"][name].update(locator=receipt["locator"], observed_at=fresh, content_digest=digest)
    packet = {"decisions": [decision], "known_misses": [], "query_adjustments": [], "direct_rechecks": [receipt]}
    errors, trusted = reviews.validate_direct_rechecks(packet, DISCOVERY_PUBLIC)
    assert not errors and receipt["signature"] in trusted
    result = reviews.review([candidate], packet, trusted_rechecks=trusted)
    assert len(result["verified"]) == 1


def test_direct_recheck_receipt_records_actual_redirect_and_retains_no_body(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_DISCOVERY_PRIVATE_KEY_B64", DISCOVERY_PRIVATE)
    monkeypatch.setattr(rechecks, "http_get", lambda _url: {"ok": True, "status_code": 200, "final_url": "https://example.org/final", "body": {"text": "not persisted"}})
    output = tmp_path / "recheck.json"
    monkeypatch.setattr(sys, "argv", ["recheck_community_source.py", "--url", "https://example.org/start", "--entity-type", "forum", "--out", str(output)])
    assert rechecks.main() == 1
    receipt = json.loads(output.read_text())
    assert receipt["final_url"] == "https://example.org/final"
    assert receipt["response_body_retained"] is False
    assert "not persisted" not in output.read_text()
    errors, trusted = reviews.validate_direct_rechecks({"direct_rechecks": [receipt]}, DISCOVERY_PUBLIC)
    assert errors and not trusted


def test_review_cli_cannot_verify_discovery_with_a_private_signing_key(tmp_path: Path, monkeypatch) -> None:
    candidate = classify_observation(forum_observation()); candidates = tmp_path / "candidates.json"; receipt = tmp_path / "receipt.json"; audit = tmp_path / "audit.json"; decisions = tmp_path / "decisions.json"; out = tmp_path / "out"
    audit.write_text(json.dumps(discovery_audit())); candidates.write_text(json.dumps([candidate])); receipt.write_text(json.dumps(communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE))); decisions.write_text(json.dumps({"decisions": [], "known_misses": [], "query_adjustments": []}))
    monkeypatch.setenv("COMMUNITY_DISCOVERY_PUBLIC_KEY_B64", DISCOVERY_PRIVATE); monkeypatch.setenv("COMMUNITY_REVIEW_PRIVATE_KEY_B64", REVIEW_PRIVATE); monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(out)])
    assert reviews.main() == 2


def test_review_cli_rejects_same_keypair_for_both_roles(tmp_path: Path, monkeypatch) -> None:
    candidate = classify_observation(forum_observation()); candidates = tmp_path / "candidates.json"; receipt = tmp_path / "receipt.json"; audit = tmp_path / "audit.json"; decisions = tmp_path / "decisions.json"; out = tmp_path / "out"
    audit.write_text(json.dumps(discovery_audit())); candidates.write_text(json.dumps([candidate])); receipt.write_text(json.dumps(communities.signed_discovery_receipt([candidate], discovery_audit(), REVIEW_PRIVATE))); decisions.write_text(json.dumps({"decisions": [], "known_misses": [], "query_adjustments": []}))
    monkeypatch.setenv("COMMUNITY_DISCOVERY_PUBLIC_KEY_B64", REVIEW_PUBLIC); monkeypatch.setenv("COMMUNITY_REVIEW_PRIVATE_KEY_B64", REVIEW_PRIVATE); monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(out)])
    assert reviews.main() == 2
    for artifact, schema_name in (("capture_authorization.json", "community-capture-authorization.schema.json"), ("community_review_current.json", "community-review-receipt.schema.json")):
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / schema_name).read_text())
        assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(json.loads((out / artifact).read_text())))


def test_invalid_rereview_revokes_previous_generation_before_http(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PRIVATE_KEY_B64", REVIEW_PRIVATE)
    monkeypatch.setenv("COMMUNITY_DISCOVERY_PUBLIC_KEY_B64", DISCOVERY_PUBLIC)
    monkeypatch.setenv("COMMUNITY_REVIEW_PUBLIC_KEY_B64", REVIEW_PUBLIC)
    monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    candidate = classify_observation(forum_observation(url="https://facebook.com/groups/allowed", markdown="", description="Widow navigation group", query_kind="facebook_group", kind="facebook_group"))
    candidates = tmp_path / "candidates.json"; discovery_receipt = tmp_path / "discovery-receipt.json"; audit = tmp_path / "audit.json"; decisions = tmp_path / "decisions.json"; out = tmp_path / "review"
    packet, _ = packet_with_rechecks([candidate], [accepted_decision(candidate)])
    candidates.write_text(json.dumps([candidate])); decisions.write_text(json.dumps(packet)); audit.write_text(json.dumps(discovery_audit()))
    discovery_receipt.write_text(json.dumps(communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)))
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(discovery_receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(out)])
    assert reviews.main() == 0
    old_auth = tmp_path / "old-auth.json"; old_verified = tmp_path / "old-verified.json"; old_receipt = tmp_path / "old-receipt.json"
    old_auth.write_text((out / "capture_authorization.json").read_text()); old_verified.write_text((out / "verified_communities.json").read_text()); old_receipt.write_text((out / "community_review_current.json").read_text())
    decisions.write_text(json.dumps({"decisions": [{"url": candidate["url"], "status": "accepted", "reason": "incomplete"}], "known_misses": [], "query_adjustments": []}))
    second_discovery = communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)
    assert second_discovery["review_lineage_id"] == json.loads(discovery_receipt.read_text())["review_lineage_id"]
    discovery_receipt.write_text(json.dumps(second_discovery))
    revoked_out = tmp_path / "review-another-output"
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(discovery_receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(revoked_out)])
    assert reviews.main() == 2
    current = json.loads((revoked_out / "community_review_current.json").read_text()); assert current["status"] == "revoked_invalid_packet"
    assert current["generation_version"] == 2
    args = argparse.Namespace(fb_groups=candidate["url"], fb_pages="", community_capture_authorization=str(old_auth), community_verified_sources=str(old_verified), community_review_receipt=str(revoked_out / "community_review_current.json"))
    calls = []; monkeypatch.setattr(collector, "http_get", lambda *a, **k: calls.append(a) or {"ok": True})
    records, summary = collector.collect_scrapecreators(args, [], tmp_path / "collection")
    assert not records and summary["status"] == "capture_gate_blocked" and not calls
    args.community_review_receipt = str(old_receipt)
    assert collector.validate_facebook_capture_authorization(args)[0] is False


def test_missing_review_key_cannot_overwrite_authoritative_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMMUNITY_REVIEW_PUBLIC_KEY_B64", REVIEW_PUBLIC); monkeypatch.setenv("COMMUNITY_REVIEW_STATE_DIR", str(tmp_path / "state"))
    candidate = classify_observation(forum_observation(url="https://facebook.com/groups/allowed", markdown="", query_kind="facebook_group", kind="facebook_group"))
    candidates = tmp_path / "candidates.json"; receipt = tmp_path / "discovery.json"; audit = tmp_path / "audit.json"; decisions = tmp_path / "decisions.json"; out = tmp_path / "bad-review"
    discovery_receipt = communities.signed_discovery_receipt([candidate], discovery_audit(), DISCOVERY_PRIVATE)
    candidates.write_text(json.dumps([candidate])); audit.write_text(json.dumps(discovery_audit())); receipt.write_text(json.dumps(discovery_receipt))
    packet, _ = packet_with_rechecks([candidate], [accepted_decision(candidate)]); decisions.write_text(json.dumps(packet))
    trusted = {row["signature"] for row in packet["direct_rechecks"]}; valid = reviews.review([candidate], packet, state_id=discovery_receipt["review_lineage_id"], trusted_rechecks=trusted)
    state_path = tmp_path / "state" / f"{discovery_receipt['review_lineage_id']}.json"; state_path.parent.mkdir(); state_path.write_text(json.dumps(valid["receipt"])); before = state_path.read_bytes()
    monkeypatch.delenv("COMMUNITY_REVIEW_PRIVATE_KEY_B64", raising=False); monkeypatch.setenv("COMMUNITY_DISCOVERY_PUBLIC_KEY_B64", DISCOVERY_PUBLIC)
    monkeypatch.setattr(sys, "argv", ["review_community_candidates.py", "--candidates", str(candidates), "--discovery-receipt", str(receipt), "--discovery-audit", str(audit), "--decisions", str(decisions), "--out-dir", str(out)])
    assert reviews.main() == 2
    assert state_path.read_bytes() == before
