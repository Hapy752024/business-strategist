#!/usr/bin/env python3
"""Tests for the Bluesky search collector (no network; synthetic fixture shaped after the lexicon docs)."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import collect
from collect import EVIDENCE_VALIDATOR, _collect_bluesky_query
from providers import bluesky
from providers.bluesky import to_records

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "evidence_scout" / "bluesky_sample.json"
PASSWORD = "abcd-efgh-ijkl-mnop"
JWT = "eyJ.SECRET.JWT"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def validate_record(record: dict) -> list[str]:
    return [e.message for e in EVIDENCE_VALIDATOR.iter_errors(record)]


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=5, days=30, customer_segment="", hypothesis_id="H1", topic="late invoices",
                problem_keywords="", workaround_keywords="", locale="", language="en",
                sampling_frame="topic_led_voc", subject_entity_id="")
    base.update(kw)
    return argparse.Namespace(**base)


def secrets(handle="me.bsky.social", password=PASSWORD):
    def fake(*names):
        if names[0] == "BLUESKY_HANDLE":
            return ("BLUESKY_HANDLE", handle) if handle else (None, None)
        if names[0] == "BLUESKY_APP_PASSWORD":
            return ("BLUESKY_APP_PASSWORD", password) if password else (None, None)
        return (None, None)
    return fake


SESSION_OK = {"ok": True, "status_code": 200, "body": {"accessJwt": JWT, "refreshJwt": "refresh.SECRET", "handle": "me.bsky.social", "did": "did:plc:me"}}


class BlueskyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.session_file = Path(self.tmp.name) / "bluesky-session.json"
        patcher = mock.patch.object(bluesky, "SESSION_PATH", self.session_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_query(self, args=None, queries=("late invoices",)):
        run_dir = Path(self.tmp.name) / "run"
        found, summary = _collect_bluesky_query(args or make_args(), list(queries), run_dir)
        raw = (run_dir / "raw" / "bluesky.json").read_text()
        return found, summary, raw

    def test_bluesky_to_records(self) -> None:
        body = load_fixture()
        recs = to_records(body, "late invoices", "2026-10-30T00:00:00Z")
        self.assertEqual(len(recs), 2)
        for r, post in zip(recs, body["posts"]):
            self.assertEqual(validate_record(r), [])
            self.assertEqual(r["source"], "bluesky")
            self.assertEqual(r["collection_method"], "official_api")
            self.assertEqual(r["retrieval_backend"], "bluesky")
            self.assertEqual(r["engagement"]["likes"], post["likeCount"])
            self.assertEqual(r["engagement"]["comments"], post["replyCount"])
            self.assertTrue(r["source_url"].startswith("https://bsky.app/profile/did:plc:"))
            self.assertNotIn("redacted_user", r["author_context"] + r["source_url"])
        self.assertTrue(recs[0]["source_url"].endswith("/post/3kaaaaaaaaa2a"))

    def test_missing_credentials(self) -> None:
        for handle, pw in ((None, None), ("me.bsky.social", None), (None, PASSWORD)):
            with mock.patch.object(collect, "get_secret", side_effect=secrets(handle, pw)), \
                    mock.patch("providers.bluesky.http_post") as post, mock.patch("providers.bluesky.http_get") as get:
                found, summary, _ = self.run_query()
            self.assertEqual((found, summary["status"]), ([], "missing_credentials"))
            self.assertEqual(summary["required_env"], ["BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"])
            post.assert_not_called()
            get.assert_not_called()

    def test_login_search_cache_and_no_secret_leak(self) -> None:
        search = {"ok": True, "status_code": 200, "body": load_fixture(), "headers": {}}
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post", return_value=SESSION_OK) as post, \
                mock.patch("providers.bluesky.http_get", return_value=search) as get:
            found, summary, raw = self.run_query(make_args(limit=2))
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(len(found), 2)
        self.assertEqual(post.call_args.kwargs["data"], {"identifier": "me.bsky.social", "password": PASSWORD})
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], f"Bearer {JWT}")
        url = get.call_args.args[0]
        self.assertIn("app.bsky.feed.searchPosts", url)
        self.assertIn("limit=2", url)
        self.assertIn("lang=en", url)
        cached = json.loads(self.session_file.read_text())
        self.assertEqual(cached["accessJwt"], JWT)
        self.assertNotIn(PASSWORD, self.session_file.read_text())
        self.assertNotIn("refresh.SECRET", self.session_file.read_text())
        for leaked in (PASSWORD, JWT, "refresh.SECRET"):
            self.assertNotIn(leaked, raw)
            self.assertNotIn(leaked, json.dumps(summary))
        self.assertNotIn(PASSWORD, "".join(r["text"] + r["author_context"] for r in found))

    def test_end_to_end_run_dir_has_no_secrets(self) -> None:
        """Scan every file the collector glue writes (raw, query captures, summary) for sentinel secrets."""
        search = {"ok": True, "status_code": 200, "body": load_fixture(), "headers": {}}
        run_dir = Path(self.tmp.name) / "e2e"
        args = make_args(limit=2)
        ledger_args = [args]
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post", return_value=SESSION_OK), \
                mock.patch("providers.bluesky.http_get", return_value=search):
            found, summary = collect.collect_scheduled_provider(args, ["late invoices"], run_dir, "bluesky")
            (run_dir / "summary.json").write_text(json.dumps({"summary": summary, "records": found}))
        files = [p for p in run_dir.rglob("*") if p.is_file()]
        self.assertTrue(any(p.name == "bluesky.json" for p in files))
        for path in files:
            text = path.read_text(errors="ignore")
            for sentinel in (PASSWORD, JWT, "refresh.SECRET"):
                self.assertNotIn(sentinel, text, f"{sentinel} leaked into {path}")

    def test_cached_session_is_reused_without_login(self) -> None:
        self.session_file.write_text(json.dumps({"handle": "me.bsky.social", "accessJwt": JWT, "created_at": bluesky.time.time()}))
        search = {"ok": True, "status_code": 200, "body": {"posts": []}, "headers": {}}
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post") as post, mock.patch("providers.bluesky.http_get", return_value=search):
            found, summary, _ = self.run_query()
        post.assert_not_called()
        self.assertEqual((found, summary["status"]), ([], "ok"))

    def test_expired_cached_session_relogins_once(self) -> None:
        self.session_file.write_text(json.dumps({"handle": "me.bsky.social", "accessJwt": "stale", "created_at": bluesky.time.time()}))
        expired = {"ok": False, "status_code": 400, "body": {"error": "ExpiredToken"}, "headers": {}, "error": "400"}
        good = {"ok": True, "status_code": 200, "body": load_fixture(), "headers": {}}
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post", return_value=SESSION_OK) as post, \
                mock.patch("providers.bluesky.http_get", side_effect=[expired, good]):
            found, summary, _ = self.run_query()
        self.assertEqual(post.call_count, 1)
        self.assertEqual((summary["status"], len(found)), ("ok", 2))

    def test_login_failure_is_reported(self) -> None:
        bad = {"ok": False, "status_code": 401, "body": {"error": "AuthenticationRequired"}, "error": "401"}
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post", return_value=bad), mock.patch("providers.bluesky.http_get") as get:
            found, summary, raw = self.run_query()
        self.assertEqual((found, summary["status"]), ([], "permission_denied"))
        get.assert_not_called()
        self.assertFalse(self.session_file.exists())
        self.assertNotIn(PASSWORD, raw)

    def test_empty_result_is_ok(self) -> None:
        search = {"ok": True, "status_code": 200, "body": {"posts": []}, "headers": {}}
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post", return_value=SESSION_OK), mock.patch("providers.bluesky.http_get", return_value=search):
            found, summary, _ = self.run_query()
        self.assertEqual((found, summary["status"]), ([], "ok"))

    def test_rate_limited_stops_without_sleeping(self) -> None:
        limited = {"ok": False, "status_code": 429, "body": {}, "headers": {"ratelimit-reset": "300"}, "error": "429"}
        with mock.patch.object(collect, "get_secret", side_effect=secrets()), \
                mock.patch("providers.bluesky.http_post", return_value=SESSION_OK), \
                mock.patch("providers.bluesky.http_get", return_value=limited) as get, mock.patch("time.sleep") as sleep:
            found, summary, _ = self.run_query(queries=("a", "b"))
        self.assertEqual((found, summary["status"]), ([], "rate_limited"))
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()

    def test_session_cache_dir_is_gitignored(self) -> None:
        self.assertIn(".research-infra/", (ROOT / ".gitignore").read_text().splitlines())

    def test_fixture_has_no_real_usernames(self) -> None:
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("handle", "displayName"):
                        self.assertEqual(v, "redacted_user")
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(load_fixture())


if __name__ == "__main__":
    unittest.main()
