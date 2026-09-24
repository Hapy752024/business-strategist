# Strategic positioning implementation plan

6 September 2026. Status: **implemented; offline validation passed; live coaching comparison unavailable**.

Implementation record: added one 49-line conditional shared reference, connected ten existing workflows, extended the existing GTM output and optional strategy record, added focused `business-positioning` routing, and preserved decision/KPI links in reviews. The existing brand handoff now preserves provenance (including legacy aliases), validates its contract, records both source hashes, detects changed/unavailable sources with `--check-sources`, and refuses snapshot overwrites. No new skill, mandatory stage, provider, or dependency was added; existing research was untouched.

Validation: final `bash scripts/validate_setup.sh` passed, including **127 Python tests**, 25 deterministic routing scenarios repeated three times, and 116 structurally valid skill eval cases. Seven coaching cases were added to existing eval files. Changed Python entrypoints compiled, the three changed skill entrypoints passed skill validation, conditional reference wiring was checked, and `git diff --check` passed. These are structural and integration results, not evidence of improved coaching.

Live comparison: attempted the bounded, tool-disabled Claude sample in the sandbox and retried outside it. Both attempts failed before a model response because the configured OAuth session was expired and could not refresh. No before/after coaching result or token-efficiency claim is available. The remaining live check requires refreshing that login; it is not an implementation or source-coverage failure. Broader outstanding work in the earlier plan remains separate.

Implement the six identified improvements: customer priorities, positioning alternatives, operating-model derivation, downstream consequences, alignment across execution, and tests of strategic coherence. This is a bounded extension of the existing business coach; outstanding infrastructure work in [the earlier plan](agent-coach-implementation-plan.md) remains separate.

The intended behavior is: understand the buying situation and alternatives, compare feasible positions, recommend a position with explicit trade-offs, derive the activities needed to deliver it, and test both customer value and business viability. Call it the best-supported hypothesis under current constraints, not the universally optimal strategy. Challenge founder preferences when evidence or delivery economics contradict them, and revise the recommendation when better evidence arrives.

## 1. Establish ownership and conditional routing

Update `config/workflow-routes.json`, relevant entries in `config/skill-catalog.json`, and `.agents/skills/business-strategist/references/{workflow,routing}.md`.

- `business-strategist` routes. `archetype-gtm-strategist` owns business-position selection. `company-operating-system` derives delivery requirements from the selected position. Marketing and branding express that position within their existing scope.
- Route an unresolved business-position choice to GTM; route an operating-model request with an existing position directly to operations. A compound request starts with position selection and proceeds only to the implications requested.
- Preserve marketing-message positioning within marketing, standalone branding within branding, and narrow campaign/cadence requests within their specialists. Reuse explicit intent dispatch; do not add another model-based router or an exhaustive synonym list.
- Apply the general positioning method across business types; load archetype-specific GTM material only where it fits. The consumer-service challenger retains its declared scope and does not become mandatory for B2B work.

Acceptance: routing fixtures distinguish business-position selection, delivery-model design, marketing expression, and standalone brand work. A full GTM deliverable is not required for a focused positioning question.

## 2. Add one shared method and extend the existing output

Add a short, conditionally loaded `references/strategic-positioning.md` (target: at most 100 lines). Wire it from relevant existing workflows, not every skill entrypoint. Update the GTM workflow and section 4 of `.agents/skills/archetype-gtm-strategist/assets/gtm-strategy-template.md`.

The shared method covers:

- In a specific buying situation, distinguish minimum requirements, deciding preferences, and acceptable sacrifices. Separate buyer, user, and payer where relevant. Label inferred priorities and missing evidence.
- When the position is unresolved, compare two or three materially different feasible options against customer value, actual alternatives including doing nothing, relative price, founder capabilities, delivery economics, and exclusions. Recommend one or identify the test needed to choose. Do not invent competing options when the choice is already supported.
- State whom the business will serve, the outcome it will deliver, why the alternative is less suitable, and what the business deliberately will not offer. Explain why the rejected options lost without fabricated scoring precision.
- Trace only consequential operating choices: what each enables, what it constrains, the next decisions it creates, how activities reinforce or conflict with each other, and the cost of reversing commitments.

Extend the existing positioning section with this compact table, using only the rows that change a decision:

| Customer priority and evidence | Promise and exclusion | Operating choice | Consequences and trade-offs | Service, brand and marketing implications | Existing test/KPI reference |
|---|---|---|---|---|---|

Reuse the existing evidence, economics, and experiment sections. For saved execution plans, add an **optional positioning section to the existing** `schemas/strategy-plan.schema.json`; do not create a new schema or per-business positioning document. Store the selected position, decision status, trade-offs, consequential activity choices, evidence references/provenance, and links to existing tests/KPIs. Keep recommendation/selection status separate from evidential support.

`strategy-plan.json` is the authoritative saved decision; the Markdown section presents that decision. A short advisory answer need not create an execution plan. Existing plans without positioning remain valid. Extend `scripts/strategy_review.py` only for structural checks the optional section needs, including unresolved test/KPI references; semantic coherence remains an agent review.

Acceptance: the six improvements fit into the existing strategy output; missing evidence stays missing; a selected hypothesis cannot be mistaken for proven demand.

## 3. Apply the method through existing specialists

Make bounded edits to the following existing `references/workflow.md` files. Replace conflicting instructions rather than appending a second process.

| Skill | Required change |
|---|---|
| `service-customer-perspective-challenger` | Add buying-situation priorities and accepted sacrifices to its current buying-context analysis; synthetic customer voices remain hypotheses. |
| `company-operating-system` | Before designing routines, derive the necessary activities, capabilities, people/technology/partners, capacity, costs, and service boundaries from the promise. Omit irrelevant functions. Return infeasibility to position selection. |
| `startup-business-builder` | Reuse the shared positioning method or selected decision; avoid creating a rival positioning process in the startup plan. |
| `marketing-strategy-builder` | Build offers, proof, messages, and channel choices from the selected position. Surface a material contradiction before proposing a change to that position. |
| `social-digital-marketing-planner` | Carry the selected promise, audience, exclusions, and proof limits into campaign briefs; do not repeat position selection for each campaign. |
| `brand-strategy-director` | For business-linked branding, creative territories express the same business position. A territory may not silently change the segment, service promise, or relative price. Preserve independent brand discovery. |
| `brand-quality-reviewer` | Check the supplied business snapshot against service claims, tone, visual expression, proof, and CTAs. Identify concrete conflicts, not merely stylistic differences. |

GTM and operations attach a customer-outcome measure and the relevant delivery/economic guardrails to the existing KPI and experiment records. Reuse owner, formula, cohort/window, target, review cadence, and stop/change rules. Do not add a KPI per table row or invent thresholds without a basis. At review, state which evidence would invalidate the position and which downstream outputs need reconsideration.

Acceptance: the agent can explain how an operating choice supports the promise and affects acquisition or delivery. It recognizes deliberate sacrifices as valid trade-offs, challenges unsupported combinations, and does not confuse operational efficiency with a differentiated strategy.

## 4. Preserve the decision and its uncertainty in the brand handoff

Update `scripts/brand/build_business_to_brand_handoff.py`, its existing validator if needed, and focused tests in `tests/integration/test_foundation.py`.

Current defect: the builder assigns `evidence_backed` to every nonempty field, regardless of its origin. Correct this as part of the enhancement.

- Read the explicitly selected strategy plan alongside business context when needed, using the existing builder and existing snapshot `positioning` object. Preserve trade-offs, evidence references, uncertainty, and coverage gaps.
- Preserve supplied provenance and check its supporting references. Missing provenance must stay unresolved; founder confirmation is a decision, not proof of customer demand. Mixed-support claims retain their individual labels.
- Record the actual positioning source and its content hash as well as the business-context source. Check that the selected source revision matches before downstream generation/review; if it changed, identify affected outputs and refresh the handoff through the existing workflow.
- Keep archived snapshots immutable and preserve standalone-brand operation. Missing business evidence can support explicitly provisional work; it cannot support a claim of validated positioning.

Acceptance: a fixture follows a hypothetical position from the strategy record through the snapshot without losing exclusions or upgrading confidence. A changed strategy source is detectable. Existing handoff inputs remain supported conservatively.

## 5. Verify wiring, then evaluate coaching

Before editing, capture the scoped baseline and define the cases below. Preserve all unrelated uncommitted changes and existing research outputs.

Add routing cases to `config/routing-evals.json` and executable scenarios in `scripts/run_behavioral_evals.py`. Add substantive cases to the existing relevant skill eval files; their presence alone is not evidence that coaching works.

| Case | Required observed behavior |
|---|---|
| Buyer priorities are mostly inferred | Separate evidence from assumptions; compare feasible positions and select the next uncertainty-reducing test. |
| Founder demands premium customization, instant delivery, and the lowest price with inadequate capacity | Explain the concrete conflict and propose a narrower promise, different price, or a bounded feasibility test. |
| Low price is supported by a narrow service range and customer self-service | Recognize a coherent trade-off; trace support burden, volume requirements, and costly commitments. |
| A business-linked brand territory introduces luxury claims into a budget position | Flag drift, preserve hypothesis labels through the handoff, and recommend a consistent expression. |
| Founder insists despite counter-evidence, then supplies credible new evidence | Resist unsupported pressure, reconsider on evidence, and identify affected operating choices and tests. |
| User requests only ad copy, standalone branding, or a cadence for an existing position | Stay within the request; avoid the full positioning exercise and unrelated references. |

Run focused tests for changed routing, optional strategy fields, KPI/test links, and handoff provenance. Then run `bash scripts/validate_setup.sh` once (it already includes root pytest, offline routing, and eval-structure checks) and `git diff --check`.

Run a small before/after coaching sample with fixed evidence packets on the same available harness/model. Inspect actual outputs against the criteria above. Record reference loads, tool calls, and tokens where observable; compare narrow tasks separately from positioning tasks. If model execution or usage telemetry is unavailable, report that limitation rather than claiming improved behavior or token savings. Do not add a benchmarking framework.

## Scope and completion limits

Implement in the order above; define acceptance cases before changes, then make routing, workflow, and handoff changes together reviewable before final validation. Update existing entrypoint/catalog descriptions only where ownership changed. Keep each `SKILL.md` within the repository's 30-line limit and verify every added reference has a valid conditional load path.

The allowed expansion is one shared runtime reference and one optional section in an existing contract, plus necessary edits to existing workflows, scripts, and tests. No new skill, default panel, mandatory stage, dashboard, provider, dependency, automatic research/branding run, or comprehensive company blueprint. Remove repeated guidance and trim any addition that does not improve a decision or prevent drift.

Completion requires passing structural/route/handoff checks and a clearly reported coaching-evaluation result. Passing offline routing does not establish honest coaching, strategic soundness, cross-harness behavior, or token efficiency. This work does not close unrelated gaps from the earlier infrastructure audit.

Sources informing the design (accessed 6 September 2026; pages undated): customer insight must be connected to differentiated delivery activities ([HBS: Distinctive Value Chain](https://www.isc.hbs.edu/strategy/creating-a-successful-strategy/Pages/distinctive-value-chain.aspx)); positioning also depends on how activities reinforce one another ([HBS: Fit Across the Value Chain](https://www.isc.hbs.edu/strategy/creating-a-successful-strategy/Pages/fit-across-the-value-chain.aspx)). The file ownership, conditional loading, and implementation boundaries above are project design decisions derived from those principles and the repository inspection.
