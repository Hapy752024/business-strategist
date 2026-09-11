#!/usr/bin/env python3
"""Generate a client shortlist report for 2–3 towns.

Usage:
  python3 scripts/town_db/build_shortlist.py --towns sulmona,lecce,ortigia-syracuse \
      --client "J. Smith" [--out <path>]

Default output: projects/italy-town-db/reports/<date>-<client-slug>.md

Division of truth, enforced at generation time: every figure comes from the
DB row (with its source + checked date); narrative comes only from
wiki/towns/<slug>.md. Missing data renders as "not verified"; single-sourced
key fields render with an "unconfirmed" marker — never as blanks or guesses.
Consultant reviews/edits the file before sending. No network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from db_common import DB_PATH, REPORTS_DIR, WIKI_DIR, connect, now_iso, today_iso

DISCLAIMER = (
    "This shortlist is orientation, not legal, tax, financial, or immigration advice. "
    "Figures are dated snapshots from the cited sources; verify anything you will act on."
)

NOT_VERIFIED = "not verified"
UNCONFIRMED_MARK = " *(unconfirmed — single source, check before quoting)*"


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in safe.split("-") if part)[:60] or "client"


def wiki_body(slug: str) -> str | None:
    page = WIKI_DIR / "towns" / f"{slug}.md"
    if not page.exists():
        return None
    text = page.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                text = "\n".join(lines[index + 1 :]).strip()
                break
    # Drop the page's own H1 — the report already prints a town heading.
    body_lines = text.splitlines()
    if body_lines and body_lines[0].startswith("# "):
        body_lines = body_lines[1:]
    return "\n".join(body_lines).strip() or None


def money(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return NOT_VERIFIED
    return f"€{value:,.0f}{suffix}".replace(",", " ")


def dated(label: str | None, url: str | None, checked: str | None) -> str:
    if not label and not url:
        return ""
    parts = []
    if label:
        parts.append(label + (f" ({url})" if url else ""))
    elif url:
        parts.append(url)
    if checked:
        parts.append(f"checked {checked}")
    return " — " + "; ".join(parts)


def render_town(row: dict) -> tuple[str, list[str]]:
    """Render one town section. Returns (markdown, warnings)."""
    warnings: list[str] = []
    lines = [f"## {row['name']} ({row['region']})"]

    body = wiki_body(row["slug"])
    if body:
        lines.append(body)
    else:
        lines.append("> **Wiki profile missing — write `wiki/towns/" + row["slug"] + ".md` before sending.**")
        warnings.append(f"{row['slug']}: wiki profile missing")

    lines.append("")
    lines.append("**The numbers** *(each with its source and checked date)*")
    lines.append("")

    # population
    if row["population"] is None:
        lines.append(f"- Population: {NOT_VERIFIED}")
    else:
        lines.append(
            f"- Population: {row['population']:,}".replace(",", " ")
            + (f" ({row['population_ref_date']})" if row["population_ref_date"] else "")
            + dated(row["population_source_label"], row["population_source_url"], row["population_checked_date"])
        )

    # buy (key field)
    if row["buy_eur_m2_low"] is None:
        lines.append(f"- Buy: {NOT_VERIFIED}")
    else:
        mark = "" if row["buy_confirmed"] else UNCONFIRMED_MARK
        if not row["buy_confirmed"]:
            warnings.append(f"{row['slug']}: buy price unconfirmed (single source)")
        lines.append(
            f"- Buy: {money(row['buy_eur_m2_low'])}–{money(row['buy_eur_m2_high'])} /m²"
            + (f" ({row['buy_semester']})" if row["buy_semester"] else "")
            + mark
            + dated(row["buy_source_label"], row["buy_source_url"], row["buy_checked_date"])
        )

    # rent
    if row["rent_1bed_eur"] is None:
        lines.append(f"- Rent (1-bed): {NOT_VERIFIED}")
    else:
        lines.append(
            f"- Rent (1-bed): {money(row['rent_1bed_eur'])} /month"
            + dated(row["rent_source_label"], row["rent_source_url"], row["rent_checked_date"])
        )

    # tax7 (key field)
    tax7_labels = {
        "eligible": "Eligible for the 7% flat-tax regime",
        "not_eligible": "Not eligible for the 7% flat-tax regime",
        "unverified": "7% regime status: not verified",
    }
    tax7_line = tax7_labels[row["tax7_status"]]
    if row["tax7_status"] != "unverified":
        mark = "" if row["tax7_confirmed"] else UNCONFIRMED_MARK
        if not row["tax7_confirmed"]:
            warnings.append(f"{row['slug']}: tax7 status unconfirmed (single source)")
        tax7_line += mark + dated(row["tax7_source_label"], row["tax7_source_url"], row["tax7_checked_date"])
    lines.append(f"- {tax7_line}")

    # hospital
    if row["hospital_name"] is None:
        lines.append(f"- Hospital: {NOT_VERIFIED}")
    else:
        drive = f", ~{row['hospital_drive_min']} min drive" if row["hospital_drive_min"] else ""
        town = f" ({row['hospital_town']})" if row["hospital_town"] else ""
        lines.append(
            f"- Hospital: {row['hospital_name']}{town}{drive}"
            + dated(row["hospital_source_label"], None, row["hospital_checked_date"])
        )

    # airport
    if row["airport"] is None:
        lines.append(f"- Airport: {NOT_VERIFIED}")
    else:
        drive = f", ~{row['airport_drive_min']} min drive" if row["airport_drive_min"] else ""
        lines.append(
            f"- Airport: {row['airport']}{drive}"
            + dated(row["airport_source_label"], None, row["airport_checked_date"])
        )

    if row["expat_presence"]:
        lines.append(f"- International resident presence: {row['expat_presence']}")
    if row["climate_note"]:
        lines.append(f"- Climate: {row['climate_note']}")
    if row["fit_note"]:
        lines.append("")
        lines.append(f"**Who it fits.** {row['fit_note']}")
    lines.append("")
    return "\n".join(lines), warnings


def render_table(rows: list[dict]) -> str:
    def tax7(row: dict) -> str:
        label = {"eligible": "yes", "not_eligible": "no", "unverified": "not verified"}[row["tax7_status"]]
        return label if row["tax7_confirmed"] else label + " (unconfirmed)"

    def buy(row: dict) -> str:
        if row["buy_eur_m2_low"] is None:
            return NOT_VERIFIED
        mark = "" if row["buy_confirmed"] else " (unconfirmed)"
        return f"€{row['buy_eur_m2_low']:,.0f}–{row['buy_eur_m2_high']:,.0f}".replace(",", " ") + mark

    lines = [
        "| | " + " | ".join(row["name"] for row in rows) + " |",
        "|---|" + "---|" * len(rows),
        "| Buy €/m² | " + " | ".join(buy(row) for row in rows) + " |",
        "| Rent 1-bed €/mo | " + " | ".join(money(row["rent_1bed_eur"]) for row in rows) + " |",
        "| 7% regime | " + " | ".join(tax7(row) for row in rows) + " |",
        "| Hospital drive | "
        + " | ".join(f"~{row['hospital_drive_min']} min" if row["hospital_drive_min"] else NOT_VERIFIED for row in rows)
        + " |",
        "| Airport drive | "
        + " | ".join(f"~{row['airport_drive_min']} min" if row["airport_drive_min"] else NOT_VERIFIED for row in rows)
        + " |",
        "| Expat presence | " + " | ".join(row["expat_presence"] or NOT_VERIFIED for row in rows) + " |",
        "| Population | "
        + " | ".join(f"{row['population']:,}".replace(",", " ") if row["population"] else NOT_VERIFIED for row in rows)
        + " |",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--towns", required=True, help="comma-separated town slugs (2–3)")
    parser.add_argument("--client", required=True, help="client name or initials")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    slugs = [slug.strip() for slug in args.towns.split(",") if slug.strip()]
    if not 2 <= len(slugs) <= 3:
        print("error: a shortlist is 2–3 towns", file=sys.stderr)
        return 1

    conn = connect(args.db)
    rows = []
    for slug in slugs:
        row = conn.execute("SELECT * FROM towns WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            print(f"error: unknown town slug '{slug}'", file=sys.stderr)
            return 1
        rows.append(dict(row))
    conn.close()

    warnings: list[str] = []
    sections = []
    for row in rows:
        section, town_warnings = render_town(row)
        sections.append(section)
        warnings.extend(town_warnings)

    report = [
        f"# Italy shortlist for {args.client}",
        "",
        f"Prepared {today_iso()} — Italy for Retirees. {DISCLAIMER}",
        "",
        "---",
        "",
        *sections,
        "## Side by side",
        "",
        render_table(rows),
        "",
        "---",
        "",
        "## Pre-send verification checklist",
        "",
        "- [ ] Every figure above shows a source and a checked date within the last 6 months",
        "- [ ] No figure marked *unconfirmed* is quoted to the client without a second-source check",
        "- [ ] No \"not verified\" cell is presented as settled fact",
        "- [ ] Wiki narrative matches the DB row (no restated figures)",
        "- [ ] Disclaimer line is present",
        "",
        f"*Generated {now_iso()} by scripts/town_db/build_shortlist.py*",
        "",
    ]

    out = args.out or REPORTS_DIR / f"{today_iso()}-{slugify(args.client)}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report), encoding="utf-8")

    print(json.dumps({"report": str(out), "towns": slugs, "warnings": warnings}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
