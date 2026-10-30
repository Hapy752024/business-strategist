import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.evidence_scout import build_voc_table as vt  # noqa: E402

VOICE = {"customer": "firsthand_customer"}


def rec(eid, source="reddit", frame="topic_led_voc", key=None, cluster=None, unit="source_record"):
    r = {"evidence_id": eid, "source_url": f"https://x/{eid}", "source": source, "sampling_frame": frame,
         "independence_key": key or f"k:{eid}", "capture_unit": unit, "customer_segment": "seg"}
    if cluster:
        r["duplicate_cluster_id"] = cluster
    return r


def rev(eid, stype="past_behaviour", **extra):
    r = {"evidence_id": eid, "source_url": f"https://x/{eid}", "status": "accepted", "voice": "customer",
         "firsthand": True, "author_relationship": "firsthand_customer", "reviewed_segment": "seg",
         "statement_type": stype}
    r.update(extra)
    return r


def synth(**need):
    n = {"id": "U1", "outcome": "o", "evidence_ids": [], "perspectives": ["customer"], "attribution": "customer_stated"}
    n.update(need)
    return {"customer_needs": [n], "solution_requirements": [], "topic_led_evidence_ids": [], "entity_led_evidence_ids": []}


def build(records, reviews, need, summary=None):
    return vt.build_table(synth(**need), {"statement_typing": True, "reviews": reviews}, records, summary)


def row(t, ident="U1"):
    return next(r for r in t["rows"] if r["id"] == ident)


class VocTable(unittest.TestCase):
    def test_duplicates_counted_once(self):
        recs = [rec("a", key="k1"), rec("b", key="k1"), rec("c", key="k2", cluster="cl"), rec("d", key="k3", cluster="cl"), rec("e")]
        t = build(recs, [rev(i) for i in "abcde"], {"evidence_ids": list("abcd")})
        f = row(t)["frames"]["topic_led_voc"]
        self.assertEqual(f["sources"], 2)      # {a,b} and {c,d}
        self.assertEqual(f["total_sources"], 3)  # plus e

    def test_compliments_excluded_but_listed(self):
        recs = [rec("a"), rec("b"), rec("c")]
        revs = [rev("a"), rev("b", "compliment"), rev("c", "feature_request")]
        t = build(recs, revs, {"evidence_ids": ["a", "b", "c"]})
        f = row(t)["frames"]["topic_led_voc"]
        self.assertEqual(f["sources"], 1)
        self.assertEqual(f["mentioned_not_supporting"], 2)

    def test_frames_never_merged(self):
        recs = [rec("a"), rec("b", frame="entity_led_feedback", source="app_review"), rec("c", frame="entity_led_feedback", source="app_review")]
        t = build(recs, [rev(i) for i in "abc"], {"evidence_ids": ["a", "b"]})
        fr = row(t)["frames"]
        self.assertEqual((fr["topic_led_voc"]["sources"], fr["topic_led_voc"]["total_sources"]), (1, 1))
        self.assertEqual((fr["entity_led_feedback"]["sources"], fr["entity_led_feedback"]["total_sources"]), (1, 2))
        self.assertNotIn("sources", row(t))

    def test_unknown_prompting_stays_unknown(self):
        recs = [rec("a", source="interview_transcript"), rec("b", source="forum"), rec("c", source="reddit_comment"), rec("d", source="forum")]
        revs = [rev("a"), rev("b"), rev("c"), rev("d", prompted=True)]
        f = row(build(recs, revs, {"evidence_ids": list("abcd")}))["frames"]["topic_led_voc"]
        self.assertEqual((f["unprompted"], f["prompted"], f["unknown_prompting"]), (1, 1, 2))

    def test_confidence_thresholds(self):
        def conf(n, types, counter=0, resolution=None):
            recs = [rec(f"s{i}", source=types[i % len(types)]) for i in range(n)] + [rec(f"c{i}", source="forum") for i in range(counter)]
            revs = [rev(r["evidence_id"]) for r in recs]
            need = {"evidence_ids": [f"s{i}" for i in range(n)], "counter_evidence_ids": [f"c{i}" for i in range(counter)]}
            if resolution:
                need["counter_evidence_resolution"] = resolution
            return row(build(recs, revs, need))["confidence"]
        self.assertEqual(conf(3, ["reddit", "forum"]), "high")
        self.assertEqual(conf(3, ["reddit"]), "medium")   # one source type
        self.assertEqual(conf(2, ["reddit", "forum"]), "medium")
        self.assertEqual(conf(1, ["reddit"]), "low")
        self.assertEqual(conf(0, ["reddit"]), "low")

    def test_counter_evidence_lowers_confidence(self):
        base = lambda **k: None
        recs = [rec(f"s{i}", source=["reddit", "forum", "stackexchange"][i]) for i in range(3)] + [rec("c0", source="forum")]
        revs = [rev(r["evidence_id"]) for r in recs]
        need = {"evidence_ids": ["s0", "s1", "s2"], "counter_evidence_ids": ["c0"]}
        r = row(build(recs, revs, need))
        self.assertEqual(r["confidence"], "medium")
        self.assertEqual(r["counter_sources"], 1)
        need["counter_evidence_resolution"] = "counter author is outside segment"
        self.assertEqual(row(build(recs, revs, need))["confidence"], "high")

    def test_legacy_untyped_not_supporting(self):
        recs = [rec("a")]
        r = {k: v for k, v in rev("a").items() if k != "statement_type"}
        t = vt.build_table(synth(evidence_ids=["a"]), {"reviews": [r]}, recs)
        f = row(t)["frames"]["topic_led_voc"]
        self.assertEqual(f["sources"], 0)
        self.assertEqual(f["mentioned_not_supporting"], 1)

    def test_markdown_and_cli(self):
        recs = [rec("a"), rec("b", source="forum")]
        revs = [rev("a"), rev("b")]
        summary = {"providers": {"x": {"status": "missing_credentials"}, "y": {"status": "ok"}}}
        t = build(recs, revs, {"evidence_ids": ["a", "b"]}, summary)
        md = vt.render_markdown(t)
        self.assertIn("frequency is not importance", md.lower())
        self.assertIn("2 of 2", md)
        self.assertIn("missing_credentials", md)
        self.assertIn("entity_led_feedback", md)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "evidence.jsonl").write_text("\n".join(json.dumps(r) for r in recs))
            (d / "syn.json").write_text(json.dumps(synth(evidence_ids=["a", "b"])))
            (d / "rev.json").write_text(json.dumps({"statement_typing": True, "reviews": revs}))
            (d / "summary.json").write_text(json.dumps(summary))
            rc = vt.main(["--evidence", str(d / "evidence.jsonl"), "--synthesis", str(d / "syn.json"),
                          "--source-review", str(d / "rev.json"), "--summary", str(d / "summary.json"), "--out-dir", str(d)])
            self.assertEqual(rc, 0)
            self.assertTrue((d / "voc-table.json").exists() and (d / "voc-table.md").exists())


if __name__ == "__main__":
    unittest.main()
