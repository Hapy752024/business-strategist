#!/usr/bin/env python3
"""Analyze competitor marketing from public web pages."""

from __future__ import annotations

import argparse
import json
import re
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


def scrape_url(url: str) -> dict[str, Any]:
    _, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    if not api_key:
        return {"ok": False, "status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}
    return http_post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {api_key}"},
        data={"url": url, "formats": ["markdown"], "onlyMainContent": True},
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
            source_pages.append({"url": page_url, "title": page_metadata.get("title", "")})
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


def analyze_text(url: str, page_bodies: list[dict[str, Any]]) -> dict[str, Any]:
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
    return {
        "url": url,
        "domain": domain_of(url),
        "retrieved_at": now_iso(),
        "source_pages": source_pages,
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "page_type": classify_page_type(url, metadata.get("title", ""), text),
        "positioning_headline": (metadata.get("title") or text[:160]).strip(),
        "detected_audiences": [pattern for pattern in audience_patterns if pattern in lower],
        "pain_language": find_phrases(text, pain_patterns),
        "cta_language": find_phrases(text, cta_patterns),
        "button_like_ctas": extract_button_like_ctas(text),
        "pricing_posture": classify_pricing_posture(text),
        "pricing_language": find_phrases(text, pricing_patterns),
        "structured_price_tokens": price_tokens,
        "normalized_price_tokens": normalize_price_tokens(price_tokens),
        "trust_proof_language": find_phrases(text, proof_patterns),
        "feature_language": find_phrases(text, ["automate", "collaborate", "track", "manage", "integrate", "workflow", "dashboard", "report"]),
        "seo_content_clues": find_phrases(text, content_patterns),
        "product_change_clues": find_phrases(text, product_change_patterns),
        "distribution_clues": find_phrases(text, distribution_patterns),
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze public competitor marketing pages.")
    parser.add_argument("--topic", default="")
    parser.add_argument("--competitor-url", action="append", default=[], help="Competitor homepage or landing page URL. Repeatable.")
    parser.add_argument("--competitors-json", default="", help="Path to competitors.json from discover_competitors.py.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--deep", action="store_true", help="Scrape common pricing, features, customers, blog, docs, and changelog paths for each competitor. Costs more credits.")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--workspace", default="", help="Topic workspace path. Defaults to research/topics/<topic-slug>.")
    parser.add_argument("--legacy-output", action="store_true", help="Write to the former research/evidence-scout/marketing layout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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
            url = item.get("url", "")
            if url:
                urls.append(url)
                competitor_items[url] = item
    urls = [url for url in dict.fromkeys(urls) if url][: args.limit]
    effective_topic = args.topic or "competitors"
    run_dir, workspace = resolve_run_dir(
        topic=effective_topic,
        workspace_arg=args.workspace,
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="competitors/marketing",
        legacy_subdir="marketing",
    )
    if workspace:
        update_stage(workspace, "competitor_marketing", status="in_progress", gate_result="not_run", next_action="Extract positioning claims without treating them as performance proof.")
    write_marketing_plan(run_dir, args, urls)

    raw: dict[str, Any] = {"scrapes": []}
    analyses: list[dict[str, Any]] = []
    provider_status = {"status": "not_run", "needs_user_attention": [], "fallback_used": False}
    for url in urls:
        page_responses: list[dict[str, Any]] = []
        for page_url in (deep_urls(url) if args.deep else [url]):
            response = scrape_url(page_url)
            raw["scrapes"].append({"url": page_url, "response": response})
            status = response.get("status") or status_from_response(response)
            provider_status["status"] = status
            provider_status["http_status"] = response.get("status_code")
            if response.get("ok"):
                page_responses.append({"url": page_url, "body": response.get("body") or {}})
            elif status not in {"not_run", "ok"}:
                provider_status["needs_user_attention"].append(f"firecrawl failed for {page_url}: {status}")
                fallback_response = direct_fetch_url(page_url)
                raw.setdefault("direct_fetch_fallbacks", []).append({"url": page_url, "response": fallback_response})
                if fallback_response.get("ok"):
                    provider_status["fallback_used"] = True
                    page_responses.append({"url": page_url, "body": fallback_response.get("body") or {}, "fallback_source": "direct_http"})
                elif page_url == url and url in competitor_items:
                    cached = cached_competitor_page(competitor_items[url])
                    if ((cached.get("body") or {}).get("data") or {}).get("markdown"):
                        provider_status["fallback_used"] = True
                        page_responses.append(cached)
                        provider_status["needs_user_attention"].append(f"used cached competitor snippet fallback for {page_url}")
        if page_responses:
            analyses.append(analyze_text(url, page_responses))

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
            "competitor_marketing",
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
