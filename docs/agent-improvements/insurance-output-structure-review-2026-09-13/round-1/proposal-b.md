# Proposal B — physical research cases inside one insurance umbrella

Round 1, 13 September 2026. Architectural proposal only; no research conclusion is independently revalidated here, and no project content is changed. External-pattern evidence is pending the root research packet.

## Diagnosis from the actual workspace

The problem is more than folder naming. The project currently has one state machine for several hypotheses whose recommendations changed independently.

- `README.md` prepends September follow-ups to an older scorecard and action plan, explicitly warning that earlier recommendations are superseded. Finding the Chinese comparison requires reading through the broader narrative.
- `market_research/manifest.json` has a root cyber-first next action, an English-first `idea_grill.next_action`, and IT-first descriptions in `segment_selection`. `problem_validation` is a conditional pass backfilled during the layout migration, with pain synthesis still outstanding. These are historical observations, not evidence of any individual candidate passing validation.
- `project-manifest.json` has an empty blocker list, while the research manifest has three blockers. A cleaner file tree alone will not reconcile authoritative current state.
- Language, profession, product, delivery mechanism and acquisition channel are mixed. `customer_segments/surelius-and-language-segments.md` itself identifies the useful research unit as decision event × circumstances × language. Register mail is called a channel in the root README.
- `strategy/decisions/2026-09-11-workspace-consolidation-map.md` records the recent merger of Surelius, digital-insurance-agent and self-employed-professionals workspaces. Undoing that merger into unrelated ventures would revive the same fragmentation.

## Core proposal

Keep one venture umbrella, but give each **separately decidable hypothesis a physical research case**. Move its current synthesis and future work into that case. Preserve common research once, with explicit references from cases. A case is an investigation, not a new company or an automatic brand/website workstream.

Create a case when it has a distinct customer/decision hypothesis, evidence assessment or next test that could receive a different decision from another case. Do not create every permutation of language × profession × product. Families are visual groupings; facets can overlap and do not govern permissions.

```text
german-insurance-opportunity/
  README.md                         # sole current umbrella comparison and decision
  project-manifest.json              # venture/workstream controller
  cases.json                        # stable case IDs, labels, facets, locations only
  cases/
    health-decision-english/
      README.md                     # current case dossier; bounded to this case
      market_research/
        manifest.json               # authoritative case stage/gate state
        customer_segments/segment.md
        customer_journey/journey.md
        pain_points/assessment.md    # includes scoped shared-evidence bindings
        pain_points/runs/            # future evidence collected only for this case
        solution_alternatives/
      strategy/
        decisions/                  # dated decisions and supersession records
        experiments/                # only once appropriate; no empty full scaffold
    health-decision-chinese/         # independently assess language delivery/access
    it-professional-and-personal/    # combined relationship hypothesis
    motor-discount-mga/              # investigated implementation, not all discounts
    cyber-insurability-precheck/
    pension-decision-self-employed/
  market_research/
    manifest.json                   # umbrella research state; never grants case gates
    customer_segments/              # genuinely comparative/shared synthesis
    customer_journey/
    pain_points/runs/               # historical runs unchanged; new shared runs
    solution_alternatives/           # common entity/source records
    deep_dives/                     # comparative investigations retained
  strategy/
    decisions/                     # umbrella choices and prior migrations
    economics.csv                  # common founder/operating assumptions
    surelius-personalised-why-and-simulation.md  # cross-case delivery thesis
```

This is deliberately flat beneath `cases/`. English and Chinese can appear grouped under “personal health decisions” in the root comparison without acquiring a parent-child gate dependency. A Chinese-speaking IT consultant can be relevant to two cases without two copies of their source evidence. “Surelius,” Arabic-language delivery and register mail initially remain linked concepts/facets with their own bounded assessment documents, rather than manufactured independent businesses. Inventory all historical candidates, including doctors and 55+, before deciding which deserve a case versus a visible related-investigation entry.

## What the founder sees

The root README starts with all investigated cases in one table: hypothesis, customer/trigger/language, disposition, evidence coverage and limitations, last reviewed date, decisive blocker, next test, dossier link. Historical superseded recommendations leave the main narrative and remain accessible through dated decision links.

Every case README answers the same six questions: What exactly is the idea? Who and which decision does it serve? What did we actually learn? What argues against it? What is its present disposition and why? What would change that decision?

Separate **disposition** (`investigating`, `parked`, `rejected`, `selected-for-test`) from **validation state** (`not_assessed`, `in_progress`, `conditional`, `passed`, `failed`). Selecting a test is not validation. Migrated contradictory recommendations receive `needs_reconciliation`, not an inferred winner. “Motor MGA parked under current budget” must not silently become “all discounted car insurance disproven.”

## Concrete mapping

| Existing material | Proposed treatment |
|---|---|
| `strategy/annex-b-motor-mga.md` and `strategy/intake/ideas/idea-3-motor-mga.md` | Consolidate current scoped interpretation in motor case; retain dated source versions/history and a migration map. |
| `customer_segments/surelius-and-language-segments.md` and `strategy/annex-a-personal-insurance.md` | Keep comparative source document once; derive separately attributed EN/ZH case syntheses with explicit source sections and limits. Do not duplicate entire documents. |
| `customer_journey/self-employment-journeys-it-and-doctors.md` | Retain shared comparison; IT case owns current IT interpretation; doctor investigation remains visible and can become a separate case when separately resumed. |
| `deep_dives/2026-09-11-segment-pain-deep-dive.md` | Preserve dated cross-case analysis; create cyber and relevant health/pension case dossiers pointing to exact supporting sections. |
| `pain_points/idea-*/run-2026-09-06/` and existing `pain_points/runs/*` | Do not relocate frozen runs; bind them to cases with reviewed applicability and contamination limits. |
| June multilingual GTM and app documents | Historical proposed execution, linked to applicable cases; never inherit current approval merely because moved. |
| `strategy/current-recommendation.md` | Historical recommendation; dated supersession record and clear link from umbrella history. |

## Evidence and state contract

`cases.json` contains identity, facets and paths; it does not duplicate stages, blockers or next actions. Each case's research manifest is authoritative for those fields. The umbrella README renders these values; the controller derives aggregate blockers from the relevant manifests. Narrative interpretation stays in the scoped dossier; prior dispositions have dated reasons in `strategy/decisions/` and manifest events.

Raw evidence has one canonical location. A case's pain assessment binds source path + record ID or document section + reviewed date + applicability + known limitations. For immutable source artifacts, store a digest so a changed upstream source requires review; this is not a duplicate raw-data store. A shared market observation is not automatically customer evidence for every language. Thin Chinese-source coverage must remain visible rather than inherit the English case's apparent maturity.

Existing global conditional passes do not seed individual case passes. Case work starts with a factual evidence inventory and explicit reconciliation of its current status. The existing history remains intact.

## Required infrastructure change

This alternative is not compatible with the current agent contract without development. `scripts/evidence_scout/workspace.py` assumes one `market_research/manifest.json` per project; `collect.py` allocates to the project-level pain runs; `scripts/route_workflow.py` binds its pain gate to the project root; `scripts/project_workspace.py` discovers one controller per immediate project directory. `schemas/project-manifest.schema.json` forbids undeclared fields. `references/workspace-lifecycle.md` defines one current root narrative and existing evidence paths.

Add an explicit optional `--case <stable-id>` to a centralized scope resolver used by routing, collection, stage updates and resume. With a case supplied, the selected case's gate is required; no fallback to the umbrella pass. A shared-evidence reference qualifies only through an assessed binding in that case's pain directory. Missing case ID, escaped paths or ambiguous destination fail closed. Existing unscoped projects keep current behavior; once a project has multiple active cases, case-specific commitment requests must identify a case. Update schemas, lifecycle guidance and meaningful regression checks together. This is moderate infrastructure work, not a directory-only migration.

## Nested cases versus linked sibling projects

Sibling slugs such as `german-insurance-english` fit current discovery and gates better and offer immediate full independence. But they present one venture as many projects, duplicate founder context/controllers, invite separate branding prematurely, and make common evidence look external. The previous merger is local evidence against that default. Reserve a sibling project for an explicitly selected venture that now needs its own independent operating lifecycle.

Nested cases better match this umbrella investigation, at the cost of explicit resolver and gate development. Do not claim nesting already works merely because `--out-dir` can create a folder: output destinations alone do not establish scoped stage authority.

## Migration and maintenance tradeoff

Inventory and classify first; capture digests and the current path map because research workspaces are gitignored. Produce a dry-run ownership/move plan, then reconcile status conflicts explicitly. Move only current case-specific syntheses; preserve frozen runs, dated cross-case reports and prior events. Rewrite operational links and manifests using approved migration tooling, validate every destination, and prove rollback from the map. A trial on EN, ZH and motor cases should show the founder can find each conclusion, supporting evidence and next action in two clicks before expanding.

Advantages: strongest physical grouping, independently resumable investigations, clear long-term home for future outputs. Costs: scoped router/schema changes, source-binding discipline, and more authored dossiers. A navigation overlay is faster and lower risk, but its workstream-first write paths can recreate this problem as volume grows. Choose this physical-case architecture when repeated independent follow-ups are expected; choose the overlay when the immediate need is only understanding the existing corpus.
