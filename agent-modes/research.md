# Research Mode

Evidence collection, competitor discovery, and marketing analysis workflows.

## Allowed Tools

- Scripts: `scripts/evidence_scout/*`, `scripts/validate_apis/*`
- MCP: brave-search, firecrawl
- Bash: git, python3, ls, find, cat, head, mkdir, curl

## Required Output Checks

- Always search before answering: run at least one retrieval (Serper, Reddit, YouTube, podcast, trends, or social provider) before any market, audience, competitor, or channel claim; end research answers with a dated source list.
- Every evidence run writes: `evidence.jsonl`, `summary.json`, `report.md`
- Every market-discovery run writes: `research_plan.md`, `market-discovery-report.md`, and a sourced `evidence/` subdirectory before it can be closed.
- Every competitor run writes: `competitors.json` with classification
- Every marketing run writes: structured analysis with source URLs
- Provider failures are recorded, not silently skipped

## Stop Conditions

- Do not proceed to collection if API validation (Phase 1) failed for all providers.
- Do not claim strong evidence from weak signals (trends-only, likes-only).
- Do not call a pocket underserved solely because it has complaints or attention; require evidence of a recurring job, workaround or cost, and a meaningful gap in current alternatives.
- If `summary.json.needs_user_attention` is true, surface it before interpreting.
- Do not fabricate evidence from memory — mark gaps as `[DATA UNAVAILABLE]`.

## Forbidden

- Interpreting trend data or engagement as proof of willingness to pay.
- Reporting competitor copy (landing pages) as proof of performance.
- Claiming provider data was fetched when the provider returned an error.
