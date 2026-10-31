#!/usr/bin/env python3
"""Tests for the Product Hunt collector (no network; synthetic fixture shaped after the v2 GraphQL docs)."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR, _collect_producthunt_query
from providers.producthunt import to_records

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout" / "producthunt_sample.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def validate_record(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=10, days=3650, customer_segment="", hypothesis_id="H1", topic="late invoices",
                problem_keywords="", workaround_keywords="", locale="", language="en",
                sampling_frame="topic_led_voc", subject_entity_id="")
    base.update(kw)
    return argparse.Namespace(**base)


def fake_post(responses):
    it = iter(responses)
    return mock.patch("providers.producthunt.http_post", side_effect=lambda *a, **k: next(it))


class ProductHuntTests(unittest.TestCase):
    def test_producthunt_to_records(self) -> None:
        recs = to_records(load_fixture()["posts"], "late invoices", "2026-10-30T00:00:00Z")
        posts = [r for r in recs if r["source"] == "producthunt"]
        comments = [r for r in recs if r["source"] == "producthunt_comment"]
        self.assertEqual((len(posts), len(comments)), (1, 3))
        for r in recs:
            self.assertEqual(validate_record(r), [])
            self.assertEqual(r["collection_method"], "official_api")
            self.assertEqual(r["retrieval_backend"], "producthunt")
            self.assertEqual(r["sampling_frame"], "topic_led_voc")
        customer = next(r for r in comments if "Friday" in r["text"])
        self.assertEqual(customer["author_voice_status"], "unreviewed")
        self.assertNotEqual(customer["source_role"], "competitor_context")
        self.assertEqual(customer["parent_source_record_id"], "1001")
        self.assertEqual(customer["engagement"]["upvotes"], 12)

    def test_maker_comments_and_launch_copy_are_supplier(self) -> None:
        recs = to_records(load_fixture()["posts"], "q", "2026-10-30T00:00:00Z")
        by_text = {r["text"][:20]: r for r in recs}
        for r in recs:
            if "Xero sync ships" in r["text"] or "spreadsheet reminder" in r["text"] or r["source"] == "producthunt":
                self.assertEqual(r["author_voice_status"], "supplier_context", r["text"])
                self.assertEqual(r["source_role"], "competitor_context")
        self.assertEqual(len([r for r in recs if r["author_voice_status"] == "supplier_context"]), 3)
        self.assertEqual(len(by_text), len(recs))

    def test_entity_led_frame(self) -> None:
        recs = to_records(load_fixture()["posts"], "InvoiceNudge", "2026-10-30T00:00:00Z",
                          sampling_frame="entity_led_feedback", subject_entity_id="ent-1")
        self.assertTrue(all(r["sampling_frame"] == "entity_led_feedback" and r["subject_entity_id"] == "ent-1" for r in recs))
        self.assertTrue(all(validate_record(r) == [] for r in recs))

    def test_missing_token(self) -> None:
        with mock.patch.object(collect, "get_secret", return_value=(None, None)), mock.patch("providers.producthunt.http_post") as post:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_producthunt_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "missing_credentials"))
        self.assertEqual(summary["required_env"], ["PRODUCTHUNT_TOKEN"])
        post.assert_not_called()

    def test_query_collects_and_hides_token(self) -> None:
        fx = load_fixture()
        with mock.patch.object(collect, "get_secret", return_value=("PRODUCTHUNT_TOKEN", "tok-SECRET-1")), \
                fake_post([{"ok": True, "status_code": 200, "body": fx["topics"], "headers": {}},
                           {"ok": True, "status_code": 200, "body": fx["posts"], "headers": {}}]) as post:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_producthunt_query(make_args(), ["late invoices"], Path(d))
                raw = (Path(d) / "raw" / "producthunt.json").read_text()
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(len(found), 4)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer tok-SECRET-1")
        self.assertNotIn("tok-SECRET-1", raw)

    def test_limit_caps_records(self) -> None:
        fx = load_fixture()
        with mock.patch.object(collect, "get_secret", return_value=("PRODUCTHUNT_TOKEN", "t")), \
                fake_post([{"ok": True, "status_code": 200, "body": fx["topics"], "headers": {}},
                           {"ok": True, "status_code": 200, "body": fx["posts"], "headers": {}}]):
            with tempfile.TemporaryDirectory() as d:
                found, _ = _collect_producthunt_query(make_args(limit=2), ["late invoices"], Path(d))
        self.assertEqual(len(found), 2)

    def test_no_matching_topic_is_ok_and_empty(self) -> None:
        empty = {"data": {"topics": {"edges": []}}}
        with mock.patch.object(collect, "get_secret", return_value=("PRODUCTHUNT_TOKEN", "t")), \
                fake_post([{"ok": True, "status_code": 200, "body": empty, "headers": {}}]):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_producthunt_query(make_args(), ["zzz"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "ok"))

    def test_empty_posts_is_ok(self) -> None:
        fx = load_fixture()
        none = {"data": {"posts": {"edges": []}}}
        with mock.patch.object(collect, "get_secret", return_value=("PRODUCTHUNT_TOKEN", "t")), \
                fake_post([{"ok": True, "status_code": 200, "body": fx["topics"], "headers": {}},
                           {"ok": True, "status_code": 200, "body": none, "headers": {}}]):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_producthunt_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "ok"))

    def test_rate_limited_stops(self) -> None:
        resp = {"ok": False, "status_code": 429, "body": {"errors": [{"error": "rate_limit_reached"}]}, "headers": {"x-rate-limit-reset": "600"}, "error": "429"}
        with mock.patch.object(collect, "get_secret", return_value=("PRODUCTHUNT_TOKEN", "t")), fake_post([resp]) as post:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_producthunt_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "rate_limited"))
        self.assertEqual(post.call_count, 1)

    def test_graphql_errors_are_failures_not_empty(self) -> None:
        resp = {"ok": True, "status_code": 200, "body": {"errors": [{"message": "bad query"}]}, "headers": {}}
        with mock.patch.object(collect, "get_secret", return_value=("PRODUCTHUNT_TOKEN", "t")), fake_post([resp]):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_producthunt_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "failed"))

    def test_fixture_has_no_real_usernames(self) -> None:
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("username", "name") and isinstance(v, str) and k == "username":
                        self.assertEqual(v, "redacted_user")
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(load_fixture())


if __name__ == "__main__":
    unittest.main()
