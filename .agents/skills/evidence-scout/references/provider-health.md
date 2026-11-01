# Provider-health mode (route `provider-health`)

Answers "which research data sources work, and what does the founder need to fund or fix?"
It starts no workspace and no research run.

## Run

```bash
python3 scripts/provider_health.py            # live: runs every validator, refreshes the cache
python3 scripts/provider_health.py --cached   # latest saved results; rows older than 24h say "as of <date>"
python3 scripts/provider_health.py --provider dataforseo --provider serper   # selected providers only
```

Add `--json` for rows, or `--out <path>` to save the Markdown report.
Exit 1 means at least one source needs the founder.
A live run calls each provider's cheapest check endpoint; that is pre-authorized research spend.

## Report

Lead with the "What to do" table as the script prints it:

- source and status;
- the founder's step: top up (with the funding page), add or replace a named key in `~/.secrets` (with the page that issues it), or verify the account;
- the research capabilities it blocks.

Then list reported balances and the ready sources.
Optional local extractors (`missing_cli`) are not blockers.

## Rules

- Name keys, never print or read their values; `~/.secrets` and `.env` stay the founder's to edit.
- Funding an account, buying a plan and creating keys are the founder's steps; give the link and stop.
- A failing source is a coverage gap, not evidence about the market.
- When a needed source is down, name the fallback from `config/source-capabilities.json` (`fallbacks`) rather than skipping the research.
- Billing pages live in `config/provider-billing.json`; when a provider's page moves, update that file, not this reference.
