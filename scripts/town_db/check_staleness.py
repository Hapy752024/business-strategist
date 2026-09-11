#!/usr/bin/env python3
"""Recompute stale flags and report what needs research; verify sessions.

Two modes:
  python3 scripts/town_db/check_staleness.py
      Recompute `stale` on every row (any fact date older than 6 months),
      scan wiki pages for old `last_verified` frontmatter, and print a JSON
      report of exactly which towns/fields need research.

  python3 scripts/town_db/check_staleness.py --verify <session-id>
      Echo every field written under that session id: old value, new value,
      source, and the value currently stored in the DB. The curation skill is
      not "done" until the agent has read this diff and confirmed each line
      matches what the source says — this catches transcription errors.

No network access. JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from db_common import (
    DATA_DIR,
    DB_PATH,
    DATED_FIELDS,
    WIKI_DIR,
    connect,
    is_date_stale,
    now_iso,
    refresh_stale_flags,
)

LAST_VERIFIED_RE = re.compile(r"^last_verified:\s*[\"']?([0-9]{4}-[0-9]{2}-[0-9]{2})[\"']?\s*$")

# date column -> the fact column(s) whose absence means a data gap
GAP_CHECK = {
    "population_checked_date": ["population"],
    "buy_checked_date": ["buy_eur_m2_low", "buy_eur_m2_high"],
    "rent_checked_date": ["rent_1bed_eur"],
    "tax7_checked_date": ["tax7_source_url"],
    "hospital_checked_date": ["hospital_name"],
    "airport_checked_date": ["airport"],
    "expat_checked_date": ["expat_presence"],
}


def wiki_staleness(today: datetime) -> list[dict]:
    pages = []
    if not WIKI_DIR.exists():
        return pages
    for page in sorted(WIKI_DIR.rglob("*.md")):
        last_verified = None
        for line in page.read_text(encoding="utf-8").splitlines()[:20]:
            match = LAST_VERIFIED_RE.match(line)
            if match:
                last_verified = match.group(1)
                break
        pages.append(
            {
                "page": str(page.relative_to(DATA_DIR)),
                "last_verified": last_verified,
                "stale": is_date_stale(last_verified, today),
            }
        )
    return pages


def verify_session(conn, session_id: str) -> dict:
    writes = conn.execute(
        "SELECT * FROM write_log WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()
    if not writes:
        return {"session_id": session_id, "error": "no writes found for this session id"}
    entries = []
    for write in writes:
        current = conn.execute(
            "SELECT * FROM towns WHERE slug = ?", (write["slug"],)
        ).fetchone()
        current_value = None
        if current is not None and write["field"] in current.keys():
            current_value = current[write["field"]]
        matches = (None if current_value is None else str(current_value)) == (
            None if write["new_value"] is None else str(write["new_value"])
        )
        entries.append(
            {
                "slug": write["slug"],
                "field": write["field"],
                "old_value": write["old_value"],
                "new_value": write["new_value"],
                "db_value_now": None if current_value is None else str(current_value),
                "stored_matches_write": matches,
                "source_label": write["source_label"],
                "source_url": write["source_url"],
                "confirm_url": write["confirm_url"],
                "written_at": write["written_at"],
            }
        )
    mismatches = [e for e in entries if not e["stored_matches_write"]]
    return {
        "session_id": session_id,
        "fields_written": len(entries),
        "mismatches": mismatches,
        "entries": entries,
        "instruction": (
            "Read each entry and confirm new_value matches what the cited source "
            "actually says. Any mismatch against the SOURCE (not just the DB) must "
            "be corrected with a fresh upsert before the session is done."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", metavar="SESSION_ID", help="echo-write verification for a session")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    conn = connect(args.db)
    if args.verify:
        print(json.dumps(verify_session(conn, args.verify), indent=2))
        conn.close()
        return 0

    stale_total = refresh_stale_flags(conn)
    rows = conn.execute("SELECT * FROM towns ORDER BY pattern, slug").fetchall()
    today = datetime.now(timezone.utc)
    towns = []
    for row in rows:
        old_fields = [
            {"field": field, "checked_date": row[field]}
            for field in DATED_FIELDS
            if row[field] and is_date_stale(row[field], today)
        ]
        gaps = [
            fact_col
            for date_col, fact_cols in GAP_CHECK.items()
            for fact_col in fact_cols
            if row[fact_col] is None and row[date_col] is None
        ]
        towns.append(
            {
                "slug": row["slug"],
                "pattern": row["pattern"],
                "stale": bool(row["stale"]),
                "stale_fields": old_fields,
                "unverified_gaps": gaps,
                "tax7_status": row["tax7_status"],
                "tax7_confirmed": bool(row["tax7_confirmed"]),
                "buy_confirmed": bool(row["buy_confirmed"]),
            }
        )
    conn.close()

    wiki = wiki_staleness(today)
    print(
        json.dumps(
            {
                "generated_at": now_iso(),
                "stale_threshold_months": 6,
                "towns_total": len(towns),
                "towns_stale": stale_total,
                "towns": towns,
                "wiki_pages": wiki,
                "wiki_pages_stale": sum(1 for p in wiki if p["stale"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
