# Generic finalist B — physical research cases as a reusable agent contract

Round 3, 13 September 2026. Reusable agent-default design; insurance is one migration example. No implementation.

## The information model

- **Project** is the persistent work container and user-selected context. Its kind is `discovery`, `venture`, or an existing standalone brand/website track. Creating a discovery project does not declare a business or activate its commitment stages.
- **Topic** describes the investigation boundary: sector, geography, customer area and questions. It is metadata/context, not another compulsory folder level or a venture.
- **Idea** is a distinguishable customer/problem/value or operating hypothesis. **Variant** is an actually investigated facet combination, such as language, buyer type or delivery model. Facets alone do not create folders.
- **Case** is the storage/execution scope for an idea or separately assessed variant. Cases are flat, related through metadata, and independently resumable. Being a case does not make something a separate company.
- **Run** is a dated research activity belonging to one case or the shared project scope. Runs can inform several cases but never substitute for enduring idea identity or automatically advance their stages.

Stable opaque IDs (`case-0001`) are independent of display title and directory slug. Registry entries contain ID, kind, facets, relations, aliases and location only. A rename retains the ID; a retired ID is never reused. Legacy names such as “idea 1” become explicit aliases rather than numerical ranking authority.

## Default structure: lazy, but physically meaningful

```text
projects/<project>/
  README.md                       # sole current project comparison/context
  history/evolution.md             # generated single project timeline
  history/decisions/<event-id>.md   # authoritative dated activities/decisions
  history/snapshots/                # superseded outputs and dated concept versions
  project-manifest.json            # project kind, selected scope, track links
  cases.json                      # created when the first case exists
  market_research/manifest.json    # shared discovery/comparison lifecycle only
  market_research/...             # actual shared outputs, created on use
  market_research/evidence-corrections.jsonl
  cases/<case-slug>/
    README.md                     # current scoped analysis
    history/evolution.md            # optional filtered view of project events
    history/snapshots/               # dated/versioned prior concepts and outputs
    market_research/manifest.json  # case state and evidence applicability
    market_research/...           # actual case-specific research
    strategy/...                  # actual scoped strategy, when authorized
  strategy/...                    # shared assumptions/comparisons when needed
  branding/ marketing/ web-site/ digital-assets/
                                  # selected venture/standalone work only, on use
```

For **broad discovery**, initialize only discovery context, README, initial evolution entry and shared manifest; do not generate a startup thesis, canvases or all stage folders. Mere candidate mentions stay in the discovery report. Create a minimal case when the output gives it a substantive separate assessment or the user selects it for a follow-up; the case starts with a real dossier, manifest and initial evolution entry, not empty downstream directories.

For **one chosen idea**, create one minimal case immediately. The root README can be a short context/decision entry linking that case. It does not need a large portfolio dashboard. Create segment/journey/pain files as that work occurs. A one-question factual lookup or copy edit still uses task-scope bypass and need not create any project or case.

The physical distinction from finalist A is durable: future case-specific source runs, research synthesis and strategy reside inside the case; shared studies remain at project scope. This creates autonomous case lifecycles, at greater migration and administrative cost.

## Lifecycle rules

| Action | Rule |
|---|---|
| Create/reuse | Resolve existing IDs, aliases and known intent first. Create only for a materially separate researched hypothesis, not a wording change. |
| Split | Allocate new IDs for new independently assessed scopes; preserve source case and dated split relationships. Reassess evidence applicability; do not clone gate passes. |
| Merge | Choose/create one surviving scope, mark others merged with redirects and dated rationale. Preserve all histories and evidence. Reassess conflicting state; no automatic maximum-stage inheritance. |
| Promote variant to idea | Change classification through a dated event; retain ID when hypothesis identity is unchanged. Promotion in importance does not imply validation. |
| Promote to venture/project | Explicit user selection plus independent operating ownership/lifecycle, budgets or deliverables justifies a venture track or separate project. Record lineage and shared-source references; do not infer launch authorization. |
| Park/reject/reopen | Preserve visible dossier, evidence and reason; record a reopening condition. New evidence permits reassessment, never automatic reinstatement. |

Retired split/merge IDs resolve read-only to their preserved history and successor choices. Writers reject them; they never silently follow an alias into an old or successor scope. Only unchanged-identity renames may reuse an ID for writes.

An idea may become a venture track within its existing project. Other investigations remain research cases; selecting a venture does not validate them. A genuinely independent second venture can become a sibling project with a relationship, rather than creating competing operating controllers beneath every language variant.

## Natural-language follow-ups and output routing

Resolve scope from explicit ID/name, then the case already selected in the conversation, then an unambiguous match to recorded hypothesis/facets. State the inferred destination in the work update. “Continue Chinese” selects the known Chinese case; “compare Chinese and English” selects a shared comparison listing both IDs. “Now look at students” reuses a matching investigated case or creates one if the intended hypothesis is clear. Do not ask the user to reselect a known workspace.

When two materially different scopes remain plausible, ask one concise distinction before dependent writes. Continue shared read-only inventory if useful. Scope changes are explicit; a new follow-up cannot silently replace the current venture or another case's status.

The router emits a scope envelope: project ID/kind, case ID or explicit `shared`, artifact root, permitted workstream destinations, source references and assessed revisions. Every writer consumes that envelope; `--out-dir` alone cannot establish authority.

| Skill/output family | Destination and state rule |
|---|---|
| Market discovery, multi-option tournament/panel | Shared `market_research/market_discovery/` or comparison reports; declare cases examined. |
| Idea grill, customer profile/journey, pain, evidence/customer voice | Selected case's intake/research paths. Shared collection is allowed only with explicit applicability assessment per consumer. |
| Competitor scout, landscape, marketing analysis, monitoring | Case-specific alternatives/monitoring when question is scoped; shared entity/report storage for cross-case questions. Preserve lane/source attribution. |
| Customer-perspective challenge, interviews/recruitment | Case research; cross-case recruitment logistics may be shared, but screener and evidence assessment remain scoped. Unpaid recruitment remains default. |
| Opportunity/risk, archetype/operator playbooks, positioning, startup strategy | Case strategy when specific; shared playbook/context/comparison once where applicable. Selected venture gate required for commitment work. |
| GTM, marketing/social, pilots, operating system | Selected case/venture strategy and marketing paths; each artifact/handoff declares the chosen case and assessed revision. |
| Brand orchestration/assets/UI/web/motion/export/quality | Existing selected venture or standalone track destinations; scoped business handoff where applicable. Research completion never starts these tracks automatically. |
| Infrastructure/setup, focused execution, standalone brand work | Existing task-scope rules; no forced discovery/case lifecycle. |

A scoped shared report can serve multiple skills; generating it does not update every case disposition. Product-specific stores such as town databases retain their owning store and provide references, rather than being copied into cases.

Latest specialist synthesis has a predictable destination: `cases/<case>/market_research/<stage>/current.md` or `cases/<case>/strategy/<family>/current.md`. Shared equivalents are project-root `market_research/<stage>/current.md` and `strategy/<family>/current.md`. Case/root README summarize and link these; dated reports and raw runs never masquerade as the current specialist result.

## Authority, corrections and gates

Each case manifest owns disposition, next action, blockers, stage readiness, evidence bindings and change events. The registry owns identity only. The root comparison and status boxes are derived. Dossier prose records the assessment/evidence revision reviewed; an interrupted update cannot make old prose current through a refreshed status box.

Each owning manifest declares `latest_artifacts` by purpose, format, path and reviewed revision. JSON/CSV and other machine or visual outputs retain native formats; `current.md` names narrative synthesis only. Every replacement archives the prior immutable version and records before/after pointers.

**Hard requirement: current findings, evolution and source audit are separate.** Every project/topic and case README presents only its latest coherent findings, assessment and next action. The same rule applies to current workstream outputs: no chronological update blocks, retained old recommendations or embedded evolution diary. Current/final means the latest delivered synthesis, never automatically validated or approved.

Borrow A/C's **one project human evolution log**: canonical `history/decisions/<event-id>.md` owns affected scope IDs, when/what/why, reviewer and before/after snapshot links. Manifest events reference ID/path only. Generate one `history/evolution.md`; optional case timelines filter these same events. Separate event files avoid concurrent append conflicts without duplicating authoritative narratives.

Archive actual concept versions at each relevant scope's `history/snapshots/<date>-concept-v<N>.md`, including customer/problem/value/model/constraints. These historical interpretations differ from raw evidence, which stays in research run directories. Current README links findings, evolution and source audit separately. Scope-local authoritative logs offer autonomy but fragment cross-case decisions; reconsider them only for explicitly independently staffed operations. Physical case storage alone is not that trigger. This revises Round 3's earlier local-log recommendation through cross-pollination.

For substantive updates: finish/audit sources → assess affected cases → snapshot replaced outputs and stage one decision record → commit reviewed state plus the decision ID/path under revision checks → publish only committed records in the derived evolution timeline → refresh current prose/views at those revisions. New decision records remain pending and invisible in the timeline until referenced by committed state. A multi-case event declares all affected IDs; until all required scope commits complete it stays pending, affected consumers remain stale, and resume finishes or explicitly aborts it. Never publish a cross-case decision as complete after only one case commits. Corrections use this same protocol. Interrupted output refresh remains visibly stale. Direct-entry legacy notices and clean rewrites are required.

Bindings identify canonical artifact/record/section, applicability and reviewed correction revision. Derived reports declare admission-relevant source dependencies. Shared correction records preserve old bytes, identify replacements, and trigger a scan of case bindings. Matching consumers become stale immediately on read/admission; incomplete dependencies conservatively stale the affected report's consumers. Unknown dependencies cannot establish readiness. This is declared dependency checking, not automatic semantic inference. Unrelated cases remain unchanged.

Discovery scope has research-completion checks, not venture launch readiness. A venture commitment request must identify its chosen case and assess that case's segment/journey/pain foundation. Another case's pass or the shared discovery pass cannot satisfy it. Case-scoped overrides retain explicit authorization, stage/reason and evidence revision; no sibling inheritance.

The same resolver serves admission, collection, stage updates, discovery/resume, locks and downstream handoffs. References remain project-root-relative. Updates require case lock plus expected manifest revision; correction revision is checked again before commit. Handoff consumers reject stale case/evidence revisions. Unknown IDs and escaped destinations fail closed. These are required future behaviors, not today's implemented guarantees.

## Reusable changes grounded in current code

Inspection confirms `init_project.py` calls `create_project_workspace`, describes every topic as a venture, and treats `--topic` as an alias. `workspace.py` eagerly creates all `PROJECT_SUBDIRS`, thesis and canvases, all stages, and a business track. `templates/project/README.md` assumes a venture's commitment sequence. These need project-kind-aware lazy initialization and separate discovery/case templates.

`collect.py`, `discover_market_problems.py`, `analyze_competitor_marketing.py` and `collect_ads.py` use `resolve_run_dir`; extend that seam and their stage updates. `build_entity_landscape.py` and `build_landscape_artifacts.py` directly call `update_stage`; `research_founder_playbooks.py` initializes its workspace/builds paths itself and delegates collection with explicit `--out-dir`. These require adapters and scoped-destination tests, not an assumption that one helper covers all writers. All names here are under `scripts/evidence_scout/`.

`route_workflow.py:pain_gate_state`, `missing_strategy_stages`, override recording and `workspace.py:update_stage` assume one root manifest: consume the resolved scope throughout. `project_workspace.py` discovery, `next_actions`, linking and brand handoff checks need case-aware selected-track references. Extend schemas, lifecycle/task-scope/runtime-routing references, skill catalog output contracts and affected specialist workflow instructions. This is a bounded contract migration, not a new framework.

Legacy single-project workspaces resolve to their existing root scope unchanged. Do not auto-move runs or import a root pass into newly split cases. Newly created projects use the new contract; existing projects opt into an inventoried migration with backups, path maps and explicit state reconciliation. Legacy read compatibility is not permission to bypass scoped gates after opt-in. Required checks cover single-case/discovery defaults, scoped writing, legacy reads, split/merge lineage, corrections, isolation and handoff denial.

## Synthetic example and decision

“Explore repair businesses for urban households” starts discovery. Substantive findings produce appliance-repair and bicycle-repair cases. A later “compare renters with homeowners for appliance repair” creates assessed variants only if separately investigated; city is initially a facet. A shared interview study stays once at project scope. Correcting one landlord-approval finding reopens dependent renter assessments, leaving bicycle evidence untouched. Selecting appliance repair for a pilot creates the chosen venture handoff; it neither passes its pain gate nor launches a brand automatically.

Best for sustained independent investigations; costlier than an overlay. The [external analogies](../external-patterns.md), retrieved 2026-09-13, inform scope, restraint and report preservation, not proof of this design.
