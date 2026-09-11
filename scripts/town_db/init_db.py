#!/usr/bin/env python3
"""Create towns.sqlite from schema.sql and seed it from seed_towns.json.

Usage:
  python3 scripts/town_db/init_db.py [--force]

Default output: projects/italy-town-db/towns.sqlite
--force drops and recreates the towns + write_log tables (seed reload).
No network access. Prints a JSON summary to stdout; errors to stderr.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from db_common import (
    DATA_DIR,
    DB_PATH,
    SCHEMA_PATH,
    SEED_PATH,
    connect,
    now_iso,
    refresh_stale_flags,
    today_iso,
)

# Maps nested seed JSON fact groups to flat table columns.
def map_town(town: dict) -> dict:
    facts = town.get("facts", {})

    def fact(name: str) -> dict:
        value = facts.get(name)
        return value if isinstance(value, dict) else {}

    pop = fact("population")
    omi = fact("omi_buy")
    rent = fact("rent_1bed_eur")
    tax7 = fact("tax7")
    hospital = fact("hospital")
    airport = fact("airport")
    expat = fact("expat_presence")
    climate = fact("climate_note")
    fit = fact("fit_note")

    return {
        "slug": town["slug"],
        "name": town["name"],
        "province": town["province"],
        "region": town["region"],
        "pattern": town["pattern"],
        "population": pop.get("value"),
        "population_ref_date": pop.get("ref_date"),
        "population_source_label": pop.get("source_label"),
        "population_source_url": pop.get("source_url"),
        "population_checked_date": pop.get("checked_date"),
        "buy_eur_m2_low": omi.get("low"),
        "buy_eur_m2_high": omi.get("high"),
        "buy_semester": omi.get("semester"),
        "buy_source_label": omi.get("source_label"),
        "buy_source_url": omi.get("source_url"),
        "buy_confirm_url": omi.get("confirm_url"),
        "buy_confirmed": 1 if omi.get("confirm_url") else 0,
        "buy_checked_date": omi.get("checked_date"),
        "rent_1bed_eur": rent.get("value"),
        "rent_source_label": rent.get("source_label"),
        "rent_source_url": rent.get("source_url"),
        "rent_checked_date": rent.get("checked_date"),
        "tax7_status": tax7.get("status", "unverified"),
        "tax7_source_label": tax7.get("source_label"),
        "tax7_source_url": tax7.get("source_url"),
        "tax7_confirm_url": tax7.get("confirm_url"),
        "tax7_confirmed": 1 if tax7.get("confirm_url") else 0,
        "tax7_checked_date": tax7.get("checked_date"),
        "hospital_name": hospital.get("name"),
        "hospital_town": hospital.get("town"),
        "hospital_drive_min": hospital.get("drive_min"),
        "hospital_source_label": hospital.get("source_label"),
        "hospital_checked_date": hospital.get("checked_date"),
        "airport": airport.get("name") or airport.get("value"),
        "airport_drive_min": airport.get("drive_min"),
        "airport_source_label": airport.get("source_label"),
        "airport_checked_date": airport.get("checked_date"),
        "expat_presence": expat.get("value"),
        "expat_source_label": expat.get("source_label"),
        "expat_checked_date": expat.get("checked_date"),
        "climate_note": climate.get("value"),
        "fit_note": fit.get("value"),
        "last_verified": today_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="drop and recreate tables before seeding")
    parser.add_argument("--seed", type=Path, default=SEED_PATH, help="seed JSON path")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="output DB path")
    args = parser.parse_args()

    if not args.seed.exists():
        print(f"error: seed file not found: {args.seed}", file=sys.stderr)
        return 1
    towns = json.loads(args.seed.read_text(encoding="utf-8"))
    if not isinstance(towns, list) or not towns:
        print("error: seed file must be a non-empty JSON array", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = connect(args.db)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    if args.force:
        conn.executescript("DROP TABLE IF EXISTS write_log; DROP TABLE IF EXISTS towns;")
    conn.executescript(schema)

    columns = list(map_town(towns[0]).keys())
    placeholders = ", ".join("?" for _ in columns)
    insert = f"INSERT OR REPLACE INTO towns ({', '.join(columns)}) VALUES ({placeholders})"

    inserted, unverified = 0, []
    for town in towns:
        row = map_town(town)
        conn.execute(insert, [row[c] for c in columns])
        inserted += 1
        gaps = [
            field
            for field in ("population", "buy_eur_m2_low", "rent_1bed_eur", "hospital_name", "airport")
            if row[field] is None
        ]
        if row["tax7_status"] == "unverified":
            gaps.append("tax7_status")
        if gaps:
            unverified.append({"slug": row["slug"], "missing": gaps})

    conn.commit()
    stale_count = refresh_stale_flags(conn)
    conn.execute(
        "INSERT INTO write_log (slug, field, old_value, new_value, source_label, source_url, confirm_url, written_at, session_id) "
        "VALUES (?, ?, NULL, ?, ?, ?, NULL, ?, ?)",
        ("*", "init_seed", f"{inserted} rows", str(args.seed), None, now_iso(), f"init-{today_iso()}"),
    )
    conn.commit()
    conn.close()

    print(
        json.dumps(
            {
                "db": str(args.db),
                "rows": inserted,
                "stale_rows": stale_count,
                "towns_with_gaps": unverified,
                "seed": str(args.seed),
                "initialized_at": now_iso(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
