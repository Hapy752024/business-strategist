"""Collection quality checks use synthetic payloads, not live coverage proof."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

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


def test_reddit_discussion_retains_nested_customer_reply_and_incomplete_expansion(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "reddit_token", lambda: ("fixture-token", {"ok": True, "status_code": 200}))
    post = {"kind": "t3", "data": {"id": "p1", "permalink": "/r/test/comments/p1/discussion/",
            "title": "PKV GKV Erfahrungen", "selftext": "How do people decide?", "subreddit": "test",
            "author": "op", "num_comments": 3, "created_utc": 1780000000}}
    child = {"kind": "t1", "data": {"id": "late", "body": "I switched after a claim was denied.",
             "author": "buyer", "parent_id": "t1_first", "created_utc": 1780000000}}
    parent = {"kind": "t1", "data": {"id": "first", "body": "My insurer answered quickly.",
              "author": "other", "replies": {"data": {"children": [child]}}}}
    def get(url, **_kwargs):
        body = [{"data": {"children": [post]}}, {"data": {"children": [parent, {"kind": "more", "data": {"children": ["x"]}}]}}] if "/comments/p1" in url else {"data": {"children": [post]}}
        return {"ok": True, "status_code": 200, "body": body}
    monkeypatch.setattr(c, "http_get", get)
    rows, summary = c.collect_reddit(args(limit=5, days=10000), ["PKV GKV Erfahrungen"], tmp_path)
    reply = next(row for row in rows if row.get("raw_id") == "late")
    assert reply["text"] == "I switched after a claim was denied."
    assert reply["sampling_metadata"]["parent_comment_id"] == "t1_first"
    assert reply["discovery_memberships"][0]["query_id"] == summary["query_ledger"][0]["query_id"]
    assert next(row for row in rows if row.get("raw_id") == "p1")["published_at"].startswith("2026-")
    assert "lc=" not in reply["source_url"] and reply["source_url"].endswith("/late")
    assert summary["comment_request_ledger"][0]["more_unexpanded"] is True


def test_youtube_retains_later_thread_and_reply_with_comment_locators(tmp_path, monkeypatch):
    calls = []
    def get(url, **_kwargs):
        calls.append(url)
        if "/search?" in url:
            body = {"items": [{"id": {"videoId": "v1"}, "snippet": {"title": "Insurance choices", "description": "PKV GKV", "channelTitle": "creator", "publishedAt": "2026-08-01T00:00:00Z"}}]}
        elif "/commentThreads?" in url:
            page_two = "pageToken=second" in url
            body = {"items": [{"id": "t2" if page_two else "t1", "snippet": {
                "topLevelComment": {"id": "later" if page_two else "first", "snippet": {
                    "textOriginal": "I struggled with the switch." if page_two else "Everything worked for us.",
                    "authorDisplayName": "customer", "publishedAt": "2026-09-01T00:00:00Z"}},
                "totalReplyCount": 0 if page_two else 1}}]}
            if not page_two: body["nextPageToken"] = "second"
        else:
            body = {"items": [{"id": "reply", "snippet": {"textOriginal": "My claim was rejected.",
                       "authorDisplayName": "another customer", "publishedAt": "2026-09-02T00:00:00Z"}}]}
        return {"ok": True, "status_code": 200, "body": body}
    monkeypatch.setattr(c, "http_get", get)
    monkeypatch.setattr(c, "get_secret", lambda *names: (names[0], "fixture-key"))
    rows, summary = c._collect_youtube_query(args(limit=2, geo="DE", language="de"), ["PKV GKV"], tmp_path)
    assert {"later", "reply"} <= {row.get("raw_id") for row in rows}
    assert next(row for row in rows if row.get("raw_id") == "reply")["sampling_metadata"]["parent_comment_id"] == "first"
    assert next(row for row in rows if row.get("raw_id") == "later")["source_url"].endswith("&lc=later")
    assert next(row for row in rows if row.get("raw_id") == "v1")["published_at"] == "2026-08-01T00:00:00Z"
    assert any("pageToken=second" in url for url in calls)
    assert summary["status"] == "ok"


def test_classification_suggestions_distinct_from_supplier_identity():
    fields = dict(source="web_search", source_url="https://local.test/thread", query="q", customer_segment="families", hypothesis="H1", text="Meine Erfahrungen mit dem Makler")
    assert c.normalize_record(**fields)["classification_basis"] == "heuristic"
    supplier = c.normalize_record(**fields, source_role_override="competitor_context", author_voice_status="supplier_context")
    assert supplier["classification_basis"] == "explicit_supplier_identity"


def test_public_comment_records_survive_schema_validation():
    reddit = c.normalize_record(source="reddit_comment", source_url="https://www.reddit.com/r/test/comments/p1/topic/c1",
        query="PKV GKV", customer_segment="families", hypothesis="H1", text="I switched after a claim was rejected.",
        author_context="u/customer", raw_id="c1", published_at="2026-09-01T00:00:00Z")
    tiktok = c.normalize_record(source="tiktok", source_url="https://www.tiktok.com/@author/video/123?comment_id=c2",
        query="PKV GKV", customer_segment="families", hypothesis="H1", text="Our family chose GKV.",
        author_context="commenter", raw_id="c2", source_entity_type="tiktok_comment")
    accepted, rejected = c.accepted_records([reddit, tiktok])
    assert len(accepted) == 2 and rejected == []
    assert accepted[0]["source"] == "reddit_comment"
    assert accepted[1]["source_entity_type"] == "tiktok_comment"


def test_reddit_comment_sample_balances_queries_and_deduplicates_crossposts():
    assert c.reddit_opening_signature("PKV-Wechsel vor Kindern? " + "a" * 310) == c.reddit_opening_signature("PKV Wechsel vor Kindern " + "a" * 310 + " edited ending")
    targets = [
        ("a1", "https://reddit.test/a1", {"query_id": "q1"}, "same-opening", 5),
        ("a2", "https://reddit.test/a2", {"query_id": "q1"}, "same-opening", 4),
        ("a3", "https://reddit.test/a3", {"query_id": "q1"}, "other-q1", 3),
        ("b1", "https://reddit.test/b1", {"query_id": "q2"}, "other-q2", 5),
        ("c0", "https://reddit.test/c0", {"query_id": "q3"}, "weak-q3", -1),
        ("c1", "https://reddit.test/c1", {"query_id": "q3"}, "other-q3", 4),
    ]
    selected = c.select_reddit_discussions(targets, 3)
    assert [row[0] for row in selected] == ["a1", "b1", "c1"]
    assert c.select_reddit_discussions(targets, 0) == []


def test_triage_retains_inventory_stockouts_and_general_insurance_claims_but_rejects_finance_noise():
    inventory = c.assess_relevance("We ran out of stock again and had to refund three orders.",
        args(topic="inventory stockouts", problem_keywords="ran out of stock refunds"), "inventory stockouts")
    insurance = c.assess_relevance("My insurer declined my claim after the flood and I paid for repairs myself.",
        args(topic="insurance claims", problem_keywords="claim denied repairs", language="en"), "insurance claims")
    finance = c.assess_relevance("Market rundown: Nvidia earnings beat estimates; ticker rises after results.",
        args(topic="inventory stockouts", problem_keywords="stockouts inventory"), "inventory stockouts")
    assert inventory[0] in {"weak", "relevant"}
    assert insurance[0] in {"weak", "relevant"}
    assert finance[0] == "irrelevant"


def test_reddit_discussion_reserves_one_slot_for_rejected_opening_when_budget_allows():
    targets = [("good1", "u1", {"query_id":"q1"}, "g1", 3),
               ("bad", "u2", {"query_id":"q2"}, "b1", -2),
               ("good2", "u3", {"query_id":"q2"}, "g2", 2)]
    selected = c.select_reddit_discussions(targets, 2)
    assert len(selected) == 2
    assert {row[0] for row in selected} == {"good1", "bad"}


def test_reddit_collector_records_rejected_opening_exploration_and_recovers_reply(tmp_path, monkeypatch):
    now = time.time()
    rows = [{"query_id":"q1", "query":"insurance claims claim rejected", "locale":"DE:de", "scheduled":True,
             "per_query_result_limit":5, "result_urls":[], "record_ids":[], "new_record_count":0}]
    monkeypatch.setattr(c, "provider_query_schedule", lambda *_: rows)
    monkeypatch.setattr(c, "reddit_token", lambda: ("token", {"ok":True, "status_code":200}))
    vague = {"kind":"t3", "data":{"id":"vague", "permalink":"/r/test/comments/vague/any-advice/",
             "title":"Any advice?", "selftext":"", "subreddit":"test", "author":"op", "num_comments":1, "created_utc":now}}
    relevant = {"kind":"t3", "data":{"id":"relevant", "permalink":"/r/test/comments/relevant/claim/",
             "title":"Insurance claim denied after a flood", "selftext":"I paid for repairs myself.",
             "subreddit":"test", "author":"op2", "num_comments":1, "created_utc":now}}
    requests = []
    def get(url, **_kwargs):
        requests.append(url)
        if "/comments/" in url:
            post_id = url.split("/comments/")[1].split("?")[0]
            text = "My insurer denied the claim too, and I had to borrow for repairs." if post_id == "vague" else "We got paid after sending repair photos."
            comment = {"kind":"t1", "data":{"id":"reply-" + post_id, "body":text, "author":"buyer", "parent_id":"t3_" + post_id, "created_utc":now}}
            return {"ok":True, "status_code":200, "body":[{}, {"data":{"children":[comment]}}]}
        return {"ok":True, "status_code":200, "body":{"data":{"children":[vague, relevant]}}}
    monkeypatch.setattr(c, "http_get", get)
    run_args = args(topic="insurance claims", problem_keywords="claim denied policy", language="en",
                    limit=10, days=5000, reddit_comment_posts=2, reddit_comments_per_post=10)
    records, summary = c.collect_reddit(run_args, ["insurance claims claim rejected"], tmp_path)
    ledger = summary["comment_request_ledger"]
    assert {row["sampling_reason"] for row in ledger} == {"rejected_opening_exploration", "query_balanced_relevance"}
    assert all(row["query_id"] == "q1" and row["status"] == "ok" for row in ledger)
    recovered = next(row for row in records if row.get("raw_id") == "reply-vague")
    assert recovered["sampling_metadata"]["parent_post_id"] == "vague"
    assert recovered.get("firsthand") is not True
    assert len([url for url in requests if "/comments/" in url]) == 2


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
