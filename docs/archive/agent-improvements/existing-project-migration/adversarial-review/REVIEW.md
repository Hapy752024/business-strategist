# Fresh adversarial review

**85/100 — FLAG. No confirmed BLOCK.** The plan is implementable and addresses the major preservation risks. Three details need explicit treatment.

Reviewed 13 September 2026 by `/root/fresh_migration_plan_adversary`, spawned with no inherited conversation. [Exact reviewed plan](plan-reviewed.md); [review context and source hash](review-context.json). Line references below refer to that snapshot and repository files at review time.

1. **P2 — Retire legacy manifest state from current discovery.** Plan lines 54, 92, 110 preserve source bytes and historical passes, but `inventory-and-proposed-paths.json:1938` maps the old research manifest directly to its active discovery location. The insurance manifest still recommends the withdrawn “unoccupied layer” (`projects/german-insurance-opportunity/market_research/manifest.json:158`). A bounded `/tmp` relocation reproduced that obsolete recommendation through `scripts/evidence_scout/workspace.py:527–539`. **Fix:** snapshot the original manifest, specify whether the shared root retains an operational manifest, and reconcile current status/action fields with case assessments. Test discovery/resume output, not only Markdown consistency. No gate bypass was demonstrated.

2. **P2 — Pin migration coordination outside the replaced tree.** Plan line 113 requires a lock, journal and consumer refusal but leaves their location and reader coverage unspecified. Existing locks/markers live inside the owner tree (`scripts/case_workspace.py:82–100`). A `/tmp` reproduction acquired a second project lock after replacing the root while the original lock remained held. Legacy discovery reads manifests directly. **Fix:** specify a stable external migration lock/marker keyed by project identity, checked by supported readers/writers before legacy fallback or directory creation. Test interruptions between both renames. This is an unsafe-reuse risk, not a demonstrated executor defect.

3. **P2 — Include external tooling in cutover and rollback.** Plan lines 109, 113–114 inventory external references but describe rollback as restoring the project directory. Town tooling hardcodes the old path outside that directory (`scripts/town_db/db_common.py:17–22`). **Fix:** prepare registered-layout-aware tooling before relocation; test both layouts and rollback. Record remaining external edits, hashes and recovery disposition.

| Category | Score |
|---|---:|
| Architecture | 20/25 |
| Security/data protection | 25/30 |
| Data flow | 15/20 |
| UX (not applicable) | 15/15 |
| Testing | 10/10 |

Read-only review; reproductions used `/tmp`. Exhaustive semantic classification, opaque website-tree integrity and SQLite snapshot consistency remain rehearsal obligations. The skill's security references and impact-graph tool were unavailable; direct inspection substituted. Recommended amendment order: manifest semantics, migration coordination, external-tool compatibility.
