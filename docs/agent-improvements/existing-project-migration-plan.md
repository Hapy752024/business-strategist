# Existing-project migration and document cleanup

13 September 2026. **Revision 2 — status: planned; no live project migrated or rewritten.** The new-project default has been renamed to `business-analysis/`. This plan covers the five active projects inspected locally, including case separation and cleanup of current documents. It does not refresh or validate their market claims.

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

\* Counts exclude opaque `.git`, `node_modules`, and `.next` trees in the Italy website. Preserve these intact during rehearsal/cutover; do not assume they are disposable. `projects/_infra/` and `projects/_archive/` are not relocated. Only a small migration coordination directory is added under `_infra` as specified below.

| Source | Destination / handling |
|---|---|
| Root `market_research/manifest.json` | Exact original goes to `business-analysis/history/snapshots/<migration-id>/market_research/manifest.json`; it is not copied into an active discovery path. See the state contract below. |
| Other `market_research/**` | `business-analysis/market_research/**`, retaining raw/run/source bytes. Shared materials stay shared; current case summaries bind exact source paths, locators, hashes and applicability. |
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

## Required migration contracts

These close the three findings from the [initial independent review](existing-project-migration/adversarial-review/REVIEW.md). They are implementation requirements with acceptance checks, not new research gates or a general orchestration framework.

### Current state and historical manifests

For the five inspected legacy projects, archive the root research manifest byte-for-byte at the path above, together with its original path/hash. Do not retain it at `business-analysis/market_research/manifest.json`. Shared research is an evidence library, with no aggregate research stage machine. Cases alone own research state. Discovery may show the analysis comparison/navigation, but cannot surface old shared-root `current_stage`, `next_action`, `open_blockers` or pass/override fields as current case state. Existing immutable run manifests remain source history, not an authority to advance new cases.

Create each newly split case manifest with no inherited stage passes or overrides, an explicit review-required blocker and a current next action derived from its cleaned assessment. Preserve prior events/decisions in history with their actual scope and dates. Reconcile root controller navigation and all user-visible resume output with those case manifests. Do not copy the old topic-wide recommendation into a new case without checking applicability. Update shared-root initialization, collection and discovery so ordinary commands cannot recreate an aggregate research manifest after migration: case workflows require a registered case; intentional shared collection remains source-only and cannot advance case stages.

This reset applies to newly split legacy cases only. A later path-only `business/` → `business-analysis/` migration preserves existing case IDs, revisions, gates and explicit selection/generation. Rebase verified path references without granting new authority; uncertain bindings become review-required. For the five legacy projects, do not infer an execution selection from old priorities or an existing website. Previously approved brand/website decisions retain their scope; a historical approval does not become a new business-stage pass.

Acceptance: fixture the insurance manifest's obsolete “unoccupied layer” action, old pass/override fields and a conflicting current assessment. After migration, discovery, routing and resume must expose only current case actions/review requirements, exactly once; the original bytes remain accessible only as history. Attempted shared-root initialization must not revive the old workflow. Test path-only migration separately to prove it does not reset valid existing case authority.

### Stable coordination and recovery

Use one stable per-project lock file and journal under `projects/_infra/layout-migrations/<project-id>/`, outside every moved tree. Resolve identity from the canonical registered project path before creating or falling back to any workspace; recovery retains that identity/path mapping while the live directory is absent. Reject aliases, escapes and duplicate identity mappings. Lock files are never replaced or unlinked during normal use. Acquire the stable lock before existing owner locks; acquire owner locks umbrella-first, then analysis/case in a fixed order.

Supported commands hold a shared migration lock for the whole read/write operation, including child processes and delayed output publication. Migration/recovery holds its exclusive counterpart. This is a held lock, not a marker check followed by an unprotected write. Existing owner publication locks continue to serialize normal writers. Discovery takes a shared lock per canonical project and reports migration-in-progress instead of falling back to legacy paths. Direct script/CLI entry points, initialization, router/host dispatch, research readers/writers, brand/website adapters and town-db operations must participate before any mkdir, database open or provider side effect. Use one guard helper at shared entry points and an executable coverage matrix of public commands; do not add a daemon. For a command spanning owners, acquire stable project locks in sorted identity order before owner locks.

Before applying a migration, install compatible guards and drain/stop pre-existing unguarded jobs, website processes and SQLite connections for that project. A lock cannot protect an arbitrary editor or an already-running old process. If quiescence is unproven, postpone that project's cutover. Detect outside edits with fresh whole-tree inventory checks and never silently restore over them. The enforcement claim remains supported commands plus an explicitly quiesced cutover, not an OS filesystem sandbox.

Keep stage, original backup and live paths on one filesystem. The durable external journal records identity, reviewed inventory/content-map hashes, exact locations, expected tree identities and the states `prepared`, `original_moved`, `replacement_installed`, `verified`, `rolled_back`. Write intent before each rename and fsync the journal and affected parent directories. Recovery checks actual directory identities/hashes, including a crash after a rename but before its state update; state labels alone are insufficient. An unknown, corrupt or incomplete journal fails closed. Keep consumers blocked until verification succeeds or exact rollback finishes. Backups/staging live outside workspace-discovery roots; never expose them as extra active projects.

Rollback retains the proposed/replacement tree for inspection and restores the original only when identities and conflict checks match; external edits cause a stop. No recursive delete or “force” overwrite to resolve ambiguity. The original snapshot and old-to-new ledger remain after acceptance; cleanup is a separate task.

Acceptance: two real processes exercise shared-operation/exclusive-migration exclusion, a long-running child writer, and the reviewer's old-lock/root-replacement reproduction. Inject interruption before/after each directory rename, before/after journal updates and during rollback. Attempt discovery, initialization and normal writes while the live root is missing or replaced; all must stay blocked and no replacement workspace may be auto-created. Verify exact recovery, post-install conflict refusal and rerun/idempotency.

### Shared tools, external edits and SQLite

Prepare path-compatible tooling before the first cutover and leave that compatibility in place during rollback. Resolve registered layout and destination at operation time, never from an import-time constant or by guessing which directory exists. In particular, replace `scripts/town_db/db_common.py`'s hardcoded `DATA_DIR` and default-bound database paths with a resolver shared by its callers; ordinary reads use explicit existing-database/read-only semantics and cannot create an empty SQLite database at a stale path. Brand/website and export consumers must also resolve the active registered owner. Legacy and new paths for different projects must coexist without a repo-wide switch. An ambiguous or missing registered destination fails closed.

The cutover report includes every external path-dependent edit (repo tools, instructions, launch configs, references): owner, original/after hashes, compatibility across old/new/restored layouts, and rollback disposition. Prefer compatibility edits that stay installed. Any remaining per-project external edit joins the external journal and is conditionally restored only if its after-hash still matches; unrelated edits stop recovery. Complete or recover those edits before removing the migration marker. Do not restart services or change deployments as part of a path rewrite.

For the Italy database, drain writers and close connections before the final inventory/copy. Inventory the database and any WAL/SHM/journal sidecars as one quiesced unit; never copy a live main database alone. Preserve the original set exactly. On an isolated copy, verify SQLite integrity and a deterministic logical row/content comparison with the captured source, then exercise the ordinary read/export tools in both layouts and after rollback. Exports go to a disposable destination; no research data updates or live export regeneration are part of rehearsal. An active database or inconsistent capture blocks cutover. Inventory and preserve the website's ignored files, nested Git metadata/topology and symlink metadata at the same quiesced boundary.

Acceptance: mixed-layout fixtures run ordinary town-db reads/exports and Brand/Website entry before migration, after migration and after rollback; no stale-path directory/database appears. Test a conflict in an external configuration edit and prove recovery does not overwrite it. Verify current links/bindings resolve while historical bytes and approvals remain unchanged.

## Implementation and rollout sequence

1. **Prepare the migration tool and content map.** Implement the required state, stable-lock and mixed-layout compatibility contracts above before any relocation. Extend the existing migration/publication machinery with this explicit layout transition, dry-run inventory, per-file/section mapping, link/binding rewrite ledger and rollback. Do not run `scripts/migrate_project_layout.py --execute` as-is: it implements an older transition and contains stage-backfill behavior incompatible with this plan. `case_workspace.migrate()` also keeps research in its old location and is not a complete umbrella relocation tool.
2. **Inventory the dependency boundary.** Check current path references in manifests, route/workspace discovery, agent instructions, scripts, Markdown links/anchors, generated exports, handoffs, SQLite/data access, website imports, test fixtures and local launch/deployment configuration. Resolve symlinks without following escapes; detect case-insensitive collisions and nested Git/worktree metadata. Record pre-existing broken links separately. Existing README examples already contain obsolete `research/...` paths; use verified files to repair them, never a blind string substitution.
3. **Author the proposed current outputs off the live tree.** Archive legacy root manifests and build current case state under the state contract above. Complete the case/section map, clean narratives, derived comparison and navigation against the captured source hashes. Carry forward applicable constraints and known decisions. Start newly split case stages as unassessed/review-required; legacy topic-level passes stay historical. Rebind current derived artifacts only when their source identity and applicability are demonstrably unchanged; otherwise mark for review. Do not rewrite archived evidence or manufacture model inputs to satisfy a validator.
4. **Rehearse on copies.** Start with individualized content, then exercise the actual insurance case split and Italy's website/data paths in disposable copies. Use safe isolated copies of the website repository, including ignored files; preserve Git status and history. Test interrupted move/publication, rollback, rerun/idempotency, conflicting edits, shared-source correction propagation, independent Brand/Website entry, and case discovery/resume. A dry run writes only its report outside live projects.
5. **Produce the cutover report.** Show per-project moves and content diffs, case mapping, unchanged source hashes, link/binding results, original and proposed gate/selection state, website/database checks, blockers and rollback location. Any ambiguous content or path has an explicit disposition before that project is eligible. This is the concrete review artifact for migration; the present request authorizes planning, not live relocation or research rewriting.
6. **Cut over one project at a time when migration is requested.** Drain its writers/connections, resolve pending publications, acquire the stable external exclusive migration lock, and verify fresh hashes against the reviewed baseline. Stage on the same filesystem; retain an intact original project as the rollback source. Use a journaled directory replacement that detects the interruption window and refuses consumers until recovery. Detect outside edits before commit or rollback. Never delete original data or overwrite new work during rollback.
7. **Verify and resume.** Confirm the registered root and every case appear exactly once, all current internal links and declared bindings resolve, raw evidence is unchanged, no stage/selection/approval was gained, histories retain original dates/bytes, and independent subprojects still work. For Italy, verify Git topology/status, website build/tests and town-db read/export paths without publishing or updating data. Resume writers on the new registered paths only after successful verification; retain the rollback snapshot and old-to-new ledger. Apply the external-edit recovery dispositions from the cutover report before clearing its marker.

Use the small project for the first live cutover; migrate the remaining projects only after their own report passes. Italy remains last. Any concurrently edited project waits for a fresh baseline instead of losing newer work.

## Acceptance and remaining work

The rename is implemented in new initialization, registered-path resolution, case CLI dispatch, handoff validation, schema compatibility, discovery and agent instructions. `--start business-analysis` is the visible command; internal `business` identifiers and the old CLI alias stay compatible.

The physical migration executor, exhaustive section classification, clean per-project current documents, copy rehearsals and live cutovers are **not implemented by this planning task**. They are the ordered work above. Success requires both navigable case folders and clean, non-contradictory current outputs; a successful file move alone is insufficient.

Rename verification: **404 Python tests, 143 structural evaluations, zero setup errors**, with the existing town-db-curator warning. See [machine-readable results](existing-project-migration/rename-verification.json) and [setup log](existing-project-migration/rename-setup-check.txt). This verification covers the naming change and compatibility, not execution of the planned migration or document cleanup.
