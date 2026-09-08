#!/usr/bin/env python3
"""Build and validate the canonical lane-aware entity landscape."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from entity_landscape import classify_entity, normalize_evidence_quality, normalize_social_presence, stable_entity_id
from workspace import update_stage


ROOT = Path(__file__).resolve().parents[2]
LANES = {"competitive_market", "similar_company", "capability_reference"}


def read(path: str, fallback: Any) -> Any:
    if not path:
        return fallback
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def rows(data: Any, key: str) -> list[dict[str, Any]]:
    values = data if isinstance(data, list) else data.get(key, []) if isinstance(data, dict) else []
    return [value for value in values if isinstance(value, dict)]


def by_url(data: Any, key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get("url")): row for row in rows(data, key) if row.get("url")}


def meaningful_terms(value: str) -> set[str]:
    return {token[:6] for token in re.findall(r"[\w-]+", value.casefold()) if len(token) >= 4}


def evidence_fit(expected: str, observations: list[Any]) -> str:
    expected_terms = meaningful_terms(expected)
    observed_terms = meaningful_terms(" ".join(str(value) for value in observations))
    if not expected_terms or not observed_terms:
        return "unknown"
    overlap = len(expected_terms & observed_terms) / len(expected_terms)
    return "strong" if overlap >= 0.5 else "partial" if overlap > 0 else "none"


def lane_context(item: dict[str, Any]) -> tuple[set[str], list[str], list[str]]:
    scopes: set[str] = set()
    analogs: list[str] = []
    capabilities: list[str] = []
    for source in item.get("sources", []):
        if not isinstance(source, dict):
            continue
        lane = str(source.get("lane_scope", ""))
        value = str(source.get("scope_value", "")).strip()
        if lane in LANES:
            scopes.add(lane)
        if lane == "similar_company" and value and value not in analogs:
            analogs.append(value)
        if lane == "capability_reference" and value and value not in capabilities:
            capabilities.append(value)
    return scopes, analogs, capabilities


def social_rows(analysis: dict[str, Any], social: dict[str, Any], now: str) -> list[dict[str, Any]]:
    observations = social.get("social_presence", []) or analysis.get("social_presence", [])
    normalized: list[dict[str, Any]] = []
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        normalized.append(normalize_social_presence(
            platform=str(observation.get("platform", "unknown")),
            url=str(observation.get("url", "")),
            status=str(observation.get("status", "unverified")),
            retrieved_at=str(observation.get("retrieved_at", now)),
            role=str(observation.get("role", "unknown")),
            evidence_type=str(observation.get("evidence_type", "official_profile")),
            posts_sampled=int(observation.get("posts_sampled", 0) or 0),
            coverage_gap=str(observation.get("coverage_gap", "")),
            sample_window=str(observation.get("sample_window", "")),
            formats=[str(value) for value in observation.get("formats", [])],
            cadence=str(observation.get("cadence", "unknown")),
            cta=[str(value) for value in observation.get("cta", [])],
            public_metrics=observation.get("public_metrics", {}) if isinstance(observation.get("public_metrics", {}), dict) else {},
        ))
    return normalized


def validate_result(result: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "schemas/entity-landscape.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(result), key=lambda error: list(error.path))
    if errors:
        details = "\n".join(f"- {'/'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors)
        raise ValueError(f"entity landscape failed schema validation:\n{details}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competitors-json", required=True)
    parser.add_argument("--discovery-summary-json", default="", help="Discovery summary used to preserve requested lanes and zero-result coverage gaps.")
    parser.add_argument("--marketing-json", default="", help="Official-page analysis from analyze_competitor_marketing.py.")
    parser.add_argument("--social-json", default="", help="Optional normalized or sampled social observations.")
    parser.add_argument("--service", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--target-segment", required=True)
    parser.add_argument("--geography", required=True)
    parser.add_argument("--buyer", default="")
    parser.add_argument("--price-tier", default="")
    parser.add_argument("--workspace", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    candidates = rows(read(args.competitors_json, []), "entities")
    discovery_summary = read(args.discovery_summary_json, {})
    marketing = by_url(read(args.marketing_json, []), "analyses")
    social_data = read(args.social_json, {})
    social = by_url(social_data, "entities")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entities: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []

    for item in candidates:
        url = str(item.get("url", ""))
        analysis = marketing.get(url, {})
        scopes, analog_markets, capabilities = lane_context(item)
        first_party_pages = [page for page in analysis.get("first_party_source_pages", []) if isinstance(page, dict) and page.get("retrieval_source") in {"firecrawl", "direct_http", "fixture_official"}]
        official = bool(analysis.get("official_service_evidence") and first_party_pages)
        entity_social = social_rows(analysis, social.get(url, {}), now)
        capability_patterns = [pattern for pattern in analysis.get("capability_patterns", []) if isinstance(pattern, dict) and pattern.get("observed_pattern")]
        for capability in capabilities:
            if capability not in {"social", "youtube"}:
                continue
            for observation in entity_social:
                if observation.get("status") == "verified_active" and observation.get("posts_sampled", 0) > 0 and (observation.get("formats") or observation.get("cadence") != "unknown"):
                    capability_patterns.append({"capability": capability, "observed_pattern": f"Observed {observation.get('formats', [])} at {observation.get('cadence', 'unknown')} cadence across {observation.get('posts_sampled')} sampled posts."})
                    break
        reference_observed = bool(first_party_pages and capability_patterns) or bool(capability_patterns and any(pattern.get("capability") in {"social", "youtube"} for pattern in capability_patterns))
        service_text = [offer.get("observed_text", "") for offer in analysis.get("service_offers", []) if isinstance(offer, dict)]
        offer_fit = evidence_fit(f"{args.service} {args.job}", service_text) if official else "unknown"
        segment_fit = evidence_fit(args.target_segment, analysis.get("detected_audiences", [])) if official else "unknown"
        buyer_fit = evidence_fit(args.buyer, analysis.get("detected_audiences", [])) if args.buyer and official else segment_fit
        geography_fit = "none" if scopes == {"similar_company"} and analog_markets else "unknown"
        if scopes == {"similar_company"} and analog_markets:
            segment_fit = "none"
        substitutability = str(item.get("purchase_substitutability", "unknown")) if "competitive_market" in scopes else "unknown"
        classification = classify_entity(
            offer_job_overlap=offer_fit,
            target_segment_overlap=segment_fit,
            buyer_overlap=buyer_fit,
            geography_overlap=geography_fit,
            price_tier_overlap=str(item.get("price_tier_overlap", "unknown")),
            purchase_substitutability=substitutability,
            official_service_evidence=official,
            supplied_as_reference=bool(capabilities),
            reference_observation_evidence=reference_observed,
            excluded_source=item.get("competitor_type_hint") in {"editorial_resource", "lead_gen_affiliate"},
            legacy_role=str(item.get("competitive_role_hint", "")),
        )
        classification_sources = [
            {"url": str(page.get("url", url)), "retrieved_at": str(analysis.get("retrieved_at", now)), "evidence_type": "official_entity_page", "claim": "official-page service and audience evidence"}
            for page in first_party_pages
        ]
        default_analog_roles = ["offer", "pricing", "positioning"] if "similar_company" in scopes else []
        inspiration_roles = list(dict.fromkeys(str(role).casefold() for role in [*item.get("inspiration_roles", []), *default_analog_roles, *capabilities]))
        if classification["verification_status"] == "verified" and classification["primary_lane"] == "capability_reference":
            classification_reason = "Verified named capability pattern from first-party page or sampled public-profile evidence."
        elif classification["verification_status"] == "verified":
            classification_reason = "Verified against official service-page evidence and explicit fit dimensions."
        else:
            classification_reason = "Insufficient official service, buyer, segment, substitutability, or capability-pattern evidence; retained outside conclusions."
        row = {
            **item,
            **classification,
            "id": stable_entity_id(url=url, name=str(item.get("name", ""))),
            "inspiration_roles": [role for role in inspiration_roles if role in {"offer", "pricing", "service_delivery", "positioning", "website", "brand", "youtube", "social", "content", "trust", "onboarding"}],
            "classification_reason": classification_reason,
            "classification_evidence": classification_sources,
            "evidence_quality": normalize_evidence_quality(item.get("evidence_quality")),
            "legacy_competitor_type_hint": str(item.get("competitor_type_hint", "")),
            "lane_observations": sorted(scopes),
            "analog_markets": analog_markets,
            "services": analysis.get("service_offers", []),
            "social_presence": entity_social,
            "marketing_observation": {
                "positioning_headline": analysis.get("positioning_headline", ""),
                "cta_language": analysis.get("cta_language", []),
                "trust_proof_language": analysis.get("trust_proof_language", []),
                "capability_patterns": capability_patterns,
                "retrieved_at": analysis.get("retrieved_at", ""),
            },
        }
        entities.append(row)
        for source in item.get("sources", []):
            if isinstance(source, dict) and source.get("url"):
                sources.append({"url": source["url"], "retrieved_at": item.get("first_seen_at", now), "evidence_type": "search_result", "claim": f"discovery observation for {source.get('lane_scope', 'unspecified')}"})
        sources.extend(classification_sources)

    lane_coverage = discovery_summary.get("lane_coverage", {}) if isinstance(discovery_summary, dict) else {}
    requested_lanes = {lane for lane, detail in lane_coverage.items() if lane in LANES and isinstance(detail, dict) and detail.get("query_count", 0) > 0}
    checked = sorted(requested_lanes or {lane for entity in entities for lane in entity.get("lane_observations", []) if lane in LANES})
    gaps = []
    for gap in social_data.get("coverage_gaps", []) if isinstance(social_data, dict) else []:
        gaps.append(f"Social coverage gap: {gap}")
    for lane in sorted(requested_lanes):
        if lane_coverage.get(lane, {}).get("candidate_count", 0) == 0:
            gaps.append(f"No candidate was found for requested lane: {lane}.")
    for alert in discovery_summary.get("needs_user_attention", []) if isinstance(discovery_summary, dict) else []:
        gaps.append(f"Discovery provider coverage gap: {alert}")
    if not marketing:
        gaps.append("No official-page marketing analysis supplied; market and analog classifications remain uncertain.")
    if any(not entity.get("social_presence") for entity in entities):
        gaps.append("One or more entities lack checked public social observations.")
    unique_sources = {(source["url"], source["retrieved_at"], source["evidence_type"], source.get("claim", "")): source for source in sources}
    result = {
        "schema_version": "1.0",
        "brief": {"service": args.service, "job": args.job, "target_segment": args.target_segment, "buyer": args.buyer, "geography": args.geography, "price_tier": args.price_tier},
        "entities": entities,
        "sources": list(unique_sources.values()),
        "coverage": {"lanes_checked": checked, "gaps": gaps, "retrieved_at": now},
    }
    validate_result(result)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    if args.workspace:
        verified = [entity for entity in entities if entity.get("verification_status") == "verified"]
        unresolved = [entity for entity in entities if entity.get("verification_status") not in {"verified", "excluded"}]
        gate = "pass" if verified and not unresolved and not gaps else "conditional_pass" if entities else "fail"
        update_stage(Path(args.workspace), "competitive_landscape", status="passed" if gate == "pass" else "in_progress" if gate == "conditional_pass" else "failed", gate_result=gate, artifacts=[out], open_gaps=gaps, next_action="Enrich unresolved entities and synthesize only verified lanes.")
    print(json.dumps({"entities": len(entities), "verified": sum(entity.get("verification_status") == "verified" for entity in entities), "output": str(out), "lanes_checked": checked}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
