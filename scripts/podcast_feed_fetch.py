#!/usr/bin/env python3
"""Discover podcast shows and enumerate company-focused RSS episodes."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

def load_provider_env() -> None:
    """Load .env from the repo root if present (stdlib-only shim)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    import os
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):]
        name, value = stripped.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def require_secret(name: str) -> str:
    import os
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"AUTH_FAILURE: missing {name}; set it in .env or the environment")
    return value



USER_AGENT = "financial-analyst-external-insights/1.0"
TRANSCRIPT_SUFFIX = "transcript"


def request_json(url: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> Any:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def request_bytes(url_or_path: str) -> bytes:
    path = Path(url_or_path)
    if path.exists():
        return path.read_bytes()
    req = urllib.request.Request(url_or_path, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def apple_search(query: str, limit: int) -> list[dict[str, Any]]:
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": query, "media": "podcast", "entity": "podcast", "limit": limit}
    )
    payload = request_json(url)
    return [
        {
            "provider": "apple",
            "show_id": item.get("collectionId"),
            "name": item.get("collectionName"),
            "publisher": item.get("artistName"),
            "feed_url": item.get("feedUrl"),
            "url": item.get("collectionViewUrl"),
        }
        for item in payload.get("results", [])
    ]


def podcastindex_search(query: str, limit: int) -> list[dict[str, Any]]:
    key = require_secret("PODCASTINDEX_API_KEY")
    secret = require_secret("PODCASTINDEX_API_SECRET")
    now = str(int(time.time()))
    auth = hashlib.sha1((key + secret + now).encode()).hexdigest()
    url = "https://api.podcastindex.org/api/1.0/search/byterm?" + urllib.parse.urlencode({"q": query, "max": limit})
    payload = request_json(url, {"X-Auth-Key": key, "X-Auth-Date": now, "Authorization": auth})
    return [
        {
            "provider": "podcastindex",
            "show_id": item.get("id"),
            "name": item.get("title"),
            "publisher": item.get("author"),
            "feed_url": item.get("url"),
            "url": item.get("link"),
        }
        for item in payload.get("feeds", [])
    ]


def spotify_search(query: str, limit: int) -> list[dict[str, Any]]:
    client_id = require_secret("SPOTIFY_CLIENT_ID")
    client_secret = require_secret("SPOTIFY_CLIENT_SECRET")
    token_data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    import base64
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token = request_json("https://accounts.spotify.com/api/token", {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}, token_data)["access_token"]
    url = "https://api.spotify.com/v1/search?" + urllib.parse.urlencode({"q": query, "type": "show", "limit": limit})
    payload = request_json(url, {"Authorization": f"Bearer {token}"})
    return [
        {
            "provider": "spotify",
            "show_id": item.get("id"),
            "name": item.get("name"),
            "publisher": item.get("publisher"),
            "feed_url": None,
            "url": (item.get("external_urls") or {}).get("spotify"),
        }
        for item in payload.get("shows", {}).get("items", [])
    ]


def child_text(node: ET.Element, local_name: str) -> str | None:
    for child in node:
        if child.tag.split("}")[-1].lower() == local_name.lower() and child.text:
            return child.text.strip()
    return None


def enumerate_feed(feed: str, company_terms: list[str]) -> list[dict[str, Any]]:
    root = ET.fromstring(request_bytes(feed))
    terms = [term.casefold() for term in company_terms if term.strip()]
    episodes: list[dict[str, Any]] = []
    for item in root.iter():
        if item.tag.split("}")[-1].lower() not in {"item", "entry"}:
            continue
        title = child_text(item, "title") or ""
        description = child_text(item, "description") or child_text(item, "summary") or ""
        haystack = f"{title}\n{description}".casefold()
        if terms and not any(term in haystack for term in terms):
            continue
        link = child_text(item, "link")
        guid = child_text(item, "guid") or child_text(item, "id")
        published = child_text(item, "pubDate") or child_text(item, "published") or child_text(item, "updated")
        transcripts = []
        enclosure = None
        for child in item:
            local = child.tag.split("}")[-1].lower()
            if local == TRANSCRIPT_SUFFIX and child.attrib.get("url"):
                transcripts.append({"url": child.attrib["url"], "type": child.attrib.get("type")})
            if local == "enclosure":
                enclosure = child.attrib.get("url")
            if local == "link" and child.attrib.get("href") and not link:
                link = child.attrib["href"]
        episodes.append({"guid": guid, "title": title, "description": description, "published": published, "url": link, "enclosure_url": enclosure, "transcripts": transcripts})
    return episodes


def write(payload: Any, output: str | None) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if output:
        path = Path(output); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(rendered, encoding="utf-8")
        print(path)
    else:
        print(rendered, end="")


def main() -> int:
    load_provider_env()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("--query", required=True); search.add_argument("--provider", choices=["apple", "podcastindex", "spotify", "all"], default="all"); search.add_argument("--limit", type=int, default=10); search.add_argument("--output")
    feed = sub.add_parser("episodes")
    feed.add_argument("--feed", required=True); feed.add_argument("--company", action="append", default=[]); feed.add_argument("--output")
    args = parser.parse_args()
    if args.command == "episodes":
        write({"feed": args.feed, "company_terms": args.company, "episodes": enumerate_feed(args.feed, args.company)}, args.output); return 0
    providers = [args.provider] if args.provider != "all" else ["apple", "podcastindex", "spotify"]
    shows: list[dict[str, Any]] = []; failures = []
    for provider in providers:
        try:
            shows.extend({"apple": apple_search, "podcastindex": podcastindex_search, "spotify": spotify_search}[provider](args.query, args.limit))
        except Exception as exc:
            failures.append({"provider": provider, "error": str(exc).splitlines()[0]})
    write({"query": args.query, "shows": shows, "failures": failures}, args.output); return 0


if __name__ == "__main__":
    from event_emit import emit_for_argv

    try:
        _status = main()
    except Exception as _exc:
        emit_for_argv(Path(__file__).stem, 2, f"{type(_exc).__name__}: {_exc}")
        raise
    emit_for_argv(Path(__file__).stem, _status)
    raise SystemExit(_status)
