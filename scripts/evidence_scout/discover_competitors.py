#!/usr/bin/env python3
"""Discover potential competitors for a business idea."""

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
REGISTRY_DIR = Path(__file__).resolve().parent / "registries"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import get_secret, http_get, http_post, now_iso, redact_sensitive, status_from_response, with_query  # noqa: E402
from workspace import resolve_run_dir, update_stage  # noqa: E402


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in safe.split("-") if part)[:80] or "competitors"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def domain_of(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host.lower()


def likely_name(title: str, domain: str) -> str:
    if title:
        for sep in ["|", "-", ":", " - "]:
            if sep in title:
                title = title.split(sep)[0]
                break
        cleaned = " ".join(title.split())
        if cleaned:
            return cleaned[:80]
    return domain.split(".")[0].replace("-", " ").title()


def brand_from_domain(domain: str) -> str:
    return domain.split(".")[0].replace("-", " ").title()


def known_competitor_terms(known: str) -> list[str]:
    return [item.strip() for item in known.split(",") if item.strip()]


KNOWN_COMPETITOR_REGISTRY = read_json(REGISTRY_DIR / "known_competitors.json", {})
CANONICAL_KNOWN_URLS = KNOWN_COMPETITOR_REGISTRY.get("canonical_urls", {})
NOISY_LOOKUP_MARKERS = KNOWN_COMPETITOR_REGISTRY.get("noisy_lookup_markers", [])


def page_type_hint(url: str, business_model: str) -> str:
    path = urllib.parse.urlsplit(url).path.lower()
    if any(part in path for part in ["blog", "/resources", "/guide", "ratgeber", "wissen"]):
        return "blog_or_resource_page"
    if any(part in path for part in ["vergleich", "comparison", "private-krankenversicherung", "privatekrankenversicherung", "private-health-insurance", "berufsun"]):
        return "product_or_comparison_page"
    if business_model == "insurance_app":
        return "adjacent_app_homepage"
    return "product_or_homepage_candidate"


def canonical_known_url(name: str, domain: str = "") -> str:
    lowered = name.lower().replace(" ", "")
    for key, url in CANONICAL_KNOWN_URLS.items():
        if key in lowered or key in domain.lower().replace("-", "").replace(".", ""):
            return url
    return ""


def segment_modifiers(segment: str) -> list[str]:
    lowered = segment.lower()
    modifiers: list[str] = []
    candidates = [
        ("expat", "expats"),
        ("english-speaking", "English speaking"),
        ("english speaking", "English speaking"),
        ("self-employed", "self employed"),
        ("freelancer", "freelancers"),
        ("founder", "founders"),
        ("manager", "managers"),
        ("tech", "tech professionals"),
        ("germany", "Germany"),
    ]
    for needle, phrase in candidates:
        if needle in lowered and phrase not in modifiers:
            modifiers.append(phrase)
    return modifiers[:4]


def query_plan(topic: str, segment: str, known: str) -> list[str]:
    modifiers = segment_modifiers(segment)
    segment_scope = " ".join(modifiers)
    scoped = f"{topic} {segment_scope}".strip()
    queries = [
        f"{scoped} software",
        f"{scoped} tools",
        f"{scoped} competitors",
        f"{topic} alternatives",
        f"{topic} vs",
        f"best {topic} for {segment}",
        f"{topic} reviews pricing",
        f"{topic} comparison",
        f"{topic} marketplace",
        f"{segment} {topic} spreadsheet template",
        f"{segment} {topic} agency service",
        f"{segment} manual workflow {topic}",
    ]
    for competitor in known_competitor_terms(known):
        queries.append(f"{competitor} alternatives")
        queries.append(f"{competitor} competitors")
        queries.append(f"{competitor} pricing reviews")
    return queries


def classify_business_model(domain: str, url: str, text: str) -> str:
    lead_gen_markers = ["we connect you", "get connected", "recommended broker", "affiliate", "partner link", "lead", "quote request"]
    editorial_markers = ["guide", "blog", "article", "news", "tips", "how to", "resources", "explained", "best ", "top 10", "list of"]
    marketplace_markers = ["comparison portal", "compare quotes", "vergleichsportal", "reviews", "ratings", "marketplace", "directory"]
    broker_markers = ["broker", "makler", "insurance intermediary", "versicherungsmakler", "advisor", "adviser"]
    insurer_markers = ["insurer", "insurance company", "private health insurance provider", "carrier", "underwriter"]
    app_markers = ["app", "digital insurance", "insurtech", "platform", "online signup", "policy management"]
    own_service_markers = [
        "we're independent brokers",
        "we are independent brokers",
        "we work for you",
        "our company specializes",
        "our advisors",
        "our experts",
        "free quote",
        "get your free",
        "get insured",
        "calculate your personal offer",
        "take out your insurance directly online",
        "our digital private health insurance",
        "ihr versicherungsmakler",
        "wir vergleichen",
    ]
    known_marketplaces = ["check24.de", "verivox.de", "germanpedia.com"]
    known_insurers = ["ottonova.de", "allianz.de", "axa.de", "debeka.de", "dkv.de", "signal-iduna.de", "hallesche.de", "hansemerkur.de", "barmenia.de"]
    known_brokers = ["clark.de", "feather-insurance.com", "getsafe.de", "getsafe.com", "hellogetsafe.com", "stayinsured.de", "myhealthcarebroker.com", "klforexpats.com", "german-insurance-broker.de", "versicherungsbuero-weiss.com"]
    known_editorial = ["how-to-germany.com", "germany-visa.org", "strategyand.pwc.com", "qonto.com", "settle-in-berlin.com", "iamexpat.de", "insurancy.de"]

    path = urllib.parse.urlsplit(url).path.lower()
    if domain in known_editorial:
        return "editorial_resource"
    if domain in known_marketplaces:
        return "marketplace_comparison_portal"
    if domain in known_insurers:
        return "insurer"
    if domain == "hellogetsafe.com" and not any(marker in text for marker in ["pkv", "private health", "private krankenversicherung", "berufsun"]):
        return "insurance_app"
    if domain in known_brokers and not any(part in path for part in ["/blog", "/guide", "/resources", "/article"]):
        return "broker"
    if any(marker in text for marker in lead_gen_markers):
        return "lead_gen_affiliate"
    if any(marker in text for marker in marketplace_markers) or any(marker in domain for marker in ["check24", "verivox"]):
        return "marketplace_comparison_portal"
    has_own_service = any(marker in text for marker in own_service_markers)
    has_editorial_shape = domain in known_editorial or any(marker in text for marker in editorial_markers) or any(part in path for part in ["/blog", "/guide", "/resources", "/article"])
    if has_editorial_shape and not has_own_service:
        return "editorial_resource"
    if any(marker in text for marker in insurer_markers) and any(marker in text for marker in app_markers) and has_own_service:
        return "insurer"
    if any(marker in text for marker in broker_markers) and has_own_service:
        return "broker"
    return "unknown"


def classify_candidate(candidate: dict[str, Any], topic: str, segment: str) -> dict[str, Any]:
    domain = candidate.get("domain", "")
    url = candidate.get("url", "")
    snippets = " ".join(candidate.get("evidence_snippets", []))
    queries = " ".join(source.get("query", "") for source in candidate.get("sources", []))
    evidence_text = f"{candidate.get('name', '')} {domain} {url} {snippets}".lower()
    query_text = queries.lower()
    text = f"{evidence_text} {query_text}"
    business_model = classify_business_model(domain, url, evidence_text)
    topic_terms = [term for term in topic.lower().replace("/", " ").split() if len(term) > 2]
    segment_terms = [term for term in segment.lower().replace("/", " ").split() if len(term) > 2]
    review_domains = ["g2.com", "capterra.com", "getapp.com", "trustradius.com", "softwareadvice.com", "producthunt.com"]
    content_domains = ["forbes.com", "techcrunch.com", "zapier.com", "hubspot.com", "medium.com", "substack.com"]
    marketplace_terms = ["marketplace", "directory", "review site", "software reviews"]
    service_terms = ["agency", "consulting", "service", "done for you", "managed"]
    substitute_terms = ["spreadsheet", "template", "notion", "excel", "google sheets", "manual workflow"]
    software_terms = ["software", "platform", "tool", "app", "saas", "automation", "dashboard"]
    insurance_topic = any(term in topic.lower() for term in ["insurance", "versicherung", "pkv", "gkv", "bu", "berufsun"])

    topic_hits = sum(1 for term in topic_terms if term in evidence_text)
    segment_hits = sum(1 for term in segment_terms if term in evidence_text)
    query_topic_hits = sum(1 for term in topic_terms if term in query_text)
    query_segment_hits = sum(1 for term in segment_terms if term in query_text)
    source_count = len(candidate.get("sources", []))

    if candidate.get("known_competitor_supplied") and not url:
        competitor_type = "known_competitor_unverified"
    elif business_model == "marketplace_comparison_portal":
        competitor_type = "marketplace_comparison_portal"
    elif business_model == "lead_gen_affiliate":
        competitor_type = "lead_gen_affiliate"
    elif business_model == "editorial_resource":
        competitor_type = "editorial_resource"
    elif business_model == "insurance_app":
        competitor_type = "future_threat_candidate"
    elif business_model == "broker" and topic_hits >= 1:
        competitor_type = "direct_broker_candidate" if segment_hits or query_segment_hits else "indirect_broker_candidate"
    elif business_model == "insurer" and topic_hits >= 1:
        competitor_type = "direct_insurer_candidate" if segment_hits or query_segment_hits else "indirect_insurer_candidate"
    elif any(domain.endswith(item) for item in review_domains) or any(term in evidence_text for term in marketplace_terms):
        competitor_type = "marketplace_comparison_portal"
    elif any(domain.endswith(item) for item in content_domains):
        competitor_type = "editorial_resource"
    elif any(term in evidence_text for term in substitute_terms):
        competitor_type = "substitute_candidate"
    elif any(term in evidence_text for term in service_terms) and not any(term in evidence_text for term in software_terms):
        competitor_type = "service_substitute_candidate"
    elif insurance_topic:
        competitor_type = "uncertain_candidate"
    elif topic_hits >= 2 and segment_hits >= 1:
        competitor_type = "direct_candidate"
    elif topic_hits >= 1:
        competitor_type = "indirect_candidate"
    elif segment_hits >= 1:
        competitor_type = "future_threat_candidate"
    else:
        competitor_type = "uncertain_candidate"

    confidence_score = min(
        0.95,
        0.25
        + (0.15 * min(source_count, 3))
        + (0.12 * min(topic_hits, 3))
        + (0.08 * min(segment_hits, 2))
        + (0.04 * min(query_topic_hits, 2))
        + (0.03 * min(query_segment_hits, 2)),
    )
    if competitor_type in {"marketplace_comparison_portal", "lead_gen_affiliate", "editorial_resource", "uncertain_candidate"}:
        confidence_score = min(confidence_score, 0.55)
    evidence_quality = "strong" if confidence_score >= 0.72 and source_count >= 2 else "medium" if confidence_score >= 0.5 else "weak"
    key_success_factors = {
        "price": "unknown",
        "feature_depth": "unknown",
        "ease_of_use": "unknown",
        "integrations": "unknown",
        "distribution": "unknown",
        "trust": "unknown",
        "support": "unknown",
    }
    if "$" in text or "pricing" in text or "per month" in text:
        key_success_factors["price"] = "mentioned_in_search_evidence"
    if "integrat" in text or "api" in text:
        key_success_factors["integrations"] = "mentioned_in_search_evidence"
    if "trusted by" in text or "customers" in text or "reviews" in text:
        key_success_factors["trust"] = "mentioned_in_search_evidence"
    if "easy" in text or "simple" in text or "automate" in text:
        key_success_factors["ease_of_use"] = "mentioned_in_search_evidence"

    candidate["competitor_type_hint"] = competitor_type
    candidate["entity_type_hint"] = competitor_type
    candidate["business_model_hint"] = business_model
    candidate["source_page_type_hint"] = page_type_hint(url, business_model)
    if candidate["source_page_type_hint"] == "blog_or_resource_page":
        confidence_score = min(confidence_score, 0.82)
        evidence_quality = "medium" if confidence_score >= 0.5 else "weak"
    candidate["confidence_score"] = round(confidence_score, 2)
    candidate["evidence_quality"] = evidence_quality
    if candidate.get("known_competitor_supplied") and not url:
        candidate["segment_fit_hint"] = "not_checked"
        candidate["job_fit_hint"] = "not_checked"
        candidate["evidence_quality"] = "weak"
        candidate["confidence_score"] = min(candidate["confidence_score"], 0.35)
    else:
        candidate["segment_fit_hint"] = "explicit" if segment_hits >= 2 else "partial" if segment_hits else "query_only" if query_segment_hits else "unknown"
        candidate["job_fit_hint"] = "explicit" if topic_hits >= 2 else "partial" if topic_hits else "query_only" if query_topic_hits else "unknown"
    candidate["key_success_factors"] = key_success_factors
    candidate["needs_human_review"] = True
    return candidate


def add_known_competitors(candidates: dict[str, dict[str, Any]], known: str) -> None:
    for name in known_competitor_terms(known):
        lowered = name.lower()
        matched = False
        for candidate in candidates.values():
            candidate_name = str(candidate.get("name", "")).lower()
            candidate_domain = str(candidate.get("domain", "")).lower()
            if lowered in candidate_name or lowered.replace(" ", "") in candidate_domain.replace("-", "").replace(".", ""):
                candidate["known_competitor_supplied"] = True
                canonical_url = canonical_known_url(name, candidate_domain)
                current_url = str(candidate.get("url", ""))
                current_path = urllib.parse.urlsplit(current_url).path.lower()
                canonical_path = urllib.parse.urlsplit(canonical_url).path.lower()
                if canonical_url and (
                    not current_url
                    or canonical_path not in {"", "/"}
                    or candidate.get("source_page_type_hint") == "blog_or_resource_page"
                    or "blog" in current_path
                ):
                    candidate["url"] = canonical_url
                    candidate["canonicalized_from_known_competitor"] = True
                candidate.setdefault("sources", []).append({"source": "known_competitors_input", "query": name, "url": candidate.get("url", "")})
                matched = True
                break
        if matched:
            continue
        key = f"known:{name.lower()}"
        candidates.setdefault(
            key,
            {
                "name": name,
                "domain": "",
                "url": "",
                "page_title": name,
                "sources": [{"source": "known_competitors_input", "query": name, "url": ""}],
                "evidence_snippets": [f"Known competitor supplied by user: {name}"],
                "first_seen_at": now_iso(),
                "known_competitor_supplied": True,
            },
        )


def known_lookup_relevant(topic: str, title: str, description: str, url: str) -> bool:
    topic_lower = topic.lower()
    text = f"{title} {description} {url}".lower()
    if any(marker in text for marker in NOISY_LOOKUP_MARKERS):
        return False
    domain = domain_of(url)
    if domain:
        expected = canonical_known_url("", domain)
        if expected and domain_of(expected) == domain:
            return True
    if any(marker in topic_lower for marker in ["pkv", "private health", "krankenversicherung", "health insurance"]):
        return any(marker in text for marker in ["pkv", "private health", "krankenversicherung", "health insurance", "private krankenversicherung"])
    return True


def enrich_known_competitors(candidates: dict[str, dict[str, Any]], known: str, raw: dict[str, Any], geo: str, language: str, topic: str) -> dict[str, Any]:
    key_name, api_key = get_secret("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return {"status": "missing_credentials", "required_env": ["BRAVE_SEARCH_API_KEY"], "candidate_count": 0}
    status = "ok"
    added = 0
    for name in known_competitor_terms(known):
        lowered = name.lower()
        if any(
            lowered in str(candidate.get("name", "")).lower()
            or lowered.replace(" ", "") in str(candidate.get("domain", "")).lower().replace("-", "").replace(".", "")
            for candidate in candidates.values()
        ):
            continue
        queries = [
            f"{name} PKV",
            f"{name} private health insurance Germany",
            f"{name} Krankenversicherung",
            f"{name} insurance Germany",
        ]
        for query in queries:
            response = http_get(
                with_query("https://api.search.brave.com/res/v1/web/search", {"q": query, "count": 3, "country": geo, "search_lang": language}),
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            )
            raw.setdefault("known_competitor_lookup", []).append({"name": name, "query": query, "response": response})
            if not response.get("ok"):
                status = status_from_response(response)
                continue
            web = (response.get("body") or {}).get("web") or {}
            before = len(candidates)
            for item in web.get("results") or []:
                if not known_lookup_relevant(topic, item.get("title", ""), item.get("description", ""), item.get("url", "")):
                    continue
                add_candidate(
                    candidates,
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    query=query,
                    source="known_competitor_lookup",
                )
            added += max(0, len(candidates) - before)
            if len(candidates) > before:
                break
    return {"status": status, "credential_source": key_name, "candidate_count": added}


def add_candidate(candidates: dict[str, dict[str, Any]], *, url: str, title: str, description: str, query: str, source: str) -> None:
    domain = domain_of(url)
    if not domain:
        return
    noisy_text = f"{domain} {url} {title} {description}".lower()
    if any(marker in noisy_text for marker in NOISY_LOOKUP_MARKERS):
        return
    ignored = {"reddit.com", "youtube.com", "facebook.com", "linkedin.com", "x.com", "twitter.com", "medium.com"}
    if domain in ignored:
        return
    candidate = candidates.setdefault(
        domain,
        {
            "name": brand_from_domain(domain),
            "domain": domain,
            "url": url,
            "page_title": likely_name(title, domain),
            "sources": [],
            "evidence_snippets": [],
            "first_seen_at": now_iso(),
        },
    )
    candidate["sources"].append({"source": source, "query": query, "url": url})
    snippet = " ".join(part for part in [title, description] if part).strip()
    if snippet and snippet not in candidate["evidence_snippets"]:
        candidate["evidence_snippets"].append(snippet[:500])


def brave_search(queries: list[str], limit: int, raw: dict[str, Any], geo: str, language: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("BRAVE_SEARCH_API_KEY")
    candidates: dict[str, dict[str, Any]] = {}
    if not api_key:
        return candidates, {"status": "missing_credentials", "required_env": ["BRAVE_SEARCH_API_KEY"]}
    status = "ok"
    for query in queries:
        response = http_get(
            with_query("https://api.search.brave.com/res/v1/web/search", {"q": query, "count": min(limit, 10), "country": geo, "search_lang": language}),
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
        )
        raw.setdefault("brave_search", []).append({"query": query, "response": response})
        if not response.get("ok"):
            status = status_from_response(response)
            continue
        web = (response.get("body") or {}).get("web") or {}
        for item in web.get("results") or []:
            add_candidate(
                candidates,
                url=item.get("url", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                query=query,
                source="brave_search",
            )
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    return candidates, {"status": status, "credential_source": key_name, "candidate_count": len(candidates)}


def firecrawl_search(queries: list[str], limit: int, raw: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    candidates: dict[str, dict[str, Any]] = {}
    if not api_key:
        return candidates, {"status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}
    status = "ok"
    for query in queries[:4]:
        response = http_post(
            "https://api.firecrawl.dev/v1/search",
            headers={"Authorization": f"Bearer {api_key}"},
            data={"query": query, "limit": min(limit, 10)},
        )
        raw.setdefault("firecrawl", []).append({"query": query, "response": response})
        if not response.get("ok"):
            status = status_from_response(response)
            continue
        for item in (response.get("body") or {}).get("data") or []:
            add_candidate(
                candidates,
                url=item.get("url", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                query=query,
                source="firecrawl",
            )
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    return candidates, {"status": status, "credential_source": key_name, "candidate_count": len(candidates)}


def write_report(run_dir: Path, args: argparse.Namespace, candidates: list[dict[str, Any]], provider_summaries: dict[str, Any]) -> None:
    needs_attention = [
        f"{provider}: {summary.get('status')}"
        for provider, summary in provider_summaries.items()
        if summary.get("status") not in {"ok", "not_run"}
    ]
    lines = [
        "# Competitor Discovery Run",
        "",
        f"- Topic: {args.topic}",
        f"- Customer segment: {args.customer_segment}",
        f"- Candidates: {len(candidates)}",
        "",
        "## Provider Status",
        "",
    ]
    for provider, summary in provider_summaries.items():
        lines.append(f"- {provider}: {summary.get('status')} ({summary.get('candidate_count', 0)} candidates)")
    if needs_attention:
        lines.extend(["", "## Provider Alerts", ""])
        for item in needs_attention:
            lines.append(f"- {item}")
    lines.extend(["", "## Candidate Competitors", ""])
    for candidate in candidates:
        snippet = candidate["evidence_snippets"][0] if candidate["evidence_snippets"] else ""
        lines.append(
            f"- {candidate['name']} - `{candidate['domain']}` - {candidate.get('competitor_type_hint', 'unknown')} "
            f"- {candidate.get('business_model_hint', 'unknown_model')} - {candidate.get('source_page_type_hint', 'unknown_page')} - confidence {candidate.get('confidence_score', 'n/a')} "
            f"- {candidate['url']} - {snippet}"
        )
    lines.extend(["", "## Competitor Array", ""])
    lines.append("| Candidate | Type hint | Segment fit | Job fit | Evidence | Key unknowns |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for candidate in candidates:
        unknowns = [
            factor
            for factor, value in candidate.get("key_success_factors", {}).items()
            if value == "unknown"
        ][:4]
        lines.append(
            "| "
            + " | ".join(
                [
                    candidate.get("name", ""),
                    f"{candidate.get('competitor_type_hint', 'unknown')} ({candidate.get('source_page_type_hint', 'unknown_page')})",
                    candidate.get("segment_fit_hint", "unknown"),
                    candidate.get("job_fit_hint", "unknown"),
                    candidate.get("evidence_quality", "weak"),
                    ", ".join(unknowns) or "none",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Analyst Warnings",
            "",
            "- Search results can include blogs, marketplaces, agencies, and review sites. Verify each candidate manually before calling it a direct competitor.",
            "- Competitor presence is not proof of market demand; use it as context for positioning, pricing, and category language.",
        ]
    )
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover potential competitors for a business idea.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--customer-segment", default="")
    parser.add_argument("--known-competitors", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--geo", default="US")
    parser.add_argument("--language", default="en")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--workspace", default="", help="Topic workspace path. Defaults to research/topics/<topic-slug>.")
    parser.add_argument("--legacy-output", action="store_true", help="Write to the former research/evidence-scout/competitors layout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir, workspace = resolve_run_dir(
        topic=args.topic,
        workspace_arg=args.workspace,
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="competitors/runs",
        legacy_subdir="competitors",
        customer_segment=args.customer_segment,
    )
    if workspace:
        update_stage(workspace, "competitor_discovery", status="in_progress", gate_result="not_run", next_action="Classify discovered alternatives and false positives.")
    queries = query_plan(args.topic, args.customer_segment, args.known_competitors)
    raw: dict[str, Any] = {"queries": queries}

    brave_candidates, brave_summary = brave_search(queries, args.limit, raw, args.geo, args.language)
    firecrawl_candidates, firecrawl_summary = firecrawl_search(queries, args.limit, raw)
    merged = {**firecrawl_candidates, **brave_candidates}
    known_lookup_summary = enrich_known_competitors(merged, args.known_competitors, raw, args.geo, args.language, args.topic)
    add_known_competitors(merged, args.known_competitors)
    classified = [classify_candidate(item, args.topic, args.customer_segment) for item in merged.values()]
    known_unverified = [item for item in classified if item.get("competitor_type_hint") == "known_competitor_unverified"]
    discovered = [item for item in classified if item.get("competitor_type_hint") != "known_competitor_unverified"]
    discovered = sorted(discovered, key=lambda item: (item["confidence_score"], len(item["sources"])), reverse=True)
    candidates = discovered[: max(args.limit - len(known_unverified), 0)] + known_unverified

    provider_summaries = {"brave_search": brave_summary, "firecrawl": firecrawl_summary, "known_competitor_lookup": known_lookup_summary}
    needs_user_attention = [
        f"{provider}: {summary.get('status')}"
        for provider, summary in provider_summaries.items()
        if summary.get("status") not in {"ok", "not_run"}
    ]
    summary = {
        "run_dir": str(run_dir),
        "topic": args.topic,
        "customer_segment": args.customer_segment,
        "candidate_count": len(candidates),
        "providers": provider_summaries,
        "needs_user_attention": needs_user_attention,
        "outputs": {
            "competitors_json": str(run_dir / "competitors.json"),
            "report": str(run_dir / "report.md"),
            "raw": str(run_dir / "raw.json"),
        },
    }
    write_json(run_dir / "raw.json", redact_sensitive(raw))
    write_json(run_dir / "competitors.json", candidates)
    write_json(run_dir / "summary.json", summary)
    write_report(run_dir, args, candidates, provider_summaries)
    if workspace:
        failures = [
            {"provider": provider, "failure_class": str(result.get("status", "failed")), "confidence_impact": "medium"}
            for provider, result in provider_summaries.items()
            if result.get("status") not in {"ok", "not_run"}
        ]
        gate_result = "fail" if not candidates else ("conditional_pass" if failures else "pass")
        update_stage(
            workspace,
            "competitor_discovery",
            status="failed" if gate_result == "fail" else "passed",
            gate_result=gate_result,
            artifacts=[run_dir / "competitors.json", run_dir / "summary.json", run_dir / "report.md"],
            provider_failures=failures,
            next_action="Verify uncertain candidates, then analyze selected competitors' marketing.",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
