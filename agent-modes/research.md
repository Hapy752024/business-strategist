# Research Mode

Evidence collection, competitor discovery, and marketing analysis workflows.

## Allowed Tools

- Scripts: `scripts/evidence_scout/*`, `scripts/validate_apis/*`
- MCP: brave-search, firecrawl
- Bash: git, python3, ls, find, cat, head, mkdir, curl

## Required Output Checks

- Every evidence run writes: `evidence.jsonl`, `summary.json`, `report.md`
- Every competitor run writes: `competitors.json` with classification
- Every marketing run writes: structured analysis with source URLs
- Provider failures are recorded, not silently skipped

## Stop Conditions

- Do not proceed to collection if API validation (Phase 1) failed for all providers.
- Do not claim strong evidence from weak signals (trends-only, likes-only).
- If `summary.json.needs_user_attention` is true, surface it before interpreting.
- Do not fabricate evidence from memory — mark gaps as `[DATA UNAVAILABLE]`.

## Forbidden

- Interpreting trend data or engagement as proof of willingness to pay.
- Reporting competitor copy (landing pages) as proof of performance.
- Claiming provider data was fetched when the provider returned an error.
