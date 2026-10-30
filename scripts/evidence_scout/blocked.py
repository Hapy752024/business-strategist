"""Read a capability's blocked-by-provider marker from config/source-capabilities.json."""

from __future__ import annotations

import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[2] / "config" / "source-capabilities.json"
BLOCKED = "blocked_by_provider"


def blocked_reason(capability_id: str, catalog: Path = CATALOG) -> str | None:
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for item in data.get("capabilities", []):
        if item.get("id") == capability_id and item.get("status") == BLOCKED:
            return str(item.get("status_reason") or "blocked by provider")
    return None
