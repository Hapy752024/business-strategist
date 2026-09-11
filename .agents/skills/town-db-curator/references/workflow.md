# Curation workflow

## 1. See what needs work

```bash
python3 scripts/town_db/check_staleness.py
```

Read the JSON report: `towns[].stale_fields` (facts older than 6 months),
`towns[].unverified_gaps` (never researched), unconfirmed key fields
(`tax7_confirmed` / `buy_confirmed` false), and stale wiki pages. Work only
what the report flags plus whatever the user asked for — do not re-research
fresh fields.

Pick a session id for the batch, e.g. `session-2026-09-09-orvieto`.

## 2. Research (bounded)

For each flagged field, use the approved sources in `references/sources.md`.
Record, per fact: value, source label, source URL, the date you checked it,
and for key fields a second independent source URL. Stop when the approved
sources are exhausted — an unresearched field stays unverified, and that is
a correct outcome.

## 3. Write via upsert (one field at a time)

```bash
python3 scripts/town_db/upsert_town.py --slug <slug> --field <field> \
    [--value ... | --low ... --high ... | --name ... --drive-min ...] \
    --source-label "<label>" --source-url <url> \
    [--confirm-url <url>] --session-id <session-id>
```

Notes:
- The script refuses fact writes without source args. Do not try to work
  around this — the refusal is the guardrail.
- Key fields (`buy`, `tax7`) without `--confirm-url` are written but marked
  unconfirmed; say so in your summary.
- `tax7` values: `eligible | not_eligible | unverified`.
- Judgment fields (`fit_note`, `climate_note`) take `--value` only.

New town: add its entry to `scripts/town_db/seed_towns.json` (same nested
shape, facts with sources) and re-run `init_db.py` **without `--force`**
(INSERT OR REPLACE preserves existing rows), or upsert every field manually.
Then write `wiki/towns/<slug>.md` (narrative only — no figures).

## 4. Verify (mandatory)

```bash
python3 scripts/town_db/check_staleness.py --verify <session-id>
```

Read every entry. For each one, re-open the cited source and confirm the
`new_value` is what the source actually says (transcription check — not just
that the DB stored it). Fix any mismatch with a fresh upsert under a new
session id and verify that too. The batch is not done until this diff is
clean.

## 5. Export + reports

```bash
python3 scripts/town_db/export_csv.py
python3 scripts/town_db/build_shortlist.py --towns a,b,c --client "<name>"   # if a report is affected
```

Regenerate any report in `reports/` that quotes a town you changed, and say
which reports are now stale in your summary.

## 6. Summarize

Fields written / left unverified (why) / still unconfirmed / verification
result / next re-check date. Plain and short.
