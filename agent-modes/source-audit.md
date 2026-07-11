# Source Audit Mode

Verify that every material claim is traceable to a source with date, vendor, and retrieval context.

## Allowed Tools

- Bash: grep, find, cat, head, jq
- MCP: filesystem (read-only)
- Scripts: none (audit is read-only verification)

## Required Checks

- Every factual claim in a report has a matching row in `evidence.jsonl` or source registry.
- Source records include: url, retrieval date, vendor, and caveats.
- Hypotheses are tagged as hypotheses, not stated as facts.
- Provider failures are recorded with failure class and confidence impact.

## Stop Conditions

- Do not publish synthesis if any thesis-critical claim lacks a source.
- Do not proceed past a gate if source audit returns `failed`.
- Flag any claim sourced only from model memory as `unsupported`.

## Forbidden

- Accepting "data not found" when the API actually returned an error.
- Treating stale sources (past material change) as current.
- Omitting source dates or vendor names.
