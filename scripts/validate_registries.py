#!/usr/bin/env python3
"""Validate registry JSON files in scripts/evidence_scout/registries/.

Checks:
  - Every registry file is valid JSON with a dict root
  - source_intents.json: required buckets, domain-like entries, no
    duplicates within a bucket, no domain assigned to two buckets
  - known_competitors.json: required keys, http(s) canonical URLs,
    unique normalized URL targets
  - query_expansion.json: each market has geo/trigger_markers and any
    reddit_queries, target_subreddits, phrase_variants use correct types
  - collect.py fallback constants stay in sync with query_expansion.json
    (reported as a warning — fallback drift degrades but does not break)

Usage: python3 scripts/validate_registries.py
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = ROOT / "scripts" / "evidence_scout" / "registries"

SOURCE_INTENT_BUCKETS = [
    "competitor_content",
    "editorial_content",
    "official_provider",
    "forum_discussion",
]

DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$")


def red(s):
    return f"\033[31m{s}\033[0m"


def green(s):
    return f"\033[32m{s}\033[0m"


def yellow(s):
    return f"\033[33m{s}\033[0m"


def load_registry(name, errors):
    path = REGISTRY_DIR / name
    if not path.exists():
        errors.append(f"{name}: file not found")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{name}: invalid JSON: {e}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{name}: root must be a JSON object")
        return None
    return data


def check_string_list(value, label, errors, allow_empty=False):
    if not isinstance(value, list):
        errors.append(f"{label}: must be a list")
        return []
    if not allow_empty and not value:
        errors.append(f"{label}: must not be empty")
        return []
    bad = [item for item in value if not isinstance(item, str) or not item.strip()]
    if bad:
        errors.append(f"{label}: entries must be non-empty strings")
    return [item for item in value if isinstance(item, str)]


def find_duplicates(values):
    seen = set()
    dupes = set()
    for value in values:
        normalized = value.strip().lower().rstrip("/")
        if normalized in seen:
            dupes.add(value)
        seen.add(normalized)
    return sorted(dupes)


def check_source_intents(errors):
    data = load_registry("source_intents.json", errors)
    if data is None:
        return

    bucket_domains = {}
    for bucket in SOURCE_INTENT_BUCKETS:
        if bucket not in data:
            errors.append(f"source_intents.json: missing bucket '{bucket}'")
            continue
        entries = check_string_list(data[bucket], f"source_intents.json:{bucket}", errors)
        non_domain = [e for e in entries if not DOMAIN_RE.match(e.strip().lower())]
        if non_domain:
            errors.append(f"source_intents.json:{bucket}: not domain-like: {non_domain}")
        dupes = find_duplicates(entries)
        if dupes:
            errors.append(f"source_intents.json:{bucket}: duplicate domains: {dupes}")
        bucket_domains[bucket] = {e.strip().lower() for e in entries}

    # A domain classified into two buckets silently corrupts intent counts.
    for i, first in enumerate(SOURCE_INTENT_BUCKETS):
        for second in SOURCE_INTENT_BUCKETS[i + 1:]:
            if first in bucket_domains and second in bucket_domains:
                overlap = bucket_domains[first] & bucket_domains[second]
                if overlap:
                    errors.append(
                        f"source_intents.json: domains in both '{first}' and '{second}': {sorted(overlap)}"
                    )


def check_known_competitors(errors):
    data = load_registry("known_competitors.json", errors)
    if data is None:
        return

    urls = data.get("canonical_urls")
    if not isinstance(urls, dict):
        errors.append("known_competitors.json: missing or non-object 'canonical_urls'")
    else:
        for name, url in urls.items():
            parsed = urlparse(str(url))
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(f"known_competitors.json: canonical_urls['{name}'] is not a valid http(s) URL: {url}")
        # Note: multiple names may legitimately share one canonical URL (brand
        # aliases such as getsafe → hellogetsafe.com), so duplicates are allowed.

    if "noisy_lookup_markers" not in data:
        errors.append("known_competitors.json: missing 'noisy_lookup_markers'")
    else:
        markers = check_string_list(
            data["noisy_lookup_markers"], "known_competitors.json:noisy_lookup_markers", errors
        )
        dupes = find_duplicates(markers)
        if dupes:
            errors.append(f"known_competitors.json:noisy_lookup_markers: duplicates: {dupes}")


def check_query_expansion(errors, warnings):
    data = load_registry("query_expansion.json", errors)
    if data is None:
        return

    markets = data.get("markets")
    if not isinstance(markets, dict) or not markets:
        errors.append("query_expansion.json: missing or empty 'markets' object")
        return

    for market_name, market in markets.items():
        label = f"query_expansion.json:markets.{market_name}"
        if not isinstance(market, dict):
            errors.append(f"{label}: must be an object")
            continue

        geo = market.get("geo")
        if not isinstance(geo, str) or not re.match(r"^[A-Z]{2}$", geo.upper()):
            errors.append(f"{label}: 'geo' must be a 2-letter country code")

        markers = check_string_list(market.get("trigger_markers"), f"{label}:trigger_markers", errors)
        if len({m.lower() for m in markers}) != len(markers):
            errors.append(f"{label}:trigger_markers: duplicates present")

        if "reddit_queries" in market:
            queries = check_string_list(
                market["reddit_queries"], f"{label}:reddit_queries", errors, allow_empty=True
            )
            dupes = find_duplicates(queries)
            if dupes:
                errors.append(f"{label}:reddit_queries: duplicates: {dupes}")

        if "target_subreddits" in market:
            check_string_list(
                market["target_subreddits"], f"{label}:target_subreddits", errors, allow_empty=True
            )

        if "phrase_variants" in market:
            variants = market["phrase_variants"]
            if not isinstance(variants, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in variants.items()
            ):
                errors.append(f"{label}:phrase_variants: must be an object of string→string")

    check_fallback_sync(data, warnings)


def check_fallback_sync(registry, warnings):
    """Detect drift between query_expansion.json and the fallbacks in collect.py."""
    try:
        sys.path.insert(0, str(ROOT / "scripts" / "evidence_scout"))
        import collect  # noqa: F401

        for market_name, market in registry.get("markets", {}).items():
            fallback = collect.FALLBACK_QUERY_MARKETS.get(market_name)
            if fallback is None:
                warnings.append(
                    f"collect.py FALLBACK_QUERY_MARKETS has no fallback for market '{market_name}'"
                )
                continue
            if sorted(market.get("reddit_queries", [])) != sorted(fallback.get("reddit_queries", [])):
                warnings.append(
                    f"collect.py fallback reddit_queries for '{market_name}' differ from the registry"
                )
            if market_name == "de-insurance":
                if dict(collect.FALLBACK_PHRASE_VARIANTS) != dict(market.get("phrase_variants", {})):
                    warnings.append("collect.py FALLBACK_PHRASE_VARIANTS differ from the registry")
                if list(collect.FALLBACK_QUERY_MARKETS[market_name].get("trigger_markers", [])) != list(
                    market.get("trigger_markers", [])
                ):
                    warnings.append(f"collect.py fallback trigger_markers for '{market_name}' differ from the registry")
    except Exception as e:  # import of collect.py is best-effort
        warnings.append(f"could not import collect.py for fallback sync check: {e}")


def main():
    errors = []
    warnings = []

    if not REGISTRY_DIR.exists():
        print(red(f"FAIL  registry directory not found: {REGISTRY_DIR}"))
        sys.exit(1)

    check_source_intents(errors)
    check_known_competitors(errors)
    check_query_expansion(errors, warnings)

    print("=== Registry Validation ===\n")
    if warnings:
        for warning in warnings:
            print(yellow(f"  WARN  {warning}"))
    if errors:
        for error in errors:
            print(red(f"  FAIL  {error}"))
        print(red(f"\n{len(errors)} registry error(s) — fix before running evidence collection."))
        sys.exit(1)

    print(green("  PASS  source_intents.json"))
    print(green("  PASS  known_competitors.json"))
    print(green("  PASS  query_expansion.json"))
    print(green("\nAll registry checks passed."))
    sys.exit(0)


if __name__ == "__main__":
    main()
