#!/usr/bin/env python3
"""Normalize public social observations for a lane-aware entity set.

The provider-specific collectors remain opt-in and governed by provider policy.
This script is intentionally network-free: it makes presence status, coverage
gaps and public-proxy boundaries deterministic before a provider is used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from entity_landscape import normalize_social_presence


def observation_rank(observation: dict[str, Any]) -> tuple[int, str, int]:
    status_rank = {"verified_active": 3, "verified_inactive": 3, "not_found_in_checked_sources": 2, "unverified": 1}
    return (status_rank.get(str(observation.get("status")), 0), str(observation.get("retrieved_at", "")), int(observation.get("posts_sampled", 0) or 0))


def is_sampled_observation(observation: Any) -> bool:
    if not isinstance(observation, dict):
        return False
    platform = str(observation.get("platform", "")).strip().casefold()
    status = str(observation.get("status", "")).strip()
    has_identity = bool(str(observation.get("url", "")).strip()) or status == "not_found_in_checked_sources"
    has_sampling = bool(int(observation.get("posts_sampled", 0) or 0) > 0 or observation.get("sample_window") or status in {"verified_active", "verified_inactive", "not_found_in_checked_sources"})
    return platform not in {"", "unknown"} and has_identity and has_sampling


def load(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("entities", []) if isinstance(data, dict) else []


def normalize_entities(items: list[dict[str, Any]], retrieved_at: str, marketing: dict[str, dict[str, Any]] | None = None, sampled: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    output = []
    for entity in items:
        if not isinstance(entity, dict):
            continue
        url = str(entity.get("url", ""))
        observations = list(entity.get("social_presence", []))
        observations.extend((marketing or {}).get(url, {}).get("social_presence", []))
        observations.extend((sampled or {}).get(url, {}).get("social_presence", []))
        normalized_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for observation in observations:
            if not isinstance(observation, dict):
                continue
            normalized = normalize_social_presence(
                platform=str(observation.get("platform", "unknown")),
                url=str(observation.get("url", "")),
                status=str(observation.get("status", "unverified")),
                retrieved_at=str(observation.get("retrieved_at", retrieved_at)),
                role=str(observation.get("role", "unknown")),
                evidence_type=str(observation.get("evidence_type", "official_profile")),
                posts_sampled=int(observation.get("posts_sampled", 0) or 0),
                coverage_gap=str(observation.get("coverage_gap", "")),
                sample_window=str(observation.get("sample_window", "")),
                formats=[str(value) for value in observation.get("formats", [])],
                cadence=str(observation.get("cadence", "unknown")),
                cta=[str(value) for value in observation.get("cta", [])],
                public_metrics=observation.get("public_metrics", {}) if isinstance(observation.get("public_metrics", {}), dict) else {},
            )
            key = (normalized["platform"], normalized["url"])
            existing = normalized_by_key.get(key)
            if existing is None or observation_rank(normalized) > observation_rank(existing):
                normalized_by_key[key] = normalized
        copy = dict(entity)
        copy["social_presence"] = list(normalized_by_key.values())
        output.append(copy)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entities-json", required=True)
    parser.add_argument("--marketing-json", default="", help="Optional official-site link observations from the marketing analyzer.")
    parser.add_argument("--observations-json", default="", help="Optional provider/manual profile sampling keyed by entity URL.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--retrieved-at", default="")
    args = parser.parse_args()
    from datetime import datetime, timezone
    retrieved_at = args.retrieved_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    def indexed(path: str) -> dict[str, dict[str, Any]]:
        if not path:
            return {}
        items = load(Path(path))
        return {str(item.get("url")): item for item in items if item.get("url")}
    marketing = indexed(args.marketing_json)
    sampled = indexed(args.observations_json)
    normalized = normalize_entities(load(Path(args.entities_json)), retrieved_at, marketing, sampled)
    sampled_observation_count = sum(
        1 for entity in sampled.values() for observation in entity.get("social_presence", []) if is_sampled_observation(observation)
    )
    gaps = [] if sampled_observation_count else ["Profile activity/content was not provider-sampled; official-site links remain unverified observations."]
    result = {"schema_version": "1.0", "retrieved_at": retrieved_at, "entities": normalized, "provider": "network-free-normalizer", "coverage_gaps": gaps}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"entities": len(result["entities"]), "output": args.out, "provider": result["provider"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
