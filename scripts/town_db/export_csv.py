#!/usr/bin/env python3
"""Export towns.sqlite to towns.csv (portability / spreadsheet fallback).

Usage:
  python3 scripts/town_db/export_csv.py [--out <path>]

Default output: projects/italy-town-db/towns.csv
Prints a JSON summary to stdout. No network access.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from db_common import CSV_PATH, DB_PATH, connect, now_iso


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=CSV_PATH)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    conn = connect(args.db)
    rows = conn.execute("SELECT * FROM towns ORDER BY pattern, slug").fetchall()
    conn.close()
    if not rows:
        print("error: towns table is empty — run init_db.py first", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    columns = rows[0].keys()
    tmp = args.out.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    tmp.replace(args.out)

    print(
        json.dumps(
            {"csv": str(args.out), "rows": len(rows), "columns": len(list(columns)), "exported_at": now_iso()},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
