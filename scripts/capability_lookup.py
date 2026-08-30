#!/usr/bin/env python3
"""Token-efficient lookup for business-strategist data/source capabilities."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "config" / "source-capabilities.json"
VALIDATION_PATH = ROOT / "research" / "evidence-scout" / "api-validation" / "all.summary.json"
VALIDATION_DIR = ROOT / "research" / "evidence-scout" / "api-validation"
DOCTOR_PATH = ROOT / "research" / "evidence-scout" / "provider-doctor" / "doctor.summary.json"


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    data = load_json(path, None)
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: missing or invalid capability catalog: {path}")
    return data


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    required = {"id", "family", "label", "use_when", "evidence_strength"}
    for index, item in enumerate(catalog.get("capabilities", [])):
        if not isinstance(item, dict):
            errors.append(f"capabilities[{index}] is not an object")
            continue
        missing = sorted(required - set(item))
        if missing:
            errors.append(f"{item.get('id', f'capabilities[{index}]')} missing {', '.join(missing)}")
        item_id = str(item.get("id", ""))
        if not item_id:
            errors.append(f"capabilities[{index}] missing id")
        elif item_id in seen:
            errors.append(f"duplicate capability id: {item_id}")
        seen.add(item_id)
    return errors


def latest_validation_status() -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {}
    for path in VALIDATION_DIR.glob("*.summary.json"):
        if path.name == "all.summary.json":
            continue
        item = load_json(path, {})
        if isinstance(item, dict) and item.get("provider"):
            statuses[str(item["provider"])] = item
    items = load_json(VALIDATION_PATH, [])
    if not isinstance(items, list):
        return statuses
    statuses.update({str(item.get("provider")): item for item in items if isinstance(item, dict) and item.get("provider")})
    return statuses


def latest_doctor_status() -> dict[str, dict[str, Any]]:
    data = load_json(DOCTOR_PATH, {})
    families = data.get("source_families") if isinstance(data, dict) else None
    return families if isinstance(families, dict) else {}


def words(value: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9_./-]+", value.lower()) if len(part) >= 2}


def searchable_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("id", "family", "label", "description", "collector_provider", "evidence_strength", "caveat"):
        if item.get(key):
            parts.append(str(item[key]))
    for key in ("use_when", "avoid_when", "provider_aliases", "validation_providers", "fallbacks", "requires_env", "requires_cli"):
        value = item.get(key) or []
        if isinstance(value, list):
            parts.extend(str(part) for part in value)
    return " ".join(parts)


def score(item: dict[str, Any], query: str) -> int:
    if not query:
        return 0
    query_lower = query.lower()
    item_text = searchable_text(item).lower()
    result = len(words(query_lower) & words(item_text))
    if str(item.get("id", "")).lower() in query_lower:
        result += 6
    if str(item.get("family", "")).lower() in query_lower:
        result += 4
    for phrase in item.get("use_when", []) or []:
        phrase_text = str(phrase).lower()
        if phrase_text and phrase_text in query_lower:
            result += 3
    return result


def runtime_for(item: dict[str, Any], validation: dict[str, dict[str, Any]]) -> dict[str, Any]:
    providers = item.get("validation_providers") or []
    statuses = []
    for provider in providers:
        latest = validation.get(str(provider))
        if latest:
            statuses.append({"provider": provider, "status": latest.get("status"), "http_status": latest.get("http_status")})
    if not statuses:
        return {"status": "not_checked", "providers": []}
    if any(entry.get("status") == "ok" for entry in statuses):
        aggregate = "ok"
    elif all(entry.get("status") in {"missing_credentials", "missing_cli"} for entry in statuses):
        aggregate = "unavailable"
    elif any(entry.get("status") in {"rate_limited", "billing_required", "insufficient_credits", "permission_denied"} for entry in statuses):
        aggregate = "degraded"
    else:
        aggregate = "failed"
    return {"status": aggregate, "providers": statuses}


def filter_items(catalog: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    items = [item for item in catalog.get("capabilities", []) if isinstance(item, dict)]
    if args.family:
        families = set(args.family)
        items = [item for item in items if item.get("family") in families]
    if args.source:
        sources = set(args.source)
        items = [item for item in items if item.get("id") in sources]
    if args.question:
        scored = [(score(item, args.question), item) for item in items]
        items = [item for item_score, item in scored if item_score > 0]
        items.sort(key=lambda item: score(item, args.question), reverse=True)
    else:
        items.sort(key=lambda item: (str(item.get("family", "")), str(item.get("id", ""))))
    if not args.all:
        items = items[: max(1, args.max)]
    return items


def render_compact(items: list[dict[str, Any]], args: argparse.Namespace, validation: dict[str, dict[str, Any]]) -> str:
    if not items:
        return "No matching capabilities. Broaden --question, --family, or --source.\n"
    lines = [f"Source capabilities: {len(items)} shown", f"Catalog: {CATALOG_PATH.relative_to(ROOT)}"]
    if args.question:
        lines.append(f"Question: {args.question}")
    lines.append("")
    current_family = None
    for item in items:
        family = str(item.get("family", "uncategorized"))
        if family != current_family:
            current_family = family
            lines.append(f"[{family}]")
        runtime = runtime_for(item, validation)
        use_when = "; ".join((item.get("use_when") or [])[:4])
        providers = ", ".join(item.get("provider_aliases") or []) or str(item.get("collector_provider") or "manual")
        checks = ", ".join(f"{entry['provider']}={entry.get('status')}" for entry in runtime["providers"]) or "not checked"
        lines.append(f"- {item['id']}: {item.get('label', '')}")
        lines.append(f"  Use: {use_when}")
        lines.append(f"  Run: providers={providers}; collector={item.get('collector_provider') or 'manual/specialist'}")
        lines.append(f"  Runtime: {runtime['status']} ({checks})")
        if item.get("approval_required"):
            lines.append("  Approval: ask before spending credits or using login/browser-backed access")
        if item.get("fallbacks"):
            lines.append(f"  Fallbacks: {', '.join(item['fallbacks'])}")
        lines.append(f"  Evidence: {item.get('evidence_strength')}")
        if item.get("caveat"):
            lines.append(f"  Caveat: {item['caveat']}")
        if item.get("example"):
            lines.append(f"  Example: {item['example']}")
    lines.append("")
    lines.append("Rule: provider failure is a coverage gap, not evidence of no demand. Record fallback and confidence impact before synthesis.")
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", default=str(CATALOG_PATH))
    p.add_argument("--question", help="Natural-language source need, e.g. 'mobile app reviews' or 'China social evidence'.")
    p.add_argument("--family", action="append", help="Filter by source family. Repeatable.")
    p.add_argument("--source", action="append", help="Filter by capability id. Repeatable.")
    p.add_argument("--max", type=int, default=8)
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--validate", action="store_true", help="Validate catalog shape and exit non-zero on errors.")
    p.add_argument("--list-families", action="store_true")
    p.add_argument("--compact", action="store_true", help="Default output mode; kept for explicit agent calls.")
    return p


def main() -> int:
    args = parser().parse_args()
    catalog = load_catalog(Path(args.catalog))
    errors = validate_catalog(catalog)
    if args.validate:
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("source capability catalog ok")
        return 0
    if errors:
        raise SystemExit("ERROR: invalid capability catalog; run --validate")
    if args.list_families:
        families = sorted({item.get("family", "uncategorized") for item in catalog.get("capabilities", []) if isinstance(item, dict)})
        print("\n".join(families))
        return 0
    validation = latest_validation_status()
    items = filter_items(catalog, args)
    if args.json:
        enriched = [{**item, "runtime": runtime_for(item, validation)} for item in items]
        print(json.dumps({"count": len(enriched), "capabilities": enriched}, indent=2, sort_keys=True))
    else:
        sys.stdout.write(render_compact(items, args, validation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
