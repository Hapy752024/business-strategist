#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "validate_serpapi_google_trends.py",
    "validate_dataforseo_google_trends.py",
    "validate_dataforseo.py",
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
    "validate_apify_reddit.py",
    "validate_scrapecreators_reddit.py",
    "validate_arctic_shift.py",
    "validate_apify_review_lanes.py",
    "validate_cfpb_complaints.py",
    "validate_stackexchange.py",
    "validate_producthunt.py",
    "validate_brightdata.py",
    "validate_parsersvc.py",
    "validate_eurostat.py",
    "validate_swiss_stats.py",
    "validate_opendata_swiss.py",
    "validate_census.py",
    "validate_bls.py",
    "validate_openalex.py",
    "validate_crossref.py",
    "validate_ecb.py",
    "validate_fred.py",
    "validate_bis.py",
    "validate_world_bank.py",
    "validate_companies_house.py",
    "validate_france_register.py",
    "validate_switzerland_register.py",
    "validate_sec_register.py",

    "validate_crawl4ai.py",
    "validate_markitdown.py",
    "validate_scrapling.py",
]

# Providers served by a shared validator module: provider -> (module, --provider value).
SHIMS = {
    "ecb": ("validate_institutional_sources", "ecb"),
    "fred": ("validate_institutional_sources", "fred"),
    "bis": ("validate_institutional_sources", "bis"),
    "world_bank": ("validate_institutional_sources", "world_bank"),
    "companies_house": ("validate_institutional_sources", "companies_house"),
    "france_register": ("validate_registry_sources", "france"),
    "switzerland_register": ("validate_registry_sources", "switzerland"),
    "sec_register": ("validate_registry_sources", "sec"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate selected source providers")
    parser.add_argument("--provider", action="append", choices=[name.removeprefix("validate_").removesuffix(".py") for name in SCRIPTS])
    parser.add_argument("--query", default="")
    parser.add_argument("--country", default="")
    parser.add_argument("--language", default="")
    parser.add_argument("--app-id", default="")
    parser.add_argument("--out", type=Path, help="Isolated validation output directory")
    args = parser.parse_args()
    if args.out:
        os.environ["EVIDENCE_SCOUT_VALIDATION_DIR"] = str(args.out.absolute())
    results = []
    for script in SCRIPTS:
        name = script.removeprefix("validate_").removesuffix(".py")
        if args.provider and name not in args.provider:
            continue
        if name in SHIMS:
            module, provider_arg = SHIMS[name]
            command = [sys.executable, str(Path(__file__).resolve().parent / f"{module}.py"), "--provider", provider_arg]
        else:
            command = [sys.executable, str(Path(__file__).resolve().parent / script)]
        supported = {"query": {"dataforseo_google_trends", "google_autocomplete", "github", "firecrawl",
                                "brave_search", "x", "reddit", "serpapi_google_trends", "hn", "youtube"},
                     "country": {"google_autocomplete", "itunes_reviews"},
                     "language": {"google_autocomplete"}, "app-id": {"itunes_reviews"}}
        forwarded = []
        for flag in ("query", "country", "language", "app-id"):
            value = getattr(args, flag.replace("-", "_"))
            if value and name in supported[flag]:
                forwarded.extend(("--" + flag, value))
        proc = subprocess.run([*command, *forwarded], cwd=ROOT, text=True, capture_output=True)
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {"provider": script.removeprefix("validate_").removesuffix(".py"), "status": "failed", "stdout": proc.stdout, "stderr": proc.stderr}
        parsed["exit_code"] = proc.returncode
        if proc.stderr:
            parsed["stderr"] = proc.stderr[-2000:]
        results.append(parsed)

    out = Path(os.environ.get("EVIDENCE_SCOUT_VALIDATION_DIR", ROOT / "projects" / "_infra" / "api-validation")) / ("selected.summary.json" if args.provider else "all.summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    ok_count = sum(1 for result in results if result.get("status") == "ok")
    return 0 if ok_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
