#!/usr/bin/env python3
"""Every fixture under fixtures/evidence_scout/ must be free of real people, places and live URLs."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "evidence_scout"
ALWAYS_NAME_KEYS = {"username", "displayname", "display_name", "reviewername", "handle", "reviewercompany", "store", "reviewermonogram"}
PARENT_NAME_KEYS = {"user", "author", "owner", "collaborators", "makers"}
# Licensed (CFPB CC0, Stack Exchange CC BY-SA) or documented-synthetic fixtures may keep their own source hosts.
HOST_EXEMPT = {
    "cfpb_sample.json": set(),
    "stackexchange_sample.json": {"stackoverflow.com", "i.sstatic.net", "docs.stripe.com"},
    "bluesky_sample.json": {"docs.bsky.app"},
    "producthunt_sample.json": {"api.producthunt.com", "www.producthunt.com"},
}
# Synthetic reddit thread URLs for the hydrate route parse as reddit URLs, so example.com is not usable.
# Exempt only r/example_sub thread/subreddit URLs and the redacted_user user page.
SYNTHETIC_REDDIT_FIXTURE = "reddit_hydrate_search_results.json"
SYNTHETIC_REDDIT_URL = re.compile(r"^https://(www|old)\.reddit\.com/(r/example_sub(/.*)?|user/redacted_user/)$")
SAFE_HOSTS = {"example.com", "www.example.com", "example.org", "www.example.org"}
DENYLIST = ["63181993057", "People Relocating", "Charlotte", "Concord", "Uwe-Dreissigacker", "Dreissigacker", "Allan-B",
            "InvoiceBerry", "LessFilms", "linkedin.com/in/", "scontent", "fbcdn"]


def strings(node, key="", parent=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from strings(v, k, key)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v, key, parent)
    elif isinstance(node, str):
        yield key, parent, node


class FixturePrivacyTests(unittest.TestCase):
    def test_fixtures_exist(self) -> None:
        self.assertGreaterEqual(len(list(FIXTURES.glob("*.json"))), 10)

    def test_every_fixture_is_private_by_construction(self) -> None:
        for path in sorted(FIXTURES.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            exempt = HOST_EXEMPT.get(path.name)
            for needle in DENYLIST:
                self.assertNotIn(needle.lower(), text.lower(), f"{path.name}: {needle}")
            for key, parent, value in strings(json.loads(text)):
                kl, pl = key.lower(), parent.lower()
                if kl in ALWAYS_NAME_KEYS or kl.startswith("profile") or (kl == "name" and pl in PARENT_NAME_KEYS):
                    self.assertEqual(value, "redacted_user", f"{path.name}: {parent}/{key}")
                for url in re.findall(r"https?://[^\s\"'<>)]+", value):
                    host = urlparse(url).netloc.lower()
                    if path.name == SYNTHETIC_REDDIT_FIXTURE and host.endswith("reddit.com"):
                        base = url.split("?")[0]
                        self.assertRegex(base, SYNTHETIC_REDDIT_URL, f"{path.name}: non-synthetic reddit URL {url}")
                        continue
                    allowed = SAFE_HOSTS | (exempt or set())
                    self.assertIn(host, allowed, f"{path.name}: live URL host {host}")
                    self.assertIsNone(re.search(r"/(profile|people|user|users)/[^/]", url), f"{path.name}: profile URL {url}")


if __name__ == "__main__":
    unittest.main()
