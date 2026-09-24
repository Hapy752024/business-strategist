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
APPROACHES = {
    "customer_workflow": {
        "owner": "market-problem-discovery/evidence-scout",
        "question": "What happens in the customer's situation, including workarounds and satisfactory outcomes?",
        "source_frame": "topic-led customer voice without requiring supplier names",
    },
    "alternatives_and_cases": {
        "owner": "competitive-landscape-builder/evidence-scout",
        "question": "How does this target customer solve the same job across software, services, manual work and no action?",
        "source_frame": "actual shortlist and relevant comparable companies; geography is a contextual field",
    },
    "switching_and_changes": {
        "owner": "competitor-monitoring/interview-bridge",
        "question": "What triggered a search or change, who could approve it, and why did others stay?",
        "source_frame": "dated customer episodes and company changes with affected-customer evidence",
    },
    "ecosystem_and_implementation": {
        "owner": "competitive-landscape-builder/evidence-scout",
        "question": "Which integrations, marketplace tasks or repeated implementation jobs illuminate the customer workflow?",
        "source_frame": "platform/ecosystem observations and attributed customer or intermediary accounts",
    },
}


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
               topic_sampling_cells: list[dict[str, Any]] | None = None, *, decision: str = "",
               research_questions: list[str] | None = None, known_facts: list[str] | None = None,
               hypotheses: list[str] | None = None, alternatives: list[str] | None = None,
               distinguishing_observations: list[str] | None = None,
               intent: str = "customer_problem", approaches: list[str] | None = None,
               study_id: str = "", research_design_digest: str = "") -> dict[str, Any]:
    if intent not in {"customer_problem", "idea_validation"}:
        raise ValueError("intent must be customer_problem or idea_validation")
    selected_approaches = list(dict.fromkeys(approaches or ["customer_workflow"]))
    unknown_approaches = sorted(set(selected_approaches) - set(APPROACHES))
    if unknown_approaches:
        raise ValueError("unknown research approaches: " + ", ".join(unknown_approaches))
    if "customer_workflow" not in selected_approaches:
        raise ValueError("substantive customer-input research requires the customer_workflow approach")
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    questions = research_questions or ([
        "Which assumptions about the proposed customer's problem and alternatives are supported, contradicted, or unresolved?",
        "What past customer behavior or context would change confidence in this idea?",
    ] if intent == "idea_validation" else [
        "In which situations do people encounter this job or problem?",
        "What do people do now, and when do those alternatives work or fail?",
        "Which consequences or contexts would change what should be investigated next?",
    ])
    question_rows = []
    for text in questions:
        clean = " ".join(str(text).split())
        if not clean:
            continue
        question_rows.append({"id": "Q-" + hashlib.sha256(clean.casefold().encode()).hexdigest()[:10], "text": clean})
    if len({row["id"] for row in question_rows}) != len(question_rows):
        raise ValueError("research questions must be unique")
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
    if study_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", study_id):
        raise ValueError("study_id must be a short path-independent identifier")
    if research_design_digest and not re.fullmatch(r"[a-f0-9]{64}", research_design_digest):
        raise ValueError("research_design_digest must be a lowercase SHA-256 digest")
    return {
        "schema_version": 2, "generated_at": generated, "topic": topic, "customer_segment": segment,
        "study_intent": intent,
        "study_id": study_id or None,
        "research_design_digest": research_design_digest or None,
        "locales": locales,
        "research_design": {
            "intent": intent,
            "decision": decision.strip() or (f"Assess the stated customer/problem hypothesis about {topic}." if intent == "idea_validation"
                                               else f"Understand customer situations and problems related to {topic}."),
            "questions": question_rows,
            "known_facts": [str(x).strip() for x in (known_facts or []) if str(x).strip()],
            "hypotheses": [str(x).strip() for x in (hypotheses or []) if str(x).strip()],
            "alternative_explanations": [str(x).strip() for x in (alternatives or []) if str(x).strip()],
            "distinguishing_observations": [str(x).strip() for x in (distinguishing_observations or []) if str(x).strip()],
        },
        "approach_work_packets": [
            {"approach_id": approach, **APPROACHES[approach],
             "question_ids": [row["id"] for row in question_rows],
             "output_owner": "coordinator", "write_scope": f"work-packets/{approach}/"}
            for approach in selected_approaches
        ],
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
    design = plan["research_design"]
    lines = ["# Customer Feedback Coverage Plan", "", f"- Decision: {design['decision']}", "", "## Research questions", ""]
    lines.extend(f"- {row['id']}: {row['text']}" for row in design["questions"])
    lines.extend(["", "## Selected research approaches", "",
                  "Each approach has an isolated work-packet directory. Only the coordinator writes the synthesis."])
    lines.extend(f"- `{row['approach_id']}` — {row['question']} Source frame: {row['source_frame']} Owner: {row['owner']}. Output: `{row['write_scope']}`"
                 for row in plan.get("approach_work_packets", []))
    for label, key in (("Known facts", "known_facts"), ("Hypotheses", "hypotheses"), ("Alternative explanations", "alternative_explanations"), ("Distinguishing observations", "distinguishing_observations")):
        if design[key]:
            lines.extend(["", f"## {label}", ""] + [f"- {item}" for item in design[key]])
    lines.extend(["", f"- Topic-led VOC: {plan['analysis_contract']['topic_led_voc']}", f"- Entity-led feedback: {plan['analysis_contract']['entity_led_feedback']}", f"- Entities: {plan['entity_count']}", "", "## Source coverage", "", "| Entity | Lane | Locale | Status | Locators |", "|---|---|---|---|---|"])
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
    parser.add_argument("--decision", default="", help="Decision this research should inform; defaults to broad problem exploration.")
    parser.add_argument("--intent", choices=("customer_problem", "idea_validation"), default="customer_problem",
                        help="Keep the user's requested research outcome explicit in the source plan.")
    parser.add_argument("--study-id", default="", help="Identity printed by the active research plan; needed to close a v3 discovery study.")
    parser.add_argument("--research-design-digest", default="", help="SHA-256 from the active research plan's current study identity.")
    parser.add_argument("--approach", action="append", choices=tuple(APPROACHES), default=None,
                        help="Select a complementary approach; repeat to create separate work packets. Defaults to customer workflow.")
    parser.add_argument("--question", action="append", default=[], help="Research question; repeat as needed. Broad discovery gets open questions by default.")
    parser.add_argument("--known-fact", action="append", default=[])
    parser.add_argument("--hypothesis", action="append", default=[])
    parser.add_argument("--alternative-explanation", action="append", default=[])
    parser.add_argument("--distinguishing-observation", action="append", default=[])
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    try:
        locales = parse_locales(args.locale); entities = load_entities(args.entities_json)
        cells = json.loads(Path(args.topic_cells_json).read_text()) if args.topic_cells_json else None
        if cells is not None and not isinstance(cells, list):
            raise ValueError("--topic-cells-json must contain a list")
        plan = build_plan(args.topic, args.customer_segment, locales, entities, cells,
                          decision=args.decision, research_questions=args.question or None, known_facts=args.known_fact,
                          hypotheses=args.hypothesis, alternatives=args.alternative_explanation,
                          distinguishing_observations=args.distinguishing_observation,
                          intent=args.intent, approaches=args.approach,
                          study_id=args.study_id, research_design_digest=args.research_design_digest)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "customer-feedback-source-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(plan, out / "customer-feedback-source-plan.md")
    for packet in plan["approach_work_packets"]:
        packet_dir = out / packet["write_scope"]
        packet_dir.mkdir(parents=True, exist_ok=True)
        (packet_dir / "assignment.json").write_text(json.dumps({
            "schema_version": 1, "study_intent": plan["study_intent"], "user_question": plan["research_design"]["decision"],
            "topic": plan["topic"], "customer_segment": plan["customer_segment"], "locales": plan["locales"],
            "approach": packet, "research_questions": plan["research_design"]["questions"],
            "known_facts": plan["research_design"]["known_facts"], "hypotheses": plan["research_design"]["hypotheses"],
            "alternative_explanations": plan["research_design"]["alternative_explanations"],
            "output_file": "result.json", "synthesis_owner": "coordinator",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "topic_led": "required", "entity_led": plan["analysis_contract"]["entity_led_feedback"], "entity_count": len(entities), "matrix_rows": len(plan["source_matrix"]), "out_dir": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
