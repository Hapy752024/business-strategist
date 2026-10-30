#!/usr/bin/env python3
"""Tests for the Reddit discovery-then-hydrate route (no network)."""

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
SEARCH = FIX / "reddit_hydrate_search_results.json"


def load(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def make_args(**kw) -> argparse.Namespace:
    base = dict(limit=20, days=30, customer_segment="", hypothesis_id="H1", topic="unpaid invoices",
                problem_keywords="", workaround_keywords="", locale="", language="en", apify_item_cap=300,
                reddit_comments_per_post=50, reddit_hydrate_from=str(SEARCH), reddit_hydrate_max=25,
                force_blocked=False)
    base.update(kw)
    return argparse.Namespace(**base)


def reddit_listing(post_id: str) -> list:
    return [{"data": {"children": [{"kind": "t3", "data": {"id": post_id, "title": "Synthetic API title", "selftext": "Synthetic API body about invoices.",
                                                           "subreddit": "example_sub", "author": "redacted_user", "ups": 4, "num_comments": 1,
                                                           "permalink": f"/r/example_sub/comments/{post_id}/synthetic_title/", "created_utc": 1790000000}}]}},
            {"data": {"children": [{"kind": "t1", "data": {"id": "k1", "body": "Synthetic API comment.", "author": "redacted_user", "ups": 1,
                                                           "permalink": f"/r/example_sub/comments/{post_id}/synthetic_title/k1/", "created_utc": 1790000100}}]}}]


def run(args=None, token=None, reddit_get=None, apify_token=None, apify_post=None, sc_key=None, sc_get=None):
    def secret(*names):
        if "APIFY_TOKEN" in names:
            return ("APIFY_TOKEN", apify_token) if apify_token else (None, None)
        return ("SCRAPE_CREATORS_API_KEY", sc_key) if sc_key else (None, None)
    reddit_get = reddit_get or mock.Mock(return_value={"ok": False, "status_code": 500, "body": None})
    apify_post = apify_post or mock.Mock(return_value={"ok": False, "status_code": 500, "body": None})
    sc_get = sc_get or mock.Mock(return_value={"ok": False, "status_code": 500, "body": None})
    with mock.patch.object(collect, "get_secret", side_effect=secret), \
            mock.patch.object(collect, "reddit_token", return_value=(token, {} if token else {"status": "missing_credentials"})), \
            mock.patch.object(collect, "http_get", reddit_get), \
            mock.patch("providers.apify_reddit.http_post", apify_post), \
            mock.patch("providers.scrapecreators_reddit.http_get", sc_get):
        with tempfile.TemporaryDirectory() as d:
            records, summary = collect.collect_reddit_hydrate(args or make_args(), [], Path(d))
    return records, summary, reddit_get, apify_post, sc_get


class HydrateTests(unittest.TestCase):
    def test_extract_dedupes_and_ignores_non_thread_urls(self) -> None:
        from providers.reddit_hydrate import extract_thread_refs
        refs = extract_thread_refs(SEARCH)
        self.assertEqual([r["post_id"] for r in refs], ["syn001", "syn002", "syn003"])
        self.assertTrue(all("/comments/" in r["url"] for r in refs))
        self.assertEqual(refs[0]["url"], "https://www.reddit.com/r/example_sub/comments/syn001/synthetic_title/")

    def test_extract_reads_jsonl(self) -> None:
        from providers.reddit_hydrate import extract_thread_refs
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.jsonl"
            p.write_text('{"source_url": "https://www.reddit.com/r/example_sub/comments/syn009/t/"}\n{"link": "https://www.reddit.com/r/example_sub/"}\n')
            self.assertEqual([r["post_id"] for r in extract_thread_refs(p)], ["syn009"])

    def test_reddit_hydrate_prefers_api_then_fallbacks(self) -> None:
        # API serves syn001; fails for syn002 (apify serves it); apify fails for syn003 (scrapecreators serves it).
        def reddit_get(url, **kw):
            if "syn001" in url:
                return {"ok": True, "status_code": 200, "body": reddit_listing("syn001")}
            return {"ok": False, "status_code": 403, "body": None}

        def apify_post(url, **kw):
            urls = [u["url"] for u in kw["data"]["startUrls"]]
            if "syn002" in urls[0]:
                return {"ok": True, "status_code": 200, "body": [
                    {"dataType": "post", "parsedId": "syn002", "url": urls[0], "title": "Synthetic apify title", "body": "Synthetic apify body.",
                     "parsedCommunityName": "example_sub", "username": "redacted_user", "upVotes": 1, "numberOfComments": 1, "createdAt": "2026-09-21T13:33:20.000Z"},
                    {"dataType": "comment", "parsedId": "ac1", "url": urls[0] + "ac1/", "body": "Synthetic apify comment.", "username": "redacted_user", "upVotes": 1}]}
            return {"ok": False, "status_code": 500, "body": None}
        sc_get = mock.Mock(return_value={"ok": True, "status_code": 200, "body": load("scrapecreators_reddit_thread_sample.json")})
        records, summary, rget, apost, sget = run(token="tok", reddit_get=reddit_get, apify_token="a", apify_post=apify_post, sc_key="k", sc_get=sc_get)
        by_id = {row["post_id"]: row for row in summary["hydrate_ledger"]}
        self.assertEqual([by_id[i]["backend"] for i in ("syn001", "syn002", "syn003")], ["reddit", "apify_reddit", "scrapecreators_reddit"])
        self.assertEqual(by_id["syn002"]["skipped"][0]["backend"], "reddit")
        self.assertEqual([s["backend"] for s in by_id["syn003"]["skipped"]], ["reddit", "apify_reddit"])
        self.assertEqual(by_id["syn001"]["skipped"], [])
        self.assertEqual(summary["status"], "ok")
        backends = {r["retrieval_backend"] for r in records}
        self.assertEqual(backends, {"reddit", "apify_reddit", "scrapecreators_reddit"})
        for r in records:
            self.assertEqual([e.message for e in EVIDENCE_VALIDATOR.iter_errors(r)], [])
            self.assertEqual(r["sampling_metadata"]["conversation_backend"], r["retrieval_backend"])
        self.assertEqual(sget.call_count, 1)

    def test_skip_reasons_when_no_credentials(self) -> None:
        records, summary, *_ = run(make_args(reddit_hydrate_max=1))
        row = summary["hydrate_ledger"][0]
        self.assertIsNone(row["backend"])
        self.assertEqual([(s["backend"], s["reason"]) for s in row["skipped"]],
                         [("reddit", "missing_credentials"), ("apify_reddit", "missing_credentials"),
                          ("scrapecreators_reddit", "missing_credentials")])
        self.assertEqual(records, [])
        self.assertEqual(summary["status"], "missing_credentials")

    def test_apify_item_cap_skips_to_scrapecreators(self) -> None:
        sc_get = mock.Mock(return_value={"ok": True, "status_code": 200, "body": load("scrapecreators_reddit_thread_sample.json")})
        _, summary, _, apost, _ = run(make_args(reddit_hydrate_max=1, apify_item_cap=5), apify_token="a", sc_key="k", sc_get=sc_get)
        apost.assert_not_called()
        row = summary["hydrate_ledger"][0]
        self.assertEqual(row["backend"], "scrapecreators_reddit")
        self.assertEqual(row["skipped"][1], {"backend": "apify_reddit", "reason": "request_budget_exhausted"})

    def test_apify_cap_counts_across_threads(self) -> None:
        # cap 10 = one thread at 10 items/post; second thread must not call Apify.
        ok = {"ok": True, "status_code": 200, "body": [{"dataType": "post", "parsedId": "x", "url": "https://www.reddit.com/r/example_sub/comments/x/t/", "title": "T", "body": "B", "parsedCommunityName": "example_sub", "username": "redacted_user"}]}
        apost = mock.Mock(return_value=ok)
        run(make_args(reddit_hydrate_max=3, apify_item_cap=10), apify_token="a", apify_post=apost)
        self.assertEqual(apost.call_count, 1)

    def test_max_threads_cap(self) -> None:
        _, summary, *_ = run(make_args(reddit_hydrate_max=2))
        self.assertEqual(len(summary["hydrate_ledger"]), 2)
        self.assertEqual(summary["threads_not_hydrated_over_max"], 1)

    def test_blocked_backend_skipped(self) -> None:
        def fake_blocked(cap, *a, **k):
            return "synthetic block" if cap == "apify_reddit" else None
        with mock.patch("blocked.blocked_reason", side_effect=fake_blocked):
            _, summary, _, apost, _ = run(make_args(reddit_hydrate_max=1), apify_token="a")
        apost.assert_not_called()
        self.assertEqual(summary["hydrate_ledger"][0]["skipped"][1], {"backend": "apify_reddit", "reason": "blocked_by_provider"})

    def test_sunset_skips_reddit_api_without_calling_it(self) -> None:
        rget = mock.Mock()
        with mock.patch.object(collect, "reddit_api_sunset_reached", return_value=True):
            _, summary, _, _, _ = run(make_args(reddit_hydrate_max=1), token="tok", reddit_get=rget)
        rget.assert_not_called()
        self.assertEqual(summary["hydrate_ledger"][0]["skipped"][0], {"backend": "reddit", "reason": "sunset"})

    def test_sunset_date_logic(self) -> None:
        from datetime import date
        self.assertFalse(collect.reddit_api_sunset_reached(date(2027, 3, 30)))
        self.assertTrue(collect.reddit_api_sunset_reached(date(2027, 3, 31)))

    def test_no_input_file(self) -> None:
        _, summary, *_ = run(make_args(reddit_hydrate_from=""))
        self.assertEqual(summary["status"], "not_applicable")


if __name__ == "__main__":
    unittest.main()
