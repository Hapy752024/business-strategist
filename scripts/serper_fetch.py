#!/usr/bin/env python3
"""Fetch Google/web/news results through Serper.dev for business-strategist research."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SERPER_ENDPOINTS = {
    "search": "https://google.serper.dev/search",
    "news": "https://google.serper.dev/news",
}


class SerperError(RuntimeError):
    pass


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return values
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :]
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip().strip('"').strip("'")
    return values


def load_local_env() -> None:
    for path in (ROOT / ".env", Path.home() / ".secrets"):
        for key, value in read_env_file(path).items():
            os.environ.setdefault(key, value)


def classify_api_failure(message: str, status: int | None = None) -> str:
    lowered = message.lower()
    if status in {401, 403} or "unauthorized" in lowered or "invalid" in lowered:
        return "AUTH_FAILURE"
    if status in {402, 429} or "quota" in lowered or "credit" in lowered or "limit" in lowered:
        return "NO_CREDITS_OR_QUOTA" if "credit" in lowered or "quota" in lowered else "RATE_LIMITED"
    return "API_FAILURE"


def require_key() -> str:
    load_local_env()
    key = os.environ.get("SERPER_DEV_API_KEY") or os.environ.get("SERPER_API_KEY")
    if not key:
        raise SerperError("AUTH_FAILURE: Missing SERPER_DEV_API_KEY. Add it to ~/.secrets or .env and mark Serper data unavailable.")
    return key


def request_json(endpoint: str, payload: dict[str, Any], timeout: int = 45) -> dict[str, Any]:
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"X-API-KEY": require_key(), "Content-Type": "application/json", "User-Agent": "business-strategist-agent/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        kind = classify_api_failure(body, exc.code)
        raise SerperError(f"{kind}: HTTP {exc.code} from Serper.dev. Mark Serper data unavailable: {body[:800]}") from exc
    except urllib.error.URLError as exc:
        raise SerperError(f"NETWORK_FAILURE: Network error contacting Serper.dev. Mark Serper data unavailable: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise SerperError(f"API_FAILURE: Serper.dev returned non-JSON response: {exc}") from exc


def compact_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "search_parameters": payload.get("searchParameters"),
        "organic_results": payload.get("organic", []),
        "news_results": payload.get("news", []),
        "top_stories": payload.get("topStories", []),
        "people_also_ask": payload.get("peopleAlsoAsk", []),
        "related_searches": payload.get("relatedSearches", []),
        "credits": payload.get("credits"),
    }


def search(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {"q": args.query, "num": max(1, min(args.num, 100)), "gl": args.gl, "hl": args.hl}
    if args.location:
        payload["location"] = args.location
    if args.time_period:
        payload["tbs"] = args.time_period
    raw = request_json(SERPER_ENDPOINTS[args.engine], payload, timeout=args.timeout)
    result = compact_result(raw) if args.compact else raw
    result["type"] = "serper_search"
    result["engine"] = args.engine
    result["query"] = args.query
    result["caveat"] = "Search results are discovery leads; source-audit material claims before using them."
    return result


def write_output(result: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
        print(path)
    else:
        print(rendered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Serper.dev Google search/news results.")
    sub = parser.add_subparsers(dest="command", required=True)
    search_parser = sub.add_parser("search", help="Run a Google Search or News query.")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--engine", default="search", choices=sorted(SERPER_ENDPOINTS))
    search_parser.add_argument("--num", type=int, default=10)
    search_parser.add_argument("--location")
    search_parser.add_argument("--hl", default="en")
    search_parser.add_argument("--gl", default="us")
    search_parser.add_argument("--time-period")
    search_parser.add_argument("--timeout", type=int, default=45)
    search_parser.add_argument("--full", action="store_true")
    search_parser.add_argument("--output")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.compact = not args.full
    try:
        if args.command == "search":
            write_output(search(args), args.output)
            return 0
        parser.error(f"Unsupported command: {args.command}")
        return 2
    except SerperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
