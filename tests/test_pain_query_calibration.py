"""Synthetic execution checks, not evidence of live VOC search quality."""
import argparse
import copy
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/evidence_scout"))
import collect as c


PROVIDERS = ("reddit", "brave_search", "serper_search", "firecrawl")


def plan(provider="brave_search", locale="DE:de", phrases=None):
    phrases = phrases or ["Leistung abgelehnt", "Makler meldet sich nicht", "selbst erledigt zufrieden"]
    return {"schema_version": 1, "revision": "round-1", "queries": [
        {"query_id": f"q{i}", "candidate_id": f"c{i}", "query": phrase, "provider": provider,
         "locale": locale, "intent": "pain" if i < 2 else "successful_alternative",
         "source_family": "local_forums", "seed_origin": "generated"}
        for i, phrase in enumerate(phrases)]}


def args(provider="brave_search", **changes):
    values = dict(topic="service", topic_keywords="", customer_segment="families", hypothesis_id="H1",
                  geo="DE", language="de", limit=6, query_limit=3, results_per_query=2, days=365,
                  problem_keywords="", workaround_keywords="", segment_keywords="Familien",
                  sampling_frame="topic_led_voc", providers=provider, query_plan_data=plan(provider))
    values.update(changes)
    return argparse.Namespace(**values)


def stub_provider(monkeypatch, provider, calls, *, duplicate=False, failure=None):
    monkeypatch.setattr(c, "get_secret", lambda *names: (names[0], "synthetic-key"))
    monkeypatch.setattr(c, "reddit_token", lambda: ("synthetic-token", {"ok": True}))
    def response(url, **kwargs):
        params = kwargs.get("data") or {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
        query = params.get("query") or params.get("q")
        calls.append((query, int(params.get("limit") or params.get("count") or params.get("num"))))
        if failure:
            return failure
        prefix = "same" if duplicate else str(len(calls))
        if provider == "reddit":
            body = {"data": {"children": [{"data": {"id": f"{prefix}-{i}", "created_utc": time.time(),
                    "title": "I needed help with service", "selftext": "I waited weeks for a reply.",
                    "permalink": f"/r/test/{prefix}-{i}", "subreddit": "test", "author": "fixture"}}
                    for i in range(5)]}}
        else:
            items = [{"url": f"https://forum.test/{prefix}/{i}", "link": f"https://forum.test/{prefix}/{i}",
                      "title": "service experiences", "description": "I waited weeks for service.",
                      "snippet": "I waited weeks for service.", "markdown": "I waited weeks for service."}
                     for i in range(5)]
            body = {"data": items} if provider == "firecrawl" else {"organic": items} if provider == "serper_search" else {"web": {"results": items}}
        return {"ok": True, "status_code": 200, "body": body}
    monkeypatch.setattr(c, "http_get", response)
    monkeypatch.setattr(c, "http_post", response)


@pytest.mark.parametrize("provider", PROVIDERS)
def test_exact_candidates_cannot_be_starved_by_full_first_response(provider, tmp_path, monkeypatch):
    run_args = args(provider)
    calls = []
    stub_provider(monkeypatch, provider, calls)
    expected = c.provider_query_schedule(run_args, ["unplanned baseline"], provider)
    records, summary = getattr(c, f"collect_{provider}")(run_args, ["unplanned baseline"], tmp_path)
    assert calls == [(row["query"], 2) for row in expected]
    assert len(records) == 6
    assert [row["query_id"] for row in summary["query_ledger"]] == ["q0", "q1", "q2"]
    assert all(row["attempted"] and row["returned_count"] == 5 and row["new_record_count"] == 2 for row in summary["query_ledger"])
    assert all(record["discovery_memberships"][0]["candidate_id"] in {"c0", "c1", "c2"} for record in records)
    assert not c.accepted_records(records)[1]
    if provider in {"serper_search", "brave_search"}:
        assert all(record["content_completeness"] == "search_snippet" for record in records)


@pytest.mark.parametrize("provider", PROVIDERS)
def test_query_cap_and_duplicate_discoveries_remain_attributable(provider, tmp_path, monkeypatch):
    run_args = args(provider, query_limit=2)
    calls = []
    stub_provider(monkeypatch, provider, calls, duplicate=True)
    records, summary = getattr(c, f"collect_{provider}")(run_args, [], tmp_path)
    assert len(calls) == 2 and len(records) == 2
    assert len(records[0]["discovery_memberships"]) == 2
    rows = summary["query_ledger"]
    assert rows[0]["record_ids"] == rows[1]["record_ids"]
    assert rows[1]["new_record_count"] == 0
    assert rows[2]["status"] == "not_attempted:query_limit" and rows[2]["returned_count"] is None


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("status,failure", [
    ("permission_denied", {"ok": False, "status_code": 403}),
    ("insufficient_credits", {"ok": False, "status_code": 402, "error": "insufficient_credits"}),
    ("request_budget_exhausted", {"ok": False, "error_type": "request_budget_exhausted"}),
])
def test_failures_are_never_zero_result_success(provider, status, failure, tmp_path, monkeypatch):
    calls = []
    stub_provider(monkeypatch, provider, calls, failure=failure)
    records, summary = getattr(c, f"collect_{provider}")(args(provider), [], tmp_path)
    assert not records and summary["status"] == status
    assert all(row["returned_count"] is None for row in summary["query_ledger"])
    if status == "request_budget_exhausted":
        assert not any(row["attempted"] for row in summary["query_ledger"])
    elif status == "insufficient_credits":
        assert len(calls) == 1
        assert all(not row["attempted"] for row in summary["query_ledger"][1:])


@pytest.mark.parametrize("provider", PROVIDERS)
def test_missing_credentials_preserve_candidate_gaps(provider, tmp_path, monkeypatch):
    monkeypatch.setattr(c, "get_secret", lambda *names: (None, None))
    monkeypatch.setattr(c, "reddit_token", lambda: (None, {"status": "missing_credentials"}))
    records, summary = getattr(c, f"collect_{provider}")(args(provider), [], tmp_path)
    assert not records and summary["status"] == "missing_credentials"
    assert len(summary["query_ledger"]) == 3
    assert all(row["status"] == "not_attempted:missing_credentials" for row in summary["query_ledger"])


@pytest.mark.parametrize("mode", ["validation", "discovery"])
@pytest.mark.parametrize("language,topic,anchor", [
    ("de", "Umzug", "Familien"), ("fr", "déménagement", "familles"),
    ("it", "trasloco", "famiglie"), ("es", "mudanza", "familias"),
    ("zh", "搬家", "家庭"), ("ja", "引越し", "家族"), ("ar", "نقل المنزل", "أسر"),
])
def test_source_language_survives_every_query_path(mode, language, topic, anchor):
    queries = c.query_plan(topic, "families", geo="US", language=language, research_mode=mode, segment_keywords=anchor)
    assert queries
    assert not any(word in q.lower() for q in queries for word in ("why is", "deal with", "complaints", "reviews problems", "frustrated", "families"))
    if mode == "validation":
        assert topic in queries and any(anchor in query for query in queries)
    if language in {"ja", "ar"}:
        assert c.segment_modifiers("parents and students", language) == []


def cli(tmp_path, monkeypatch, data=None, extra=None):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data or plan(), ensure_ascii=False))
    argv = ["collect.py", "--topic", "Insurance advice for families in Germany", "--customer-segment", "families",
            "--query-plan", str(path), "--providers", "brave_search", "--geo", "DE", "--language", "de",
            "--limit", "6", "--results-per-query", "2"]
    monkeypatch.setattr(sys, "argv", argv + (extra or []))
    return path


def test_preview_has_exact_schedule_and_no_io_side_effects(tmp_path, monkeypatch, capsys):
    cli(tmp_path, monkeypatch, extra=["--query-preview"])
    def forbidden(*a, **kw):
        pytest.fail("Preview read credentials, called network or wrote a workspace")
    for name in ("get_secret", "http_get", "http_post", "resolve_run_dir", "write_json"):
        monkeypatch.setattr(c, name, forbidden)
    assert c.main() == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["queries"] == [r["query"] for r in plan()["queries"]]
    assert [r["query"] for r in preview["provider_schedules"]["brave_search"] if r["scheduled"]] == preview["queries"]
    assert preview["input_plan_digest"] and preview["providers_outside_preview"] == []


@pytest.mark.parametrize("extra", [
    ["--limit", "5"], ["--results-per-query", "0"], ["--query-limit", "0"],
    ["--language", "fr"], ["--geo", "AUTO"], ["--providers", "default"],
    ["--sampling-frame", "entity_led_feedback", "--subject-entity-id", "e1"],
])
def test_invalid_execution_fails_before_workspace_write(extra, tmp_path, monkeypatch):
    cli(tmp_path, monkeypatch, extra=extra)
    monkeypatch.setattr(c, "resolve_run_dir", lambda **kw: pytest.fail("Invalid plan wrote workspace"))
    with pytest.raises(SystemExit) as exc:
        c.main()
    assert exc.value.code == 2


@pytest.mark.parametrize("mutation", ["duplicate_id", "duplicate_query", "unsupported_provider", "source_without_locator", "missing_intent", "unknown_field"])
def test_malformed_plans_are_rejected(mutation, tmp_path, monkeypatch):
    data = copy.deepcopy(plan())
    row = data["queries"][1]
    if mutation == "duplicate_id": row["query_id"] = "q0"
    elif mutation == "duplicate_query": row["query"] = data["queries"][0]["query"].upper()
    elif mutation == "unsupported_provider": row["provider"] = "unsupported_test_provider"
    elif mutation == "source_without_locator": row["seed_origin"] = "source_derived"
    elif mutation == "missing_intent": del row["intent"]
    else: row["typo_field"] = True
    cli(tmp_path, monkeypatch, data)
    with pytest.raises(SystemExit) as exc:
        c.parse_args()
    assert exc.value.code == 2


@pytest.mark.parametrize("provider", PROVIDERS)
def test_short_generated_lists_do_not_crash_and_honor_query_limit(provider, tmp_path, monkeypatch):
    calls = []
    stub_provider(monkeypatch, provider, calls)
    records, summary = getattr(c, f"collect_{provider}")(args(provider, query_plan_data={}, query_limit=1), ["help", "experience"], tmp_path)
    assert len(calls) == 1 and len(records) <= 6
    assert summary["query_ledger"][1]["status"] == "not_attempted:query_limit"


def test_entity_gap_depends_on_capture_not_provider_name():
    for status in ("missing_credentials", "ok", "empty", "insufficient_credits"):
        flags = c.quality_summary([], {"trustpilot_reviews": {"status": status}})
        assert any("No entity-bound records" in flag for flag in flags)
    flags = c.quality_summary([{"sampling_frame": "entity_led_feedback", "subject_entity_id": "e1"}], {"firecrawl": {"status": "ok"}})
    assert any("Entity-led capture" in flag and "pending" in flag for flag in flags)
    assert not any("No entity-bound records" in flag for flag in flags)


def test_full_run_persists_plan_digest_and_exact_memberships(tmp_path, monkeypatch, capsys):
    cli(tmp_path, monkeypatch, extra=["--topic", "Insurance advice and claims problems for families living in Germany"])
    calls = []
    stub_provider(monkeypatch, "brave_search", calls)
    monkeypatch.setattr(c, "assess_relevance", lambda *a: ("relevant", "synthetic fixture", 1))
    out = tmp_path / "run"
    monkeypatch.setattr(c, "resolve_run_dir", lambda **kw: (out, None))
    monkeypatch.setattr(c, "load_provider_routing", lambda: {})
    assert c.main() == 0
    summary = json.loads((out / "summary.json").read_text())
    snapshot = json.loads((out / "query_plan.json").read_text())
    records = [json.loads(line) for line in (out / "evidence.jsonl").read_text().splitlines()]
    assert summary["query_plan_digest"] == snapshot["input_plan_digest"]
    assert snapshot["input_plan"] == plan()
    assert "Query calibration warning" not in (out / "research_plan.md").read_text()
    assert len(records) == 6 and len(calls) == 3
    assert all(record["discovery_memberships"][0]["query_id"] for record in records)
    assert len(summary["providers"]["brave_search"]["query_ledger"]) == 3


@pytest.mark.parametrize("locale,phrases", [
    ("JP:ja", ["引越し 荷物 届かない", "引越し 自分で 解決"]),
    ("SA:ar", ["نقل الأثاث تأخر", "نقلت الأثاث بنفسي"]),
    ("GB:en", ["deposit still not returned", "got my deposit back"]),
])
def test_exact_plan_transfers_without_english_or_german_expansion(locale, phrases, tmp_path, monkeypatch):
    country, language = locale.split(":")
    data = plan(locale=locale, phrases=phrases)
    cli(tmp_path, monkeypatch, data, ["--geo", country, "--language", language])
    run_args = c.parse_args()
    calls = []
    stub_provider(monkeypatch, "brave_search", calls)
    c.collect_brave_search(run_args, ["unplanned English topic"], tmp_path)
    assert [query for query, _ in calls] == phrases


def test_auto_audience_inference_uses_resolved_locale(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["collect.py", "--topic", "Umzug", "--customer-segment", "families",
                                     "--geo", "DE", "--language", "de", "--query-preview"])
    assert c.parse_args().segment_keywords == "Familien"


def test_entity_capture_is_not_previewed_as_web_search():
    snapshot = c.query_plan_snapshot(args("firecrawl", query_plan_data={}, sampling_frame="entity_led_feedback"), ["query"])
    assert not snapshot["provider_schedules"]
    assert snapshot["providers_outside_preview"] == ["firecrawl"]


def test_generated_unsupported_language_has_explicit_warning():
    snapshot = c.query_plan_snapshot(args(language="ja", geo="JP", query_plan_data={}), ["引越し"])
    assert any("No built-in language expansion" in warning for warning in snapshot["warnings"])


def test_http_budget_stops_later_provider_with_query_gaps(tmp_path, monkeypatch, capsys):
    data = plan("brave_search", phrases=["service experiences"])
    second = plan("firecrawl", phrases=["service successful workaround"])["queries"][0]
    second["query_id"] = "second"
    data["queries"].append(second)
    cli(tmp_path, monkeypatch, data, ["--providers", "brave_search,firecrawl", "--max-http-requests", "1"])
    monkeypatch.setattr(c, "get_secret", lambda *names: (names[0], "synthetic-key"))
    monkeypatch.setattr(c, "resolve_run_dir", lambda **kw: (tmp_path / "run", None))
    monkeypatch.setattr(c, "load_provider_routing", lambda: {})
    import common
    monkeypatch.setattr(common.urllib.request, "urlopen", lambda *a, **kw: (_ for _ in ()).throw(OSError("fixture offline")))
    monkeypatch.setattr(c, "collect_firecrawl", lambda *a: pytest.fail("Provider started after exhausted request budget"))
    assert c.main() == 2
    summary = json.loads((tmp_path / "run/summary.json").read_text())
    row = summary["providers"]["firecrawl"]["query_ledger"][0]
    assert row["query_id"] == "second" and not row["attempted"]
    assert row["status"] == "not_attempted:request_budget_exhausted"
