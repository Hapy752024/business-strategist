# Implementation and gap closure

**Acceptance: READY for the reviewed implementation scope.** The eight findings in the [original fresh review](FRESH-IMPLEMENTATION-ADVERSARIAL-REVIEW.md) are closed. The [closure plan](GAP-CLOSURE-PLAN.md) incorporates the user's subsequent independent-subproject and naming requirements. The [independent closure review](implementation-evidence/gap-closure/independent-review.md) confirms no remaining material gap in F1–F8. Earlier implementation claims and the BLOCK verdict remain in history.

Latest naming amendment: `business-analysis/` replaces the new-project `business/` default; cases live under `business-analysis/cases/`. [Migration and document-cleanup plan](../existing-project-migration-plan.md) covers existing projects. Rename verification: 404 tests and 143 structural evaluations passed; no live migration or cleanup performed. The independent review below predates this naming amendment.

## Current structure and behavior

```text
projects/<slug>/
  README.md
  business-analysis/
    README.md                    # current case comparison
    cases/<case-id>/              # findings, feasibility, business case, economics
    market_research/              # shared research
    strategy/                     # selected business plan, including GTM
    history/                      # decisions and archived versions
  branding/
  digital-assets/
    website/
    others/
  history/                        # branding/digital decisions and versions
```

Each of the four destinations starts independently from its own brief. Brand and Website commands work without research. Explicit handoffs let work build on earlier Business or Branding outputs; they retain source and freshness checks. Completing one subproject never starts another automatically. `digital-assets/` groups deliverables and adds no stage machine. Business retains one explicit execution selection while allowing multiple investigations. Current documents show the latest findings; timelines and snapshots explain their evolution.

The [shared subproject contract](../../../references/subprojects.md) documents entry commands and ownership. New projects use the layout above. Existing legacy and version-2 projects keep their paths; no live migration was performed.

## Finding-to-fix evidence

| Finding | Implemented change | Verification |
|---|---|---|
| F1/F5: publication and downstream writers | Shared adapter stages supported Brand/Website writers, checks destination ownership, current explicit business handoffs, revisions and input digests, then publishes through the existing recoverable journal. Genuine standalone work requires no Business. | Normal CLI rejection without writes, cross-project and stale handoff rejection, valid standalone starts, late conflict and interrupted recovery regressions. Independent reviewer reran the earlier failures. |
| F2: output paths | Reconcile explicit workspace and destination; check default paths and symlinks before creating outputs. Enforce registered destinations in new layouts. | Cross-case and legacy/case mismatch, default symlink, motion/component selector escape tests. |
| F3: research dependencies | Builders capture actual input bindings and recursively declared upstream context. Shared input applicability is explicit; stage closure checks freshness. | Normal shared-input interpretation correction invalidates dependent stages; changed bytes block closure. |
| F4: numerical prose | Require reviewed economics digests and checked placeholders for model-derived figures in current documents, comparison summaries and selected-plan sections. | Stale/multiline handwritten values rejected. Fresh author receives an undisclosed revenue correction; contribution and capacity conclusions update through normal CLI publication. |
| F6: economics | Reject unknown fields; separate owner cash and imputed labor; avoid double-counting; distinguish recurring contribution from cash timing; expose missing downside/sensitivity coverage. | Focused accounting and sensitivity regressions; unavailable assumptions stay unresolved. |
| F7: comparison | Generate Business comparison from each case's current summary, principal uncertainty and next action; corrections visibly require review. | Comparison freshness and no-implicit-selection regressions. |
| F8: pilot scope | Require outcome/trust evidence plus cost/capacity implications for scope amendments. | Actual semantic exercise accepts a bounded comprehension fix and defers an unsupported leaderboard. |

No external framework, standing agent, provider, skill or additional stage machine was imported. Shared helpers extend existing publication, research and routing contracts.

## Verification and limits

- Full setup: **401 Python tests passed**, route/catalog checks passed, **143 structural evaluations passed**, website fixture passed; **1 warning, 0 errors**. The warning concerns existing town-db-curator checklist/evaluation coverage.
- Final small nested research discovery/resume change: **5 targeted tests passed**, 56 deselected. The complete suite predates this final change; it was not separately independently reviewed.
- Independent final bounded recheck: **71 passed**, seven Node-related cases deselected. The separate full setup covers the Node-backed checks outside the restricted sandbox.
- [Saved semantic replay](implementation-evidence/gap-closure/semantic-replay/verification.json): revenue 100→150 changes contribution 50→100 and required sales 80→40 against capacity 60. All three current narratives update; initial versions remain archived; execution stays unselected. The harness normalized initial comparison field names and supplied fixture revision/source bindings without editing authored prose.

These checks establish supported CLI behavior and bounded synthetic semantic performance. They do not establish market validation, universal natural-language correctness, undeclared dependency discovery, arbitrary filesystem containment or live provider/deployment quality. Existing external-service and release approvals remain applicable.

## Existing research preservation

No implementation command intentionally migrated or edited the live insurance research. The final [inventory comparison](implementation-evidence/gap-closure/preservation-check.json) is **not identical** to the original 376-file inventory: it finds 378 files, two new cyber-insurance research documents, and edits to the project README and the September 11 segment deep dive; no files are missing. The provenance of those concurrent changes was not established by this check. They were left intact. The earlier claim of 376 byte-identical files describes an earlier checkpoint and must not be read as the final state.

Original review, approved plan, migration rehearsal and earlier semantic evidence remain historical. Historical snapshots retain original bytes and path context.
