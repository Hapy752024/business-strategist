#!/usr/bin/env python3
"""Tests for the ScrapeCreators Reddit and Arctic Shift collectors (no network)."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout"


def load(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def errors(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=3, days=30, customer_segment="", hypothesis_id="H1", subreddit="example_sub",
                topic="unpaid invoices", problem_keywords="", workaround_keywords="", locale="", language="en",
                reddit_comment_posts=1, reddit_comments_per_post=50, force_blocked=False)
    base.update(kw)
    return argparse.Namespace(**base)


def resp(body, code=200, headers=None):
    ok = code < 400
    return {"ok": ok, "status_code": code, "body": body, "headers": headers or {}}


class ScrapeCreatorsRedditTests(unittest.TestCase):
    def test_search_records(self) -> None:
        from providers.scrapecreators_reddit import search_to_records
        recs = search_to_records(load("scrapecreators_reddit_search_sample.json")["posts"], "invoice", "2026-10-30T00:00:00Z")
        self.assertEqual(len(recs), 2)
        for r in recs:
            self.assertEqual(errors(r), [])
            self.assertEqual(r["source"], "reddit")
            self.assertEqual(r["collection_method"], "third_party_api")
            self.assertEqual(r["retrieval_backend"], "scrapecreators_reddit")
            self.assertEqual(r["author_voice_status"], "unreviewed")

    def test_thread_records_flatten_nested_replies(self) -> None:
        from providers.scrapecreators_reddit import thread_to_records
        recs = thread_to_records(load("scrapecreators_reddit_thread_sample.json"), "invoice", "2026-10-30T00:00:00Z")
        self.assertEqual([r["source"] for r in recs], ["reddit", "reddit_comment", "reddit_comment"])
        self.assertEqual(recs[1]["parent_source_record_id"], "syn001")
        self.assertTrue(all(errors(r) == [] for r in recs))

    def test_missing_credentials(self) -> None:
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.scrapecreators_reddit.http_get") as get:
            with tempfile.TemporaryDirectory() as d:
                found, summary = collect._collect_scrapecreators_reddit_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "missing_credentials"))
        get.assert_not_called()

    def test_search_then_comments_with_mocked_http_and_key_not_leaked(self) -> None:
        calls = []

        def fake_get(url, **kw):
            calls.append((url, kw.get("headers")))
            if "/v1/reddit/search" in url:
                return resp(load("scrapecreators_reddit_search_sample.json"))
            return resp(load("scrapecreators_reddit_thread_sample.json"))
        with mock.patch.object(collect, "get_secret", return_value=("SCRAPE_CREATORS_API_KEY", "sekret-key")), \
                mock.patch("providers.scrapecreators_reddit.http_get", side_effect=fake_get):
            with tempfile.TemporaryDirectory() as d:
                found, summary = collect._collect_scrapecreators_reddit_query(make_args(), ["invoice"], Path(d))
                raw = (Path(d) / "raw" / "scrapecreators_reddit.json").read_text()
        self.assertEqual(summary["status"], "ok")
        self.assertTrue(any(r["source"] == "reddit_comment" for r in found))
        self.assertEqual(calls[0][1], {"x-api-key": "sekret-key"})
        self.assertNotIn("sekret-key", raw)
        self.assertEqual(len([c for c in calls if "post/comments" in c[0]]), 1)

    def test_existing_comment_fallbacks_share_provider_code(self) -> None:
        import inspect
        src = inspect.getsource(collect)
        self.assertEqual(src.count("api.scrapecreators.com/v1/reddit/post/comments"), 0)


class ArcticShiftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sleeps: list[float] = []
        import providers.arctic_shift as a
        self.mod = a
        a._reset_throttle()

    def test_requires_subreddit(self) -> None:
        with mock.patch("providers.arctic_shift.http_get") as get:
            with tempfile.TemporaryDirectory() as d:
                found, summary = collect._collect_arctic_shift_query(make_args(subreddit=""), ["x"], Path(d))
        self.assertEqual(summary["status"], "subreddit_required")
        get.assert_not_called()

    def test_records(self) -> None:
        recs = self.mod.posts_to_records(load("arctic_shift_posts_sample.json")["data"], "invoice", "2026-10-30T00:00:00Z") + \
            self.mod.comments_to_records(load("arctic_shift_comments_sample.json")["data"], "invoice", "2026-10-30T00:00:00Z")
        self.assertEqual([r["source"] for r in recs], ["reddit", "reddit_comment"])
        for r in recs:
            self.assertEqual(errors(r), [])
            self.assertEqual(r["collection_method"], "community_archive")
            self.assertEqual(r["retrieval_backend"], "arctic_shift")
            self.assertIn("volunteer", r["sampling_metadata"]["subset_limitations"])
        self.assertEqual(recs[1]["parent_source_record_id"], "syn101")

    def test_backoff_then_rate_limited_bounded(self) -> None:
        timeout = resp({"data": None, "error": "Timeout. Maybe slow down a bit"}, 422)
        with mock.patch("providers.arctic_shift.http_get", return_value=timeout) as get:
            body, meta = self.mod.get_json("posts/search", {"subreddit": "example_sub"}, sleep=self.sleeps.append, clock=lambda: 0.0)
        self.assertEqual(meta["status"], "rate_limited")
        self.assertEqual(get.call_count, 4)  # first try + 3 backoffs
        self.assertLessEqual(sum(self.sleeps), 30)
        self.assertEqual(self.sleeps.count(5), 3)

    def test_long_ratelimit_reset_is_not_slept(self) -> None:
        timeout = resp({"data": None, "error": "Timeout. Maybe slow down a bit"}, 422, {"x-ratelimit-reset": "57"})
        with mock.patch("providers.arctic_shift.http_get", return_value=timeout) as get:
            _, meta = self.mod.get_json("posts/search", {"subreddit": "s"}, sleep=self.sleeps.append, clock=lambda: 0.0)
        self.assertEqual(meta["status"], "rate_limited")
        self.assertEqual(get.call_count, 1)
        self.assertEqual(sum(self.sleeps), 0)

    def test_short_ratelimit_reset_honoured(self) -> None:
        timeout = resp({"data": None, "error": "Timeout. Maybe slow down a bit"}, 422, {"x-ratelimit-reset": "2"})
        ok = resp(load("arctic_shift_posts_sample.json"))
        with mock.patch("providers.arctic_shift.http_get", side_effect=[timeout, ok]):
            body, meta = self.mod.get_json("posts/search", {"subreddit": "s"}, sleep=self.sleeps.append, clock=lambda: 0.0)
        self.assertEqual(meta["status"], "ok")
        self.assertIn(2, self.sleeps)

    def test_throttle_spaces_requests_one_second(self) -> None:
        now = [100.0]
        ok = resp({"data": []})
        with mock.patch("providers.arctic_shift.http_get", return_value=ok):
            self.mod.get_json("posts/search", {"subreddit": "s"}, sleep=self.sleeps.append, clock=lambda: now[0])
            self.mod.get_json("posts/search", {"subreddit": "s"}, sleep=self.sleeps.append, clock=lambda: now[0] + 0.25)
        self.assertTrue(any(abs(s - 0.75) < 1e-6 for s in self.sleeps))

    def test_collector_posts_then_comments(self) -> None:
        def fake(url, **kw):
            return resp(load("arctic_shift_comments_sample.json") if "comments/search" in url else load("arctic_shift_posts_sample.json"))
        with mock.patch("providers.arctic_shift.http_get", side_effect=fake), mock.patch("providers.arctic_shift.time.sleep"):
            with tempfile.TemporaryDirectory() as d:
                found, summary = collect._collect_arctic_shift_query(make_args(), ["invoice"], Path(d))
        self.assertEqual(summary["status"], "ok")
        self.assertEqual({r["source"] for r in found}, {"reddit", "reddit_comment"})


if __name__ == "__main__":
    unittest.main()
