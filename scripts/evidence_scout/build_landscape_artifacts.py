#!/usr/bin/env python3
"""Build synthesis artifacts from a schema-validated entity landscape."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from workspace import update_stage

ROOT = Path(__file__).resolve().parents[2]

def load(path: str, default: Any) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def entities(data: Any) -> list[dict[str, Any]]:
    values = data if isinstance(data, list) else data.get("entities", []) if isinstance(data, dict) else []
    return [value for value in values if isinstance(value, dict)]


def analyses(data: Any) -> dict[str, dict[str, Any]]:
    values = data if isinstance(data, list) else data.get("analyses", []) if isinstance(data, dict) else []
    return {str(value.get("url")): value for value in values if isinstance(value, dict) and value.get("url")}


def compact(value: Any, limit: int = 180) -> str:
    return " ".join(str(value or "").split())[:limit].replace("|", "\\|")


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def validate_landscape(data: Any) -> None:
    schema = json.loads((ROOT / "schemas/entity-landscape.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data), key=lambda error: list(error.path))
    if errors:
        details = "\n".join(f"- {'/'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors)
        raise ValueError(f"refusing to synthesize an invalid entity landscape:\n{details}")


def verified(rows: list[dict[str, Any]], lane: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("primary_lane") == lane and row.get("verification_status") == "verified"]


def render_market(rows: list[dict[str, Any]], by_url: dict[str, dict[str, Any]]) -> str:
    lines = ["# Competitive market matrix", "", "Only verified `competitive_market` entities appear below.", "", "| Entity | Role | Offer/job | Segment | Buyer | Geography | Substitutability | Observed services/pricing | Social evidence |", "|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        analysis = by_url.get(str(row.get("url", "")), {})
        services = row.get("services", [])
        pricing = analysis.get("normalized_price_tokens", {})
        social = row.get("social_presence", [])
        lines.append("| " + " | ".join([
            compact(row.get("name")), compact(row.get("competitive_role")), compact(row.get("offer_job_overlap")),
            compact(row.get("target_segment_overlap")), compact(row.get("buyer_overlap")), compact(row.get("geography_overlap")),
            compact(row.get("purchase_substitutability")), compact({"services": len(services), "pricing": pricing or "not_found"}),
            compact(f"{len(social)} checked observation(s)" if social else "not collected"),
        ]) + " |")
    if not rows:
        lines.extend(["", "No verified same-market entity is available; competitive-pressure and whitespace conclusions are blocked."])
    lines.extend(["", "## Interpretation boundary", "", "Unknown and unverified cells are not market gaps. A candidate USP additionally requires repeated customer evidence and a credible proof mechanism.", ""])
    return "\n".join(lines)


def inspiration_record(row: dict[str, Any]) -> dict[str, Any]:
    observation = row.get("marketing_observation", {})
    headline = compact(observation.get("positioning_headline"))
    capability_patterns = [pattern for pattern in observation.get("capability_patterns", []) if isinstance(pattern, dict) and pattern.get("observed_pattern")]
    roles = row.get("inspiration_roles", [])
    if row.get("primary_lane") == "capability_reference":
        pattern = compact(capability_patterns[0]["observed_pattern"]) if capability_patterns else "No transferable pattern observed in the supplied evidence."
        complete = bool(capability_patterns and roles)
    else:
        pattern = headline or "No transferable pattern observed in the supplied evidence."
        complete = bool(headline and roles)
    context = ", ".join(row.get("analog_markets", [])) or compact(row.get("target_segment_overlap"))
    return {
        "entity": row.get("name", ""),
        "roles": roles,
        "observed_pattern": pattern,
        "context": context or "context not established",
        "adaptation_required": f"Re-derive the {', '.join(roles)} pattern for the target customer's language, proof needs, and buying context." if roles else "Name a capability purpose before using this entity as inspiration.",
        "transfer_risk": "The source audience, market, and proof conditions may not transfer to the target segment.",
        "do_not_copy": "Do not copy protected expression, visual identity, wording, or unsupported claims.",
        "cheapest_test": f"Test one original {roles[0]} variation with target customers before adoption." if roles else "Blocked until a learning purpose is named.",
        "synthesis_status": "ready" if complete else "needs_enrichment",
    }


def render_inspiration(rows: list[dict[str, Any]], title: str) -> tuple[str, list[dict[str, Any]]]:
    records = [inspiration_record(row) for row in rows]
    lines = [f"# {title}", "", "These are inspiration inputs, not evidence of competitive pressure or demand.", "", "| Entity | Roles | Observed pattern | Adaptation | Transfer risk | Do not copy | Cheapest test | Status |", "|---|---|---|---|---|---|---|---|"]
    for record in records:
        lines.append("| " + " | ".join(compact(record[key]) for key in ["entity", "roles", "observed_pattern", "adaptation_required", "transfer_risk", "do_not_copy", "cheapest_test", "synthesis_status"]) + " |")
    if not records:
        lines.extend(["", "No verified entity is available for this inspiration lane."])
    return "\n".join(lines) + "\n", records


def positioning_document(competitive: list[dict[str, Any]]) -> str:
    lines = ["# Positioning hypotheses", "", "Status: customer-evidence gate required.", ""]
    if not competitive:
        lines.append("No verified same-market competitor is available. Competitive gap claims are blocked; a customer-based entry hypothesis may still be investigated with explicit coverage limits.")
    else:
        lines.extend([
            "The verified landscape can identify occupied promises, but it cannot establish a USP by itself.",
            "Assess the customer need and why the entrant could be noticed, chosen and retained at viable economics. Existing supply does not establish saturation; an uncovered outcome is required only for a claim of an unmet need.",
            "",
            "Verified entities to contrast: " + ", ".join(str(row.get("name", "")) for row in competitive) + ".",
        ])
    lines.extend(["", "## Entrant assessment — analyst review required", "", "Assess visibility, sales, service and retention against the customer journey, with sourced strengths, weaknesses and unknowns. Link the acquisition path and delivery capacity to the founder's required customers, contribution and 12–24-month horizon or explicit deadline. These generated instructions are not a completed assessment."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entities-json", required=True)
    parser.add_argument("--marketing-json", default="")
    parser.add_argument("--workspace", default="")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out = Path(args.out_dir)
    landscape = load(args.entities_json, {})
    validate_landscape(landscape)
    all_rows = entities(landscape)
    by_url = analyses(load(args.marketing_json, [])) if args.marketing_json else {}
    competitive = verified(all_rows, "competitive_market")
    similar = verified(all_rows, "similar_company")
    references = verified(all_rows, "capability_reference")

    offer_matrix = []
    social_matrix = []
    for row in all_rows:
        analysis = by_url.get(str(row.get("url", "")), {})
        services = row.get("services", [])
        canonical_prices = [service.get("prices", {}) for service in services if isinstance(service, dict) and service.get("prices")]
        service_statuses = [service.get("price_status") for service in services if isinstance(service, dict)]
        pricing = canonical_prices or analysis.get("normalized_price_tokens", {})
        pricing_status = "structured_price_found" if "structured_price_found" in service_statuses else "pricing_mentioned" if "pricing_mentioned" in service_statuses else analysis.get("price_status", "not_found")
        offer_matrix.append({"entity": row.get("name"), "url": row.get("url"), "lane": row.get("primary_lane"), "verification_status": row.get("verification_status"), "services": services, "pricing": pricing, "pricing_status": pricing_status})
        social_matrix.append({"entity": row.get("name"), "url": row.get("url"), "lane": row.get("primary_lane"), "social_presence": row.get("social_presence", []), "metrics_are_public_proxies": True})
    write(out / "offer-price-matrix.json", offer_matrix)
    write(out / "social-presence.json", social_matrix)
    (out / "competitive-market-matrix.md").write_text(render_market(competitive, by_url), encoding="utf-8")
    similar_md, similar_records = render_inspiration(similar, "Similar-company inspiration")
    reference_md, reference_records = render_inspiration(references, "Capability reference library")
    (out / "similar-company-inspiration.md").write_text(similar_md, encoding="utf-8")
    (out / "capability-reference-library.md").write_text(reference_md, encoding="utf-8")
    (out / "positioning-hypotheses.md").write_text(positioning_document(competitive), encoding="utf-8")

    unresolved = [row.get("name") for row in all_rows if row.get("verification_status") not in {"verified", "excluded"}]
    incomplete_inspiration = [record["entity"] for record in similar_records + reference_records if record["synthesis_status"] != "ready"]
    verified_rows = [row for row in all_rows if row.get("verification_status") == "verified"]
    incomplete_social = [
        row.get("name") for row in verified_rows
        if not any(observation.get("status") in {"verified_active", "verified_inactive", "not_found_in_checked_sources"} for observation in row.get("social_presence", []))
    ]
    gate = {
        "ready_for_competitive_conclusions": bool(competitive),
        "ready_for_inspiration_synthesis": not incomplete_inspiration,
        "social_coverage_complete": not incomplete_social,
        "unresolved_entities": unresolved,
        "incomplete_inspiration_entities": incomplete_inspiration,
        "incomplete_social_entities": incomplete_social,
        "coverage_gaps": landscape.get("coverage", {}).get("gaps", []) if isinstance(landscape, dict) else [],
    }
    gate["passed"] = gate["ready_for_competitive_conclusions"] and gate["ready_for_inspiration_synthesis"] and gate["social_coverage_complete"] and not unresolved and not gate["coverage_gaps"]
    write(out / "quality-gate.json", gate)
    write(out / "competitive-insight-handoff.json", {"schema_version": "1.0", "source": "competitive-landscape-builder", "competitive_entities": [row.get("name") for row in competitive], "inspiration_entities": [row.get("name") for row in similar + references], "approved_for_branding": False, "quality_gate_passed": gate["passed"], "note": "Optional input to branding or website work; not a substitute for customer validation."})
    if args.workspace:
        artifact_paths = [
            out / "competitive-market-matrix.md", out / "offer-price-matrix.json", out / "social-presence.json",
            out / "similar-company-inspiration.md", out / "capability-reference-library.md",
            out / "positioning-hypotheses.md", out / "quality-gate.json", out / "competitive-insight-handoff.json",
        ]
        open_gaps = [*gate["coverage_gaps"], *[f"Unresolved entity: {name}" for name in unresolved], *[f"Incomplete inspiration record: {name}" for name in incomplete_inspiration], *[f"Unchecked social coverage: {name}" for name in incomplete_social]]
        update_stage(Path(args.workspace), "competitive_landscape", status="passed" if gate["passed"] else "failed", gate_result="pass" if gate["passed"] else "fail", artifacts=artifact_paths, open_gaps=open_gaps, next_action="Use verified landscape findings in positioning tests." if gate["passed"] else "Resolve quality-gate gaps before competitive or inspiration synthesis.")
    print(json.dumps({"competitive": len(competitive), "similar": len(similar), "references": len(references), "quality_gate_passed": gate["passed"], "out_dir": str(out)}, indent=2))
    return 0 if gate["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
