import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("research_review_packet", ROOT / "scripts/evidence_scout/build_review_packet.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def test_packet_shows_original_context_and_never_accepts_proposed_annotations():
    source = {"evidence_id":"e1", "source_url":"https://community.example/thread", "source":"forum",
              "text":"I tried the old process. It failed on Monday, but my colleague resolved it Tuesday.", "sampling_frame":"topic_led_voc"}
    annotations = [{"evidence_id":"e1", "annotations":[{"start":36, "end":59, "label":"failure"}]}]
    out = module.build({"input_plan":{"queries":[{"query_id":"q1"}]}}, [source], annotations,
                       [], {"status":"partial"}, ["e1"])
    row = out["items"][0]
    assert row["text"] == source["text"]
    assert row["annotations"][0]["quote"] == source["text"][36:59]
    assert row["review_status"] == "unreviewed"
    assert out["read_only"] is True


SUMMARY = {
    "days": 90, "geo": "DE", "language": "de",
    "providers_requested": ["reddit", "hn", "serper", "trustpilot", "x", "firecrawl", "producthunt"],
    "providers": {
        "reddit": {"status": "ok", "credential_source": "REDDIT_CLIENT_ID",
                   "query_ledger": [{"query": "steuer chaos", "locale": "de-DE", "attempted": True, "status": "ok"}]},
        "hn": {"status": "ok", "query_ledger": [{"query": "bookkeeping pain", "locale": "en", "attempted": True, "status": "ok"}]},
        "serper": {"status": "missing_credentials", "required_env": ["SERPER_DEV_API_KEY"]},
        "trustpilot": {"status": "blocked_by_provider", "reason": "Cloudflare challenge on every request"},
        "x": {"status": "rate_limited"},
        "firecrawl": {"status": "insufficient_credits"},
    },
}
EVIDENCE = [{"evidence_id": "e1", "text": "t", "sampling_frame": "topic_led_voc", "published_at": "2026-08-01T00:00:00Z"},
            {"evidence_id": "e2", "text": "t", "sampling_frame": "entity_led_feedback", "published_at": "2026-10-02"}]


def test_review_packet_has_methodology():
    out = module.build({"input_plan": {"queries": []}}, EVIDENCE, [], [], {"status": "partial"}, run_summary=SUMMARY)
    m = out["methodology"]
    assert out["methodology_markdown"].startswith("## Methodology")
    reddit = m["providers"]["reddit"]
    assert reddit["outcome"] == "attempted" and reddit["access"] == "keyed"
    assert reddit["queries"] == [{"query": "steuer chaos", "locale": "de-DE", "status": "ok"}]
    assert m["providers"]["hn"]["access"] == "keyless"
    assert m["sampling_frames"] == {"entity_led_feedback": 1, "topic_led_voc": 1}
    assert m["date_range"] == {"lookback_days": 90, "earliest": "2026-08-01", "latest": "2026-10-02"}
    assert "de-DE" in out["methodology_markdown"] and "steuer chaos" in out["methodology_markdown"]


def test_skipped_provider_appears_with_reason():
    out = module.build({"input_plan": {"queries": []}}, EVIDENCE, [], [], {}, run_summary=SUMMARY)
    p = out["methodology"]["providers"]
    assert p["serper"]["outcome"] == "skipped" and "SERPER_DEV_API_KEY" in p["serper"]["reason"]
    assert p["trustpilot"]["status"] == "blocked_by_provider" and "Cloudflare" in p["trustpilot"]["reason"]
    assert p["x"]["outcome"] == "skipped" and "rate" in p["x"]["reason"]
    assert p["firecrawl"]["outcome"] == "skipped" and "quota" in p["firecrawl"]["reason"]
    assert p["producthunt"]["status"] == "not_run"
    md = out["methodology_markdown"]
    for name in ("serper", "trustpilot", "x", "firecrawl", "producthunt"):
        assert f"| {name} |" in md


def test_methodology_without_summary_says_not_recorded():
    out = module.build({"input_plan": {"queries": []}}, EVIDENCE, [], [], {})
    assert out["methodology"]["providers"] == {}
    assert "not recorded" in out["methodology_markdown"]
