#!/usr/bin/env python3
"""Customer search-journey SERP study: brainstormed journey queries -> Google SERP -> sponsored vs organic.

Desk research that runs before the pain gate. Outputs (in --run-dir):
  raw/<query_id>__<provider>__<n>.json   provider payloads (point-in-time, unpersonalised samples)
  captures.json                          normalised captures (ads separated from organic)
  serp-landscape.json / serp-landscape.md per-stage landscape report
  content-opportunities.json             one input to content/SEO planning (volumes stay null)

Ads are a supplier-spend signal for an intent, not customer demand. "unobserved" (the provider cannot
see ads) is never reported as zero. Brainstormed queries are hypotheses about what customers type.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
for _extra in (ROOT / "scripts", ROOT / "scripts" / "validate_apis"):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))

from jsonschema import Draft202012Validator  # noqa: E402

PLAN_SCHEMA = ROOT / "schemas" / "search-journey-plan.schema.json"
OPPORTUNITY_SCHEMA = ROOT / "schemas" / "content-opportunities.schema.json"
DOMAIN_TYPES = ROOT / "config" / "serp-domain-types.json"
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
NO_RESULTS_TEXT = "hasn't returned any results"
STAGES = ["problem_aware", "solution_aware", "comparison", "purchase", "local", "post_purchase"]
RESULT_TYPES = ["competitor", "publisher", "forum_community", "marketplace_aggregator", "directory_review",
                "government_institution", "video", "unknown"]
REUSE_DAYS = 30
CAVEATS = [
    "Point-in-time, unpersonalised SERP samples; ads vary by time, location and device.",
    "Ads are a supplier-spend signal for an intent, not customer demand. No ads observed is not evidence of no demand.",
    "ads_status 'unobserved' means the provider cannot see ads; it is never zero.",
    "Brainstormed queries (seed_origin: brainstorm) are hypotheses about what customers type, not observed searches.",
    "result_type comes from a curated domain map plus heuristics; it is a hint, not a verified fact.",
    "Content gaps are hypotheses from SERP shape; read the ranking pages first. A gap does not prove demand.",
    "Desk research before the pain gate; it does not authorize ads or content publication.",
]


# ---------------------------------------------------------------------------------------------- plan

def _validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def validate_plan(plan: dict) -> list[str]:
    errors = []
    for err in _validator(PLAN_SCHEMA).iter_errors(plan):
        where = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{where}: {err.message}")
    seen: set[str] = set()
    for row in plan.get("rows") or []:
        qid = row.get("query_id") if isinstance(row, dict) else None
        if qid and qid in seen:
            errors.append(f"duplicate query_id: {qid}")
        if qid:
            seen.add(qid)
    return errors


def validate_content_opportunities(doc: dict) -> list[str]:
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in _validator(OPPORTUNITY_SCHEMA).iter_errors(doc)]


# -------------------------------------------------------------------------------------- classification

_DOMAIN_TYPES: dict | None = None


def domain_types() -> dict:
    global _DOMAIN_TYPES
    if _DOMAIN_TYPES is None:
        _DOMAIN_TYPES = json.loads(DOMAIN_TYPES.read_text(encoding="utf-8"))
    return _DOMAIN_TYPES


def normalize_host(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    if "://" not in value:
        value = "http://" + value
    host = urllib.parse.urlparse(value).hostname or ""
    return host[4:] if host.startswith("www.") else host


def _host_matches(host: str, entry: str) -> bool:
    if entry.endswith(".*"):
        labels = host.split(".")
        return any(fnmatch.fnmatch(".".join(labels[i:]), entry) and len(labels) - i <= 3 for i in range(len(labels)))
    return host == entry or host.endswith("." + entry)


def _competitor_match(host: str, known: Iterable[str]) -> bool:
    return any(c and (host == c or host.endswith("." + c)) for c in known)


def classify_url(url: str | None, known_competitors: Iterable[str] = (), domain: str | None = None) -> tuple[str, str]:
    """Return (result_type, basis); basis is competitor|curated|heuristic|none."""
    host = normalize_host(domain or url)
    if not host:
        return "unknown", "none"
    known = {normalize_host(c) for c in known_competitors}
    if _competitor_match(host, known):
        return "competitor", "competitor"
    cfg = domain_types()
    path = urllib.parse.urlparse(url).path.lower() if url and "://" in url else ""
    for rtype, entries in cfg["types"].items():
        for entry in entries:
            if "/" in entry:
                ehost, epath = entry.split("/", 1)
                if _host_matches(host, ehost) and path.lstrip("/").startswith(epath):
                    return rtype, "curated"
    for rtype, entries in cfg["types"].items():
        if any("/" not in e and _host_matches(host, e) for e in entries):
            return rtype, "curated"
    for rtype, suffixes in cfg.get("suffixes", {}).items():
        if any(host.endswith(s) for s in suffixes):
            return rtype, "curated"
    hints = cfg.get("publisher_hints", {})
    segments = [s for s in path.split("/") if s]
    if any(tok in host for tok in hints.get("host_tokens", [])) or any(
            seg.split(".")[0] in hints.get("path_tokens", []) for seg in segments):
        return "publisher", "heuristic"
    return "unknown", "none"


def classify_domain(domain: str, known_competitors: set[str]) -> str:
    return classify_url(None, known_competitors, domain=domain)[0]


# ------------------------------------------------------------------------------------------- parsing

PLATFORM_SOURCES = {"youtube": "youtube.com", "reddit": "reddit.com", "facebook": "facebook.com",
                    "instagram": "instagram.com", "tiktok": "tiktok.com", "linkedin": "linkedin.com", "x": "x.com"}


def _domain_from(link: str | None, displayed: str | None, source: str | None = None) -> str:
    """Advertiser/organic domain: real link host, else displayed_link host, else a platform named in source.

    Google often returns opaque /goto redirects, and video rows display view counts instead of a host.
    """
    host = normalize_host(link) if link and link.startswith("http") else ""
    if host and not host.startswith("google.") and ".google." not in host:
        return host
    shown = (displayed or "").split("›")[0].strip()
    if shown and " " not in shown and "." in shown:
        return normalize_host(shown)
    platform = (source or "").split("·")[0].strip().lower()
    return PLATFORM_SOURCES.get(platform, "")


def _real_url(link: str | None) -> str | None:
    if link and link.startswith("http") and "google." not in (urllib.parse.urlparse(link).hostname or ""):
        return link
    return None


def _organic(rows: list[dict], known: Iterable[str], link_key: str, displayed_key: str) -> list[dict]:
    out = []
    for i, row in enumerate(rows or [], 1):
        domain = _domain_from(row.get(link_key), row.get(displayed_key), row.get("source"))
        url = _real_url(row.get(link_key))
        rtype, basis = classify_url(url, known, domain=domain)
        out.append({"rank": row.get("position") or i, "domain": domain, "title": row.get("title"), "url": url,
                    "display_url": row.get(displayed_key), "result_type": rtype, "classification_basis": basis})
    return out


def parse_serpapi(payload: dict, known_competitors: Iterable[str] = ()) -> dict:
    """Normalise a SerpApi engine=google payload. SerpApi sees ads, so absence is observed_none.

    A top-level ``error`` (quota, auth, bad request) or a non-Success status is a coverage gap: every
    observable is unobserved/None and the error is returned. SerpApi's "Google hasn't returned any results"
    (status Success) is the explicit ``no_results`` state, not ``observed_none``.
    """
    meta = payload.get("search_metadata") or {}
    status, error = meta.get("status"), payload.get("error")
    no_results = bool(error) and status == "Success" and NO_RESULTS_TEXT in str(error).lower()
    failed = (bool(error) and not no_results) or (bool(status) and status != "Success")
    ads = []
    for i, ad in enumerate(payload.get("ads") or [], 1):
        block = ad.get("block_position")
        ads.append({"position": block if block in ("top", "bottom") else "other", "rank": ad.get("position") or i,
                    "advertiser_domain": _domain_from(ad.get("link"), ad.get("displayed_link"), ad.get("source")),
                    "advertiser_name": ad.get("source"), "headline": ad.get("title"),
                    "description": ad.get("description"), "display_url": ad.get("displayed_link")})
    ads_status = "unobserved" if failed else "no_results" if no_results else ("observed" if ads else "observed_none")
    organic = _organic(payload.get("organic_results") or [], known_competitors, "link", "displayed_link")
    ao = payload.get("ai_overview")
    if failed:
        ai = {"present": None, "cited_domains": None}
    elif not ao:
        ai = {"present": False, "cited_domains": []}
    elif ao.get("references"):
        ai = {"present": True, "cited_domains": sorted({normalize_host(r.get("link")) for r in ao["references"] if r.get("link")})}
    else:  # page_token only: citations need a follow-up paid request, which this study does not make
        ai = {"present": True, "cited_domains": None}
    ai_headings = [b.get("snippet") for b in (ao or {}).get("text_blocks") or [] if b.get("type") == "heading" and b.get("snippet")]
    local = payload.get("local_results")
    places = local.get("places", []) if isinstance(local, dict) else (local or [])
    local_pack = [{"rank": p.get("position") or i, "title": p.get("title"), "domain": normalize_host(p.get("website")),
                   "rating": p.get("rating"), "reviews": p.get("reviews"), "type": p.get("type")}
                  for i, p in enumerate(places, 1)]
    shopping_rows = (payload.get("shopping_results") or []) + (payload.get("inline_shopping") or [])
    shopping = [{"rank": s.get("position") or i, "title": s.get("title"), "seller": s.get("source"),
                 "price": s.get("price"), "domain": normalize_host(s.get("link"))} for i, s in enumerate(shopping_rows, 1)]
    top10 = [o for o in organic if (o["rank"] or 99) <= 10]

    def seen(*keys: str) -> bool | None:
        return None if failed else any(payload.get(k) for k in keys)

    features = {
        "ads": None if failed else bool(ads),
        "ai_overview": ai["present"],
        "paa": None if failed else bool(payload.get("related_questions")),
        "video": seen("inline_videos", "video_results", "short_videos"),
        "forum": None if failed else bool(payload.get("discussions_and_forums")) or any(o["result_type"] == "forum_community" for o in top10),
        "local_pack": None if failed else bool(local_pack),
        "shopping": None if failed else bool(shopping),
        "perspectives": seen("perspectives"),
    }
    out = {"ads_status": ads_status, "ads": ads, "organic": organic, "shopping": shopping, "local_pack": local_pack,
           "ai_overview": ai, "ai_overview_headings": ai_headings,
           "paa": [q.get("question") for q in payload.get("related_questions") or [] if q.get("question")],
           "related": [r.get("query") for r in payload.get("related_searches") or [] if r.get("query")],
           "features": features, "serp_state": "failed" if failed else "no_results" if no_results else "ok"}
    if failed:
        out["error"] = f"PROVIDER_ERROR: {error or f'search_metadata.status={status}'}"
    return out


def parse_serper(payload: dict, known_competitors: Iterable[str] = ()) -> dict:
    """Normalise a raw or compacted Serper payload. Serper cannot reliably see ads or SERP blocks."""
    raw_ads = payload.get("ads") or []
    ads = [{"position": "other", "rank": a.get("position") or i, "advertiser_domain": _domain_from(a.get("link"), a.get("displayedLink")),
            "advertiser_name": a.get("source"), "headline": a.get("title"), "description": a.get("snippet") or a.get("description"),
            "display_url": a.get("displayedLink")} for i, a in enumerate(raw_ads, 1)]
    organic_rows = payload.get("organic") if "organic" in payload else payload.get("organic_results")
    organic = _organic(organic_rows or [], known_competitors, "link", "displayedLink")
    paa = payload.get("peopleAlsoAsk") if "peopleAlsoAsk" in payload else payload.get("people_also_ask")
    related = payload.get("relatedSearches") if "relatedSearches" in payload else payload.get("related_searches")
    places = payload.get("places") or []
    shopping_rows = payload.get("shopping") or []
    top10 = [o for o in organic if (o["rank"] or 99) <= 10]
    features = {"ads": True if ads else None, "ai_overview": None, "paa": bool(paa),
                "video": True if payload.get("videos") else None,
                "forum": True if any(o["result_type"] == "forum_community" for o in top10) else None,
                "local_pack": True if places else None, "shopping": True if shopping_rows else None, "perspectives": None}
    return {"ads_status": "observed" if ads else "unobserved", "ads": ads, "organic": organic,
            "shopping": [{"rank": i, "title": s.get("title"), "seller": s.get("source"), "price": s.get("price"),
                          "domain": normalize_host(s.get("link"))} for i, s in enumerate(shopping_rows, 1)],
            "local_pack": [{"rank": i, "title": p.get("title"), "domain": normalize_host(p.get("website")),
                            "rating": p.get("rating"), "reviews": p.get("ratingCount"), "type": p.get("category")}
                           for i, p in enumerate(places, 1)],
            "ai_overview": {"present": None, "cited_domains": None}, "ai_overview_headings": [],
            "paa": [q.get("question") for q in paa or [] if q.get("question")],
            "related": [r.get("query") for r in related or [] if r.get("query")], "features": features}


DROP_LINK_KEYS = {"tracking_link", "serpapi_link", "about_page_serpapi_link", "serpapi_ai_overview_link", "serpapi_pagination"}
GOOGLE_CLICK = re.compile(r"^https?://(www\.)?google\.[a-z.]+/(aclk|goto|url)\b", re.I)


def _strip_links(node: Any, landing: str | None = None) -> Any:
    if isinstance(node, dict):
        return {k: _strip_links(v, landing) for k, v in node.items() if k not in DROP_LINK_KEYS}
    if isinstance(node, list):
        return [_strip_links(v, landing) for v in node]
    if isinstance(node, str) and GOOGLE_CLICK.match(node) and (landing is not None or "/aclk" in node):
        return landing or "redacted_ad_click"
    return node


def redact_serpapi(payload: dict) -> dict:
    """Drop per-search identifiers, SerpApi follow-up links and ad-click redirects before saving a payload.

    Ad click links (google.*/aclk, /goto, /url) are replaced with the advertiser's landing domain so no
    agent follows a real, billable ad click; SerpApi follow-up links would spend searches.
    """
    out = json.loads(json.dumps(payload))
    meta = out.get("search_metadata") or {}
    for key in ("id", "json_endpoint", "markdown_endpoint", "pixel_position_endpoint", "raw_html_file"):
        meta.pop(key, None)
    ads = []
    for ad in out.get("ads") or []:
        domain = _domain_from(None, ad.get("displayed_link"), ad.get("source"))
        ads.append(_strip_links(ad, f"https://{domain}/" if domain else "redacted_ad_click"))
    if "ads" in out:
        out["ads"] = ads
    return {k: (v if k == "ads" else _strip_links(v)) for k, v in out.items() if k not in DROP_LINK_KEYS}


# ------------------------------------------------------------------------------------------ fetching

GOOGLE_DOMAINS = {"de": "google.de", "at": "google.at", "ch": "google.ch", "fr": "google.fr", "it": "google.it",
                  "es": "google.es", "nl": "google.nl", "gb": "google.co.uk", "uk": "google.co.uk", "us": "google.com"}


def _row_params(row: dict) -> dict:
    country = row["locale"].split("-")[-1].lower()
    return {"q": row["query"], "gl": country, "hl": row["language"], "location": row.get("location"),
            "device": row.get("device", "desktop"), "num": 10, "google_domain": GOOGLE_DOMAINS.get(country, "google.com")}


def fetch_serpapi(params: dict, timeout: int = 90) -> dict:
    from common import get_secret
    _, key = get_secret("SERPAPI_API_KEY")
    if not key:
        raise RuntimeError("AUTH_FAILURE: SERPAPI_API_KEY missing; SerpApi SERP data unavailable.")
    query = {"engine": "google", **{k: v for k, v in params.items() if v is not None}, "api_key": key}
    try:
        with urllib.request.urlopen(SERPAPI_ENDPOINT + "?" + urllib.parse.urlencode(query), timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"API_FAILURE: HTTP {exc.code} from SerpApi: {exc.read().decode('utf-8', 'replace')[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"NETWORK_FAILURE: SerpApi unreachable: {exc.reason}") from exc


def fetch_serper(params: dict, timeout: int = 45) -> dict:
    import serper_fetch
    body = {"q": params["q"], "gl": params["gl"], "hl": params["hl"], "num": params["num"]}
    if params.get("location"):
        body["location"] = params["location"]
    return serper_fetch.request_json(serper_fetch.SERPER_ENDPOINTS["search"], body, timeout=timeout)


def capture(row: dict, provider: str, run_dir: Path, *, repeat_index: int = 1,
            known_competitors: Iterable[str] = ()) -> dict:
    """Fetch one SERP for a plan row, save the raw payload and return a normalised capture."""
    params = _row_params(row)
    run_dir = Path(run_dir)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256("|".join(str(x) for x in (row["query"], row["locale"], params["device"],
                                                       params.get("location"), stamp)).encode()).hexdigest()[:8]
    capture_id = f"{row['query_id']}__{provider}__{repeat_index}__{stamp}__{digest}"
    raw_rel = f"raw/{capture_id}.json"
    base = {"capture_id": capture_id, "query_id": row["query_id"], "query": row["query"], "provider": provider,
            "locale": row["locale"], "device": params["device"], "location": params.get("location"),
            "google_domain": params["google_domain"], "repeat_index": repeat_index,
            "captured_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        if provider == "serpapi":
            payload = redact_serpapi(fetch_serpapi(params))
            parsed = parse_serpapi(payload, known_competitors)
        elif provider == "serper_search":
            payload = fetch_serper(params)
            parsed = parse_serper(payload, known_competitors)
        else:
            raise ValueError(f"unsupported provider: {provider}")
    except Exception as exc:  # a failed route is a coverage gap, never absence of results
        return {**base, "error": str(exc), "ads_status": "unobserved", "ads": [], "organic": [], "shopping": [],
                "local_pack": [], "ai_overview": {"present": None, "cited_domains": None}, "ai_overview_headings": [],
                "paa": [], "related": [], "features": {}, "raw_path": None}
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / raw_rel).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {**base, **parsed, "raw_path": raw_rel}


# -------------------------------------------------------------------------------------------- report

def _rows_by_id(plan: dict) -> dict[str, dict]:
    return {r["query_id"]: r for r in plan.get("rows") or []}


def _top10(cap: dict) -> list[dict]:
    return [o for o in cap.get("organic") or [] if (o.get("rank") or 99) <= 10]


def _share(caps: list[dict], rtype: str) -> float | None:
    slots = [o for c in caps for o in _top10(c)]
    return round(sum(o.get("result_type") == rtype for o in slots) / len(slots), 3) if slots else None


def _stage_stats(caps: list[dict], known: set[str]) -> dict:
    status_counts = Counter(c.get("ads_status", "unobserved") for c in caps)
    observed = [c for c in caps if c.get("ads_status") in ("observed", "observed_none")]
    adv_caps: Counter = Counter()
    for c in observed:
        for d in {a.get("advertiser_domain") for a in c.get("ads") or [] if a.get("advertiser_domain")}:
            adv_caps[d] += 1
    by_query: dict[str, list[set]] = defaultdict(list)
    for c in observed:
        by_query[c["query_id"]].append({a.get("advertiser_domain") for a in c.get("ads") or [] if a.get("advertiser_domain")})
    stable, occasional = set(), set()
    for runs in by_query.values():
        if len(runs) >= 2:
            stable |= set.intersection(*runs)
            occasional |= set.union(*runs) - set.intersection(*runs)
    type_mix = Counter(o.get("result_type", "unknown") for c in caps for o in _top10(c))
    ai = Counter("present" if c.get("ai_overview", {}).get("present") is True else
                 "absent" if c.get("ai_overview", {}).get("present") is False else "unknown" for c in caps)
    ad_types = {}
    for c in observed:
        for a in c.get("ads") or []:
            ad_types[a.get("advertiser_domain")] = classify_domain(a.get("advertiser_domain") or "", known)
    candidates = {d for d, t in ad_types.items() if d and t not in ("competitor", "government_institution", "forum_community", "video")}
    organic_unknown = Counter(o["domain"] for c in caps for o in _top10(c) if o.get("result_type") == "unknown" and o.get("domain"))
    candidates |= set(organic_unknown)
    claims, seen_claims = [], set()
    for c in observed:
        for a in c.get("ads") or []:
            key = (a.get("advertiser_domain"), a.get("headline"))
            if key not in seen_claims:
                seen_claims.add(key)
                claims.append({"query_id": c["query_id"], "advertiser_domain": a.get("advertiser_domain"),
                               "position": a.get("position"), "headline": a.get("headline"), "description": a.get("description")})
    return {
        "queries": sorted({c["query_id"] for c in caps}),
        "captures": len(caps),
        "ads_status_counts": {k: status_counts.get(k, 0) for k in ("observed", "observed_none", "no_results", "unobserved")},
        "queries_observed_for_ads": len({c["query_id"] for c in observed}),
        "queries_with_ads": len({c["query_id"] for c in observed if c.get("ads")}) if observed else None,
        "advertiser_count": len(adv_caps) if observed else None,
        "advertisers": dict(adv_caps.most_common()),
        "repeated_advertisers": sorted(d for d, n in adv_caps.items() if n >= 2),
        "stable_advertisers": sorted(stable),
        "occasional_advertisers": sorted(occasional),
        "top_ad_positions": dict(Counter(a.get("position") for c in observed for a in c.get("ads") or [])),
        "organic_type_mix": dict(type_mix.most_common()),
        "forum_share_top10": _share(caps, "forum_community"),
        "aggregator_share_top10": _share(caps, "marketplace_aggregator"),
        "ai_overview": {k: ai.get(k, 0) for k in ("present", "absent", "unknown")},
        "new_competitor_candidates": sorted(candidates - {normalize_host(k) for k in known}),
        "ad_claims": claims[:25],
        "errors": [{"query_id": c["query_id"], "provider": c.get("provider"), "error": c["error"]} for c in caps if c.get("error")],
    }


def build_report(captures: list[dict], plan: dict, run_dir: Path | None = None) -> dict:
    rows = _rows_by_id(plan)
    known = {normalize_host(c) for c in plan.get("known_competitors") or []}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for cap in captures:
        stage = rows.get(cap["query_id"], {}).get("journey_stage", "unassigned")
        grouped[stage].append(cap)
    stages = {s: _stage_stats(grouped[s], known) for s in STAGES + ["unassigned"] if grouped.get(s)}
    for stage, st in stages.items():
        origins_here = [rows.get(q, {}).get("seed_origin", "brainstorm") for q in st["queries"]]
        st["observed_seed_fraction"] = _observed_fraction(origins_here)
        st["brainstorm_only"] = st["observed_seed_fraction"] == 0
    hypotheses = []
    for stage, st in stages.items():
        label = f"{stage}) (brainstorm-only stage" if st["brainstorm_only"] else stage
        if stage == "problem_aware" and (st["forum_share_top10"] or 0) >= 0.1:
            hypotheses.append(f"Hypothesis ({label}): forum/community pages hold {st['forum_share_top10']:.0%} of top-10 slots; "
                              "searchers may lack an authoritative answer. Check the threads before the case appraisal uses it.")
        if stage in ("purchase", "comparison") and (st["aggregator_share_top10"] or 0) >= 0.3:
            hypotheses.append(f"Hypothesis ({label}): aggregators/marketplaces hold {st['aggregator_share_top10']:.0%} of top-10 slots; "
                              "an independent page may compete with them for organic and paid attention. Not a finding until tested.")
        if st["queries_observed_for_ads"] and st["queries_with_ads"] and st["queries_with_ads"] / st["queries_observed_for_ads"] >= 0.5:
            hypotheses.append(f"Hypothesis ({label}): suppliers bid on most observed queries; paid acquisition at this intent "
                              "is contested. Ads show supplier spend, not customer demand.")
    origins = Counter(r.get("seed_origin") for r in rows.values())
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "providers": sorted({c.get("provider") for c in captures}),
        "locales": sorted({c.get("locale") for c in captures}),
        "devices": sorted({c.get("device") for c in captures if c.get("device")}),
        "locations": sorted({c.get("location") for c in captures if c.get("location")}),
        "captured_window": [min((c["captured_at"] for c in captures), default=None),
                            max((c["captured_at"] for c in captures), default=None)],
        "searches": len([c for c in captures if not c.get("error")]),
        "seed_origin_mix": dict(origins),
        "stages": stages,
        "hypotheses": hypotheses,
        "caveats": CAVEATS,
    }
    if run_dir is not None:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "serp-landscape.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (run_dir / "serp-landscape.md").write_text(render_markdown(report, plan), encoding="utf-8")
    return report


def _observed_fraction(origins: list[str]) -> float:
    return round(sum(o != "brainstorm" for o in origins) / len(origins), 3) if origins else 0.0


def _ads_line(st: dict) -> str:
    counts = st["ads_status_counts"]
    if counts.get("no_results") == st["captures"]:
        return f"- Ads: Google returned no results on all {st['captures']} captures (no_results; not observed_none)."
    if st["advertiser_count"] is None:
        return (f"- Ads: **unobserved** on all {st['captures']} captures (provider cannot see ads; not zero, not absence).")
    tail = f"; unobserved on {counts['unobserved']} captures" if counts["unobserved"] else ""
    if counts.get("no_results"):
        tail += f"; no results on {counts['no_results']} captures"
    if not st["queries_with_ads"]:
        return (f"- Ads: none observed on {st['queries_observed_for_ads']} queries checked{tail} "
                "(no ads is not evidence of no demand).")
    return (f"- Ads: observed on {st['queries_with_ads']} of {st['queries_observed_for_ads']} queries checked{tail}; "
            f"{st['advertiser_count']} distinct advertisers; positions {st['top_ad_positions']}.")


def render_markdown(report: dict, plan: dict | None = None) -> str:
    rows = _rows_by_id(plan or {})
    lines = ["# SERP landscape: customer search journey", "",
             f"Providers: {', '.join(report['providers'])}. Locales: {', '.join(report['locales'])}. "
             f"Devices: {', '.join(report['devices']) or 'n/a'}. Locations: {', '.join(report['locations']) or 'n/a'}.",
             f"Captured: {report['captured_window'][0]} to {report['captured_window'][1]}. Searches: {report['searches']}.",
             f"Seed origins: {report['seed_origin_mix']} (brainstorm rows are hypotheses).", ""]
    for stage, st in report["stages"].items():
        lines += [f"## {stage}" + (" (brainstorm-only stage)" if st.get("brainstorm_only") else ""), "",
                  f"Observed-seed fraction: {st.get('observed_seed_fraction', 0):.0%} of this stage's queries came from a non-brainstorm origin."]
        for qid in st["queries"]:
            r = rows.get(qid, {})
            lines.append(f"- `{qid}` {r.get('query', '')} ({r.get('intent', '?')}, {r.get('searcher_role', '?')}, {r.get('seed_origin', '?')})")
        lines.append(_ads_line(st))
        if st["advertisers"]:
            lines.append(f"- Advertisers (captures): {st['advertisers']}. Repeated: {st['repeated_advertisers'] or 'none'}.")
        if st["stable_advertisers"] or st["occasional_advertisers"]:
            lines.append(f"- Across repeats: stable {st['stable_advertisers'] or 'none'}; occasional {st['occasional_advertisers'] or 'none'}.")
        lines.append(f"- Organic top-10 type mix: {st['organic_type_mix']}.")
        fs, ag = st["forum_share_top10"], st["aggregator_share_top10"]
        lines.append(f"- Forum share top 10: {'n/a' if fs is None else f'{fs:.0%}'}; aggregator share: {'n/a' if ag is None else f'{ag:.0%}'}.")
        lines.append(f"- AI overview: {st['ai_overview']}.")
        cands = st["new_competitor_candidates"]
        if cands:
            shown = f"{len(cands)} total, first 15" if len(cands) > 15 else f"{len(cands)} total"
            lines.append(f"- Advertisers and unclassified ranking domains for competitor-research scout triage ({shown}; unverified, "
                         f"may include institutions): {', '.join(cands[:15])}.")
        for claim in st["ad_claims"][:6]:
            lines.append(f"  - Ad claim [{claim['advertiser_domain']}, {claim['position']}]: {claim['headline']} | {claim['description']}")
        for err in st["errors"]:
            lines.append(f"- Coverage gap: `{err['query_id']}` via {err['provider']}: {err['error'][:160]}")
        lines.append("")
    lines += ["## Hypotheses for the case appraisal (not findings)", ""]
    lines += [f"- {h}" for h in report["hypotheses"]] or ["- None from SERP shape."]
    lines += ["", "## Caveats", ""] + [f"- {c}" for c in report["caveats"]]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------- content opportunities

# Compound-friendly substrings (German compounds such as "Versicherungsvergleich") and whole words.
CALC_SUBSTRINGS = ("rechner", "calculator", "berechnen")
CALC_WORDS = {"kosten", "cost", "costs", "price", "preis", "preise", "beitrag"}
COMPARE_SUBSTRINGS = ("vergleich",)
COMPARE_WORDS = {"vs", "versus", "compare", "comparison", "beste", "besten", "best", "test", "testsieger", "alternative", "alternativen"}


def _has(text: str, substrings: Iterable[str], words: set[str]) -> bool:
    tokens = set(re.findall(r"[\wäöüß]+", text))
    return any(s in text for s in substrings) or bool(tokens & words)
BRIDGES = {
    "guide": "Offer a short self-check or checklist that leads to the solution explainer (suggestion; test it).",
    "faq": "Answer the question, then link to the matching guide or comparison page (suggestion; test it).",
    "comparison": "Invite the reader to a shortlist, comparison table or consultation request (suggestion; test it).",
    "calculator": "Show the estimate, then offer a personalised quote or saved result (suggestion; test it).",
    "landing": "Primary call to action to request a quote, book or start (suggestion; test it).",
    "local_page": "Call, visit or book a local appointment (suggestion; test it).",
}


def _cluster_key(row: dict) -> str:
    return row.get("cluster_id") or f"{row['journey_stage']}:{row['searcher_role']}:{row['intent']}:{row['locale']}"


def _tri(values: list) -> bool | None:
    if any(v is True for v in values):
        return True
    if values and all(v is False for v in values):
        return False
    return None


def _ads_feature(statuses: set[str]) -> str:
    if statuses == {"no_results"}:
        return "no_results"
    statuses = statuses - {"no_results"}
    if "observed" in statuses:
        return "observed"
    if statuses == {"observed_none"}:
        return "observed_none"
    if statuses == {"unobserved"} or not statuses:
        return "unobserved"
    return "mixed"


def _query_page_type(stage: str, query: str, paa_count: int, local: bool | None) -> str:
    text = query.lower()
    if stage == "local" or local:
        return "local_page"
    if _has(text, CALC_SUBSTRINGS, set()):
        return "calculator"
    if stage == "comparison" or _has(text, COMPARE_SUBSTRINGS, COMPARE_WORDS):
        return "comparison"
    if stage == "purchase":
        return "calculator" if _has(text, CALC_SUBSTRINGS, CALC_WORDS) else "landing"
    if stage == "post_purchase" or (stage == "problem_aware" and paa_count >= 4):
        return "faq"
    return "guide"


def _page_type(stage: str, queries: list[str], paa_count: int, local: bool | None) -> str:
    """Majority page type across the cluster's queries; ties go to the first query's type."""
    votes = [_query_page_type(stage, q, paa_count, local) for q in queries]
    counts = Counter(votes)
    best = max(counts.values())
    return next(v for v in votes if counts[v] == best)


def build_content_opportunities(captures: list[dict], plan: dict) -> dict:
    clusters: dict[str, list[dict]] = defaultdict(list)
    for row in plan.get("rows") or []:
        clusters[_cluster_key(row)].append(row)
    by_query: dict[str, list[dict]] = defaultdict(list)
    for cap in captures:
        if not cap.get("error"):
            by_query[cap["query_id"]].append(cap)
    out_rows, uncaptured = [], []
    for cid, rows in clusters.items():
        caps = [c for r in rows for c in by_query.get(r["query_id"], [])]
        refs = sorted({c["raw_path"] for c in caps if c.get("raw_path")})
        if not caps or not refs:
            uncaptured.append(cid)
            continue
        paa = list(dict.fromkeys(q for c in caps for q in c.get("paa") or []))
        related = list(dict.fromkeys(q for c in caps for q in c.get("related") or []))
        headings = list(dict.fromkeys(h for c in caps for h in c.get("ai_overview_headings") or []))
        feats = [c.get("features") or {} for c in caps]
        top = [o for c in caps for o in _top10(c)]
        ranking: dict[str, list[str]] = defaultdict(list)
        for o in top:
            if o.get("domain") and o["domain"] not in ranking[o["result_type"]]:
                ranking[o["result_type"]].append(o["domain"])
        forum = [d for d in ranking.get("forum_community", [])]
        agg_slots = sum(o.get("result_type") == "marketplace_aggregator" for o in top)
        parts = []
        if forum:
            parts.append(f"Forum/community pages rank in the top 10 ({', '.join(forum[:4])}); searchers may not find an authoritative answer.")
        if agg_slots >= 3:
            parts.append(f"Aggregators hold {agg_slots} top-10 slots across these SERPs; an independent page may compete with comparison portals.")
        if paa:
            parts.append(f"{len(paa)} People-also-ask questions show sub-questions the ranking pages may or may not answer.")
        if not parts:
            parts.append("No SERP-shape signal of an unanswered need.")
        parts.append("Read the ranking pages before treating this as a gap; a gap does not prove demand.")
        stage = rows[0]["journey_stage"]
        page = _page_type(stage, [r["query"] for r in rows], len(paa), _tri([f.get("local_pack") for f in feats]))
        out_rows.append({
            "cluster_id": cid,
            "queries": [{"query_id": r["query_id"], "query": r["query"], "seed_origin": r["seed_origin"]} for r in rows],
            "journey_stage": stage,
            "intent": Counter(r["intent"] for r in rows).most_common(1)[0][0],
            "searcher_role": Counter(r["searcher_role"] for r in rows).most_common(1)[0][0],
            "locale": rows[0]["locale"],
            "questions": {"paa": paa[:20], "related_searches": related[:20], "ai_overview_prompts": headings[:10]},
            "serp_features": {
                "ads": _ads_feature({c.get("ads_status", "unobserved") for c in caps}),
                "ai_overview": _tri([c.get("ai_overview", {}).get("present") for c in caps]),
                "paa": bool(paa),
                "video": _tri([f.get("video") for f in feats]),
                "forum": _tri([f.get("forum") for f in feats]),
                "local_pack": _tri([f.get("local_pack") for f in feats]),
                "shopping": _tri([f.get("shopping") for f in feats]),
            },
            "ranking_by_type": dict(ranking),
            "content_gap": {"status": "hypothesis", "hypothesis": " ".join(parts), "evidence_refs": refs, "needs_review": True},
            "recommended_page_type": page,
            "conversion_bridge": BRIDGES[page],
            "evidence_refs": refs,
            "observed_seed_fraction": _observed_fraction([r["seed_origin"] for r in rows]),
            "evidence_status": "includes_observed_seed" if any(r["seed_origin"] != "brainstorm" for r in rows) else "brainstorm_hypothesis_only",
            "volume": None,
        })
    # Rows with a non-brainstorm seed rank first, then by journey order.
    out_rows.sort(key=lambda r: (r["evidence_status"] != "includes_observed_seed", STAGES.index(r["journey_stage"])))
    doc = {"schema_version": 1, "source": "search_journey_serp_study",
           "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "caveats": CAVEATS + ["One input to content planning alongside the competitor content inventory, customer questions "
                                 "from reviewed voice and social discussion topics. Volumes stay null until a volume provider fills them."],
           "rows": out_rows}
    if uncaptured:
        doc["uncaptured_clusters"] = uncaptured
    return doc


# ----------------------------------------------------------------------------------------------- CLI

def load_competitor_domains(path: Path) -> set[str]:
    """Collect domains from a landscape/competitor JSON: URL strings anywhere, bare domains under domain/website keys."""
    found: set[str] = set()

    def walk(node: Any, key: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k.lower())
        elif isinstance(node, list):
            for v in node:
                walk(v, key)
        elif isinstance(node, str):
            if node.startswith(("http://", "https://")) or (any(t in key for t in ("domain", "website", "site")) and "." in node and " " not in node):
                host = normalize_host(node)
                if host and classify_url(None, (), domain=host)[1] == "none":
                    found.add(host)

    walk(json.loads(Path(path).read_text(encoding="utf-8")))
    return found


def _capture_key(cap_or_row: dict, provider: str | None = None, repeat_index: int | None = None) -> tuple:
    params = cap_or_row if "device" in cap_or_row and "captured_at" in cap_or_row else _row_params(cap_or_row)
    return (cap_or_row["query_id"], cap_or_row["query"], cap_or_row["locale"], params.get("device", "desktop"),
            params.get("location"), provider or cap_or_row.get("provider"),
            repeat_index if repeat_index is not None else cap_or_row.get("repeat_index", 1))


def load_captures(run_dir: Path) -> list[dict]:
    path = Path(run_dir) / "captures.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _reusable(run_dir: Path, row: dict, provider: str, repeat_index: int) -> dict | None:
    """Reuse a current capture of the same query, locale, device, location, provider and repeat within REUSE_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=REUSE_DAYS)
    key = _capture_key(row, provider, repeat_index)
    for cap in reversed(load_captures(run_dir)):
        if _capture_key(cap) == key and not cap.get("error") and not cap.get("superseded_by") \
                and datetime.fromisoformat(cap["captured_at"].replace("Z", "+00:00")) >= cutoff:
            return cap
    return None


def merge_captures(existing: list[dict], new: list[dict]) -> list[dict]:
    """Append new captures; earlier rows with the same key are kept and marked superseded, never rewritten away."""
    merged = [dict(c) for c in existing]
    ids = {c.get("capture_id") for c in merged}
    for cap in new:
        if cap.get("capture_id") in ids:
            continue
        for old in merged:
            if _capture_key(old) == _capture_key(cap) and not old.get("superseded_by"):
                old["superseded_by"] = cap["capture_id"]
        merged.append(cap)
        ids.add(cap.get("capture_id"))
    return merged


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--providers", default="serpapi", help="Comma list: serpapi (sees ads), serper_search (organic-only fallback).")
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--competitors", type=Path, help="Landscape or competitor JSON; its domains classify as competitor.")
    ap.add_argument("--repeat", type=int, default=1, help="Captures per query, to separate stable from occasional advertisers.")
    ap.add_argument("--repeat-gap-minutes", type=float, default=0.0)
    ap.add_argument("--max-searches", type=int, default=30, help="Refuse runs that would exceed this many paid searches.")
    args = ap.parse_args(argv)

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    errors = validate_plan(plan)
    if errors:
        print("Plan invalid:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    known = {normalize_host(c) for c in plan.get("known_competitors") or []}
    if args.competitors:
        known |= load_competitor_domains(args.competitors)
        plan = {**plan, "known_competitors": sorted(known)}
    planned = len(plan["rows"]) * len(providers) * args.repeat
    if planned > args.max_searches:
        print(f"Refusing: {planned} searches planned > --max-searches {args.max_searches}.", file=sys.stderr)
        return 2
    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "search-journey-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    captures, fetched = [], 0
    for rep in range(1, args.repeat + 1):
        if rep > 1 and args.repeat_gap_minutes:
            time.sleep(args.repeat_gap_minutes * 60)
        for row in plan["rows"]:
            for provider in providers:
                cap = _reusable(run_dir, row, provider, rep)
                if cap is None:
                    cap = capture(row, provider, run_dir, repeat_index=rep, known_competitors=known)
                    fetched += 1
                captures.append(cap)
    merged = merge_captures(load_captures(run_dir), captures)
    (run_dir / "captures.json").write_text(json.dumps(merged, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    build_report(captures, plan, run_dir)
    opportunities = build_content_opportunities(captures, plan)
    problems = validate_content_opportunities(opportunities)
    if problems:
        print("content-opportunities invalid:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    (run_dir / "content-opportunities.json").write_text(json.dumps(opportunities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = sum(1 for c in captures if c.get("error"))
    print(json.dumps({"run_dir": str(run_dir), "captures": len(captures), "fetched": fetched, "failed": failed,
                      "content_opportunity_rows": len(opportunities["rows"])}))
    return 0 if failed < len(captures) else 1


if __name__ == "__main__":
    raise SystemExit(main())
