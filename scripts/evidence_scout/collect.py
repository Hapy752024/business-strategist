#!/usr/bin/env python3
"""Collect normalized market evidence from script-accessible providers.

This is intentionally API-first and dependency-light so the same script can be
called from Codex, OpenCode, Claude Code, CI, or a plain terminal.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "scripts" / "validate_apis"
REGISTRY_DIR = Path(__file__).resolve().parent / "registries"
EVIDENCE_SCHEMA_PATH = ROOT / "schemas" / "evidence-record.schema.json"
COMMUNITY_AUTH_SCHEMA_PATH = ROOT / "schemas" / "community-capture-authorization.schema.json"
COMMUNITY_RECEIPT_SCHEMA_PATH = ROOT / "schemas" / "community-review-receipt.schema.json"
VERIFIED_COMMUNITY_SCHEMA_PATH = ROOT / "schemas" / "verified-community.schema.json"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import (  # noqa: E402
    fields_present,
    finish,
    get_secret,
    http_get,
    http_post,
    request_budget,
    is_credit_exhaustion,
    now_iso,
    redact_sensitive,
    status_from_response,
    with_query,
)
from workspace import create_run_manifest, resolve_run_dir, update_run_manifest, update_stage  # noqa: E402

EVIDENCE_VALIDATOR = Draft202012Validator(
    json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8")), format_checker=FormatChecker()
)
COMMUNITY_AUTH_VALIDATOR = Draft202012Validator(json.loads(COMMUNITY_AUTH_SCHEMA_PATH.read_text(encoding="utf-8")), format_checker=FormatChecker())
COMMUNITY_RECEIPT_VALIDATOR = Draft202012Validator(json.loads(COMMUNITY_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8")), format_checker=FormatChecker())
VERIFIED_COMMUNITY_VALIDATOR = Draft202012Validator(json.loads(VERIFIED_COMMUNITY_SCHEMA_PATH.read_text(encoding="utf-8")), format_checker=FormatChecker())


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    safe = "-".join(part for part in safe.split("-") if part)
    return safe[:80] or "evidence-run"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


# Optional emergency fallbacks remain empty by design. The registry is the
# source of truth, keeping project-specific markets out of reusable code.
FALLBACK_PHRASE_VARIANTS: dict[str, str] = {}
FALLBACK_QUERY_MARKETS: dict[str, Any] = {}

QUERY_EXPANSION = read_json(REGISTRY_DIR / "query_expansion.json", {})


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def csv_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def infer_geo_language(topic: str, customer_segment: str, problem_keywords: str = "", workaround_keywords: str = "") -> tuple[str, str]:
    text = " ".join([topic, customer_segment, problem_keywords, workaround_keywords]).lower()
    if any("\u0600" <= char <= "\u06ff" for char in text):
        return "SA", "ar"
    for locale in QUERY_EXPANSION.get("locale_inference", []):
        if any(str(marker).lower() in text for marker in locale.get("markers", [])):
            language = locale.get("english_language") if "english" in text and locale.get("english_language") else locale.get("language")
            return str(locale.get("geo", "US")), str(language or "en")
    return "US", "en"


def segment_modifiers(customer_segment: str) -> list[str]:
    """Return short audience/location phrases users might actually include in searches."""
    segment = customer_segment.lower()
    modifiers: list[str] = []
    candidates = [
        ("expat", "expats"),
        ("freelancer", "freelancers"),
        ("self-employed", "self employed"),
        ("founder", "founders"),
        ("creator", "creators"),
        ("student", "students"),
        ("parent", "parents"),
        ("family", "families"),
        ("developer", "developers"),
        ("engineer", "engineers"),
        ("english-speaking", "English speaking"),
        ("english speaking", "English speaking"),
    ]
    for needle, phrase in candidates:
        if needle in segment and phrase not in modifiers:
            modifiers.append(phrase)
    return modifiers[:3]


def user_language_terms(topic: str, problem_keywords: str = "", workaround_keywords: str = "") -> list[str]:
    terms = [topic.strip()]
    terms.extend(csv_terms(problem_keywords))
    terms.extend(csv_terms(workaround_keywords))
    deduped: list[str] = []
    for term in terms:
        clean = " ".join(term.replace('"', "").split())
        if clean and clean not in deduped:
            deduped.append(clean)
    return deduped


def german_variants(term: str) -> list[str]:
    variants = [term]
    swaps = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
    ascii_term = term
    for source, target in swaps.items():
        ascii_term = ascii_term.replace(source, target)
    if ascii_term != term:
        variants.append(ascii_term)

    lower = term.lower()
    phrase_variants: dict[str, str] = dict(FALLBACK_PHRASE_VARIANTS)
    for market in QUERY_EXPANSION.get("markets", {}).values():
        if str(market.get("geo", "")).upper() == "DE":
            phrase_variants.update(market.get("phrase_variants", {}))
    for needle, replacement in phrase_variants.items():
        if needle in lower and replacement not in variants:
            variants.append(re.sub(needle, replacement, term, flags=re.IGNORECASE))

    deduped: list[str] = []
    for variant in variants:
        clean = " ".join(variant.split())
        if clean and clean not in deduped:
            deduped.append(clean)
    return deduped


def expand_language_variants(terms: list[str], geo: str, language: str) -> list[str]:
    expanded: list[str] = []
    is_german = geo.upper() == "DE" or language.lower().startswith("de")
    for term in terms:
        variants = german_variants(term) if is_german else [term]
        for variant in variants:
            if variant not in expanded:
                expanded.append(variant)
    return expanded


def inferred_search_terms(topic: str) -> list[str]:
    """Best-effort fallback terms when idea-grill did not supply search phrases."""
    base = " ".join(topic.replace('"', "").split())
    if not base:
        return []

    lower = base.lower()
    terms = [base]

    if "insurance" in lower or "pkv" in lower or "gkv" in lower or "bu" in lower:
        terms.extend(
            [
                base.replace("digital ", "").replace(" advice", ""),
                f"{base} comparison",
                f"{base} explained",
                f"{base} reviews",
            ]
        )
    else:
        terms.extend(
            [
                f"{base} alternative",
                f"{base} comparison",
                f"{base} reviews",
                f"{base} problem",
            ]
        )

    deduped: list[str] = []
    for term in terms:
        clean = " ".join(term.split())
        if clean and clean not in deduped:
            deduped.append(clean)
    return deduped[:5]


def problem_first_terms(topic: str, geo: str, language: str) -> list[str]:
    lower = topic.lower()
    for market in QUERY_EXPANSION.get("markets", {}).values():
        if market.get("geo", "").upper() == geo.upper() and any(str(marker).lower() in lower for marker in market.get("trigger_markers", [])):
            return expand_language_variants(list(market.get("problem_first_terms", [])), geo, language)
    return []


def discovery_query_plan(
    topic: str,
    problem_keywords: str = "",
    workaround_keywords: str = "",
    geo: str = "US",
    language: str = "en",
) -> list[str]:
    """Broaden collection before a customer/problem thesis has been chosen."""
    base = topic.strip()
    queries = [
        f"{base} problems",
        f"{base} pain points",
        f"{base} complaints",
        f'"frustrated" {base}',
        f"{base} forum complaints",
        f"{base} reddit complaints",
        f"{base} workaround",
        f"{base} alternatives",
        f"{base} reviews problems",
        f'"too expensive" {base}',
    ]
    for term in expand_language_variants(csv_terms(problem_keywords), geo, language):
        queries.extend([term, f"{term} complaints", f"{term} forum", f"{term} workaround"])
    for term in expand_language_variants(csv_terms(workaround_keywords), geo, language):
        queries.extend([term, f"{term} manual", f"{term} alternative"])
    deduped: list[str] = []
    for query in queries:
        clean = " ".join(query.split())
        if clean and clean not in deduped:
            deduped.append(clean)
    if language.split("-")[0].lower() != "en":
        suffixes = {
            "de": ["Probleme", "Beschwerden", "Forum Erfahrungen", "selbst gemacht Alternative", "gute Erfahrungen zufrieden", "nicht genutzt warum", "gewechselt gekündigt", "Facebook Gruppe Erfahrungen"],
            "fr": ["problèmes", "réclamations", "forum expérience", "solution alternative fait maison", "bonne expérience satisfait", "pas utilisé pourquoi", "changé résilié", "groupe Facebook expérience"],
            "es": ["problemas", "quejas", "foro experiencia", "alternativa por mi cuenta", "buena experiencia satisfecho", "no utilicé por qué", "cambié cancelé", "grupo Facebook experiencia"],
            "it": ["problemi", "reclami", "forum esperienza", "alternativa fai da te", "buona esperienza soddisfatto", "non utilizzato perché", "cambiato disdetto", "gruppo Facebook esperienza"],
            "zh": ["问题", "投诉", "论坛 经验", "手动 替代方案", "好用 满意", "不用了 原因", "换了 取消", "Facebook 群组 经验"],
        }.get(language.split("-")[0].lower())
        seeds = [base, *csv_terms(problem_keywords), *csv_terms(workaround_keywords)]
        # Unknown language: preserve supplied source-language seeds, never silently
        # assert English scaffolding is native coverage. The agent supplies terms.
        return list(dict.fromkeys([f"{seed} {suffix}" for suffix in suffixes for seed in seeds] if suffixes else seeds))
    return deduped


def query_plan(
    topic: str,
    customer_segment: str,
    problem_keywords: str = "",
    workaround_keywords: str = "",
    geo: str = "US",
    language: str = "en",
    research_mode: str = "validation",
    segment_keywords: str = "",
) -> list[str]:
    if research_mode == "discovery":
        return balanced_queries(discovery_query_plan(topic, problem_keywords, workaround_keywords, geo, language) + perspective_queries(topic, language))
    if language.split("-")[0].lower() != "en":
        seeds = discovery_query_plan(topic, problem_keywords, workaround_keywords, geo, language)
        seeds.extend(problem_first_terms(topic, geo, language) if not (problem_keywords or workaround_keywords) else [])
        anchors = csv_terms(segment_keywords)
        return balanced_queries(list(dict.fromkeys(f"{query} {anchor}" for query in seeds for anchor in anchors)) if anchors else seeds)
    base = topic.strip()
    modifiers = segment_modifiers(customer_segment)
    explicit_terms = bool(csv_terms(problem_keywords) or csv_terms(workaround_keywords))
    problem_terms = [] if explicit_terms else problem_first_terms(topic, geo, language)
    scoped_terms = [base]
    scoped_terms.extend(f"{base} {modifier}" for modifier in modifiers)
    queries = []
    for term in problem_terms:
        queries.extend(
            [
                term,
                f"{term} Erfahrungen",
                f"{term} Forum",
                f"{term} Reddit",
            ]
        )
    queries.extend([
        *scoped_terms,
        f'"why is it so hard to" {base}',
        f'"how do you deal with" {base}',
        f'"frustrated" {base}',
        f'"alternative to" {base}',
        f'"best way to" {base}',
        f'{base} forum pain points',
        f'{base} reddit complaints',
    ])
    for term in expand_language_variants(csv_terms(problem_keywords), geo, language):
        scoped_problem_terms = [term]
        scoped_problem_terms.extend(f"{term} {modifier}" for modifier in modifiers)
        queries.extend(
            [
                *scoped_problem_terms,
                f'"why is it so hard to" {term}',
                f'"how do you deal with" {term}',
                f'"frustrated" {term}',
                f'{term} forum complaints',
                f'{term} reddit workflow',
            ]
        )
    for term in expand_language_variants(csv_terms(workaround_keywords), geo, language):
        scoped_workaround_terms = [term]
        scoped_workaround_terms.extend(f"{term} {modifier}" for modifier in modifiers)
        queries.extend(
            [
                *scoped_workaround_terms,
                f'"manually" {term}',
                f'"spreadsheet" {term}',
                f'"template" {term}',
            ]
        )
    deduped: list[str] = []
    for query in queries:
        if query and query not in deduped:
            deduped.append(query)
    # Explicit short audience terms narrow every validation query. They are
    # retrieval constraints, not proof that a retrieved author fits the target.
    deduped.extend(perspective_queries(base, language))
    anchors = csv_terms(segment_keywords)
    if anchors:
        deduped = list(dict.fromkeys(f"{query} {anchor}" for query in deduped for anchor in anchors))
    return balanced_queries(deduped)


def perspective_queries(topic: str, language: str) -> list[str]:
    """Countercases and customer language complement, not replace, pain seeds."""
    terms = {
        "en": ["worked well experience", "decided not to use", "switched cancelled", "forum experience", "Facebook group experience"],
        "de": ["gute Erfahrungen zufrieden", "nicht genutzt warum", "gewechselt gekündigt", "Forum Erfahrungen", "Facebook Gruppe Erfahrungen"],
        "fr": ["bonne expérience satisfait", "pas utilisé pourquoi", "changé résilié", "forum expérience", "groupe Facebook expérience"],
        "es": ["buena experiencia satisfecho", "no utilicé por qué", "cambié cancelé", "foro experiencia", "grupo Facebook experiencia"],
        "it": ["buona esperienza soddisfatto", "non utilizzato perché", "cambiato disdetto", "forum esperienza", "gruppo Facebook esperienza"],
        "zh": ["好用 满意", "不用了 原因", "换了 取消", "论坛 经验", "Facebook 群组 经验"],
    }.get(language.split("-")[0].lower(), [])
    return [f"{topic} {term}" for term in terms]


def query_intent(query: str) -> str:
    lower = query.casefold()
    for intent, markers in (
        ("successful_alternative", ["worked well", "gute erfahrungen", "bonne expérience", "buena experiencia", "buona esperienza", "好用 满意"]),
        ("nonadoption", ["not to use", "nicht genutzt", "pas utilisé", "no utilicé", "non utilizzato", "不用了"]),
        ("switching_exit", ["switched", "cancelled", "gewechselt", "gekündigt", "résilié", "cambié", "cancelé", "disdetto", "换了"]),
        ("facebook_discovery", ["facebook"]),
        ("community_discovery", ["forum", "reddit", "foro", "论坛"]),
        ("workaround", ["workaround", "manually", "spreadsheet", "alternative", "alternativa", "deal with", "替代方案"]),
        ("pain", ["complaint", "frustrated", "hard to", "pain", "expensive", "probleme", "beschwerden", "problèmes", "réclamations", "problemas", "quejas", "problemi", "reclami", "问题", "投诉"]),
    ):
        if any(marker in lower for marker in markers): return intent
    return "open_discovery"


def balanced_queries(queries: list[str]) -> list[str]:
    """Round-robin intents so positional provider limits cannot select pain only."""
    buckets: dict[str, list[str]] = {}
    for query in dict.fromkeys(queries): buckets.setdefault(query_intent(query), []).append(query)
    output = []
    while any(buckets.values()):
        for values in buckets.values():
            if values: output.append(values.pop(0))
    return output


def scheduled_queries(args: argparse.Namespace, queries: list[str]) -> list[str]:
    return balanced_queries(queries)[:max(1, getattr(args, "query_limit", 12))]


def trend_terms(topic: str, problem_keywords: str = "", workaround_keywords: str = "", geo: str = "US", language: str = "en") -> list[str]:
    """Google Trends terms should be phrases users would type, never segment prose."""
    seeded_terms = [*csv_terms(problem_keywords), *csv_terms(workaround_keywords)]
    terms = user_language_terms(topic if not seeded_terms else "", problem_keywords, workaround_keywords)
    if not seeded_terms:
        terms = inferred_search_terms(topic)
    terms = expand_language_variants(terms, geo, language)
    expansion_terms = [] if seeded_terms else demand_expansion_terms(topic, geo, language)
    if expansion_terms:
        terms = expansion_terms + terms
    filtered = [
        term
        for term in terms
        if len(term) <= 80 and not any(marker in term.lower() for marker in ["why is it", "how do you", "frustrated"])
    ]
    return filtered[:5]


def demand_expansion_terms(topic: str, geo: str, language: str) -> list[str]:
    lower = topic.lower()
    for market in QUERY_EXPANSION.get("markets", {}).values():
        if market.get("geo", "").upper() == geo.upper() and any(str(marker).lower() in lower for marker in market.get("trigger_markers", [])):
            return expand_language_variants(list(market.get("demand_terms", [])), geo, language)
    return []


def social_terms(topic: str, problem_keywords: str = "", workaround_keywords: str = "", geo: str = "US", language: str = "en") -> list[str]:
    """Social search works best on compact pain/category/competitor phrases."""
    seeded_terms = [*csv_terms(problem_keywords), *csv_terms(workaround_keywords)]
    if not seeded_terms:
        return expand_language_variants(inferred_search_terms(topic), geo, language)[:3]
    return expand_language_variants(user_language_terms("", problem_keywords, workaround_keywords), geo, language)[:3]


def reddit_queries(args: argparse.Namespace, queries: list[str]) -> list[str]:
    if csv_terms(args.problem_keywords) or csv_terms(args.workaround_keywords):
        return queries[:5]
    topic_context = args.topic.lower()
    markets = QUERY_EXPANSION.get("markets", {}) or FALLBACK_QUERY_MARKETS
    for market in markets.values():
        markers = [str(m).lower() for m in market.get("trigger_markers", [])]
        if market.get("geo", "").upper() == args.geo.upper() and any(marker in topic_context for marker in markers):
            return list(market.get("reddit_queries", [])) + queries[:4]
    return queries[:5]


def tokenize_for_relevance(value: str) -> set[str]:
    stop = {
        "and",
        "the",
        "for",
        "with",
        "from",
        "that",
        "this",
        "your",
        "you",
        "how",
        "why",
        "best",
        "way",
        "forum",
        "reddit",
        "complaints",
        "workflow",
        "pain",
        "points",
        "english",
        "speaking",
        "germany",
        "german",
        "digital",
        "advice",
        "self",
        "employed",
    }
    return {token for token in re.findall(r"[\wäöüÄÖÜß]{3,}", value.lower()) if token not in stop}


def relevance_terms(args: argparse.Namespace, query: str) -> set[str]:
    seeded = " ".join([args.topic, args.problem_keywords, args.workaround_keywords, query])
    return tokenize_for_relevance(seeded)


def assess_relevance(text: str, args: argparse.Namespace, query: str, url: str = "", author_context: str = "") -> tuple[str, str, int]:
    haystack = " ".join([text, url, author_context]).lower()
    terms = relevance_terms(args, query)
    hits = {term for term in terms if term in haystack}
    score = len(hits)
    lower = text.lower()
    topic_context = " ".join([args.topic, args.problem_keywords, args.workaround_keywords]).lower()
    insurance_topic = any(marker in topic_context for marker in ["insurance", "versicherung", "pkv", "gkv", "berufsun", "makler"])
    if insurance_topic:
        insurance_anchors = [
            "pkv",
            "gkv",
            "bu ",
            "berufsun",
            "private health insurance",
            "health insurance",
            "krankenversicherung",
            "versicherungsmakler",
            "versicherungsberater",
            "versicher",
            "makler",
            "risikovoranfrage",
            "voranfrage",
            "tarif",
            "ottonova",
            "feather",
            "check24",
            "finanztip",
            "getsafe",
            "clark",
        ]
        if not any(anchor in haystack for anchor in insurance_anchors):
            return "irrelevant", "Insurance topic requires a concrete PKV/GKV/BU/health-insurance/broker anchor; only generic terms matched.", score
        if "youtube" in query.lower() or "youtube.com" in url.lower():
            decision_markers = [
                "pkv",
                "gkv",
                "bu ",
                "berufsun",
                "private health insurance",
                "public insurance",
                "krankenversicherung",
                "risikovoranfrage",
                "voranfrage",
                "which",
                "choose",
                "wechsel",
                "vergleich",
                "tarif",
                "versicherung",
                "cost",
                "kosten",
                "claim",
                "anspruch",
            ]
            if len(text) < 180 and not any(marker in haystack for marker in decision_markers):
                return "irrelevant", "Short insurance comment lacks concrete PKV/GKV/BU decision or workaround intent.", score
    if any(marker in lower for marker in ["game title", "developer:", "platforms:", "metacritic", "opencritic", "review thread"]):
        score -= 4
    if any(marker in lower for marker in ["market rundown", "stock", "nvidia", "ticker", "earnings"]) and not any(
        marker in lower for marker in ["insurance", "versicherung", "pkv", "gkv", "broker"]
    ):
        score -= 2
    if score <= 0:
        return "irrelevant", "No material overlap with topic/problem/workaround terms.", score
    if score == 1:
        return "weak", "Only one material topic term matched; treat as weak lead.", score
    return "relevant", f"Matched {score} material topic terms.", score


def infer_evidence_type(text: str) -> str:
    lower = text.lower()
    decision_markers = [
        "pkv oder gkv",
        "gkv oder pkv",
        "entscheiden",
        "entscheidung",
        "wechseln oder nicht",
        "rückkehr",
        "rueckkehr",
        "gesundheitsfragen",
        "risikovoranfrage",
        "voranfrage",
        "welcher tarif",
        "welche versicherung",
        "überfragt",
        "qual der wahl",
        "keine relevanten entscheidungsgrundlagen",
    ]
    pain_markers = [
        "hate",
        "frustrated",
        "hard",
        "annoying",
        "pain",
        "struggle",
        "broken",
        "angst",
        "verzweifelt",
        "unmöglich",
        "kompliziert",
        "keine ahnung",
        "unsicher",
    ]
    if any(token in lower for token in ["alternative to", "switched from", "moved from", "gegen die pkv entschieden", "wechseln oder nicht", "平替", "换了", "替代", "不用了", "转投"]):
        return "competitor_gap"
    if any(token in lower for token in ["workaround", "hack", "manually", "spreadsheet", "zapier", "recherche", "maklern", "quellen", "angebote", "tarife vergleichen", "手动", "表格", "凑合", "临时方案", "替代方案", "自己整理"]):
        return "workaround"
    if any(token in lower for token in ["not a problem", "solved", "works fine", "good enough", "没问题", "够用", "已经解决", "挺好用"]):
        return "counter_evidence"
    if any(token in lower for token in decision_markers):
        return "decision_uncertainty"
    if any(token in lower for token in ["怎么选", "如何选择", "纠结", "求推荐", "有没有推荐", "靠谱吗", "值得买吗", "避雷"]):
        return "decision_uncertainty"
    if any(token in lower for token in pain_markers):
        return "pain"
    if any(token in lower for token in ["麻烦", "踩坑", "坑", "难用", "不好用", "后悔", "崩溃", "费劲", "不靠谱", "太复杂"]):
        return "pain"
    if any(token in lower for token in ["expensive", "paid", "price", "cost", "$", "€", "beiträge", "kosten", "zuschlag", "provision", "贵", "价格", "收费", "花钱", "成本"]):
        return "spend"
    return "community"


SOURCE_INTENT_DOMAINS = read_json(REGISTRY_DIR / "source_intents.json", {})


def infer_comment_intent(source: str, text: str, evidence_type: str) -> str:
    lower = text.lower()
    if source not in {"reddit", "youtube_comment", "x", "tiktok", "instagram", "threads", "facebook"}:
        if source not in {"bilibili", "bilibili_comment", "xiaohongshu", "v2ex", "weibo", "zhihu", "douban", "tieba"}:
            return "not_social_comment"
    if evidence_type == "irrelevant":
        return "offtopic"
    if evidence_type == "decision_uncertainty" or any(marker in lower for marker in ["?", "？", "welche", "welcher", "soll ich", "pkv oder gkv", "what should", "which insurance", "怎么选", "怎么办", "值得买吗", "靠谱吗", "如何选择"]):
        return "decision_question"
    if evidence_type in {"pain", "counter_evidence"} or any(marker in lower for marker in ["angst", "kompliziert", "frustriert", "problem", "schlecht", "nicht vertrauen", "麻烦", "踩坑", "避雷", "坑", "后悔", "难用", "不好用", "不靠谱"]):
        return "complaint"
    if any(marker in lower for marker in ["ottonova", "feather", "clark", "getsafe", "check24", "verivox", "makler", "berater", "anbieter"]):
        return "provider_question"
    if any(marker in lower for marker in ["danke", "hilfreich", "super", "gutes video", "empfehlen"]):
        return "provider_praise"
    return "social_context"


def infer_source_intent(source: str, source_url: str, text: str, evidence_type: str) -> str:
    lower_url = source_url.lower()
    lower = text.lower()
    editorial_markers = ["guide", "blog", "article", "explained", "best ", "top ", "vergleich", "comparison", "ratgeber", "erfahrungen"]
    china_social_sources = {"bilibili", "bilibili_comment", "xiaohongshu", "weibo", "douban"}
    china_forum_sources = {"v2ex", "zhihu", "tieba"}
    if source in {"reddit", "youtube_comment", "x", "tiktok", "instagram", "threads", "facebook"}:
        if evidence_type in {"pain", "workaround", "counter_evidence", "spend", "competitor_gap", "decision_uncertainty"}:
            return "user_pain"
        return "social_comment"
    if source in china_social_sources:
        if evidence_type in {"pain", "workaround", "counter_evidence", "spend", "competitor_gap", "decision_uncertainty"}:
            return "user_pain"
        return "social_comment"
    if source in china_forum_sources:
        if evidence_type in {"pain", "workaround", "counter_evidence", "spend", "competitor_gap", "decision_uncertainty"}:
            return "user_pain"
        return "forum_discussion"
    if source == "google_trends":
        return "search_demand"
    if source == "app_store":
        return "search_demand" if evidence_type == "search_demand" else "competitor_content"
    if source == "app_review":
        return "user_pain" if evidence_type in {"pain", "workaround", "counter_evidence", "spend", "competitor_gap", "decision_uncertainty"} else "social_context"
    if any(domain in lower_url for domain in SOURCE_INTENT_DOMAINS["forum_discussion"]):
        return "forum_discussion"
    for intent, domains in SOURCE_INTENT_DOMAINS.items():
        if intent == "forum_discussion":
            continue
        if any(domain in lower_url for domain in domains):
            return intent
    if any(marker in lower_url or marker in lower for marker in editorial_markers):
        return "editorial_content"
    if source == "forum":
        return "forum_discussion"
    if source in {"web_search", "forum"} and any(marker in lower for marker in ["get a quote", "free quote", "broker", "makler", "tariff", "tarif"]):
        return "competitor_content"
    return "unknown"


def engagement_int(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def estimate_strength(text: str, engagement: dict[str, Any]) -> str:
    lower = text.lower()
    pain_terms = ["hate", "frustrated", "hard", "annoying", "pain", "struggle", "broken", "waste", "überfragt", "angst", "verzweifelt", "qual der wahl", "unmöglich", "kompliziert", "麻烦", "踩坑", "避雷", "难用", "不好用", "后悔", "崩溃", "不靠谱"]
    workaround_terms = ["workaround", "manually", "spreadsheet", "hack", "alternative", "recherche", "maklern", "quellen", "angebote", "tarife vergleichen", "手动", "表格", "凑合", "临时方案", "替代方案", "自己整理"]
    score = 0
    if any(term in lower for term in pain_terms):
        score += 1
    if any(term in lower for term in workaround_terms):
        score += 1
    # Platform engagement helps discovery, but cannot manufacture independent
    # corroboration or willingness-to-pay evidence from a single observation.
    if score == 2:
        return "medium"
    return "weak"


def source_role(source: str, source_intent: str) -> str:
    if source == "youtube_transcript":
        return "creator_statement"
    if source == "google_autocomplete":
        return "search_suggestion"
    if source == "xai_x_search":
        return "discovery_only"
    if source in {"itunes_reviews", "app_review", "google_places_review", "trustpilot_review"}:
        return "customer_review"
    if source in {"reddit", "youtube_comment", "x", "tiktok", "instagram", "threads", "facebook", "hn", "github", "v2ex", "zhihu", "weibo", "douban", "tieba", "xiaohongshu", "bilibili_comment"}:
        return "community_context"
    if source_intent == "competitor_content":
        return "competitor_context"
    if source_intent == "editorial_content":
        return "editorial_context"
    if source_intent in {"forum_discussion", "social_comment"}:
        return "community_context"
    return "search_result"


def normalize_record(
    *,
    source: str,
    source_url: str,
    query: str,
    customer_segment: str,
    hypothesis: str,
    text: str,
    author_context: str = "",
    engagement: dict[str, Any] | None = None,
    raw_id: str = "",
    evidence_type: str | None = None,
    strength: str | None = None,
    relevance: str = "relevant",
    relevance_notes: str = "",
    relevance_score: int | None = None,
    confidence_notes: str | None = None,
    source_role_override: str | None = None,
    source_intent_override: str | None = None,
    published_at: str | None = None,
    source_language: str = "",
    source_entity_type: str = "",
    author_relationship: str = "",
    sampling_frame: str = "topic_led_voc",
    author_voice_status: str = "unreviewed",
    subject_entity_id: str = "",
    collection_source_lane: str = "",
    collection_locator: str = "",
) -> dict[str, Any]:
    engagement = engagement or {}
    short_quote = " ".join(text.split())[:500]
    record_type = evidence_type or infer_evidence_type(text)
    record_strength = strength or estimate_strength(text, engagement)
    source_intent = source_intent_override or ("customer_feedback" if source in {"itunes_reviews", "app_review", "google_places_review", "trustpilot_review"} else infer_source_intent(source, source_url, text, record_type))
    comment_intent = infer_comment_intent(source, text, record_type)
    if source_intent in {"competitor_content", "editorial_content", "official_provider", "search_demand", "forum_discussion"} and record_strength != "irrelevant":
        record_strength = "weak"
    stable_material = raw_id or source_url or "\n".join([source, short_quote])
    record = {
        "schema_version": "1.2",
        "source": source,
        "source_url": source_url,
        "retrieved_at": now_iso(),
        "query": query,
        "customer_segment": customer_segment,
        "segment_relation": "unresolved",
        "hypothesis_id": hypothesis,
        "evidence_type": record_type,
        "source_intent": source_intent,
        "classification_basis": "explicit_supplier_identity" if author_voice_status == "supplier_context" or source_role_override == "competitor_context" else "provider_structure" if source_intent_override or source in {"itunes_reviews", "app_review", "google_places_review", "trustpilot_review"} else "heuristic",
        "comment_intent": comment_intent,
        "text": text,
        "verbatim_quote": short_quote,
        "author_context": author_context,
        "source_record_id": str(stable_material),
        "evidence_id": f"ev-{hashlib.sha256(f'{source}|{stable_material}'.encode()).hexdigest()[:16]}",
        "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "canonical_url": source_url,
        "independence_key": "unknown:" + str(stable_material),
        "source_role": source_role_override or source_role(source, source_intent),
        "sampling_frame": sampling_frame,
        "discovery_memberships": [{"sampling_frame": sampling_frame, "query": query}],
        "author_voice_status": author_voice_status,
        "retrieval_backend": source,
        "capture_unit": "document" if source in {"web_search", "web", "firecrawl", "crawl4ai", "markitdown", "scrapling"} else "source_record",
        "content_completeness": "unknown",
        "sampling_metadata": {"sort_requested": None, "sort_actual": None, "rating_filter": None, "time_window": None, "product_version": None, "pages_retrieved": None, "accessible_total": None, "subset_limitations": "Provider selection and completeness not established; not a representative sample."},
        "engagement": {
            "upvotes": engagement_int(engagement.get("upvotes")) if engagement.get("upvotes") is not None else None,
            "comments": engagement_int(engagement.get("comments")) if engagement.get("comments") is not None else None,
            "views": engagement_int(engagement.get("views")) if engagement.get("views") is not None else None,
            "likes": engagement_int(engagement.get("likes")) if engagement.get("likes") is not None else None,
        },
        "strength": record_strength,
        "relevance": relevance,
        "relevance_score": relevance_score,
        "relevance_notes": relevance_notes,
        "confidence_notes": confidence_notes
        or "Collected directly from source API/search result. Treat as signal, not proof of willingness to pay.",
        "raw_id": raw_id,
    }
    if published_at: record["published_at"] = published_at
    if source_language: record["source_language"] = source_language
    if source_entity_type: record["source_entity_type"] = source_entity_type
    if author_relationship: record["author_relationship"] = author_relationship
    if subject_entity_id: record["subject_entity_id"] = subject_entity_id
    if collection_source_lane: record["collection_source_lane"] = collection_source_lane
    if collection_locator: record["collection_locator"] = collection_locator
    return record


def validate_instagram_entity_plan(args: argparse.Namespace) -> tuple[bool, str, list[tuple[str, str]]]:
    """Require exact, human-reviewed entity bindings for company Instagram profiles."""
    try:
        pairs = parse_entity_locator_pairs(getattr(args, "ig_handles", ""), "--ig-handles")
    except ValueError as exc:
        return False, str(exc), []
    if not pairs:
        return True, "not_requested", []
    allowed, reason = validate_entity_pairs_in_plan(args, pairs, "company_instagram_comments", "--ig-handles")
    if not allowed:
        return False, reason, []
    return True, "authorized", [(entity, handle.lstrip("@")) for entity, handle in pairs]


def runtime_locale(args: argparse.Namespace) -> str:
    country = str(getattr(args, "geo", "") or "").strip().upper()
    language = str(getattr(args, "language", "") or "").strip().casefold()
    return f"{country}:{language}" if re.fullmatch(r"[A-Z]{2}", country) and language not in {"", "auto"} else ""


def validate_entity_pairs_in_plan(args: argparse.Namespace, pairs: list[tuple[str, str]], lane: str, flag: str, requested_locales: list[str] | None = None) -> tuple[bool, str]:
    """Match entity locators to explicit human-accepted source-plan entries."""
    if not pairs:
        return True, "not_requested"
    plan_path = str(getattr(args, "customer_feedback_source_plan", "") or "").strip()
    if not plan_path:
        return False, f"{flag} requires --customer-feedback-source-plan with accepted {lane} locators"
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"invalid customer feedback source plan: {exc}"
    locales = requested_locales if requested_locales is not None else [runtime_locale(args)]
    locales = [locale for locale in locales if locale]
    if not locales:
        return False, f"{flag} requires an explicit COUNTRY:language locale binding"
    accepted: set[tuple[str, str, str]] = set()
    for row in plan.get("source_matrix", []):
        if row.get("source_lane") != lane or not row.get("applicable"):
            continue
        for reviewed in row.get("reviewed_locators", []):
            if isinstance(reviewed, dict) and reviewed.get("review_reason"):
                locator = str(reviewed.get("locator", "")).strip().lstrip("@").rstrip("/").casefold()
                if locator:
                    accepted.add((str(row.get("entity_id", "")), locator, str(row.get("locale", ""))))
    missing = [(entity, locator, locale) for entity, locator in pairs for locale in locales if (entity, locator.lstrip("@").rstrip("/").casefold(), locale) not in accepted]
    if missing:
        return False, "unreviewed entity locator/locale(s): " + ", ".join(f"{e}={locator}@{locale}" for e, locator, locale in missing)
    return True, "authorized"


def generic_entity_binding(args: argparse.Namespace) -> tuple[dict[str, str], str]:
    """Exact reviewed URL capture; a broad entity search is discovery, not binding."""
    if getattr(args, "sampling_frame", "topic_led_voc") != "entity_led_feedback": return {}, "not_requested"
    entity = str(getattr(args, "subject_entity_id", "") or "").strip()
    locator = str(getattr(args, "entity_source_url", "") or "").strip()
    lane = str(getattr(args, "entity_source_lane", "") or "").strip()
    if lane not in {"external_forums_communities", "independent_review_platforms", "company_hosted_supplier_context"}:
        return {}, "generic entity capture requires --entity-source-lane for a forum, independent review or supplier source"
    parsed = urllib.parse.urlparse(locator)
    if not entity or parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return {}, "generic entity capture requires --subject-entity-id and an exact --entity-source-url"
    if any(parsed.hostname.lower() == host or parsed.hostname.lower().endswith('.' + host) for host in ("facebook.com", "instagram.com")):
        return {}, "Facebook/Instagram targets require their dedicated reviewed collection route"
    allowed, reason = validate_entity_pairs_in_plan(args, [(entity, locator)], lane, "--entity-source-url")
    if not allowed: return {}, reason
    plan = json.loads(Path(args.customer_feedback_source_plan).read_text(encoding="utf-8"))
    exact = any(row.get("entity_id") == entity and row.get("locale") == runtime_locale(args) and row.get("source_lane") == lane and row.get("applicable") and any(reviewed.get("locator") == locator and reviewed.get("review_reason") for reviewed in row.get("reviewed_locators", []) if isinstance(reviewed, dict)) for row in plan.get("source_matrix", []))
    if not exact: return {}, "exact reviewed URL binding missing (URL paths are case-sensitive)"
    return {"subject_entity_id": entity, "collection_locator": locator, "collection_source_lane": lane, "collection_locale": runtime_locale(args), "sampling_frame": "entity_led_feedback"}, "authorized"


def collect_reviewed_entity_page(args: argparse.Namespace, run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    binding, reason = generic_entity_binding(args)
    if not binding: return [], {"status": "capture_gate_blocked", "reason": reason, "record_count": 0}
    key_name, key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    if not key: return [], {"status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}
    response = http_post("https://api.firecrawl.dev/v1/scrape", headers={"Authorization": f"Bearer {key}"}, data={"url": binding["collection_locator"], "formats": ["markdown"]})
    write_json(run_dir / "raw" / "firecrawl.json", redact_sensitive({"credential_source": key_name, "binding": binding, "response": response}))
    body = response.get("body") or {}
    data = body.get("data") or {} if isinstance(body, dict) else {}
    metadata = data.get("metadata") or {}
    returned_url = metadata.get("sourceURL") or metadata.get("url") or binding["collection_locator"]
    if returned_url.rstrip("/") != binding["collection_locator"].rstrip("/"):
        return [], {"status": "capture_gate_blocked", "reason": "returned page differs from reviewed target; review redirected source before use", "record_count": 0}
    content = str(data.get("markdown") or "")
    if not response.get("ok") or not content:
        return [], {"status": status_from_response(response) if not response.get("ok") else "empty", "record_count": 0}
    supplier = binding["collection_source_lane"] == "company_hosted_supplier_context"
    record = normalize_record(source="web_search", source_url=binding["collection_locator"], query="reviewed-source:" + binding["collection_locator"], customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=content, raw_id=binding["collection_locator"], author_context="Full extracted page; speakers and experience episodes require review", source_role_override="competitor_context" if supplier else None, author_voice_status="supplier_context" if supplier else "unreviewed", sampling_frame="entity_led_feedback", subject_entity_id=binding["subject_entity_id"])
    record.update(binding)
    record["content_completeness"] = "extracted_page"
    record["sampling_metadata"].update({"pages_retrieved": 1, "subset_limitations": "One reviewed URL; extraction may omit dynamic replies or other pages. Speaker boundaries not inferred."})
    return [record], {"status": "ok", "record_count": 1, "reviewed_binding": binding, "capture_ledger": [{"url": binding["collection_locator"], "attempted": True, "status": "ok"}]}


def normalized_published_at(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text: return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?", text): return text + "Z"
    return text


def accepted_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for record in records:
        errors = sorted(EVIDENCE_VALIDATOR.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            rejected.append({"source": str(record.get("source", "unknown")), "source_record_id": str(record.get("source_record_id", "")), "error": errors[0].message})
        else:
            accepted.append(record)
    return accepted, rejected


def app_market_relevant(topic: str, problem_keywords: str = "", workaround_keywords: str = "") -> bool:
    text = " ".join([topic, problem_keywords, workaround_keywords]).lower()
    markers = [
        "app",
        "apps",
        "mobile",
        "ios",
        "android",
        "app store",
        "play store",
        "google play",
        "aso",
    ]
    return any(marker in text for marker in markers)


def parse_sonar_apps(value: str) -> list[tuple[str, str]]:
    apps: list[tuple[str, str]] = []
    for raw_item in [item.strip() for item in value.split(",") if item.strip()]:
        item = raw_item.replace("=", ":")
        if ":" in item:
            store, app_id = item.split(":", 1)
        elif "/" in item:
            store, app_id = item.split("/", 1)
        else:
            continue
        store = store.strip().lower()
        app_id = app_id.strip()
        if store in {"ios", "android"} and app_id:
            apps.append((store, app_id))
    return apps


def split_document_paths(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def run_cli(command: list[str], *, timeout: int = 60) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "status": "timeout", "error": str(exc), "command": command}
    except OSError as exc:
        return {"ok": False, "status": "broken_cli", "error": str(exc), "command": command}
    return {
        "ok": proc.returncode == 0,
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "command": command,
    }


def local_discovery_urls(args: argparse.Namespace, queries: list[str], raw: dict[str, Any], *, provider: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Discover a small URL set for local extractors without pulling full pages into context."""
    max_urls = max(1, min(args.local_extract_url_limit, 8))
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    serper_key_name, serper_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
    key_name, brave_key = get_secret("BRAVE_SEARCH_API_KEY")
    firecrawl_key_name, firecrawl_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    raw["discovery_credential_source"] = serper_key_name or key_name or firecrawl_key_name
    raw["discovery_calls"] = []

    if serper_key:
        active_backend = "serper_search"
        for query in queries[:3]:
            response = http_post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                data={"q": query, "num": min(max_urls, 10), "gl": args.geo.lower(), "hl": args.language},
            )
            raw["discovery_calls"].append({"backend": active_backend, "query": query, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            for item in body.get("organic", []) if isinstance(body, dict) else []:
                url = item.get("link") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                records.append({"url": url, "query": query, "title": item.get("title", ""), "description": item.get("snippet", "")})
                if len(records) >= max_urls:
                    return records, {"status": "ok", "active_backend": active_backend, "discovered_count": len(records)}
    elif brave_key:
        active_backend = "brave_search"
        for query in queries[:3]:
            response = http_get(
                with_query(
                    "https://api.search.brave.com/res/v1/web/search",
                    {"q": query, "count": min(max_urls, 10), "country": args.geo, "search_lang": args.language},
                ),
                headers={"X-Subscription-Token": brave_key, "Accept": "application/json"},
            )
            raw["discovery_calls"].append({"backend": active_backend, "query": query, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            web = body.get("web", {}) if isinstance(body, dict) else {}
            for item in web.get("results", []) if isinstance(web, dict) else []:
                url = item.get("url") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                records.append({"url": url, "query": query, "title": item.get("title", ""), "description": item.get("description", "")})
                if len(records) >= max_urls:
                    return records, {"status": "ok", "active_backend": active_backend, "discovered_count": len(records)}
    elif firecrawl_key:
        active_backend = "firecrawl_search"
        for query in queries[:3]:
            response = http_post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {firecrawl_key}"},
                data={"query": query, "limit": max_urls},
            )
            raw["discovery_calls"].append({"backend": active_backend, "query": query, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            for item in body.get("data") or []:
                url = item.get("url") or item.get("sourceURL") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                records.append({"url": url, "query": query, "title": item.get("title", ""), "description": item.get("description", "")})
                if len(records) >= max_urls:
                    return records, {"status": "ok", "active_backend": active_backend, "discovered_count": len(records)}
    else:
        return [], {"status": "missing_credentials", "required_env": ["SERPER_DEV_API_KEY", "BRAVE_SEARCH_API_KEY", "FIRECRAWL_API_KEY_HGINVESTOR"]}

    first_response = (raw["discovery_calls"][0] or {}).get("response", {}) if raw["discovery_calls"] else {}
    status = "ok" if records else status_from_response(first_response) if first_response else "failed"
    return records, {"status": status, "active_backend": active_backend if "active_backend" in locals() else None, "discovered_count": len(records)}


def normalize_local_extraction_records(
    *,
    source: str,
    args: argparse.Namespace,
    run_dir: Path,
    extracted_items: list[dict[str, str]],
    raw: dict[str, Any],
    confidence_notes: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    char_limit = max(300, min(args.local_extract_char_limit, 4000))
    for item in extracted_items:
        text = " ".join((item.get("text") or "").split())
        if not text:
            continue
        text = text[:char_limit]
        url = item.get("url") or item.get("path") or ""
        query = item.get("query") or args.topic
        relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, source)
        records.append(
            normalize_record(
                source=source,
                source_url=url,
                query=query,
                customer_segment=args.customer_segment,
                hypothesis=args.hypothesis_id,
                text=text,
                author_context=item.get("author_context") or source,
                engagement={},
                raw_id=url,
                evidence_type="irrelevant" if relevance == "irrelevant" else None,
                strength="irrelevant" if relevance == "irrelevant" else None,
                relevance=relevance,
                relevance_notes=relevance_notes,
                relevance_score=relevance_score,
                confidence_notes=confidence_notes,
            )
        )
    write_json(run_dir / "raw" / f"{source}.json", redact_sensitive(raw))
    return records


def selected_providers(value: str) -> list[str]:
    defaults = ["reddit", "serpapi_google_trends", "youtube", "serper_search", "firecrawl", "brave_search", "hn", "github", "google_autocomplete"]
    social = ["x", "scrapecreators"]
    entity_reviews = ["trustpilot_reviews", "google_places_reviews", "itunes_reviews", "sonar"]
    local_web = ["crawl4ai"]
    china_public = ["china_bilibili", "china_v2ex", "china_web"]
    china_social = ["china_xiaohongshu"]
    if not value or value == "default":
        return defaults
    providers: list[str] = []
    for part in [item.strip() for item in value.split(",") if item.strip()]:
        if part == "default":
            providers.extend(defaults)
        elif part == "social":
            providers.extend(social)
        elif part == "entity_reviews":
            providers.extend(entity_reviews)
        elif part == "local_web":
            providers.extend(local_web)
        elif part == "free_community":
            providers.extend(["hn", "github", "google_autocomplete"])
        elif part == "china_public":
            providers.extend(china_public)
        elif part == "china_social":
            providers.extend(china_social)
        elif part == "china":
            providers.extend([*china_public, *china_social])
        elif part == "all":
            providers.extend([*defaults, *social])
        else:
            providers.append(part)
    deduped: list[str] = []
    for provider in providers:
        if provider not in deduped:
            deduped.append(provider)
    return deduped


def reddit_token() -> tuple[str | None, dict[str, Any]]:
    _, client_id = get_secret("REDDIT_CLIENT_ID")
    _, client_secret = get_secret("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None, {"status": "missing_credentials", "required_env": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]}
    response = http_post(
        "https://www.reddit.com/api/v1/access_token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}),
        basic_auth=(client_id, client_secret),
    )
    if not response.get("ok"):
        return None, response
    token = (response.get("body") or {}).get("access_token")
    return token, response


def collect_reddit(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    token, token_raw = reddit_token()
    raw: dict[str, Any] = {"token": token_raw, "searches": []}
    if not token:
        write_json(run_dir / "raw" / "reddit.json", redact_sensitive(raw))
        return [], {"status": status_from_response(token_raw) if token_raw.get("status_code") else "missing_credentials"}

    headers = {"Authorization": f"Bearer {token}", "User-Agent": "evidence-scout/0.1"}
    cutoff = time.time() - (args.days * 86400)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_query_limit = max(3, args.limit // max(1, min(len(queries), 5)))

    for query in reddit_queries(args, queries):
        response = http_get(
            with_query(
                "https://oauth.reddit.com/search",
                {"q": query, "limit": per_query_limit, "sort": "relevance", "type": "link"},
            ),
            headers=headers,
        )
        raw["searches"].append({"query": query, "response": response})
        children = (((response.get("body") or {}).get("data") or {}).get("children") or []) if response.get("ok") else []
        for child in children:
            data = child.get("data") or {}
            post_id = data.get("id") or data.get("name") or ""
            if not post_id or post_id in seen:
                continue
            if data.get("created_utc") and float(data["created_utc"]) < cutoff:
                continue
            seen.add(post_id)
            title = data.get("title") or ""
            body = data.get("selftext") or ""
            text = f"{title}\n\n{body}".strip()
            if not text:
                continue
            source_url = f"https://www.reddit.com{data.get('permalink', '')}"
            author_context = f"r/{data.get('subreddit', '')} u/{data.get('author', '')}"
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, source_url, author_context)
            records.append(
                normalize_record(
                    source="reddit",
                    source_url=source_url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context=author_context,
                    engagement={"upvotes": data.get("ups"), "comments": data.get("num_comments")},
                    raw_id=post_id,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    outcomes = [item["response"] for item in raw["searches"]]
    succeeded = sum(1 for response in outcomes if response.get("ok"))
    failed = [response for response in outcomes if not response.get("ok")]
    status = "ok" if succeeded and not failed else "partial" if succeeded else status_from_response(failed[0]) if failed else "failed"
    write_json(run_dir / "raw" / "reddit.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "request_count": len(outcomes), "successful_requests": succeeded, "failed_requests": len(failed), "fields": fields_present(raw)}


def collect_firecrawl(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if getattr(args, "sampling_frame", "topic_led_voc") == "entity_led_feedback":
        return collect_reviewed_entity_page(args, run_dir)
    key_name, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    if not api_key:
        write_json(run_dir / "raw" / "firecrawl.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    selected_queries = scheduled_queries(args, queries)
    per_query_limit = max(1, args.limit // max(1, len(selected_queries)))
    query_ledger: list[dict[str, Any]] = []
    credit_exhausted = False
    for position, query in enumerate(selected_queries):
        response = http_post(
            "https://api.firecrawl.dev/v1/search",
            headers={"Authorization": f"Bearer {api_key}"},
            data={"query": query, "limit": per_query_limit, "country": args.geo, "location": args.geo, "scrapeOptions": {"formats": ["markdown"]}},
        )
        raw["searches"].append({"query": query, "response": response})
        response_status = status_from_response(response)
        query_ledger.append({"query": query, "intent": query_intent(query), "locale": runtime_locale(args), "attempted": True, "status": response_status})
        if is_credit_exhaustion(response):
            credit_exhausted = True
            for skipped in selected_queries[position + 1:]:
                query_ledger.append({"query": skipped, "intent": query_intent(skipped), "locale": runtime_locale(args), "attempted": False, "status": "skipped:insufficient_credits"})
            break
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        for item in (body.get("data") or [])[:per_query_limit]:
            url = item.get("url") or item.get("sourceURL") or ""
            if url in seen:
                for record in records:
                    if record["source_url"] == url:
                        record["discovery_memberships"].append({"sampling_frame": "topic_led_voc", "query": query, "collection_locale": runtime_locale(args)})
            if not url or url in seen:
                continue
            seen.add(url)
            title = item.get("title") or ""
            description = item.get("description") or ""
            markdown = item.get("markdown") or ""
            text = str(markdown).strip() or "\n\n".join(part for part in [title, description] if part).strip()
            if not text:
                continue
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, item.get("siteName") or item.get("metadata", {}).get("siteName", ""))
            records.append(
                normalize_record(
                    source="web_search",
                    source_url=url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context=item.get("siteName") or item.get("metadata", {}).get("siteName", ""),
                    engagement={},
                    raw_id=url,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                )
            )
            records[-1]["content_completeness"] = "extracted_page" if markdown else "search_snippet"
            records[-1]["sampling_metadata"].update({"sort_requested": "provider_relevance", "pages_retrieved": 1, "per_query_result_limit": per_query_limit, "subset_limitations": "Search-ranked pages; dynamic replies and pagination may be absent. Document is not an attributed experience."})
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    attempted_queries = {item["query"] for item in query_ledger}
    query_ledger.extend({"query": query, "intent": query_intent(query), "locale": runtime_locale(args), "attempted": False, "status": "not_attempted:sample_limit"} for query in queries if query not in attempted_queries)
    failures = [item for item in query_ledger if item.get("attempted") and item["status"] != "ok"]
    status = "insufficient_credits" if credit_exhausted else "partial" if records and failures else "ok" if records else query_ledger[0]["status"] if query_ledger else "failed"
    write_json(run_dir / "raw" / "firecrawl.json", redact_sensitive(raw))
    summary = {"status": status, "record_count": len(records), "query_ledger": query_ledger, "fields": fields_present(raw)}
    if credit_exhausted:
        summary["top_up_url"] = "https://www.firecrawl.dev/app"
    return records, summary


def collect_serpapi_google_trends(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("SERPAPI_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name}
    if not api_key:
        write_json(run_dir / "raw" / "serpapi_google_trends.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SERPAPI_API_KEY"]}

    if args.days <= 31:
        trend_date = "today 1-m"
    elif args.days <= 93:
        trend_date = "today 3-m"
    elif args.days <= 365:
        trend_date = "today 12-m"
    else:
        trend_date = "today 5-y"
    terms = trend_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    q = ",".join(dict.fromkeys(term[:100] for term in terms if term.strip()).keys())[:500]
    response = http_get(
        with_query(
            "https://serpapi.com/search.json",
            {
                "engine": "google_trends",
                "q": q,
                "data_type": "TIMESERIES",
                "date": trend_date,
                "geo": args.geo,
                "api_key": api_key,
            },
        )
    )
    raw["response"] = response
    records: list[dict[str, Any]] = []
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    if response.get("ok"):
        averages = ((body.get("interest_over_time") or {}).get("averages") or [])
        timeline = ((body.get("interest_over_time") or {}).get("timeline_data") or [])
        text = (
            f"Google Trends demand proxy for `{q}` in geo `{args.geo}` over the last {args.days} days. "
            f"Averages: {json.dumps(averages, sort_keys=True)}. Timeline points: {len(timeline)}."
        )
        records.append(
            normalize_record(
                source="google_trends",
                source_url=(body.get("search_metadata") or {}).get("google_trends_url", ""),
                query=q,
                customer_segment=args.customer_segment,
                hypothesis=args.hypothesis_id,
                text=text,
                author_context="SerpAPI Google Trends",
                engagement={},
                raw_id=(body.get("search_metadata") or {}).get("id", ""),
                evidence_type="search_demand",
                strength="weak",
                confidence_notes="Google Trends is a directional search-interest proxy. It does not prove pain, urgency, or willingness to pay.",
            )
        )

    status = "ok" if records else status_from_response(response)
    write_json(run_dir / "raw" / "serpapi_google_trends.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


def collect_brave_search(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("BRAVE_SEARCH_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    if not api_key:
        write_json(run_dir / "raw" / "brave_search.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["BRAVE_SEARCH_API_KEY"]}

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in [queries[0], queries[3], queries[6]][:3]:
        response = http_get(
            with_query(
                "https://api.search.brave.com/res/v1/web/search",
                {"q": query, "count": min(max(args.limit, 1), 10), "country": args.geo, "search_lang": args.language},
            ),
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
        )
        raw["searches"].append({"query": query, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        web = body.get("web", {}) if isinstance(body, dict) else {}
        for item in web.get("results", []) if isinstance(web, dict) else []:
            url = item.get("url") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", "")] if part).strip()
            if not text:
                continue
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "Brave Search")
            records.append(
                normalize_record(
                    source="web_search",
                    source_url=url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context="Brave Search",
                    engagement={},
                    raw_id=url,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else status_from_response((raw["searches"][0] or {}).get("response", {})) if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "brave_search.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


def collect_hn(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Hacker News via the free Algolia API. No credentials required."""
    raw: dict[str, Any] = {"searches": []}
    cutoff = int(time.time() - (args.days * 86400))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_tag_limit = max(2, args.limit // 2)
    for tag in ["story", "comment"]:
        for query in [queries[0], queries[3], queries[6], queries[8]][:4]:
            response = http_get(
                with_query(
                    "https://hn.algolia.com/api/v1/search",
                    {
                        "query": query,
                        "tags": tag,
                        "hitsPerPage": min(per_tag_limit, 10),
                        "numericFilters": f"created_at_i>{cutoff}",
                    },
                )
            )
            raw["searches"].append({"query": query, "tags": tag, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            hits = body.get("hits", []) if isinstance(body.get("hits"), list) else []
            for hit in hits:
                object_id = hit.get("objectID") or ""
                url = hit.get("url") or (f"https://news.ycombinator.com/item?id={object_id}" if object_id else "")
                if not object_id or object_id in seen:
                    continue
                seen.add(object_id)
                title = hit.get("title") or hit.get("story_title") or ""
                text_body = hit.get("story_text") or hit.get("comment_text") or ""
                text = "\n\n".join(part for part in [title, text_body] if part).strip()
                if not text:
                    continue
                author_context = f"HN @{hit.get('author', '')} ({tag})"
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, author_context)
                records.append(
                    normalize_record(
                        source="hn",
                        source_url=url,
                        query=query,
                        customer_segment=args.customer_segment,
                        hypothesis=args.hypothesis_id,
                        text=text,
                        author_context=author_context,
                        engagement={"upvotes": hit.get("points"), "comments": hit.get("num_comments")},
                        raw_id=object_id,
                        evidence_type="irrelevant" if relevance == "irrelevant" else None,
                        strength="irrelevant" if relevance == "irrelevant" else None,
                        relevance=relevance,
                        relevance_notes=relevance_notes,
                        relevance_score=relevance_score,
                    )
                )
                if len(records) >= args.limit:
                    break
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else "failed" if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "hn.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


def collect_github(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """GitHub issue search via the free REST API. Optional GITHUB_TOKEN raises rate limits."""
    key_name, token = get_secret("GITHUB_TOKEN", "GH_TOKEN")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    cutoff_date = time.strftime("%Y-%m-%d", time.gmtime(time.time() - (args.days * 86400)))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_query_limit = max(2, args.limit // max(1, min(len(queries), 3)))
    for query in [queries[0], queries[3], queries[6]][:3]:
        search_q = f"{query} type:issue created:>={cutoff_date}"
        response = http_get(
            with_query(
                "https://api.github.com/search/issues",
                {"q": search_q, "sort": "reactions", "order": "desc", "per_page": min(per_query_limit, 10)},
            ),
            headers=headers,
        )
        raw["searches"].append({"query": search_q, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        items = body.get("items", []) if isinstance(body.get("items"), list) else []
        for item in items:
            html_url = item.get("html_url") or ""
            issue_id = str(item.get("id") or html_url)
            if not issue_id or issue_id in seen:
                continue
            seen.add(issue_id)
            text = "\n\n".join(part for part in [item.get("title", ""), item.get("body") or ""] if part).strip()
            if not text:
                continue
            repo = "/".join(html_url.split("/")[3:5]) if html_url.count("/") >= 4 else ""
            author_context = f"github.com/{repo}" if repo else "GitHub issue"
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, html_url, author_context)
            records.append(
                normalize_record(
                    source="github",
                    source_url=html_url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text[:4000],
                    author_context=author_context,
                    engagement={"upvotes": item.get("reactions", {}).get("+1") if isinstance(item.get("reactions"), dict) else None, "comments": item.get("comments")},
                    raw_id=issue_id,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else ("rate_limited" if any(s.get("response", {}).get("status_code") == 403 for s in raw["searches"]) else "failed") if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "github.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


def collect_google_autocomplete(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Google autocomplete suggestions. Free demand-language proxy; no credentials."""
    raw: dict[str, Any] = {"searches": []}
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    seeds = [queries[0], queries[3], queries[6], problem_first_terms(args.topic, args.problem_keywords, args.workaround_keywords)[0] if problem_first_terms(args.topic, args.problem_keywords, args.workaround_keywords) else args.topic][:4]
    for seed in seeds:
        response = http_get(
            with_query(
                "https://suggestqueries.google.com/complete/search",
                {"client": "firefox", "hl": args.language, "gl": args.geo.lower(), "q": seed},
            )
        )
        raw["searches"].append({"seed": seed, "response": response})
        body = response.get("body")
        suggestions = body[1] if isinstance(body, list) and len(body) > 1 and isinstance(body[1], list) else []
        for suggestion in suggestions:
            text = str(suggestion).strip()
            if not text or text.lower() in seen:
                continue
            seen.add(text.lower())
            records.append(
                normalize_record(
                    source="google_autocomplete",
                    source_url=f"https://www.google.com/search?q={urllib.parse.quote(text)}",
                    query=seed,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context="Google autocomplete",
                    engagement={},
                    raw_id=text,
                    confidence_notes="Autocomplete suggestion. Attention/language proxy only, never demand proof.",
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else "failed"
    write_json(run_dir / "raw" / "google_autocomplete.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


def collect_itunes_reviews(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Public Apple reviews with a per-app/store sample cap and explicit entity binding."""
    entity_apps = parse_entity_locator_pairs(getattr(args, "itunes_entity_apps", ""), "--itunes-entity-apps")
    app_ids = [("", part.strip()) for part in csv_terms(args.itunes_app_ids)]
    if app_ids:
        raw = {"apps": []}
        write_json(run_dir / "raw" / "itunes_reviews.json", raw)
        return [], {"status": "capture_gate_blocked", "reason": "targeted Apple reviews require --itunes-entity-apps and a reviewed source plan; --itunes-app-ids cannot produce topic-led VOC", "record_count": 0}
    requested_apps = entity_apps
    raw: dict[str, Any] = {"apps": []}
    if not requested_apps:
        write_json(run_dir / "raw" / "itunes_reviews.json", raw)
        return [], {"status": "not_run", "required_arg": "--itunes-entity-apps or --itunes-app-ids"}
    locale_values = [value.strip() for value in csv_terms(getattr(args, "itunes_locales", ""))]
    if entity_apps and not locale_values:
        write_json(run_dir / "raw" / "itunes_reviews.json", raw)
        return [], {"status": "capture_gate_blocked", "reason": "--itunes-entity-apps requires --itunes-locales COUNTRY:language for every storefront", "record_count": 0}
    if any(not re.fullmatch(r"[A-Za-z]{2}:[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", value) for value in locale_values):
        write_json(run_dir / "raw" / "itunes_reviews.json", raw)
        return [], {"status": "capture_gate_blocked", "reason": "invalid --itunes-locales value; use COUNTRY:language", "record_count": 0}
    normalized_locales = [value.split(":", 1)[0].upper() + ":" + value.split(":", 1)[1].casefold() for value in locale_values]
    allowed, reason = validate_entity_pairs_in_plan(args, entity_apps, "apple_app_store_reviews", "--itunes-entity-apps", normalized_locales)
    if not allowed:
        write_json(run_dir / "raw" / "itunes_reviews.json", raw)
        return [], {"status": "capture_gate_blocked", "reason": reason, "record_count": 0}
    countries = list(dict.fromkeys(locale.split(":", 1)[0].lower() for locale in normalized_locales))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    cutoff_days_seconds = args.days * 86400
    ledger: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for entity_id, app_id in requested_apps:
        app_id = app_id.split(":")[-1]
        for country in countries:
            country_locales = [locale for locale in normalized_locales if locale.startswith(country.upper() + ":")]
            lane_count = 0
            lane = {"entity_id": entity_id or None, "app_id": app_id, "country": country, "requested_locales": country_locales, "language_filter_supported": False, "language_coverage": "unresolved; RSS filters storefront, not language", "pages": [], "attempted": True, "retrieved_count": 0, "status": "empty"}
            page_fingerprints = set()
            for page in range(1, max(1, args.itunes_max_pages) + 1):
                response = http_get(
                    f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                )
                raw["apps"].append({"app_id": app_id, "country": country, "page": page, "response_status": response.get("status_code")})
                if not response.get("ok"):
                    lane["status"] = status_from_response(response)
                    failures.append({"entity_id": entity_id or None, "app_id": app_id, "country": country, "status": lane["status"]})
                    break
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                feed = body.get("feed", {}) if isinstance(body.get("feed"), dict) else {}
                entries = feed.get("entry", [])
                if not entries:
                    break
                entries = entries if isinstance(entries, list) else [entries]
                fingerprint = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
                lane["pages"].append({"page": page, "returned_entries": len(entries), "repeated_page": fingerprint in page_fingerprints})
                if fingerprint in page_fingerprints:
                    failures.append({"entity_id": entity_id, "app_id": app_id, "country": country, "status": "repeated_page", "page": page})
                    break
                page_fingerprints.add(fingerprint)
                for entry in entries:
                    review_id = ""
                    id_node = entry.get("id")
                    if isinstance(id_node, dict):
                        review_id = str(id_node.get("label") or "")
                    elif id_node:
                        review_id = str(id_node)
                    if not review_id or review_id in seen:
                        continue
                    seen.add(review_id)
                    updated = entry.get("updated", {})
                    updated_label = updated.get("label", "") if isinstance(updated, dict) else str(updated)
                    try:
                        review_ts = time.mktime(time.strptime(updated_label[:19], "%Y-%m-%dT%H:%M:%S"))
                    except (ValueError, TypeError):
                        review_ts = time.time()
                    if time.time() - review_ts > cutoff_days_seconds:
                        continue
                    title = entry.get("title", {}).get("label", "") if isinstance(entry.get("title"), dict) else ""
                    content = entry.get("content", {}).get("label", "") if isinstance(entry.get("content"), dict) else ""
                    rating = entry.get("im:rating", {}).get("label") if isinstance(entry.get("im:rating"), dict) else None
                    author = entry.get("author", {}).get("name", {}).get("label", "") if isinstance(entry.get("author"), dict) else ""
                    text = "\n\n".join(part for part in [title, content] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, f"app:{app_id}", "", f"{author} rating={rating}")
                    records.append(
                        normalize_record(
                            source="itunes_reviews",
                            source_url=f"https://apps.apple.com/{country}/app/id{app_id}",
                            query=f"app:{app_id}",
                            customer_segment=args.customer_segment,
                            hypothesis=args.hypothesis_id,
                            text=text,
                            author_context=f"{author} rating={rating}",
                            engagement={"likes": None},
                            raw_id=review_id,
                            evidence_type="irrelevant" if relevance == "irrelevant" else None,
                            strength="irrelevant" if relevance == "irrelevant" else None,
                            relevance=relevance,
                            relevance_notes=relevance_notes,
                            relevance_score=relevance_score,
                            sampling_frame="entity_led_feedback" if entity_id else "topic_led_voc",
                            author_voice_status="unreviewed",
                            subject_entity_id=entity_id,
                        )
                    )
                    records[-1]["collection_locale"] = country_locales[0] if len(country_locales) == 1 else country.upper() + ":und"
                    records[-1]["requested_locales"] = country_locales
                    records[-1]["observed_language"] = "unknown"
                    records[-1]["language_coverage"] = "storefront_only; review language must be inspected"
                    records[-1]["collection_source_lane"] = "apple_app_store_reviews"
                    records[-1]["collection_locator"] = app_id
                    records[-1]["sampling_metadata"].update({"sort_requested": "mostRecent", "time_window": {"lookback_days": args.days, "applied_by": "collector"}, "page_number": page, "requested_max_pages": args.itunes_max_pages, "record_limit": args.limit, "subset_limitations": "Recent storefront RSS slice; storefront is not author geography, dates missing from source remain unknown."})
                    if updated_label: records[-1]["published_at"] = updated_label
                    records[-1]["review_rating"] = rating
                    records[-1]["product_version"] = entry.get("im:version", {}).get("label") if isinstance(entry.get("im:version"), dict) else None
                    lane_count += 1
                    if lane_count >= args.limit:
                        break
                if lane_count >= args.limit:
                    break
            lane["retrieved_count"] = lane_count
            if lane_count:
                lane["status"] = "ok"
            ledger.append(lane)

    status = "partial" if failures and records else failures[0]["status"] if failures else "ok" if records else "no_recent_reviews"
    write_json(run_dir / "raw" / "itunes_reviews.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "entity_ledger": ledger, "failures": failures, "fields": fields_present(raw)}


def parse_entity_locator_pairs(value: str, flag: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for item in csv_terms(value):
        if "=" not in item:
            raise ValueError(f"{flag} entries must use entity_id=locator")
        entity_id, locator = (part.strip() for part in item.split("=", 1))
        if not entity_id or not locator:
            raise ValueError(f"{flag} entries must use entity_id=locator")
        pairs.append((entity_id, locator))
    return pairs


def parse_entity_store_apps(value: str, flag: str) -> list[tuple[str, str, str]]:
    triples: list[tuple[str, str, str]] = []
    for entity_id, locator in parse_entity_locator_pairs(value, flag):
        if ":" not in locator:
            raise ValueError(f"{flag} entries must use entity_id=ios:app_id or entity_id=android:package")
        store, app_id = locator.split(":", 1)
        if store not in {"ios", "android"} or not app_id.strip():
            raise ValueError(f"{flag} entries must use entity_id=ios:app_id or entity_id=android:package")
        triples.append((entity_id, store, app_id.strip()))
    return triples


def collect_trustpilot_reviews(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect public reviews bound to an exact Trustpilot business unit domain."""
    pairs = parse_entity_locator_pairs(getattr(args, "trustpilot_domains", ""), "--trustpilot-domains")
    raw: dict[str, Any] = {"entities": []}
    if not pairs:
        write_json(run_dir / "raw" / "trustpilot_reviews.json", raw)
        return [], {"status": "not_run", "required_arg": "--trustpilot-domains"}
    allowed, reason = validate_entity_pairs_in_plan(args, pairs, "independent_review_platforms", "--trustpilot-domains")
    if not allowed:
        return [], {"status": "capture_gate_blocked", "reason": reason, "record_count": 0}
    key_name, api_key = get_secret("TRUSTPILOT_API_KEY")
    if not api_key:
        return [], {"status": "missing_credentials", "required_env": ["TRUSTPILOT_API_KEY"]}
    records: list[dict[str, Any]] = []; failures: list[dict[str, Any]] = []
    for entity_id, domain in pairs:
        find = http_get(with_query("https://api.trustpilot.com/v1/business-units/find", {"name": domain}), headers={"apikey": api_key})
        business = find.get("body") if isinstance(find.get("body"), dict) else {}
        business_id = str(business.get("id") or "")
        ledger = {"entity_id": entity_id, "domain": domain, "business_unit_id": business_id or None, "find_http_status": find.get("status_code"), "pages": [], "retrieved_count": 0}
        raw["entities"].append(ledger)
        if not find.get("ok") or not business_id:
            failures.append({"entity_id": entity_id, "stage": "find_business_unit", "status": status_from_response(find)})
            continue
        token: str | None = None
        for _page in range(max(1, getattr(args, "trustpilot_max_pages", 2))):
            response = http_get(with_query(f"https://api.trustpilot.com/v1/business-units/{business_id}/all-reviews", {"pageToken": token} if token else {}), headers={"apikey": api_key})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            reviews = body.get("reviews") if isinstance(body.get("reviews"), list) else []
            ledger["pages"].append({"http_status": response.get("status_code"), "retrieved": len(reviews), "page_token_used": bool(token)})
            if not response.get("ok"):
                failures.append({"entity_id": entity_id, "stage": "reviews", "status": status_from_response(response)})
                break
            for review in reviews:
                text_value = "\n\n".join(str(review.get(key) or "").strip() for key in ("title", "text") if str(review.get(key) or "").strip())
                if not text_value: continue
                review_id = str(review.get("id") or hashlib.sha256(text_value.encode()).hexdigest())
                consumer = review.get("consumer") if isinstance(review.get("consumer"), dict) else {}
                record = normalize_record(source="trustpilot_review", source_url=f"https://www.trustpilot.com/review/{domain}", query=f"entity:{entity_id}", customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text_value, author_context=f"rating={review.get('stars')}; platform_verified={bool(review.get('isVerified'))}; reviewer={consumer.get('displayName') or 'unresolved'}", raw_id=review_id, published_at=normalized_published_at(review.get("createdAt")), source_language=str(review.get("language") or ""), confidence_notes="Public Trustpilot review for an entity-bound business unit. Platform verification does not establish target-segment fit; companyReply is supplier context and is not normalized as customer voice.", sampling_frame="entity_led_feedback", subject_entity_id=entity_id)
                record["subject_entity_id"] = entity_id; record["subject_entity_domain"] = domain; record["review_rating"] = review.get("stars"); record["platform_verified"] = bool(review.get("isVerified"))
                record["collection_source_lane"] = "independent_review_platforms"; record["collection_locator"] = domain
                record["sampling_metadata"].update({"page_number": _page + 1, "requested_max_pages": getattr(args, "trustpilot_max_pages", 2), "record_limit": args.limit, "returned_on_page": len(reviews), "platform_verified": bool(review.get("isVerified")), "review_provenance": review.get("source"), "subset_limitations": "API token-pagination slice; sort and solicitation provenance unknown unless supplied by platform."})
                records.append(record); ledger["retrieved_count"] += 1
                reply = review.get("companyReply") if isinstance(review.get("companyReply"), dict) else {}
                if str(reply.get("text") or "").strip():
                    supplier_record = normalize_record(source="trustpilot_review", source_url=f"https://www.trustpilot.com/review/{domain}", query=f"entity:{entity_id}", customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=str(reply["text"]), author_context=f"company reply to review {review_id}", raw_id=f"{review_id}:company-reply", published_at=normalized_published_at(reply.get("createdAt")), source_role_override="competitor_context", source_intent_override="competitor_content", confidence_notes="Supplier reply attached to a Trustpilot review; retain as service-response context, never customer voice.", sampling_frame="entity_led_feedback", author_voice_status="supplier_context", subject_entity_id=entity_id)
                    supplier_record["subject_entity_id"] = entity_id; supplier_record["subject_entity_domain"] = domain; supplier_record["responds_to_review_id"] = review_id
                    supplier_record["collection_source_lane"] = "independent_review_platforms"; supplier_record["collection_locator"] = domain
                    records.append(supplier_record)
                if ledger["retrieved_count"] >= args.limit: break
            if ledger["retrieved_count"] >= args.limit: break
            token = str(body.get("nextPageToken") or "") or None
            if not token: break
    status = "partial" if failures and records else status_from_response({"ok": False, "status_code": None, "body": failures}) if failures else "ok" if records else "empty"
    if failures and not records: status = failures[0]["status"]
    write_json(run_dir / "raw" / "trustpilot_reviews.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "credential_source": key_name, "entity_ledger": [{key: value for key, value in item.items() if key != "pages"} | {"pages": item["pages"]} for item in raw["entities"]], "failures": failures}


def collect_google_places_reviews(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect the API-returned review subset for exact Google Place IDs."""
    pairs = parse_entity_locator_pairs(getattr(args, "google_place_ids", ""), "--google-place-ids")
    raw: dict[str, Any] = {"entities": []}
    if not pairs:
        write_json(run_dir / "raw" / "google_places_reviews.json", raw)
        return [], {"status": "not_run", "required_arg": "--google-place-ids"}
    allowed, reason = validate_entity_pairs_in_plan(args, pairs, "google_business_reviews", "--google-place-ids")
    if not allowed:
        return [], {"status": "capture_gate_blocked", "reason": reason, "record_count": 0}
    key_name, api_key = get_secret("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return [], {"status": "missing_credentials", "required_env": ["GOOGLE_PLACES_API_KEY"]}
    records: list[dict[str, Any]] = []; failures: list[dict[str, Any]] = []; ledger: list[dict[str, Any]] = []
    for entity_id, place_id in pairs:
        url = with_query(f"https://places.googleapis.com/v1/places/{urllib.parse.quote(place_id, safe='')}", {"languageCode": args.language, "regionCode": args.geo})
        response = http_get(url, headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": "id,displayName,rating,userRatingCount,reviews,googleMapsUri"})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        reviews = body.get("reviews") if isinstance(body.get("reviews"), list) else []
        item_ledger = {"entity_id": entity_id, "place_id": place_id, "http_status": response.get("status_code"), "returned_review_count": len(reviews), "user_rating_count": body.get("userRatingCount"), "aggregate_rating": body.get("rating"), "api_subset_not_population": True}
        ledger.append(item_ledger); raw["entities"].append({**item_ledger, "response": response})
        if not response.get("ok"):
            failures.append({"entity_id": entity_id, "status": status_from_response(response)}); continue
        for review in reviews:
            text_node = review.get("originalText") or review.get("text") or {}
            text_value = str(text_node.get("text") or "") if isinstance(text_node, dict) else str(text_node or "")
            if not text_value: continue
            author = review.get("authorAttribution") if isinstance(review.get("authorAttribution"), dict) else {}
            review_id = str(review.get("name") or hashlib.sha256(f"{place_id}|{text_value}".encode()).hexdigest())
            source_url = str(review.get("googleMapsUri") or body.get("googleMapsUri") or f"https://www.google.com/maps/place/?q=place_id:{place_id}")
            record = normalize_record(source="google_places_review", source_url=source_url, query=f"entity:{entity_id}", customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text_value, author_context=f"rating={review.get('rating')}; reviewer={author.get('displayName') or 'unresolved'}", raw_id=review_id, published_at=review.get("publishTime") or None, source_language=str(text_node.get("languageCode") or "") if isinstance(text_node, dict) else "", confidence_notes="Review returned by Google Places for an exact Place ID. The API-returned subset and aggregate rating are not a representative VOC sample; target-segment fit requires review.", sampling_frame="entity_led_feedback", subject_entity_id=entity_id)
            record["subject_entity_id"] = entity_id; record["google_place_id"] = place_id; record["review_rating"] = review.get("rating")
            record["collection_source_lane"] = "google_business_reviews"; record["collection_locator"] = place_id
            record["sampling_metadata"].update({"pages_retrieved": 1, "returned_count": len(reviews), "platform_rating_count": body.get("userRatingCount"), "subset_limitations": "Provider-selected subset, not all reviews. Rating count is not accessible text count or independent customer count."})
            records.append(record)
    status = "partial" if failures and records else failures[0]["status"] if failures else "ok" if records else "empty"
    write_json(run_dir / "raw" / "google_places_reviews.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "credential_source": key_name, "entity_ledger": ledger, "failures": failures, "sampling_frame": "provider_selected_api_subset"}


def collect_serper_search(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if getattr(args, "sampling_frame", "topic_led_voc") == "entity_led_feedback":
        return [], {"status": "capture_gate_blocked", "reason": "Search is discovery only; use firecrawl with an exact reviewed --entity-source-url", "record_count": 0}
    key_name, api_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    if not api_key:
        write_json(run_dir / "raw" / "serper_search.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SERPER_DEV_API_KEY"]}

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    selected_queries = scheduled_queries(args, queries)
    per_query_limit = max(1, args.limit // max(1, len(selected_queries)))
    query_ledger: list[dict[str, Any]] = []
    for query in selected_queries:
        response = http_post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            data={"q": query, "num": min(per_query_limit, 10), "gl": args.geo.lower(), "hl": args.language},
        )
        raw["searches"].append({"query": query, "response": response})
        query_ledger.append({"query": query, "intent": query_intent(query), "locale": runtime_locale(args), "attempted": True, "status": status_from_response(response)})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        for item in (body.get("organic", []) if isinstance(body, dict) else [])[:per_query_limit]:
            url = item.get("link") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            text = "\n\n".join(part for part in [item.get("title", ""), item.get("snippet", "")] if part).strip()
            if not text:
                continue
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "Serper.dev")
            records.append(
                normalize_record(
                    source="web_search",
                    source_url=url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context="Serper.dev Google SERP",
                    engagement={},
                    raw_id=url,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                    confidence_notes="Collected via Serper.dev Google-only SERP. Use SerpApi/DataForSEO only for non-Google engines, edge-case parsers, or SEO-depth datasets.",
                )
            )
            records[-1]["content_completeness"] = "search_snippet"
            records[-1]["sampling_metadata"].update({"sort_requested": "provider_relevance", "per_query_result_limit": min(per_query_limit, 10), "subset_limitations": "Search snippet only; fetch original page before accepting an experience."})
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    failures = [entry for entry in query_ledger if entry["status"] != "ok"]
    status = "partial" if records and failures else "ok" if records else failures[0]["status"] if failures else "empty"
    write_json(run_dir / "raw" / "serper_search.json", redact_sensitive(raw))
    executed = {item["query"] for item in query_ledger}
    query_ledger.extend({"query": query, "intent": query_intent(query), "locale": runtime_locale(args), "attempted": False, "status": "not_attempted:sample_limit"} for query in queries if query not in executed)
    return records, {"status": status, "record_count": len(records), "query_ledger": query_ledger, "fields": fields_present(raw)}


def collect_crawl4ai(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: dict[str, Any] = {"extractor": "crawl4ai", "calls": []}
    cli = shutil.which("crwl")
    if not cli:
        write_json(run_dir / "raw" / "crawl4ai.json", raw)
        return [], {"status": "missing_cli", "required_cli": ["crwl"], "install_hint": "pip install crawl4ai && crawl4ai-setup"}

    urls, discovery_summary = local_discovery_urls(args, queries, raw, provider="crawl4ai")
    if not urls:
        write_json(run_dir / "raw" / "crawl4ai.json", redact_sensitive(raw))
        return [], {**discovery_summary, "record_count": 0}

    extracted: list[dict[str, str]] = []
    for item in urls:
        url = item["url"]
        response = run_cli([cli, url, "-o", "markdown"], timeout=args.local_extract_timeout)
        raw["calls"].append({"url": url, "query": item.get("query"), "response": response})
        if response.get("ok") and response.get("stdout"):
            extracted.append({**item, "text": response["stdout"], "author_context": "crawl4ai local markdown"})

    records = normalize_local_extraction_records(
        source="crawl4ai",
        args=args,
        run_dir=run_dir,
        extracted_items=extracted,
        raw=raw,
        confidence_notes="Collected by local crawl4ai after lightweight URL discovery. Treat as page evidence; inspect raw output before relying on extracted context.",
    )
    status = "ok" if records else "failed"
    if not extracted and raw["calls"]:
        status = (raw["calls"][0].get("response") or {}).get("status") or "failed"
    return records, {
        "status": status,
        "record_count": len([record for record in records if record.get("relevance") != "irrelevant"]),
        "active_backend": discovery_summary.get("active_backend"),
        "discovered_count": discovery_summary.get("discovered_count", 0),
        "extracted_count": len(extracted),
        "fields": fields_present(raw),
    }


def collect_markitdown(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: dict[str, Any] = {"extractor": "markitdown", "calls": []}
    paths = split_document_paths(args.document_paths)
    if not paths:
        write_json(run_dir / "raw" / "markitdown.json", raw)
        return [], {"status": "no_input", "record_count": 0, "required_arg": "--document-paths"}

    cli = shutil.which("markitdown")
    if not cli:
        write_json(run_dir / "raw" / "markitdown.json", raw)
        return [], {"status": "missing_cli", "required_cli": ["markitdown"], "install_hint": "pip install 'markitdown[all]'"}

    extracted: list[dict[str, str]] = []
    for raw_path in paths[: max(1, min(args.document_limit, 12))]:
        is_url = raw_path.startswith(("http://", "https://"))
        path = raw_path if is_url else str((Path(raw_path).expanduser()).resolve())
        if not is_url and not Path(path).exists():
            raw["calls"].append({"path": raw_path, "response": {"ok": False, "status": "not_found", "error": "Document path does not exist"}})
            continue
        response = run_cli([cli, path], timeout=args.local_extract_timeout)
        raw["calls"].append({"path": raw_path, "resolved_path": path, "response": response})
        if response.get("ok") and response.get("stdout"):
            source_url = path if is_url else Path(path).as_uri()
            extracted.append({"path": raw_path, "url": source_url, "query": args.topic, "text": response["stdout"], "author_context": "markitdown document conversion"})

    records = normalize_local_extraction_records(
        source="markitdown",
        args=args,
        run_dir=run_dir,
        extracted_items=extracted,
        raw=raw,
        confidence_notes="Converted from user-supplied document path/URL with MarkItDown. Treat as document evidence and verify document provenance.",
    )
    status = "ok" if records else "failed"
    if not extracted and raw["calls"]:
        status = (raw["calls"][0].get("response") or {}).get("status") or "failed"
    return records, {
        "status": status,
        "record_count": len([record for record in records if record.get("relevance") != "irrelevant"]),
        "input_count": len(paths),
        "converted_count": len(extracted),
        "fields": fields_present(raw),
    }


def collect_scrapling(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: dict[str, Any] = {"extractor": "scrapling", "calls": []}
    cli = shutil.which("scrapling")
    if not cli:
        write_json(run_dir / "raw" / "scrapling.json", raw)
        return [], {"status": "missing_cli", "required_cli": ["scrapling"], "install_hint": "pip install 'scrapling[fetchers]' && scrapling install"}

    urls, discovery_summary = local_discovery_urls(args, queries, raw, provider="scrapling")
    if not urls:
        write_json(run_dir / "raw" / "scrapling.json", redact_sensitive(raw))
        return [], {**discovery_summary, "record_count": 0}

    page_dir = run_dir / "raw" / "scrapling_pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, str]] = []
    for idx, item in enumerate(urls, start=1):
        url = item["url"]
        out_file = page_dir / f"{idx}.md"
        response = run_cli([cli, "extract", "fetch", url, str(out_file)], timeout=args.local_extract_timeout)
        if not response.get("ok"):
            fallback = run_cli([cli, "extract", "get", url, str(out_file)], timeout=args.local_extract_timeout)
            response = {**response, "fallback_response": fallback}
        raw["calls"].append({"url": url, "query": item.get("query"), "output_file": str(out_file), "response": response})
        if out_file.exists() and out_file.stat().st_size:
            text = out_file.read_text(encoding="utf-8", errors="replace")
            extracted.append({**item, "text": text, "author_context": "scrapling local extraction"})

    records = normalize_local_extraction_records(
        source="scrapling",
        args=args,
        run_dir=run_dir,
        extracted_items=extracted,
        raw=raw,
        confidence_notes="Collected by local Scrapling fallback after lightweight URL discovery. Use only for hard pages where normal providers are insufficient.",
    )
    status = "ok" if records else "failed"
    if not extracted and raw["calls"]:
        status = (raw["calls"][0].get("response") or {}).get("status") or "failed"
    return records, {
        "status": status,
        "record_count": len([record for record in records if record.get("relevance") != "irrelevant"]),
        "active_backend": discovery_summary.get("active_backend"),
        "discovered_count": discovery_summary.get("discovered_count", 0),
        "extracted_count": len(extracted),
        "fields": fields_present(raw),
    }


YOUTUBE_TRANSCRIPT_MAX_CHARS = 6000


def fetch_youtube_transcript(video_id: str, languages: list[str]) -> tuple[str, str]:
    """Return (status, text) for a video transcript via youtube_transcript_api.

    Status is one of: ok, disabled, unavailable, missing_module, error.
    Free (no API quota) but YouTube can IP-throttle; keep volumes low.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            IpBlocked,
            NoTranscriptFound,
            RequestBlocked,
            TranscriptsDisabled,
            VideoUnavailable,
        )
    except ImportError:
        return "missing_module", ""
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    except TranscriptsDisabled:
        return "disabled", ""
    except (NoTranscriptFound, VideoUnavailable):
        return "unavailable", ""
    except (IpBlocked, RequestBlocked):
        return "blocked", ""
    except Exception as exc:  # noqa: BLE001 - library raises several HTTP-era errors
        return f"error:{type(exc).__name__}", ""
    text = " ".join(segment.text.strip() for segment in fetched if segment.text.strip())
    return "ok", " ".join(text.split())[:YOUTUBE_TRANSCRIPT_MAX_CHARS]


def collect_youtube(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("YOUTUBE_API_KEY", "GOOGLE_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": [], "comments": [], "transcripts": []}
    if not api_key:
        write_json(run_dir / "raw" / "youtube.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["YOUTUBE_API_KEY"]}

    records: list[dict[str, Any]] = []
    seen_videos: set[str] = set()
    transcripts_attempted = 0
    transcripts_fetched = 0
    transcript_max = max(0, getattr(args, "youtube_transcript_max", 5))
    for query in [queries[0], queries[2], queries[5]][:3]:
        search_response = http_get(
            with_query(
                "https://www.googleapis.com/youtube/v3/search",
                {"part": "snippet", "q": query, "type": "video", "maxResults": min(max(args.limit, 1), 5), "key": api_key},
            )
        )
        raw["searches"].append({"query": query, "response": search_response})
        items = (search_response.get("body") or {}).get("items", []) if search_response.get("ok") else []
        for item in items:
            video_id = (item.get("id") or {}).get("videoId")
            if not video_id or video_id in seen_videos:
                continue
            seen_videos.add(video_id)
            snippet = item.get("snippet") or {}
            url = f"https://www.youtube.com/watch?v={video_id}"
            text = "\n\n".join(part for part in [snippet.get("title", ""), snippet.get("description", "")] if part).strip()
            if text:
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, snippet.get("channelTitle", ""))
                records.append(
                    normalize_record(
                        source="youtube",
                        source_url=url,
                        query=query,
                        customer_segment=args.customer_segment,
                        hypothesis=args.hypothesis_id,
                        text=text,
                        author_context=snippet.get("channelTitle", ""),
                        engagement={},
                        raw_id=video_id,
                        evidence_type="irrelevant" if relevance == "irrelevant" else None,
                        strength="irrelevant" if relevance == "irrelevant" else None,
                        relevance=relevance,
                        relevance_notes=relevance_notes,
                        relevance_score=relevance_score,
                    )
                )
            comments_response = http_get(
                with_query(
                    "https://www.googleapis.com/youtube/v3/commentThreads",
                    {
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": min(5, max(args.limit, 1)),
                        "textFormat": "plainText",
                        "key": api_key,
                    },
                )
            )
            raw["comments"].append({"video_id": video_id, "response": comments_response})
            if comments_response.get("ok"):
                for comment in (comments_response.get("body") or {}).get("items", []):
                    top = (((comment.get("snippet") or {}).get("topLevelComment") or {}).get("snippet") or {})
                    comment_text = top.get("textDisplay") or top.get("textOriginal") or ""
                    if not comment_text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(comment_text, args, query, url, top.get("authorDisplayName", ""))
                    records.append(
                        normalize_record(
                            source="youtube_comment",
                            source_url=url,
                            query=query,
                            customer_segment=args.customer_segment,
                            hypothesis=args.hypothesis_id,
                            text=comment_text,
                            author_context=top.get("authorDisplayName", ""),
                            engagement={"likes": top.get("likeCount")},
                            raw_id=comment.get("id", ""),
                            evidence_type="irrelevant" if relevance == "irrelevant" else None,
                            strength="irrelevant" if relevance == "irrelevant" else None,
                            relevance=relevance,
                            relevance_notes=relevance_notes,
                            relevance_score=relevance_score,
                        )
                    )
                    if len(records) >= args.limit:
                        break
            if getattr(args, "youtube_transcripts", False) and transcripts_attempted < transcript_max:
                transcripts_attempted += 1
                transcript_status, transcript_text = fetch_youtube_transcript(video_id, [args.language, "en"])
                raw["transcripts"].append({"video_id": video_id, "status": transcript_status, "chars": len(transcript_text)})
                if transcript_status == "ok" and transcript_text:
                    transcripts_fetched += 1
                    full_text = f"Transcript of video \"{snippet.get('title', '')}\": {transcript_text}"
                    relevance, relevance_notes, relevance_score = assess_relevance(full_text, args, query, url, snippet.get("channelTitle", ""))
                    records.append(
                        normalize_record(
                            source="youtube_transcript",
                            source_url=url,
                            query=query,
                            customer_segment=args.customer_segment,
                            hypothesis=args.hypothesis_id,
                            text=full_text,
                            author_context=snippet.get("channelTitle", ""),
                            engagement={},
                            raw_id=f"{video_id}:transcript",
                            evidence_type="irrelevant" if relevance == "irrelevant" else None,
                            strength="irrelevant" if relevance == "irrelevant" else None,
                            relevance=relevance,
                            relevance_notes=relevance_notes,
                            relevance_score=relevance_score,
                            confidence_notes="Creator-voice transcript via youtube_transcript_api (free, no API quota). A transcript is the creator's narrative, not independent customer voice; mine it for quoted user stories, mentioned workarounds, and linked products, never as demand proof.",
                        )
                    )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else status_from_response((raw["searches"][0] or {}).get("response", {})) if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "youtube.json", redact_sensitive(raw))
    summary: dict[str, Any] = {"status": status, "record_count": len(records), "fields": fields_present(raw)}
    if getattr(args, "youtube_transcripts", False):
        transcript_statuses: dict[str, int] = {}
        for entry in raw["transcripts"]:
            key = str(entry.get("status", "unknown")).split(":")[0]
            transcript_statuses[key] = transcript_statuses.get(key, 0) + 1
        summary["transcripts"] = {"attempted": transcripts_attempted, "fetched": transcripts_fetched, "statuses": transcript_statuses}
    return records, summary


def collect_x(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, bearer = get_secret("X_BEARER_TOKEN", "TWITTER_BEARER_TOKEN")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    if not bearer:
        write_json(run_dir / "raw" / "x.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["X_BEARER_TOKEN"]}

    terms = social_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    quoted_terms = " OR ".join(f'"{term}"' for term in terms[:2])
    query = f'({quoted_terms}) -is:retweet lang:{args.language}'
    response = http_get(
        with_query(
            "https://api.x.com/2/tweets/search/recent",
            {"query": query, "max_results": 10, "tweet.fields": "created_at,public_metrics,lang,author_id"},
        ),
        headers={"Authorization": f"Bearer {bearer}"},
    )
    raw["searches"].append({"query": query, "response": response})
    records: list[dict[str, Any]] = []
    if response.get("ok"):
        for tweet in (response.get("body") or {}).get("data", [])[: args.limit]:
            metrics = tweet.get("public_metrics") or {}
            text = tweet.get("text", "")
            source_url = f"https://x.com/i/web/status/{tweet.get('id', '')}"
            author_context = f"author_id:{tweet.get('author_id', '')}"
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, source_url, author_context)
            records.append(
                normalize_record(
                    source="x",
                    source_url=source_url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context=author_context,
                    engagement={"likes": metrics.get("like_count"), "comments": metrics.get("reply_count")},
                    raw_id=tweet.get("id", ""),
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                )
            )
    status = "ok" if response.get("ok") else status_from_response(response)
    write_json(run_dir / "raw" / "x.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


def extract_xai_text(body: Any) -> str:
    if not isinstance(body, dict):
        return ""
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    parts: list[str] = []
    for item in body.get("output", []) if isinstance(body.get("output"), list) else []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) if isinstance(item.get("content"), list) else []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    return "\n".join(parts)


def collect_xai_x_search(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("GROK_API_KEY", "XAI_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "calls": []}
    if not api_key:
        write_json(run_dir / "raw" / "xai_x_search.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["GROK_API_KEY"]}

    terms = social_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    prompt = args.xai_prompt or (
        "Search X for recent public posts about this business research topic. "
        "Focus on direct customer complaints, workarounds, buyer objections, investor/operator disagreement, and repeated themes. "
        "Return cited post URLs and separate evidence from interpretation. "
        f"Topic: {args.topic}. Segment: {args.customer_segment}. Search terms: {', '.join(terms[:4])}."
    )
    tool: dict[str, Any] = {"type": "x_search"}
    handles = [handle.strip().lstrip("@") for handle in args.x_handles.split(",") if handle.strip()]
    if handles:
        tool["allowed_x_handles"] = handles[:20]
    if args.x_from_date:
        tool["from_date"] = args.x_from_date
    if args.x_to_date:
        tool["to_date"] = args.x_to_date
    response = http_post(
        "https://api.x.ai/v1/responses",
        headers={"Authorization": f"Bearer {api_key}"},
        data={"model": args.xai_model, "input": [{"role": "user", "content": prompt}], "tools": [tool]},
        timeout=90,
    )
    raw["calls"].append({"prompt": prompt, "tool": tool, "response": response})
    records: list[dict[str, Any]] = []
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    citations = body.get("citations", []) if isinstance(body, dict) else []
    text = extract_xai_text(body)
    citation_text = "\n".join(str(item) for item in citations[:20])
    if response.get("ok") and (text or citation_text):
        source_url = str(citations[0]) if citations else "https://docs.x.ai/developers/tools/x-search"
        combined = "\n\n".join(part for part in [text, f"Citations:\n{citation_text}" if citation_text else ""] if part)
        records.append(
            normalize_record(
                source="xai_x_search",
                source_url=source_url,
                query=prompt,
                customer_segment=args.customer_segment,
                hypothesis=args.hypothesis_id,
                text=combined,
                author_context="Grok/xAI X Search cited discovery",
                engagement={},
                raw_id=str(body.get("id") or source_url),
                evidence_type="community",
                strength="weak",
                relevance="relevant",
                relevance_notes="Model-mediated X Search discovery; verify cited posts before using claims.",
                relevance_score=1,
                confidence_notes="Grok/xAI X Search is a discovery layer. Underlying cited X posts must be inspected before treating anything as evidence.",
            )
        )
    status = "ok" if response.get("ok") else status_from_response(response)
    write_json(run_dir / "raw" / "xai_x_search.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "citation_count": len(citations), "fields": fields_present(body)}


def list_candidates(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    for key in ["search_item_list", "items", "results", "data", "reels", "videos", "posts", "comments"]:
        child = value.get(key)
        if isinstance(child, list):
            return child
    return []


def stringify_social_item(item: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    aweme = item.get("aweme_info") if isinstance(item.get("aweme_info"), dict) else item
    title = aweme.get("desc") or aweme.get("title") or aweme.get("caption") or aweme.get("text") or aweme.get("description") or ""
    url = aweme.get("url") or aweme.get("webVideoUrl") or aweme.get("video_url") or aweme.get("link") or aweme.get("permalink") or ""
    stats = aweme.get("statistics") or aweme.get("stats") or {}
    engagement = {
        "views": stats.get("play_count") or stats.get("viewCount") or aweme.get("views") or aweme.get("view_count"),
        "likes": stats.get("digg_count") or stats.get("like_count") or aweme.get("likes") or aweme.get("likeCount"),
        "comments": stats.get("comment_count") or aweme.get("comments") or aweme.get("commentCount"),
    }
    raw_id = str(aweme.get("aweme_id") or aweme.get("id") or aweme.get("shortcode") or url)
    return title, url, engagement, raw_id


def stringify_twitter_item(item: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    text = item.get("text") or item.get("full_text") or item.get("content") or item.get("description") or ""
    url = item.get("url") or item.get("twitterUrl") or item.get("xUrl") or item.get("link") or ""
    metrics = item.get("public_metrics") or item.get("metrics") or item
    engagement = {
        "views": metrics.get("view_count") or metrics.get("views") or metrics.get("viewCount"),
        "likes": metrics.get("like_count") or metrics.get("likeCount") or metrics.get("likes"),
        "comments": metrics.get("reply_count") or metrics.get("replyCount") or metrics.get("replies"),
    }
    raw_id = str(item.get("id") or item.get("tweetId") or item.get("rest_id") or url)
    return text, url, engagement, raw_id


def stringify_facebook_item(item: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    text = item.get("text") or item.get("message") or item.get("caption") or ""
    url = item.get("url") or item.get("link") or item.get("post_url") or item.get("permalink") or ""
    comments = item.get("comments_count") or item.get("comment_count") or item.get("comments")
    engagement = {
        "views": item.get("views") or item.get("view_count"),
        "likes": item.get("likes") or item.get("like_count") or item.get("reactions"),
        "comments": len(comments) if isinstance(comments, list) else comments,
    }
    raw_id = str(item.get("id") or item.get("post_id") or url or text[:80])
    return text, url, engagement, raw_id


def facebook_item_context(item: dict[str, Any], endpoint_context: str) -> dict[str, str]:
    author = item.get("author") or item.get("from") or item.get("user") or item.get("owner") or {}
    if isinstance(author, dict): author_label = str(author.get("name") or author.get("username") or author.get("id") or "")
    else: author_label = str(author or "")
    published = item.get("published_at") or item.get("created_time") or item.get("timestamp") or item.get("time") or ""
    if isinstance(published, (int, float)):
        published = datetime.fromtimestamp(published, tz=timezone.utc).replace(microsecond=0).isoformat()
    elif published:
        try: published = datetime.fromisoformat(str(published).replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError: published = ""
    is_page = endpoint_context.startswith(("ScrapeCreators fb-page", "ScrapeCreators fb-entity:"))
    author_type = " ".join(str(author.get(key, "")) for key in ("type", "category", "role") if isinstance(author, dict)).casefold()
    supplier_author = bool(isinstance(author, dict) and (author.get("is_page") or author.get("is_admin") or author.get("is_business"))) or any(token in author_type for token in ("page", "admin", "business", "organization", "vendor"))
    supplier_context = is_page or supplier_author
    return {"author_label": author_label, "published_at": str(published), "source_entity_type": "facebook_page" if supplier_context else "facebook_group", "author_relationship": "page_or_supplier_author" if supplier_context else "group_participant_unverified", "source_role": "competitor_context" if supplier_context else "community_context", "source_intent": "competitor_content" if supplier_context else "forum_discussion"}


def stringify_instagram_item(item: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    caption = item.get("caption") or item.get("text") or ""
    if isinstance(caption, dict):
        caption = caption.get("text") or ""
    url = item.get("url") or item.get("permalink") or ""
    if not url and item.get("shortcode"):
        url = f"https://www.instagram.com/p/{item['shortcode']}/"
    comments = item.get("comment_count") or item.get("comments")
    engagement = {
        "views": item.get("views") or item.get("view_count") or item.get("video_view_count"),
        "likes": item.get("likes") or item.get("like_count"),
        "comments": len(comments) if isinstance(comments, list) else comments,
    }
    raw_id = str(item.get("id") or item.get("shortcode") or url or str(caption)[:80])
    return str(caption), url, engagement, raw_id


def stringify_social_comment(item: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    text = item.get("text") or item.get("content") or item.get("comment") or ""
    if isinstance(text, dict):
        text = text.get("text") or ""
    url = item.get("url") or item.get("link") or ""
    engagement = {"views": None, "likes": item.get("likes") or item.get("like_count"), "comments": None}
    raw_id = str(item.get("id") or item.get("comment_id") or url or str(text)[:80])
    return str(text), url, engagement, raw_id


def social_comment_context(item: dict[str, Any], source: str, supplier_identity: str = "") -> dict[str, str]:
    author = item.get("author") or item.get("from") or item.get("user") or item.get("owner") or {}
    author_label = str(author.get("name") or author.get("username") or author.get("id") or "") if isinstance(author, dict) else str(author or "")
    author_type = " ".join(str(author.get(key, "")) for key in ("type", "category", "role") if isinstance(author, dict)).casefold()
    normalized_author = author_label.strip().lstrip("@").casefold()
    normalized_supplier = supplier_identity.strip().lstrip("@").casefold()
    supplier = bool(normalized_supplier and normalized_author == normalized_supplier) or bool(isinstance(author, dict) and (author.get("is_page") or author.get("is_admin") or author.get("is_business"))) or any(token in author_type for token in ("page", "admin", "business", "organization", "vendor"))
    return {
        "author_label": author_label,
        "source_role": "competitor_context" if supplier else "community_context",
        "source_intent": "competitor_content" if supplier else "social_comment",
        "source_entity_type": f"{source}_supplier_comment" if supplier else f"{source}_comment",
        "author_relationship": "page_or_supplier_author" if supplier else "commenter_unverified",
    }


def scrapecreators_paginate(
    endpoint: str,
    params: dict[str, Any],
    api_key: str,
    items_key: str,
    cursor_key: str,
    max_items: int,
    raw_calls: list[dict[str, Any]],
    source: str,
) -> tuple[list[Any], str]:
    items: list[Any] = []
    cursor: str | None = None
    while len(items) < max_items:
        call_params = dict(params)
        if cursor:
            call_params[cursor_key] = cursor
        response = http_get(with_query(endpoint, call_params), headers={"x-api-key": api_key})
        raw_calls.append({"source": source, "endpoint": endpoint, "params": call_params, "response": response})
        if not response.get("ok"):
            if response.get("status_code") == 404:
                return items, "http_404:not_accessible_or_unsupported"
            return items, status_from_response(response)
        body = response.get("body") or {}
        page = body.get(items_key) or []
        if not page:
            break
        items.extend(page)
        new_cursor = body.get(cursor_key)
        if not new_cursor or new_cursor == cursor:
            break
        cursor = new_cursor
    return items[:max_items], "ok" if items else "empty"


def validate_facebook_capture_authorization(args: argparse.Namespace) -> tuple[bool, str, dict[str, Any]]:
    entity_pages = parse_entity_locator_pairs(getattr(args, "fb_entity_pages", ""), "--fb-entity-pages")
    requested = [(item.strip().rstrip("/"), family) for value, family in ((getattr(args, "fb_groups", ""), "facebook_group_posts"), (getattr(args, "fb_pages", ""), "facebook_page_posts")) for item in value.split(",") if item.strip()]
    requested.extend((url.rstrip("/"), "facebook_page_posts") for _entity, url in entity_pages)
    targets = [item[0] for item in requested]
    if not targets:
        return True, "not_applicable", {}
    if len(targets) != len(set(targets)):
        return False, "The same Facebook target cannot be supplied to multiple endpoint families.", {}
    path = getattr(args, "community_capture_authorization", "")
    verified_path = getattr(args, "community_verified_sources", "")
    receipt_path = getattr(args, "community_review_receipt", "")
    if not path or not verified_path or not receipt_path:
        return False, "Facebook targets require the authorization, verified sources, and current receipt emitted by review_community_candidates.py.", {}
    try:
        packet = json.loads(Path(path).read_text(encoding="utf-8"))
        verified = json.loads(Path(verified_path).read_text(encoding="utf-8"))
        receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        state_dir = Path(os.environ.get("COMMUNITY_REVIEW_STATE_DIR", ROOT / "projects" / "_infra" / "community-review-state"))
        current_state = json.loads((state_dir / f"{packet.get('state_id', '')}.json").read_text(encoding="utf-8"))
        generated_at = datetime.fromisoformat(str(packet.get("generated_at", "")).replace("Z", "+00:00"))
        if generated_at.tzinfo is None: generated_at = generated_at.replace(tzinfo=timezone.utc)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        return False, f"Invalid Facebook capture authorization: {exc}", {}
    key = os.environ.get("COMMUNITY_REVIEW_PUBLIC_KEY_B64", "")
    def digest(value: Any) -> str: return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    def signature_valid(value: dict[str, Any]) -> bool:
        signature = value.get("signature", ""); unsigned = {name: item for name, item in value.items() if name != "signature"}
        try:
            public_raw = base64.b64decode(key); Ed25519PublicKey.from_public_bytes(public_raw).verify(base64.b64decode(str(signature)), json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
            return value.get("key_id") == hashlib.sha256(public_raw).hexdigest()
        except Exception: return False
    schema_checks = {
        "authorization_schema": not list(COMMUNITY_AUTH_VALIDATOR.iter_errors(packet)),
        "verified_schema": not list(VERIFIED_COMMUNITY_VALIDATOR.iter_errors(verified)),
        "receipt_schema": not list(COMMUNITY_RECEIPT_VALIDATOR.iter_errors(receipt)),
    }
    canonical_verified_digest = hashlib.sha256(json.dumps(verified, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    target_records = {str(item.get("url", "")).strip().rstrip("/"): item for item in packet.get("targets", []) if isinstance(item, dict)}
    verified_records = {str(item.get("url", "")).strip().rstrip("/"): item for item in verified if isinstance(item, dict)}
    now = datetime.now(timezone.utc)
    target_checks: dict[str, bool] = {}
    requested_families = dict(requested)
    for target in targets:
        authorization, source = target_records.get(target, {}), verified_records.get(target, {})
        try:
            reviewed_at = datetime.fromisoformat(str(authorization.get("reviewed_at", "")).replace("Z", "+00:00")); valid_until = datetime.fromisoformat(str(authorization.get("valid_until", "")).replace("Z", "+00:00"))
            if reviewed_at.tzinfo is None: reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)
            if valid_until.tzinfo is None: valid_until = valid_until.replace(tzinfo=timezone.utc)
            fresh = timedelta(0) <= now - reviewed_at.astimezone(timezone.utc) <= timedelta(days=30) and now < valid_until.astimezone(timezone.utc) <= reviewed_at.astimezone(timezone.utc) + timedelta(days=30)
        except (ValueError, TypeError):
            fresh = False
        expected_entity = "facebook_group" if requested_families[target] == "facebook_group_posts" else "facebook_page"
        parsed = urllib.parse.urlsplit(target)
        reviewed_locales = source.get("reviewed_locale_ids") if isinstance(source.get("reviewed_locale_ids"), list) else []
        target_checks[target] = bool(authorization) and bool(source) and runtime_locale(args) in reviewed_locales and parsed.hostname in {"facebook.com", "www.facebook.com", "m.facebook.com"} and bool(parsed.path.strip("/")) and authorization.get("platform") == "facebook" and authorization.get("entity_type") == expected_entity and authorization.get("endpoint_family") == requested_families[target] and source.get("verified_entity_type") == expected_entity and source.get("public_access") == "public" and source.get("access", {}).get("method") in {"public_web", "paid_public_api"} and authorization.get("access_class") == "public" and authorization.get("access_method") in {"public_web", "paid_public_api"} and authorization.get("no_credential_or_technical_bypass") is True and source.get("access", {}).get("no_credential_or_technical_bypass") is True and authorization.get("candidate_digest") == source.get("content_digest") and fresh
    checks = {
        **schema_checks,
        "status": packet.get("status") == "valid" and bool(packet.get("targets")),
        "purpose": packet.get("purpose") == "internal_voice_of_customer_research",
        "internal_gate_only": packet.get("platform_authorization_claim") == "none_internal_gate_only",
        "generated_recently": timedelta(0) <= now - generated_at.astimezone(timezone.utc) <= timedelta(days=1),
        "verified_artifact": packet.get("verified_artifact_digest") == canonical_verified_digest,
        "signed_authorization": signature_valid(packet), "signed_current_receipt": signature_valid(receipt),
        "authoritative_state": signature_valid(current_state) and current_state == receipt,
        "current_generation": receipt.get("status") == "valid" and receipt.get("state_id") == packet.get("state_id") and receipt.get("generation_id") == packet.get("generation_id") and receipt.get("generation_version") == packet.get("generation_version") and receipt.get("review_run_id") == packet.get("review_run_id") and receipt.get("authorization_digest") == digest(packet) and receipt.get("verified_artifact_digest") == canonical_verified_digest and receipt.get("review_log_digest") == packet.get("review_log_digest"),
        "targets": all(target_checks.values()) and set(targets) <= set(target_records),
    }
    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        return False, f"Facebook capture authorization failed: {failed}.", {"checks": checks}
    return True, "authorized", {"checks": checks, "target_checks": target_checks, "policy_version": packet.get("policy_version")}


def collect_scrapecreators(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    instagram_allowed, instagram_reason, instagram_pairs = validate_instagram_entity_plan(args)
    if not instagram_allowed:
        raw = {"credential_source": None, "calls": [], "instagram_capture_reason": instagram_reason}
        write_json(run_dir / "raw" / "scrapecreators.json", raw)
        return [], {"status": "capture_gate_blocked", "record_count": 0, "reason": instagram_reason}
    facebook_entity_pairs = parse_entity_locator_pairs(getattr(args, "fb_entity_pages", ""), "--fb-entity-pages")
    facebook_entity_allowed, facebook_entity_reason = validate_entity_pairs_in_plan(args, facebook_entity_pairs, "company_facebook_comments", "--fb-entity-pages")
    if not facebook_entity_allowed:
        raw = {"credential_source": None, "calls": [], "facebook_entity_capture_reason": facebook_entity_reason}
        write_json(run_dir / "raw" / "scrapecreators.json", raw)
        return [], {"status": "capture_gate_blocked", "record_count": 0, "reason": facebook_entity_reason}
    capture_allowed, capture_reason, capture_audit = validate_facebook_capture_authorization(args)
    if not capture_allowed:
        raw = {"credential_source": None, "calls": [], "facebook_capture_gate": capture_audit, "capture_reason": capture_reason}
        write_json(run_dir / "raw" / "scrapecreators.json", raw)
        return [], {"status": "capture_gate_blocked", "record_count": 0, "reason": capture_reason}
    key_name, api_key = get_secret("SCRAPE_CREATORS_API_KEY", "SCRAPECREATORS_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "calls": [], "facebook_capture_gate": capture_audit, "capture_reason": capture_reason}
    if not api_key:
        write_json(run_dir / "raw" / "scrapecreators.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SCRAPE_CREATORS_API_KEY"]}

    # Pre-flight credit check (free endpoint) so an exhausted balance fails loudly
    # before any paid call is attempted.
    credits_remaining: int | None = None
    balance_response = http_get("https://api.scrapecreators.com/v1/credit-balance", headers={"x-api-key": api_key})
    raw["credit_balance"] = balance_response
    balance_body = balance_response.get("body") if isinstance(balance_response.get("body"), dict) else {}
    if balance_response.get("ok") and isinstance(balance_body.get("creditCount"), int):
        credits_remaining = balance_body["creditCount"]
    if credits_remaining is not None and credits_remaining <= 0:
        write_json(run_dir / "raw" / "scrapecreators.json", redact_sensitive(raw))
        return [], {
            "status": "insufficient_credits",
            "credits_remaining": credits_remaining,
            "top_up_url": "https://app.scrapecreators.com/",
        }

    terms = social_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    social_query = terms[0] if terms else args.topic
    per_endpoint = max(1, args.social_per_endpoint)
    fb_max = min(max(3, args.fb_max_posts), 60)

    # spec: (source, endpoint, params, items_key, cursor_key, cap, context, parser)
    # items_key None means a single-call endpoint parsed with list_candidates.
    specs: list[tuple[str, str, dict[str, Any], str | None, str | None, int, str, Any]] = [
        ("tiktok", "https://api.scrapecreators.com/v1/tiktok/search/keyword", {"query": social_query, "date_posted": "month", "sort_by": "relevance", "trim": "true"}, None, None, per_endpoint, "ScrapeCreators tiktok-search", stringify_social_item),
        ("instagram", "https://api.scrapecreators.com/v2/instagram/reels/search", {"query": social_query, "date_posted": "last-month", "page": 1}, None, None, per_endpoint, "ScrapeCreators ig-reels-search", stringify_social_item),
        ("threads", "https://api.scrapecreators.com/v1/threads/search", {"query": social_query, "trim": "true"}, None, None, per_endpoint, "ScrapeCreators threads-search", stringify_social_item),
    ]
    for handle in [item.strip().lstrip("@") for item in args.x_handles.split(",") if item.strip()]:
        specs.append(("x", "https://api.scrapecreators.com/v1/twitter/user-tweets", {"handle": handle, "trim": "true"}, None, None, per_endpoint, f"ScrapeCreators x-handle:{handle}", stringify_twitter_item))
    for group in [item.strip() for item in args.fb_groups.split(",") if item.strip()]:
        specs.append(("facebook", "https://api.scrapecreators.com/v1/facebook/group/posts", {"url": group}, "posts", "cursor", fb_max, f"ScrapeCreators fb-group:{group}", stringify_facebook_item))
    for page in [item.strip() for item in args.fb_pages.split(",") if item.strip()]:
        specs.append(("facebook", "https://api.scrapecreators.com/v1/facebook/profile/posts", {"url": page}, "posts", "cursor", fb_max, f"ScrapeCreators fb-page:{page}", stringify_facebook_item))
        specs.append(("facebook", "https://api.scrapecreators.com/v1/facebook/profile/reels", {"url": page}, "reels", "cursor", per_endpoint, f"ScrapeCreators fb-page-reels:{page}", stringify_facebook_item))
    for entity_id, page in facebook_entity_pairs:
        specs.append(("facebook", "https://api.scrapecreators.com/v1/facebook/profile/posts", {"url": page}, "posts", "cursor", fb_max, f"ScrapeCreators fb-entity:{entity_id}:{page}", stringify_facebook_item))
        specs.append(("facebook", "https://api.scrapecreators.com/v1/facebook/profile/reels", {"url": page}, "reels", "cursor", per_endpoint, f"ScrapeCreators fb-entity:{entity_id}:{page}", stringify_facebook_item))
    for entity_id, handle in instagram_pairs:
        specs.append(("instagram", "https://api.scrapecreators.com/v2/instagram/user/posts", {"handle": handle, "trim": "true"}, "items", "next_max_id", per_endpoint, f"ScrapeCreators ig-entity:{entity_id}:{handle}", stringify_instagram_item))
    for tag in [item.strip().lstrip("#") for item in args.ig_hashtags.split(",") if item.strip()]:
        specs.append(("instagram", "https://api.scrapecreators.com/v1/instagram/search/hashtag", {"hashtag": tag}, "posts", "cursor", per_endpoint, f"ScrapeCreators ig-hashtag:{tag}", stringify_instagram_item))

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    endpoint_statuses: dict[str, str] = {}
    comment_candidates: list[tuple[str, str, str, str]] = []
    comment_request_ledger: list[dict[str, Any]] = []
    credits_exhausted = False
    for source, endpoint, params, items_key, cursor_key, cap, context, parser in specs:
        if credits_exhausted:
            endpoint_statuses[context] = "skipped:insufficient_credits"
            continue
        if items_key is None:
            response = http_get(with_query(endpoint, params), headers={"x-api-key": api_key})
            raw["calls"].append({"source": source, "endpoint": endpoint, "params": params, "response": response})
            if not response.get("ok") or is_credit_exhaustion(response):
                call_status = status_from_response(response)
                endpoint_statuses[context] = call_status
                if call_status == "insufficient_credits":
                    credits_exhausted = True
                continue
            items = list_candidates(response.get("body"))[:cap]
            status = "ok" if items else "empty"
        else:
            items, status = scrapecreators_paginate(endpoint, params, api_key, items_key, cursor_key, cap, raw["calls"], source)
            if status == "insufficient_credits":
                credits_exhausted = True
                endpoint_statuses[context] = status
                continue
        before = len(records)
        for item in items:
            if not isinstance(item, dict):
                continue
            text, url, engagement, raw_id = parser(item)
            identity = raw_id or url or text[:80]
            if not text or identity in seen:
                continue
            seen.add(identity)
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, social_query, url, context)
            facebook_context = facebook_item_context(item, context) if source == "facebook" else {}
            instagram_entity = context.split(":", 2)[1] if context.startswith("ScrapeCreators ig-entity:") else ""
            facebook_entity = context.split(":", 2)[1] if context.startswith("ScrapeCreators fb-entity:") else ""
            subject_entity = instagram_entity or facebook_entity
            records.append(
                normalize_record(
                    source=source,
                    source_url=url,
                    query=social_query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context=f"{context}; author={facebook_context.get('author_label') or 'unresolved'}" if facebook_context else context,
                    engagement=engagement,
                    raw_id=raw_id,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                    confidence_notes="Collected via ScrapeCreators public social scraping API. Verify platform limitations, costs, and source URLs before broad runs.",
                    source_role_override="competitor_context" if instagram_entity else facebook_context.get("source_role"),
                    source_intent_override="competitor_content" if instagram_entity else facebook_context.get("source_intent") or None,
                    published_at=facebook_context.get("published_at"), source_language=str(item.get("language") or item.get("lang") or ""),
                    source_entity_type="instagram_profile" if instagram_entity else facebook_context.get("source_entity_type", ""),
                    author_relationship="page_or_supplier_author" if instagram_entity else facebook_context.get("author_relationship", ""),
                    sampling_frame="entity_led_feedback" if subject_entity else "topic_led_voc",
                    author_voice_status="supplier_context" if subject_entity else "unreviewed",
                    subject_entity_id=subject_entity,
                    collection_source_lane="company_instagram_comments" if instagram_entity else "company_facebook_comments" if facebook_entity else "",
                    collection_locator=context.split(":", 2)[2] if subject_entity else "",
                )
            )
            if url and source in {"facebook", "instagram"}:
                supplier_identity = facebook_context.get("author_label", "") if source == "facebook" and context.startswith(("ScrapeCreators fb-page", "ScrapeCreators fb-entity:")) else context.split(":", 2)[2] if instagram_entity else ""
                comment_candidates.append((source, url, context, supplier_identity))
        produced = len(records) - before
        if items and produced == 0:
            status = f"{status};items_without_text"
        endpoint_statuses[context] = f"{status};records={produced}"

    if args.social_comments and not credits_exhausted:
        comment_endpoints = {
            "facebook": "https://api.scrapecreators.com/v1/facebook/post/comments",
            "instagram": "https://api.scrapecreators.com/v2/instagram/post/comments",
        }
        buckets: dict[tuple[str, str], list[tuple[str, str, str, str]]] = {}
        for candidate in comment_candidates:
            buckets.setdefault((candidate[0], candidate[2]), []).append(candidate)
        ordered_comments: list[tuple[str, str, str, str]] = []
        while any(buckets.values()):
            for key in sorted(buckets, key=lambda item: (item[0] != "facebook", item[0], item[1])):
                if buckets[key]: ordered_comments.append(buckets[key].pop(0))
        selected_comments = ordered_comments[: max(0, args.comments_max)]
        for source, url, context, _supplier_identity in ordered_comments[len(selected_comments):]:
            skipped_key = f"{context} comments:{hashlib.sha256(url.encode()).hexdigest()[:12]}"
            endpoint_statuses[skipped_key] = "skipped:comments_max"
            comment_request_ledger.append({"source": source, "target_url": url, "context": context, "attempted": False, "status": "skipped:comments_max", "http_status": None, "record_count": 0})
        for position, (source, url, context, known_supplier_identity) in enumerate(selected_comments):
            endpoint = comment_endpoints[source]
            ledger_key = f"{context} comments:{hashlib.sha256(url.encode()).hexdigest()[:12]}"
            params = {"url": url, "trim": "true"}
            response = http_get(with_query(endpoint, params), headers={"x-api-key": api_key})
            raw["calls"].append({"source": f"{source}_comment", "endpoint": endpoint, "params": params, "response": response})
            if not response.get("ok"):
                comment_status = status_from_response(response)
                endpoint_statuses[ledger_key] = comment_status
                comment_request_ledger.append({"source": source, "target_url": url, "context": context, "attempted": True, "status": comment_status, "http_status": response.get("status_code"), "record_count": 0})
                if comment_status == "insufficient_credits":
                    credits_exhausted = True
                    for skipped_source, skipped_url, skipped_context, _skipped_identity in selected_comments[position + 1:]:
                        skipped_key = f"{skipped_context} comments:{hashlib.sha256(skipped_url.encode()).hexdigest()[:12]}"
                        endpoint_statuses[skipped_key] = "skipped:insufficient_credits"
                        comment_request_ledger.append({"source": skipped_source, "target_url": skipped_url, "context": skipped_context, "attempted": False, "status": "skipped:insufficient_credits", "http_status": None, "record_count": 0})
                    break
                continue
            before = len(records)
            comment_items = list_candidates(response.get("body"))[:10]
            for item in comment_items:
                if not isinstance(item, dict):
                    continue
                text, comment_url, engagement, raw_id = stringify_social_comment(item)
                identity = raw_id or str(text)[:80]
                if not text or identity in seen:
                    continue
                seen.add(identity)
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, social_query, comment_url or url, context)
                supplier_identity = known_supplier_identity
                comment_context = social_comment_context(item, source, supplier_identity)
                instagram_entity = context.split(":", 2)[1] if context.startswith("ScrapeCreators ig-entity:") else ""
                facebook_entity = context.split(":", 2)[1] if context.startswith("ScrapeCreators fb-entity:") else ""
                subject_entity = instagram_entity or facebook_entity
                records.append(
                    normalize_record(
                        source=source,
                        source_url=comment_url or url,
                        query=social_query,
                        customer_segment=args.customer_segment,
                        hypothesis=args.hypothesis_id,
                        text=text,
                        author_context=f"{context} comment; author={comment_context['author_label'] or 'unresolved'}",
                        engagement=engagement,
                        raw_id=raw_id,
                        evidence_type="irrelevant" if relevance == "irrelevant" else None,
                        strength="irrelevant" if relevance == "irrelevant" else None,
                        relevance=relevance,
                        relevance_notes=relevance_notes,
                        relevance_score=relevance_score,
                        confidence_notes="Comment on a public post via ScrapeCreators. Treat as interview lead unless independent comments repeat the pain.",
                        source_role_override=comment_context["source_role"], source_intent_override=comment_context["source_intent"],
                        source_language=str(item.get("language") or item.get("lang") or ""),
                        source_entity_type=comment_context["source_entity_type"], author_relationship=comment_context["author_relationship"],
                        sampling_frame="entity_led_feedback" if subject_entity else "topic_led_voc",
                        author_voice_status="supplier_context" if comment_context["source_role"] == "competitor_context" else "unreviewed",
                        subject_entity_id=subject_entity,
                        collection_source_lane="company_instagram_comments" if instagram_entity else "company_facebook_comments" if facebook_entity else "",
                        collection_locator=context.split(":", 2)[2] if subject_entity else "",
                    )
                )
            produced_comments = len(records) - before
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            continuation = body.get("cursor") or body.get("next_cursor") or body.get("nextCursor")
            comment_status = "partial:pagination_cursor" if continuation else "ok" if produced_comments else "empty"
            endpoint_statuses[ledger_key] = f"{comment_status};records={produced_comments}"
            comment_request_ledger.append({"source": source, "target_url": url, "context": context, "attempted": True, "status": comment_status, "http_status": response.get("status_code"), "record_count": produced_comments, "continuation_cursor_present": bool(continuation)})

    first_response = (raw["calls"][0] or {}).get("response", {}) if raw["calls"] else {}
    requested_facebook = bool(args.fb_groups.strip() or args.fb_pages.strip() or facebook_entity_pairs)
    if args.social_comments and requested_facebook and not any(source == "facebook" for source, _, _, _ in comment_candidates):
        endpoint_statuses["ScrapeCreators fb-comments"] = "not_attempted:no_accessible_posts"
    targeted_failures = [f"{name}={value}" for name, value in endpoint_statuses.items() if (name.startswith("ScrapeCreators fb-") or name.startswith("ScrapeCreators ig-entity:")) and not value.startswith("ok")]
    if credits_exhausted:
        status = "insufficient_credits"
    elif targeted_failures:
        status = "partial"
    else:
        status = "ok" if records else status_from_response(first_response)
    write_json(run_dir / "raw" / "scrapecreators.json", redact_sensitive(raw))
    summary: dict[str, Any] = {"status": status, "record_count": len(records), "endpoint_statuses": endpoint_statuses, "comment_request_ledger": comment_request_ledger, "fields": fields_present(raw), "coverage_alerts": targeted_failures}
    if credits_remaining is not None:
        summary["credits_remaining_at_start"] = credits_remaining
    if credits_exhausted:
        summary["top_up_url"] = "https://app.scrapecreators.com/"
    return records, summary


def china_query_terms(args: argparse.Namespace, queries: list[str]) -> list[str]:
    terms = social_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    terms.extend(trend_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language))
    terms.extend(queries[:3])
    deduped: list[str] = []
    for term in terms:
        clean = " ".join(term.split())
        if clean and clean not in deduped:
            deduped.append(clean)
    return deduped[:6] or [args.topic]


def strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def china_source_from_url(url: str) -> str:
    lower = url.lower()
    if "zhihu.com" in lower:
        return "zhihu"
    if "weibo.com" in lower:
        return "weibo"
    if "douban.com" in lower:
        return "douban"
    if "tieba.baidu.com" in lower:
        return "tieba"
    if "bilibili.com" in lower:
        return "bilibili"
    if "xiaohongshu.com" in lower:
        return "xiaohongshu"
    if "v2ex.com" in lower:
        return "v2ex"
    return "web_search"


def collect_china_bilibili(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: dict[str, Any] = {"backend": "bilibili_public_search", "searches": [], "fallback_calls": []}
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    first_response: dict[str, Any] = {}
    for query in china_query_terms(args, queries)[:3]:
        response = http_get(
            with_query(
                "https://api.bilibili.com/x/web-interface/search/type",
                {"search_type": "video", "keyword": query, "page": 1, "page_size": min(max(args.limit, 1), 10)},
            ),
            headers={
                "User-Agent": "Mozilla/5.0 evidence-scout/0.1",
                "Referer": "https://www.bilibili.com/",
            },
        )
        if not first_response:
            first_response = response
        raw["searches"].append({"query": query, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        data = body.get("data") if isinstance(body, dict) else {}
        for item in (data.get("result") or []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            raw_id = str(item.get("id") or item.get("bvid") or item.get("arcurl") or "")
            if not raw_id or raw_id in seen:
                continue
            seen.add(raw_id)
            url = item.get("arcurl") or (f"https://www.bilibili.com/video/{item.get('bvid')}" if item.get("bvid") else "")
            title = strip_html(item.get("title") or "")
            description = strip_html(item.get("description") or "")
            tags = strip_html(item.get("tag") or "")
            text = "\n\n".join(part for part in [title, description, tags] if part).strip()
            if not text:
                continue
            author = item.get("author") or item.get("mid") or "Bilibili"
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, str(author))
            records.append(
                normalize_record(
                    source="bilibili",
                    source_url=url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context=str(author),
                    engagement={
                        "views": item.get("play"),
                        "comments": item.get("video_review") or item.get("review"),
                        "likes": item.get("like"),
                    },
                    raw_id=raw_id,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                    confidence_notes="Collected from Bilibili public search. Treat video metadata and engagement as weak context unless paired with repeated user comments or complaints.",
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break
    active_backend = "bilibili_public_search"
    if not records:
        serper_key_name, serper_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
        key_name, brave_key = get_secret("BRAVE_SEARCH_API_KEY")
        firecrawl_key_name, firecrawl_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
        raw["fallback_credential_source"] = serper_key_name or key_name or firecrawl_key_name
        if serper_key:
            active_backend = "bilibili_site_search_serper"
            for term in china_query_terms(args, queries)[:3]:
                query = f"site:bilibili.com/video {term}"
                response = http_post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                    data={"q": query, "num": min(max(args.limit, 1), 10), "gl": "cn", "hl": args.language},
                )
                raw["fallback_calls"].append({"backend": active_backend, "query": query, "response": response})
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                for item in body.get("organic", []) if isinstance(body, dict) else []:
                    url = item.get("link") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    text = "\n\n".join(part for part in [item.get("title", ""), item.get("snippet", "")] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "Bilibili via Serper")
                    records.append(normalize_record(source="bilibili", source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="Bilibili via Serper.dev", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from Bilibili site-search fallback via Serper.dev. Treat as weak source discovery unless enriched with comments or direct user-pain text."))
                    if len(records) >= args.limit:
                        break
                if len(records) >= args.limit:
                    break
        elif brave_key:
            active_backend = "bilibili_site_search_brave"
            for term in china_query_terms(args, queries)[:3]:
                query = f"site:bilibili.com/video {term}"
                response = http_get(
                    with_query("https://api.search.brave.com/res/v1/web/search", {"q": query, "count": min(max(args.limit, 1), 10), "country": "CN", "search_lang": args.language}),
                    headers={"X-Subscription-Token": brave_key, "Accept": "application/json"},
                )
                raw["fallback_calls"].append({"backend": active_backend, "query": query, "response": response})
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                web = body.get("web", {}) if isinstance(body, dict) else {}
                for item in web.get("results", []) if isinstance(web, dict) else []:
                    url = item.get("url") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", "")] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "Bilibili via Brave")
                    records.append(normalize_record(source="bilibili", source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="Bilibili via Brave", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from Bilibili site-search fallback. Treat as weak source discovery unless enriched with comments or direct user-pain text."))
                    if len(records) >= args.limit:
                        break
                if len(records) >= args.limit:
                    break
        elif firecrawl_key:
            active_backend = "bilibili_site_search_firecrawl"
            for term in china_query_terms(args, queries)[:3]:
                query = f"site:bilibili.com/video {term}"
                response = http_post(
                    "https://api.firecrawl.dev/v1/search",
                    headers={"Authorization": f"Bearer {firecrawl_key}"},
                    data={"query": query, "limit": min(max(args.limit, 1), 10), "scrapeOptions": {"formats": ["markdown"]}},
                )
                raw["fallback_calls"].append({"backend": active_backend, "query": query, "response": response})
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                for item in body.get("data") or []:
                    url = item.get("url") or item.get("sourceURL") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", ""), (item.get("markdown") or "")[:1200]] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "Bilibili via Firecrawl")
                    records.append(normalize_record(source="bilibili", source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="Bilibili via Firecrawl", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from Bilibili site-search fallback. Treat as weak source discovery unless enriched with comments or direct user-pain text."))
                    if len(records) >= args.limit:
                        break
                if len(records) >= args.limit:
                    break
        else:
            active_backend = "none"

    if records:
        status = "ok"
    elif first_response.get("status_code") == 412:
        status = "permission_denied"
    else:
        status = status_from_response(first_response) if first_response else "missing_credentials"
    write_json(run_dir / "raw" / "china_bilibili.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "active_backend": active_backend, "fields": fields_present(raw)}


def collect_china_bilibili_comments(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: dict[str, Any] = {"backend": "bilibili_public_search_plus_comments", "searches": [], "comments": []}
    records: list[dict[str, Any]] = []
    seen_comments: set[str] = set()
    video_limit = max(1, min(args.china_comment_video_limit, 3))
    comment_limit = max(1, min(args.china_comment_limit, 20))
    videos: list[dict[str, Any]] = []
    first_response: dict[str, Any] = {}

    for query in china_query_terms(args, queries)[:3]:
        response = http_get(
            with_query(
                "https://api.bilibili.com/x/web-interface/search/type",
                {"search_type": "video", "keyword": query, "page": 1, "page_size": video_limit},
            ),
            headers={
                "User-Agent": "Mozilla/5.0 evidence-scout/0.1",
                "Referer": "https://www.bilibili.com/",
            },
        )
        if not first_response:
            first_response = response
        raw["searches"].append({"query": query, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        data = body.get("data") if isinstance(body, dict) else {}
        for item in (data.get("result") or []) if isinstance(data, dict) else []:
            if isinstance(item, dict) and item.get("id"):
                videos.append({"query": query, "aid": item.get("id"), "bvid": item.get("bvid"), "url": item.get("arcurl") or f"https://www.bilibili.com/video/{item.get('bvid', '')}", "title": strip_html(item.get("title") or "")})
            if len(videos) >= video_limit:
                break
        if len(videos) >= video_limit:
            break

    for video in videos[:video_limit]:
        response = http_get(
            with_query(
                "https://api.bilibili.com/x/v2/reply",
                {"type": 1, "oid": video["aid"], "pn": 1, "ps": comment_limit, "sort": 2},
            ),
            headers={
                "User-Agent": "Mozilla/5.0 evidence-scout/0.1",
                "Referer": video["url"],
            },
        )
        raw["comments"].append({"video": video, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        data = body.get("data") if isinstance(body, dict) else {}
        for reply in (data.get("replies") or []) if isinstance(data, dict) else []:
            if not isinstance(reply, dict):
                continue
            raw_id = str(reply.get("rpid") or reply.get("oid") or "")
            if not raw_id or raw_id in seen_comments:
                continue
            seen_comments.add(raw_id)
            content = reply.get("content") if isinstance(reply.get("content"), dict) else {}
            text = content.get("message") or ""
            if not text:
                continue
            member = reply.get("member") if isinstance(reply.get("member"), dict) else {}
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, video["query"], video["url"], member.get("uname", ""))
            records.append(
                normalize_record(
                    source="bilibili_comment",
                    source_url=video["url"],
                    query=video["query"],
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context=member.get("uname", ""),
                    engagement={"likes": reply.get("like"), "comments": reply.get("rcount")},
                    raw_id=raw_id,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                    confidence_notes="Collected from Bilibili public comments for a capped set of videos. Treat as user-comment leads, not proof of demand.",
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    if records:
        status = "ok"
    elif first_response.get("status_code") == 412:
        status = "permission_denied"
    else:
        status = status_from_response(first_response) if first_response else "failed"
    write_json(run_dir / "raw" / "china_bilibili_comments.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "active_backend": "bilibili_public_comments", "video_count": len(videos), "fields": fields_present(raw)}


def collect_china_v2ex(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    serper_key_name, serper_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
    key_name, brave_key = get_secret("BRAVE_SEARCH_API_KEY")
    firecrawl_key_name, firecrawl_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    raw: dict[str, Any] = {"credential_source": serper_key_name or key_name or firecrawl_key_name, "calls": []}
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    terms = china_query_terms(args, queries)
    active_backend = ""

    if serper_key:
        active_backend = "serper_site_search"
        for term in terms[:3]:
            query = f"site:v2ex.com/t {term}"
            response = http_post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                data={"q": query, "num": min(max(args.limit, 1), 10), "gl": "cn", "hl": args.language},
            )
            raw["calls"].append({"backend": active_backend, "query": query, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            for item in body.get("organic", []) if isinstance(body, dict) else []:
                url = item.get("link") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                text = "\n\n".join(part for part in [item.get("title", ""), item.get("snippet", "")] if part).strip()
                if not text:
                    continue
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "V2EX via Serper")
                records.append(normalize_record(source="v2ex", source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="V2EX via Serper.dev", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score))
                if len(records) >= args.limit:
                    break
            if len(records) >= args.limit:
                break
    elif brave_key:
        active_backend = "brave_site_search"
        for term in terms[:3]:
            query = f"site:v2ex.com/t {term}"
            response = http_get(
                with_query("https://api.search.brave.com/res/v1/web/search", {"q": query, "count": min(max(args.limit, 1), 10), "country": "CN", "search_lang": args.language}),
                headers={"X-Subscription-Token": brave_key, "Accept": "application/json"},
            )
            raw["calls"].append({"backend": active_backend, "query": query, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            web = body.get("web", {}) if isinstance(body, dict) else {}
            for item in web.get("results", []) if isinstance(web, dict) else []:
                url = item.get("url") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", "")] if part).strip()
                if not text:
                    continue
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "V2EX via Brave")
                records.append(normalize_record(source="v2ex", source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="V2EX via Brave", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score))
                if len(records) >= args.limit:
                    break
            if len(records) >= args.limit:
                break
    elif firecrawl_key:
        active_backend = "firecrawl_site_search"
        for term in terms[:3]:
            query = f"site:v2ex.com/t {term}"
            response = http_post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {firecrawl_key}"},
                data={"query": query, "limit": min(max(args.limit, 1), 10), "scrapeOptions": {"formats": ["markdown"]}},
            )
            raw["calls"].append({"backend": active_backend, "query": query, "response": response})
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            for item in body.get("data") or []:
                url = item.get("url") or item.get("sourceURL") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", ""), (item.get("markdown") or "")[:1200]] if part).strip()
                if not text:
                    continue
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "V2EX via Firecrawl")
                records.append(normalize_record(source="v2ex", source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="V2EX via Firecrawl", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score))
                if len(records) >= args.limit:
                    break
            if len(records) >= args.limit:
                break
    else:
        active_backend = "v2ex_public_hot"
        response = http_get("https://www.v2ex.com/api/topics/hot.json", headers={"User-Agent": "evidence-scout/0.1"})
        raw["calls"].append({"backend": active_backend, "query": "hot topics", "response": response})
        if response.get("ok"):
            items = response.get("body") if isinstance(response.get("body"), list) else []
            for item in items[: max(args.limit, 20)]:
                if not isinstance(item, dict):
                    continue
                url = item.get("url") or ""
                title = item.get("title") or ""
                content = item.get("content") or ""
                text = "\n\n".join(part for part in [title, content] if part).strip()
                if not text:
                    continue
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, "V2EX hot topics", url, "V2EX public hot")
                records.append(normalize_record(source="v2ex", source_url=url, query="V2EX hot topics", customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context="V2EX public hot", engagement={"comments": item.get("replies")}, raw_id=str(item.get("id") or url), evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from V2EX public hot topics because no search backend was configured. Treat zero relevant records as limited coverage, not absence of developer pain."))
    first_response = (raw["calls"][0] or {}).get("response", {}) if raw["calls"] else {}
    status = "ok" if first_response.get("ok") else status_from_response(first_response)
    if active_backend == "v2ex_public_hot" and status == "ok":
        status = "warn"
    write_json(run_dir / "raw" / "china_v2ex.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "active_backend": active_backend, "fields": fields_present(raw)}


def collect_china_web(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    serper_key_name, serper_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
    firecrawl_key_name, firecrawl_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    brave_key_name, brave_key = get_secret("BRAVE_SEARCH_API_KEY")
    raw: dict[str, Any] = {"credential_source": serper_key_name or firecrawl_key_name or brave_key_name, "calls": []}
    if not serper_key and not firecrawl_key and not brave_key:
        write_json(run_dir / "raw" / "china_web.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SERPER_DEV_API_KEY", "FIRECRAWL_API_KEY_HGINVESTOR", "BRAVE_SEARCH_API_KEY"]}

    domains = ["zhihu.com", "weibo.com", "douban.com", "tieba.baidu.com", "36kr.com", "huxiu.com", "xiaohongshu.com"]
    terms = china_query_terms(args, queries)[:3]
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    active_backend = "serper_china_web" if serper_key else "firecrawl_china_web" if firecrawl_key else "brave_china_web"

    for term in terms:
        for domain in domains:
            query = f"{term} site:{domain}"
            if serper_key:
                response = http_post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                    data={"q": query, "num": 3, "gl": "cn", "hl": args.language},
                )
                raw["calls"].append({"backend": active_backend, "query": query, "response": response})
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                for item in body.get("organic", []) if isinstance(body, dict) else []:
                    url = item.get("link") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    text = "\n\n".join(part for part in [item.get("title", ""), item.get("snippet", "")] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, domain)
                    records.append(normalize_record(source=china_source_from_url(url), source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context=f"China web via Serper.dev ({domain})", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from Chinese web/domain search via Serper.dev. Treat as source discovery unless it contains direct user complaint, workaround, or decision language."))
                    if len(records) >= args.limit:
                        break
            elif firecrawl_key:
                response = http_post(
                    "https://api.firecrawl.dev/v1/search",
                    headers={"Authorization": f"Bearer {firecrawl_key}"},
                    data={"query": query, "limit": 3, "scrapeOptions": {"formats": ["markdown"]}},
                )
                raw["calls"].append({"backend": active_backend, "query": query, "response": response})
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                items = body.get("data") or []
                for item in items:
                    url = item.get("url") or item.get("sourceURL") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", ""), (item.get("markdown") or "")[:1200]] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, domain)
                    records.append(normalize_record(source=china_source_from_url(url), source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context=f"China web via Firecrawl ({domain})", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from Chinese web/domain search. Treat as source discovery unless it contains direct user complaint, workaround, or decision language."))
                    if len(records) >= args.limit:
                        break
            else:
                response = http_get(
                    with_query("https://api.search.brave.com/res/v1/web/search", {"q": query, "count": 3, "country": "CN", "search_lang": args.language}),
                    headers={"X-Subscription-Token": brave_key, "Accept": "application/json"},
                )
                raw["calls"].append({"backend": active_backend, "query": query, "response": response})
                body = response.get("body") if isinstance(response.get("body"), dict) else {}
                web = body.get("web", {}) if isinstance(body, dict) else {}
                for item in web.get("results", []) if isinstance(web, dict) else []:
                    url = item.get("url") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    text = "\n\n".join(part for part in [item.get("title", ""), item.get("description", "")] if part).strip()
                    if not text:
                        continue
                    relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, domain)
                    records.append(normalize_record(source=china_source_from_url(url), source_url=url, query=query, customer_segment=args.customer_segment, hypothesis=args.hypothesis_id, text=text, author_context=f"China web via Brave ({domain})", engagement={}, raw_id=url, evidence_type="irrelevant" if relevance == "irrelevant" else None, strength="irrelevant" if relevance == "irrelevant" else None, relevance=relevance, relevance_notes=relevance_notes, relevance_score=relevance_score, confidence_notes="Collected from Chinese web/domain search. Treat as source discovery unless it contains direct user complaint, workaround, or decision language."))
                    if len(records) >= args.limit:
                        break
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    first_response = (raw["calls"][0] or {}).get("response", {}) if raw["calls"] else {}
    status = "ok" if first_response.get("ok") else status_from_response(first_response)
    write_json(run_dir / "raw" / "china_web.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "active_backend": active_backend, "fields": fields_present(raw)}


def parse_cli_items(output: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [item for item in list_candidates(data) if isinstance(item, dict)]
    return []


def collect_china_xiaohongshu(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    opencli = shutil.which("opencli")
    raw: dict[str, Any] = {"backend": "opencli_xiaohongshu", "calls": []}
    if not opencli:
        write_json(run_dir / "raw" / "china_xiaohongshu.json", raw)
        return [], {"status": "missing_cli", "required_cli": ["opencli"], "account_risk": "login_or_cookie_backed"}

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in china_query_terms(args, queries)[:3]:
        try:
            proc = subprocess.run(
                [opencli, "xiaohongshu", "search", query, "-f", "json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
        except subprocess.TimeoutExpired:
            raw["calls"].append({"query": query, "status": "timeout"})
            continue
        except OSError as exc:
            raw["calls"].append({"query": query, "status": "failed", "error": str(exc)})
            continue
        raw["calls"].append({"query": query, "exit_code": proc.returncode, "stdout": proc.stdout[:20000], "stderr": proc.stderr[-4000:]})
        if proc.returncode != 0:
            continue
        items = parse_cli_items(proc.stdout)
        if not items and proc.stdout.strip():
            items = [{"text": proc.stdout.strip(), "url": ""}]
        for item in items:
            text, url, engagement, raw_id = stringify_social_item(item)
            if not text:
                text = "\n\n".join(str(item.get(key, "")) for key in ["title", "desc", "content", "text"] if item.get(key)).strip()
            identity = raw_id or url or text[:80]
            if not text or identity in seen:
                continue
            seen.add(identity)
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, "XiaoHongShu via OpenCLI")
            records.append(
                normalize_record(
                    source="xiaohongshu",
                    source_url=url,
                    query=query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context="XiaoHongShu via OpenCLI",
                    engagement=engagement,
                    raw_id=identity,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                    confidence_notes="Collected from XiaoHongShu through OpenCLI/browser-session access. Use a non-primary account and treat account/cookie-backed scraping as fragile.",
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break
    status = "ok" if records else "login_required_or_failed"
    write_json(run_dir / "raw" / "china_xiaohongshu.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "active_backend": "opencli_xiaohongshu", "account_risk": "login_or_cookie_backed", "fields": fields_present(raw)}


def collect_sonar(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entity_sonar_apps = parse_entity_store_apps(getattr(args, "sonar_entity_apps", ""), "--sonar-entity-apps")
    if parse_sonar_apps(getattr(args, "sonar_apps", "")):
        return [], {"status": "capture_gate_blocked", "reason": "targeted app reviews require --sonar-entity-apps and a reviewed source plan; --sonar-apps cannot produce topic-led VOC", "record_count": 0}
    for lane, pairs in {
        "apple_app_store_reviews": [(entity, f"{store}:{app_id}") for entity, store, app_id in entity_sonar_apps if store == "ios"],
        "google_play_store_reviews": [(entity, f"{store}:{app_id}") for entity, store, app_id in entity_sonar_apps if store == "android"],
    }.items():
        allowed, reason = validate_entity_pairs_in_plan(args, pairs, lane, "--sonar-entity-apps")
        if not allowed:
            return [], {"status": "capture_gate_blocked", "reason": reason, "record_count": 0}
    key_name, api_key = get_secret("SONAR_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "calls": []}
    if not api_key:
        write_json(run_dir / "raw" / "sonar.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SONAR_API_KEY"]}

    base_url = "https://trysonar.app/api/v1"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    country = args.geo.lower() if len(args.geo) == 2 else "us"
    stores = [store.strip().lower() for store in args.sonar_stores.split(",") if store.strip().lower() in {"ios", "android"}]
    stores = stores or ["ios", "android"]
    keyword_limit = max(1, min(args.sonar_keyword_limit, 10))
    terms = trend_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)[:keyword_limit]
    if not terms:
        terms = queries[:keyword_limit]

    records: list[dict[str, Any]] = []
    for store in stores:
        for term in terms:
            suggestions_response = http_get(
                with_query(f"{base_url}/keywords/suggestions", {"q": term, "store": store, "country": country}),
                headers=headers,
            )
            raw["calls"].append({"kind": "keyword_suggestions", "store": store, "term": term, "response": suggestions_response})
            if suggestions_response.get("ok"):
                suggestions = (suggestions_response.get("body") or {}).get("data") or []
                if suggestions:
                    text = (
                        f"Sonar app-store autocomplete suggestions for `{term}` on `{store}` in `{country}`: "
                        f"{json.dumps(suggestions[:10], sort_keys=True)}"
                    )
                    records.append(
                        normalize_record(
                            source="app_store",
                            source_url="https://trysonar.app/docs/api#suggestions",
                            query=term,
                            customer_segment=args.customer_segment,
                            hypothesis=args.hypothesis_id,
                            text=text,
                            author_context="Sonar keyword suggestions",
                            engagement={},
                            raw_id=f"{store}:{country}:{term}:suggestions",
                            evidence_type="search_demand",
                            strength="weak",
                            confidence_notes="Sonar app-store autocomplete is a directional ASO/search-interest proxy. It does not prove pain, urgency, or willingness to pay.",
                        )
                    )

        metrics_terms = ",".join(terms[:keyword_limit])
        metrics_response = http_get(
            with_query(f"{base_url}/keywords/metrics", {"qs": metrics_terms, "store": store, "country": country}),
            headers=headers,
        )
        raw["calls"].append({"kind": "keyword_metrics", "store": store, "terms": terms[:keyword_limit], "response": metrics_response})
        if metrics_response.get("ok"):
            data = (metrics_response.get("body") or {}).get("data")
            metrics_items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            for item in metrics_items:
                if not isinstance(item, dict):
                    continue
                keyword = item.get("keyword") or ""
                text = (
                    f"Sonar app-store keyword metrics for `{keyword}` on `{store}` in `{country}`: "
                    f"difficulty={item.get('difficulty')}, popularity={item.get('popularity')}, "
                    f"results_count={item.get('results_count')}."
                )
                if item.get("error"):
                    text += f" Per-keyword error: {json.dumps(item.get('error'), sort_keys=True)}."
                records.append(
                    normalize_record(
                        source="app_store",
                        source_url="https://trysonar.app/docs/api#keyword-metrics",
                        query=keyword or metrics_terms,
                        customer_segment=args.customer_segment,
                        hypothesis=args.hypothesis_id,
                        text=text,
                        author_context="Sonar keyword metrics",
                        engagement={},
                        raw_id=f"{store}:{country}:{keyword}:metrics",
                        evidence_type="search_demand",
                        strength="weak",
                        confidence_notes="Sonar keyword metrics are app-store demand and competition context. Treat as weak market signal unless paired with direct user pain.",
                    )
                )

    requested_sonar_apps = entity_sonar_apps
    review_ledger: list[dict[str, Any]] = []
    review_failures: list[dict[str, Any]] = []
    for entity_id, store, app_id in requested_sonar_apps:
        reviews_response = http_get(
            with_query(
                f"{base_url}/apps/reviews",
                {
                    "store": store,
                    "id": app_id,
                    "country": country,
                    "sort": "recent",
                    "max_rating": args.sonar_review_max_rating,
                    "limit": min(args.limit, 50),
                },
            ),
            headers=headers,
        )
        raw["calls"].append({"kind": "app_reviews", "entity_id": entity_id or None, "store": store, "app_id": app_id, "response": reviews_response})
        lane = {"entity_id": entity_id or None, "store": store, "app_id": app_id, "country": country, "attempted": True, "retrieved_count": 0, "status": status_from_response(reviews_response)}
        if reviews_response.get("ok"):
            for item in ((reviews_response.get("body") or {}).get("data") or [])[: args.limit]:
                title = item.get("title") or ""
                body = item.get("text") or ""
                text = "\n\n".join(part for part in [title, body] if part).strip()
                if not text:
                    continue
                source_url = item.get("url") or f"https://trysonar.app/docs/api#reviews"
                relevance, relevance_notes, relevance_score = assess_relevance(text, args, f"{store}:{app_id} reviews", source_url, "Sonar app review")
                records.append(
                    normalize_record(
                        source="app_review",
                        source_url=source_url,
                        query=f"{store}:{app_id}",
                        customer_segment=args.customer_segment,
                        hypothesis=args.hypothesis_id,
                        text=text,
                        author_context=f"Sonar {store} review score={item.get('score')} version={item.get('version')}",
                        engagement={"likes": item.get("thumbsUp")},
                        raw_id=str(item.get("id") or source_url),
                        evidence_type="irrelevant" if relevance == "irrelevant" else None,
                        strength="irrelevant" if relevance == "irrelevant" else None,
                        relevance=relevance,
                        relevance_notes=relevance_notes,
                        relevance_score=relevance_score,
                        confidence_notes="Collected from public app-store reviews via Sonar. Reviews are biased toward store users and should be paired with direct customer interviews.",
                        sampling_frame="entity_led_feedback" if entity_id else "topic_led_voc",
                        author_voice_status="unreviewed",
                        subject_entity_id=entity_id,
                        collection_source_lane="apple_app_store_reviews" if store == "ios" else "google_play_store_reviews",
                        collection_locator=f"{store}:{app_id}",
                    )
                )
                records[-1]["sampling_metadata"].update({"sort_requested": "recent", "rating_filter": {"maximum": args.sonar_review_max_rating}, "record_limit": min(args.limit, 50), "product_version": item.get("version"), "pages_retrieved": 1, "subset_limitations": "Recent app-review slice with requested maximum rating; not representative of other versions or dates."})
                lane["retrieved_count"] += 1
            lane["status"] = "ok" if lane["retrieved_count"] else "empty"
        else:
            review_failures.append({"entity_id": entity_id or None, "store": store, "app_id": app_id, "country": country, "status": lane["status"]})
        review_ledger.append(lane)

    if requested_sonar_apps and args.sonar_include_revenue:
        by_store: dict[str, list[str]] = {}
        for _entity_id, store, app_id in requested_sonar_apps:
            by_store.setdefault(store, []).append(app_id)
        for store, app_ids in by_store.items():
            revenue_response = http_get(
                with_query(f"{base_url}/apps/revenue", {"store": store, "ids": ",".join(app_ids[:25]), "country": country}),
                headers=headers,
            )
            raw["calls"].append({"kind": "app_revenue", "store": store, "app_ids": app_ids[:25], "response": revenue_response})
            if not revenue_response.get("ok"):
                continue
            data = (revenue_response.get("body") or {}).get("data")
            revenue_items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            for item in revenue_items:
                if not isinstance(item, dict):
                    continue
                app = item.get("app") or {}
                revenue = item.get("revenue") or {}
                error = item.get("error")
                text = (
                    f"Sonar revenue estimate for `{app.get('name') or item.get('store_id')}` on `{store}` in `{country}`: "
                    f"monthly={revenue.get('monthly_formatted') or revenue.get('monthly')}, model={revenue.get('model')}. "
                    f"Methodology: {revenue.get('methodology') or 'not provided'}."
                )
                if error:
                    text += f" Error: {json.dumps(error, sort_keys=True)}."
                records.append(
                    normalize_record(
                        source="app_store",
                        source_url="https://trysonar.app/docs/api#revenue-estimate",
                        query=f"{store}:{item.get('store_id') or app.get('store_id')}",
                        customer_segment=args.customer_segment,
                        hypothesis=args.hypothesis_id,
                        text=text,
                        author_context="Sonar revenue estimate",
                        engagement={},
                        raw_id=f"{store}:{item.get('store_id') or app.get('store_id')}:revenue",
                        evidence_type="spend",
                        strength="weak",
                        confidence_notes="Sonar revenue is an estimate and should be treated as monetization context, not proof of willingness to pay for a new product.",
                    )
                )

    first_response = (raw["calls"][0] or {}).get("response", {}) if raw["calls"] else {}
    if review_failures:
        status = "partial" if records else review_failures[0]["status"]
    elif review_ledger and any(item["status"] != "ok" for item in review_ledger):
        status = "partial" if records else "empty"
    else:
        status = "ok" if records else status_from_response(first_response)
    write_json(run_dir / "raw" / "sonar.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "review_ledger": review_ledger, "review_failures": review_failures, "fields": fields_present(raw)}


def write_report(
    run_dir: Path,
    args: argparse.Namespace,
    queries: list[str],
    records: list[dict[str, Any]],
    irrelevant_records: list[dict[str, Any]],
    provider_summaries: dict[str, Any],
) -> None:
    by_source: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_strength: dict[str, int] = {}
    by_intent: dict[str, int] = {}
    by_comment_intent: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for record in records:
        by_source[record["source"]] = by_source.get(record["source"], 0) + 1
        by_type[record["evidence_type"]] = by_type.get(record["evidence_type"], 0) + 1
        by_strength[record["strength"]] = by_strength.get(record["strength"], 0) + 1
        role = record.get("source_role", "unknown")
        by_role[role] = by_role.get(role, 0) + 1
        intent = record.get("source_intent", "unknown")
        by_intent[intent] = by_intent.get(intent, 0) + 1
        comment_intent = record.get("comment_intent", "unknown")
        if comment_intent != "not_social_comment":
            by_comment_intent[comment_intent] = by_comment_intent.get(comment_intent, 0) + 1
    quality_flags = quality_summary(records, provider_summaries)

    top = sorted(
        (item for item in records if item.get("source_role") in {"customer_review", "community_context"}),
        key=lambda item: (
            {"strong": 3, "medium": 2, "weak": 1}.get(item["strength"], 0),
            item["engagement"].get("upvotes") or 0,
            item["engagement"].get("comments") or 0,
        ),
        reverse=True,
    )[:10]
    run_title = "# Evidence Scout Discovery Collection" if args.research_mode == "discovery" else "# Evidence Scout Run"
    segment_label = args.customer_segment or "[unresolved: market discovery]"
    lines = [
        run_title,
        "",
        f"- Topic: {args.topic}",
        f"- Customer segment: {segment_label}",
        f"- Hypothesis: {args.hypothesis_id}",
        f"- Geography/language: {args.geo}/{args.language}",
        f"- Lookback days: {args.days}",
        f"- Relevant records: {len(records)}",
        f"- Irrelevant records excluded: {len(irrelevant_records)}",
        "",
        "## Provider Status",
        "",
    ]
    for provider, summary in provider_summaries.items():
        detail = []
        if summary.get("irrelevant_count"):
            detail.append(f"{summary.get('irrelevant_count')} irrelevant excluded")
        if summary.get("http_status"):
            detail.append(f"HTTP {summary.get('http_status')}")
        if summary.get("active_backend"):
            detail.append(f"backend {summary.get('active_backend')}")
        suffix = f" ({'; '.join(detail)})" if detail else ""
        lines.append(f"- {provider}: {summary.get('status')} ({summary.get('record_count', 0)} relevant records){suffix}")
    failed = provider_alerts(provider_summaries)
    if failed:
        lines.extend(["", "## Provider Alerts", ""])
        for alert in failed:
            lines.append(f"- {alert}")
    pending = remaining_tasks(provider_summaries, quality_flags)
    if pending:
        lines.extend(["", "## Remaining Tasks", ""])
        lines.extend(f"- {task['provider']} ({task['status']}): {task['action']}" for task in pending)
    lines.extend(["", "## Query Plan", ""])
    lines.extend(f"- `{query}`" for query in queries)
    lines.extend(["", "## Evidence Mix", ""])
    lines.append(f"- By source: `{json.dumps(by_source, sort_keys=True)}`")
    lines.append(f"- By type: `{json.dumps(by_type, sort_keys=True)}`")
    lines.append(f"- By source intent: `{json.dumps(by_intent, sort_keys=True)}`")
    lines.append(f"- By source role: `{json.dumps(by_role, sort_keys=True)}`")
    lines.append(f"- By comment intent: `{json.dumps(by_comment_intent, sort_keys=True)}`")
    lines.append(f"- By strength: `{json.dumps(by_strength, sort_keys=True)}`")
    if quality_flags:
        lines.extend(["", "## Quality Flags", ""])
        lines.extend(f"- {flag}" for flag in quality_flags)
    if irrelevant_records:
        lines.extend(["", "## Irrelevant Records Excluded", ""])
        for item in irrelevant_records[:10]:
            quote = item["verbatim_quote"].replace("\n", " ")
            lines.append(f"- [{item['source']}] {quote} ({item['source_url']})")
    lines.extend(["", "## Candidate Customer Inputs (source review required)", ""])
    for item in top:
        quote = item["verbatim_quote"].replace("\n", " ")
        lines.append(f"- [{item['source']}/{item.get('source_role', 'unknown')}/{item['strength']}/{item['evidence_type']}] {quote} ({item['source_url']})")
    lines.extend(
        [
            "",
            "## Analyst Warnings",
            "",
            "- This script collects raw signals. It does not prove willingness to pay.",
            "- Treat weak evidence as leads for interviews, not as validation.",
            "- Counter-evidence and quiet communities are important; absence of complaints can mean the search plan is wrong.",
        ]
    )
    if args.research_mode == "discovery":
        lines.extend(
            [
                "- This is a market-discovery collection. Do not treat it as evidence that any candidate is underserved until the synthesized report compares recurring pain, workarounds, and current alternatives.",
            ]
        )
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def provider_alerts(provider_summaries: dict[str, Any]) -> list[str]:
    alerts: list[str] = []
    for provider, summary in provider_summaries.items():
        status = summary.get("status")
        if status in {"ok", None}:
            continue
        if status == "missing_credentials":
            alerts.append(f"`{provider}` did not run because credentials are missing. Add the required key(s), then rerun validation.")
        elif status == "insufficient_credits":
            credits = summary.get("credits_remaining_at_start")
            credit_note = f" (balance at run start: {credits})" if credits is not None else ""
            alerts.append(
                f"`{provider}` stopped because its paid credits are exhausted{credit_note}. "
                "Top up the provider account to restore this coverage. Continue with valid fallbacks, preserve the source gap, "
                "and rerun this provider after a reported top-up; never treat the gap as absence of demand."
            )
        elif status == "billing_required":
            alerts.append(f"`{provider}` is blocked by billing, missing credits, or quota. Add credits or switch providers before trusting source coverage.")
        elif status == "permission_denied":
            alerts.append(f"`{provider}` returned permission denied. Check key scopes, account plan, zone permissions, or endpoint access.")
        elif status == "account_verification_required":
            message = summary.get("provider_status_message") or "Account verification is required before this API can be used."
            alerts.append(f"`{provider}` account verification required: {message}")
        elif status == "network_blocked_or_sandboxed":
            alerts.append(f"`{provider}` could not be reached from this environment. This may be sandbox/network blocking rather than bad credentials.")
        elif status == "rate_limited":
            alerts.append(f"`{provider}` is rate limited. Wait, reduce limits, or use a fallback provider.")
        elif status == "unsupported":
            alerts.append(f"`{provider}` is unsupported by this collector configuration.")
        elif status == "missing_cli":
            required = ", ".join(summary.get("required_cli", [])) or "required CLI"
            alerts.append(f"`{provider}` did not run because {required} is not installed or not on PATH.")
        elif status == "no_input":
            required = summary.get("required_arg") or "required input"
            alerts.append(f"`{provider}` did not run because no input was provided. Supply {required} when requesting this provider.")
        elif status == "login_required_or_failed":
            alerts.append(f"`{provider}` did not return usable records. This source is login/cookie-backed; check the browser session, account restrictions, and raw output before relying on China social coverage.")
        elif status == "warn":
            alerts.append(f"`{provider}` ran through a limited fallback route. Inspect `active_backend` and raw output before treating zero records as absence of evidence.")
        else:
            alerts.append(f"`{provider}` failed with status `{status}`. Inspect raw provider output before relying on the run.")
    return alerts


def remaining_tasks(provider_summaries: dict[str, Any], quality_flags: list[str]) -> list[dict[str, str]]:
    """Explicit unresolved work, never a claim that a missing source disproves demand."""
    tasks = []
    for provider, summary in provider_summaries.items():
        status = summary.get("status", "unknown")
        if status == "ok":
            continue
        action = ("Review the request limit and rerun this provider within the approved scope."
                  if status == "request_budget_exhausted" else
                  "Report the top-up route, continue valid fallbacks, and preserve this source gap until rerun."
                  if status in {"billing_required", "insufficient_credits"} else
                  "Resolve provider coverage and rerun or record an explicit source gap.")
        tasks.append({"provider": provider, "status": str(status), "action": action})
    tasks.extend({"provider": "evidence_quality", "status": "unresolved", "action": flag}
                 for flag in quality_flags)
    return tasks


def quality_summary(records: list[dict[str, Any]], provider_summaries: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    # Source intent is a heuristic discovery label; the collector cannot verify
    # the author's segment or firsthand account. Semantic review happens later.
    candidate_pain_count = sum(1 for record in records if record.get("source_intent") == "user_pain")
    if candidate_pain_count:
        flags.append(f"{candidate_pain_count} candidate user-pain item(s) require semantic source and target-segment review; none are validated target-customer pain by collection alone.")
    reddit_count = sum(1 for record in records if record.get("source") == "reddit")
    editorialish_count = sum(
        1
        for record in records
        if record.get("source_intent") in {"competitor_content", "editorial_content", "official_provider"}
    )
    if reddit_count == 0:
        flags.append("No relevant Reddit records survived filtering; do not infer community pain from this run.")
    flags.append("No reviewed target-customer user-pain records established by collection; evidence is source discovery, not demand validation.")
    if records and editorialish_count / len(records) >= 0.6:
        flags.append("Most records are competitor, editorial, or provider content; treat as category mapping, not customer evidence.")
    weak_count = sum(1 for record in records if record.get("strength") == "weak")
    unknown_intent_count = sum(1 for record in records if record.get("source_intent") == "unknown")
    if records and weak_count / len(records) >= 0.75:
        flags.append(f"Most relevant records are weak ({weak_count}/{len(records)}); use this run to shape interviews, not to validate purchase intent.")
    if records and unknown_intent_count / len(records) >= 0.25:
        flags.append(f"Many records have unknown source intent ({unknown_intent_count}/{len(records)}); inspect raw sources before making customer-evidence claims.")
    trends = [record for record in records if record.get("source") == "google_trends"]
    if trends and all('"value": 0' in record.get("text", "") or '"value": 1' in record.get("text", "") for record in trends):
        flags.append("Google Trends signals are very low for the tested phrases.")
    for provider, summary in provider_summaries.items():
        if summary.get("status") == "ok" and summary.get("record_count", 0) == 0:
            flags.append(f"{provider} API worked but produced zero relevant records.")
    return flags


def write_user_review_plan(run_dir: Path, args: argparse.Namespace, records: list[dict[str, Any]], quality_flags: list[str]) -> None:
    top_user_pain = [
        record
        for record in records
        if record.get("source_intent") == "user_pain"
    ][:10]
    decision_questions = [
        record
        for record in records
        if record.get("comment_intent") == "decision_question"
    ][:8]
    segment_label = args.customer_segment or "[unresolved: market discovery]"
    lines = [
        "# User Review Plan",
        "",
        f"- Topic: {args.topic}",
        f"- Segment under test: {segment_label}",
        "",
        "## Founder Checkpoints",
        "",
        "Interaction rule: ask the founder exactly one question at a time. Do not bundle multiple questions into one message.",
        "",
    ]
    if args.research_mode == "discovery":
        lines.extend(
            [
                "1. Do not ask the founder to choose a solution before synthesis.",
                "2. First synthesize candidate problem-segment pockets in `market-discovery-report.md`.",
                "3. Then ask one question: `Which path should we take next: validate Candidate [X], broaden/narrow the market scope, extend a named source gap, or stop?`",
            ]
        )
    else:
        lines.extend(
            [
                "1. First ask: `Which evidence item below feels most like real buyer pain to you?`",
                "2. After the answer, ask: `Which single assumption would most change your decision if false?`",
                "3. After the answer, ask: `Should the next research focus on interviews, narrower segment evidence, or competitor flow teardown?`",
                "4. Define the pass/fail threshold only after the user has answered the prior questions.",
            ]
        )
    lines.extend(
        [
        "",
        "## Quality Flags To Discuss",
        "",
        ]
    )
    if quality_flags:
        lines.extend(f"- {flag}" for flag in quality_flags)
    else:
        lines.append("- No automatic quality flags, but still review source mix and evidence strength manually.")
    lines.extend(
        [
            "",
            "## Candidate User-Pain Items For Source and Segment Review",
            "",
        ]
    )
    for idx, record in enumerate(top_user_pain, start=1):
        quote = record.get("verbatim_quote", "").replace("\n", " ")
        lines.append(f"{idx}. [{record.get('source')}/{record.get('evidence_type')}/{record.get('strength')}] {quote} ({record.get('source_url')})")
    if not top_user_pain:
        lines.append("- No direct user-pain records found. Treat the run as source discovery only.")
    lines.extend(
        [
            "",
            "## Candidate Decision Questions — Review Segment Fit Before Interview Probes",
            "",
        ]
    )
    for idx, record in enumerate(decision_questions, start=1):
        quote = record.get("verbatim_quote", "").replace("\n", " ")
        lines.append(f"{idx}. {quote} ({record.get('source_url')})")
    if not decision_questions:
        lines.append("- No decision-question records found.")
    if args.research_mode == "discovery":
        lines.extend(
            [
                "",
                "## User Decision Required",
                "",
                "Do not draw a business-viability conclusion from this collection. Finish the market-discovery report, then ask the single routing question above.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Suggested Interview Prompts",
                "",
                f"- Tell me about the last time you needed to handle `{args.topic}`.",
                "- What triggered the decision and what did you do first?",
                "- Which sources or people did you trust, and which did you avoid?",
                "- What felt risky, confusing, or too time-consuming?",
                "- Which alternatives, manual workarounds, or do-nothing options did you consider?",
                "- What would have made the process materially easier or more reliable?",
                "- What concrete behavior would show enough urgency to change or pay?",
                "",
                "## User Decision Required",
                "",
                "Before drawing a business-viability conclusion, ask the user to choose one next action:",
                "",
                "- Recommended if public evidence is mostly weak: `Interview` - recruit 8-12 people matching the tightest segment and run the prompts above.",
                "- `Narrow Segment`: pick one trigger event and rerun evidence collection with narrower keywords.",
                "- `Competitor Deep Dive`: inspect product flows and pricing for the top 3 direct competitors.",
                "- `Stop`: evidence is too weak or the segment is not reachable enough.",
            ]
        )
    (run_dir / "user_review_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_assumptions(run_dir: Path, args: argparse.Namespace, queries: list[str]) -> None:
    sample_queries = queries[:20]
    lines = [
        "# Assumptions To Verify",
        "",
        "Review these before interpreting the research output. If any assumption is wrong, rerun with corrected inputs.",
        "",
        "## Inferred Inputs",
        "",
        f"- Geography: `{args.geo}`",
        f"- Language: `{args.language}`",
        f"- Segment phrase used for fit judgment: `{args.customer_segment or '[unresolved: market discovery]'}`",
        f"- Topic phrase: `{args.topic}`",
        f"- Problem keywords: `{args.problem_keywords or 'not provided'}`",
        f"- Workaround keywords: `{args.workaround_keywords or 'not provided'}`",
        "",
        "## Working Assumptions",
        "",
        "- Query language is an initial approximation of how people may describe the job, frustration, and workaround; inspect it before trusting coverage.",
        "- The stated geography and language define the evidence scope; do not generalize findings beyond it.",
        "- Public posts, comments, and search results are treated as signals for interview design, not proof of willingness to pay.",
        "- Competitor/editorial/provider content is treated as category context, not customer pain.",
        "- Weak evidence requires user review before it can influence a business decision.",
        "- Coverage reflects who actually posts on the indexed sources (forums, Reddit, YouTube, search). Reachability bias: offline-first, older, or less-online demographics may appear silent even when their pain is real; read low signal for such segments as a coverage question, not absence of pain.",
        "",
        "## Explicitly Not Resolved By This Run",
        "",
        "- Legal, regulatory, and operational feasibility were not assessed in this run unless a source directly addressed them.",
        "- Unit economics, conversion, and willingness to pay were not validated.",
        "- A search or social signal alone cannot show market size, buyer identity, or a defensible gap.",
        "",
        "## Query Sample For Review",
        "",
    ]
    lines.extend(f"- `{query}`" for query in sample_queries)
    lines.extend(
        [
            "",
        "## User Verification Sequence",
        "",
        "Closing-question rule for the agent: end every response with exactly one question — the first item below that is not yet answered — then wait for the user's reply before asking the next. Never stack multiple questions in one response. Mark items as resolved as the user answers them.",
        "",
        "Ask in this order unless the user redirects:",
        "",
        ]
    )
    if args.research_mode == "discovery":
        lines.extend(
            [
                "1. Is the stated market scope and geography the right place to look first?",
                "2. After synthesis, which candidate problem-segment pocket should enter focused validation, if any?",
                "",
                "Recommended next research: let the user choose one candidate, change scope, extend a source gap, or stop. Do not turn discovery signals into a startup thesis automatically.",
            ]
        )
    else:
        lines.extend(
            [
                "1. Is the segment too broad, or should the run focus on one trigger event?",
                "2. Are these terms representative of how your target users would search or complain?",
                "3. Should a different geography or language be separated from this evidence set?",
                "4. Are the named alternatives true substitutes for the chosen problem?",
                "5. Which assumption above would most change your decision if false?",
                "",
                "Recommended next research if any answer is uncertain: narrow the segment to one trigger event and rerun evidence before competitor interpretation.",
            ]
        )
    (run_dir / "assumptions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_research_plan(run_dir: Path, args: argparse.Namespace, queries: list[str], providers: list[str]) -> None:
    trend_preview = trend_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    lines = [
        "# Research Plan",
        "",
        "This plan is generated before provider collection so the research flow has an explicit plan step before evidence interpretation.",
        "",
        "## Objective",
        "",
        (
            f"Discover candidate customer problems, workarounds, and segments in `{args.topic}` before choosing a validation hypothesis."
            if args.research_mode == "discovery"
            else f"Test whether public evidence supports the hypothesis behind `{args.topic}` for `{args.customer_segment}`."
        ),
        "",
        "## Current Assumptions",
        "",
        f"- Geography/language: `{args.geo}/{args.language}`",
        "- Public evidence can identify pain patterns and interview targets, but cannot validate willingness to pay alone.",
        "- Weak evidence should trigger user review and interviews, not a viability conclusion.",
        "- User interaction should ask exactly one question at a time.",
        "",
        "## Provider Plan",
        "",
    ]
    lines.extend(f"- `{provider}`" for provider in providers)
    if "sonar" not in providers and app_market_relevant(args.topic, args.problem_keywords, args.workaround_keywords):
        lines.extend(
            [
                "",
                "## Enrichment Checkpoint",
                "",
                "This appears to have an app-market angle. Ask the user one question before spending Sonar credits:",
                "",
                "`Do you want app-store enrichment via Sonar for keyword demand, app reviews, and competitor app context?`",
                "",
                "If yes, rerun with explicit `--providers default,sonar`. Add `--sonar-apps ios:<id>,android:<package>` when competitor app review or revenue evidence is needed.",
            ]
        )
    lines.extend(
        [
            "",
            "## Query Strategy",
            "",
            "- Start with problem-first terms before solution-led terms.",
            "- Include German umlaut and ASCII variants where relevant.",
            "- Keep Google Trends terms short and search-like.",
            "- Treat competitor/editorial/provider pages as category context, not user demand.",
            "",
            "## Google Trends Preview",
            "",
        ]
    )
    lines.extend(f"- `{term}`" for term in trend_preview)
    lines.extend(
        [
            "",
            "## Query Sample",
            "",
        ]
    )
    lines.extend(f"- `{query}`" for query in queries[:25])
    lines.extend(
        [
            "",
            "## Planned User Checkpoint",
            "",
            "Ask one question after collection:",
            "",
            (
                "`Which path should we take next: validate Candidate [X], broaden/narrow the market scope, extend a named source gap, or stop?`"
                if args.research_mode == "discovery"
                else "`Which evidence item feels most like real buyer pain to you?`"
            ),
            "",
            (
                "Recommended next research: synthesize source-backed candidates before asking the user to choose one; do not make a business-viability conclusion."
                if args.research_mode == "discovery"
                else "Recommended next research if evidence is mostly weak: run 8-12 customer interviews before making a business-viability conclusion."
            ),
        ]
    )
    (run_dir / "research_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_provider_routing() -> dict[str, Any]:
    """Read the latest provider-doctor summary so runs record which backend actually served each source family."""
    doctor_path = ROOT / "projects" / "_infra" / "provider-doctor" / "doctor.summary.json"
    legacy_path = ROOT / "projects" / "research" / "evidence-scout" / "provider-doctor" / "doctor.summary.json"
    if not doctor_path.exists() and legacy_path.exists():
        # Pre-migration location; removed in a later cleanup.
        doctor_path = legacy_path
    try:
        data = json.loads(doctor_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    families = data.get("source_families") if isinstance(data, dict) else None
    if not isinstance(families, dict):
        return {}
    routing: dict[str, str] = {}
    for family, item in families.items():
        if isinstance(item, dict) and item.get("active_backend"):
            routing[str(family)] = str(item["active_backend"])
    return {"generated_at": data.get("generated_at"), "families": routing}


PROVIDER_ROUTING_FAMILY = {
    "reddit": "reddit",
    "serpapi_google_trends": "google_trends",
    "youtube": "youtube",
    "firecrawl": "web_search",
    "brave_search": "web_search",
    "serper_search": "web_search",
    "x": "social",
    "xai_x_search": "social",
    "scrapecreators": "social",
    "sonar": "app_store",
    "itunes_reviews": "app_store",
    "trustpilot_reviews": "customer_reviews",
    "google_places_reviews": "customer_reviews",
    "hn": "founder_community",
    "google_autocomplete": "founder_community",
    "github": "github_issues",
    "china_bilibili": "china_public_native",
    "china_v2ex": "china_public_native",
    "china_web": "china_web",
    "china_xiaohongshu": "china_social",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect normalized business-idea evidence.")
    parser.add_argument("--topic", required=True, help="Business idea, problem, category, or job-to-be-done.")
    parser.add_argument("--customer-segment", default="", help="Target customer segment to test.")
    parser.add_argument("--segment-keywords", default="", help="Short, comma-separated target-audience phrases in the source language; appended to every validation query. Not the full segment brief.")
    parser.add_argument(
        "--research-mode",
        choices=["validation", "discovery"],
        default="validation",
        help="Use discovery only before a customer/problem candidate has been selected; default validation tests a chosen hypothesis.",
    )
    parser.add_argument("--hypothesis-id", default="H1", help="Hypothesis label for normalized records.")
    parser.add_argument("--sampling-frame", choices=["topic_led_voc", "entity_led_feedback"], default="topic_led_voc", help="Sampling frame for generic providers. Entity-led collection also requires --subject-entity-id.")
    parser.add_argument("--subject-entity-id", default="", help="Exact entity ID for a generic entity-led collection run.")
    parser.add_argument("--entity-source-url", default="", help="Exact reviewed public page URL for generic entity capture through Firecrawl, not a broad search query.")
    parser.add_argument("--entity-source-lane", choices=["external_forums_communities", "independent_review_platforms", "company_hosted_supplier_context"], default="", help="Source-plan lane binding for --entity-source-url.")
    parser.add_argument("--query-limit", type=int, default=12, help="Reproducible query sample size per supported search provider; increase for missing coverage, not a spending cap.")
    parser.add_argument("--days", type=int, default=30, help="Lookback window for recency-aware sources.")
    parser.add_argument("--max-http-requests", type=int, default=100,
                        help="Per-run cap on shared HTTP helper calls; excludes SDK/CLI traffic. Default: 100.")
    parser.add_argument("--fresh-http", action="store_true",
                        help="Disable in-run reuse of identical successful GET requests.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum normalized records per provider.")
    parser.add_argument(
        "--problem-keywords",
        default="",
        help="Comma-separated job/pain phrases from idea-grill, e.g. client updates,status reports,scattered email.",
    )
    parser.add_argument(
        "--workaround-keywords",
        default="",
        help="Comma-separated current workaround phrases, e.g. spreadsheet,email follow-up,manual status report.",
    )
    parser.add_argument(
        "--providers",
        default="default",
        help="Comma-separated providers. Use default, social, entity_reviews, local_web, free_community, china_public, china_social, china, all, or explicit names including trustpilot_reviews and google_places_reviews.",
    )
    parser.add_argument(
        "--local-extract-url-limit",
        type=int,
        default=3,
        help="Maximum discovered URLs to pass to local extractors such as crawl4ai or Scrapling. Keep low to control context and runtime.",
    )
    parser.add_argument(
        "--local-extract-char-limit",
        type=int,
        default=1500,
        help="Maximum extracted characters normalized per local extraction record.",
    )
    parser.add_argument(
        "--local-extract-timeout",
        type=int,
        default=60,
        help="Timeout in seconds for each local extractor CLI call.",
    )
    parser.add_argument(
        "--document-paths",
        default="",
        help="Comma-separated local paths or URLs for MarkItDown document ingestion. Used only with --providers markitdown.",
    )
    parser.add_argument(
        "--document-limit",
        type=int,
        default=5,
        help="Maximum documents to convert with MarkItDown in one run.",
    )
    parser.add_argument(
        "--china-comment-video-limit",
        type=int,
        default=3,
        help="Maximum videos to enrich with comments for explicit China comment providers.",
    )
    parser.add_argument(
        "--china-comment-limit",
        type=int,
        default=10,
        help="Maximum comments to fetch per video for explicit China comment providers.",
    )
    parser.add_argument(
        "--sonar-apps",
        default="",
        help="Deprecated for review collection: targeted apps must use --sonar-entity-apps plus a reviewed source plan.",
    )
    parser.add_argument(
        "--sonar-entity-apps",
        default="",
        help="Entity-bound app mappings for VOC, formatted entity_id=ios:123456789 or entity_id=android:com.example.app.",
    )
    parser.add_argument(
        "--sonar-stores",
        default="ios,android",
        help="Comma-separated app stores for Sonar keyword enrichment: ios,android.",
    )
    parser.add_argument(
        "--sonar-keyword-limit",
        type=int,
        default=3,
        help="Maximum app-store keywords to send to Sonar per store. Keep low because keyword metrics consume credits per keyword.",
    )
    parser.add_argument(
        "--sonar-review-max-rating",
        type=int,
        default=5,
        help="Maximum app-review rating. Defaults to 5 so favorable and unfavorable solution feedback remain eligible.",
    )
    parser.add_argument(
        "--sonar-include-revenue",
        action="store_true",
        help="Also fetch Sonar revenue estimates for --sonar-apps. Treat as weak monetization context.",
    )
    parser.add_argument("--x-handles", default="", help="Comma-separated X handles for handle-bounded Grok/X Search or ScrapeCreators Twitter user-tweet enrichment.")
    parser.add_argument(
        "--social-per-endpoint",
        type=int,
        default=10,
        help="Maximum records each ScrapeCreators endpoint may contribute. Prevents one productive platform from starving the others.",
    )
    parser.add_argument(
        "--fb-groups",
        default="",
        help="Comma-separated reviewed public Facebook group URLs for ScrapeCreators group-post collection.",
    )
    parser.add_argument(
        "--fb-pages",
        default="",
        help="Comma-separated reviewed public Facebook page/profile URLs for ScrapeCreators page-post and reel collection.",
    )
    parser.add_argument(
        "--fb-entity-pages",
        default="",
        help="Comma-separated entity_id=reviewed Facebook Page URL mappings for entity-led company-comment collection; requires the customer-feedback source plan and community authorization bundle.",
    )
    parser.add_argument(
        "--community-capture-authorization",
        default="",
        help="Fresh capture_authorization.json from review_community_candidates.py; required for --fb-groups/--fb-pages.",
    )
    parser.add_argument(
        "--community-verified-sources",
        default="",
        help="Matching verified_communities.json from review_community_candidates.py; required for --fb-groups/--fb-pages.",
    )
    parser.add_argument(
        "--community-review-receipt",
        default="",
        help="Matching community_review_current.json receipt from review_community_candidates.py; required for --fb-groups/--fb-pages.",
    )
    parser.add_argument(
        "--fb-max-posts",
        type=int,
        default=12,
        help="Maximum posts to fetch per Facebook group/page via cursor pagination (hard cap 60; 3 posts per API call, 1 credit per call).",
    )
    parser.add_argument(
        "--ig-handles",
        default="",
        help="Comma-separated reviewed entity_id=handle mappings for company Instagram profiles; requires --customer-feedback-source-plan.",
    )
    parser.add_argument(
        "--customer-feedback-source-plan",
        default="",
        help="Customer-feedback source plan containing human-accepted entity locators used to authorize entity social capture.",
    )
    parser.add_argument(
        "--ig-hashtags",
        default="",
        help="Comma-separated Instagram hashtags (without #) for ScrapeCreators hashtag search.",
    )
    parser.add_argument(
        "--social-comments",
        action="store_true",
        help="Also fetch comments on the top collected Facebook/Instagram posts (extra credits; pain language often lives in comments).",
    )
    parser.add_argument(
        "--comments-max",
        type=int,
        default=5,
        help="Maximum collected posts to enrich with comments when --social-comments is set.",
    )
    parser.add_argument(
        "--youtube-transcripts",
        action="store_true",
        help="Also fetch video transcripts via youtube_transcript_api (free, no API quota). Transcripts are creator voice, not customer voice.",
    )
    parser.add_argument(
        "--youtube-transcript-max",
        type=int,
        default=5,
        help="Maximum videos to fetch transcripts for when --youtube-transcripts is set. Keep low: YouTube can IP-throttle transcript requests.",
    )
    parser.add_argument("--x-from-date", help="ISO date/datetime for Grok/xAI X Search start date.")
    parser.add_argument("--x-to-date", help="ISO date/datetime for Grok/xAI X Search end date.")
    parser.add_argument("--itunes-app-ids", default="", help="Deprecated for review collection: targeted apps must use --itunes-entity-apps plus a reviewed source plan.")
    parser.add_argument("--itunes-entity-apps", default="", help="Comma-separated entity_id=Apple_app_id mappings for entity-led Apple review collection.")
    parser.add_argument("--itunes-locales", default="", help="Comma-separated COUNTRY:language storefront locales required with --itunes-entity-apps, e.g. DE:de,FR:fr.")
    parser.add_argument("--itunes-countries", default="", help="Comma-separated storefronts for itunes_reviews. Defaults to --geo.")
    parser.add_argument("--itunes-max-pages", type=int, default=2, help="Maximum RSS pages per app/country for itunes_reviews (~50 reviews/page).")
    parser.add_argument("--trustpilot-domains", default="", help="Comma-separated exact entity_id=domain mappings for public Trustpilot business-unit reviews.")
    parser.add_argument("--trustpilot-max-pages", type=int, default=2, help="Maximum public Trustpilot review pages per entity.")
    parser.add_argument("--google-place-ids", default="", help="Comma-separated exact entity_id=place_id mappings for Google Places review subsets.")
    parser.add_argument("--xai-model", default="grok-4.3", help="xAI/Grok model for xai_x_search provider.")
    parser.add_argument("--xai-prompt", help="Override prompt for xai_x_search provider.")
    parser.add_argument("--geo", default="AUTO", help="Country/region code for providers that support geography. Use AUTO to infer from topic/segment.")
    parser.add_argument("--language", default="AUTO", help="Language code for providers that support language filtering. Use AUTO to infer from topic/segment.")
    parser.add_argument("--case", default="", help="Registered case ID within --workspace.")
    parser.add_argument("--out-dir", default="", help="Optional output directory.")
    parser.add_argument("--workspace", default="", help="Project workspace path. Defaults to projects/<project-slug>.")
    parser.add_argument("--legacy-output", action="store_true", help="Removed: the projects/research/evidence-scout layout is gone (now projects/_archive, read-only). Use --out-dir for an explicit path.")
    args = parser.parse_args()
    if args.research_mode == "validation":
        if args.customer_segment.strip().casefold() in {"", "unknown", "unspecified", "unresolved", "tbd", "[unresolved: market discovery]"}:
            parser.error("validation requires --customer-segment; use --research-mode discovery before selecting a target hypothesis")
        if not csv_terms(args.segment_keywords):
            args.segment_keywords = ",".join(segment_modifiers(args.customer_segment))
        if not csv_terms(args.segment_keywords):
            parser.error("validation requires --segment-keywords for the selected target; use short source-language audience terms")
    if args.max_http_requests < 1:
        parser.error("--max-http-requests must be positive")
    if args.query_limit < 1 or args.limit < 1:
        parser.error("--query-limit and --limit must be positive")
    if args.sampling_frame == "entity_led_feedback" and not args.subject_entity_id.strip():
        parser.error("--sampling-frame entity_led_feedback requires --subject-entity-id")
    if args.trustpilot_max_pages < 1:
        parser.error("--trustpilot-max-pages must be positive")
    try:
        parse_entity_locator_pairs(args.trustpilot_domains, "--trustpilot-domains")
        parse_entity_locator_pairs(args.google_place_ids, "--google-place-ids")
        parse_entity_locator_pairs(args.itunes_entity_apps, "--itunes-entity-apps")
        parse_entity_store_apps(args.sonar_entity_apps, "--sonar-entity-apps")
        if args.ig_handles:
            parse_entity_locator_pairs(args.ig_handles, "--ig-handles")
    except ValueError as exc:
        parser.error(str(exc))
    return args


def main() -> int:
    args = parse_args()
    inferred_geo, inferred_language = infer_geo_language(args.topic, args.customer_segment, args.problem_keywords, args.workaround_keywords)
    if args.geo.upper() == "AUTO":
        args.geo = inferred_geo
    if args.language.upper() == "AUTO":
        args.language = inferred_language
    run_dir, workspace = resolve_run_dir(
        topic=args.topic,
        workspace_arg=args.workspace,
        case_id=getattr(args, "case", ""),
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="market_research/pain_points/runs",
        legacy_subdir="runs",
        customer_segment=args.customer_segment,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    if workspace:
        update_stage(
            workspace,
            "evidence_collection", run_dir=run_dir,
            status="in_progress",
            gate_result="not_run",
            next_action="Complete provider collection and inspect source quality.",
        )
    create_run_manifest(
        run_dir,
        subject=args.topic,
        run_type="evidence_collection",
        stage="evidence_collection",
        sources=selected_providers(args.providers),
        next_action="Complete provider collection and inspect source quality.",
    )

    queries = query_plan(
        args.topic,
        args.customer_segment,
        args.problem_keywords,
        args.workaround_keywords,
        args.geo,
        args.language,
        args.research_mode,
        args.segment_keywords,
    )
    requested_providers = selected_providers(args.providers)
    write_research_plan(run_dir, args, queries, requested_providers)
    provider_funcs = {
        "reddit": collect_reddit,
        "serpapi_google_trends": collect_serpapi_google_trends,
        "serper_search": collect_serper_search,
        "youtube": collect_youtube,
        "firecrawl": collect_firecrawl,
        "brave_search": collect_brave_search,
        "hn": collect_hn,
        "github": collect_github,
        "google_autocomplete": collect_google_autocomplete,
        "itunes_reviews": collect_itunes_reviews,
        "trustpilot_reviews": collect_trustpilot_reviews,
        "google_places_reviews": collect_google_places_reviews,
        "crawl4ai": collect_crawl4ai,
        "markitdown": collect_markitdown,
        "scrapling": collect_scrapling,
        "x": collect_x,
        "xai_x_search": collect_xai_x_search,
        "scrapecreators": collect_scrapecreators,
        "sonar": collect_sonar,
        "china_bilibili": collect_china_bilibili,
        "china_bilibili_comments": collect_china_bilibili_comments,
        "china_v2ex": collect_china_v2ex,
        "china_web": collect_china_web,
        "china_xiaohongshu": collect_china_xiaohongshu,
    }
    records: list[dict[str, Any]] = []
    provider_summaries: dict[str, Any] = {}
    with request_budget(args.max_http_requests, reuse_gets=not args.fresh_http) as budget:
        for provider in requested_providers:
            if args.sampling_frame == "entity_led_feedback" and provider not in {"firecrawl", "itunes_reviews", "trustpilot_reviews", "google_places_reviews", "scrapecreators", "sonar"}:
                provider_summaries[provider] = {"status": "capture_gate_blocked", "record_count": 0, "reason": "Generic entity capture requires firecrawl and an exact reviewed URL; broad search remains topic-led discovery."}
                continue
            func = provider_funcs.get(provider)
            if not func:
                provider_summaries[provider] = {"status": "unsupported", "record_count": 0}
                continue
            if budget.requests >= budget.max_requests:
                provider_summaries[provider] = {"status": "request_budget_exhausted", "record_count": 0}
                continue
            blocked_before = budget.blocked_requests
            provider_records, provider_summary = func(args, queries, run_dir)
            # Store the route actually used for this retrieval, rather than adding
            # a hypothetical backend after collection. Language fields express the
            # requested search scope; they do not claim a language detector ran.
            for record in provider_records:
                record["retrieval_backend"] = provider
                record["query_language"] = args.language
                record.setdefault("source_language", "und")
                record["output_language"] = "en"
                if not record.get("collection_locale"):
                    record["collection_locale"] = runtime_locale(args)
                for membership in record.get("discovery_memberships", []):
                    membership.setdefault("collection_locale", record["collection_locale"])
            accepted, rejected = accepted_records(provider_records)
            relevant_provider_records = [record for record in accepted if record.get("relevance") != "irrelevant"]
            irrelevant_provider_records = [record for record in accepted if record.get("relevance") == "irrelevant"]
            records.extend(accepted)
            provider_summary["record_count"] = len(relevant_provider_records)
            provider_summary["irrelevant_count"] = len(irrelevant_provider_records)
            provider_summary["rejected_record_count"] = len(rejected)
            if rejected:
                provider_summary["record_rejections"] = rejected[:10]
                provider_summary["status"] = "partial" if accepted else "invalid_records"
            if budget.blocked_requests > blocked_before:
                provider_summary["status"] = "request_budget_exhausted"
            provider_summaries[provider] = provider_summary

    relevant_records = [record for record in records if record.get("relevance") != "irrelevant"]
    irrelevant_records = [record for record in records if record.get("relevance") == "irrelevant"]
    routing = load_provider_routing()
    append_jsonl(run_dir / "evidence.jsonl", relevant_records)
    append_jsonl(run_dir / "irrelevant.jsonl", irrelevant_records)
    alerts = provider_alerts(provider_summaries)
    quality_flags = quality_summary(relevant_records, provider_summaries)
    remaining = remaining_tasks(provider_summaries, quality_flags)
    budget_exhausted = any(s.get("status") == "request_budget_exhausted" for s in provider_summaries.values())
    summary = {
        "run_dir": str(run_dir),
        "topic": args.topic,
        "customer_segment": args.customer_segment,
        "segment_keywords": args.segment_keywords,
        "research_mode": args.research_mode,
        "hypothesis_id": args.hypothesis_id,
        "days": args.days,
        "geo": args.geo,
        "language": args.language,
        "providers_requested": selected_providers(args.providers),
        "provider_routing": routing or None,
        "record_count": len(relevant_records),
        "irrelevant_count": len(irrelevant_records),
        "providers": provider_summaries,
        "needs_user_attention": alerts,
        "request_budget": budget.summary(),
        "remaining_tasks": remaining,
        "collection_complete": not remaining,
        "quality_flags": quality_flags,
        "outputs": {
            "evidence_jsonl": str(run_dir / "evidence.jsonl"),
            "irrelevant_jsonl": str(run_dir / "irrelevant.jsonl"),
            "report": str(run_dir / "report.md"),
            "research_plan": str(run_dir / "research_plan.md"),
            "user_review_plan": str(run_dir / "user_review_plan.md"),
            "assumptions": str(run_dir / "assumptions.md"),
            "raw_dir": str(run_dir / "raw"),
        },
    }
    write_json(run_dir / "summary.json", summary)
    write_report(run_dir, args, queries, relevant_records, irrelevant_records, provider_summaries)
    write_assumptions(run_dir, args, queries)
    write_user_review_plan(run_dir, args, relevant_records, quality_flags)
    if workspace:
        failures = [
            {"provider": provider, "failure_class": str(result.get("status", "failed")), "confidence_impact": "high"}
            for provider, result in provider_summaries.items()
            if result.get("status") not in {"ok", "not_run"}
        ]
        gate_result = "fail" if budget_exhausted or not relevant_records else ("conditional_pass" if failures or quality_flags else "pass")
        update_stage(
            workspace,
            "evidence_collection", run_dir=run_dir,
            status="blocked" if budget_exhausted else ("failed" if gate_result == "fail" else "passed"),
            gate_result=gate_result,
            artifacts=[run_dir / "report.md", run_dir / "summary.json", run_dir / "evidence.jsonl", run_dir / "assumptions.md"],
            provider_failures=failures,
            open_gaps=quality_flags,
            next_action="Resolve remaining_tasks in summary.json before continuing collection." if budget_exhausted else "Review evidence and interview users before synthesis." if gate_result != "pass" else "Proceed to competitor discovery or opportunity-risk design.",
        )
    update_run_manifest(
        run_dir,
        stage="evidence_collection",
        stage_status="blocked" if budget_exhausted else ("failed" if not relevant_records else "passed"),
        gate_result="fail" if budget_exhausted or not relevant_records else ("conditional_pass" if (provider_summaries and any(s.get("status") not in {"ok", "not_run"} for s in provider_summaries.values())) or quality_flags else "pass"),
        artifacts=[run_dir / "report.md", run_dir / "summary.json", run_dir / "evidence.jsonl"],
        open_gaps=quality_flags,
        next_action="Resolve remaining_tasks in summary.json before continuing collection." if budget_exhausted else "Review evidence and interview users before synthesis." if not relevant_records or quality_flags else "Proceed to competitor discovery or opportunity-risk design.",
        event="evidence_collection_budget_exhausted" if budget_exhausted else "evidence_collection_completed",
        record_count=len(relevant_records),
        source_count=len([s for s in provider_summaries.values() if s.get("status") == "ok"]),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 2 if budget_exhausted else (0 if relevant_records else 1)


if __name__ == "__main__":
    raise SystemExit(main())
