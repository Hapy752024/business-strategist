"""Collection quality checks use synthetic payloads, not live coverage proof."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("voc_collection", ROOT / "scripts/evidence_scout/collect.py")
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def args(**kw):
    values = dict(topic="service", customer_segment="families", hypothesis_id="H1", geo="DE", language="de", limit=20, query_limit=12, sampling_frame="topic_led_voc", segment_keywords="families", problem_keywords="", workaround_keywords="")
    values.update(kw)
    return argparse.Namespace(**values)


def entity_args(tmp_path, **kw):
    url = "https://forum.example.test/thread/123"
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"source_matrix": [{"entity_id": "e1", "locale": "DE:de", "source_lane": "external_forums_communities", "applicable": True, "reviewed_locators": [{"locator": url, "review_reason": "Checked target company, public access and forum discussion."}]}]}))
    values = dict(sampling_frame="entity_led_feedback", subject_entity_id="e1", entity_source_url=url, entity_source_lane="external_forums_communities", customer_feedback_source_plan=str(plan))
    values.update(kw)
    return args(**values)


def test_generic_entity_requires_review_before_http(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "http_post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("unreviewed fetch")))
    records, summary = c.collect_firecrawl(entity_args(tmp_path, entity_source_url="https://other.test/thread"), [], tmp_path)
    assert records == [] and summary["status"] == "capture_gate_blocked"


def test_generic_capture_has_exact_binding_and_full_document(tmp_path, monkeypatch):
    run_args = entity_args(tmp_path)
    content = "speaker 1\n" + "Long background. " * 200 + "\nspeaker 2: successful workaround"
    calls = []
    monkeypatch.setattr(c, "get_secret", lambda *a: (a[0], "fixture-key"))
    monkeypatch.setattr(c, "http_post", lambda url, **kw: calls.append((url, kw["data"])) or {"ok": True, "status_code": 200, "body": {"data": {"markdown": content}}})
    records, summary = c.collect_firecrawl(run_args, ["must not search"], tmp_path)
    record = records[0]
    assert calls[0][0].endswith("/scrape") and calls[0][1]["url"] == run_args.entity_source_url
    assert record["text"] == content and record["capture_unit"] == "document"
    assert record["author_voice_status"] == "unreviewed"
    assert (record["subject_entity_id"], record["collection_locale"], record["collection_source_lane"], record["collection_locator"]) == ("e1", "DE:de", "external_forums_communities", run_args.entity_source_url)
    assert summary["status"] == "ok" and not c.accepted_records(records)[1]


def test_targeted_search_cannot_relabel_broad_results(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "http_post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("broad fetch")))
    assert c.collect_serper_search(entity_args(tmp_path), ["q"], tmp_path)[1]["status"] == "capture_gate_blocked"


def test_redirect_not_accepted_under_original_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "get_secret", lambda *a: (a[0], "fixture-key"))
    monkeypatch.setattr(c, "http_post", lambda *a, **k: {"ok": True, "body": {"data": {"markdown": "customer experience", "metadata": {"sourceURL": "https://unreviewed.test"}}}})
    assert c.collect_firecrawl(entity_args(tmp_path), [], tmp_path)[1]["status"] == "capture_gate_blocked"


def test_intent_schedule_contains_success_nonadoption_and_local_communities():
    queries = c.query_plan("Umzug", "Familien", geo="DE", language="de", segment_keywords="Familien")
    intents = {c.query_intent(q) for q in queries[:8]}
    assert {"successful_alternative", "nonadoption", "switching_exit", "community_discovery", "facebook_discovery"} <= intents
    assert any("Familien" in q for q in queries)
    assert any("Familien" not in q for q in queries)


def test_native_language_queries_do_not_default_to_english_pain_scaffolding():
    for language, topic in (("fr", "déménagement"), ("it", "trasloco"), ("zh", "搬家")):
        queries = c.query_plan(topic, "", language=language, research_mode="discovery")
        assert {"pain", "successful_alternative", "nonadoption", "workaround", "facebook_discovery"} <= {c.query_intent(q) for q in queries[:8]}
        assert not any("complaints" in q or "pain points" in q for q in queries)
    assert c.discovery_query_plan("引越し", language="ja") == ["引越し"]


def test_firecrawl_full_content_and_actual_query_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "get_secret", lambda *a: (a[0], "fixture-key"))
    monkeypatch.setattr(c, "assess_relevance", lambda *a: ("relevant", "fixture", 1))
    content = "context " * 300 + "rare consequential need"
    calls = []
    def post(url, **kw):
        calls.append(kw["data"]["query"])
        return {"ok": True, "status_code": 200, "body": {"data": [{"url": f"https://forum.test/{len(calls)}", "markdown": content}]}}
    monkeypatch.setattr(c, "http_post", post)
    records, summary = c.collect_firecrawl(args(query_limit=2), ["open", "pain complaints", "worked well", "not to use"], tmp_path)
    assert all(r["text"] == content for r in records)
    assert [r["query"] for r in summary["query_ledger"] if r["attempted"]] == calls
    assert len([r for r in summary["query_ledger"] if not r["attempted"]]) == 2


def test_classification_suggestions_distinct_from_supplier_identity():
    fields = dict(source="web_search", source_url="https://local.test/thread", query="q", customer_segment="families", hypothesis="H1", text="Meine Erfahrungen mit dem Makler")
    assert c.normalize_record(**fields)["classification_basis"] == "heuristic"
    supplier = c.normalize_record(**fields, source_role_override="competitor_context", author_voice_status="supplier_context")
    assert supplier["classification_basis"] == "explicit_supplier_identity"


def test_source_url_path_case_cannot_change_reviewed_target(tmp_path):
    assert c.generic_entity_binding(entity_args(tmp_path, entity_source_url="https://forum.example.test/THREAD/123"))[0] == {}


def test_apple_pagination_and_multilingual_scope_are_honest(tmp_path, monkeypatch):
    plan = tmp_path / "apple-plan.json"
    plan.write_text(json.dumps({"source_matrix": [{"entity_id": "e1", "locale": locale, "source_lane": "apple_app_store_reviews", "applicable": True, "reviewed_locators": [{"locator": "123", "review_reason": "verified app"}]} for locale in ("CH:de", "CH:fr")]}))
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        page = 1 if "/page=1/" in url else 2
        return {"ok": True, "body": {"feed": {"entry": [{"id": {"label": str(page)}, "title": {"label": "Erfahrungen"}, "content": {"label": "Die App hilft mir"}, "im:version": {"label": "3.1"}}]}}}
    monkeypatch.setattr(c, "http_get", get)
    monkeypatch.setattr(c, "assess_relevance", lambda *a: ("relevant", "fixture", 1))
    rows, summary = c.collect_itunes_reviews(args(itunes_entity_apps="e1=123", itunes_app_ids="", itunes_locales="CH:de,CH:fr", customer_feedback_source_plan=str(plan), days=30, itunes_max_pages=2), [], tmp_path)
    assert len(calls) == 2 and all(f"/page={page}/" in calls[page-1] for page in (1, 2))
    assert len(rows) == 2 and {r["collection_locale"] for r in rows} == {"CH:und"}
    assert all(r["requested_locales"] == ["CH:de", "CH:fr"] and r["product_version"] == "3.1" for r in rows)
    assert summary["entity_ledger"][0]["language_filter_supported"] is False
