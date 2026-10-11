# Optional source worker packet

Use this only when the coordinator explicitly chooses parallel source collection. Module entry never launches a worker or model automatically.

Each worker receives one packet containing:

- **Question and scope:** the exact customer problem or segment question, geography, time window, and exclusions. Foreign companies may be comparables; they do not replace validation of the user's target customer and idea.
- **Relevant evidence:** immutable source IDs, exact spans, dates, source roles, current limitations, and the known competing interpretations. Do not send unsupported synthesis as fact.
- **Allowed retrieval:** named public sources/providers and permitted query budget. No credentials, private-community access, or unapproved spend is implied by the packet.
- **Allocation:** exclusive query IDs, entities, or source families so workers do not duplicate samples or contaminate independent evidence counts.
- **Output boundary:** a new exclusive output directory. Workers return raw/normalized evidence and a short handoff; they do not edit shared synthesis, findings, claims, gates, or module manifests.
- **Required handoff:** retrieval attempts and failures, exact source locators/spans, source/customer/supplier role, deduplication notes, counterevidence, unresolved questions, and coverage limits.

The coordinator verifies sources, independence, dates, scope and claim links, then owns the shared synthesis. A failed or unavailable retrieval is a coverage gap, not evidence that customers lack the problem.

## Bounded corrections and resume

When worker work is split, keep a coordinator-owned run-local ledger using `schemas/source-work-packet.schema.json`. Bind exact input/output bytes and known check-result artifacts; checks contain evidence, never executable commands. Use exclusive output paths and dependencies naming consumed outputs. See `fixtures/research/work-packets/ledger.json` for a synthetic four-unit example.

Run `python3 scripts/evidence_scout/work_packets.py <ledger.json> --base <run-root> --previous <prior-ledger.json>` before resume. A valid incomplete ledger exits 1 and lists eligible units. Return only the rejected unit with the failed requirement, bound evidence, allowed outputs and next action. Preserve unaffected accepted units and attempt history; compare with the previous ledger. Changed bindings invalidate acceptance and consumers. Retry exhaustion requires revising the plan, not weakening checks. The coordinator reviews stale work before resetting it to pending. No helper dispatch, stage promotion or semantic-review certification is implied. Record recurring failures in the shared workflow log.
