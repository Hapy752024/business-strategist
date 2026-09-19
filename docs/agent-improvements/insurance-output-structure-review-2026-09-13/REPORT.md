# Reusable agent output structure: two designs

Design review, 13 September 2026. **The target is the reusable agent and all future projects.** German insurance is the inspected example and a later migration candidate. Existing project files and agent code remain unchanged.

**Recommendation: physical research cases under one topic/project umbrella, with one project evolution timeline and separate archived concept versions.** The alternative is a generated idea library backed by centralized state and stage-based storage. Both must support broad topic discovery, one chosen idea, and multiple investigated variants without turning every variant into another company.

Independent Round 3 review: **A 85/100, B 87/100; both qualified as design options.** The judge stopped after three of the permitted five rounds. These are weighted design judgments, not measured usability or implementation results. [Round 3 judgment](round-3/judge.md). The subsequent user clarification below refines both options; its integration by the root agent has not received another independent review. The [exact reviewed report](history/REPORT-round-3-reviewed.md) is archived.

## Selection and business-plan ownership

The [implementation plan, Revision 2](IMPROVEMENT-PLAN.md) includes research-content improvements derived from four closer open-source agents and resolves the later adversarial findings. It consolidates case identity entries into the existing project manifest instead of requiring a separate `cases.json`; case stage ownership remains local. The [independent revision check](INDEPENDENT-REVISION-CHECK.md) finds it READY at plan level. This does not establish implementation correctness or migration approval; the earlier tournament scores remain historical.

**Investigate many ideas, select one for execution.** Cases hold current research, a feasibility assessment and a high-level business case. Project-root `strategy/` holds the business plan for the single selected idea, with its financial model and implementation roadmap as needed. Other cases remain available for research and comparison. They do not receive parallel execution tracks merely because their assessments are promising.

Feasibility asks what delivery would require: people, technology, partners, permissions, time, capacity, upfront effort/cost and unresolved dependencies. A business case asks whether choosing it makes economic sense: revenue mechanism, acquisition and delivery costs, required cash, break-even, downside assumptions and the evidence needed to decide. Both are exploratory assessments, not execution approval.

The project has one nullable `selected_idea_id`, with an explicit selected scope/configuration and a selection revision. Research focus is separate from execution selection. Before selection there is no approved root business plan. After selection the root plan and downstream handoffs must identify the same selection revision; selection alone does not waive pain validation or action-specific authorization. An explicit user decision is required to switch selection. Preserve the prior plan in snapshots, record the change once, and invalidate its execution handoffs. Unselected variants remain research unless explicitly included in the chosen idea's execution scope.

The root README remains the short overview and comparison/navigation entrypoint. It links to the authoritative business plan rather than maintaining another full plan. Do not combine revenue forecasts for mutually exclusive ideas or count common costs and overlapping demand twice.

See [open-source comparables, business-plan coverage and proposed assessment contracts](business-plan-coverage-and-open-source.md). These are proposed reusable-agent changes, not implemented behavior or an insurance business plan.

## The common output contract

A reader should be able to answer “What do we know now?” without reading the research diary.

| Material | Purpose | Update rule |
|---|---|---|
| Current project overview | Compare investigated alternatives and show the current decision/unknowns | Rewrite affected synthesis; do not prepend another dated update. |
| Current idea/variant dossier | Explain the concept, latest findings, counter-evidence, disposition and next action | One current interpretation for the named scope. Current does not mean validated. |
| Current specialist outputs | Latest segment, journey, pain, competitor, risk or strategy assessment | Stable paths; scope and reviewed evidence revision visible. |
| Evolution/decision history | Explain when, what and why a concept or decision changed | Record each decision once, with affected IDs and before/after archive links. |
| Archived concept/output versions | Preserve the actual prior concept and findings | Immutable dated/versioned snapshots, clearly historical. |
| Evidence and run records | Preserve sources, retrieval context, provider failures and execution details | Retain original run artifacts and their provenance separately from human decision history. |

A current concept should name its customer/topic scope, problem or question, proposed value/model where applicable, findings, decisive uncertainties and present disposition. Old rejected wording, previous rankings and chronological work notes belong in history and archives. Current documents link to them; they do not embed them.

## One log or several?

**Default to one readable project evolution timeline, tagged by stable idea/variant IDs.** The founder can see how the overall investigation evolved without searching several diaries.

Store a decision once in `history/decisions/<event-id>.md`: date, affected scopes, what changed, why, evidence references and before/after snapshot links. Generate `history/evolution.md` from those records. Machine-state events reference that decision ID/path instead of independently repeating its explanation. This is one logical history with a single reading entrypoint, even though detailed decision records are individual files.

Keep operational/provider logs with their research runs. Keep concept snapshots with their owning scope or in a project archive indexed by scope. Generate a filtered variant timeline only when the overall timeline becomes cumbersome. Multiple independently maintained decision logs are justified only when separate ownership requires them; that is not the default.

Only committed decisions appear in the timeline. A shared decision that has not finished updating all affected scopes remains pending, and its dependent views remain stale. Each scope also declares its latest artifact by purpose, format, path and reviewed revision: JSON/CSV and other deliverables retain their native format and archived prior versions. The `current.md` paths below describe narrative outputs, not a requirement to convert everything to Markdown.

## Option A — idea library with centralized scoped workflows

```text
projects/<topic-or-venture>/
  README.md                           # current overview/comparison
  ideas/
    index.json                        # IDs, labels, relations and locations
    <idea>/brief.md                    # generated current dossier
    <idea>/<variant>.md                # created when actually investigated
  market_research/
    manifest.json                     # topic + independent scoped checkpoints
    customer_segments/<scope>/current.md
    customer_journey/<scope>/current.md
    pain_points/<scope>/current.md
    pain_points/runs/<run>/            # original evidence
    solution_alternatives/...
  assessments/<scope>/feasibility.md
  assessments/<scope>/business-case.md
  strategy/business-plan.md           # only the selected idea
  strategy/financial-model.*          # supporting selected-idea economics
  history/
    evolution.md                      # one readable timeline
    decisions/<event-id>.md            # canonical decision records
    snapshots/<revision>/...           # archived concepts and outputs
```

You browse by idea, while source files and future work remain organized by research stage. Central scope records own each idea/variant's narrative, next action, disposition, evidence applicability and sparse stage checkpoints. The idea index owns identity only; dossiers and status rows are generated views.

For insurance, the idea library exposes English and Chinese under personal insurance decisions, IT and doctors under combined professional/personal cover, and direct entries for motor, cyber, retirement and broker acquisition. Arabic doctors has one cross-linked dossier. Languages, professions and channels are facets; their combinations are not automatically new businesses.

**Best fit:** shared research and uniform stage-based tooling matter more than having all of an idea's files in its own folder.

**Cost:** authored narrative in structured state, generated-view discipline, a growing central manifest and serialized updates. Full scoped routing, stage transitions and handoffs still require implementation. This is not just adding an index, and it is not a proven low-cost shortcut.

**Distinctive property:** one central state authority; new outputs remain in shared workstream folders. The complete reusable design supports independent scoped workflows, superseding the earlier research-only draft.

Full contract: [Option A](round-3/proposal-a.md).

## Option B — physical research cases with local state

A case is the durable home of an investigated idea or variant. It can develop independently without becoming another company. Relationships and facets organize the comparison; the filesystem does not need a rigid language/profession hierarchy.

```text
projects/<topic-or-venture>/
  README.md                           # current overview/comparison
  project-manifest.json                # context, case identities, selection, tracks
  cases/<case>/
    README.md                         # current concept and findings
    market_research/
      manifest.json                   # this case's state and evidence assessment
      customer_segments/current.md
      customer_journey/current.md
      pain_points/current.md
      pain_points/runs/<run>/
      solution_alternatives/current.md
    feasibility.md                    # can we implement this idea?
    business-case.md                   # is it economically worth choosing?
    economics/                        # assumptions/model when needed
    history/snapshots/
      <date>-concept-v<N>.md           # actual prior concept versions
      <revision>/...                  # archived other outputs
  market_research/...                  # common studies and historical evidence
  strategy/business-plan.md           # one selected idea, current plan
  strategy/financial-model.*          # supporting model when needed
  strategy/implementation-roadmap.md  # selected idea only, when needed
  history/
    evolution.md                      # one project timeline, tagged by case
    decisions/<event-id>.md            # one canonical record per decision
    snapshots/...                     # prior project-level comparisons
```

Start a dormant case with its dossier and minimal state. Create other folders when there is actual work. A shared report remains at project scope; cases link to the relevant sections or records and assess applicability separately. Original insurance evidence need not move simply because new case folders exist.

The insurance case list would include English personal cover, Chinese personal cover, IT combined cover, doctors/Arabic doctors, the investigated discount motor MGA, cyber readiness, retirement and broker acquisition. Japanese/Korean comparisons remain visible with their limited coverage. Keep Surelius/simulation as linked capabilities and register mail as a channel unless they become independently defined commercial hypotheses.

**Best fit:** sustained independent follow-ups, where the user regularly returns to a particular variant and wants its future outputs together.

**Cost:** case-aware initialization, routing, output allocation, locking, stage updates and handoffs; more local manifests and explicit shared-evidence review. Existing code does not recognize nested cases automatically.

**Distinctive property:** each case owns its state, research and feasibility/economic assessments; the project owns the selected idea's business plan and execution. This is why B is the stronger fit for the workflow described here. It can use the same single project timeline as A; logging policy is not dictated by physical storage.

Full contract: [Option B](round-3/proposal-b.md).

## How the agent should behave in future projects

| User request or event | Required reusable behavior |
|---|---|
| “Explore this topic” | Create an exploratory topic scope, without a pretend chosen venture or empty business canvases. |
| “Investigate this specific idea” | Create one minimal idea/case, not a forest of variant placeholders. |
| Discovery identifies alternatives | Register substantively investigated alternatives with evidence limits; registration is not selection or validation. |
| “Continue the Chinese version” | Reuse its stable scope from the conversation/registry; no unnecessary workspace question or duplicate folder. |
| “Compare English and Chinese” | Write a shared comparison with explicit affected IDs; do not advance both scopes automatically. |
| “Check whether motor insurance is feasible and profitable” | Assess that case's delivery requirements and economics as hypotheses; do not select it or authorize execution. |
| “Select this idea” | Record one execution selection and its scope; plan readiness and action authorization remain separate. |
| “Switch to another idea” | Require explicit selection, archive the prior plan, record the reason and invalidate prior execution handoffs. |
| A wording/rank change | Retain identity. Display names and ranking are not IDs. |
| Split or merge hypotheses | Preserve relationships, histories and source references; reassess applicability. Retired scopes remain readable but cannot receive silent new writes. |
| Park/reopen a variant | Keep it discoverable with reason and reopening condition. New evidence permits reassessment, not automatic validation. |
| A concept's customer/problem/model changes | Archive the old concept and record the change; old evidence/gates require renewed applicability review. |
| A source or interpretation is corrected | Mark dependent current conclusions and readiness review-required; preserve original evidence and unaffected scopes. |
| “Build for the selected idea” | Require the single current selection and matching revision, that scope's prerequisites, authorization and immutable handoff; another scope's pass does not qualify it. |
| Standalone logo/copy/factual task | Preserve the existing focused/standalone bypass; do not impose a portfolio workflow. |

The agent resolves a known target from user intent and context and states it briefly. It asks one question only when multiple plausible destinations would materially change the work. Users should not need to supply technical IDs.

Both designs need reviewed source-use bindings, correction revision checks and explicit dependencies from derived reports. A file hash alone cannot detect a mistaken interpretation. Checks cover declared dependencies; they cannot discover every semantic dependency automatically. Interrupted writes/rendering must make stale views detectable on resume. No gate is inherited just because two scopes share a source, parent or industry.

## What changes in the reusable agent

| Area | Concrete existing surface |
|---|---|
| New-project defaults and output allocation | `scripts/evidence_scout/init_project.py`; `workspace.py:create_project_workspace`, `resolve_run_dir`, run manifests and `update_stage` |
| Scope-aware dispatch and permissions | `scripts/route_workflow.py`; `scripts/enforce_skill_route.py`; `references/runtime-routing.md` |
| Project discovery, resume and selected tracks | `scripts/project_workspace.py`; workspace replay helpers and lifecycle contract |
| Evidence/discovery/competitor writers | `collect.py`, `discover_market_problems.py`, `discover_competitors.py`, `analyze_competitor_marketing.py`, `collect_ads.py` |
| Direct and custom writers | `build_entity_landscape.py`, `build_landscape_artifacts.py`, `research_founder_playbooks.py`, `build_interview_kit.py` |
| Strategy and downstream consumers | Strategy validation and business-to-brand builders/validators; scoped GTM, marketing, pilot, brand and website handoffs |
| Reusable documentation/templates | `AGENTS.md`; `references/workspace-lifecycle.md`, `research-coaching.md`; project/dossier/current-output/history templates and applicable specialist workflow references |
| Executable contracts and checks | Relevant project/research/stage/handoff schemas, skill catalog and route validation; producer/caller coverage and scope-isolation regressions |

This is a targeted change map, not a claim that every writer has already been audited. A common scope/output contract must be consumed by relevant skills and scripts. Copying the same instruction independently into many skills would invite drift. No additional agent framework or specialist skill is needed for the folder policy itself.

Current initialization eagerly creates venture scaffolding even when invoked through topic research. Several tools also update project-wide stages directly. Those behaviors explain why changing only Markdown templates would be insufficient.

## Adoption and acceptance

New projects use the selected contract by default after implementation. Existing projects remain readable and do not migrate silently. For insurance, first inventory scope, links, current-status conflicts and protected evidence; then use a local backup and reversible path map. Existing umbrella conditional passes are historical state, not validation of newly registered variants.

Required future checks include topic versus single-idea initialization, stable reuse, scoped writes across all producer families, concurrent different-scope updates, split/merge redirects, source-correction interruption, latest-versus-history separation, before/after concept archives, stale handoff rejection, standalone bypass and legacy non-migration. Selection checks must reject multiple execution targets, execution for unselected cases and handoffs from a prior selection revision while allowing research on other cases. Exploratory economics must remain distinct from commitment and launch permissions. Rehearse migration and rollback on a copy before applying it to live local-only research.

The architecture review uses synthetic restaurant-food-waste and household-repair examples to test generality. These are paper scenarios, not market findings or executed regression tests. Insurance evidence remains unchanged.

## Evidence and review material

The local inspection found 376 files, including 130 Markdown files, with idea material spread across stage folders and current-looking historical recommendations. A five-document sample found nine missing relative link targets. Details: [local findings](local-findings.md), [file inventory](workspace-inventory.json), [sample link audit](sample-link-audit.json).

Read the latest reviewer assessment and iteration history through [the review log](REVIEW-LOG.md), keeping this report focused on the current proposals. Prior proposals and concept versions remain in their round directories; the earlier insurance-focused report is [archived](history/REPORT-round-2-draft.md).

[Verification](verification.json) confirms all 376 insurance-project files remain byte-identical to the initial inventory, with no additions or removals. Review-artifact local links were checked for target existence. No agent implementation, project migration, full link/anchor audit or human usability trial was performed.

External sources, retrieved 13 September 2026: [Spec Kit decomposition](https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md), [Spec Kit scope selection](https://github.com/github/spec-kit/blob/main/docs/guides/monorepo.md), [BMad planning paths](https://docs.bmad-method.org/cs/plan/choose-a-planning-path/), [GPT Researcher](https://github.com/assafelovic/gpt-researcher/blob/main/README.md). They support bounded patterns of scoped work, proportionate artifacts and research runs; they do not prove either proposed business-research structure. [Retrieval notes](external-patterns.md) record that Firecrawl returned HTTP 402 and references came from the already-issued web-search batch.
