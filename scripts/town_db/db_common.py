"""Shared helpers for the town key-data store scripts.

Conventions: stdlib-only, ROOT-anchored paths, atomic JSON writes,
UTC ISO provenance. Data lives at projects/us-retirees-italy/digital-assets/town-db/
(local only, gitignored — never published, never read by the website).
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "projects" / "us-retirees-italy" / "digital-assets" / "town-db"
DB_PATH = DATA_DIR / "towns.sqlite"
CSV_PATH = DATA_DIR / "towns.csv"
WIKI_DIR = DATA_DIR / "wiki"
REPORTS_DIR = DATA_DIR / "reports"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
SEED_PATH = Path(__file__).resolve().parent / "seed_towns.json"

STALE_AFTER_MONTHS = 6

# Fact groups: (prefix, date column). A town is stale when any recorded
# fact date (or last_verified) is older than STALE_AFTER_MONTHS.
DATED_FIELDS = [
    "population_checked_date",
    "buy_checked_date",
    "rent_checked_date",
    "tax7_checked_date",
    "hospital_checked_date",
    "airport_checked_date",
    "expat_checked_date",
]

# Key fields require a second independent source (--confirm-url) to be
# treated as confirmed; single-sourced key facts render as "unconfirmed".
KEY_FIELDS = {"buy", "tax7"}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_json(path: Path, payload: Any) -> None:
    """Atomic JSON write (tmp file + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def is_date_stale(value: str | None, today: datetime | None = None) -> bool:
    """True when a checked_date is older than STALE_AFTER_MONTHS (or missing)."""
    parsed = _parse_date(value)
    if parsed is None:
        return True
    today = today or datetime.now(timezone.utc)
    age_days = (today - parsed).days
    return age_days > STALE_AFTER_MONTHS * 31


def compute_stale(row: sqlite3.Row | dict[str, Any]) -> bool:
    """A town is stale if any recorded fact date is older than the threshold.

    Missing dates do not make a town stale on their own (an unverified
    field is a data gap, not staleness); last_verified is the floor.
    """
    dates = [row.get(field) if isinstance(row, dict) else row[field] for field in DATED_FIELDS]
    dates.append(row.get("last_verified") if isinstance(row, dict) else row["last_verified"])
    recorded = [d for d in dates if d]
    if not recorded:
        return True
    return any(is_date_stale(d) for d in recorded)


def refresh_stale_flags(conn: sqlite3.Connection) -> int:
    """Recompute the stale flag for every row. Returns count of stale rows."""
    rows = conn.execute("SELECT * FROM towns").fetchall()
    stale_count = 0
    for row in rows:
        stale = 1 if compute_stale(dict(row)) else 0
        stale_count += stale
        conn.execute("UPDATE towns SET stale = ? WHERE slug = ?", (stale, row["slug"]))
    conn.commit()
    return stale_count


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None
