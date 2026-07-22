#!/usr/bin/env python3
"""Collect competitor paid-ads intelligence from the Meta Ad Library.

Primary provider: official Meta Ad Library API (ads_archive). Free, but covers
commercial ads only for EU/UK/EEA audiences (DSA transparency); outside those
countries only political/social-issue ads are returned.

Fallback provider: Apify Facebook Ad Library actor (paid, global coverage).
Requires explicit --approve-paid because it spends credits.

This is intentionally API-first and dependency-light so the same script can be
called from Codex, OpenCode, Claude Code, CI, or a plain terminal.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "scripts" / "validate_apis"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import get_secret, http_get, http_post, now_iso, redact_sensitive, status_from_response  # noqa: E402
from workspace import resolve_run_dir, update_stage  # noqa: E402

GRAPH_VERSION = "v20.0"
ADS_ARCHIVE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}/ads_archive"
ADS_ARCHIVE_FIELDS = ",".join(
    [
        "id",
        "page_id",
        "page_name",
        "ad_creative_bodies",
        "ad_creative_link_captions",
        "ad_creative_link_titles",
        "ad_creative_link_descriptions",
        "ad_delivery_start_time",
        "ad_delivery_stop_time",
        "ad_snapshot_url",
        "publisher_platforms",
        "spend",
        "impressions",
        "currency",
    ]
)

# EU member states + UK + EEA: where the Ad Library exposes commercial ads.
DSA_COVERAGE_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE", "GB", "UK", "IS", "LI", "NO",
}

COVERAGE_CAVEAT = (
    "Meta Ad Library covers commercial ads only for EU/UK/EEA audiences (DSA transparency, ~1-year retention). "
    "Outside those countries only political/social-issue ads are returned. Spend/impressions are coarse ranges; "
    "no engagement metrics. Ad longevity signals what keeps running, not proven performance."
)

DEFAULT_APIFY_ACTOR = "apify/facebook-ads-scraper"


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in safe.split("-") if part)[:80] or "ads"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def parse_countries(value: str) -> list[str]:
    return [part.strip().upper() for part in value.split(",") if part.strip()]


def load_competitor_names(args: argparse.Namespace) -> list[str]:
    names = list(args.competitor_name)
    if args.competitors_json:
        data = json.loads(Path(args.competitors_json).read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("business_name") or ""
            if not name:
                domain = item.get("domain") or ""
                name = domain.split(".")[0] if domain else ""
            if name:
                names.append(name)
    deduped: list[str] = []
    for name in names:
        clean = " ".join(str(name).split())
        if clean and clean.lower() not in {n.lower() for n in deduped}:
            deduped.append(clean)
    return deduped[: args.limit]


def graph_get(path: str, params: dict[str, Any], token: str, raw_calls: list[dict[str, Any]], label: str) -> dict[str, Any]:
    """GET a Graph API endpoint with bounded retries and ~200 calls/hour pacing."""
    full_params = {**params, "access_token": token}
    attempts = 0
    while True:
        attempts += 1
        response = http_get(f"{path}?{urllib.parse.urlencode(full_params)}")
        raw_calls.append({"label": label, "path": path, "params": {k: v for k, v in params.items()}, "response": response})
        body = response.get("body") or {}
        error = body.get("error") if isinstance(body, dict) else None
        if response.get("ok") and not error:
            time.sleep(1.0)  # stay well under the ~200 calls/hour budget
            return response
        code = (error or {}).get("code")
        if code in {4, 17, 32, 613} and attempts <= 3:  # rate-limit family
            time.sleep(20 * attempts)
            continue
        return response


def normalize_meta_ad(ad: dict[str, Any], *, matched: str, match_type: str, countries: list[str]) -> dict[str, Any]:
    def first(value: Any) -> str:
        if isinstance(value, list) and value:
            return str(value[0])
        return str(value) if value else ""

    spend = ad.get("spend") or {}
    impressions = ad.get("impressions") or {}
    start = ad.get("ad_delivery_start_time") or ""
    stop = ad.get("ad_delivery_stop_time") or ""
    longevity_days: int | None = None
    if start:
        try:
            start_date = start[:10]
            end_date = (stop[:10] if stop else now_iso()[:10])
            longevity_days = (
                time.mktime(time.strptime(end_date, "%Y-%m-%d")) - time.mktime(time.strptime(start_date, "%Y-%m-%d"))
            ) // 86400
            longevity_days = int(longevity_days)
        except (ValueError, OverflowError):
            longevity_days = None
    return {
        "ad_id": str(ad.get("id") or ""),
        "page_id": str(ad.get("page_id") or ""),
        "page_name": ad.get("page_name") or "",
        "matched": matched,
        "match_type": match_type,
        "source": "meta_ad_library",
        "retrieved_at": now_iso(),
        "countries": countries,
        "platforms": ad.get("publisher_platforms") or [],
        "creative_body": first(ad.get("ad_creative_bodies")),
        "link_caption": first(ad.get("ad_creative_link_captions")),
        "link_title": first(ad.get("ad_creative_link_titles")),
        "link_description": first(ad.get("ad_creative_link_descriptions")),
        "delivery_start": start,
        "delivery_stop": stop,
        "active": not bool(stop),
        "spend_lower": spend.get("lower_bound"),
        "spend_upper": spend.get("upper_bound"),
        "impressions_lower": impressions.get("lower_bound"),
        "impressions_upper": impressions.get("upper_bound"),
        "currency": ad.get("currency") or "",
        "snapshot_url": ad.get("ad_snapshot_url") or "",
        "longevity_days": longevity_days,
        "confidence_notes": COVERAGE_CAVEAT,
    }


def collect_meta_ad_library(
    searches: list[tuple[str, str]],
    countries: list[str],
    limit: int,
    raw_calls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, token = get_secret("META_ACCESS_TOKEN", "FACEBOOK_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")
    if not token:
        return [], {
            "status": "missing_credentials",
            "required_env": ["META_ACCESS_TOKEN"],
            "setup": [
                "Create/select a Meta app at https://developers.facebook.com/apps/",
                "Complete Meta identity verification (required for Ad Library API access)",
                "Generate a token with ads_read scope via Graph API Explorer",
                "Set META_ACCESS_TOKEN in the environment or ~/.secrets",
                "Note: tokens expire after ~60 days; regenerate before runs",
            ],
        }
    records: list[dict[str, Any]] = []
    status = "ok"
    for matched, match_type in searches:
        params = {
            "ad_reached_countries": json.dumps(countries),
            "ad_active_status": "ALL",
            "ad_type": "ALL",
            "search_terms": matched,
            "fields": ADS_ARCHIVE_FIELDS,
            "limit": min(limit, 100),
        }
        response = graph_get(ADS_ARCHIVE_URL, params, token, raw_calls, f"search:{matched}")
        body = response.get("body") or {}
        error = body.get("error") if isinstance(body, dict) else None
        if error:
            code = error.get("code")
            message = error.get("message") or ""
            if code == 190 or "expired" in message.lower():
                status = "token_expired"
            elif code in {10, 200, 294} or "ads_read" in message.lower() or "permission" in message.lower():
                status = "scope_denied"
            else:
                status = f"error:{code}"
            continue
        for ad in body.get("data") or []:
            if isinstance(ad, dict):
                records.append(normalize_meta_ad(ad, matched=matched, match_type=match_type, countries=countries))
        if not (body.get("data") or []):
            # Zero results is a coverage limitation signal, not proof of no ads.
            status = "ok" if records else "empty"
    return records[: limit * max(1, len(searches))], {"status": status, "record_count": len(records), "credential_source": key_name}


def ad_library_url(query: str, country: str) -> str:
    return (
        "https://www.facebook.com/ads/library/"
        f"?active_status=all&ad_type=all&country={country}&q={urllib.parse.quote(query)}"
    )


def collect_apify_ads(
    searches: list[tuple[str, str]],
    countries: list[str],
    limit: int,
    approve_paid: bool,
    actor: str,
    raw_calls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not approve_paid:
        return [], {"status": "approval_required", "note": "Apify spends credits. Rerun with --approve-paid after user confirmation."}
    key_name, token = get_secret("APIFY_TOKEN")
    if not token:
        return [], {"status": "missing_credentials", "required_env": ["APIFY_TOKEN"]}
    start_urls = [{"url": ad_library_url(query, countries[0])} for query, _ in searches]
    payload = {"startUrls": start_urls, "resultsLimit": limit * max(1, len(searches))}
    response = http_post(
        f"https://api.apify.com/v2/acts/{actor.replace('/', '~')}/run-sync-get-dataset-items",
        headers={"Authorization": f"Bearer {token}"},
        data=payload,
    )
    raw_calls.append({"label": "apify_run", "actor": actor, "params": {"startUrls": start_urls, "resultsLimit": payload["resultsLimit"]}, "response": response})
    if not response.get("ok"):
        return [], {"status": status_from_response(response), "credential_source": key_name}
    body = response.get("body")
    items = body if isinstance(body, list) else []
    records: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        snapshot = item.get("snapshot") or {}
        body_items = snapshot.get("body") or {}
        text = body_items.get("text") if isinstance(body_items, dict) else ""
        records.append(
            {
                "ad_id": str(item.get("adArchiveID") or item.get("ad_archive_id") or item.get("id") or ""),
                "page_id": str(item.get("pageID") or item.get("page_id") or ""),
                "page_name": item.get("pageName") or item.get("page_name") or "",
                "matched": searches[0][0] if searches else "",
                "match_type": "keyword" if searches else "",
                "source": "apify_ads",
                "retrieved_at": now_iso(),
                "countries": countries,
                "platforms": item.get("publisherPlatform") or item.get("publisher_platforms") or [],
                "creative_body": text or "",
                "link_caption": (snapshot.get("caption") or "") if isinstance(snapshot, dict) else "",
                "link_title": (snapshot.get("title") or "") if isinstance(snapshot, dict) else "",
                "link_description": "",
                "delivery_start": str(item.get("startDateFormatted") or item.get("start_date") or ""),
                "delivery_stop": str(item.get("endDateFormatted") or item.get("end_date") or ""),
                "active": bool(item.get("isActive", True)),
                "spend_lower": None,
                "spend_upper": None,
                "impressions_lower": None,
                "impressions_upper": None,
                "currency": "",
                "snapshot_url": item.get("adSnapshotUrl") or item.get("snapshot_url") or "",
                "longevity_days": None,
                "confidence_notes": "Collected via Apify Ad Library actor (paid). Field shapes vary by actor version; verify before broad runs.",
            }
        )
    return records, {"status": "ok" if records else "empty", "record_count": len(records), "credential_source": key_name}


def build_report(records: list[dict[str, Any]], searches: list[tuple[str, str]], countries: list[str], provider_notes: dict[str, Any]) -> str:
    lines = [
        "# Competitor Ads Intelligence",
        "",
        f"Retrieved: {now_iso()}",
        f"Countries: {', '.join(countries)}",
        f"Searches: {', '.join(q for q, _ in searches)}",
        "",
        f"> **Coverage caveat:** {COVERAGE_CAVEAT}",
        "",
        "## Provider status",
        "",
    ]
    for name, note in provider_notes.items():
        lines.append(f"- **{name}**: {note.get('status')} ({note.get('record_count', 0)} records)")
    if provider_notes.get("apify_ads", {}).get("status") not in {None, "not_run"}:
        lines.append(f"- Fallback used: {provider_notes.get('fallback_reason', 'n/a')}")
    lines += ["", "## Ads by matched competitor/keyword", ""]
    by_matched: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_matched.setdefault(record["matched"], []).append(record)
    for matched, ads in by_matched.items():
        lines.append(f"### {matched} — {len(ads)} ads")
        lines.append("")
        active = [ad for ad in ads if ad["active"]]
        longest = sorted(ads, key=lambda ad: (ad.get("longevity_days") or 0), reverse=True)[:3]
        platforms: dict[str, int] = {}
        for ad in ads:
            for platform in ad.get("platforms") or []:
                platforms[platform] = platforms.get(platform, 0) + 1
        lines.append(f"- Active now: {len(active)} / {len(ads)}")
        lines.append(f"- Platforms: {', '.join(f'{p} ({n})' for p, n in sorted(platforms.items(), key=lambda kv: -kv[1])) or 'unknown'}")
        if longest and longest[0].get("longevity_days"):
            lines.append("- Longest-running (judgment signal, not performance proof):")
            for ad in longest:
                lines.append(f"  - {ad['longevity_days']}d — {ad['link_title'] or ad['creative_body'][:80]}")
        lines.append("")
        for ad in ads[:10]:
            lines.append(f"**{ad['page_name']}** ({ad['delivery_start'][:10]} → {ad['delivery_stop'][:10] or 'running'})")
            if ad["creative_body"]:
                lines.append(f"> {ad['creative_body'][:300]}")
            meta_bits = []
            if ad["link_title"]:
                meta_bits.append(f"title: {ad['link_title']}")
            if ad["spend_lower"] is not None:
                meta_bits.append(f"spend: {ad['spend_lower']}–{ad['spend_upper']} {ad['currency']}")
            if ad["impressions_lower"] is not None:
                meta_bits.append(f"impressions: {ad['impressions_lower']}–{ad['impressions_upper']}")
            if meta_bits:
                lines.append(f"_{'; '.join(meta_bits)}_")
            if ad["snapshot_url"]:
                lines.append(f"[snapshot]({ad['snapshot_url']})")
            lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect competitor paid-ads intelligence from the Meta Ad Library (primary) and Apify (paid fallback).")
    parser.add_argument("--topic", default="")
    parser.add_argument("--competitor-name", action="append", default=[], help="Competitor name to search in the Ad Library. Repeatable.")
    parser.add_argument("--competitors-json", default="", help="Path to competitors.json from discover_competitors.py.")
    parser.add_argument("--keywords", default="", help="Comma-separated keyword searches to discover WHO advertises, not just known competitors.")
    parser.add_argument("--countries", default="DE", help="Comma-separated ISO country codes for ad_reached_countries. EU/UK/EEA only for Meta commercial ads.")
    parser.add_argument("--limit", type=int, default=20, help="Max ads per competitor search (competitor mode) or total (keyword mode). Hard cap 200.")
    parser.add_argument(
        "--providers",
        default="meta_ad_library",
        help="Comma-separated: meta_ad_library (default, free), apify_ads (paid fallback), or auto (meta primary, apify when non-EU countries or token missing).",
    )
    parser.add_argument("--approve-paid", action="store_true", help="Confirm paid-credit spend for apify_ads. Required or apify_ads returns approval_required.")
    parser.add_argument("--apify-actor", default=DEFAULT_APIFY_ACTOR, help=f"Apify actor for the fallback (default {DEFAULT_APIFY_ACTOR}).")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--workspace", default="", help="Topic workspace path. Defaults to research/topics/<topic-slug>.")
    parser.add_argument("--legacy-output", action="store_true", help="Write to the former research/evidence-scout/ads layout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.limit = min(max(1, args.limit), 200)
    countries = parse_countries(args.countries) or ["DE"]
    competitor_names = load_competitor_names(args)
    keywords = [" ".join(k.split()) for k in args.keywords.split(",") if k.strip()]
    searches: list[tuple[str, str]] = [(name, "competitor") for name in competitor_names] + [(kw, "keyword") for kw in keywords]
    if not searches:
        print(json.dumps({"status": "error", "message": "Provide --competitor-name, --competitors-json, or --keywords."}, indent=2))
        return 1

    effective_topic = args.topic or "competitor-ads"
    run_dir, workspace = resolve_run_dir(
        topic=effective_topic,
        workspace_arg=args.workspace,
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="ads/runs",
        legacy_subdir="ads",
    )
    if workspace:
        update_stage(workspace, "competitor_marketing", status="in_progress", gate_result="not_run", next_action="Interpret ad evidence alongside landing-page marketing analysis.")

    requested = [part.strip() for part in args.providers.split(",") if part.strip()]
    non_covered = [c for c in countries if c not in DSA_COVERAGE_COUNTRIES]
    use_meta = "meta_ad_library" in requested or "auto" in requested or "all" in requested
    want_apify = "apify_ads" in requested or "auto" in requested or "all" in requested

    raw_calls: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    provider_notes: dict[str, Any] = {}
    fallback_reason = ""

    if use_meta:
        meta_records, meta_status = collect_meta_ad_library(searches, countries, args.limit, raw_calls)
        records.extend(meta_records)
        provider_notes["meta_ad_library"] = meta_status
        if want_apify and (meta_status.get("status") in {"missing_credentials", "token_expired", "scope_denied"}):
            fallback_reason = f"meta_ad_library {meta_status.get('status')}"
        elif want_apify and "auto" in requested and non_covered:
            fallback_reason = f"countries outside EU/UK/EEA commercial coverage: {', '.join(non_covered)}"
    elif want_apify and non_covered:
        fallback_reason = f"countries outside EU/UK/EEA commercial coverage: {', '.join(non_covered)}"

    if want_apify and (fallback_reason or "apify_ads" in requested):
        if not fallback_reason:
            fallback_reason = "explicitly requested"
        apify_records, apify_status = collect_apify_ads(searches, countries, args.limit, args.approve_paid, args.apify_actor, raw_calls)
        records.extend(apify_records)
        apify_status["fallback_reason"] = fallback_reason
        provider_notes["apify_ads"] = apify_status

    # Dedup by ad_id
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        identity = record.get("ad_id") or f"{record.get('page_name')}:{record.get('creative_body', '')[:60]}"
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(record)

    write_json(run_dir / "raw" / "providers.json", redact_sensitive({"calls": raw_calls}))
    with (run_dir / "ads.jsonl").open("w", encoding="utf-8") as handle:
        for record in deduped:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    report = build_report(deduped, searches, countries, provider_notes)
    (run_dir / "report.md").write_text(report, encoding="utf-8")

    summary = {
        "run_dir": str(run_dir),
        "topic": effective_topic,
        "searches": [{"query": q, "type": t} for q, t in searches],
        "countries": countries,
        "coverage_caveat": COVERAGE_CAVEAT,
        "countries_outside_dsa_coverage": non_covered,
        "providers": provider_notes,
        "record_count": len(deduped),
        "outputs": {
            "ads_jsonl": str(run_dir / "ads.jsonl"),
            "report_md": str(run_dir / "report.md"),
            "raw": str(run_dir / "raw" / "providers.json"),
        },
    }
    write_json(run_dir / "summary.json", summary)

    if workspace:
        ok = any(note.get("status") == "ok" for note in provider_notes.values())
        update_stage(
            workspace,
            "competitor_marketing",
            status="completed" if ok else "blocked",
            gate_result="pass" if ok else "not_run",
            artifacts=[run_dir / "ads.jsonl", run_dir / "report.md", run_dir / "summary.json"],
            provider_failures=[{"provider": name, "status": str(note.get("status"))} for name, note in provider_notes.items() if note.get("status") != "ok"],
            next_action="Compare ad messaging with landing-page positioning from analyze_competitor_marketing.py.",
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
