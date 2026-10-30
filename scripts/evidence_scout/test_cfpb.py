#!/usr/bin/env python3
"""Tests for the CFPB consumer complaint collector (no network).

The recorded fixture is a real 2026-10-30 response. The live public API no
longer returns narrative text, so narrative-bearing hits are synthesized from
the documented legacy shape (``complaint_what_happened``) inside the tests.
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR, _collect_cfpb_complaints_query
from providers.cfpb import to_records

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "evidence_scout" / "cfpb_sample.json"
NARRATIVE = "XXXX charged me three overdraft fees in one day. I called twice and nobody fixed it."


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def with_narratives() -> dict:
    body = copy.deepcopy(load_fixture())
    for hit in body["hits"]["hits"]:
        hit["_source"]["complaint_what_happened"] = NARRATIVE
    return body


def validate_record(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=3, days=30, customer_segment="", hypothesis_id="H1", topic="overdraft fees",
                problem_keywords="", workaround_keywords="", locale="", language="en",
                sampling_frame="topic_led_voc", subject_entity_id="")
    base.update(kw)
    return argparse.Namespace(**base)


class CfpbTests(unittest.TestCase):
    def test_cfpb_to_records(self) -> None:
        body = with_narratives()
        recs = to_records(body, "overdraft fee", "2026-10-30T00:00:00Z")
        self.assertEqual(len(recs), 3)
        for r, hit in zip(recs, body["hits"]["hits"]):
            self.assertEqual(validate_record(r), [])
            self.assertEqual(r["source"], "cfpb_complaint")
            self.assertEqual(r["author_voice_status"], "unreviewed")
            self.assertEqual(r["collection_method"], "official_api")
            self.assertEqual(r["retrieval_backend"], "cfpb_complaints")
            self.assertIn("XXXX", r["text"])
            self.assertIn(hit["_source"]["product"], r["author_context"])
            self.assertIn(hit["_source"]["issue"], r["author_context"])
            self.assertIn(hit["_source"]["company"], r["author_context"])
            self.assertIn(hit["_source"]["state"], r["author_context"])
            self.assertNotIn(hit["_source"]["zip_code"], json.dumps(r))
            self.assertEqual(r["published_at"][:10], hit["_source"]["date_received"][:10])
            self.assertIn(hit["_source"]["complaint_id"], r["source_url"])
        self.assertEqual(recs[0]["source_role"], "customer_statement")

    def test_hits_without_narrative_yield_no_records(self) -> None:
        self.assertEqual(to_records(load_fixture(), "q", "2026-10-30T00:00:00Z"), [])

    def test_cfpb_empty_result_is_ok(self) -> None:
        empty = {"hits": {"total": {"value": 0, "relation": "eq"}, "hits": []}}
        resp = {"ok": True, "status_code": 200, "body": empty}
        with mock.patch("providers.cfpb.http_get", return_value=resp):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_cfpb_complaints_query(make_args(), ["nothing"], Path(d))
        self.assertEqual(found, [])
        self.assertEqual(summary["status"], "ok")

    def test_query_collects_and_respects_limit(self) -> None:
        resp = {"ok": True, "status_code": 200, "body": with_narratives()}
        with mock.patch("providers.cfpb.http_get", return_value=resp) as get:
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_cfpb_complaints_query(make_args(limit=2), ["overdraft"], Path(d))
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(len(found), 2)
        self.assertIn("size=2", get.call_args.args[0])
        self.assertIn("has_narrative=true", get.call_args.args[0])
        self.assertTrue(all(validate_record(r) == [] for r in found))

    def test_rate_limited_is_reported(self) -> None:
        resp = {"ok": False, "status_code": 429, "body": {}, "error": "429"}
        with mock.patch("providers.cfpb.http_get", return_value=resp):
            with tempfile.TemporaryDirectory() as d:
                found, summary = _collect_cfpb_complaints_query(make_args(), ["x"], Path(d))
        self.assertEqual((found, summary["status"]), ([], "rate_limited"))

    def test_no_credentials_required(self) -> None:
        from collect import PROVIDER_ROUTING_FAMILY
        self.assertEqual(PROVIDER_ROUTING_FAMILY["cfpb_complaints"], "customer_reviews")


if __name__ == "__main__":
    unittest.main()
