#!/usr/bin/env python3
"""Deterministically select the narrowest specialist workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "config" / "workflow-routes.json"


def load_routes() -> list[dict[str, Any]]:
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))["routes"]


def route_request(request: str, *, active_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    text = request.casefold()
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for index, route in enumerate(load_routes()):
        hits = [phrase for phrase in route.get("match", []) if phrase.casefold() in text]
        if hits:
            # Longer phrases are more specific; index is a stable tie-breaker.
            candidates.append((max(map(len, hits)), len(hits), {**route, "matched": hits, "order": index}))
    if candidates:
        _, _, selected = max(candidates, key=lambda item: (item[0], item[1], -item[2]["order"]))
        reason = "explicit phrase match"
    else:
        selected = {
            "id": "clarify",
            "skill": "business-strategist",
            "forbidden": [],
            "matched": [],
            "order": -1,
        }
        reason = "no route phrase matched"
    if active_manifest:
        active = active_manifest.get("active_track")
        if active == "website" and selected["skill"] == "brand-designer":
            selected["skill"] = "brand-website-designer-builder"
            reason += "; active website track"
        elif active == "brand" and selected["skill"] == "business-strategist":
            selected["skill"] = "brand-designer"
            reason += "; active brand track"
    return {
        "route_id": selected["id"],
        "skill": selected["skill"],
        "mode": selected.get("mode", "default"),
        "matched": selected.get("matched", []),
        "forbidden_skills": selected.get("forbidden", []),
        "ask_question": selected["skill"] == "business-strategist",
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    manifest = None
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(route_request(args.request, active_manifest=manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
