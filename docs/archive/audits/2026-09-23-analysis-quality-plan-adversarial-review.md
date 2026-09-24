# Independent plan review — 23 September 2026

## Score: 75/100 — FLAG

The plan addresses the defects and distinguishes validation from semantic improvement. No demonstrated BLOCK; resolve the first two flags before P4. References are repository-relative.

## Prioritized flags

1. **High — verification can omit the findings being approved.** Plan P3–P4, lines 109–124, requires verification objects but no exhaustive U/R-to-claim association. `scripts/evidence_scout/validate_customer_voc_synthesis.py:182–197` validates mappings separately; `scripts/evidence_scout/validate_synthesis.py:36–39` accepts an empty ledger (confirmed offline). Calling both validators can therefore leave material findings unverified. Require every material finding and rendered claim to resolve to a current verification record; test a valid synthesis with an empty/unrelated claim ledger, while permitting genuine zero-finding conclusions.

2. **High — scoped completion and overrides lack a consumer decision table.** Plan P4, lines 123–125, and compatibility line 190 promise scoped passes and preserved overrides while requiring current receipts. `scripts/route_workflow.py:97–132` exposes a Boolean pain gate; `scripts/evidence_scout/workspace.py:410–420` stores override reasons in events, outside checkpoints. A narrow finding could unlock a broader commitment, or receipt enforcement could reject an authorized exception. Specify persisted decision scope and completion basis, exact commitment applicability checks, and revision-bound override consumption. Test narrow-to-broad reuse and valid/stale overrides through routing and publication.

3. **Medium — resume does not specify restoring consumed allowances.** Plan P1, lines 82–87, binds settings and captures. However, `scripts/validate_apis/common.py:145–153` resets request counters, and `scripts/evidence_scout/collect.py:1557` resets transcript allowance. Restarts can exceed run limits despite identical settings. Persist consumed/reserved operations and enrichment allowances; test interrupted versus uninterrupted exhaustion, including uncertain operations.

4. **Medium — held-out independence is underspecified.** Plan P0/P7, lines 66–73 and 174, splits tasks and predeclares improvement only before scoring. Existing `evals/voc/live/cases.json:23–32` contains related episodes from shared studies/sources. Split by study/source/incident cluster; freeze improvement rules in P0 before tuning. Test leakage and preserve unsuccessful comparisons.

5. **Medium — architectural work delays the quality decision.** Plan dependency lines 54–55 puts Marketing ownership, hooks and handoffs before P7. Existing `scripts/run_evals.py:2–9` cannot evaluate semantic gains meanwhile. Run the research comparison after P5; evaluate modules after P6. Make P8 extraction a separately justified maintenance batch.

## Category breakdown

Architecture 15/25; security 30/30; data flow 10/20; UX 15/15 (not applicable); testing 5/10.

## Limits and order

Code inspection plus one pure empty-ledger probe; no full suite, live providers, migrations or project edits. Graph tooling and referenced security-review skills were unavailable. Semantic gains and live host behavior remain unverified. Order: resolve contracts, capture fixes, research changes/comparison, modules, optional extraction.
