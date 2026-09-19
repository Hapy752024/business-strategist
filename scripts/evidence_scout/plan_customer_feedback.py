#!/usr/bin/env python3
"""Build the mandatory topic-led plus entity-led VOC source-coverage plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LANES = (
    "independent_review_platforms",
    "google_business_reviews",
    "company_facebook_comments",
    "company_instagram_comments",
    "apple_app_store_reviews",
    "google_play_store_reviews",
    "external_forums_communities",
    "company_hosted_supplier_context",
)
ENTITY_LANES = {"competitive_market", "similar_company", "substitute"}


def load_entities(path: str) -> list[dict[str, Any]]:
    if not path:
        return []
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    entities = value.get("entities") if isinstance(value, dict) else value
    if not isinstance(entities, list):
        raise ValueError("--entities-json must contain a list or an object with an entities list")
    seen: set[str] = set()
    for entity in entities:
        if not isinstance(entity, dict):
            raise ValueError("each entity must be an object")
        missing = [key for key in ("id", "name", "domain", "lane") if not str(entity.get(key, "")).strip()]
        if missing:
            raise ValueError(f"entity is missing required fields: {', '.join(missing)}")
        if entity["lane"] not in ENTITY_LANES:
            raise ValueError(f"entity {entity['id']} has invalid lane {entity['lane']!r}")
        if entity["id"] in seen:
            raise ValueError(f"duplicate entity id {entity['id']!r}")
        seen.add(str(entity["id"]))
    return entities


def parse_locales(values: list[str]) -> list[str]:
    if not values:
        raise ValueError("repeat --locale COUNTRY:LANGUAGE at least once")
    locales: list[str] = []
    for value in values:
        if not re.fullmatch(r"[A-Za-z]{2}:[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", value.strip()):
            raise ValueError(f"invalid locale {value!r}; use COUNTRY:LANGUAGE")
        normalized = value.split(":", 1)[0].upper() + ":" + value.split(":", 1)[1].casefold()
        if normalized not in locales:
            locales.append(normalized)
    return locales


def locators(entity: dict[str, Any], lane: str, locale: str) -> list[str]:
    sources = entity.get("sources") if isinstance(entity.get("sources"), dict) else {}
    raw = sources.get(lane, [])
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    values: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            scopes = item.get("locales") if isinstance(item.get("locales"), list) else []
            if scopes and locale not in scopes:
                continue
        locator = item.get("locator") if isinstance(item, dict) else item
        if str(locator or "").strip():
            values.append(str(locator).strip())
    return values


def accepted_locators(entity: dict[str, Any], lane: str, locale: str) -> list[dict[str, str]]:
    """Return locators that a human explicitly accepted with a reason."""
    sources = entity.get("sources") if isinstance(entity.get("sources"), dict) else {}
    raw = sources.get(lane, [])
    if isinstance(raw, str):
        raw = [raw]
    accepted: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return accepted
    for item in raw:
        if not isinstance(item, dict):
            continue
        locator = str(item.get("locator", "")).strip()
        reason = str(item.get("review_reason", "")).strip()
        scopes = item.get("locales") if isinstance(item.get("locales"), list) else []
        if locator and item.get("review_status") == "accepted" and reason and locale in scopes:
            accepted.append({"locator": locator, "review_reason": reason})
    return accepted


def topic_cells(topic: str, segment: str, locales: list[str], cells: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Keep requested markets visible, even before the sampling plan is refined.

    Extra cells describe deliberate sampling, not a Cartesian quota. Country is
    collection scope, never evidence of a contributor's residence.
    """
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for supplied in cells or []:
        if not isinstance(supplied, dict) or supplied.get("locale") not in locales:
            raise ValueError("each topic cell must be an object with a requested locale")
        row = {name: str(supplied.get(name) or default).strip() for name, default in (
            ("locale", ""), ("job", topic), ("role", segment),
            ("source_family", "unspecified"), ("query_intent", "open_discovery"),
        )}
        digest = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:12]
        row["cell_id"] = str(supplied.get("cell_id") or f"topic-{digest}").strip()
        if not row["cell_id"] or row["cell_id"] in seen:
            raise ValueError("topic cell IDs must be non-empty and unique")
        seen.add(row["cell_id"])
        row["sampling_detail_status"] = "declared" if row["source_family"] != "unspecified" else "initial_broad_scope"
        output.append(row)
    for locale in locales:
        if any(row["locale"] == locale for row in output):
            continue
        cell_id = f"topic:{locale}"
        if cell_id in seen:
            raise ValueError(f"topic cell ID {cell_id!r} conflicts with a missing-locale cell")
        output.append({"cell_id": cell_id, "locale": locale, "job": topic, "role": segment,
                       "source_family": "unspecified", "query_intent": "open_discovery",
                       "sampling_detail_status": "initial_broad_scope"})
    return output


def build_plan(topic: str, segment: str, locales: list[str], entities: list[dict[str, Any]],
               topic_sampling_cells: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows: list[dict[str, Any]] = []
    for entity in entities:
        not_applicable = entity.get("not_applicable") if isinstance(entity.get("not_applicable"), dict) else {}
        for locale in locales:
            for lane in LANES:
                lane_locators = locators(entity, lane, locale)
                reviewed_locators = accepted_locators(entity, lane, locale)
                disposition = not_applicable.get(lane, "")
                # A language/storefront can exist in one market but not another.
                if isinstance(disposition, dict):
                    disposition = disposition.get(locale, "")
                reason = str(disposition).strip()
                if reason and lane_locators:
                    raise ValueError(f"entity {entity['id']} lane {lane} cannot have both locators and not_applicable")
                status = "locator_supplied" if lane_locators else "not_applicable" if reason else "discovery_required"
                rows.append({
                    "entity_id": entity["id"], "entity_name": entity["name"], "entity_domain": entity["domain"],
                    "entity_lane": entity["lane"], "locale": locale, "source_lane": lane,
                    "applicable": not bool(reason), "not_applicable_reason": reason or None,
                    "locator_status": status, "locators": lane_locators,
                    "reviewed_locators": reviewed_locators,
                    "planned": True if not reason else False, "attempted": False, "retrieved_count": 0,
                    "reviewed_count": 0, "accepted_customer_voice_count": 0, "failed_or_blocked": None,
                })
    return {
        "schema_version": 2, "generated_at": generated, "topic": topic, "customer_segment": segment,
        "locales": locales,
        "topic_matrix": topic_cells(topic, segment, locales, topic_sampling_cells),
        "analysis_contract": {
            "topic_led_voc": "required",
            "topic_led_entity_names_required": False,
            "entity_led_feedback": "required" if entities else "pending_entity_discovery",
            "sampling_frames_must_remain_separate_until_reviewed_u_r_mapping": True,
        },
        "entity_count": len(entities), "source_matrix": rows,
        "interpretation_rules": [
            "Star averages and rating counts are context, not customer voice.",
            "Company posts, replies and testimonials are supplier context.",
            "Customer comments remain unresolved until author role, actual use and target fit are reviewed.",
            "Separate independent customer needs (U) from solution-use requirements (R).",
            "Report per-entity and per-lane attempted, retrieved, reviewed and accepted denominators.",
            "Missing source locators require discovery; they do not prove a lane is inapplicable.",
            "Topic coverage is recorded per requested locale and refined job/role/source/intent cell, not inferred from aggregate counts.",
            "A collection locale is not proof of the speaker's country; author geography can remain unknown.",
            "Partial evidence supports only scoped findings; missing coverage is not absence of a customer need.",
        ],
    }


def write_markdown(plan: dict[str, Any], path: Path) -> None:
    lines = ["# Customer Feedback Coverage Plan", "", f"- Topic-led VOC: {plan['analysis_contract']['topic_led_voc']}", f"- Entity-led feedback: {plan['analysis_contract']['entity_led_feedback']}", f"- Entities: {plan['entity_count']}", "", "## Source coverage", "", "| Entity | Lane | Locale | Status | Locators |", "|---|---|---|---|---|"]
    for row in plan["source_matrix"]:
        locs = ", ".join(row["locators"]) or row["not_applicable_reason"] or "discover"
        lines.append(f"| {row['entity_name']} ({row['entity_lane']}) | {row['source_lane']} | {row['locale']} | {row['locator_status']} | {locs} |")
    if not plan["source_matrix"]:
        lines.append("| Pending verified entity discovery | all entity-feedback lanes | all declared locales | pending_entity_discovery | Topic-led VOC still runs now |")
    lines.extend(["", "## Mandatory topic-led sampling", "",
                  "| Cell | Locale | Job | Role | Source family | Query intent |", "|---|---|---|---|---|---|"])
    for row in plan["topic_matrix"]:
        lines.append("| " + " | ".join(str(row[key]) for key in ("cell_id", "locale", "job", "role", "source_family", "query_intent")) + " |")
    lines.extend(["", "## Interpretation boundary", ""] + [f"- {rule}" for rule in plan["interpretation_rules"]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True); parser.add_argument("--customer-segment", required=True)
    parser.add_argument("--locale", action="append", default=[]); parser.add_argument("--entities-json", default="")
    parser.add_argument("--topic-cells-json", default="", help="Optional list of job/role/source_family/query_intent cells with locale; omitted locales remain explicit discovery cells")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    try:
        locales = parse_locales(args.locale); entities = load_entities(args.entities_json)
        cells = json.loads(Path(args.topic_cells_json).read_text()) if args.topic_cells_json else None
        if cells is not None and not isinstance(cells, list):
            raise ValueError("--topic-cells-json must contain a list")
        plan = build_plan(args.topic, args.customer_segment, locales, entities, cells)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "customer-feedback-source-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(plan, out / "customer-feedback-source-plan.md")
    print(json.dumps({"status": "ok", "topic_led": "required", "entity_led": plan["analysis_contract"]["entity_led_feedback"], "entity_count": len(entities), "matrix_rows": len(plan["source_matrix"]), "out_dir": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
