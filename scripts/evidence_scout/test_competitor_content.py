#!/usr/bin/env python3
"""Tests for the competitor and similar-company content inventory (no network; synthetic Firecrawl replay)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import analyze_competitor_marketing as acm  # noqa: E402
from scripts.marketing.keyword_map import merge_content_inputs  # noqa: E402

FIXTURE = json.loads((ROOT / "fixtures" / "evidence_scout" / "firecrawl_content_inventory_sample.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "schemas" / "competitor-content.schema.json").read_text(encoding="utf-8"))
COMPETITOR = "https://www.example.com"
ANALOG = "https://www.example.org"


def _fetcher():
    return acm.FixtureInventoryFetcher(FIXTURE)


def _search_row(cid, queries, paa=()):
    return {'cluster_id': cid, 'queries': [{'query_id': f'{cid}-{i}', 'query': q, 'seed_origin': 'autocomplete'} for i, q in enumerate(queries)],
            'journey_stage': 'solution_aware', 'intent': 'commercial', 'searcher_role': 'buyer', 'locale': 'DE:de',
            'questions': {'paa': list(paa), 'related_searches': [], 'ai_overview_prompts': []},
            'serp_features': {'ads': 'observed', 'ai_overview': True, 'paa': True, 'video': False, 'forum': False, 'local_pack': False, 'shopping': False},
            'ranking_by_type': {}, 'content_gap': {'status': 'hypothesis', 'hypothesis': 'h', 'evidence_refs': ['cap/1.json'], 'needs_review': True},
            'recommended_page_type': 'comparison', 'conversion_bridge': 'quote request', 'evidence_refs': ['cap/1.json'],
            'evidence_status': 'includes_observed_seed', 'volume': None, 'observed_seed_fraction': 1.0}


CLUSTERS = [_search_row('bu-vergleich', ['bu versicherung vergleich']), _search_row('bu-studenten', ['bu für studenten']),
            _search_row('income-protection', ['income protection comparison'])]


@pytest.fixture
def inventories():
    return [acm.inventory_site(COMPETITOR, "competitive_market", max_pages=10, entity="Example Versicherung", fetcher=_fetcher()),
            acm.inventory_site(ANALOG, "similar_company", max_pages=10, entity="Example Abroad", fetcher=_fetcher())]


def test_inventory_skips_legal_and_login_pages(inventories):
    site = inventories[0]
    urls = {page["url"] for page in site["pages"]}
    for skipped in ("/impressum", "/datenschutz", "/karriere/jobs", "/login", "/mein-konto/einstellungen", "/warenkorb", "/assets/broschuere.pdf"):
        assert COMPETITOR + skipped not in urls
        assert COMPETITOR + skipped in {item["url"] for item in site["excluded"]}
    # robots.txt disallows /intern/: never fetched, recorded as robots-skipped
    assert COMPETITOR + "/intern/ratgeber-entwurf" not in urls
    assert COMPETITOR + "/intern/ratgeber-entwurf" in site["robots_disallowed"]
    assert COMPETITOR + "/ratgeber/bu-versicherung-vergleich" in urls
    assert site["discovery"] == "firecrawl_map"
    # map failure falls back to sitemap.xml; legal/career/account pages still skipped
    analog = inventories[1]
    assert analog["discovery"] == "sitemap"
    assert [page["url"] for page in analog["pages"]] == [ANALOG + "/guides/income-protection-comparison"]
    assert analog["entity_type"] == "similar_company"


def test_focus_terms_spend_small_samples_on_relevant_pages():
    site = acm.inventory_site(COMPETITOR, "competitive_market", max_pages=1, fetcher=_fetcher(), focus_terms=["bu kosten"])
    assert [p["url"] for p in site["pages"]] == [COMPETITOR + "/ratgeber/bu-kosten"]


def test_questions_extracted_from_headings_and_faq_schema(inventories):
    page = next(p for p in inventories[0]["pages"] if p["url"].endswith("bu-versicherung-vergleich"))
    questions = page["questions_answered"]
    assert "Was kostet eine BU?" in questions            # H2 question
    assert "Wie finde ich den passenden Tarif?" in questions  # H3 question
    assert "Wann zahlt die BU?" in questions            # FAQPage schema only
    assert questions.count("Was kostet eine BU?") == 1  # heading + schema deduplicated
    assert "Hinweise zur Auswahl" not in questions
    assert {"FAQPage", "Article"} <= set(page["schema_types"])
    assert {"comparison_table", "video", "checklist"} <= set(page["formats"])
    assert page["last_updated"] == "2026-03-12"
    assert page["topic"] == "BU-Versicherung im Vergleich"
    assert page["primary_cta"] == "Jetzt Beitrag berechnen"
    assert page["retrieved_at"]
    analog_page = inventories[1]["pages"][0]
    assert "calculator" in analog_page["formats"]


def test_excerpts_capped_at_300_chars(inventories):
    for site in inventories:
        for page in site["pages"]:
            assert len(page.get("excerpt") or "") <= 300
            assert "markdown" not in page and "rawHtml" not in page and "body" not in page
    long_page = next(p for p in inventories[0]["pages"] if p["url"].endswith("bu-versicherung-vergleich"))
    assert len(long_page["excerpt"]) == 300
    # the whole serialized inventory never carries body text
    assert "Synthetic answer text" not in json.dumps(inventories)


def test_coverage_matrix_separates_lanes(inventories, tmp_path):
    result = acm.coverage_matrix(inventories, CLUSTERS, out_dir=tmp_path)
    by = {(r["cluster_id"], r["entity_type"]): r for r in result["rows"]}
    assert by[("bu-vergleich", "competitor")]["coverage"] in {"covered_well", "covered_thin"}
    assert by[("bu-vergleich", "similar_company")]["coverage"] == "uncovered"
    assert by[("income-protection", "similar_company")]["coverage"] in {"covered_well", "covered_thin"}
    assert by[("income-protection", "competitor")]["coverage"] == "uncovered"
    assert by[("bu-studenten", "competitor")]["coverage"] == "uncovered"
    summary = {s["cluster_id"]: s for s in result["cluster_summary"]}
    assert set(summary["bu-vergleich"]["by_entity_type"]) == {"competitor", "similar_company", "capability_reference"}
    assert summary["bu-studenten"]["interpretation"] == "demand_question"
    # refs bind real files under out_dir by sha256
    for row in result["rows"]:
        for ref in row["refs"]:
            raw = (tmp_path / ref["path"]).read_bytes()
            assert acm.sha256_hex(raw) == ref["sha256"]
    assert not list(Draft202012Validator(SCHEMA).iter_errors(result))


def test_analog_lane_never_marks_topic_as_market_evidence(inventories, tmp_path):
    result = acm.coverage_matrix(inventories, CLUSTERS, out_dir=tmp_path)
    summary = {s["cluster_id"]: s for s in result["cluster_summary"]}
    ip = summary["income-protection"]
    assert ip["market_competitor_coverage"] is False
    assert ip["interpretation"] == "demand_question"
    assert ip["inspiration"] and all(i["entity_type"] != "competitor" for i in ip["inspiration"])
    # downstream: the analog row stays inspiration-only in the keyword-map merge
    search = tmp_path / "content-opportunities.json"
    search.write_text(json.dumps({'schema_version': 1, 'source': 'search_journey_serp_study', 'caveats': ['c'], 'rows': CLUSTERS}))
    comp = tmp_path / "competitor-content.json"
    comp.write_text(json.dumps(result))
    merged = {r["cluster_id"]: r for r in merge_content_inputs(search, competitor_content=comp, out=tmp_path / "keyword-map.proposed.json")["rows"]}
    assert merged["income-protection"]["single_input"] is True
    assert merged["income-protection"]["inspiration_count"] >= 1


def test_output_validates_against_schema_and_merges(inventories, tmp_path):
    result = acm.coverage_matrix(inventories, CLUSTERS, out_dir=tmp_path)
    assert not list(Draft202012Validator(SCHEMA).iter_errors(result))
    assert result["schema_version"] == 1 and result["caveats"]
    search = tmp_path / "content-opportunities.json"
    search.write_text(json.dumps({'schema_version': 1, 'source': 'search_journey_serp_study', 'caveats': ['c'], 'rows': CLUSTERS}))
    comp = tmp_path / "competitor-content.json"
    comp.write_text(json.dumps(result))
    merged = {r["cluster_id"]: r for r in merge_content_inputs(search, competitor_content=comp, out=tmp_path / "keyword-map.proposed.json")["rows"]}
    assert set(merged) == {"bu-vergleich", "bu-studenten", "income-protection"}  # no stray clusters
    assert merged["bu-vergleich"]["input_count"] == 2  # search + covering market competitor
    # an uncovered market competitor is not a contributing input
    assert merged["bu-studenten"]["input_count"] == 1


def test_cli_writes_json_and_markdown(tmp_path):
    landscape = tmp_path / "entity-landscape.json"
    landscape.write_text(json.dumps({"entities": [
        {"name": "Example Versicherung", "url": COMPETITOR, "primary_lane": "competitive_market", "verification_status": "verified"},
        {"name": "Example Abroad", "url": ANALOG, "primary_lane": "similar_company", "verification_status": "verified"},
        {"name": "Unclear Co", "url": "https://example.com/unclear", "primary_lane": "uncertain", "verification_status": "uncertain"}]}))
    clusters = tmp_path / "content-opportunities.json"
    clusters.write_text(json.dumps({'schema_version': 1, 'source': 'search_journey_serp_study', 'caveats': ['c'], 'rows': CLUSTERS}))
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps(FIXTURE))
    out = tmp_path / "out"
    code = acm.main(["--content-inventory", "--landscape", str(landscape), "--clusters", str(clusters), "--out", str(out),
                     "--max-pages", "10", "--fixture-inventory-json", str(fixture)])
    assert code == 0
    doc = json.loads((out / "competitor-content.json").read_text())
    assert not list(Draft202012Validator(SCHEMA).iter_errors(doc))
    md = (out / "competitor-content.md").read_text()
    assert "not what customers need" in md and "Unclear Co" in md
