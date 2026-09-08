"""Shared timestamp selection for cached provider checks; never infer live success."""
import json
from datetime import datetime, timezone
from pathlib import Path


def load_latest(directory: Path, ttl_hours: float = 24) -> dict:
    selected = {}
    dates = {}
    now = datetime.now(timezone.utc)
    for path in sorted(directory.glob("*.summary.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in data if isinstance(data, list) else [data]:
            if not isinstance(item, dict) or not item.get("provider"):
                continue
            try:
                timestamp = datetime.fromisoformat(item["validated_at"].replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    raise ValueError("timestamp needs timezone")
            except (KeyError, ValueError, TypeError):
                timestamp = datetime.min.replace(tzinfo=timezone.utc)
            provider = item["provider"]
            if provider in dates and dates[provider] >= timestamp:
                continue
            dates[provider] = timestamp
            result = dict(item)
            age = (now - timestamp).total_seconds() / 3600
            if age < 0 or age > ttl_hours:
                result.update(status="stale", observed_status=item.get("status"))
            selected[provider] = result
    return selected
