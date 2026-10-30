#!/usr/bin/env python3
"""Tests for the Apify Reddit fallback collector (no network)."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR, _collect_apify_reddit_query, collect_apify_reddit
from providers.apify_reddit import to_records

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout" / "apify_reddit_sample.json"


def load_fixture() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def validate_record(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=3, days=30, customer_segment="", hypothesis_id="H1", apify_item_cap=300,
                topic="unpaid invoices", problem_keywords="", workaround_keywords="", locale="", language="en")
    base.update(kw)
    return argparse.Namespace(**base)


class ApifyRedditTests(unittest.TestCase):
    def test_to_records_maps_post_and_comments(self) -> None:
        items = load_fixture()
        recs = to_records(items, "invoice chasing small business", "2026-10-30T00:00:00Z")
        posts = [r for r in recs if r["source"] == "reddit"]
        comments = [r for r in recs if r["source"] == "reddit_comment"]
        self.assertEqual(len(posts), 3)
        self.assertEqual(len(comments), sum(len(i["comments"]) for i in items))
        for r in recs:
            self.assertEqual(validate_record(r), [])
            self.assertEqual(r["sampling_frame"], "topic_led_voc")
            self.assertEqual(r["author_voice_status"], "unreviewed")
        self.assertEqual(posts[0]["source_url"], items[0]["url"])
        self.assertEqual(posts[0]["engagement"]["upvotes"], items[0]["upVotes"])
        self.assertEqual(posts[0]["engagement"]["comments"], items[0]["numberOfComments"])
        c = comments[0]
        self.assertEqual(c["source_record_id"], f"{items[0]['parsedId']}/{items[0]['comments'][0]['parsedId']}")
        self.assertEqual(c["parent_source_record_id"], items[0]["parsedId"])

    def test_missing_token(self) -> None:
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.apify_reddit.http_post") as post:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_apify_reddit_query(make_args(), ["x"], Path(d))
        self.assertEqual(found, [])
        self.assertEqual(summary["status"], "missing_credentials")
        post.assert_not_called()

    def test_cap_enforced_before_network(self) -> None:
        with mock.patch.object(collect, "get_secret", return_value=("APIFY_TOKEN", "t")), mock.patch("providers.apify_reddit.http_post") as post:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_apify_reddit_query(make_args(limit=50, apify_item_cap=10), ["x"], Path(d))
                self.assertEqual(summary["status"], "request_budget_exhausted")
                found2, summary2 = collect_apify_reddit(make_args(limit=50, apify_item_cap=10), ["x", "y"], Path(d))
                self.assertEqual(summary2["status"], "request_budget_exhausted")
        post.assert_not_called()

    def test_query_collects_with_mocked_actor(self) -> None:
        resp = {"ok": True, "status_code": 200, "body": load_fixture()}
        with mock.patch.object(collect, "get_secret", return_value=("APIFY_TOKEN", "secret-token")), mock.patch("providers.apify_reddit.http_post", return_value=resp) as post:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_apify_reddit_query(make_args(), ["invoice"], Path(d))
                raw = (Path(d) / "raw" / "apify_reddit.json").read_text()
        self.assertEqual(summary["status"], "ok")
        self.assertTrue(found and all(validate_record(r) == [] for r in found))
        self.assertNotIn("secret-token", raw)
        self.assertEqual(post.call_args.kwargs["data"]["maxItems"], 3)

    def test_fixture_has_no_real_usernames(self) -> None:
        import re

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("username", "author"):
                        self.assertEqual(v, "redacted_user")
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, str):
                for m in re.findall(r"(?<![\w/])/?u/([A-Za-z0-9_-]+)", o):
                    self.assertEqual(m, "redacted_user")
        walk(load_fixture())

    def test_records_marked_third_party_scrape(self) -> None:
        for r in to_records(load_fixture(), "q", "2026-10-30T00:00:00Z"):
            self.assertEqual(r["collection_method"], "third_party_scrape")
            self.assertEqual(r["retrieval_backend"], "apify_reddit")
            self.assertIn("third-party scrape", r["sampling_metadata"]["subset_limitations"])

    def test_review_packet_surfaces_backend(self) -> None:
        from build_review_packet import build
        recs = to_records(load_fixture(), "q", "2026-10-30T00:00:00Z")
        packet = build({}, recs, [], [], {})
        self.assertEqual(packet["items"][0]["retrieval_backend"], "apify_reddit")
        self.assertEqual(packet["items"][0]["collection_method"], "third_party_scrape")

    def test_cap_math_counts_comments(self) -> None:
        # 5 posts x 10 items = 50 > cap 49 refuses; cap 50 passes the guard.
        with mock.patch.object(collect, "get_secret", return_value=("APIFY_TOKEN", "t")), mock.patch("providers.apify_reddit.http_post", return_value={"ok": True, "status_code": 200, "body": []}) as post:
            with tempfile.TemporaryDirectory() as d:
                _, s1 = _collect_apify_reddit_query(make_args(limit=5, apify_item_cap=49), ["x"], Path(d))
                self.assertEqual(s1["status"], "request_budget_exhausted")
                post.assert_not_called()
                _collect_apify_reddit_query(make_args(limit=5, apify_item_cap=50), ["x"], Path(d))
                post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
