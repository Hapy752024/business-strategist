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
