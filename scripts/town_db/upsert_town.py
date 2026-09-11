#!/usr/bin/env python3
"""Surgical, source-required updates to a single town row.

This is the agent's ONLY write path into towns.sqlite. Rules enforced here:
- Fact writes require --source-label AND --source-url. Refused otherwise.
- Key fields (buy, tax7) also need --confirm-url (second independent source)
  to be marked confirmed; without it the write lands as UNCONFIRMED and
  reports will render it as "not verified — check before quoting".
- Every write is appended to write_log with old/new values and a session id.

Usage:
  python3 scripts/town_db/upsert_town.py --slug sulmona --field tax7 \
      --value eligible --source-label "Agenzia delle Entrate 7% comuni list" \
      --source-url https://... --confirm-url https://...

  python3 scripts/town_db/upsert_town.py --slug sulmona --field buy \
      --low 700 --high 1100 --semester "2025-S2" --source-label "OMI" \
      --source-url https://...

  python3 scripts/town_db/upsert_town.py --slug sulmona --field fit_note \
      --value "Honest one-liner…"

Prints a JSON result to stdout; errors to stderr, exit 1 on refusal.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from db_common import DB_PATH, connect, now_iso, refresh_stale_flags, today_iso

# field group -> (required value args, column mapping builder)
FACT_GROUPS = {
    "population": {
        "args": ["value"],
        "refuse_without_source": True,
        "columns": lambda a: {
            "population": int(a.value),
            "population_ref_date": a.ref_date,
            "population_source_label": a.source_label,
            "population_source_url": a.source_url,
            "population_checked_date": a.checked_date,
        },
    },
    "buy": {
        "args": ["low", "high"],
        "refuse_without_source": True,
        "key": True,
        "columns": lambda a: {
            "buy_eur_m2_low": float(a.low),
            "buy_eur_m2_high": float(a.high),
            "buy_semester": a.semester,
            "buy_source_label": a.source_label,
            "buy_source_url": a.source_url,
            "buy_confirm_url": a.confirm_url,
            "buy_confirmed": 1 if a.confirm_url else 0,
            "buy_checked_date": a.checked_date,
        },
    },
    "rent": {
        "args": ["value"],
        "refuse_without_source": True,
        "columns": lambda a: {
            "rent_1bed_eur": float(a.value),
            "rent_source_label": a.source_label,
            "rent_source_url": a.source_url,
            "rent_checked_date": a.checked_date,
        },
    },
    "tax7": {
        "args": ["value"],
        "refuse_without_source": True,
        "key": True,
        "columns": lambda a: {
            "tax7_status": a.value,
            "tax7_source_label": a.source_label,
            "tax7_source_url": a.source_url,
            "tax7_confirm_url": a.confirm_url,
            "tax7_confirmed": 1 if a.confirm_url else 0,
            "tax7_checked_date": a.checked_date,
        },
    },
    "hospital": {
        "args": ["name"],
        "refuse_without_source": True,
        "columns": lambda a: {
            "hospital_name": a.name,
            "hospital_town": a.town,
            "hospital_drive_min": int(a.drive_min) if a.drive_min is not None else None,
            "hospital_source_label": a.source_label,
            "hospital_checked_date": a.checked_date,
        },
    },
    "airport": {
        "args": ["name"],
        "refuse_without_source": True,
        "columns": lambda a: {
            "airport": a.name,
            "airport_drive_min": int(a.drive_min) if a.drive_min is not None else None,
            "airport_source_label": a.source_label,
            "airport_checked_date": a.checked_date,
        },
    },
    "expat": {
        "args": ["value"],
        "refuse_without_source": True,
        "columns": lambda a: {
            "expat_presence": a.value,
            "expat_source_label": a.source_label,
            "expat_checked_date": a.checked_date,
        },
    },
    # Judgment fields: no source required, still dated and logged.
    "climate_note": {
        "args": ["value"],
        "refuse_without_source": False,
        "columns": lambda a: {"climate_note": a.value},
    },
    "fit_note": {
        "args": ["value"],
        "refuse_without_source": False,
        "columns": lambda a: {"fit_note": a.value},
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--field", required=True, choices=sorted(FACT_GROUPS))
    parser.add_argument("--value", help="scalar value (population, rent, tax7, expat, notes)")
    parser.add_argument("--low", type=float, help="buy €/m² low bound")
    parser.add_argument("--high", type=float, help="buy €/m² high bound")
    parser.add_argument("--semester", help="reference period, e.g. 2025-S2")
    parser.add_argument("--ref-date", help="reference date for population figures")
    parser.add_argument("--name", help="hospital/airport name")
    parser.add_argument("--town", help="hospital town")
    parser.add_argument("--drive-min", help="drive minutes")
    parser.add_argument("--source-label")
    parser.add_argument("--source-url")
    parser.add_argument("--confirm-url", help="second independent source (key fields)")
    parser.add_argument("--checked-date", default=None, help="defaults to today (UTC)")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--db", default=str(DB_PATH))
    args = parser.parse_args()

    group = FACT_GROUPS[args.field]
    args.checked_date = args.checked_date or today_iso()
    session_id = args.session_id or f"session-{uuid.uuid4().hex[:8]}"

    for required in group["args"]:
        if getattr(args, required) is None:
            print(f"error: --field {args.field} requires --{required}", file=sys.stderr)
            return 1
    if args.field == "tax7" and args.value not in ("eligible", "not_eligible", "unverified"):
        print("error: tax7 value must be eligible|not_eligible|unverified", file=sys.stderr)
        return 1
    if args.field == "expat" and args.value not in ("low", "medium", "high"):
        print("error: expat value must be low|medium|high", file=sys.stderr)
        return 1
    if group["refuse_without_source"] and not (args.source_label and args.source_url):
        print(
            f"error: fact write '{args.field}' refused — pass --source-label and --source-url. "
            "Unverified beats invented: leave the field empty instead.",
            file=sys.stderr,
        )
        return 1

    conn = connect(Path(args.db))
    row = conn.execute("SELECT * FROM towns WHERE slug = ?", (args.slug,)).fetchone()
    if row is None:
        print(f"error: unknown town slug '{args.slug}'", file=sys.stderr)
        return 1

    new_columns = group["columns"](args)
    old = {col: row[col] for col in new_columns}
    assignments = ", ".join(f"{col} = ?" for col in new_columns)
    conn.execute(
        f"UPDATE towns SET {assignments}, last_verified = ? WHERE slug = ?",
        [*new_columns.values(), today_iso(), args.slug],
    )
    for col, new_value in new_columns.items():
        conn.execute(
            "INSERT INTO write_log (slug, field, old_value, new_value, source_label, source_url, confirm_url, written_at, session_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                args.slug,
                col,
                None if old[col] is None else str(old[col]),
                None if new_value is None else str(new_value),
                args.source_label,
                args.source_url,
                args.confirm_url,
                now_iso(),
                session_id,
            ),
        )
    conn.commit()
    stale = refresh_stale_flags(conn)
    conn.close()

    unconfirmed = bool(group.get("key")) and not args.confirm_url
    print(
        json.dumps(
            {
                "slug": args.slug,
                "field": args.field,
                "written": {k: v for k, v in new_columns.items()},
                "confirmed": not unconfirmed,
                "note": (
                    "KEY FIELD single-sourced → UNCONFIRMED. Reports render it as "
                    "'not verified — check before quoting' until you re-write with --confirm-url."
                    if unconfirmed
                    else "ok"
                ),
                "session_id": session_id,
                "stale_rows_total": stale,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
