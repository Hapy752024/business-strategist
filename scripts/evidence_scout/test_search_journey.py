#!/usr/bin/env python3
"""Tests for the customer search-journey SERP study (no network)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import search_journey as sj
from search_journey import build_content_opportunities, build_report, parse_serpapi, parse_serper, validate_plan

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout"


def load(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _row(query_id, query, stage, intent="transactional", origin="brainstorm"):
    return {"query_id": query_id, "query": query, "journey_stage": stage, "searcher_role": "buyer",
            "intent": intent, "seed_origin": origin, "locale": "en-US", "language": "en"}


plan = {"schema_version": 1, "revision": "r1", "rows": [
    _row("q1", "invoicing app pricing", "purchase"),
    _row("q2", "buy invoicing software", "purchase"),
]}


def _cap(query_id, ad_domain, raw):
    return {"query_id": query_id, "provider": "serpapi", "locale": "en-US", "device": "desktop", "location": "United States",
            "captured_at": "2026-10-30T10:00:00Z", "ads_status": "observed",
            "ads": [{"position": "top", "rank": 1, "advertiser_domain": ad_domain, "headline": "Invoices in 2 minutes",
                     "description": "Start free", "display_url": f"https://{ad_domain}"}],
            "organic": [{"rank": 1, "domain": "example.org", "title": "Best invoicing apps", "url": "https://example.org/best",
                         "result_type": "publisher"},
                        {"rank": 2, "domain": "forum.example.com", "title": "Which app?", "url": "https://forum.example.com/t/1",
                         "result_type": "forum_community"}],
            "shopping": [], "local_pack": [], "ai_overview": {"present": True, "cited_domains": ["example.org"]},
            "paa": ["Which invoicing app is cheapest?"], "related": ["free invoicing app"],
            "features": {"video": False, "forum": True}, "raw_path": raw}


cap_a = _cap("q1", "example-competitor.com", "raw/q1__serpapi__1.json")
cap_b = _cap("q2", "example-competitor.com", "raw/q2__serpapi__1.json")


def test_serpapi_ads_and_organic_separated():
    # The real 2026-10-30 sample carried its ads in the bottom block; the parser must keep SerpApi's block_position.
    payload = load("serpapi_google_sample.json")
    cap = parse_serpapi(payload)
    assert cap["ads_status"] == "observed" and cap["ads"][0]["position"] == payload["ads"][0]["block_position"]
    assert {a["position"] for a in cap["ads"]} <= {"top", "bottom", "other"}
    assert all("advertiser_domain" not in o for o in cap["organic"])
    assert all(a["advertiser_domain"] and "google" not in a["advertiser_domain"] for a in cap["ads"])
    top = dict(payload["ads"][0], block_position="top")
    assert parse_serpapi(dict(payload, ads=[top]))["ads"][0]["position"] == "top"


def test_video_rows_without_host_fall_back_to_platform_source():
    row = {"position": 1, "title": "t", "link": "https://www.google.com/goto?url=x", "displayed_link": "Ca. 1340 Aufrufe",
           "source": "YouTube · ExampleChannel"}
    cap = parse_serpapi({"organic_results": [row]})
    assert cap["organic"][0]["domain"] == "youtube.com" and cap["organic"][0]["result_type"] == "video"


def test_serper_marks_ads_unobserved_not_zero():
    cap = parse_serper(load("serper_sample.json"))
    assert cap["ads_status"] == "unobserved" and cap["ads"] == []


def test_serpapi_without_ads_is_observed_none():
    payload = load("serpapi_google_sample.json"); payload.pop("ads", None)
    assert parse_serpapi(payload)["ads_status"] == "observed_none"


def test_plan_row_requires_journey_stage_and_origin():
    errs = validate_plan({"rows": [{"query": "best invoicing app", "locale": "en-US"}]})
    assert any("journey_stage" in e for e in errs) and any("seed_origin" in e for e in errs)


def test_content_opportunities_rows_bind_to_captures():
    rows = build_content_opportunities([cap_a, cap_b], plan)["rows"]
    assert rows and all(r["evidence_refs"] and r["journey_stage"] and r["recommended_page_type"] for r in rows)
    assert all(r.get("volume") is None for r in rows)


def test_report_counts_repeated_advertisers_per_stage():
    rep = build_report([cap_a, cap_b], plan)  # same advertiser in two purchase-stage captures
    assert rep["stages"]["purchase"]["repeated_advertisers"] == ["example-competitor.com"]


# --- additional guards ---------------------------------------------------------------------------------------

def test_valid_plan_passes_and_brainstorm_rows_are_hypotheses():
    assert validate_plan(plan) == []
    rows = build_content_opportunities([cap_a, cap_b], plan)["rows"]
    assert all(r["evidence_status"] == "brainstorm_hypothesis_only" for r in rows)
    assert all(r["content_gap"]["status"] == "hypothesis" for r in rows)


def test_content_opportunities_validate_against_schema():
    out = build_content_opportunities([cap_a, cap_b], plan)
    assert sj.validate_content_opportunities(out) == []


def test_unobserved_ads_are_never_reported_as_zero():
    unobs = dict(cap_a, provider="serper_search", ads_status="unobserved", ads=[])
    rep = build_report([unobs], plan)
    stage = rep["stages"]["purchase"]
    assert stage["advertiser_count"] is None and stage["queries_with_ads"] is None
    assert stage["ads_status_counts"]["unobserved"] == 1
    md = sj.render_markdown(rep)
    assert "unobserved" in md and "0 advertisers" not in md


def test_serpapi_ai_overview_page_token_is_present_without_citations():
    payload = load("serpapi_google_sample.json")
    payload["ai_overview"] = {"page_token": "tok", "serpapi_link": "https://serpapi.com/search.json?engine=google_ai_overview"}
    assert parse_serpapi(payload)["ai_overview"] == {"present": True, "cited_domains": None}
    payload.pop("ai_overview")
    assert parse_serpapi(payload)["ai_overview"]["present"] is False
    assert parse_serper(load("serper_sample.json"))["ai_overview"]["present"] is None


def test_classify_domain_uses_curated_map_and_competitors():
    comp = {"example-competitor.com"}
    assert sj.classify_domain("www.reddit.com", comp) == "forum_community"
    assert sj.classify_domain("check24.de", comp) == "marketplace_aggregator"
    assert sj.classify_domain("amazon.de", comp) == "marketplace_aggregator"
    assert sj.classify_domain("de.trustpilot.com", comp) == "directory_review"
    assert sj.classify_domain("www.bafin.de", comp) == "government_institution"
    assert sj.classify_domain("www.bmas.bund.de", comp) == "government_institution"
    assert sj.classify_domain("youtube.com", comp) == "video"
    assert sj.classify_domain("shop.example-competitor.com", comp) == "competitor"
    assert sj.classify_domain("unknown-site.example", comp) == "unknown"
    assert sj.classify_url("https://www.finanztip.de/community/thread/1", set()) == ("forum_community", "curated")


def test_serper_compact_result_keeps_ads_and_marks_unobserved():
    import serper_fetch
    assert serper_fetch.compact_result({"organic": []})["ads_status"] == "unobserved"
    kept = serper_fetch.compact_result({"organic": [], "ads": [{"title": "x"}]})
    assert kept["ads"] == [{"title": "x"}] and kept["ads_status"] == "observed"


def test_capture_writes_raw_and_binds_metadata():
    row = dict(_row("q1", "invoicing app pricing", "purchase"), location="United States", device="desktop")
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sj, "fetch_serpapi", return_value=load("serpapi_google_sample.json")):
        cap = sj.capture(row, "serpapi", Path(tmp))
        assert Path(tmp, cap["raw_path"]).exists() and cap["query_id"] == "q1"
        assert cap["device"] == "desktop" and cap["location"] == "United States" and cap["captured_at"]


def test_report_flags_forum_and_aggregator_signals_as_hypotheses():
    rep = build_report([cap_a, cap_b], plan)
    st = rep["stages"]["purchase"]
    assert st["forum_share_top10"] == pytest.approx(0.5)
    assert all("hypothesis" in h.lower() for h in rep["hypotheses"])
    assert "example-competitor.com" in st["new_competitor_candidates"]


def test_page_type_is_cluster_majority_not_any_token():
    rows = [_row("p1", "insurance sign up online", "purchase"), _row("p2", "buy insurance now", "purchase"),
            _row("p3", "insurance calculator", "purchase")]
    caps = [_cap(r["query_id"], "example-competitor.com", f"raw/{r['query_id']}.json") for r in rows]
    out = build_content_opportunities(caps, {"rows": rows})["rows"]
    assert out[0]["recommended_page_type"] == "landing"


def test_cli_reuses_recent_capture_and_refetches_changed_query():
    row = dict(_row("q1", "invoicing app pricing", "purchase"), location="United States")
    with tempfile.TemporaryDirectory() as tmp:
        run, plan_path = Path(tmp), Path(tmp, "plan.json")
        plan_path.write_text(json.dumps({"rows": [row]}))
        with mock.patch.object(sj, "fetch_serpapi", return_value=load("serpapi_google_sample.json")) as fetch:
            assert sj.main(["--plan", str(plan_path), "--run-dir", str(run)]) == 0
            assert sj.main(["--plan", str(plan_path), "--run-dir", str(run)]) == 0
            assert fetch.call_count == 1
            plan_path.write_text(json.dumps({"rows": [dict(row, query="invoicing app cost")]}))
            assert sj.main(["--plan", str(plan_path), "--run-dir", str(run)]) == 0
            assert fetch.call_count == 2
        assert (run / "serp-landscape.md").exists() and (run / "content-opportunities.json").exists()
