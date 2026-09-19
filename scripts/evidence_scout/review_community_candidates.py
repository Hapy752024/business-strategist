#!/usr/bin/env python3
"""Promote evidence-bound community reviews and emit scoped capture artifacts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "community-review.schema.json"
CANDIDATE_SCHEMA = ROOT / "schemas" / "community-candidates.schema.json"
DISCOVERY_RECEIPT_SCHEMA = ROOT / "schemas" / "community-discovery-receipt.schema.json"
DISCOVERY_AUDIT_SCHEMA = ROOT / "schemas" / "community-discovery-audit.schema.json"
MAX_REVIEW_AGE = timedelta(days=30)
MAX_AUTH_TTL = timedelta(days=30)
DIMENSION_MAX_AGE = {"activity_status": timedelta(days=7), "public_access": timedelta(days=7)}
REQUIRED_DIMENSIONS = {
    "community_shape": "verified", "target_member_presence": "evidenced", "customer_segment_fit": "matched",
    "geography_fit": "matched", "language_fit": "matched", "activity_status": "active",
    "source_ownership": "peer_community", "recent_experience_route": "evidenced",
}
PUBLIC_METHODS = {"public_web", "paid_public_api"}
TEST_PRIVATE_KEY_B64 = base64.b64encode(bytes(range(32))).decode()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_bundle(out_dir: Path, values: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for name, value in values.items():
            handle, temp_name = tempfile.mkstemp(prefix=f".{name}.", dir=out_dir)
            os.close(handle); temp_path = Path(temp_name)
            temp_path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            staged.append((temp_path, out_dir / name))
        for temp_path, target in staged: temp_path.replace(target)
    finally:
        for temp_path, _ in staged:
            temp_path.unlink(missing_ok=True)


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def sign(value: dict[str, Any], key: str) -> str:
    unsigned = {name: item for name, item in value.items() if name != "signature"}
    return base64.b64encode(Ed25519PrivateKey.from_private_bytes(base64.b64decode(key)).sign(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())).decode()


def public_key_id(private_key_b64: str) -> str:
    raw = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64)).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def validate_packet(packet: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(read_json(SCHEMA), format_checker=FormatChecker())
    return [f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}" for error in sorted(validator.iter_errors(packet), key=lambda item: list(item.absolute_path))]


def validate_discovery(candidates: list[dict[str, Any]], receipt: dict[str, Any], audit: dict[str, Any], public_key_b64: str) -> list[str]:
    errors = [f"candidates: {error.message}" for error in Draft202012Validator(read_json(CANDIDATE_SCHEMA), format_checker=FormatChecker()).iter_errors(candidates)]
    errors.extend(f"receipt: {error.message}" for error in Draft202012Validator(read_json(DISCOVERY_RECEIPT_SCHEMA), format_checker=FormatChecker()).iter_errors(receipt))
    errors.extend(f"audit: {error.message}" for error in Draft202012Validator(read_json(DISCOVERY_AUDIT_SCHEMA), format_checker=FormatChecker()).iter_errors(audit))
    supplied = receipt.get("signature", ""); unsigned = {name: value for name, value in receipt.items() if name != "signature"}
    try:
        public_raw = base64.b64decode(public_key_b64); Ed25519PublicKey.from_public_bytes(public_raw).verify(base64.b64decode(str(supplied)), json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
        if receipt.get("key_id") != hashlib.sha256(public_raw).hexdigest(): errors.append("receipt key_id is invalid")
    except Exception: errors.append("receipt signature is invalid")
    if receipt.get("review_candidates_digest") != canonical_digest(candidates): errors.append("receipt candidate digest does not match")
    if receipt.get("audit_digest") != canonical_digest(audit): errors.append("receipt audit digest does not match")
    if set(audit.get("requested_providers", [])) != set(audit.get("provider_outcomes", {})): errors.append("discovery audit provider outcomes do not cover every requested provider")
    plan_ids = {item.get("query_id") for item in audit.get("query_plan", []) if isinstance(item, dict) and item.get("query_id")}
    for provider in audit.get("requested_providers", []):
        outcome = (audit.get("provider_outcomes") or {}).get(provider, {})
        executed, skipped = set(outcome.get("executed_queries", [])), set(outcome.get("skipped_queries", []))
        if executed & skipped or executed | skipped != plan_ids:
            errors.append(f"discovery audit {provider} does not account for every planned query exactly once")
        counts = outcome.get("result_counts_by_query", {})
        if provider != "offline_fixture" and (set(counts) != executed or sum(value for value in counts.values() if isinstance(value, int)) != outcome.get("result_count")):
            errors.append(f"discovery audit {provider} result counts do not match executed queries")
        if provider != "offline_fixture":
            observations = audit.get(provider, [])
            if not isinstance(observations, list) or {item.get("query_id") for item in observations if isinstance(item, dict)} != executed:
                errors.append(f"discovery audit {provider} execution records do not match executed queries")
    return errors


def validate_direct_rechecks(packet: dict[str, Any], public_key_b64: str, now: datetime | None = None) -> tuple[list[str], set[str]]:
    now = now or datetime.now(timezone.utc); errors: list[str] = []; trusted: set[str] = set(); public_raw = base64.b64decode(public_key_b64); public = Ed25519PublicKey.from_public_bytes(public_raw)
    for index, item in enumerate(packet.get("direct_rechecks", [])):
        signature = str(item.get("signature", "")); unsigned = {name: value for name, value in item.items() if name != "signature"}
        try: public.verify(base64.b64decode(signature), json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
        except Exception: errors.append(f"direct_rechecks/{index}: invalid discovery-role signature"); continue
        try: observed = parse_time(item["observed_at"])
        except (KeyError, ValueError, TypeError): errors.append(f"direct_rechecks/{index}: invalid observed_at"); continue
        checks = [item.get("key_id") == hashlib.sha256(public_raw).hexdigest(), item.get("status") == "retrieved", item.get("schema_version") == 2, item.get("entity_type") == item.get("entity_type_observed"), isinstance(item.get("http_status"), int) and item["http_status"] == 200, timedelta(0) <= now - observed <= timedelta(days=7), str(item.get("url", "")).rstrip("/") == str(item.get("final_url", "")).rstrip("/")]
        if not all(checks): errors.append(f"direct_rechecks/{index}: recheck must be current, successful, key-bound, and URL-stable"); continue
        trusted.add(signature)
    return errors, trusted


def evidence_locators(candidate: dict[str, Any], packet: dict[str, Any], trusted_rechecks: set[str]) -> set[str]:
    locators = {candidate.get("url", "")}
    locators.update(source.get("original_url", "") for source in candidate.get("sources", []))
    locators.update(item.get("locator", "") for item in packet.get("direct_rechecks", []) if item.get("url") == candidate.get("url") and item.get("signature") in trusted_rechecks)
    return {item for item in locators if item}


def evidence_records(candidate: dict[str, Any], packet: dict[str, Any], trusted_rechecks: set[str]) -> dict[tuple[str, str], set[str]]:
    result: dict[tuple[str, str], set[str]] = {}
    for source in candidate.get("sources", []):
        if isinstance(source.get("http_status"), int) and 200 <= source["http_status"] < 300:
            result.setdefault((source.get("original_url", ""), source.get("content_digest", "")), set()).add(source.get("fetched_at", ""))
    for item in packet.get("direct_rechecks", []):
        if item.get("url") == candidate.get("url") and item.get("status") == "retrieved" and item.get("signature") in trusted_rechecks:
            result.setdefault((item.get("locator", ""), item.get("content_digest", "")), set()).add(item.get("observed_at", ""))
    return result


def trusted_recheck_for(record: dict[str, Any], candidate: dict[str, Any], packet: dict[str, Any], trusted_rechecks: set[str]) -> dict[str, Any] | None:
    for item in packet.get("direct_rechecks", []):
        if item.get("signature") in trusted_rechecks and item.get("url") == candidate.get("url") and (item.get("locator"), item.get("content_digest"), item.get("observed_at")) == (record.get("locator"), record.get("content_digest"), record.get("observed_at")):
            return item
    return None


def decision_errors(decision: dict[str, Any], candidate: dict[str, Any], packet: dict[str, Any], now: datetime, trusted_rechecks: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        reviewed_at, valid_until = parse_time(decision["reviewed_at"]), parse_time(decision["valid_until"])
        if reviewed_at > now + timedelta(minutes=5):
            errors.append("reviewed_at is in the future")
        if now - reviewed_at > MAX_REVIEW_AGE:
            errors.append("review is older than 30 days")
        if valid_until <= now:
            errors.append("review is expired")
        if valid_until - reviewed_at > MAX_AUTH_TTL:
            errors.append("valid_until exceeds the 30-day maximum TTL")
    except (KeyError, ValueError, TypeError):
        errors.append("invalid reviewed_at or valid_until")
    allowed_locators = evidence_locators(candidate, packet, trusted_rechecks); records = evidence_records(candidate, packet, trusted_rechecks)
    method = (decision.get("access") or {}).get("method"); direct_required = method in PUBLIC_METHODS
    dimensions = decision.get("dimensions") or {}
    for field, expected in REQUIRED_DIMENSIONS.items():
        record = dimensions.get(field) or {}
        if record.get("status") != expected:
            errors.append(f"{field}.status must be {expected}")
        if record.get("locator") not in allowed_locators:
            errors.append(f"{field}.locator must match candidate provenance or a direct recheck")
        try:
            observed_at = parse_time(record.get("observed_at", ""))
            if observed_at > reviewed_at + timedelta(minutes=5):
                errors.append(f"{field}.observed_at is in the future")
            if reviewed_at - observed_at > DIMENSION_MAX_AGE.get(field, timedelta(days=30)):
                errors.append(f"{field}.observed_at is stale")
        except (ValueError, TypeError):
            errors.append(f"{field}.observed_at is invalid")
        evidence_times = records.get((record.get("locator"), record.get("content_digest")), set())
        if not evidence_times:
            errors.append(f"{field}.content_digest does not match the cited evidence")
        elif record.get("observed_at") not in evidence_times:
            errors.append(f"{field}.observed_at does not match the immutable retrieval record")
        if not record.get("note"):
            errors.append(f"{field}.note is required")
        if direct_required and field in {"community_shape", "activity_status"}:
            recheck = trusted_recheck_for(record, candidate, packet, trusted_rechecks)
            if not recheck:
                errors.append(f"{field} requires a signed direct target recheck")
            elif field == "community_shape" and recheck.get("entity_type_observed") != decision.get("verified_entity_type"):
                errors.append("community_shape direct recheck does not prove the verified entity type")
            elif field == "activity_status" and recheck.get("activity_status") != "active_recent":
                errors.append("activity_status direct recheck does not contain recent activity evidence")
    public_record = dimensions.get("public_access") or {}
    if public_record.get("status") not in {"public", "legitimate_member_access"}:
        errors.append("public_access.status is invalid")
    if public_record.get("locator") not in allowed_locators:
        errors.append("public_access.locator must match candidate provenance or a direct recheck")
    try:
        public_observed = parse_time(public_record.get("observed_at", ""))
        if public_observed > reviewed_at + timedelta(minutes=5):
            errors.append("public_access.observed_at is in the future")
        if reviewed_at - public_observed > DIMENSION_MAX_AGE["public_access"]:
            errors.append("public_access.observed_at is stale")
    except (ValueError, TypeError):
        errors.append("public_access.observed_at is invalid")
    if not public_record.get("note"):
        errors.append("public_access.note is required")
    public_times = records.get((public_record.get("locator"), public_record.get("content_digest")), set())
    if not public_times:
        errors.append("public_access.content_digest does not match the cited evidence")
    elif public_record.get("observed_at") not in public_times:
        errors.append("public_access.observed_at does not match the immutable retrieval record")
    if public_record.get("status") == "public":
        public_recheck = trusted_recheck_for(public_record, candidate, packet, trusted_rechecks)
        if not public_recheck:
            errors.append("public_access requires a signed direct target recheck")
        elif public_recheck.get("access_status") != "public_content":
            errors.append("public_access direct recheck did not retrieve public content")
    access = decision.get("access") or {}
    public_access = (dimensions.get("public_access") or {}).get("status")
    method = access.get("method")
    if public_access == "public" and method not in PUBLIC_METHODS:
        errors.append("public access requires public_web or paid_public_api")
    if public_access == "legitimate_member_access" and method != "user_supplied_legitimate_access":
        errors.append("legitimate member material must be user_supplied_legitimate_access")
    if access.get("no_credential_or_technical_bypass") is not True:
        errors.append("no_credential_or_technical_bypass must be true")
    signed_source_records = {(source.get("original_url"), source.get("content_digest"), source.get("fetched_at")) for source in candidate.get("sources", []) if isinstance(source.get("http_status"), int) and 200 <= source["http_status"] < 300}
    signed_source_records.update((item.get("locator"), item.get("content_digest"), item.get("observed_at")) for item in packet.get("direct_rechecks", []) if item.get("signature") in trusted_rechecks)
    if method in PUBLIC_METHODS and any((record.get("locator"), record.get("content_digest"), record.get("observed_at")) not in signed_source_records for record in dimensions.values()):
        errors.append("review evidence may rely only on signed index observations or signed direct rechecks")
    if decision.get("candidate_digest") != candidate.get("content_digest"):
        errors.append("candidate_digest does not match the reviewed candidate")
    entity = decision.get("verified_entity_type")
    candidate_entity = candidate.get("community_type")
    if candidate_entity == "facebook_group" and entity != "facebook_group":
        errors.append("a Facebook group candidate must be verified as facebook_group")
    if candidate_entity == "forum" and entity != "forum":
        errors.append("a forum candidate must be verified as forum")
    if candidate_entity == "facebook_entity_candidate" and entity not in {"facebook_group", "facebook_page"}:
        errors.append("a Facebook entity candidate must be directly verified as a group or page")
    qualified_locales = {lane.get("locale_id") for lane in candidate.get("lane_assessments", []) if lane.get("qualified")}
    source_locales = {f"{source.get('country')}:{source.get('language')}" for source in candidate.get("sources", [])}
    for locale_id in decision.get("reviewed_locale_ids", []):
        if locale_id not in qualified_locales:
            errors.append(f"reviewed locale {locale_id} has no qualified discovery lane")
        cited = {(record.get("locator"), record.get("content_digest")) for record in decision.get("dimensions", {}).values()}
        locale_sources = {(source.get("original_url"), source.get("content_digest")) for source in candidate.get("sources", []) if f"{source.get('country')}:{source.get('language')}" == locale_id}
        if not cited.intersection(locale_sources): errors.append(f"reviewed locale {locale_id} has no cited locale observation")
    return errors


def review(candidates: list[dict[str, Any]], packet: dict[str, Any], prior: list[dict[str, Any]] | None = None, now: datetime | None = None, signing_key: str = TEST_PRIVATE_KEY_B64, generation_id: str | None = None, generation_version: int = 1, state_id: str = "unit-test-state", trusted_rechecks: set[str] | None = None, discovery_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    by_url = {row.get("url"): row for row in candidates if row.get("url")}
    decision_rows = packet.get("decisions", [])
    duplicates = {url for url in (row.get("url") for row in decision_rows) if url and sum(item.get("url") == url for item in decision_rows) > 1}
    decisions = {row.get("url"): row for row in decision_rows if row.get("url") and row.get("url") not in duplicates}
    review_log: list[dict[str, Any]] = [{"url": url, "status": "unresolved", "reason": "Duplicate decisions supplied."} for url in sorted(duplicates)]
    unknown = sorted(set(decisions) - set(by_url))
    review_log.extend({"url": url, "status": "unresolved", "reason": "Decision URL is not a candidate."} for url in unknown)
    verified: list[dict[str, Any]] = []
    for url, candidate in by_url.items():
        decision = decisions.get(url)
        if not decision:
            if url not in duplicates:
                review_log.append({"url": url, "status": "unresolved", "reason": "No review decision supplied."})
            continue
        if decision.get("status") != "accepted":
            review_log.append({"url": url, "status": decision.get("status", "unresolved"), "reason": decision.get("reason", "No reason supplied.")})
            continue
        errors = decision_errors(decision, candidate, packet, now, trusted_rechecks or set())
        if errors:
            review_log.append({"url": url, "status": "unresolved", "reason": decision.get("reason"), "errors": errors})
            continue
        flat_dimensions = {name: value["status"] for name, value in decision["dimensions"].items()}
        promoted = {**candidate, **flat_dimensions, "review_status": "accepted", "reviewer": decision["reviewer"], "reviewed_at": decision["reviewed_at"], "review_reason": decision["reason"], "dimension_evidence": decision["dimensions"], "access": decision["access"], "research_use": "internal", "valid_until": decision["valid_until"], "ownership_cluster": decision["ownership_cluster"], "independence_status": decision["independence_status"], "verified_entity_type": decision["verified_entity_type"], "reviewed_locale_ids": decision["reviewed_locale_ids"], "eligible_for_targeted_collection": True}
        verified.append(promoted); review_log.append({"url": url, "status": "accepted", "reason": decision["reason"]})
    clusters: dict[str, list[dict[str, Any]]] = {}
    for row in verified: clusters.setdefault(row["ownership_cluster"], []).append(row)
    conflicted = {row["url"] for rows in clusters.values() if len(rows) > 1 for row in rows if row["independence_status"] == "distinct_source"}
    if conflicted:
        verified = [row for row in verified if row["url"] not in conflicted]
        for item in review_log:
            if item.get("url") in conflicted: item.update(status="unresolved", reason="distinct_source conflicts with another accepted source in the same ownership_cluster")
    current_urls = set(by_url); lifecycle: list[dict[str, Any]] = []
    for old in prior or []:
        url = old.get("url")
        if url not in current_urls:
            lifecycle.append({"url": url, "current_status": "not_observed_in_rerun", "action": "direct_recheck_required"})
        elif old.get("content_digest") != by_url[url].get("content_digest"):
            lifecycle.append({"url": url, "current_status": "changed_since_capture", "action": "repeat_source_review"})
    public_targets, user_supplied = [], []
    for row in verified:
        target = {"url": row["url"], "candidate_digest": row["content_digest"], "platform": "facebook" if row["verified_entity_type"].startswith("facebook_") else "web", "entity_type": row["verified_entity_type"], "endpoint_family": {"facebook_group": "facebook_group_posts", "facebook_page": "facebook_page_posts"}.get(row["verified_entity_type"], "none"), "access_class": row["public_access"], "access_method": row["access"]["method"], "no_credential_or_technical_bypass": row["access"]["no_credential_or_technical_bypass"], "reviewed_at": row["reviewed_at"], "reviewer": row["reviewer"], "valid_until": row["valid_until"]}
        if row["public_access"] == "public" and row["access"]["method"] in PUBLIC_METHODS and row["verified_entity_type"] in {"facebook_group", "facebook_page"}: public_targets.append(target)
        elif row["public_access"] != "public": user_supplied.append(target)
    verified_digest = canonical_digest(verified)
    generation_id = generation_id or str(uuid.uuid4()); review_run_id = str(uuid.uuid4())
    authorization = {"artifact_type": "community_capture_authorization", "schema_version": 4, "policy_version": "private-exploratory-research-v3", "purpose": "internal_voice_of_customer_research", "platform_authorization_claim": "none_internal_gate_only", "spend_authorization": "standing_authorized_no_cap", "state_id": state_id, "generation_id": generation_id, "generation_version": generation_version, "review_run_id": review_run_id, "candidates_artifact_digest": canonical_digest(candidates), "decisions_packet_digest": canonical_digest(packet), "targets": public_targets, "verified_artifact_digest": verified_digest, "generated_at": now.replace(microsecond=0).isoformat(), "status": "valid" if public_targets else "no_public_api_targets", "signature_algorithm": "ed25519", "key_id": public_key_id(signing_key)}
    reviewed = [row for row in review_log if row["status"] in {"accepted", "rejected"}]
    accepted_urls = {row["url"] for row in verified}; reviewed_urls = {row["url"] for row in reviewed}
    decision_by_url = {row.get("url"): row for row in packet.get("decisions", []) if row.get("status") in {"accepted", "rejected"}}
    def grouped_counts(key: str) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = {}
        for candidate in candidates:
            accepted = next((row for row in verified if row["url"] == candidate.get("url")), None)
            lanes = [lane for lane in candidate.get("lane_assessments", []) if lane.get("qualified")]
            values = {(lane.get("locale_id") if key == "locale" else lane.get("provider", "unknown")) for lane in lanes}
            for value in values or {"unknown"}:
                bucket = counts.setdefault(value, {"candidate_source_memberships": 0, "reviewed_source_memberships": 0, "accepted_source_memberships": 0})
                decision = decision_by_url.get(candidate.get("url"), {})
                reviewed_locales = decision.get("reviewed_locale_ids") or {lane.get("locale_id") for lane in lanes}
                reviewed_here = candidate.get("url") in reviewed_urls and (key != "locale" or value in reviewed_locales)
                accepted_here = candidate.get("url") in accepted_urls and (key != "locale" or value in (accepted or {}).get("reviewed_locale_ids", []))
                bucket["candidate_source_memberships"] += 1; bucket["reviewed_source_memberships"] += reviewed_here; bucket["accepted_source_memberships"] += accepted_here
        return counts
    provider_outcomes = (discovery_audit or {}).get("provider_outcomes", {})
    discovery_query_coverage = {name: {key: value.get(key, [] if key != "result_counts_by_query" else {}) for key in ("executed_queries", "skipped_queries", "result_counts_by_query")} | {"status": value.get("status")} for name, value in provider_outcomes.items()}
    metrics = {"candidate_count": len(candidates), "reviewed_count": len(reviewed), "accepted_source_count": len(verified), "locale_memberships_are_non_additive": True, "accepted_ownership_cluster_count": len({row["ownership_cluster"] for row in verified}), "independent_customer_observation_count": None, "unresolved_count": sum(row["status"] == "unresolved" for row in review_log), "decision_acceptance_rate": (len(verified) / len(reviewed)) if reviewed else None, "precision": None, "recall": None, "known_misses": packet.get("known_misses", []), "query_adjustments": packet.get("query_adjustments", []), "by_locale": grouped_counts("locale"), "by_provider": grouped_counts("provider"), "discovery_query_coverage": discovery_query_coverage, "recall_boundary": "Locale source memberships are non-additive. Accepted sources are not independent customer observations. No truth set or population frame exists, so precision and recall remain unknown; log known-positive misses and query changes per locale/provider."}
    authorization["review_log_digest"] = canonical_digest(review_log); authorization["signature"] = sign(authorization, signing_key)
    receipt = {"artifact_type": "community_review_current_receipt", "schema_version": 2, "state_id": state_id, "generation_id": generation_id, "generation_version": generation_version, "review_run_id": review_run_id, "status": authorization["status"], "authorization_digest": canonical_digest(authorization), "verified_artifact_digest": verified_digest, "review_log_digest": canonical_digest(review_log), "generated_at": authorization["generated_at"], "signature_algorithm": "ed25519", "key_id": public_key_id(signing_key)}
    receipt["signature"] = sign(receipt, signing_key)
    return {"verified": verified, "user_supplied": user_supplied, "review_log": review_log, "authorization": authorization, "receipt": receipt, "metrics": metrics, "lifecycle": lifecycle}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review and promote community candidates.")
    parser.add_argument("--candidates", required=True); parser.add_argument("--discovery-receipt", required=True); parser.add_argument("--discovery-audit", required=True); parser.add_argument("--decisions", required=True); parser.add_argument("--out-dir", required=True); parser.add_argument("--prior-verified", default=""); parser.add_argument("--signing-key-env", default="COMMUNITY_REVIEW_PRIVATE_KEY_B64"); parser.add_argument("--discovery-signing-key-env", default="COMMUNITY_DISCOVERY_PUBLIC_KEY_B64")
    return parser.parse_args()


def next_generation_version(state_dir: Path, state_id: str, review_public_raw: bytes) -> int:
    path = state_dir / f"{state_id}.json"
    if not path.exists():
        return 1
    current = read_json(path); signature = current.get("signature", ""); unsigned = {name: value for name, value in current.items() if name != "signature"}
    try:
        Ed25519PublicKey.from_public_bytes(review_public_raw).verify(base64.b64decode(str(signature)), json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
        version = int(current["generation_version"])
        if current.get("state_id") != state_id or version < 1: raise ValueError
    except Exception as exc:
        raise SystemExit(f"Authoritative community review state is invalid for lineage {state_id}; refusing overwrite.") from exc
    return version + 1


def main() -> int:
    args = parse_args(); out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    candidates = read_json(Path(args.candidates)); discovery_receipt = read_json(Path(args.discovery_receipt)); discovery_audit = read_json(Path(args.discovery_audit)); packet = read_json(Path(args.decisions)); prior = read_json(Path(args.prior_verified)) if args.prior_verified else []
    signing_key = os.environ.get(args.signing_key_env, ""); discovery_key = os.environ.get(args.discovery_signing_key_env, ""); state_id = str(discovery_receipt.get("review_lineage_id", "")); state_dir = Path(os.environ.get("COMMUNITY_REVIEW_STATE_DIR", ROOT / "projects" / "_infra" / "community-review-state"))
    try:
        review_public_raw = Ed25519PrivateKey.from_private_bytes(base64.b64decode(signing_key)).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        discovery_public_raw = base64.b64decode(discovery_key); Ed25519PublicKey.from_public_bytes(discovery_public_raw)
        if review_public_raw == discovery_public_raw: raise ValueError("discovery and review keypairs must differ")
    except Exception:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat(); log = [{"status": "invalid_signing_key_separation", "required_env": [args.signing_key_env, args.discovery_signing_key_env]}]
        generation_id, run_id, dummy_key, dummy_signature = str(uuid.uuid4()), str(uuid.uuid4()), "0" * 64, base64.b64encode(bytes(64)).decode()
        invalid_auth = {"artifact_type": "community_capture_authorization", "schema_version": 4, "policy_version": "private-exploratory-research-v3", "purpose": "internal_voice_of_customer_research", "platform_authorization_claim": "none_internal_gate_only", "spend_authorization": "standing_authorized_no_cap", "state_id": state_id, "generation_id": generation_id, "generation_version": 0, "review_run_id": run_id, "candidates_artifact_digest": canonical_digest(candidates), "decisions_packet_digest": canonical_digest(packet), "targets": [], "verified_artifact_digest": canonical_digest([]), "review_log_digest": canonical_digest(log), "generated_at": now, "status": "revoked_missing_signing_key", "signature_algorithm": "ed25519", "key_id": dummy_key, "signature": dummy_signature}
        invalid_receipt = {"artifact_type": "community_review_current_receipt", "schema_version": 2, "state_id": state_id, "generation_id": generation_id, "generation_version": 0, "review_run_id": run_id, "status": "revoked_missing_signing_key", "authorization_digest": canonical_digest(invalid_auth), "verified_artifact_digest": canonical_digest([]), "review_log_digest": canonical_digest(log), "generated_at": now, "signature_algorithm": "ed25519", "key_id": dummy_key, "signature": dummy_signature}
        write_bundle(out_dir, {"verified_communities.json": [], "user_supplied_private_sources.json": [], "community_review_log.json": log, "capture_authorization.json": invalid_auth, "community_review_current.json": invalid_receipt, "community_review_metrics.json": {"status": "missing_signing_key"}, "community_lifecycle.json": []})
        print(json.dumps({"authorization_status": "missing_signing_key", "required_env": [args.signing_key_env, args.discovery_signing_key_env]}, indent=2)); return 2
    generation_version = next_generation_version(state_dir, state_id, review_public_raw)
    recheck_errors, trusted_rechecks = validate_direct_rechecks(packet, discovery_key)
    schema_errors = validate_packet(packet) + validate_discovery(candidates, discovery_receipt, discovery_audit, discovery_key) + recheck_errors
    if schema_errors:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat(); generation_id = str(uuid.uuid4()); run_id = str(uuid.uuid4()); log = [{"status": "invalid_packet", "errors": schema_errors}]
        authorization = {"artifact_type": "community_capture_authorization", "schema_version": 4, "policy_version": "private-exploratory-research-v3", "purpose": "internal_voice_of_customer_research", "platform_authorization_claim": "none_internal_gate_only", "spend_authorization": "standing_authorized_no_cap", "state_id": state_id, "generation_id": generation_id, "generation_version": generation_version, "review_run_id": run_id, "candidates_artifact_digest": canonical_digest(candidates), "decisions_packet_digest": canonical_digest(packet), "targets": [], "verified_artifact_digest": canonical_digest([]), "review_log_digest": canonical_digest(log), "generated_at": now, "status": "revoked_invalid_packet", "signature_algorithm": "ed25519", "key_id": public_key_id(signing_key)}; authorization["signature"] = sign(authorization, signing_key)
        receipt = {"artifact_type": "community_review_current_receipt", "schema_version": 2, "state_id": state_id, "generation_id": generation_id, "generation_version": generation_version, "review_run_id": run_id, "status": "revoked_invalid_packet", "authorization_digest": canonical_digest(authorization), "verified_artifact_digest": canonical_digest([]), "review_log_digest": canonical_digest(log), "generated_at": now, "signature_algorithm": "ed25519", "key_id": public_key_id(signing_key)}; receipt["signature"] = sign(receipt, signing_key)
        write_bundle(out_dir, {"verified_communities.json": [], "user_supplied_private_sources.json": [], "community_review_log.json": log, "capture_authorization.json": authorization, "community_review_current.json": receipt, "community_review_metrics.json": {"status": "invalid_packet"}, "community_lifecycle.json": []})
        write_bundle(state_dir, {f"{state_id}.json": receipt})
        print(json.dumps({"verified_count": 0, "authorization_status": "revoked_invalid_packet", "errors": schema_errors}, indent=2)); return 2
    result = review(candidates, packet, prior, signing_key=signing_key, generation_version=generation_version, state_id=state_id, trusted_rechecks=trusted_rechecks, discovery_audit=discovery_audit)
    write_bundle(out_dir, {"verified_communities.json": result["verified"], "user_supplied_private_sources.json": result["user_supplied"], "community_review_log.json": result["review_log"], "capture_authorization.json": result["authorization"], "community_review_current.json": result["receipt"], "community_review_metrics.json": result["metrics"], "community_lifecycle.json": result["lifecycle"]})
    write_bundle(state_dir, {f"{state_id}.json": result["receipt"]})
    print(json.dumps({"verified_count": len(result["verified"]), "public_api_target_count": len(result["authorization"]["targets"]), "authorization_status": result["authorization"]["status"], "output_dir": str(out_dir)}, indent=2)); return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
