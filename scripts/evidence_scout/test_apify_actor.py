#!/usr/bin/env python3
"""Tests for the generic Apify actor runner and the review lanes (no network)."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR
from providers import apify_actor
from providers.apify_actor import CapExceeded, load_config, render_input, run_actor, to_records

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout"
LANES = ("software_reviews", "g2_reviews", "shopify_app_reviews", "quora", "facebook_public_groups")
ENTITY_LANES = ("software_reviews", "g2_reviews", "shopify_app_reviews")
NAME_KEYS = {"name", "reviewername", "store", "username", "reviewercompany", "reviewermonogram", "profilename", "profilepic", "profileid"}


def load_fixture(lane: str) -> list[dict]:
    return json.loads((FIXTURES / f"apify_{lane}_sample.json").read_text(encoding="utf-8"))


def convert(lane: str, items=None, **kw):
    return to_records(lane, items if items is not None else load_fixture(lane), "q", "2026-10-30T00:00:00Z",
                      subject_entity_id="ent-1" if lane in ENTITY_LANES else "", **kw)


def validate_record(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=3, days=30, customer_segment="", hypothesis_id="H1", apify_review_item_cap=500,
                topic="unpaid invoices", problem_keywords="", workaround_keywords="", locale="", language="en",
                apify_review_targets="", apify_facebook_groups="", query_limit=12, results_per_query=5,
                query_plan_data={}, customer_feedback_source_plan="", sampling_frame="topic_led_voc",
                subject_entity_id="", force_blocked=False, geo="US")
    base.update(kw)
    return argparse.Namespace(**base)


class ConfigTests(unittest.TestCase):
    def test_every_lane_is_complete_and_public_only(self) -> None:
        cfg = load_config()["lanes"]
        self.assertEqual(set(cfg), set(LANES))
        for lane, row in cfg.items():
            for key in ("actor_id", "input_template", "field_map", "cost_per_1k_usd", "items_per_unit", "incentivised_flag_field", "public_only"):
                self.assertIn(key, row, f"{lane} missing {key}")
            self.assertIs(row["public_only"], True)
            self.assertGreater(row["cost_per_1k_usd"], 0)
            self.assertGreaterEqual(row["items_per_unit"], 1)

    def test_no_logins_cookies_or_proxy_credentials_configured(self) -> None:
        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    self.assertIsNone(re.search(r"cookie|login|password|token|session|proxy|username", k, re.I), f"{path}/{k}")
                    walk(v, f"{path}/{k}")
            elif isinstance(o, list):
                for v in o:
                    walk(v, path)
        for lane, row in load_config()["lanes"].items():
            walk(row["input_template"], lane)

    def test_render_input_keeps_types(self) -> None:
        out = render_input({"a": "{max_items}", "b": ["{entity_url}"], "c": {"d": "{query}"}, "e": 5},
                           {"max_items": 3, "entity_url": "https://x", "query": "q"})
        self.assertEqual(out, {"a": 3, "b": ["https://x"], "c": {"d": "q"}, "e": 5})


class RunActorTests(unittest.TestCase):
    def test_cap_refused_before_network(self) -> None:
        with mock.patch("providers.apify_actor.http_post") as post:
            with self.assertRaises(CapExceeded):
                run_actor("o~a", {}, cap=10, requested_items=11, token="t")
        post.assert_not_called()

    def test_token_only_in_header_and_charge_cap_sent(self) -> None:
        resp = {"ok": True, "status_code": 201, "body": [{"a": 1}]}
        with mock.patch("providers.apify_actor.http_post", return_value=resp) as post:
            items, meta = run_actor("o~a", {"x": 1}, cap=500, requested_items=3, token="sekret", max_charge_usd=1.0)
        url = post.call_args.args[0]
        self.assertIn("o~a/run-sync-get-dataset-items", url)
        self.assertNotIn("sekret", url)
        self.assertEqual(post.call_args.kwargs["headers"], {"Authorization": "Bearer sekret"})
        self.assertIn("maxTotalChargeUsd=1.0", url)
        self.assertEqual(items, [{"a": 1}])
        self.assertEqual(meta["status"], "ok")

    def test_non_list_body_is_empty_items(self) -> None:
        resp = {"ok": False, "status_code": 400, "body": {"error": {"type": "x"}}}
        with mock.patch("providers.apify_actor.http_post", return_value=resp):
            items, meta = run_actor("o~a", {}, cap=5, requested_items=1, token="t")
        self.assertEqual(items, [])
        self.assertNotEqual(meta["status"], "ok")


class MappingTests(unittest.TestCase):
    def test_every_lane_maps_valid_records(self) -> None:
        for lane in LANES:
            recs = convert(lane)
            self.assertTrue(recs, lane)
            for r in recs:
                self.assertEqual(validate_record(r), [], lane)
                self.assertEqual(r["collection_method"], "third_party_scrape")
                self.assertEqual(r["retrieval_backend"], f"apify_{lane}")
                self.assertEqual(r["author_voice_status"], "unreviewed")
                self.assertIn("third-party scrape", r["sampling_metadata"]["subset_limitations"])

    def test_entity_lanes_are_entity_led_customer_reviews(self) -> None:
        expect = {"software_reviews": 3, "g2_reviews": 3, "shopify_app_reviews": 3}
        for lane, n in expect.items():
            recs = convert(lane)
            self.assertEqual(len(recs), n)
            for r in recs:
                self.assertEqual(r["sampling_frame"], "entity_led_feedback")
                self.assertEqual(r["subject_entity_id"], "ent-1")
                self.assertEqual(r["source_role"], "customer_review")
                self.assertEqual(r["source_intent"], "customer_feedback")
                self.assertIn("rating=", r["author_context"])
        self.assertEqual({r["source"] for r in convert("g2_reviews")}, {"g2_review"})
        self.assertEqual({r["source"] for r in convert("shopify_app_reviews")}, {"shopify_app_review"})

    def test_topic_lanes(self) -> None:
        for lane in ("quora", "facebook_public_groups"):
            for r in convert(lane):
                self.assertEqual(r["sampling_frame"], "topic_led_voc")
                self.assertEqual(r["subject_entity_id"] if "subject_entity_id" in r else "", "")
                self.assertNotEqual(r["source_role"], "customer_review")

    def test_field_values_follow_field_map(self) -> None:
        items = load_fixture("g2_reviews")
        r = convert("g2_reviews")[0]
        self.assertEqual(r["source_url"], items[0]["reviewUrl"])
        self.assertEqual(r["source_record_id"], items[0]["reviewId"])
        self.assertEqual(r["published_at"][:10], items[0]["date"])
        self.assertIn(items[0]["title"], r["text"])
        self.assertIn(items[0]["likes"][:40], r["text"])
        fb = convert("facebook_public_groups")
        raw = load_fixture("facebook_public_groups")[0]
        self.assertEqual(fb[0]["source_url"], raw["url"])
        self.assertEqual(len(fb), 1 + len(raw["topComments"]))
        self.assertEqual(fb[1]["parent_source_record_id"], fb[0]["source_record_id"])

    def test_shopify_reviews_without_ids_get_distinct_ids(self) -> None:
        recs = convert("shopify_app_reviews")
        self.assertEqual(len({r["evidence_id"] for r in recs}), len(recs))

    def test_incentivised_review_is_flagged(self) -> None:
        items = load_fixture("g2_reviews")
        items[0]["incentivized"] = True
        items[1]["incentivized"] = False
        recs = convert("g2_reviews", items)
        self.assertEqual(recs[0]["signal_quality"]["authenticity"], "incentivised")
        self.assertNotIn("signal_quality", recs[1])
        self.assertEqual(validate_record(recs[0]), [])

    def test_vendor_reply_is_a_separate_supplier_record(self) -> None:
        items = load_fixture("software_reviews")
        items[0]["vendorResponse"] = "Thanks for the feedback, we are improving this."
        recs = convert("software_reviews", items, extra_field_map={"vendorResponse": "vendor_reply"})
        replies = [r for r in recs if r["author_voice_status"] == "supplier_context"]
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0]["source_role"], "competitor_context")
        self.assertEqual(replies[0]["parent_source_record_id"], recs[0]["source_record_id"])
        self.assertNotIn("improving this", recs[0]["text"])
        self.assertEqual(validate_record(replies[0]), [])

    def test_records_do_not_carry_reviewer_names(self) -> None:
        for lane in LANES:
            for r in convert(lane):
                self.assertNotIn("redacted_user", r["author_context"] + r["text"], lane)

    def test_duplicate_text_is_dropped_by_content_hash(self) -> None:
        items = load_fixture("g2_reviews")
        dup = dict(items[0], reviewId="other", reviewUrl="https://www.g2.com/products/notion/reviews/other")
        recs = convert("g2_reviews", items + [dup])
        self.assertEqual(len(recs), len(items))


class FixtureHygieneTests(unittest.TestCase):
    def test_fixtures_carry_no_real_names(self) -> None:
        def walk(o, key=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    kl = k.lower()
                    if isinstance(v, str) and (kl in NAME_KEYS or kl.startswith("profile")):
                        self.assertEqual(v, "redacted_user", f"{key}/{k}")
                    walk(v, f"{key}/{k}")
            elif isinstance(o, list):
                for v in o:
                    walk(v, key)
            elif isinstance(o, str):
                self.assertNotIn("linkedin.com/in/", o)
                self.assertNotIn("scontent", o)
                self.assertIsNone(re.search(r"quora\.com/profile/|facebook\.com/(profile|people)", o), o)
        for lane in LANES:
            data = load_fixture(lane)
            self.assertTrue(data)
            walk(data, lane)


class CollectorTests(unittest.TestCase):
    def run_lane(self, lane: str, args, queries=("x",), body=None, secret=("APIFY_TOKEN", "t")):
        resp = {"ok": True, "status_code": 201, "body": body if body is not None else load_fixture(lane)}
        with mock.patch.object(collect, "get_secret", return_value=secret), \
                mock.patch("providers.apify_actor.http_post", return_value=resp) as post, \
                tempfile.TemporaryDirectory() as d:
            out = collect.collect_apify_lane(lane, args, list(queries), Path(d))
            raw = (Path(d) / "raw" / f"apify_{lane}.json").read_text()
        return out, post, raw

    def test_missing_token(self) -> None:
        (found, summary), post, _ = self.run_lane("quora", make_args(), secret=(None, None))
        self.assertEqual(summary["status"], "missing_credentials")
        post.assert_not_called()

    def test_software_review_collects_bound_target_and_hides_token(self) -> None:
        args = make_args(apify_review_targets="slack=https://www.trustradius.com/products/slack/reviews")
        with mock.patch.object(collect, "validate_entity_pairs_in_plan", return_value=(True, "authorized")):
            (found, summary), post, raw = self.run_lane("software_reviews", args)
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(len(found), 3)
        self.assertTrue(all(r["subject_entity_id"] == "slack" and validate_record(r) == [] for r in found))
        self.assertNotIn("Bearer", raw)
        self.assertEqual(post.call_args.kwargs["data"]["productUrls"], ["https://www.trustradius.com/products/slack/reviews"])
        self.assertEqual(post.call_args.kwargs["data"]["maxReviews"], 3)

    def test_unreviewed_entity_target_is_gated(self) -> None:
        args = make_args(apify_review_targets="slack=https://www.trustradius.com/products/slack/reviews")
        (found, summary), post, _ = self.run_lane("software_reviews", args)
        self.assertEqual(summary["status"], "capture_gate_blocked")
        post.assert_not_called()

    def test_wrong_host_target_is_not_sent_to_lane(self) -> None:
        args = make_args(apify_review_targets="x=https://www.g2.com/products/notion/reviews")
        with mock.patch.object(collect, "validate_entity_pairs_in_plan", return_value=(True, "authorized")):
            (found, summary), post, _ = self.run_lane("software_reviews", args)
        self.assertEqual(summary["status"], "not_run")
        post.assert_not_called()

    def test_cap_is_enforced_before_network_and_counts_across_lanes(self) -> None:
        args = make_args(limit=20, apify_review_item_cap=25)
        (_, s1), post, _ = self.run_lane("quora", args, queries=("a",))
        self.assertEqual(s1["status"], "ok")
        self.assertEqual(args._apify_review_items_used, 20)
        self.assertEqual(post.call_count, 1)
        (_, s2), post2, _ = self.run_lane("quora", args, queries=("b",))
        self.assertEqual(s2["status"], "request_budget_exhausted")
        post2.assert_not_called()

    def test_single_lane_cap_refusal(self) -> None:
        (_, summary), post, _ = self.run_lane("quora", make_args(limit=50, apify_review_item_cap=10), queries=("a", "b"))
        self.assertEqual(summary["status"], "request_budget_exhausted")
        post.assert_not_called()

    def test_facebook_groups_need_explicit_group_urls(self) -> None:
        (_, summary), post, _ = self.run_lane("facebook_public_groups", make_args())
        self.assertEqual(summary["status"], "not_run")
        post.assert_not_called()
        args = make_args(apify_facebook_groups="https://www.facebook.com/groups/63181993057/", limit=2)
        (found, summary), post, _ = self.run_lane("facebook_public_groups", args)
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(post.call_args.kwargs["data"]["resultsLimit"], 2)

    def test_blocked_lane_reports_status_without_call(self) -> None:
        with mock.patch("blocked.blocked_reason", return_value="gone"):
            (_, summary), post, _ = self.run_lane("quora", make_args())
        self.assertEqual(summary["status"], "blocked_by_provider")
        post.assert_not_called()

    def test_providers_are_registered(self) -> None:
        for lane in LANES:
            self.assertIn(f"apify_{lane}", collect.APIFY_LANE_PROVIDERS)


if __name__ == "__main__":
    unittest.main()
