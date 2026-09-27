#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "validate_serpapi_google_trends.py",
    "validate_dataforseo_google_trends.py",
    "validate_reddit.py",
    "validate_youtube.py",
    "validate_firecrawl.py",
    "validate_serper.py",
    "validate_brave_search.py",
    "validate_hn.py",
    "validate_github.py",
    "validate_google_autocomplete.py",
    "validate_itunes_reviews.py",
    "validate_x.py",
    "validate_xai.py",
    "validate_tiktok.py",
    "validate_meta.py",
    "validate_scrapecreators.py",
    "validate_app_reviews.py",
    "validate_sonar.py",
    "validate_apify.py",
    "validate_brightdata.py",
    "validate_crawl4ai.py",
    "validate_markitdown.py",
    "validate_scrapling.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate selected source providers")
    parser.add_argument("--provider", action="append", choices=[name.removeprefix("validate_").removesuffix(".py") for name in SCRIPTS])
    parser.add_argument("--query", default="")
    parser.add_argument("--country", default="")
    parser.add_argument("--language", default="")
    parser.add_argument("--app-id", default="")
    args = parser.parse_args()
    results = []
    for script in SCRIPTS:
        name = script.removeprefix("validate_").removesuffix(".py")
        if args.provider and name not in args.provider:
            continue
        path = Path(__file__).resolve().parent / script
        supported = {"query": {"dataforseo_google_trends", "google_autocomplete", "github", "firecrawl",
                                "brave_search", "x", "reddit", "serpapi_google_trends", "hn", "youtube"},
                     "country": {"google_autocomplete", "itunes_reviews"},
                     "language": {"google_autocomplete"}, "app-id": {"itunes_reviews"}}
        forwarded = []
        for flag in ("query", "country", "language", "app-id"):
            value = getattr(args, flag.replace("-", "_"))
            if value and name in supported[flag]:
                forwarded.extend(("--" + flag, value))
        proc = subprocess.run([sys.executable, str(path), *forwarded], cwd=ROOT, text=True, capture_output=True)
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {"provider": script.removeprefix("validate_").removesuffix(".py"), "status": "failed", "stdout": proc.stdout, "stderr": proc.stderr}
        parsed["exit_code"] = proc.returncode
        if proc.stderr:
            parsed["stderr"] = proc.stderr[-2000:]
        results.append(parsed)

    out = ROOT / "projects" / "_infra" / "api-validation" / ("selected.summary.json" if args.provider else "all.summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    ok_count = sum(1 for result in results if result.get("status") == "ok")
    return 0 if ok_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
