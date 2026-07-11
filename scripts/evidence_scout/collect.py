#!/usr/bin/env python3
"""Collect normalized market evidence from script-accessible providers.

This is intentionally API-first and dependency-light so the same script can be
called from Codex, OpenCode, Claude Code, CI, or a plain terminal.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "scripts" / "validate_apis"
REGISTRY_DIR = Path(__file__).resolve().parent / "registries"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import (  # noqa: E402
    fields_present,
    finish,
    get_secret,
    http_get,
    http_post,
    now_iso,
    redact_sensitive,
    status_from_response,
    with_query,
)
from workspace import resolve_run_dir, update_stage  # noqa: E402


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


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def csv_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def infer_geo_language(topic: str, customer_segment: str, problem_keywords: str = "", workaround_keywords: str = "") -> tuple[str, str]:
    text = " ".join([topic, customer_segment, problem_keywords, workaround_keywords]).lower()
    german_markers = [
        "germany",
        "german",
        "deutschland",
        "deutsche",
        "pkv",
        "gkv",
        "berufsun",
        "rückkehr",
        "rueckkehr",
        "voranfrage",
        "versicherung",
        "finanztip",
        "check24",
        "verivox",
    ]
    china_markers = [
        "china",
        "chinese",
        "cn",
        "小红书",
        "xiaohongshu",
        "bilibili",
        "b站",
        "zhihu",
        "知乎",
        "weibo",
        "微博",
        "douyin",
        "抖音",
        "v2ex",
        "微信",
        "wechat",
        "淘宝",
        "taobao",
        "京东",
        "jd.com",
    ]
    if any(marker in text for marker in german_markers):
        return "DE", "de"
    if any(marker in text for marker in china_markers):
        return "CN", "zh"
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
    phrase_variants = {
        "rueckkehr": "Rückkehr",
        "rückkehr": "Rueckkehr",
        "berufsunfaehigkeit": "Berufsunfähigkeit",
        "berufsunfähigkeit": "Berufsunfaehigkeit",
        "risikovoranfrage": "Risikovoranfrage",
        "voranfrage": "Voranfrage",
    }
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
    if not (geo.upper() == "DE" and any(marker in lower for marker in ["insurance", "versicherung", "pkv", "gkv", "bu", "berufsun"])):
        return []
    return expand_language_variants(
        [
            "PKV Entscheidung",
            "PKV wechseln",
            "PKV oder GKV",
            "BU Gesundheitsfragen",
            "anonyme Risikovoranfrage",
            "Makler Provision Vertrauen",
            "Honorarberater Versicherung",
            "Versicherungsmakler Vertrauen",
        ],
        geo,
        language,
    )


def query_plan(
    topic: str,
    customer_segment: str,
    problem_keywords: str = "",
    workaround_keywords: str = "",
    geo: str = "US",
    language: str = "en",
) -> list[str]:
    base = topic.strip()
    modifiers = segment_modifiers(customer_segment)
    problem_terms = problem_first_terms(topic, geo, language)
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
    return deduped


def trend_terms(topic: str, problem_keywords: str = "", workaround_keywords: str = "", geo: str = "US", language: str = "en") -> list[str]:
    """Google Trends terms should be phrases users would type, never segment prose."""
    seeded_terms = [*csv_terms(problem_keywords), *csv_terms(workaround_keywords)]
    terms = user_language_terms(topic if not seeded_terms else "", problem_keywords, workaround_keywords)
    if not seeded_terms:
        terms = inferred_search_terms(topic)
    terms = expand_language_variants(terms, geo, language)
    expansion_terms = demand_expansion_terms(topic, geo, language)
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
    if not (geo.upper() == "DE" and any(marker in lower for marker in ["pkv", "gkv", "bu", "berufsun", "insurance", "versicherung"])):
        return []
    return expand_language_variants(
        [
            "Private Krankenversicherung",
            "private Krankenversicherung Kosten",
            "PKV Kosten",
            "PKV Vergleich",
            "PKV Rechner",
            "GKV oder PKV",
            "Berufsunfähigkeitsversicherung",
            "BU Versicherung",
            "BU Gesundheitsfragen",
            "Versicherungsmakler",
            "Honorarberater Versicherung",
            "CHECK24 PKV",
            "Verivox PKV",
            "Finanztip PKV",
        ],
        geo,
        language,
    )


def social_terms(topic: str, problem_keywords: str = "", workaround_keywords: str = "", geo: str = "US", language: str = "en") -> list[str]:
    """Social search works best on compact pain/category/competitor phrases."""
    seeded_terms = [*csv_terms(problem_keywords), *csv_terms(workaround_keywords)]
    if not seeded_terms:
        return expand_language_variants(inferred_search_terms(topic), geo, language)[:3]
    return expand_language_variants(user_language_terms("", problem_keywords, workaround_keywords), geo, language)[:3]


def reddit_queries(args: argparse.Namespace, queries: list[str]) -> list[str]:
    topic_context = " ".join([args.topic, args.problem_keywords, args.workaround_keywords]).lower()
    if args.geo.upper() == "DE" and any(marker in topic_context for marker in ["pkv", "gkv", "berufsun", "versicherung"]):
        targeted = [
            "PKV subreddit:Finanzen",
            "GKV PKV subreddit:Finanzen",
            "Berufsunfähigkeitsversicherung subreddit:Finanzen",
            "Berufsunfaehigkeitsversicherung subreddit:Finanzen",
            "anonyme Risikovoranfrage subreddit:Finanzen",
            "Versicherungsmakler Provision subreddit:Finanzen",
            "PKV subreddit:Versicherung",
            "GKV PKV subreddit:Versicherung",
            "BU Gesundheitsfragen subreddit:Versicherung",
            "PKV subreddit:Krankenkassen",
            "PKV Beihilfe subreddit:beamte",
            "private health insurance Germany subreddit:germany",
            "health insurance Germany broker subreddit:germany",
        ]
        return targeted + queries[:4]
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
    if source not in {"reddit", "youtube_comment", "x", "tiktok", "instagram", "threads"}:
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
    if source in {"reddit", "youtube_comment", "x", "tiktok", "instagram", "threads"}:
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


def estimate_strength(text: str, engagement: dict[str, Any]) -> str:
    lower = text.lower()
    pain_terms = ["hate", "frustrated", "hard", "annoying", "pain", "struggle", "broken", "waste", "überfragt", "angst", "verzweifelt", "qual der wahl", "unmöglich", "kompliziert", "麻烦", "踩坑", "避雷", "难用", "不好用", "后悔", "崩溃", "不靠谱"]
    workaround_terms = ["workaround", "manually", "spreadsheet", "hack", "alternative", "recherche", "maklern", "quellen", "angebote", "tarife vergleichen", "手动", "表格", "凑合", "临时方案", "替代方案", "自己整理"]
    score = 0
    if any(term in lower for term in pain_terms):
        score += 1
    if any(term in lower for term in workaround_terms):
        score += 1
    if (engagement.get("upvotes") or 0) >= 25 or (engagement.get("comments") or 0) >= 10:
        score += 1
    if score >= 3:
        return "strong"
    if score == 2:
        return "medium"
    return "weak"


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
) -> dict[str, Any]:
    engagement = engagement or {}
    short_quote = " ".join(text.split())[:500]
    record_type = evidence_type or infer_evidence_type(text)
    record_strength = strength or estimate_strength(text, engagement)
    source_intent = infer_source_intent(source, source_url, text, record_type)
    comment_intent = infer_comment_intent(source, text, record_type)
    if source_intent in {"competitor_content", "editorial_content", "official_provider", "search_demand", "forum_discussion"} and record_strength != "irrelevant":
        record_strength = "weak"
    return {
        "source": source,
        "source_url": source_url,
        "retrieved_at": now_iso(),
        "query": query,
        "customer_segment": customer_segment,
        "hypothesis_id": hypothesis,
        "evidence_type": record_type,
        "source_intent": source_intent,
        "comment_intent": comment_intent,
        "text": text,
        "verbatim_quote": short_quote,
        "author_context": author_context,
        "engagement": {
            "upvotes": engagement.get("upvotes"),
            "comments": engagement.get("comments"),
            "views": engagement.get("views"),
            "likes": engagement.get("likes"),
        },
        "strength": record_strength,
        "relevance": relevance,
        "relevance_score": relevance_score,
        "relevance_notes": relevance_notes,
        "confidence_notes": confidence_notes
        or "Collected directly from source API/search result. Treat as signal, not proof of willingness to pay.",
        "raw_id": raw_id,
    }


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
    defaults = ["reddit", "serpapi_google_trends", "youtube", "serper_search", "firecrawl", "brave_search"]
    social = ["x", "scrapecreators"]
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
        elif part == "local_web":
            providers.extend(local_web)
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

    write_json(run_dir / "raw" / "reddit.json", redact_sensitive(raw))
    return records, {"status": "ok", "record_count": len(records), "fields": fields_present(raw)}


def collect_firecrawl(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    if not api_key:
        write_json(run_dir / "raw" / "firecrawl.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["FIRECRAWL_API_KEY_HGINVESTOR"]}

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_query_limit = max(2, args.limit // max(1, min(len(queries), 4)))
    for query in queries[:4]:
        response = http_post(
            "https://api.firecrawl.dev/v1/search",
            headers={"Authorization": f"Bearer {api_key}"},
            data={"query": query, "limit": per_query_limit, "scrapeOptions": {"formats": ["markdown"]}},
        )
        raw["searches"].append({"query": query, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        for item in body.get("data") or []:
            url = item.get("url") or item.get("sourceURL") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            title = item.get("title") or ""
            description = item.get("description") or ""
            markdown = item.get("markdown") or ""
            text = "\n\n".join(part for part in [title, description, markdown[:1500]] if part).strip()
            if not text:
                continue
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, query, url, item.get("siteName") or item.get("metadata", {}).get("siteName", ""))
            records.append(
                normalize_record(
                    source="forum",
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
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else status_from_response((raw["searches"][0] or {}).get("response", {})) if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "firecrawl.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


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


def collect_serper_search(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("SERPER_DEV_API_KEY", "SERPER_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": []}
    if not api_key:
        write_json(run_dir / "raw" / "serper_search.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SERPER_DEV_API_KEY"]}

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in [queries[0], queries[3], queries[6]][:3]:
        response = http_post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            data={"q": query, "num": min(max(args.limit, 1), 10), "gl": args.geo.lower(), "hl": args.language},
        )
        raw["searches"].append({"query": query, "response": response})
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        for item in body.get("organic", []) if isinstance(body, dict) else []:
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
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else status_from_response((raw["searches"][0] or {}).get("response", {})) if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "serper_search.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


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


def collect_youtube(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("YOUTUBE_API_KEY", "GOOGLE_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "searches": [], "comments": []}
    if not api_key:
        write_json(run_dir / "raw" / "youtube.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["YOUTUBE_API_KEY"]}

    records: list[dict[str, Any]] = []
    seen_videos: set[str] = set()
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
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break

    status = "ok" if records else status_from_response((raw["searches"][0] or {}).get("response", {})) if raw["searches"] else "failed"
    write_json(run_dir / "raw" / "youtube.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


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
    for key in ["search_item_list", "items", "results", "data", "reels", "videos", "posts"]:
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


def collect_scrapecreators(args: argparse.Namespace, queries: list[str], run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key_name, api_key = get_secret("SCRAPE_CREATORS_API_KEY", "SCRAPECREATORS_API_KEY")
    raw: dict[str, Any] = {"credential_source": key_name, "calls": []}
    if not api_key:
        write_json(run_dir / "raw" / "scrapecreators.json", raw)
        return [], {"status": "missing_credentials", "required_env": ["SCRAPE_CREATORS_API_KEY"]}

    terms = social_terms(args.topic, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    social_query = terms[0] if terms else args.topic
    endpoints = [
        ("tiktok", "https://api.scrapecreators.com/v1/tiktok/search/keyword", {"query": social_query, "date_posted": "month", "sort_by": "relevance", "trim": "true"}),
        ("instagram", "https://api.scrapecreators.com/v2/instagram/reels/search", {"query": social_query, "date_posted": "month", "page": 1}),
        ("threads", "https://api.scrapecreators.com/v1/threads/search", {"query": social_query, "trim": "true"}),
    ]
    for handle in [item.strip().lstrip("@") for item in args.x_handles.split(",") if item.strip()][:10]:
        endpoints.append(("x", "https://api.scrapecreators.com/v1/twitter/user-tweets", {"handle": handle, "trim": "true"}))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source, endpoint, params in endpoints:
        response = http_get(with_query(endpoint, params), headers={"x-api-key": api_key})
        raw["calls"].append({"source": source, "endpoint": endpoint, "params": params, "response": response})
        if not response.get("ok"):
            continue
        for item in list_candidates(response.get("body")):
            if not isinstance(item, dict):
                continue
            text, url, engagement, raw_id = stringify_twitter_item(item) if source == "x" else stringify_social_item(item)
            identity = raw_id or url or text[:80]
            if not text or identity in seen:
                continue
            seen.add(identity)
            relevance, relevance_notes, relevance_score = assess_relevance(text, args, social_query, url, "ScrapeCreators")
            records.append(
                normalize_record(
                    source=source,
                    source_url=url,
                    query=social_query,
                    customer_segment=args.customer_segment,
                    hypothesis=args.hypothesis_id,
                    text=text,
                    author_context="ScrapeCreators",
                    engagement=engagement,
                    raw_id=raw_id,
                    evidence_type="irrelevant" if relevance == "irrelevant" else None,
                    strength="irrelevant" if relevance == "irrelevant" else None,
                    relevance=relevance,
                    relevance_notes=relevance_notes,
                    relevance_score=relevance_score,
                    confidence_notes="Collected via ScrapeCreators public social scraping API. Verify platform limitations, costs, and source URLs before broad runs.",
                )
            )
            if len(records) >= args.limit:
                break
        if len(records) >= args.limit:
            break
    first_response = (raw["calls"][0] or {}).get("response", {}) if raw["calls"] else {}
    status = "ok" if records else status_from_response(first_response)
    write_json(run_dir / "raw" / "scrapecreators.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


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

    sonar_apps = parse_sonar_apps(args.sonar_apps)
    for store, app_id in sonar_apps:
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
        raw["calls"].append({"kind": "app_reviews", "store": store, "app_id": app_id, "response": reviews_response})
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
                    )
                )

    if sonar_apps and args.sonar_include_revenue:
        by_store: dict[str, list[str]] = {}
        for store, app_id in sonar_apps:
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
    status = "ok" if records else status_from_response(first_response)
    write_json(run_dir / "raw" / "sonar.json", redact_sensitive(raw))
    return records, {"status": status, "record_count": len(records), "fields": fields_present(raw)}


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
    for record in records:
        by_source[record["source"]] = by_source.get(record["source"], 0) + 1
        by_type[record["evidence_type"]] = by_type.get(record["evidence_type"], 0) + 1
        by_strength[record["strength"]] = by_strength.get(record["strength"], 0) + 1
        intent = record.get("source_intent", "unknown")
        by_intent[intent] = by_intent.get(intent, 0) + 1
        comment_intent = record.get("comment_intent", "unknown")
        if comment_intent != "not_social_comment":
            by_comment_intent[comment_intent] = by_comment_intent.get(comment_intent, 0) + 1
    quality_flags = quality_summary(records, provider_summaries)

    top = sorted(
        records,
        key=lambda item: (
            {"strong": 3, "medium": 2, "weak": 1}.get(item["strength"], 0),
            item["engagement"].get("upvotes") or 0,
            item["engagement"].get("comments") or 0,
        ),
        reverse=True,
    )[:10]
    lines = [
        "# Evidence Scout Run",
        "",
        f"- Topic: {args.topic}",
        f"- Customer segment: {args.customer_segment}",
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
    lines.extend(["", "## Query Plan", ""])
    lines.extend(f"- `{query}`" for query in queries)
    lines.extend(["", "## Evidence Mix", ""])
    lines.append(f"- By source: `{json.dumps(by_source, sort_keys=True)}`")
    lines.append(f"- By type: `{json.dumps(by_type, sort_keys=True)}`")
    lines.append(f"- By source intent: `{json.dumps(by_intent, sort_keys=True)}`")
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
    lines.extend(["", "## Highest-Signal Items", ""])
    for item in top:
        quote = item["verbatim_quote"].replace("\n", " ")
        lines.append(f"- [{item['source']}/{item['strength']}/{item['evidence_type']}] {quote} ({item['source_url']})")
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
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def provider_alerts(provider_summaries: dict[str, Any]) -> list[str]:
    alerts: list[str] = []
    for provider, summary in provider_summaries.items():
        status = summary.get("status")
        if status in {"ok", None}:
            continue
        if status == "missing_credentials":
            alerts.append(f"`{provider}` did not run because credentials are missing. Add the required key(s), then rerun validation.")
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


def quality_summary(records: list[dict[str, Any]], provider_summaries: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    user_pain_count = sum(1 for record in records if record.get("source_intent") == "user_pain")
    reddit_count = sum(1 for record in records if record.get("source") == "reddit")
    editorialish_count = sum(
        1
        for record in records
        if record.get("source_intent") in {"competitor_content", "editorial_content", "official_provider"}
    )
    if reddit_count == 0:
        flags.append("No relevant Reddit records survived filtering; do not infer community pain from this run.")
    if user_pain_count == 0:
        flags.append("No direct user-pain records found; evidence is discovery/market context, not demand validation.")
    elif user_pain_count < 5:
        flags.append(f"Only {user_pain_count} direct user-pain record(s) found; treat demand evidence as thin.")
    elif records and user_pain_count / len(records) < 0.25:
        flags.append(f"Direct user-pain share is low ({user_pain_count}/{len(records)} records); do not overstate demand strength.")
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
    lines = [
        "# User Review Plan",
        "",
        f"- Topic: {args.topic}",
        f"- Segment under test: {args.customer_segment}",
        "",
        "## Founder Checkpoints",
        "",
        "Interaction rule: ask the founder exactly one question at a time. Do not bundle multiple questions into one message.",
        "",
        "1. First ask: `Which evidence item below feels most like real buyer pain to you?`",
        "2. After the answer, ask: `Which single assumption would most change your decision if false?`",
        "3. After the answer, ask: `Should the next research focus on interviews, narrower segment evidence, or competitor flow teardown?`",
        "4. Define the pass/fail threshold only after the user has answered the prior questions.",
        "",
        "## Quality Flags To Discuss",
        "",
    ]
    if quality_flags:
        lines.extend(f"- {flag}" for flag in quality_flags)
    else:
        lines.append("- No automatic quality flags, but still review source mix and evidence strength manually.")
    lines.extend(
        [
            "",
            "## Top User-Pain Items For Human Review",
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
            "## Decision Questions To Turn Into Interviews",
            "",
        ]
    )
    for idx, record in enumerate(decision_questions, start=1):
        quote = record.get("verbatim_quote", "").replace("\n", " ")
        lines.append(f"{idx}. {quote} ({record.get('source_url')})")
    if not decision_questions:
        lines.append("- No decision-question records found.")
    lines.extend(
        [
            "",
            "## Suggested Interview Prompts",
            "",
            "- Tell me about the last time you considered PKV, BU, or changing an insurance advisor.",
            "- What triggered the decision and what did you do first?",
            "- Which sources or people did you trust, and which did you avoid?",
            "- What felt risky, confusing, or too time-consuming?",
            "- Did you compare portals, brokers, fee-based advisors, employer benefits, or do nothing?",
            "- What would have made you comfortable completing 80% of the process self-service?",
            "- At what point would you still want a human advisor, and what would that person need to prove?",
            "- What would make you pay, switch broker mandate, or upload existing contracts into an app?",
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
        f"- Segment phrase used for fit judgment: `{args.customer_segment}`",
        f"- Topic phrase: `{args.topic}`",
        f"- Problem keywords: `{args.problem_keywords or 'not provided'}`",
        f"- Workaround keywords: `{args.workaround_keywords or 'not provided'}`",
        "",
        "## Working Assumptions",
        "",
        "- The segment is interpreted as high-income employees and self-employed professionals in Germany who are considering PKV or BU.",
        "- Search behavior is assumed to include both technical German insurance terms and English expat/insurance terms when relevant sources use English.",
        "- Public posts, comments, and search results are treated as signals for interview design, not proof of willingness to pay.",
        "- Competitor/editorial/provider content is treated as category context, not customer pain.",
        "- Weak evidence requires user review before it can influence a business decision.",
        "",
        "## Explicitly Not Resolved By This Run",
        "",
        "- Legal/regulatory feasibility was not assessed in this run.",
        "- Unit economics, CAC, conversion, commission economics, and advisor capacity were not validated.",
        "- Actual user willingness to switch broker mandate, pay a fee, or upload contracts was not validated.",
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
        "Ask exactly one question at a time, in this order unless the user redirects:",
        "",
        "1. Is the segment too broad, or should the run focus on one trigger event?",
        "2. Are the German terms representative of how your target users would search or complain?",
        "3. Should English-language expat broker evidence be included or separated from German affluent-employee evidence?",
        "4. Are comparison portals like CHECK24/Verivox true substitutes for your concept or only research tools?",
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
        f"Test whether public evidence supports the hypothesis behind `{args.topic}` for `{args.customer_segment}`.",
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
            "`Which evidence item feels most like real buyer pain to you?`",
            "",
            "Recommended next research if evidence is mostly weak: run 8-12 customer interviews before making a business-viability conclusion.",
        ]
    )
    (run_dir / "research_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect normalized business-idea evidence.")
    parser.add_argument("--topic", required=True, help="Business idea, problem, category, or job-to-be-done.")
    parser.add_argument("--customer-segment", default="", help="Target customer segment to test.")
    parser.add_argument("--hypothesis-id", default="H1", help="Hypothesis label for normalized records.")
    parser.add_argument("--days", type=int, default=30, help="Lookback window for recency-aware sources.")
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
        help="Comma-separated providers. Use default, social, local_web, china_public, china_social, china, all, or explicit names: reddit,serpapi_google_trends,youtube,serper_search,firecrawl,brave_search,crawl4ai,markitdown,scrapling,x,xai_x_search,scrapecreators,sonar,china_bilibili,china_bilibili_comments,china_v2ex,china_web,china_xiaohongshu.",
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
        help="Optional comma-separated competitor app IDs for Sonar review/revenue enrichment, formatted ios:123456789 or android:com.example.app.",
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
        default=3,
        help="Maximum app review rating to fetch via Sonar for pain mining when --sonar-apps is supplied.",
    )
    parser.add_argument(
        "--sonar-include-revenue",
        action="store_true",
        help="Also fetch Sonar revenue estimates for --sonar-apps. Treat as weak monetization context.",
    )
    parser.add_argument("--x-handles", default="", help="Comma-separated X handles for handle-bounded Grok/X Search or ScrapeCreators Twitter user-tweet enrichment.")
    parser.add_argument("--x-from-date", help="ISO date/datetime for Grok/xAI X Search start date.")
    parser.add_argument("--x-to-date", help="ISO date/datetime for Grok/xAI X Search end date.")
    parser.add_argument("--xai-model", default="grok-4.3", help="xAI/Grok model for xai_x_search provider.")
    parser.add_argument("--xai-prompt", help="Override prompt for xai_x_search provider.")
    parser.add_argument("--geo", default="AUTO", help="Country/region code for providers that support geography. Use AUTO to infer from topic/segment.")
    parser.add_argument("--language", default="AUTO", help="Language code for providers that support language filtering. Use AUTO to infer from topic/segment.")
    parser.add_argument("--out-dir", default="", help="Optional output directory.")
    parser.add_argument("--workspace", default="", help="Topic workspace path. Defaults to research/topics/<topic-slug>.")
    parser.add_argument("--legacy-output", action="store_true", help="Write to the former research/evidence-scout/runs layout.")
    return parser.parse_args()


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
        out_dir=args.out_dir,
        legacy_output=args.legacy_output,
        workspace_subdir="evidence/runs",
        legacy_subdir="runs",
        customer_segment=args.customer_segment,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    if workspace:
        update_stage(
            workspace,
            "evidence_collection",
            status="in_progress",
            gate_result="not_run",
            next_action="Complete provider collection and inspect source quality.",
        )

    queries = query_plan(args.topic, args.customer_segment, args.problem_keywords, args.workaround_keywords, args.geo, args.language)
    requested_providers = selected_providers(args.providers)
    write_research_plan(run_dir, args, queries, requested_providers)
    provider_funcs = {
        "reddit": collect_reddit,
        "serpapi_google_trends": collect_serpapi_google_trends,
        "serper_search": collect_serper_search,
        "youtube": collect_youtube,
        "firecrawl": collect_firecrawl,
        "brave_search": collect_brave_search,
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
    for provider in requested_providers:
        func = provider_funcs.get(provider)
        if not func:
            provider_summaries[provider] = {"status": "unsupported", "record_count": 0}
            continue
        provider_records, provider_summary = func(args, queries, run_dir)
        relevant_provider_records = [record for record in provider_records if record.get("relevance") != "irrelevant"]
        irrelevant_provider_records = [record for record in provider_records if record.get("relevance") == "irrelevant"]
        records.extend(provider_records)
        provider_summary["record_count"] = len(relevant_provider_records)
        provider_summary["irrelevant_count"] = len(irrelevant_provider_records)
        provider_summaries[provider] = provider_summary

    relevant_records = [record for record in records if record.get("relevance") != "irrelevant"]
    irrelevant_records = [record for record in records if record.get("relevance") == "irrelevant"]
    append_jsonl(run_dir / "evidence.jsonl", relevant_records)
    append_jsonl(run_dir / "irrelevant.jsonl", irrelevant_records)
    alerts = provider_alerts(provider_summaries)
    quality_flags = quality_summary(relevant_records, provider_summaries)
    summary = {
        "run_dir": str(run_dir),
        "topic": args.topic,
        "customer_segment": args.customer_segment,
        "hypothesis_id": args.hypothesis_id,
        "days": args.days,
        "geo": args.geo,
        "language": args.language,
        "providers_requested": selected_providers(args.providers),
        "record_count": len(relevant_records),
        "irrelevant_count": len(irrelevant_records),
        "providers": provider_summaries,
        "needs_user_attention": alerts,
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
        gate_result = "fail" if not relevant_records else ("conditional_pass" if failures or quality_flags else "pass")
        update_stage(
            workspace,
            "evidence_collection",
            status="failed" if gate_result == "fail" else "passed",
            gate_result=gate_result,
            artifacts=[run_dir / "report.md", run_dir / "summary.json", run_dir / "evidence.jsonl", run_dir / "assumptions.md"],
            provider_failures=failures,
            open_gaps=quality_flags,
            next_action="Review evidence and interview users before synthesis." if gate_result != "pass" else "Proceed to competitor discovery or opportunity-risk design.",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if relevant_records else 1


if __name__ == "__main__":
    raise SystemExit(main())
