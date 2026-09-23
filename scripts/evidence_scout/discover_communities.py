#!/usr/bin/env python3
"""Discover public community leads without retaining copied user content."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "scripts" / "validate_apis"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import get_secret, http_get, http_post, now_iso, request_budget, status_from_response, with_query  # noqa: E402
from workspace import create_run_manifest, resolve_run_dir, update_run_manifest, update_stage  # noqa: E402

COLLECTOR_VERSION = "community-discovery-v2"
SUPPORTED_LANGUAGES = {
    "de": {"forum": "Forum Erfahrungen Hilfe", "facebook": "Facebook Gruppe Community", "facebook_page": "Facebook Seite", "voice": (" ich ", " wir ", " mein", "hilfe", "müssen", "muessen")},
    "fr": {"forum": "forum temoignage aide", "facebook": "groupe Facebook communaute", "facebook_page": "page Facebook", "voice": (" je ", " nous ", " mon ", "aide", "besoin", "difficile")},
    "it": {"forum": "forum esperienze aiuto", "facebook": "gruppo Facebook comunita", "facebook_page": "pagina Facebook", "voice": (" io ", " noi ", " mio ", "aiuto", "bisogno", "difficile")},
    "en": {"forum": "forum experiences help", "facebook": "Facebook group community", "facebook_page": "Facebook page", "voice": (" i ", " we ", " my ", "help", "need", "struggl")},
    "ar": {"forum": "منتدى تجارب مساعدة", "facebook": "مجموعة فيسبوك مجتمع", "facebook_page": "صفحة فيسبوك", "voice": (" أنا ", " نحن ", " أحتاج", "مساعدة", "صعب", "كيف ")},
}
GENERIC_STOPWORDS = {
    "about", "after", "and", "avec", "dans", "der", "des", "die", "ein", "eine", "en", "et", "for", "how",
    "in", "la", "le", "les", "nach", "organiser", "organisieren", "pour", "the", "und", "une", "with",
    "community", "forum", "facebook", "group", "gruppe", "groupe", "support", "help", "aide", "hilfe",
}
FORUM_HOST_MARKERS = ("community.", "discourse.", "forum.", "gutefrage.net", "quora.com", "reddit.com", "wer-weiss-was.de", "aufeminin.com", "doctissimo.fr")
FORUM_PATH_SEGMENTS = {"community", "discussion", "discussions", "forum", "forums", "thread", "threads", "topic", "topics"}
FORUM_ENGINE_MARKERS = ("ubbthreads.php", "viewtopic.php", "showthread.php", "showflat", "/topic/", "/thread/")
INTERACTION_MARKERS = ("answers", "antwort", "beitrag", "discussion", "member", "membre", "post", "replies", "reply", "reponse", "réponse", "thread", "topic")
FACEBOOK_EXCLUDED_PATHS = ("/login", "/share", "/sharer", "/watch", "/help", "/privacy", "/profile.php")
INACTIVE_MARKERS = ("read-only archive", "archive only", "forum ferme", "forum fermé", "nur als archiv")
ISO_ALPHA2_COUNTRIES = set("AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW".split())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def signed_discovery_receipt(candidates: list[dict[str, Any]], audit: dict[str, Any], key: str, review_lineage_id: str = "") -> dict[str, Any]:
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(key)); public_raw = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    lineage = review_lineage_id or canonical_digest({"candidate_scope": sorted(row.get("url", "") for row in candidates)})
    receipt = {"artifact_type": "community_discovery_receipt", "schema_version": 2, "discovery_run_id": str(uuid.uuid4()), "review_lineage_id": lineage, "review_candidates_digest": canonical_digest(candidates), "audit_digest": canonical_digest(audit), "generated_at": now_iso(), "signature_algorithm": "ed25519", "key_id": hashlib.sha256(public_raw).hexdigest()}
    receipt["signature"] = base64.b64encode(private_key.sign(json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())).decode()
    return receipt


def parse_locales(locale_args: list[str], geo: str, language: str) -> list[dict[str, str]]:
    values = list(locale_args)
    if not values:
        geos, languages = csv_terms(geo), csv_terms(language)
        if len(geos) != 1 or len(languages) != 1:
            raise ValueError("Use repeatable --locale COUNTRY:LANGUAGE for multi-market discovery.")
        values = [f"{geos[0]}:{languages[0]}"]
    locales: list[dict[str, str]] = []
    for value in values:
        if ":" not in value:
            raise ValueError("Each --locale must use COUNTRY:LANGUAGE, for example CH:de.")
        country, language_code = (part.strip() for part in value.split(":", 1))
        language_code = language_code.casefold()
        if not re.fullmatch(r"[A-Za-z]{2}", country) or not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", language_code):
            raise ValueError(f"Invalid locale {value!r}; use COUNTRY plus a BCP-47-style language tag.")
        if country.upper() not in ISO_ALPHA2_COUNTRIES:
            raise ValueError(f"Invalid locale {value!r}; COUNTRY must be an assigned ISO 3166-1 alpha-2 code.")
        item = {"country": country.upper(), "language": language_code, "locale_id": f"{country.upper()}:{language_code}"}
        if item not in locales:
            locales.append(item)
    return locales


def parse_locale_keywords(values: list[str], locales: list[dict[str, str]]) -> dict[str, list[str]]:
    locale_ids = {item["locale_id"] for item in locales}
    parsed: dict[str, list[str]] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("Each --locale-keywords must use COUNTRY:LANGUAGE=phrase|phrase.")
        locale_id, terms = (part.strip() for part in value.split("=", 1))
        locale_id = locale_id.split(":", 1)[0].upper() + ":" + locale_id.split(":", 1)[1].casefold() if ":" in locale_id else locale_id
        if locale_id not in locale_ids:
            raise ValueError(f"--locale-keywords references undeclared locale {locale_id!r}.")
        phrases = [term.strip() for term in terms.split("|") if term.strip()]
        if not phrases:
            raise ValueError(f"--locale-keywords for {locale_id} has no phrases.")
        parsed[locale_id] = phrases
    return parsed


def parse_locale_source_terms(values: list[str], locales: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    locale_ids = {item["locale_id"] for item in locales}; parsed: dict[str, dict[str, str]] = {}
    for value in values:
        if "=" not in value: raise ValueError("Each --locale-source-terms must use COUNTRY:LANGUAGE=forum terms|group terms|page terms.")
        locale_id, raw = (part.strip() for part in value.split("=", 1)); parts = [part.strip() for part in raw.split("|")]
        normalized = locale_id.split(":", 1)[0].upper() + ":" + locale_id.split(":", 1)[1].casefold() if ":" in locale_id else locale_id
        if normalized not in locale_ids or len(parts) != 3 or not all(parts): raise ValueError(f"Invalid --locale-source-terms for {locale_id!r}; declare the locale and provide forum|group|page terms.")
        parsed[normalized] = {"forum": parts[0], "facebook_group": parts[1], "facebook_page": parts[2]}
    return parsed


def query_plan(topic: str, community_keywords: str, locales: list[dict[str, str]] | str, locale_keywords: dict[str, list[str]] | None = None, locale_source_terms: dict[str, dict[str, str]] | None = None) -> list[dict[str, Any]]:
    if isinstance(locales, str):
        locales = parse_locales([], "ZZ", locales)
    plan: list[dict[str, Any]] = []
    for locale in locales:
        local_terms = (locale_keywords or {}).get(locale["locale_id"])
        seeds = list(dict.fromkeys(local_terms or [*csv_terms(community_keywords)] or [topic.strip()]))
        if not seeds:
            continue
        builtin = SUPPORTED_LANGUAGES.get(locale["language"], {})
        terms = (locale_source_terms or {}).get(locale["locale_id"]) or {"forum": builtin.get("forum", ""), "facebook_group": builtin.get("facebook", ""), "facebook_page": builtin.get("facebook_page", "Facebook page")}
        for seed_index, seed in enumerate(seeds, 1):
            for family, suffix in (("forum", terms["forum"]), ("facebook_group", terms["facebook_group"]), ("facebook_page", terms["facebook_page"])):
                query = f'"{seed}" {suffix}'
                if family == "facebook_group":
                    query = f"site:facebook.com/groups {query}"
                elif family == "facebook_page":
                    query = f"site:facebook.com {query} -site:facebook.com/groups"
                plan.append({"query_id": f"{locale['locale_id']}:{family}:s{seed_index}", "kind": family, "query": query, "seed": seed, "seed_index": seed_index, **locale})
    return plan


def provider_queries(plan: list[dict[str, Any]], limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # query_plan interleaves forum/Facebook within each locale, preventing a
    # low cap from consuming every slot on one source family.
    ordered = list(plan)
    return ordered[:limit], [{**item, "skip_reason": "query_limit"} for item in ordered[limit:]]


def require_complete_locale_coverage(plan: list[dict[str, Any]], query_limit: int) -> None:
    if query_limit < len(plan):
        raise ValueError(f"--query-limit {query_limit} cannot cover every forum/Facebook locale lane; use at least {len(plan)}")


def canonical_url(value: str) -> str:
    try:
        parts = urllib.parse.urlsplit(value.strip())
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return ""
    host = parts.hostname.casefold()
    if host.startswith("www."):
        host = host[4:]
    if host in {"m.facebook.com", "web.facebook.com"}:
        host = "facebook.com"
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    query: list[tuple[str, str]] = []
    if host == "facebook.com":
        chunks = [chunk for chunk in path.split("/") if chunk]
        if chunks[:1] == ["groups"] and len(chunks) >= 2:
            path = "/groups/" + chunks[1]
        elif chunks and len(chunks) >= 2 and chunks[1] in {"posts", "videos", "reels"}:
            path = "/" + chunks[0]
        else:
            query = urllib.parse.parse_qsl(parts.query, keep_blank_values=False)
    elif path.endswith("index.php") and parts.query.startswith("/"):
        return urllib.parse.urlunsplit(("https", host, path, parts.query, ""))
    else:
        query = urllib.parse.parse_qsl(parts.query, keep_blank_values=False)
    query = [(key, val) for key, val in query if key.casefold() not in {"fbclid", "gclid"} and not key.casefold().startswith("utm_")]
    return urllib.parse.urlunsplit(("https", host, path, urllib.parse.urlencode(query), ""))


def host_of(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").casefold()


def tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[^\W\d_]{3,}", value.casefold(), flags=re.UNICODE) if token not in GENERIC_STOPWORDS}


def candidate_type(url: str, text: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host, path = (parsed.hostname or "").casefold(), parsed.path.casefold()
    if host == "facebook.com" or host.endswith(".facebook.com"):
        if any(path.startswith(marker) for marker in FACEBOOK_EXCLUDED_PATHS):
            return "rejected"
        chunks = [chunk for chunk in path.split("/") if chunk]
        if chunks[:1] == ["groups"] and len(chunks) >= 2:
            return "facebook_group"
        return "facebook_entity_candidate" if chunks else "rejected"
    path_segments = {chunk for chunk in path.split("/") if chunk}
    host_labels = host.split(".")
    host_shape = any(host.startswith(marker) if marker.endswith(".") else host == marker or host.endswith(f".{marker}") for marker in FORUM_HOST_MARKERS) or any(label == "forum" for label in host_labels)
    engine_shape = any(marker in f"{path}?{parsed.query}" for marker in FORUM_ENGINE_MARKERS)
    lower = text.casefold()
    if engine_shape or path_segments.intersection(FORUM_PATH_SEGMENTS):
        return "forum"
    if host_shape and len(text) >= 200 and sum(marker in lower for marker in INTERACTION_MARKERS) >= 2:
        return "forum"
    return "rejected"


def voice_signal_count(text: str, language: str) -> int:
    padded = f" {' '.join(text.casefold().split())} "
    return sum(marker in padded for marker in SUPPORTED_LANGUAGES.get(language, {"voice": ()})["voice"])


def sensitivity_level(topic: str, segment: str, requested: str) -> str:
    # Sensitivity is an explicit case input, never inferred from reusable
    # industry or country vocabulary.
    return "not_classified" if requested == "auto" else requested


def classify(candidate: dict[str, Any], topic: str, community_keywords: str, customer_segment: str = "", sensitivity: str = "auto") -> dict[str, Any]:
    snippets = candidate.get("_snippets", candidate.get("evidence_snippets", []))
    markdown = candidate.get("_markdown", candidate.get("markdown", ""))
    title = candidate.get("_title", candidate.get("title", ""))
    text = " ".join([title, candidate.get("url", ""), *snippets, markdown[:10000]])
    kind = candidate_type(candidate.get("url", ""), text)
    source_phrases = [phrase for source in candidate.get("sources", []) for phrase in source.get("query_seeds", [])]
    keyword_phrases = list(dict.fromkeys(source_phrases or csv_terms(community_keywords)))
    relevant_tokens = tokens(" ".join([topic, *keyword_phrases]))
    found_tokens = sorted(token for token in relevant_tokens if token in text.casefold())
    phrase_hits = sorted(phrase for phrase in keyword_phrases if phrase.casefold() in text.casefold())
    topic_fit = "strong_candidate" if phrase_hits or (not keyword_phrases and len(found_tokens) >= 2) else "weak" if found_tokens else "none"
    lower = text.casefold()
    interaction_hits = sorted(marker for marker in INTERACTION_MARKERS if marker in lower)
    parsed = urllib.parse.urlsplit(candidate.get("url", ""))
    structural_forum = any(marker in f"{parsed.path.casefold()}?{parsed.query.casefold()}" for marker in FORUM_ENGINE_MARKERS) or bool({chunk for chunk in parsed.path.casefold().split("/") if chunk}.intersection(FORUM_PATH_SEGMENTS))
    inactive = any(marker in lower for marker in INACTIVE_MARKERS)
    languages = sorted({source.get("language", "") for source in candidate.get("sources", []) if source.get("language")})
    voice_count = max((voice_signal_count(markdown, language) for language in languages if language in SUPPORTED_LANGUAGES), default=0) if markdown else 0
    sensitive = sensitivity_level(topic, customer_segment, sensitivity)
    if kind == "rejected":
        status, reason = "rejected", "URL and retrieved metadata do not establish a discussion community."
    elif topic_fit != "strong_candidate":
        status, reason = "rejected", "Community-shaped URL lacks a sufficiently specific topic match."
    elif kind.startswith("facebook_"):
        status, reason = "indexed_candidate", "The group/entity URL was indexed; access, entity type, activity, audience, and platform authorization remain unverified."
    elif markdown and len(markdown) >= 200 and structural_forum and len(interaction_hits) >= 2:
        status, reason = "source_shape_verified", "Retrieved content verifies discussion-page shape only; target audience and customer evidence remain unverified."
    else:
        status, reason = "indexed_candidate", "A forum-shaped URL matched indexed metadata; page access and audience remain unverified."
    observed_at = candidate.get("observed_at") or now_iso()
    review_due = (datetime.now(timezone.utc) + timedelta(days=90)).replace(microsecond=0).isoformat()
    source_count = len({source.get("provider") for source in candidate.get("sources", []) if source.get("provider")})
    lane_assessments: list[dict[str, Any]] = []
    for observation in candidate.get("_observations", []):
        lane_evidence_text = " ".join([observation.get("title", ""), observation.get("description", ""), observation.get("markdown", "")[:10000]])
        lane_text = " ".join([lane_evidence_text, candidate.get("url", "")])
        lane_kind = candidate_type(candidate.get("url", ""), lane_text)
        query_kind = observation.get("query_kind", observation.get("kind", ""))
        shape_matches_lane = (query_kind == "forum" and lane_kind == "forum") or (query_kind == "facebook_group" and lane_kind == "facebook_group") or (query_kind == "facebook_page" and lane_kind == "facebook_entity_candidate")
        lane_seed = str(observation.get("seed", ""))
        lane_tokens = tokens(lane_seed)
        lane_match = bool(lane_seed and lane_seed.casefold() in lane_evidence_text.casefold()) or (not lane_seed and bool(tokens(topic) & tokens(lane_evidence_text)))
        lane_assessments.append({
            "locale_id": observation.get("locale_id") or f"{observation.get('country', '')}:{observation.get('language', '')}",
            "seed": lane_seed, "query_kind": query_kind,
            "provider": observation.get("provider", ""), "qualified": shape_matches_lane and lane_match,
            "community_type": lane_kind, "source_content_digest": digest("\n".join([observation.get("title", ""), observation.get("description", ""), observation.get("markdown", "")])),
        })
    return {
        "url": candidate.get("url", ""), "domain": candidate.get("domain", ""), "community_type": kind,
        "verification_status": status, "verification_reason": reason, "topic_fit": topic_fit, "topic_matches": found_tokens,
        "keyword_phrase_matches": phrase_hits, "community_shape": "verified" if status == "source_shape_verified" else "candidate" if status == "indexed_candidate" else "rejected",
        "target_member_presence": "unverified", "customer_segment_fit": "unverified", "geography_fit": "unverified", "language_fit": "unverified",
        "activity_status": "inactive_archive" if inactive else "unverified", "public_access": "unverified", "source_ownership": "unverified",
        "interaction_markers": interaction_hits, "index_count": source_count,
        "voice_status": "firsthand_signal_requires_review" if voice_count else "no_retained_voice_text", "voice_signal_count": voice_count,
        "exact_text_retained": False, "eligible_for_voice_review": voice_count > 0, "eligible_for_recruitment_review": False,
        "eligible_for_targeted_collection": False,
        "capture_gate": {"spend_authorization": "standing_authorized_no_cap", "public_or_legitimately_accessible_route": "unverified", "no_credential_or_technical_bypass": "required", "research_use": "internal", "status": "manual_source_review_required"},
        "sensitivity": sensitive, "sources": candidate.get("sources", []), "observed_at": observed_at,
        "lane_assessments": lane_assessments,
        "current_status": "indexed_or_retrieved", "last_checked_at": observed_at, "changed_since_capture": "unverified", "deleted_or_private": "unverified",
        "retention_policy": "metadata_only_review_90_days", "retention_review_due": review_due, "content_digest": candidate.get("content_digest", ""), "collector_version": COLLECTOR_VERSION,
    }


def add_observation(candidates: dict[str, dict[str, Any]], observation: dict[str, Any]) -> None:
    original_url = str(observation.get("url", "")).strip()
    url = canonical_url(original_url)
    if not url:
        return
    observed_at = str(observation.get("fetched_at") or now_iso())
    candidate = candidates.setdefault(url, {"url": url, "domain": host_of(url), "_title": "", "_snippets": [], "_markdown": "", "_observations": [], "sources": [], "observed_at": observed_at, "content_digest": ""})
    title, description, markdown = (str(observation.get(key, "")) for key in ("title", "description", "markdown"))
    snippet = " ".join([title.strip(), description.strip()]).strip()
    if snippet and snippet not in candidate["_snippets"]:
        candidate["_snippets"].append(snippet)
    if len(markdown) > len(candidate["_markdown"]):
        candidate["_markdown"] = markdown; candidate["content_digest"] = digest(markdown)
    if title and not candidate["_title"]:
        candidate["_title"] = title
    candidate["_observations"].append({key: observation.get(key, "") for key in ("provider", "locale_id", "country", "language", "query_kind", "kind", "seed", "title", "description", "markdown")})
    source = {
        "provider": observation.get("provider", ""), "query_id": observation.get("query_id", ""), "query": observation.get("query", ""),
        "query_kind": observation.get("query_kind", observation.get("kind", "")), "original_url": original_url,
        "query_seeds": observation.get("seeds", [observation.get("seed")] if observation.get("seed") else []),
        "result_rank": observation.get("result_rank"), "fetched_at": observed_at, "http_status": observation.get("http_status"),
        "observation_scope": "search_index_result",
        "response_id": observation.get("response_id", ""), "redirect_url": observation.get("redirect_url", ""),
        "country": observation.get("country", ""), "language": observation.get("language", ""),
        "content_digest": digest("\n".join([title, description, markdown])) if any((title, description, markdown)) else "", "collector_version": COLLECTOR_VERSION,
    }
    if source not in candidate["sources"]:
        candidate["sources"].append(source)
    candidate["content_digest"] = digest("|".join(sorted(item.get("content_digest", "") for item in candidate["sources"] if item.get("content_digest"))))


def response_audit(response: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    body = response.get("body") or {}
    return {"query_id": item["query_id"], "query": item["query"], "query_kind": item["kind"], "country": item["country"], "language": item["language"], "status": "ok" if response.get("ok") else status_from_response(response), "http_status": response.get("status_code", response.get("status")), "response_id": body.get("id", "") if isinstance(body, dict) else "", "fetched_at": now_iso(), "response_body_retained": False}


def collect_provider(provider: str, plan: list[dict[str, Any]], args: argparse.Namespace, audit: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = {
        "brave_search": ("BRAVE_SEARCH_API_KEY", "https://api.search.brave.com/res/v1/web/search"),
        "serper_search": ("SERPER_API_KEY", "https://google.serper.dev/search"),
        "firecrawl": ("FIRECRAWL_API_KEY_HGINVESTOR", "https://api.firecrawl.dev/v1/search"),
    }
    env_name, endpoint = config[provider]; key_name, key = get_secret("SERPER_DEV_API_KEY", env_name) if provider == "serper_search" else get_secret(env_name)
    if not key:
        return [], {"status": "missing_credentials", "required_env": [env_name], "result_count": 0, "result_counts_by_query": {}, "executed_queries": [], "skipped_queries": [item["query_id"] for item in plan]}
    selected, skipped = provider_queries(plan, args.query_limit); observations: list[dict[str, Any]] = []; statuses: list[str] = []; result_counts: dict[str, int] = {}
    for item in selected:
        if provider == "brave_search":
            response = http_get(with_query(endpoint, {"q": item["query"], "count": min(args.limit, 10), "country": item["country"], "search_lang": item["language"]}), headers={"X-Subscription-Token": key, "Accept": "application/json"})
            results = (((response.get("body") or {}).get("web") or {}).get("results") or [])
        elif provider == "serper_search":
            response = http_post(endpoint, headers={"X-API-KEY": key}, data={"q": item["query"], "num": min(args.limit, 10), "gl": item["country"].casefold(), "hl": item["language"]})
            results = (response.get("body") or {}).get("organic") or []
        else:
            # Discovery is metadata-only. Content capture happens later through
            # a reviewed public or legitimately accessible route.
            response = http_post(
                endpoint,
                headers={"Authorization": f"Bearer {key}"},
                data={"query": item["query"], "limit": min(args.limit, 10), "country": item["country"], "location": item["country"]},
            )
            results = (response.get("body") or {}).get("data") or []
        if not response.get("ok"):
            results = []
        record = response_audit(response, item); audit.setdefault(provider, []).append(record); statuses.append(record["status"])
        result_counts[item["query_id"]] = len(results)
        for rank, result in enumerate(results, 1):
            observations.append({**item, "provider": provider, "query_kind": item["kind"], "url": result.get("link", result.get("url", "")), "title": result.get("title", ""), "description": result.get("snippet", result.get("description", "")), "markdown": result.get("markdown", ""), "result_rank": rank, "fetched_at": record["fetched_at"], "http_status": record["http_status"], "response_id": record["response_id"]})
    status = "ok" if statuses and all(value == "ok" for value in statuses) else "partial" if "ok" in statuses else (statuses[0] if statuses else "failed")
    return observations, {"status": status, "credential_source": key_name, "result_count": len(observations), "result_counts_by_query": result_counts, "executed_queries": [item["query_id"] for item in selected], "skipped_queries": [item["query_id"] for item in skipped]}


def write_plan(run_dir: Path, args: argparse.Namespace, plan: list[dict[str, Any]]) -> None:
    lines = ["# Community Discovery Plan", "", f"- Topic: {args.topic}", f"- Segment: {args.customer_segment}", f"- Locales: {', '.join(item['locale_id'] for item in args.locales)}", f"- Providers: {args.providers}", f"- Sensitivity: {sensitivity_level(args.topic, args.customer_segment, args.sensitivity)}", "", "## Contract", "", "Discover community leads using metadata-only artifacts. Paid customer-evidence APIs have standing no-cap authorization. Search indexing still does not establish target fit, customer evidence, or legitimate access to private material.", "", "## Queries", ""]
    lines.extend(f"- [{item['query_id']}] `{item['query']}`" for item in plan)
    (run_dir / "research_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(run_dir: Path, args: argparse.Namespace, candidates: list[dict[str, Any]], rejected: list[dict[str, Any]], providers: dict[str, Any], gaps: list[str]) -> None:
    lines = ["# Community Discovery Report", "", f"- Topic: {args.topic}", f"- Review candidates: {len(candidates)}", f"- Rejected: {len(rejected)}", "", "## Method boundary", "", "These are capped, ranked search-engine convenience samples. They are not a population frame, prevalence estimate, representative sample, or proof of demand. Multiple indexes of one URL are not independent customer observations. Target membership, geography, language, activity, ownership, and recent experience require separate review.", "", "## Provider and query coverage", ""]
    for name, value in providers.items():
        lines.append(f"- {name}: {value.get('status')} ({value.get('result_count', 0)} results); executed={len(value.get('executed_queries', []))}; skipped={len(value.get('skipped_queries', []))}")
    lines.extend(["", "## Candidate sources", ""])
    lines.extend(f"- [{row['community_type']}/{row['verification_status']}] {row['domain']} — {row['url']} — {row['verification_reason']}" for row in candidates)
    if not candidates:
        lines.append("- None. This does not show that no community exists.")
    lines.extend(["", "## Coverage gaps", ""]); lines.extend(f"- {gap}" for gap in gaps or ["No provider failure; relevance and sampling limitations still apply."])
    lines.extend(["", "## Capture and recruitment boundary", "", "Discovery retains no copied post text. Paid-API spending is authorized by the user; reviewed public Facebook targets may be internally allowlisted, without claiming Meta permission or terms compliance. Private material must be user-supplied from legitimate access; never steal/share credentials, bypass technical controls, or use deceptive membership. No GDPR paperwork or formal ethics review is required for this internal exploratory phase. Recruitment eligibility defaults false until current activity, target-member presence, geography, language, recent experience, and an acceptable contact route are manually evidenced.", ""])
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover forum and Facebook community leads with metadata-only outputs.")
    parser.add_argument("--topic", required=True); parser.add_argument("--customer-segment", required=True)
    parser.add_argument("--community-keywords", default=""); parser.add_argument("--geo", default=""); parser.add_argument("--language", default="")
    parser.add_argument("--locale", action="append", default=[], help="Repeatable COUNTRY:LANGUAGE pair, for example --locale CH:de.")
    parser.add_argument("--locale-keywords", action="append", default=[], help="Optional per-locale phrases: COUNTRY:LANGUAGE=phrase|phrase.")
    parser.add_argument("--locale-source-terms", action="append", default=[], help="Required for languages without a built-in pack: COUNTRY:LANGUAGE=forum terms|group terms|page terms.")
    parser.add_argument("--seed-language", default="", help="Attest the language of shared --community-keywords for single-language locales.")
    parser.add_argument("--query-preview", action="store_true", help="Print all locale/source queries without credentials, signing keys, network or workspace writes.")
    parser.add_argument("--query-review", default="", help="Analyst vocabulary/source review JSON, including optional source-derived seed lineage; not capture approval.")
    parser.add_argument("--sensitivity", choices=("auto", "standard", "sensitive", "vulnerable"), default="auto")
    parser.add_argument("--providers", default="brave_search,firecrawl,serper_search"); parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--query-limit", type=int, default=100); parser.add_argument("--max-http-requests", type=int, default=500)
    parser.add_argument("--fixture-results-json", default=""); parser.add_argument("--workspace", default=""); parser.add_argument("--case", default=""); parser.add_argument("--out-dir", default="")
    args = parser.parse_args(); allowed = {"brave_search", "firecrawl", "serper_search"}; requested = set(csv_terms(args.providers))
    if not requested or not requested <= allowed:
        parser.error("--providers accepts only brave_search,firecrawl,serper_search")
    if args.limit < 1 or args.query_limit < 1 or args.max_http_requests < 1:
        parser.error("limits and request budget must be positive")
    try:
        args.locales = parse_locales(args.locale, args.geo, args.language)
        args.locale_keyword_map = parse_locale_keywords(args.locale_keywords, args.locales)
        args.locale_source_term_map = parse_locale_source_terms(args.locale_source_terms, args.locales)
    except ValueError as exc:
        parser.error(str(exc))
    missing_lexicons = [item for item in args.locales if item["locale_id"] not in args.locale_keyword_map]
    if missing_lexicons:
        shared_language = args.seed_language.casefold()
        if not csv_terms(args.community_keywords) or any(item["language"] != shared_language for item in missing_lexicons):
            parser.error("Each locale needs --locale-keywords, or global --community-keywords plus a matching --seed-language attestation.")
    unsupported = [item["locale_id"] for item in args.locales if item["language"] not in SUPPORTED_LANGUAGES and item["locale_id"] not in args.locale_source_term_map]
    if unsupported: parser.error(f"Unsupported languages require explicit --locale-source-terms for: {', '.join(unsupported)}")
    return args


def reviewed_query_plan(args):
    plan = query_plan(args.topic, args.community_keywords, args.locales, args.locale_keyword_map, args.locale_source_term_map)
    review = read_json(Path(args.query_review)) if args.query_review else {}
    if args.query_review:
        if not isinstance(review, dict) or not isinstance(review.get("revision"), str) or not review["revision"].strip() or not isinstance(review.get("review_notes"), str) or not review["review_notes"].strip():
            raise ValueError("Query review requires revision and review_notes; analyst notes are not source verification")
        if review.get("previous_plan_digest") and not re.fullmatch(r"[a-f0-9]{64}", review["previous_plan_digest"]):
            raise ValueError("previous_plan_digest must be a SHA256 digest")
        seeds = review.get("seeds", [])
        if not isinstance(seeds, list):
            raise ValueError("Query review seeds must be an array")
        seen = set()
        for seed in seeds:
            if not isinstance(seed, dict):
                raise ValueError("Each reviewed seed must be an object")
            key = (seed.get("locale"), seed.get("seed"))
            if key in seen or not any((row["locale_id"], row["seed"]) == key for row in plan):
                raise ValueError("Reviewed seeds must uniquely match a scheduled locale/seed")
            seen.add(key)
            if seed.get("seed_origin") not in {"supplied", "translated", "source_derived", "generated"}:
                raise ValueError("Each reviewed seed requires a valid seed_origin")
            locators = seed.get("seed_locators", [])
            if seed["seed_origin"] == "source_derived" and (not isinstance(locators, list) or not locators or not all(isinstance(x, str) and x.strip() for x in locators)):
                raise ValueError("Source-derived seeds require nonempty seed_locators")
            for row in plan:
                if (row["locale_id"], row["seed"]) == key:
                    row.update({"seed_origin": seed["seed_origin"], "seed_locators": locators})
    for row in plan:
        row["candidate_id"] = hashlib.sha256(f"{row['locale_id']}:{row['seed']}".encode()).hexdigest()[:16]
    return plan, review


def main() -> int:
    args = parse_args()
    try:
        plan, query_review = reviewed_query_plan(args)
        require_complete_locale_coverage(plan, args.query_limit)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    snapshot = {"query_plan": plan, "query_review": query_review,
                "query_plan_digest": hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
    if args.query_preview:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return 0
    signing_key = os.environ.get("COMMUNITY_DISCOVERY_PRIVATE_KEY_B64", "")
    try: Ed25519PrivateKey.from_private_bytes(base64.b64decode(signing_key))
    except Exception as exc: raise SystemExit("COMMUNITY_DISCOVERY_PRIVATE_KEY_B64 must contain a base64-encoded 32-byte Ed25519 private key.") from exc
    run_dir, workspace = resolve_run_dir(topic=args.topic, workspace_arg=args.workspace, case_id=args.case, out_dir=args.out_dir, legacy_output=False, workspace_subdir="market_research/pain_points/community_discovery/runs", legacy_subdir="community-discovery", customer_segment=args.customer_segment)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_plan(run_dir, args, plan)
    write_json(run_dir / "query_plan.json", snapshot)
    create_run_manifest(run_dir, subject=args.topic, run_type="community_discovery", stage="evidence_collection", artifacts=[run_dir / "research_plan.md"], sources=csv_terms(args.providers), next_action="Manually review source shape and fit dimensions; capture remains separately gated.")
    if workspace:
        update_stage(workspace, "evidence_collection", run_dir=run_dir, status="in_progress", gate_result="not_run", artifacts=[run_dir / "research_plan.md"], next_action="Review community candidates; do not collect posts from discovery output.")
    audit: dict[str, Any] = {"collector_version": COLLECTOR_VERSION, **snapshot, "raw_content_retained": False}; providers: dict[str, Any] = {}; observations: list[dict[str, Any]] = []
    if args.fixture_results_json:
        observations = list(read_json(Path(args.fixture_results_json)).get("results", []))
        for item in observations:
            item.setdefault("fetched_at", now_iso())
            if not item.get("country") and args.locales:
                item.update({key: args.locales[0][key] for key in ("country", "language", "locale_id")})
        providers["offline_fixture"] = {"status": "fixture_only", "result_count": len(observations), "result_counts_by_query": {}, "executed_queries": [], "skipped_queries": [item["query_id"] for item in plan], "fixture_mode": True}
    else:
        with request_budget(args.max_http_requests) as budget:
            for provider in csv_terms(args.providers):
                rows, summary = collect_provider(provider, plan, args, audit); observations.extend(rows); providers[provider] = summary
            audit["request_budget"] = budget.summary()
    candidates: dict[str, dict[str, Any]] = {}
    for observation in observations:
        add_observation(candidates, observation)
    classified = [classify(candidate, args.topic, args.community_keywords, args.customer_segment, args.sensitivity) for candidate in candidates.values()]
    review_candidates = sorted((row for row in classified if row["verification_status"] != "rejected"), key=lambda row: (row["verification_status"] == "source_shape_verified", row["index_count"], len(row["topic_matches"])), reverse=True)
    rejected = sorted((row for row in classified if row["verification_status"] == "rejected"), key=lambda row: row["url"])
    gaps = [f"{name} returned {value.get('status')}; preserve the source gap." for name, value in providers.items() if value.get("status") != "ok"]
    for name, value in providers.items():
        if value.get("skipped_queries"):
            gaps.append(f"{name} skipped query lanes due to --query-limit: {', '.join(value['skipped_queries'])}.")
    if not any(row["verification_status"] == "source_shape_verified" for row in review_candidates):
        gaps.append("No discussion-page shape was verified; indexed candidates remain leads only.")
    if not any(row["community_type"].startswith("facebook_") for row in review_candidates):
        gaps.append("No relevant Facebook group/entity URL was identified; do not infer absence of discussion.")
    audit["requested_providers"] = ["offline_fixture"] if args.fixture_results_json else csv_terms(args.providers)
    audit["provider_outcomes"] = providers
    lineage_id = canonical_digest({"workspace": str(workspace or args.workspace or "standalone"), "case": args.case, "topic": " ".join(args.topic.casefold().split()), "customer_segment": " ".join(args.customer_segment.casefold().split()), "locales": sorted(item["locale_id"] for item in args.locales)})
    receipt = signed_discovery_receipt(review_candidates, audit, signing_key, lineage_id)
    write_json(run_dir / "raw.json", audit); write_json(run_dir / "community_candidates.json", classified); write_json(run_dir / "review_candidates.json", review_candidates); write_json(run_dir / "community_discovery_receipt.json", receipt); write_json(run_dir / "rejected_candidates.json", rejected); write_report(run_dir, args, review_candidates, rejected, providers, gaps)
    locale_coverage = {}
    for locale in args.locales:
        locale_id = locale["locale_id"]
        rows = [row for row in classified if any(lane.get("locale_id") == locale_id for lane in row.get("lane_assessments", []))]
        locale_coverage[locale_id] = {"planned_query_lanes": sum(item["locale_id"] == locale_id for item in plan), "candidate_count": len(rows), "review_candidate_count": sum(any(lane.get("locale_id") == locale_id and lane.get("qualified") for lane in row.get("lane_assessments", [])) for row in rows)}
    summary = {"run_dir": str(run_dir), "topic": args.topic, "customer_segment": args.customer_segment, "candidate_count": len(classified), "review_candidate_count": len(review_candidates), "source_shape_verified_count": sum(row["verification_status"] == "source_shape_verified" for row in review_candidates), "facebook_candidate_count": sum(row["community_type"].startswith("facebook_") for row in review_candidates), "providers": providers, "locale_coverage": locale_coverage, "needs_user_attention": gaps, "paid_api_spend_authorization": "standing_authorized_no_cap", "capture_review_status": "not_run", "raw_user_text_retained": False, "sampling_frame": "capped_ranked_search_convenience_sample", "outputs": {name: str(run_dir / name) for name in ("research_plan.md", "community_candidates.json", "review_candidates.json", "community_discovery_receipt.json", "rejected_candidates.json", "report.md", "raw.json", "run-manifest.json")}}
    write_json(run_dir / "summary.json", summary)
    artifacts = [run_dir / name for name in ("research_plan.md", "community_candidates.json", "review_candidates.json", "community_discovery_receipt.json", "rejected_candidates.json", "report.md", "summary.json", "raw.json")]
    gate = "conditional_pass" if review_candidates else "fail"
    update_run_manifest(run_dir, stage="evidence_collection", stage_status="in_progress" if review_candidates else "failed", gate_result=gate, artifacts=artifacts, open_gaps=gaps, next_action="Manually audit candidates; content capture requires source review and the generated capture gate.", event="community_discovery_completed", record_count=len(review_candidates), source_count=len(providers))
    if workspace:
        failures = [{"provider": name, "failure_class": value.get("status", "failed"), "confidence_impact": "medium"} for name, value in providers.items() if value.get("status") != "ok"]
        update_stage(workspace, "evidence_collection", run_dir=run_dir, status="in_progress" if review_candidates else "failed", gate_result=gate, artifacts=artifacts, provider_failures=failures, open_gaps=gaps, next_action="Manual source audit required; content capture remains blocked.")
    print(json.dumps(summary, indent=2, sort_keys=True)); return 0 if review_candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
