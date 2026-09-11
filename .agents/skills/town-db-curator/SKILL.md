---
name: town-db-curator
description: Curate the internal Italy town key-data store — research stale or missing town facts, write them with dated sources, verify the writes, and regenerate exports/reports. Use for any update, refresh, or shortlist-preparation work on projects/italy-town-db/.
---

# Town DB Curator

`projects/italy-town-db/` is local-only; clients only ever see generated
reports from `reports/`, never the DB or the wiki.

## Non-negotiable rules

1. **Unverified beats invented** — never guess; leave fields empty/unverified.
2. **Dated source on every fact** — `upsert_town.py` refuses unsourced writes.
3. **Key fields (`buy`/`tax7`) need `--confirm-url`** — else unconfirmed.
4. **7% regime: official list only** — never blogs or agency pages.
5. **Division of truth** — figures live in DB rows only; wiki never restates them.
6. **Brand voice** — `fit_note`: who it suits + one watch-out; no "dream".

## Procedure

Follow `references/workflow.md`: staleness report → research flagged fields
only (approved sources in `references/sources.md`) → upsert with sources →
`check_staleness.py --verify <session-id>`, confirming each value against its
cited source → export CSV → regenerate affected reports.

## Output

Fields written / left unverified (why) / still unconfirmed / verification-diff
result / next re-check date.
