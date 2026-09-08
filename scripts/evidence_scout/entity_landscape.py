#!/usr/bin/env python3
"""Pure, deterministic lane classification helpers.

Network collectors remain in their existing provider scripts. Keeping the
classification contract pure makes it cheap to test and prevents a search
snippet from silently becoming a competitive verdict.
"""

from __future__ import annotations

import hashlib
import urllib.parse
from typing import Any


LANES = {"competitive_market", "similar_company", "capability_reference", "excluded", "uncertain"}
ROLES = {"direct", "indirect", "substitute", "future_threat", "none", "unknown"}
FIT = {"strong", "partial", "none", "unknown"}
EVIDENCE_QUALITY = {"high", "medium", "low", "unverified"}


def _fit(value: Any) -> str:
    return value if value in FIT else "unknown"


def normalize_evidence_quality(value: Any) -> str:
    """Map discovery vocabulary to the canonical landscape vocabulary."""
    normalized = str(value or "").casefold()
    return {
        "strong": "high",
        "high": "high",
        "medium": "medium",
        "weak": "low",
        "low": "low",
        "unverified": "unverified",
    }.get(normalized, "unverified")


def stable_entity_id(*, url: str = "", name: str = "") -> str:
    """Return an ordering-independent identifier suitable for cross-run joins."""
    host = (urllib.parse.urlsplit(url).hostname or "").casefold()
    if host.startswith("www."):
        host = host[4:]
    identity = host or " ".join(name.casefold().split())
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    return f"entity-{digest}"


def classify_entity(
    *,
    offer_job_overlap: str,
    target_segment_overlap: str,
    buyer_overlap: str = "unknown",
    geography_overlap: str = "unknown",
    price_tier_overlap: str = "unknown",
    purchase_substitutability: str = "unknown",
    official_service_evidence: bool = False,
    supplied_as_reference: bool = False,
    reference_observation_evidence: bool = False,
    excluded_source: bool = False,
    legacy_role: str = "",
) -> dict[str, str]:
    """Return the primary lane and commercial role from explicit dimensions.

    Geography is intentionally not required for digital/global offers when a
    buyer and purchasability match are explicit. Unknowns remain unknown.
    """
    dimensions = {
        "offer_job_overlap": _fit(offer_job_overlap),
        "target_segment_overlap": _fit(target_segment_overlap),
        "buyer_overlap": _fit(buyer_overlap),
        "geography_overlap": _fit(geography_overlap),
        "price_tier_overlap": _fit(price_tier_overlap),
        "purchase_substitutability": _fit(purchase_substitutability),
    }
    if excluded_source:
        return {**dimensions, "primary_lane": "excluded", "competitive_role": "none", "verification_status": "excluded"}

    same_market = (
        dimensions["offer_job_overlap"] == "strong"
        and dimensions["target_segment_overlap"] == "strong"
        and dimensions["buyer_overlap"] in {"strong", "partial"}
        and dimensions["purchase_substitutability"] in {"strong", "partial"}
        and dimensions["geography_overlap"] in {"strong", "partial", "unknown"}
        and official_service_evidence
    )
    if same_market:
        role = legacy_role if legacy_role in {"direct", "indirect", "substitute", "future_threat"} else "direct"
        if role == "direct":
            lane = "competitive_market"
        else:
            lane = "competitive_market"
        return {**dimensions, "primary_lane": lane, "competitive_role": role, "verification_status": "verified"}

    analogous = (
        dimensions["offer_job_overlap"] in {"strong", "partial"}
        and official_service_evidence
        and (
            dimensions["target_segment_overlap"] in {"none", "partial"}
            or dimensions["geography_overlap"] in {"none", "partial"}
            or dimensions["buyer_overlap"] in {"none", "partial"}
        )
    )
    if analogous:
        return {**dimensions, "primary_lane": "similar_company", "competitive_role": "none", "verification_status": "verified"}

    if supplied_as_reference and reference_observation_evidence:
        return {**dimensions, "primary_lane": "capability_reference", "competitive_role": "none", "verification_status": "verified"}

    return {**dimensions, "primary_lane": "uncertain", "competitive_role": "unknown", "verification_status": "uncertain"}


def legacy_hint(competitive_role: str, primary_lane: str) -> str:
    """Provide a stable compatibility hint for existing consumers."""
    if primary_lane == "similar_company":
        return "similar_company_analog"
    if primary_lane == "capability_reference":
        return "capability_reference"
    if primary_lane == "competitive_market":
        return competitive_role
    return "uncertain_candidate"


def normalize_social_presence(*, platform: str, url: str, status: str, retrieved_at: str, role: str = "unknown", evidence_type: str = "official_profile", posts_sampled: int = 0, coverage_gap: str = "", sample_window: str = "", formats: list[str] | None = None, cadence: str = "unknown", cta: list[str] | None = None, public_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize a public platform observation without implying absence or success."""
    allowed_status = {"verified_active", "verified_inactive", "unverified", "not_found_in_checked_sources"}
    return {
        "platform": platform,
        "url": url,
        "status": status if status in allowed_status else "unverified",
        "role": role,
        "retrieved_at": retrieved_at,
        "evidence_type": evidence_type,
        "posts_sampled": max(0, int(posts_sampled)),
        "sample_window": sample_window,
        "formats": list(dict.fromkeys(formats or [])),
        "cadence": cadence,
        "cta": list(dict.fromkeys(cta or [])),
        "public_metrics": public_metrics or {},
        "coverage_gap": coverage_gap,
        "metrics_are_public_proxies": True,
    }


if __name__ == "__main__":
    print("entity_landscape helpers: import classify_entity or normalize_social_presence")
