#!/usr/bin/env python3
"""Tests for the Stack Exchange collector (no network)."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR, _collect_stackexchange_query
from providers import stackexchange
from providers.stackexchange import strip_html, to_records

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout" / "stackexchange_sample.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def validate_record(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=3, days=3650, customer_segment="", hypothesis_id="H1", topic="late invoices",
                problem_keywords="", workaround_keywords="", locale="", language="en",
                stackexchange_site="stackoverflow", sampling_frame="topic_led_voc", subject_entity_id="")
    base.update(kw)
    return argparse.Namespace(**base)


class StackExchangeTests(unittest.TestCase):
    def setUp(self) -> None:
        stackexchange.reset_throttle()

    def test_stackexchange_to_records(self) -> None:
        body = load_fixture()
        recs = to_records(body, "late invoice", "stackoverflow", "2026-10-30T00:00:00Z")
        self.assertEqual(len(recs), len(body["items"]))
        for r, item in zip(recs, body["items"]):
            self.assertEqual(validate_record(r), [])
            self.assertEqual(r["source"], "stackexchange")
            self.assertEqual(r["collection_method"], "official_api")
            self.assertEqual(r["retrieval_backend"], "stackexchange")
            self.assertEqual(r["source_url"], item["link"])
            self.assertNotIn("<p>", r["text"])
            self.assertNotIn("&lt;", r["text"])
            self.assertIn(item["title"], r["text"])
            self.assertEqual(r["engagement"]["upvotes"], item["score"])
            self.assertEqual(r["engagement"]["views"], item["view_count"])
            self.assertEqual(r["sampling_frame"], "topic_led_voc")

    def test_strip_html(self) -> None:
        self.assertEqual(strip_html("<p>a &lt;b&gt; <code>x&amp;y</code></p>\n<pre>z</pre>"), "a <b> x&y z")

    def test_missing_key_still_runs_keyless(self) -> None:
        resp = {"ok": True, "status_code": 200, "body": load_fixture()}
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.stackexchange.http_get", return_value=resp) as get:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_stackexchange_query(make_args(), ["invoice"], Path(d))
        self.assertEqual(summary["status"], "ok")
        self.assertTrue(found)
        url = get.call_args.args[0]
        self.assertNotIn("key=", url)
        self.assertIn("site=stackoverflow", url)
        self.assertIn("filter=withbody", url)
        self.assertIn("pagesize=3", url)

    def test_key_sent_but_not_stored(self) -> None:
        resp = {"ok": True, "status_code": 200, "final_url": "https://api.stackexchange.com/2.3/search/advanced?key=SEKRET99&q=x", "body": load_fixture()}
        with mock.patch.object(collect, "get_secret", return_value=("STACKEXCHANGE_KEY", "SEKRET99")), mock.patch("providers.stackexchange.http_get", return_value=resp) as get:
            with tempfile.TemporaryDirectory() as d:
                _collect_stackexchange_query(make_args(), ["invoice"], Path(d))
                raw = (Path(d) / "raw" / "stackexchange.json").read_text()
        self.assertIn("key=SEKRET99", get.call_args.args[0])
        self.assertNotIn("SEKRET99", raw)

    def test_site_is_configurable(self) -> None:
        resp = {"ok": True, "status_code": 200, "body": {"items": []}}
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.stackexchange.http_get", return_value=resp) as get:
            with tempfile.TemporaryDirectory() as d:
                _collect_stackexchange_query(make_args(stackexchange_site="money"), ["invoice"], Path(d))
        self.assertIn("site=money", get.call_args.args[0])

    def test_empty_result_is_ok(self) -> None:
        resp = {"ok": True, "status_code": 200, "body": {"items": [], "has_more": False, "quota_remaining": 250}}
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.stackexchange.http_get", return_value=resp):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_stackexchange_query(make_args(), ["zzz"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "ok"))

    def test_throttle_violation_reports_rate_limited(self) -> None:
        resp = {"ok": False, "status_code": 400, "body": {"error_id": 502, "error_message": "too many requests from this IP"}, "error": "400"}
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.stackexchange.http_get", return_value=resp):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_stackexchange_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "rate_limited"))

    def test_long_backoff_stops_without_sleeping(self) -> None:
        ok = {"ok": True, "status_code": 200, "body": {"items": [], "backoff": 120}}
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.stackexchange.http_get", return_value=ok) as get, mock.patch("providers.stackexchange.time.sleep") as sleep:
            with tempfile.TemporaryDirectory() as d:
                _collect_stackexchange_query(make_args(), ["a"], Path(d))
                found, summary = _collect_stackexchange_query(make_args(), ["b"], Path(d))
        self.assertEqual(summary["status"], "rate_limited")
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()

    def test_short_backoff_sleeps_within_cap(self) -> None:
        ok = {"ok": True, "status_code": 200, "body": {"items": [], "backoff": 5}}
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.stackexchange.http_get", return_value=ok), mock.patch("providers.stackexchange.time.sleep") as sleep:
            with tempfile.TemporaryDirectory() as d:
                _collect_stackexchange_query(make_args(), ["a"], Path(d))
                _, summary = _collect_stackexchange_query(make_args(), ["b"], Path(d))
        self.assertEqual(summary["status"], "ok")
        self.assertLessEqual(sleep.call_args.args[0], 5.1)

    def test_fixture_has_no_real_usernames(self) -> None:
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("display_name", "username", "author"):
                        self.assertEqual(v, "redacted_user")
                    self.assertNotIn(k, ("profile_image", "user_id", "account_id"))
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(load_fixture())


if __name__ == "__main__":
    unittest.main()
