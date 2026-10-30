#!/usr/bin/env python3
"""Analyze competitor marketing from public web pages.

`--content-inventory` inventories what competitors and similar companies publish (topics, questions, formats,
depth) into competitor-content.json (schemas/competitor-content.schema.json). It records topics and structure,
never reuses wording: no page body is stored, excerpts are capped at 300 characters, and robots.txt is respected.
Supplier content shows what suppliers publish, not what customers need; similar companies and capability
references are inspiration for format and structure only, never market evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any
from urllib.robotparser import RobotFileParser


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "scripts" / "validate_apis"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import get_secret, http_get, http_post, now_iso, redact_sensitive, status_from_response  # noqa: E402
from workspace import resolve_run_dir, update_stage  # noqa: E402


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in safe.split("-") if part)[:80] or "marketing"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def domain_of(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host[4:] if host.startswith("www.") else host


def normalize_base_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme or "https"
    host = parsed.netloc or parsed.path.split("/")[0]
    return f"{scheme}://{host}".rstrip("/")


def deep_urls(url: str) -> list[str]:
    base = normalize_base_url(url)
    paths = [
        "",
        "/pricing",
        "/features",
        "/customers",
        "/case-studies",
        "/compare",
        "/alternatives",
        "/blog",
        "/integrations",
        "/docs",
        "/changelog",
        "/release-notes",
    ]
    return [base + path for path in paths]


def scrape_url(url: str, formats: list[str] | None = None) -> dict[str, Any]:
    _, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    if not api_key:
        return {"ok": False, "status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}
    return http_post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {api_key}"},
        data={"url": url, "formats": formats or ["markdown"], "onlyMainContent": True},
    )


def direct_fetch_url(url: str) -> dict[str, Any]:
    response = http_get(url, headers={"User-Agent": "evidence-scout-marketing-fallback/0.1"})
    if not response.get("ok"):
        return response
    body = response.get("body") or {}
    html = body.get("text", "") if isinstance(body, dict) else ""
    html = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", html)
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    description_match = re.search(r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html)
    text = re.sub(r"(?is)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "ok": True,
        "status_code": response.get("status_code"),
        "body": {
            "data": {
                "metadata": {
                    "title": compact_text(title_match.group(1), 200) if title_match else "",
                    "description": compact_text(description_match.group(1), 500) if description_match else "",
                },
                "markdown": compact_text(text, 12000),
            }
        },
    }


def cached_competitor_page(item: dict[str, Any]) -> dict[str, Any]:
    snippets = item.get("evidence_snippets") or []
    text = "\n\n".join(str(snippet) for snippet in snippets if snippet)
    return {
        "url": item.get("url", ""),
        "body": {
            "data": {
                "metadata": {
                    "title": item.get("page_title") or item.get("name") or "",
                    "description": snippets[0] if snippets else "",
                },
                "markdown": text,
            }
        },
        "fallback_source": "competitors_json_snippet",
    }


def compact_text(value: str, limit: int = 8000) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def find_phrases(text: str, patterns: list[str]) -> list[str]:
    found: list[str] = []
    lower = text.lower()
    for pattern in patterns:
        idx = lower.find(pattern)
        if idx >= 0:
            found.append(text[max(0, idx - 80) : idx + 180].strip())
    return found[:8]


def page_text(raw_body: dict[str, Any]) -> tuple[dict[str, Any], str]:
    data = raw_body.get("data") if isinstance(raw_body.get("data"), dict) else raw_body
    metadata = data.get("metadata") if isinstance(data, dict) else {}
    markdown = data.get("markdown", "") if isinstance(data, dict) else ""
    return metadata, compact_text(markdown)


def merge_pages(url: str, page_bodies: list[dict[str, Any]]) -> tuple[dict[str, Any], str, list[dict[str, str]]]:
    metadata: dict[str, Any] = {}
    texts: list[str] = []
    source_pages: list[dict[str, str]] = []
    for page in page_bodies:
        page_url = page.get("url", url)
        page_metadata, text = page_text(page.get("body") or {})
        if not metadata and page_metadata:
            metadata = page_metadata
        if text:
            texts.append(text)
            source_pages.append({"url": page_url, "title": page_metadata.get("title", ""), "retrieval_source": str(page.get("retrieval_source") or page.get("fallback_source") or "unknown")})
    return metadata, compact_text(" ".join(texts), 24000), source_pages


def classify_pricing_posture(text: str) -> str:
    lower = text.lower()
    if "contact sales" in lower and "$" not in lower:
        return "sales-led_or_hidden_pricing"
    price_tokens = extract_price_tokens(text)
    monetary_labels = ["currency_amounts", "monthly_terms", "annual_terms", "savings_claims", "deductible_terms", "salary_thresholds"]
    if any(price_tokens[label] for label in monetary_labels):
        return "transparent_pricing_signal"
    if "free trial" in lower or "try for free" in lower:
        return "trial_led_signal"
    if "free plan" in lower or "freemium" in lower:
        return "freemium_signal"
    if any(marker in lower for marker in ["pricing", "preis", "preise", "tarif", "beitrag", "premium", "transparenz", "transparent"]):
        return "pricing_language_only"
    return "not_found"


def extract_price_tokens(text: str) -> dict[str, list[str]]:
    snippets = compact_text(text, 24000)
    patterns = {
        "currency_amounts": r"(?:€|\$|eur\s*)\s?(?:\d{1,3}(?:[.,]\d{3})+|\d{1,6})(?:[.,]\d{1,2})?|(?:\d{1,3}(?:[.,]\d{3})+|\d{1,6})(?:[.,]\d{1,2})?\s?(?:€|eur)",
        "monthly_terms": r"\b(?:per month|monthly|monatlich|mtl\.?|/monat|im monat)\b",
        "annual_terms": r"\b(?:per year|annually|jährlich|jaehrlich|/jahr|im jahr)\b",
        "savings_claims": r"\b(?:save|sparen|ersparnis|bis zu\s+\d+%|up to\s+\d+%)\b",
        "deductible_terms": r"\b(?:deductible|selbstbeteiligung|selbstbehalt)\b",
        "salary_thresholds": r"\b(?:jahresarbeitsentgeltgrenze|pflichtversicherungsgrenze|salary threshold|income threshold)\b",
        "tariff_terms": r"\b(?:tarif|tariff|beitrag|premium)\b",
    }
    tokens: dict[str, list[str]] = {}
    for label, pattern in patterns.items():
        matches = []
        for match in re.finditer(pattern, snippets, flags=re.IGNORECASE):
            value = " ".join(match.group(0).split())
            if value not in matches:
                matches.append(value)
            if len(matches) >= 8:
                break
        tokens[label] = matches
    return tokens


def normalize_currency_amount(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    currency = "EUR" if "€" in cleaned or "eur" in cleaned.lower() else "USD" if "$" in cleaned else "unknown"
    numeric = re.sub(r"(?i)(eur|€|\$)", "", cleaned).strip()
    if "," in numeric and "." in numeric:
        decimal_sep = "," if numeric.rfind(",") > numeric.rfind(".") else "."
        thousands_sep = "." if decimal_sep == "," else ","
        numeric = numeric.replace(thousands_sep, "").replace(decimal_sep, ".")
    elif "," in numeric:
        parts = numeric.split(",")
        numeric = numeric.replace(",", "") if len(parts[-1]) == 3 else numeric.replace(",", ".")
    elif "." in numeric:
        parts = numeric.split(".")
        numeric = numeric.replace(".", "") if len(parts[-1]) == 3 and len(parts) > 1 else numeric
    try:
        value = float(numeric)
    except ValueError:
        value = None
    return {"raw": raw, "currency": currency, "value": value}


def normalize_price_tokens(tokens: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "currency_amounts": [normalize_currency_amount(raw) for raw in tokens.get("currency_amounts", [])],
        "monthly_terms": tokens.get("monthly_terms", []),
        "annual_terms": tokens.get("annual_terms", []),
        "savings_claims": tokens.get("savings_claims", []),
        "deductible_terms": tokens.get("deductible_terms", []),
        "salary_thresholds": tokens.get("salary_thresholds", []),
        "tariff_terms": tokens.get("tariff_terms", []),
    }


def classify_page_type(url: str, title: str, text: str) -> str:
    path = urllib.parse.urlsplit(url).path.lower().strip("/")
    lower = f"{title} {text[:2000]}".lower()
    if any(part in path for part in ["blog", "ratgeber", "guide", "wissen", "article"]):
        return "blog_article"
    if any(part in path for part in ["compare", "vergleich", "comparison", "private-krankenversicherung", "privatekrankenversicherung", "private-health-insurance", "berufsun"]):
        return "product_page"
    if any(marker in lower for marker in ["vergleich", "compare", "comparison portal"]) and any(marker in lower for marker in ["pkv", "private health", "krankenversicherung"]):
        return "comparison_article"
    if not path:
        return "homepage"
    return "other_page"


def extract_button_like_ctas(text: str) -> list[str]:
    patterns = [
        r"\[([^\]]{3,80})\]\([^)]+\)",
        r"\b(?:Jetzt|Kostenlos|Free|Get|Start|Book|Termin|Beratung|Angebot)[^\n.!?]{0,80}",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = " ".join((match.group(1) if match.lastindex else match.group(0)).split())
            if value and value.lower() not in {item.lower() for item in found}:
                found.append(value[:120])
            if len(found) >= 8:
                return found
    return found


def extract_social_link_hints(text: str) -> list[dict[str, str]]:
    """Extract only explicit public links; a hint is not verified presence."""
    platforms = {
        "youtube": r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s)]+",
        "instagram": r"https?://(?:www\.)?instagram\.com/[^\s)]+",
        "facebook": r"https?://(?:www\.)?facebook\.com/[^\s)]+",
        "linkedin": r"https?://(?:www\.)?linkedin\.com/[^\s)]+",
        "tiktok": r"https?://(?:www\.)?tiktok\.com/[^\s)]+",
        "x": r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[^\s)]+",
    }
    found: list[dict[str, str]] = []
    for platform, pattern in platforms.items():
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            url = match.rstrip(".,;\"")
            if not any(item["url"] == url for item in found):
                found.append({"platform": platform, "url": url, "status": "unverified", "evidence_type": "official_entity_page_link"})
    return found[:20]


def requested_capabilities(entity_meta: dict[str, Any] | None) -> list[str]:
    values: list[str] = []
    for source in (entity_meta or {}).get("sources", []):
        if isinstance(source, dict) and source.get("lane_scope") == "capability_reference":
            value = str(source.get("scope_value", "")).casefold().strip()
            if value and value not in values:
                values.append(value)
    return values


def extract_capability_patterns(capabilities: list[str], result: dict[str, Any], text: str) -> list[dict[str, str]]:
    """Return only capability-specific observed patterns, not generic page titles."""
    patterns: list[dict[str, str]] = []
    for capability in capabilities:
        observed = ""
        if capability == "onboarding":
            matches = find_phrases(text, ["onboarding", "product tour", "guided setup", "getting started", "step-by-step"])
            observed = matches[0] if matches else ""
        elif capability == "pricing" and result.get("price_status") == "structured_price_found":
            observed = f"Structured pricing is publicly visible: {result.get('normalized_price_tokens', {})}"
        elif capability == "trust" and result.get("trust_proof_language"):
            observed = str(result["trust_proof_language"][0])
        elif capability == "offer" and result.get("service_offers"):
            observed = str(result["service_offers"][0].get("observed_text", ""))
        elif capability == "positioning" and result.get("description") and result.get("title"):
            observed = f"{result['title']} — {result['description']}"
        elif capability == "website":
            signal_count = sum(bool(result.get(key)) for key in ["cta_language", "trust_proof_language", "feature_language"])
            if signal_count >= 2:
                observed = f"Page combines {signal_count} evidenced conversion/trust/product signal groups."
        if observed:
            patterns.append({"capability": capability, "observed_pattern": " ".join(observed.split())[:360]})
    return patterns


def extract_service_offers(text: str, audience_patterns: list[str]) -> list[dict[str, Any]]:
    """Extract source snippets as offer observations, never as inferred packages."""
    markers = ["service", "package", "plan", "solution", "consulting", "subscription", "membership"]
    sentences = [" ".join(part.split()) for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    offers: list[dict[str, Any]] = []
    for sentence in sentences:
        lower = sentence.casefold()
        if not any(marker in lower for marker in markers):
            continue
        price_tokens = extract_price_tokens(sentence)
        offers.append({
            "observed_text": sentence[:360],
            "target_segments": [pattern for pattern in audience_patterns if pattern in lower],
            "prices": normalize_price_tokens(price_tokens),
            "price_status": "structured_price_found" if price_tokens.get("currency_amounts") else "not_found",
            "conditions": [value for key in ("monthly_terms", "annual_terms") for value in price_tokens.get(key, [])],
            "evidence_type": "official_page_copy",
        })
        if len(offers) >= 12:
            break
    return offers


def analyze_text(url: str, page_bodies: list[dict[str, Any]], entity_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata, text, source_pages = merge_pages(url, page_bodies)
    lower = text.lower()
    cta_patterns = [
        "get started",
        "start free",
        "book a demo",
        "request a demo",
        "try for free",
        "contact sales",
        "sign up",
        "join waitlist",
        "angebot anfordern",
        "beratung vereinbaren",
        "vergleich starten",
        "kostenlos vergleichen",
        "jetzt berechnen",
        "beitrag berechnen",
        "get a free quote",
        "get consultation",
        "get a consultation",
        "free quote",
        "kontakt aufnehmen",
        "termin vereinbaren",
    ]
    proof_patterns = ["trusted by", "customers", "reviews", "case study", "security", "soc 2", "gdpr", "teams at", "trustpilot", "provenexpert", "stiftung warentest", "bafin", "ihk"]
    pricing_patterns = ["pricing", "$", "€", "eur", "free trial", "free plan", "per month", "per user", "enterprise", "monatlich", "mtl", "jährlich", "sparen", "ersparnis", "deductible", "selbstbeteiligung", "tarif", "beitrag"]
    audience_patterns = ["freelancer", "freiberufler", "selbstständig", "self-employed", "agency", "small business", "enterprise", "creator", "founder", "team", "manager", "developer", "expat", "international resident"]
    content_patterns = ["blog", "guide", "template", "alternatives", "compare", "vs", "resources", "webinar", "report"]
    product_change_patterns = ["changelog", "release notes", "what's new", "docs", "api", "integrations", "roadmap"]
    distribution_patterns = ["partners", "affiliate", "marketplace", "integrations", "community", "app store", "chrome extension"]
    pain_patterns = ["manual", "spreadsheet", "waste", "slow", "error", "missed", "overwhelmed", "chaos", "busywork", "fragmented"]
    price_tokens = extract_price_tokens(text)
    page_type = classify_page_type(url, metadata.get("title", ""), text)
    social_links = extract_social_link_hints(text)
    service_offers = extract_service_offers(text, audience_patterns)
    first_party_sources = [
        page for page in source_pages
        if page.get("retrieval_source") in {"firecrawl", "direct_http", "fixture_official"}
        and domain_of(str(page.get("url", ""))) == domain_of(url)
    ]
    official_service_evidence = bool(first_party_sources and page_type in {"homepage", "product_page"} and service_offers)
    offer_evidence_type = "official_page_copy" if official_service_evidence else "search_or_cached_copy"
    for offer in service_offers:
        offer["evidence_type"] = offer_evidence_type
    result = {
        "url": url,
        "domain": domain_of(url),
        "retrieved_at": now_iso(),
        "source_pages": source_pages,
        "first_party_source_pages": first_party_sources,
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "page_type": page_type,
        "positioning_headline": (metadata.get("title") or text[:160]).strip(),
        "detected_audiences": [pattern for pattern in audience_patterns if pattern in lower],
        "pain_language": find_phrases(text, pain_patterns),
        "cta_language": find_phrases(text, cta_patterns),
        "button_like_ctas": extract_button_like_ctas(text),
        "social_link_hints": social_links,
        "social_presence": [
            {**item, "retrieved_at": now_iso(), "role": "linked_from_official_site", "posts_sampled": 0, "coverage_gap": "Profile activity and content usage not sampled."}
            for item in social_links
        ],
        "pricing_posture": classify_pricing_posture(text),
        "pricing_language": find_phrases(text, pricing_patterns),
        "structured_price_tokens": price_tokens,
        "normalized_price_tokens": normalize_price_tokens(price_tokens),
        "trust_proof_language": find_phrases(text, proof_patterns),
        "feature_language": find_phrases(text, ["automate", "collaborate", "track", "manage", "integrate", "workflow", "dashboard", "report"]),
        "seo_content_clues": find_phrases(text, content_patterns),
        "product_change_clues": find_phrases(text, product_change_patterns),
        "distribution_clues": find_phrases(text, distribution_patterns),
        "offer_signals": find_phrases(text, ["service", "package", "plan", "solution", "consulting", "subscription", "membership"]),
        "service_offers": service_offers,
        "official_service_evidence": official_service_evidence,
        "price_status": "structured_price_found" if price_tokens.get("currency_amounts") else "pricing_mentioned" if pricing_patterns and any(p in lower for p in pricing_patterns) else "not_found",
        "missing_evidence": [
            label
            for label, values in {
                "audience": [pattern for pattern in audience_patterns if pattern in lower],
                "cta": find_phrases(text, cta_patterns),
                "pricing": find_phrases(text, pricing_patterns),
                "trust_proof": find_phrases(text, proof_patterns),
                "seo_content": find_phrases(text, content_patterns),
                "product_changes": find_phrases(text, product_change_patterns),
            }.items()
            if not values
        ],
        "marketing_notes": "Heuristic extraction from public page copy. Verify claims and add ad-library, SEO, and social evidence before drawing channel conclusions.",
    }
    if entity_meta:
        result["primary_lane"] = entity_meta.get("primary_lane", "uncertain")
        result["competitive_role"] = entity_meta.get("competitive_role", "unknown")
        result["inspiration_roles"] = entity_meta.get("inspiration_roles", [])
    else:
        result["primary_lane"] = "uncertain"
        result["competitive_role"] = "unknown"
        result["inspiration_roles"] = []
    result["capability_patterns"] = extract_capability_patterns(requested_capabilities(entity_meta), result, text)
    return result


# ---------------------------------------------------------------------------
# Content inventory (--content-inventory)
#
# What competitors and similar companies publish: topics, questions answered, formats and depth per page.
# Records topics and structure only and never reuses wording: no page body is stored, only headings, schema
# types, counts and a <=300-character excerpt per page. Supplier content shows what suppliers choose to publish,
# not what customers need. Only verified same-market competitors (entity_type `competitor`) can signal market
# coverage; similar companies and capability references are inspiration for format and structure only.
# Robots.txt is checked before any page is scraped; a site whose robots.txt cannot be read (network/5xx) is skipped.
# ---------------------------------------------------------------------------

EXCERPT_LIMIT = 300
LANE_TO_ENTITY_TYPE = {
    "competitive_market": "competitor", "market_competitor": "competitor", "competitor": "competitor",
    "similar_company": "similar_company", "cross_market_analog": "similar_company",
    "capability_reference": "capability_reference",
}
ENTITY_TYPES = ("competitor", "similar_company", "capability_reference")
ROBOTS_AGENT = "FirecrawlAgent"  # Firecrawl fetches the pages; groups for it fall back to `*`.
EXCLUDED_PATH = re.compile(
    r"(?:^|/)(?:impressum|imprint|legal|rechtliche[s-]?hinweise?|datenschutz\w*|privacy\w*|agb|terms\w*|nutzungsbedingungen|"
    r"cookie\w*|disclaimer|widerruf\w*|karriere|careers?|jobs?|stellenangebote|login|log-in|signin|sign-in|anmelden|"
    r"logout|register|registrierung|account|mein-konto|konto|my-account|profil|password\w*|passwort\w*|cart|warenkorb|"
    r"basket|checkout|kasse)(?:/|$|[.?#-])", re.IGNORECASE)
ASSET_SUFFIX = re.compile(r"\.(?:pdf|jpe?g|png|gif|svg|webp|zip|docx?|xlsx?|mp4|mp3|xml|json|css|js)$", re.IGNORECASE)
CONTENT_PATH = re.compile(
    r"ratgeber|guide|blog|magazin|wissen|lexikon|glossar|glossary|faq|fragen|hilfe|help|vergleich|compare|comparison|"
    r"\bvs\b|rechner|calculator|tarif|kosten|preis|pricing|checklist|checkliste|tipps|article|artikel|news|stadt|city|local",
    re.IGNORECASE)
QUESTION_START = re.compile(
    r"^(?:wie|was|wann|warum|wieso|weshalb|welche[rsmn]?|wer|wo|wohin|woher|wieviel|wie\s?viel|kann|können|muss|müssen|"
    r"darf|ist|sind|gibt|lohnt|brauche|braucht|soll|sollte|how|what|when|why|which|who|where|can|do|does|is|are|should|will)\b",
    re.IGNORECASE)
CTA_VERB = re.compile(r"jetzt|kostenlos|vergleich|berechn|angebot|beratung|termin|anfrag|abschlie|start|get|book|try|sign up|quote|demo|contact|kontakt", re.IGNORECASE)
DATE_TEXT = re.compile(
    r"(?:Stand|Aktualisiert(?: am)?|Zuletzt aktualisiert(?: am)?|Last updated|Updated(?: on)?)\s*[:\-]?\s*"
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}\.\s?\d{1,2}\.\s?\d{4}|\d{1,2}\.?\s+[A-Za-zäöüÄÖÜ]+\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},\s+\d{4})")
STOPWORDS = {"für", "fuer", "und", "oder", "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "mit", "von", "vom",
             "zum", "zur", "bei", "auf", "aus", "ist", "wie", "was", "the", "and", "for", "with", "what", "how", "best", "beste", "test"}
COVERAGE_HEURISTIC = {
    "match": "every meaningful query token (6-char stem) appears in the page topic, title, headings, questions or URL path",
    "covered_well": "a matched page with >=800 words, or >=400 words plus a format or >=3 answered questions",
    "covered_thin": "matched pages exist but none meets covered_well",
    "uncovered": "no inventoried page matched; sample limited by max_pages, so this is not proof of absence",
}
INVENTORY_CAVEATS = [
    "Supplier content shows what suppliers choose to publish, not what customers need.",
    "Only entity_type `competitor` (verified same-market) signals market coverage; similar companies and capability references are inspiration for format and structure only, never evidence that a topic matters in this market.",
    "A topic every competitor covers thinly is a quality-gap hypothesis; a topic nobody covers is a demand question to check against search and customer voice, not proof of opportunity.",
    "Topics and structure are recorded, never wording: no body text is stored and excerpts are capped at 300 characters.",
    "Coverage is a heuristic over a sample of at most max_pages per site; uncovered means not found in the sample.",
]


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def map_site(base_url: str, limit: int = 500) -> dict[str, Any]:
    _, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    if not api_key:
        return {"ok": False, "status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}
    return http_post(
        "https://api.firecrawl.dev/v1/map",
        headers={"Authorization": f"Bearer {api_key}"},
        data={"url": base_url, "limit": limit, "includeSubdomains": False},
        timeout=90,
    )


class LiveInventoryFetcher:
    """Firecrawl map/scrape via the analyzer's helpers; robots.txt and sitemap.xml by direct HTTP."""

    def __init__(self) -> None:
        self.firecrawl_calls = {"map": 0, "scrape": 0}
        self.credits_reported = 0

    def _count(self, kind: str, response: dict[str, Any]) -> None:
        self.firecrawl_calls[kind] += 1
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        used = (data.get("metadata") or {}).get("creditsUsed") if isinstance(data.get("metadata"), dict) else None
        if isinstance(used, (int, float)):
            self.credits_reported += used

    def robots(self, base: str) -> dict[str, Any]:
        response = http_get(base + "/robots.txt", timeout=20, max_bytes=512_000, max_text_chars=512_000)
        body = response.get("body")
        text = body.get("text") if isinstance(body, dict) else (body if isinstance(body, str) else None)
        return {"status_code": response.get("status_code"), "text": text if response.get("ok") else None}

    def map(self, base: str) -> list[str] | None:
        response = map_site(base)
        if response.get("status") == "missing_credentials":
            return None
        self._count("map", response)
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        return _map_links(body) if response.get("ok") else None

    def sitemap(self, url: str) -> str | None:
        response = http_get(url, timeout=30, max_bytes=8_000_000, max_text_chars=8_000_000)
        body = response.get("body")
        return body.get("text") if response.get("ok") and isinstance(body, dict) else None

    def scrape(self, url: str) -> dict[str, Any]:
        response = scrape_url(url, formats=["markdown", "rawHtml"])
        if response.get("status") != "missing_credentials":
            self._count("scrape", response)
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        return body if response.get("ok") else {"success": False, "error": response.get("error") or response.get("status")}


class FixtureInventoryFetcher:
    """Replay of recorded/synthetic robots, map, sitemap and scrape responses (tests and offline runs)."""

    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture
        self.firecrawl_calls = {"map": 0, "scrape": 0}
        self.credits_reported = 0

    def robots(self, base: str) -> dict[str, Any]:
        return self.fixture.get("robots", {}).get(base) or {"status_code": 404, "text": None}

    def map(self, base: str) -> list[str] | None:
        response = self.fixture.get("map", {}).get(base)
        return _map_links(response) if isinstance(response, dict) and response.get("success") else None

    def sitemap(self, url: str) -> str | None:
        return self.fixture.get("sitemaps", {}).get(url)

    def scrape(self, url: str) -> dict[str, Any]:
        return self.fixture.get("scrape", {}).get(url) or {"success": False, "error": "not_in_fixture"}


def _map_links(body: dict[str, Any]) -> list[str]:
    links = body.get("links") or []
    return [str(item.get("url") if isinstance(item, dict) else item) for item in links if item]


def _robots_parser(record: dict[str, Any]) -> RobotFileParser | None:
    """None means robots.txt could not be read (network/5xx): the site is skipped, not assumed open."""
    parser = RobotFileParser()
    status = record.get("status_code")
    if isinstance(status, int) and 400 <= status < 500:
        parser.parse([])  # no robots.txt: crawling allowed
        return parser
    if status != 200 or record.get("text") is None:
        return None
    parser.parse(str(record["text"]).splitlines())
    return parser


def _sitemap_urls(fetcher: Any, base: str, robots: RobotFileParser) -> list[str]:
    queue = list(robots.site_maps() or []) or [base + "/sitemap.xml"]
    urls: list[str] = []
    seen: set[str] = set()
    while queue and len(seen) < 4:
        sitemap_url = queue.pop(0)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        text = fetcher.sitemap(sitemap_url) or ""
        locs = [html_lib.unescape(value.strip()) for value in re.findall(r"(?is)<loc>(.*?)</loc>", text)]
        if re.search(r"(?is)<sitemapindex", text):
            queue.extend(locs)
        else:
            urls.extend(locs)
    return urls


def _content_priority(url: str) -> tuple[int, int]:
    path = urllib.parse.urlsplit(url).path
    return (0 if CONTENT_PATH.search(path) else 1 if path.strip("/") else 2, len(path))


def _select_urls(base: str, candidates: list[str], robots: RobotFileParser, max_pages: int,
                 focus_terms: list[str] | None = None) -> tuple[list[str], list[dict[str, str]], list[str]]:
    keep: list[str] = []
    excluded: list[dict[str, str]] = []
    disallowed: list[str] = []
    for url in dict.fromkeys(candidates):
        if domain_of(url) != domain_of(base):
            continue
        path = urllib.parse.urlsplit(url).path or "/"
        if ASSET_SUFFIX.search(path):
            excluded.append({"url": url, "reason": "asset"})
        elif EXCLUDED_PATH.search(path):
            excluded.append({"url": url, "reason": "legal_careers_account_or_cart"})
        elif not robots.can_fetch(ROBOTS_AGENT, url):
            disallowed.append(url)
        else:
            keep.append(url)
    focus = _stems(" ".join(focus_terms or []))
    keep.sort(key=lambda url: (-len(focus & _stems(urllib.parse.urlsplit(url).path.replace("-", " ").replace("/", " "))), *_content_priority(url)))
    return keep[:max_pages], excluded, disallowed


def _clean(value: str, limit: int) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_`#>]+", " ", value)
    return " ".join(value.split())[:limit]


def _json_ld_nodes(raw_html: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for block in re.findall(r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', raw_html or ""):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                nodes.append(node)
                stack.extend(value for key, value in node.items() if key in {"@graph", "mainEntity", "hasPart", "itemListElement"})
    return nodes


def _types(node: dict[str, Any]) -> list[str]:
    value = node.get("@type")
    return [str(v) for v in (value if isinstance(value, list) else [value]) if v]


def extract_questions(markdown: str, nodes: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Question-form H2/H3 headings plus FAQPage Question names; returns (questions, h2/h3 headings)."""
    headings = [_clean(h, 200) for h in re.findall(r"(?m)^#{2,3}\s+(.+?)\s*#*\s*$", markdown or "")]
    found = [h for h in headings if h.endswith("?") or QUESTION_START.match(h)]
    for node in nodes:
        if "Question" in _types(node) and node.get("name"):
            found.append(_clean(str(node["name"]), 200))
    questions: list[str] = []
    for q in found:
        if q and q.casefold() not in {x.casefold() for x in questions}:
            questions.append(q)
    return questions[:40], [h for h in headings if h][:40]


def detect_formats(url: str, markdown: str, raw_html: str, headings: list[str], schema_types: list[str]) -> list[str]:
    path = urllib.parse.urlsplit(url).path.lower()
    blob = " ".join([path, *headings, markdown[:4000] if markdown else ""]).lower()
    html_lower = (raw_html or "").lower()
    formats = []
    if re.search(r"rechner|calculator|berechnen sie|beitragsrechner", blob):
        formats.append("calculator")
    if re.search(r"(?m)^\s*\|.*\|.*\|.*\|\s*$", markdown or "") or re.search(r"<table\b", html_lower):
        formats.append("comparison_table")
    if re.search(r"<video\b|youtube\.com/embed|player\.vimeo|/embed/video", html_lower) or "VideoObject" in schema_types:
        formats.append("video")
    if re.search(r"checklist|checkliste", blob) or len(re.findall(r"(?m)^\s*[-*]\s+\[[ xX]\]", markdown or "")) >= 2:
        formats.append("checklist")
    if re.search(r"\btool\b|konfigurator|quiz|selbsttest|\bcheck\b", blob):
        formats.append("tool")
    return formats


def _last_updated(metadata: dict[str, Any], nodes: list[dict[str, Any]], markdown: str) -> str | None:
    for key in ("article:modified_time", "modifiedTime", "dateModified", "og:updated_time"):
        value = metadata.get(key)
        if value:
            return str(value[0] if isinstance(value, list) else value)[:40]
    for node in nodes:
        if node.get("dateModified"):
            return str(node["dateModified"])[:40]
    match = DATE_TEXT.search(markdown or "")
    return match.group(1) if match else None


def _primary_cta(markdown: str) -> str | None:
    for candidate in extract_button_like_ctas(markdown or ""):
        if CTA_VERB.search(candidate):
            return candidate[:120]
    return None


def inventory_page(url: str, body: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    data = body.get("data") if isinstance(body.get("data"), dict) else body
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    markdown = str(data.get("markdown") or "")
    raw_html = str(data.get("rawHtml") or data.get("html") or "")
    nodes = _json_ld_nodes(raw_html)
    schema_types = sorted({t for node in nodes for t in _types(node)} - {"Question", "Answer"})
    questions, headings = extract_questions(markdown, nodes)
    h1 = re.search(r"(?m)^#\s+(.+?)\s*$", markdown)
    title = _clean(str(metadata.get("title") or ""), 200)
    topic = _clean(h1.group(1), 200) if h1 else title
    paragraphs = [p for p in re.split(r"\n\s*\n", markdown) if p.strip() and not p.lstrip().startswith(("#", "|", "-", "*", "["))]
    excerpt = _clean(str(metadata.get("description") or "") or (paragraphs[0] if paragraphs else ""), EXCERPT_LIMIT)
    page_type = classify_page_type(url, title, markdown[:2000])
    path = urllib.parse.urlsplit(url).path.lower()
    if re.search(r"faq|fragen", path) or "FAQPage" in schema_types:
        page_type = "faq"
    elif re.search(r"glossar|lexikon|glossary", path):
        page_type = "glossary"
    elif re.search(r"rechner|calculator", path):
        page_type = "calculator"
    elif re.search(r"vergleich|compare|comparison|\bvs\b", path):
        page_type = "comparison"
    return {
        "url": url,
        "page_type": page_type,
        "topic": topic or title or url,
        "title": title,
        "headings": headings,
        "questions_answered": questions,
        "formats": detect_formats(url, markdown, raw_html, headings, schema_types),
        "word_count": len(re.findall(r"\w+", _clean(markdown, 10**7))),
        "schema_types": schema_types,
        "primary_cta": _primary_cta(markdown),
        "last_updated": _last_updated(metadata, nodes, markdown),
        "excerpt": excerpt,
        "retrieved_at": retrieved_at,
    }


def inventory_site(base_url: str, lane: str, max_pages: int = 25, *, entity: str = "", fetcher: Any = None,
                   focus_terms: list[str] | None = None) -> dict[str, Any]:
    """Inventory one site's content pages (see the section comment for what is and is not recorded).

    `focus_terms` (the clusters' queries) rank URLs whose path shares terms with them first, so a small
    `max_pages` sample of a large site is spent on relevant pages; content-type paths come next.
    """
    entity_type = LANE_TO_ENTITY_TYPE.get(lane)
    if not entity_type:
        raise ValueError(f"lane {lane!r} is not an inventory lane")
    fetcher = fetcher or LiveInventoryFetcher()
    base = normalize_base_url(base_url)
    site: dict[str, Any] = {
        "entity": entity or domain_of(base), "entity_type": entity_type, "lane": lane, "base_url": base,
        "max_pages": max_pages, "discovery": None, "pages": [], "excluded": [], "robots_disallowed": [],
        "failures": [], "gaps": [],
    }
    robots = _robots_parser(fetcher.robots(base))
    if robots is None:
        site["gaps"].append("robots.txt could not be read; site skipped rather than assumed open.")
        return site
    links = fetcher.map(base)
    site["discovery"] = "firecrawl_map" if links else "sitemap"
    if not links:
        links = _sitemap_urls(fetcher, base, robots)
        if not links:
            site["discovery"] = "homepage_only"
            links = [base + "/"]
    selected, site["excluded"], site["robots_disallowed"] = _select_urls(base, links, robots, max_pages, focus_terms)
    for url in selected:
        body = fetcher.scrape(url)
        if not body.get("success", True) or not isinstance(body.get("data", body), dict):
            site["failures"].append({"url": url, "error": str(body.get("error", "scrape_failed"))[:200]})
            continue
        site["pages"].append(inventory_page(url, body, now_iso()))
    if site["failures"]:
        site["gaps"].append(f"{len(site['failures'])} page(s) failed to scrape.")
    return site


def _stems(text: str) -> set[str]:
    return {t[:6] for t in re.findall(r"\w+", text.casefold()) if len(t) >= 3 and t not in STOPWORDS}


def _cluster_terms(cluster: dict[str, Any]) -> list[str]:
    return [str(q.get("query") if isinstance(q, dict) else q) for q in cluster.get("queries", []) if q]


def _page_matches(page: dict[str, Any], terms: list[str]) -> bool:
    path = urllib.parse.urlsplit(page["url"]).path.replace("-", " ").replace("/", " ")
    tokens = _stems(" ".join([page.get("topic", ""), page.get("title", ""), path, *page.get("headings", []), *page.get("questions_answered", [])]))
    return any((stems := _stems(term)) and stems <= tokens for term in terms)


def _depth(page: dict[str, Any]) -> str:
    words = page.get("word_count", 0)
    if words >= 800 or (words >= 400 and (page.get("formats") or len(page.get("questions_answered", [])) >= 3)):
        return "covered_well"
    return "covered_thin"


def _bind(out_dir: Path, rel: str, data: Any) -> dict[str, str]:
    raw = (json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    target = out_dir / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {"path": rel, "sha256": sha256_hex(raw)}


def coverage_matrix(inventories: list[dict[str, Any]], clusters: list[dict[str, Any]], *, out_dir: Path | str) -> dict[str, Any]:
    """Per content-opportunity cluster and entity: covered_well | covered_thin | uncovered, with bound page refs.

    Refs are `{path, sha256}` bindings relative to `out_dir` (the directory of competitor-content.json): each
    covering page is written to `inventory/<entity>/pNN.json`, each site to `inventory/<entity>/index.json`
    (cited by uncovered rows as the sample that was checked). Only `competitor` rows set
    `market_competitor_coverage`; analog rows appear under `inspiration` only.
    """
    out_dir = Path(out_dir)
    rows: list[dict[str, Any]] = []
    page_refs: dict[tuple[str, str], dict[str, str]] = {}
    index_refs: dict[str, dict[str, str]] = {}
    for site in inventories:
        slug = slugify(site["entity"])
        for n, page in enumerate(site["pages"], start=1):
            page_refs[(site["entity"], page["url"])] = _bind(out_dir, f"inventory/{slug}/p{n:02d}.json", {"entity": site["entity"], "entity_type": site["entity_type"], **page})
        index_refs[site["entity"]] = _bind(out_dir, f"inventory/{slug}/index.json", {k: v for k, v in site.items() if k != "pages"} | {"page_urls": [p["url"] for p in site["pages"]]})
    summaries: list[dict[str, Any]] = []
    for cluster in clusters:
        cid = str(cluster.get("cluster_id") or "").strip() or None
        terms = _cluster_terms(cluster) or ([cid] if cid else [])
        topic = terms[0] if terms else (cid or "topic")
        by_type: dict[str, list[str]] = {t: [] for t in ENTITY_TYPES}
        inspiration: list[dict[str, Any]] = []
        for site in inventories:
            matched = [p for p in site["pages"] if _page_matches(p, terms)]
            coverage = "uncovered" if not matched else ("covered_well" if any(_depth(p) == "covered_well" for p in matched) else "covered_thin")
            refs = [page_refs[(site["entity"], p["url"])] for p in matched] or [index_refs[site["entity"]]]
            questions = list(dict.fromkeys(q for p in matched for q in p["questions_answered"]))
            rows.append({"topic": topic, "cluster_id": cid, "questions": questions, "refs": refs,
                         "entity": site["entity"], "entity_type": site["entity_type"], "coverage": coverage})
            by_type[site["entity_type"]].append(coverage)
            if site["entity_type"] != "competitor" and matched:
                inspiration.append({"entity": site["entity"], "entity_type": site["entity_type"], "coverage": coverage,
                                    "formats": sorted({f for p in matched for f in p["formats"]}),
                                    "page_types": sorted({p["page_type"] for p in matched})})
        competitor = by_type["competitor"]
        if not competitor:
            interpretation = "no_market_competitor_inventoried"
        elif "covered_well" in competitor:
            interpretation = "covered_by_market_competitors"
        elif "covered_thin" in competitor:
            interpretation = "quality_gap_hypothesis"
        else:
            interpretation = "demand_question"
        summaries.append({"cluster_id": cid, "topic": topic,
                          "by_entity_type": {t: {"entities": len(v), "covered_well": v.count("covered_well"), "covered_thin": v.count("covered_thin"), "uncovered": v.count("uncovered")} for t, v in by_type.items()},
                          "market_competitor_coverage": any(c != "uncovered" for c in competitor),
                          "interpretation": interpretation, "inspiration": inspiration})
    return {"schema_version": 1, "generated_at": now_iso(), "caveats": INVENTORY_CAVEATS, "heuristics": COVERAGE_HEURISTIC,
            "rows": rows, "cluster_summary": summaries}


INTERPRETATION_TEXT = {
    "covered_by_market_competitors": "covered by at least one market competitor",
    "quality_gap_hypothesis": "market competitors cover it only thinly: quality-gap hypothesis",
    "demand_question": "no market competitor covers it: demand question for search and customer voice, not proof of opportunity",
    "no_market_competitor_inventoried": "no market competitor inventoried: no market signal",
}


def render_content_inventory(result: dict[str, Any], inventories: list[dict[str, Any]], skipped: list[dict[str, str]], fetcher: Any) -> str:
    lines = ["# Competitor and similar-company content inventory", "", "## Read this first", ""]
    lines += [f"- {c}" for c in result["caveats"]]
    lines += ["", "## Sites", "", "| Entity | Type | Discovery | Pages | Excluded | Robots-disallowed | Failures |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for s in inventories:
        lines.append(f"| {s['entity']} | {s['entity_type']} | {s['discovery'] or 'skipped'} | {len(s['pages'])} | {len(s['excluded'])} | {len(s['robots_disallowed'])} | {len(s['failures'])} |")
    for item in skipped:
        lines.append(f"| {item['entity']} | not inventoried | {item['reason']} | 0 | - | - | - |")
    lines += ["", f"Firecrawl calls: map {fetcher.firecrawl_calls['map']}, scrape {fetcher.firecrawl_calls['scrape']} (credits reported by responses: {fetcher.credits_reported or 'not reported'}).",
              "", "## Coverage by cluster", "", "| Cluster | Competitors (well/thin/none) | Similar companies | Capability refs | Reading |", "| --- | --- | --- | --- | --- |"]
    for s in result["cluster_summary"]:
        cell = lambda t: "{covered_well}/{covered_thin}/{uncovered}".format(**s["by_entity_type"][t])  # noqa: E731
        lines.append(f"| {s['cluster_id'] or s['topic']} | {cell('competitor')} | {cell('similar_company')} | {cell('capability_reference')} | {INTERPRETATION_TEXT[s['interpretation']]} |")
    lines += ["", "## Pages", ""]
    for s in inventories:
        lines.append(f"### {s['entity']} ({s['entity_type']})")
        for p in s["pages"]:
            lines.append(f"- {p['url']} | {p['page_type']} | {p['word_count']} words | questions {len(p['questions_answered'])} | formats {', '.join(p['formats']) or '-'} | schema {', '.join(p['schema_types']) or '-'} | updated {p['last_updated'] or '-'}")
        for gap in s["gaps"]:
            lines.append(f"- Gap: {gap}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main_content_inventory(args: argparse.Namespace) -> int:
    out_dir = Path(args.out or args.out_dir or "")
    if not args.landscape or not args.clusters or not str(out_dir).strip(". "):
        print("--content-inventory needs --landscape, --clusters and --out", file=sys.stderr)
        return 2
    landscape = json.loads(Path(args.landscape).read_text(encoding="utf-8"))
    clusters_doc = json.loads(Path(args.clusters).read_text(encoding="utf-8"))
    clusters = clusters_doc.get("rows", []) if isinstance(clusters_doc, dict) else clusters_doc
    fetcher: Any = FixtureInventoryFetcher(json.loads(Path(args.fixture_inventory_json).read_text(encoding="utf-8"))) if args.fixture_inventory_json else LiveInventoryFetcher()
    inventories: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for entity in (landscape.get("entities", []) if isinstance(landscape, dict) else landscape)[: args.limit]:
        name = str(entity.get("name") or domain_of(str(entity.get("url", ""))))
        lane = str(entity.get("primary_lane") or entity.get("lane") or "")
        if lane not in LANE_TO_ENTITY_TYPE or entity.get("verification_status", "verified") != "verified" or not entity.get("url"):
            skipped.append({"entity": name, "reason": f"lane {lane or 'missing'} / {entity.get('verification_status', 'unknown')}: not inventoried"})
            continue
        inventories.append(inventory_site(str(entity["url"]), lane, args.max_pages, entity=name, fetcher=fetcher,
                                          focus_terms=[t for c in clusters for t in _cluster_terms(c)]))
    result = coverage_matrix(inventories, clusters, out_dir=out_dir)
    result["firecrawl_calls"] = dict(fetcher.firecrawl_calls)
    result["skipped_entities"] = skipped
    write_json(out_dir / "competitor-content.json", result)
    (out_dir / "competitor-content.md").write_text(render_content_inventory(result, inventories, skipped, fetcher), encoding="utf-8")
    print(json.dumps({"out": str(out_dir), "sites": len(inventories), "pages": sum(len(s["pages"]) for s in inventories),
                      "rows": len(result["rows"]), "skipped_entities": len(skipped), "firecrawl_calls": fetcher.firecrawl_calls,
                      "credits_reported": fetcher.credits_reported}, indent=2))
    return 0 if inventories else 1


def write_marketing_plan(run_dir: Path, args: argparse.Namespace, urls: list[str]) -> None:
    source_note = f"competitors.json at `{args.competitors_json}`" if args.competitors_json else f"{len(urls)} URL argument(s)"
    lines = [
        "# Competitor Marketing Analysis Plan",
        "",
        "## Objective",
        "",
        f"Extract positioning, CTAs, pricing posture, and channel signals for `{args.topic or 'competitors'}` without treating competitor claims as performance proof.",
        "",
        "## Scope",
        "",
        f"- Topic: `{args.topic or '[from competitors.json]'}`",
        f"- Competitor source: {source_note}",
        f"- Competitor limit: `{args.limit}`",
        f"- Deep scrape mode: `{args.deep}` (pricing/features/customers/blog/docs/changelog pages cost more credits)",
        "",
        "## Questions This Run Can Explore",
        "",
        "- What promise, audience, and enemy does each competitor's copy claim?",
        "- Which CTAs and pricing posture do they present, and what does that imply about their funnel?",
        "- Which claims are verifiable proof and which are marketing assertion?",
        "- Where do competitor messages agree (category table stakes) vs. diverge (positioning angles)?",
        "",
        "## Limits",
        "",
        "- Competitor pages state what competitors want believed; they are positioning evidence, not demand or performance evidence.",
        "- Scrape failures and fallbacks reduce coverage and must be disclosed in the report.",
        "- Detected audiences, CTAs, and pricing signals are heuristic extractions; verify material claims on the live page.",
        "",
        "## Required User Checkpoint",
        "",
        "After the run, compare ad messaging with landing-page positioning, then ask one question: `Which positioning angle or proof gap should we test against these competitors first?`",
    ]
    plan_path = run_dir / "marketing_plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(run_dir: Path, args: argparse.Namespace, analyses: list[dict[str, Any]], provider_status: dict[str, Any]) -> None:
    needs_attention = provider_status.get("needs_user_attention") or []
    lines = [
        "# Competitor Marketing Analysis",
        "",
        f"- Topic: {args.topic}",
        f"- Competitors analyzed: {len(analyses)}",
        f"- Deep mode: {args.deep}",
        "",
        "## Provider Status",
        "",
        f"- firecrawl: {provider_status.get('status')}",
        f"- fallback_used: {provider_status.get('fallback_used', False)}",
        "",
        "## Competitor Positioning",
        "",
    ]
    for item in analyses:
        lines.append(f"### {item['domain']}")
        lines.append(f"- Lane: {item.get('primary_lane', 'uncertain')} | competitive role: {item.get('competitive_role', 'unknown')}")
        lines.append(f"- URL: {item['url']}")
        lines.append(f"- Page type: {item.get('page_type', 'unknown')}")
        lines.append(f"- Source pages: {len(item.get('source_pages', []))}")
        lines.append(f"- Headline/title: {item['positioning_headline']}")
        lines.append(f"- Audiences detected: {', '.join(item['detected_audiences']) or 'unclear'}")
        lines.append(f"- CTAs: {json.dumps(item['cta_language'][:3], ensure_ascii=False)}")
        lines.append(f"- Button-like CTAs: {json.dumps(item.get('button_like_ctas', [])[:3], ensure_ascii=False)}")
        lines.append(f"- Pricing posture: {item.get('pricing_posture', 'not_found')}")
        lines.append(f"- Pricing signals: {json.dumps(item['pricing_language'][:3], ensure_ascii=False)}")
        lines.append(f"- Structured price tokens: {json.dumps(item.get('structured_price_tokens', {}), ensure_ascii=False)}")
        lines.append(f"- Normalized price tokens: {json.dumps(item.get('normalized_price_tokens', {}), ensure_ascii=False)}")
        lines.append(f"- Trust/proof signals: {json.dumps(item['trust_proof_language'][:3], ensure_ascii=False)}")
        lines.append(f"- SEO/content clues: {json.dumps(item.get('seo_content_clues', [])[:3], ensure_ascii=False)}")
        lines.append(f"- Product-change clues: {json.dumps(item.get('product_change_clues', [])[:3], ensure_ascii=False)}")
        lines.append(f"- Distribution clues: {json.dumps(item.get('distribution_clues', [])[:3], ensure_ascii=False)}")
        lines.append(f"- Missing evidence: {', '.join(item.get('missing_evidence', [])) or 'none'}")
        lines.append("")
    if needs_attention:
        lines.extend(["## Provider Alerts", ""])
        for item in needs_attention:
            lines.append(f"- {item}")
        if any("billing_required" in item for item in needs_attention):
            lines.append("- Firecrawl returned billing_required, so full landing-page scraping was not performed for affected pages. Results may rely on direct HTTP fallback or cached competitor snippets.")
        lines.append("")
    lines.extend(
        [
            "## Analyst Warnings",
            "",
            "- This is copy and positioning analysis, not proof of performance.",
            "- To assess channel strategy, add ad-library, social, SEO, and email/funnel evidence.",
            "- Compare competitor promises against user pain evidence before copying their category language.",
        ]
    )
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze public competitor marketing pages.")
    parser.add_argument("--topic", default="")
    parser.add_argument("--competitor-url", action="append", default=[], help="Competitor homepage or landing page URL. Repeatable.")
    parser.add_argument("--competitors-json", default="", help="Path to competitors.json from discover_competitors.py.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--deep", action="store_true", help="Scrape common pricing, features, customers, blog, docs, and changelog paths for each competitor. Costs more credits.")
    parser.add_argument("--lane", choices=["all", "competitive_market", "similar_company", "capability_reference"], default="all", help="Analyze only entities in one lane when using --competitors-json.")
    parser.add_argument("--fixture-pages-json", default="", help="Offline first-party page replay fixture keyed by entity URL.")
    parser.add_argument("--case", default="", help="Registered case ID within --workspace.")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--workspace", default="", help="Project workspace path. Defaults to projects/<project-slug>.")
    parser.add_argument("--content-inventory", action="store_true", help="Inventory content topics, questions, formats and depth of entities from --landscape against --clusters; writes competitor-content.json/.md to --out.")
    parser.add_argument("--landscape", default="", help="entity-landscape.json (content-inventory mode).")
    parser.add_argument("--clusters", default="", help="content-opportunities.json whose rows are the clusters (content-inventory mode).")
    parser.add_argument("--out", default="", help="Output directory (content-inventory mode).")
    parser.add_argument("--max-pages", type=int, default=25, help="Pages scraped per site (content-inventory mode).")
    parser.add_argument("--fixture-inventory-json", default="", help="Offline robots/map/sitemap/scrape replay (content-inventory mode).")
    parser.add_argument("--legacy-output", action="store_true", help="Removed: the projects/research/evidence-scout layout is gone (now projects/_archive, read-only). Use --out-dir for an explicit path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.content_inventory:
        return main_content_inventory(args)
    urls = list(args.competitor_url)
    competitor_items: dict[str, dict[str, Any]] = {}
    if args.competitors_json:
        data = json.loads(Path(args.competitors_json).read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
        priority = {
            "direct_broker_candidate": 0,
            "direct_insurer_candidate": 1,
            "marketplace_comparison_portal": 2,
            "indirect_broker_candidate": 3,
            "indirect_insurer_candidate": 4,
            "lead_gen_affiliate": 5,
            "editorial_resource": 6,
            "known_competitor_unverified": 7,
        }
        items = sorted(items, key=lambda item: priority.get(item.get("competitor_type_hint", ""), 9) if isinstance(item, dict) else 9)
        for item in items:
            if not isinstance(item, dict):
                continue
            observed_lanes = item.get("lane_observations", [])
            if args.lane != "all" and item.get("primary_lane", "") != args.lane and args.lane not in observed_lanes:
                continue
            url = item.get("url", "")
            if url:
                urls.append(url)
                competitor_items[url] = item
    urls = [url for url in dict.fromkeys(urls) if url][: args.limit]
    effective_topic = args.topic or "competitors"
    run_dir, workspace = resolve_run_dir(
        topic=effective_topic,
        workspace_arg=args.workspace,
        case_id=getattr(args, "case", ""),
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="market_research/solution_alternatives/marketing",
        legacy_subdir="marketing",
    )
    if workspace:
        update_stage(workspace, "competitor_marketing", run_dir=run_dir, status="in_progress", gate_result="not_run", next_action="Extract positioning claims without treating them as performance proof.")
    write_marketing_plan(run_dir, args, urls)

    raw: dict[str, Any] = {"scrapes": []}
    analyses: list[dict[str, Any]] = []
    provider_status = {"status": "not_run", "needs_user_attention": [], "fallback_used": False}
    fixture_pages = json.loads(Path(args.fixture_pages_json).read_text(encoding="utf-8")) if args.fixture_pages_json else None
    for url in urls:
        page_responses: list[dict[str, Any]] = []
        if fixture_pages is not None:
            for page in fixture_pages.get(url, []):
                if isinstance(page, dict):
                    page_responses.append({**page, "retrieval_source": str(page.get("retrieval_source", "fixture_official"))})
            provider_status["status"] = "ok" if page_responses else "fixture_missing"
        else:
            for page_url in (deep_urls(url) if args.deep else [url]):
                response = scrape_url(page_url)
                raw["scrapes"].append({"url": page_url, "response": response})
                status = response.get("status") or status_from_response(response)
                provider_status["status"] = status
                provider_status["http_status"] = response.get("status_code")
                if response.get("ok"):
                    page_responses.append({"url": page_url, "body": response.get("body") or {}, "retrieval_source": "firecrawl"})
                elif status not in {"not_run", "ok"}:
                    provider_status["needs_user_attention"].append(f"firecrawl failed for {page_url}: {status}")
                    fallback_response = direct_fetch_url(page_url)
                    raw.setdefault("direct_fetch_fallbacks", []).append({"url": page_url, "response": fallback_response})
                    if fallback_response.get("ok"):
                        provider_status["fallback_used"] = True
                        page_responses.append({"url": page_url, "body": fallback_response.get("body") or {}, "fallback_source": "direct_http", "retrieval_source": "direct_http"})
                    elif page_url == url and url in competitor_items:
                        cached = cached_competitor_page(competitor_items[url])
                        if ((cached.get("body") or {}).get("data") or {}).get("markdown"):
                            provider_status["fallback_used"] = True
                            page_responses.append(cached)
                            provider_status["needs_user_attention"].append(f"used cached competitor snippet fallback for {page_url}")
        if page_responses:
            analyses.append(analyze_text(url, page_responses, competitor_items.get(url)))

    summary = {
        "run_dir": str(run_dir),
        "topic": args.topic,
        "competitor_count": len(analyses),
        "provider": provider_status,
        "needs_user_attention": provider_status.get("needs_user_attention", []),
        "outputs": {
            "analysis_json": str(run_dir / "marketing_analysis.json"),
            "report": str(run_dir / "report.md"),
            "marketing_plan": str(run_dir / "marketing_plan.md"),
            "raw": str(run_dir / "raw.json"),
        },
    }
    write_json(run_dir / "raw.json", redact_sensitive(raw))
    write_json(run_dir / "marketing_analysis.json", analyses)
    write_json(run_dir / "summary.json", summary)
    write_report(run_dir, args, analyses, provider_status)
    if workspace:
        provider_failure = []
        if provider_status.get("status") not in {"ok", "not_run"}:
            provider_failure.append({"provider": "firecrawl", "failure_class": str(provider_status.get("status")), "confidence_impact": "high"})
        gate_result = "fail" if not analyses else ("conditional_pass" if provider_failure or provider_status.get("fallback_used") else "pass")
        update_stage(
            workspace,
            "competitor_marketing", run_dir=run_dir,
            status="failed" if gate_result == "fail" else "passed",
            gate_result=gate_result,
            artifacts=[run_dir / "marketing_analysis.json", run_dir / "summary.json", run_dir / "report.md", run_dir / "marketing_plan.md"],
            provider_failures=provider_failure,
            next_action="Compare competitor promises with customer evidence before selecting positioning.",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if analyses else 1


if __name__ == "__main__":
    raise SystemExit(main())
