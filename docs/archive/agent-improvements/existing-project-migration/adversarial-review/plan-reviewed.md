# Existing-project migration and document cleanup

13 September 2026. **Status: planned; no live project migrated or rewritten.** The new-project default has been renamed to `business-analysis/`. This plan covers the five active projects inspected locally, including case separation and cleanup of current documents. It does not refresh or validate their market claims.

## Target

```text
projects/<slug>/
  README.md                              # short navigation and current project status
  project-manifest.json                  # umbrella, independent subproject destinations
  business-analysis/
    README.md                            # current case comparison and explicit selection
    project-manifest.json                # case registry; one nullable execution selection
    cases/<stable-case-id>/
      README.md                          # current assessment, evidence limits, next action
      feasibility.md                     # implementation, delivery, access, capacity, risks
      business-case.md                    # latest economic interpretation and assumptions
      economics.json                     # checked model, when assessed
      market_research/                    # this case's research and stage manifest
    market_research/                      # shared sources and original research runs
    strategy/                            # one selected business plan including GTM
    history/
      evolution.md                       # one analysis timeline, tagged by case
      decisions/                         # decision details, dates and reasons
      reviews/                           # dated challenge/review records
      snapshots/<decision-id>/           # exact superseded documents and concepts
  branding/
  digital-assets/
    website/
    others/                              # e.g. the Italy town database
  history/                               # umbrella migration and design/digital history
```

Create only meaningful outputs. Cases can be registered as unassessed without fabricating a feasibility report or model. Analysis, Branding, Website and other digital assets remain independently startable. A research priority, old recommendation or existing website is not an execution selection.

Use one analysis timeline, with case IDs and links to per-decision details. Do not add an independently maintained log to every case. Each case links to its relevant history. Umbrella history covers structure, Branding and Digital Assets; it does not duplicate analysis decisions.

## Inspected scope and physical mapping

[Inventory and proposed file destinations](existing-project-migration/inventory-and-proposed-paths.json) records source hashes and a proposed destination/action for 1,552 files. It excludes three opaque Git/runtime trees from hashing and records them separately. This is a planning snapshot, not a cutover baseline: active research was changing during this session. Re-inventory immediately before rehearsal and again under the cutover lock.

| Existing project | Inspected files* | Proposed treatment |
|---|---:|---|
| `individualized-marketing-content` | 33 | First rehearsal: small research-only project. One initially unassessed case; no stage machine or evidence pass invented. |
| `tattoo-insurance` | 140 | Separate direct consumer cover from the studio-embedded protection hypothesis. Keep country evidence shared unless its use is genuinely case-specific. |
| `credit-cards-enhanced-payments` | 271 | Separate the three explicit commercial alternatives; retain payer/cohort distinctions within their case. Move dated `reviews/` into analysis history. |
| `german-insurance-opportunity` | 379 | Separate language/service, cyber and operating-model investigations; consolidate overlapping current recommendations into case assessments and one comparison. |
| `us-retirees-italy` | 729 | Separate relocation, resident support and housing/community cases; preserve Branding, the website repository and the town database. Migrate last because path-dependent tooling is broader. |

\* Counts exclude opaque `.git`, `node_modules`, and `.next` trees in the Italy website. Preserve these intact during rehearsal/cutover; do not assume they are disposable. `projects/_infra/` and `projects/_archive/` are outside this migration.

| Source | Destination / handling |
|---|---|
| `market_research/**` | `business-analysis/market_research/**`, retaining raw/run/source bytes. Shared materials stay shared; current case summaries bind exact source paths, locators, hashes and applicability. |
| `strategy/**` | `business-analysis/strategy/**` initially; separate case assessments and dated history through the content map below. Old multi-idea plans do not become an approved selected business plan. |
| `strategy/decisions/**` | `business-analysis/history/decisions/legacy/**`; preserve bytes and actual decision dates. |
| `marketing/**` | `business-analysis/marketing/**`; preserve campaign status and authorization. |
| `reviews/**` | `business-analysis/history/reviews/**`; retain review outcomes and limitations. |
| `branding/**` | Same path. Check its current links/handoffs; do not change approvals. |
| `web-site/**` | `digital-assets/website/**`, including its Git repository and ignored files. Inspect `.git` topology, scripts, configuration, site content imports and local launch paths. No deployment is part of migration. |
| Existing `digital-assets/**` | `digital-assets/others/**`; the Italy `town-db/` remains one intact data asset. Route-specific `website/` or `others/` in already-new layouts must be recognized, never nested again. |
| Root `test-results/**` | Proposed Italy destination: `digital-assets/website/qa/legacy-project-test-results/`. Confirm producer ownership before applying; no overwrite of the website's existing test results. |
| Root README / project manifest | Archive exact originals with original-path metadata; author new navigation and the two controllers. Preserve project identity. |
| Existing umbrella `business/**`, if encountered later | Resolve the registered path, then explicitly relocate to `business-analysis/**`. Until cutover, commands continue using `business/`. Reject conflicting simultaneous roots. |

The JSON destinations are a physical relocation proposal. They do not decide that every old strategy/deep-dive document is still current. The section-level content map controls that decision before publication.

## Proposed case map

These are migration classifications derived from existing documents, not new recommendations or validation. Stable IDs can be chosen independently of their display titles. Materially distinct buyer, need, delivery or economics justify a case; incidental language, country and channel combinations do not justify an automatic Cartesian expansion.

| Project | Initial cases | Shared material / important boundary |
|---|---|---|
| German insurance | `personal-english`, `personal-chinese`, `professional-it`, `arabic-doctors`, `cyber-access`, `discount-motor-mga`, `broker-succession` | Language cohorts are separately visible because they were explicitly investigated. Surelius decision tooling is a shared capability hypothesis unless assessed as an independent product/business. Keep other retirement/self-employed/SME segment investigations visible in the comparison as candidate or parked topics where the section map supports a distinct case; do not silently drop them. Do not multiply every profession by every language. |
| Enhanced payments | `card-funded-bill-payment`, `rewards-assistance`, `contractor-cash-workflow` | Existing founder-fit comparison names these three. Business/private rewards payers, retailer/contractor cohorts and countries remain explicit facets unless the research establishes separate offers/economics. Public-body channels remain deferred hypotheses. |
| Tattoo insurance | `direct-consumer-cover`, `studio-embedded-protection` | Preserve the broad-cover counter-evidence and the embedded hypothesis separately. Spain/Italy/France/Germany are research facets, not four approved businesses. |
| Individualized marketing content | `individualized-content` | Working identity only; do not invent a segment or claim validation from the old evidence run. |
| Italy retirees | `relocation-advice`, `resident-support`, `village-housing-community` | Pre-move and already-resident needs/economics differ. The proposed homes/community model carries distinct capacity/capital obligations. US/UK/other English-speaking cohorts and rent/buy journeys remain visible facets. Preserve existing brand and offer decisions without extending their scope to new cases. |

Case-map source anchors: each project's current README; insurance `strategy/current-recommendation.md`, `strategy/arabic-brokerage-assessment.md`, `strategy/annex-{a,b,c}-*.md`, and the September 11/13 segment/cyber deep dives; payments' founder-fit comparison; Italy's resident-services/village assessment. The executor must account for every investigated alternative found in the full section inventory: map to a case, shared topic, or explicitly parked history entry with a reason. The initial list above is not a claim of exhaustive semantic classification.

## Clean current documents, preserve evolution

Migration includes editorial consolidation, not just folder moves. Before replacing anything, save the entire original document byte-for-byte in a snapshot. Build a compact section map with: original path and heading, proposed case/shared owner, role (`current`, `history`, `source`), superseding source/decision where applicable, and unresolved conflict.

For current documents:

- State the latest supported conclusion directly. Keep evidence, interpretation, assumptions and unknowns distinct. Include sources with their original observation/retrieval dates and a last-reviewed date; removing logs does not mean removing provenance.
- Remove chronological appendices such as “what changed”, “follow-up”, “earlier we thought” and repeated versions of the same recommendation. Put their decision/evolution content in the timeline and link to exact snapshots. A follow-up's still-current findings are integrated into the appropriate topic section.
- Resolve known superseded assertions using the supplied correction and its scope. A newer timestamp alone does not make a claim stronger. Where the record conflicts without resolution, say “unresolved” in the current assessment and describe the disagreement in history.
- Keep the project README as navigation, the analysis README as the current comparison, and each case README as its authoritative assessment. Do not leave another competing `current-recommendation.md` with a different conclusion.
- Keep dated research reports/raw runs as attributed source records; they are not all logs and must not be stripped of evidence. Current documents link to the relevant findings. Preserve historical reports and snapshots as authored, including their original link base recorded in the migration ledger.
- Separate founder decisions from facts. Preserve the actual date, reason, alternatives and authority where known. Use “date/author unknown” when absent; migration time is not the original decision time. No migration-generated stage pass, validation claim, price approval or execution selection.

Concrete cleanup acceptance examples:

| Existing issue observed locally | Required result |
|---|---|
| Insurance README retains an earlier “unoccupied” cyber layer assertion alongside a later withdrawal | Current cyber assessment presents incumbent overlap and the remaining hypothesis/unknowns. The old assertion and why it changed are discoverable in history, not repeated as current fact. |
| Insurance root and `strategy/current-recommendation.md` emphasize different investigation priorities | One comparison explains current research priorities and unresolved ranking; neither priority silently selects a business. |
| Payments README appends fee, retention, AI-cost and acquiring follow-ups to earlier scenarios | One current business case explains the latest conditional assumptions and sensitivities. Earlier calculations remain dated history/source artifacts, with no contradictory “current” profit claims. |
| Italy README combines dated price/audience decisions, revised competitor claims, relocation economics and housing scenarios | Each case gets its own current assessment/model context. Keep existing decisions in history and their currently applicable constraints in the relevant output. Do not add EUR housing scenarios to USD relocation scenarios. |

No new web retrieval is needed merely to classify these supplied documents. A claim requiring fresh verification is marked as such; research refresh is a separate scoped action.

## Implementation and rollout sequence

1. **Prepare the migration tool and content map.** Extend the existing migration/publication machinery with this explicit layout transition, dry-run inventory, per-file/section mapping, link/binding rewrite ledger and rollback. Do not run `scripts/migrate_project_layout.py --execute` as-is: it implements an older transition and contains stage-backfill behavior incompatible with this plan. `case_workspace.migrate()` also keeps research in its old location and is not a complete umbrella relocation tool.
2. **Inventory the dependency boundary.** Check current path references in manifests, route/workspace discovery, agent instructions, scripts, Markdown links/anchors, generated exports, handoffs, SQLite/data access, website imports, test fixtures and local launch/deployment configuration. Resolve symlinks without following escapes; detect case-insensitive collisions and nested Git/worktree metadata. Record pre-existing broken links separately. Existing README examples already contain obsolete `research/...` paths; use verified files to repair them, never a blind string substitution.
3. **Author the proposed current outputs off the live tree.** Complete the case/section map, clean narratives, derived comparison and navigation against the captured source hashes. Carry forward applicable constraints and known decisions. Start newly split case stages as unassessed/review-required; legacy topic-level passes stay historical. Rebind current derived artifacts only when their source identity and applicability are demonstrably unchanged; otherwise mark for review. Do not rewrite archived evidence or manufacture model inputs to satisfy a validator.
4. **Rehearse on copies.** Start with individualized content, then exercise the actual insurance case split and Italy's website/data paths in disposable copies. Use safe isolated copies of the website repository, including ignored files; preserve Git status and history. Test interrupted move/publication, rollback, rerun/idempotency, conflicting edits, shared-source correction propagation, independent Brand/Website entry, and case discovery/resume. A dry run writes only its report outside live projects.
5. **Produce the cutover report.** Show per-project moves and content diffs, case mapping, unchanged source hashes, link/binding results, original and proposed gate/selection state, website/database checks, blockers and rollback location. Any ambiguous content or path has an explicit disposition before that project is eligible. This is the concrete review artifact for migration; the present request authorizes planning, not live relocation or research rewriting.
6. **Cut over one project at a time when migration is requested.** Pause its writers, resolve pending publications, acquire the migration lock, and verify fresh hashes against the reviewed baseline. Stage on the same filesystem; retain an intact original project as the rollback source. Use a journaled directory replacement that detects the interruption window and refuses consumers until recovery. Detect outside edits before commit or rollback. Never delete original data or overwrite new work during rollback.
7. **Verify and resume.** Confirm the registered root and every case appear exactly once, all current internal links and declared bindings resolve, raw evidence is unchanged, no stage/selection/approval was gained, histories retain original dates/bytes, and independent subprojects still work. For Italy, verify Git topology/status, website build/tests and town-db read/export paths without publishing or updating data. Resume writers on the new registered paths only after successful verification; retain the rollback snapshot and old-to-new ledger.

Use the small project for the first live cutover; migrate the remaining projects only after their own report passes. Italy remains last. Any concurrently edited project waits for a fresh baseline instead of losing newer work.

## Acceptance and remaining work

The rename is implemented in new initialization, registered-path resolution, case CLI dispatch, handoff validation, schema compatibility, discovery and agent instructions. `--start business-analysis` is the visible command; internal `business` identifiers and the old CLI alias stay compatible.

The physical migration executor, exhaustive section classification, clean per-project current documents, copy rehearsals and live cutovers are **not implemented by this planning task**. They are the ordered work above. Success requires both navigable case folders and clean, non-contradictory current outputs; a successful file move alone is insufficient.

Rename verification: **404 Python tests, 143 structural evaluations, zero setup errors**, with the existing town-db-curator warning. See [machine-readable results](existing-project-migration/rename-verification.json) and [setup log](existing-project-migration/rename-setup-check.txt). This verification covers the naming change and compatibility, not execution of the planned migration or document cleanup.
