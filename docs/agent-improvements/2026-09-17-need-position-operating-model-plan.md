# Plan: unmet need → specific promise → operating model → defensibility

Date: 17 September 2026. Status: implementation delivered; see [implementation evidence](need-operating-model/implementation.md). Independent model comparison remains unmeasured. The proposal below is retained as the design baseline.

## Recommendation

Strengthen the existing decision chain rather than create more specialists. The agent should answer four separate questions: is an important outcome inadequately served for a specific group; would that group choose this particular promise over its alternatives; can this founder deliver it economically; and what, if anything, could protect the resulting advantage?

“Optimal” means the best-supported feasible configuration for the chosen customer outcome, constraints and horizon—not a provably global optimum. A plausible business can have no durable moat. Conversely, an elegant operating system can serve an outcome customers do not value. Preserve these possible conclusions.

The supplied business-model catalogue is useful as conditional design inspiration, not a ranking or mandatory checklist. Distinguish monetization, delivery economics, financing, capital allocation and defensibility. Do not convert twenty examples and ten overlapping moat categories into thirty scored fields.

## Current implementation and actual gaps

Live inspection found substantial existing foundations:

- `references/strategic-positioning.md` already covers buying situations, feasible positions, exclusions, entrant feasibility, activity consequences, economics and provenance.
- `references/voc-research-method.md` already requires topic-led and entity-led research, non-adoption, successful journeys, contrary cases, and source-linked experiences. Retain this stronger local evidence machinery.
- `archetype-gtm-strategist` owns business-position selection. `company-operating-system` owns delivery implications. `opportunity-risk-designer` already supports provisional case appraisal.
- `schemas/strategy-plan.schema.json` has an optional positioning object and activity rows. `scripts/strategy_review.py` checks experiment/KPI links, preserves the positioning object, and detects changes against a baseline.
- `docs/strategic-positioning-implementation-plan.md` already described much of this architecture. This plan extends it; it must not reimplement completed work.

The gaps are narrower: latent-need inference needs an explicit falsification test; the promise needs a sharper link to customer choice; activity rows lack explicit relationships and imitation analysis; operations entrypoint success criteria still emphasize cadence and KPIs. Route `company-operations` covers both delivery design and management routines without an explicit mode distinction. No structured defensibility assessment currently appears in the inspected positioning contract.

The working tree contains extensive existing changes, including relevant skills. Implementation must capture the current scoped baseline and layer on top of it without restoring or overwriting unrelated work.

## What to take from the requested video

Retrieved and read the English caption transcript of [the supplied video](https://www.youtube.com/watch?v=9fueVTU3Cig) on 17 September 2026: 1,235 segments, approximately 43:44. Captions contain transcription errors, especially around “Piton.” The author's [Piton essay](https://www.speedwellmemos.com/p/the-piton-network-decisions-that) and [meta-optimization essay](https://www.speedwellmemos.com/p/meta-optimizations-knowing-when-a) clarify the terminology.

Useful passages: approximately 07:50–10:40 compares designing around existing assets with reconsidering the assets themselves; 10:40–13:50 traces interdependent Costco choices; 25:10–29:40 illustrates cascading delivery choices through Square; 33:20 onward reconnects customer preferences, the proposition and the operating configuration.

Translate that into plain operational questions: what does each choice enable, constrain and force next; which choices reinforce or conflict; what would change in a clean-sheet design; and can the transition be financed? Keep the metaphor as an attributed reference, not a new agent vocabulary or subsystem.

Do not import the video's strongest claims as laws. One primary aim can coexist with several minimum service constraints. Existing assets may provide useful economies as well as constrain change. A faster operation is not necessarily a better business. The Netflix account compresses the distinction between separating services and ending DVD operations: Netflix's own announcement dates the final DVD shipments to September 2023. Treat company stories as explanatory hypotheses unless independently verified. [Netflix announcement](https://about.netflix.com/en/news/netflix-dvd-the-final-season).

## Target behavior

### 1. Diagnose an underserved outcome without presupposing an opportunity

For each candidate, identify segment by situation and constraints, user/buyer/payer, job and trigger, desired outcome, actual workaround or alternative, shortfall and consequence, and why existing provision falls short. Include doing nothing, informal help and internal work.

Separate four cases: dissatisfied users of existing offers; nonconsumers blocked by cost/access/time/skill; customers paying for unwanted complexity who might accept a narrower offer; and customers already adequately served. These are sampling lenses, not four mandatory studies. Nonconsumption barriers are a useful discovery frame from the [Christensen Institute](https://www.christenseninstitute.org/blog/to-build-a-new-market-overcome-these-4-barriers/).

“Latent need” means an inferred unmet outcome supported by observed behavior or consequences; it does not mean hidden demand that the model is permitted to invent. Retain observation → interpretation → competing explanation → disconfirming test. Adaptation or silence can conceal a shortfall, but can also indicate low urgency. A workaround is not automatically evidence that customers will switch or pay.

Assess importance and satisfaction separately, following the useful distinction in [Strategyn's method](https://strategyn.com/outcome-driven-innovation/). Do not compute opportunity scores from scraped mentions or invented survey ratings. Public-source frequency is not segment prevalence. Preserve `insufficient_evidence` as distinct from evidence of adequate service.

### 2. Specify a customer choice hypothesis

Use one concise contract:

> For [segment in situation], improve [outcome versus current alternative] through [delivery mechanism], within [price/effort/time/risk boundaries], accepting [explicit sacrifices].

Record minimum requirements separately from deciding preferences. Explain why the promised improvement is sufficient to overcome switching effort, trust requirements and acquisition friction. Quantify only where evidence supports it; otherwise state the measurement needed. The [Value Proposition Canvas](https://www.strategyzer.com/library/the-value-proposition-canvas) provides a useful job-to-offer linkage, but a filled canvas does not validate choice.

Compare materially different propositions only when unresolved. A specific proposition is testable; “better service using AI” is not. Use existing interview and experiment records to test recent behavior, alternative choice, permitted commitments and observed outcomes. Continue unpaid recruitment and existing authorization boundaries.

### 3. Compare feasible operating configurations

Operations first derives the work needed to fulfil the promise, before meetings or dashboards. Consider only relevant processes, people/organization, locations/assets, information, suppliers and management controls—the [Operating Model Canvas](https://operatingmodelcanvas.com/) offers a compact coverage check.

Where the choice matters, compare current/available assets, a clean-sheet target, and a feasible transition. A startup need not invent a fictional current operation. Show which constraints are hard, which can change, and at what cost. Do not prescribe the capital-intensive target simply because it optimizes one service metric.

For consequential activities capture: customer outcome served; build/buy/partner/manual choice; enabling effect; constraint/exclusion; reinforcing or conflicting activities; bottleneck/capacity; economics and risk; transition/reversal cost; and evidence or test reference. Do not force every field into every row or create a KPI per activity.

Evaluate contribution after service and acquisition labor, fixed costs, utilization or density where relevant, working capital, early cash needs, and downside. Reuse case economics helpers. Distinguish viability at entry scale from advantages requiring later scale. A promise that fails delivery or economics returns to positioning for revision.

Use a small activity diagram only when relationships are clearer visually. Porter's [activity-fit explanation](https://www.isc.hbs.edu/strategy/creating-a-successful-strategy/Pages/fit-across-the-value-chain.aspx) is the conceptual basis; a Wardley evolution map answers a different build/buy question and is optional.

### 4. Assess a defensibility hypothesis, not a moat label

For each material claimed advantage state: economic benefit; imitation barrier; beneficiary who captures value; evidence; establishment time and investment; competent competitor response; erosion conditions; next falsification test. Test both an incumbent and a new entrant. Incumbent cannibalization does not prevent another startup copying.

Use `not_assessed`, `none_identified`, `hypothesis`, `emerging`, or `supported` as assessment maturity; retain evidence provenance separately. “Supported” remains scoped to a market and date and never means permanent. Separate this status from founder selection and problem validation.

Reuse the user's benefit-plus-barrier discipline and [Helmer's persistent differential-return framing](https://7powers.com/). Avoid additive scores across overlapping mechanisms. Recurring billing, working capital, AI, accumulated data, high margins and execution quality do not individually demonstrate a barrier. Data requires an evidenced improvement loop and access/replication limits. Distribution analysis must include dependence and bargaining power.

For early ventures, assess the path from entry advantage to a potentially defensible position; do not demand historical ROIC from a pre-revenue company. For established businesses with usable data, examine sustained and incremental capital returns, reinvestment needs and who captures the surplus. A profitable small business with limited defensibility can still satisfy the founder's objective; report the exposure candidly.

## Ownership and bounded edits

All skill paths below are under `.agents/skills/`. Prefer replacement and deduplication over appended procedures.

| Owner/files | Planned adjustment |
|---|---|
| `market-problem-discovery/{SKILL.md,references/workflow.md}` | Make underserved-outcome and nonconsumption hypotheses explicit in existing candidate outputs; distinguish adequately served from insufficient evidence. |
| `evidence-scout/references/workflow.md`, `references/voc-research-method.md` | Add the latent-need falsification rule and outcome comparisons to the existing synthesis; reuse experience IDs, U-needs, R-requirements and contrary cases. |
| `idea-grill/references/workflow.md` | Separate need, proposed promise, entry feasibility and defensibility assumptions; do not require founders to assert a moat. |
| `archetype-gtm-strategist/{SKILL.md,references/workflow.md}`, `references/strategic-positioning.md` | Own proposition/position choice, exclusions and defensibility assessment; incorporate customer-choice, imitation and value-capture tests. |
| `company-operating-system/{SKILL.md,references/workflow.md}` | Explicit delivery-design versus cadence modes; outcome-derived configuration and transition first in delivery mode; stage-appropriate success criteria replacing tool-call quotas. |
| `opportunity-risk-designer/references/workflow.md`, `references/case-assessment.md` | Reuse current appraisal sections for provisional proposition/operating/defensibility hypotheses; link the riskiest assumptions to existing tests. |
| `startup-business-builder` and `marketing-strategy-builder` workflows | Consume the selected decision and its uncertainty; revise only conflicting handoff instructions. No new parallel framework. |
| `business-archetype-playbook-researcher` workflow | Retrieve relevant operating mechanisms, failed analogues and limits of transfer; do not treat successful companies as proof of demand or copy their full business models. |
| `config/workflow-routes.json`, `config/skill-catalog.json`, router references | Preserve skill IDs. Add an explicit delivery mode/route only if required to distinguish it reliably from cadence; preserve existing `company-operations` compatibility. |
| `schemas/strategy-plan.schema.json`, `scripts/strategy_review.py`, existing templates/tests | Make only the optional contract extensions below; retain legacy acceptance and frozen baselines. |

No new skill is warranted. Discovery, evidence synthesis, proposition selection, delivery design and risk tests already have owners. Branding and standalone website work retain their independent scopes.

## Records, gates and handoffs

Before the pain gate, place provisional analysis in existing discovery/case artifacts through their authorized publication paths. `case-appraisal` remains an appraisal route, not an execution bypass. Do not start a selected strategy plan or call business-positioning just to store a hypothesis. After validation/explicit override and applicable case selection, the existing selected `strategy-plan.json` remains execution authority. Proposed analytical labels do not create new lifecycle stages or automatically pass existing gates.

Extend the existing optional `positioning` object only where downstream checking needs structured fields:

- Optional `need_refs` and `value_proposition` link reviewed needs to the promised outcome, alternative, mechanism and sacrifices, retaining per-claim provenance.
- Optional activity `id` and typed relations (`requires`, `reinforces`, `conflicts_with`) support a compact map. Require IDs only when relationships reference them; legacy rows remain valid. Reinforcement cycles are legitimate; do not impose a generic acyclic-graph rule.
- Optional `defensibility` stores assessment status and bounded benefit/barrier hypotheses linked to activities, evidence and existing tests. `none_identified` with an explanation is a valid result.

Keep economics, experiment definitions and KPI definitions in their current owners; reference rather than duplicate them. Do not create separate operating-model, moat or framework databases. Prefer prose in current case documents when machine consumers do not need a new field.

Extend validation for schema shape, dangling references, duplicate activity IDs and preservation through current publication/handoff paths. Preserve changed-position detection and immutable snapshots. Missing fields in old plans must not acquire invented proof. Validators cannot establish semantic customer fit or prove a moat; explicit unresolved findings belong in human-readable review, not a fake automated truth score.

Implementation must verify the existing brand snapshot reader's handling of these optional fields before choosing whether any adapter changes are necessary. Preserve the evidence status in any business-linked claims; standalone branding does not inherit new Business gates.

## Open-source reuse decisions

These are source inspections, not executed compatibility/security benchmarks. Pin a reviewed commit and retain applicable license notices before copying anything. Repository popularity is not quality evidence.

| Candidate | Checked implementation and license | Decision |
|---|---|---|
| [lowwwbank/interview-to-jtbd](https://github.com/lowwwbank/interview-to-jtbd) | Read README and actual `SKILL.md`; MIT. Evidence-linked jobs, workarounds and opportunity synthesis. | Adapt a concise extraction/checking pattern if it adds something missing. Do not install another research skill or reproduce its multiple default deliverables; local source/experience tracking is already stronger. |
| [haberlah/wardley-mapping](https://github.com/haberlah/wardley-mapping) | README describes OWM parser and validator, build/buy analysis and React output; code/skill MIT, framework-derived materials CC BY-SA 4.0. Direct validator retrieval failed, so executable behavior is unverified. | Defer scripts and UI. Potential optional syntax reference for a demonstrated complex build/buy need. Its advertised cycle prohibition must not be applied to reinforcing activity systems. |
| [damonsk/onlinewardleymaps](https://github.com/damonsk/onlinewardleymaps) | Repository/README show MIT application, text maps, frontend and optional storage API; framework attribution is separate. | Optional external rendering format/reference. Do not embed or host an application to support a compact strategy table. |

Recommended initial runtime dependency increase: zero. The strongest reuse is the existing local evidence ledger, strategy schema, case publication helper and evaluation harness. Do not introduce an agent framework, vector database, full ontology, graph service, optimization solver or automatic review panel.

## Implementation sequence and acceptance

1. **Baseline and fixtures.** Record scoped diffs, route behavior and reference-load sizes. Define the behavioral cases below before edits. Preserve existing research and prior uncommitted work.
2. **Improve reasoning in existing references.** Update need synthesis, proposition choice, operating-design mode and defensibility test. Keep general logic in the existing shared positioning/VOC references; reserve at most one short conditional operating-design reference if splitting genuinely reduces default context.
3. **Wire minimum records and routes.** Add optional fields only where the fixtures demonstrate a persistence need. Test legacy plans, provisional appraisal, selected execution, source uncertainty and downstream preservation together.
4. **Evaluate and simplify.** Run deterministic checks, then paired before/after outputs on fixed evidence packets using the same model/harness. Inspect actual decisions and unsupported claims. Remove added instructions that do not improve a decision or prevent a demonstrated failure.

| Behavioral case | Required result |
|---|---|
| Many complaints, no consequence or switching evidence | No underserved-demand conclusion; explicit unresolved urgency/choice test. |
| Little public discussion, costly observed workaround | Plausible latent-need hypothesis with alternatives and falsification; no invented prevalence. |
| Nonconsumer blocked by access but not interested when access improves | Revise or reject that opportunity explanation. |
| Existing offer satisfies the job | Acknowledge adequate service; no manufactured white space. |
| Overserved customer accepts fewer features for lower cost | Recognize a viable narrower proposition when evidence and delivery economics support it. |
| Low price + custom service + instant delivery | Identify actual capacity/cost conflict; allow a supported novel configuration rather than mechanically declaring impossibility. |
| Clean-sheet delivery beats existing assets on speed but consumes unavailable capital | Select feasible transition/test or reject; no “optimal” fantasy. |
| Subscription or AI dataset presented as moat | Require benefit and imitation barrier; report none/hypothesis if unsupported. |
| Incumbent cannot copy without cannibalization | Still assess a new entrant and the incumbent's possible separate unit. |
| Reinforcing activity cycle | Accept meaningful reinforcement; reject dangling IDs, not cycles by default. |
| Profitable small service without durable barrier | Judge against founder goals; disclose vulnerability without automatic rejection. |
| Need appears strong but proposition-choice test fails | Keep need evidence, revise the promise; do not downgrade all evidence or continue unchanged. |
| Pre-gate appraisal, legacy plan, ad-copy-only, cadence-only, standalone brand | Preserve scope, backwards compatibility and existing gates. |

Structural checks: focused pytest for changed contracts/router/handoffs, `python3 scripts/validate_skill_routes.py`, `python3 scripts/run_evals.py`, `bash scripts/validate_setup.sh`, and scoped `git diff --check`. Avoid redundant reruns when setup already covers a check. Baseline failures must be separated from introduced failures.

Behavioral acceptance: no unsupported need/choice/moat promotion in the critical negative cases; outcomes trace to evidence and material operating choices; infeasibility returns to the correct prior decision; narrow tasks do not load the expanded workflow. Report model, packet revisions, actual outputs, failures and coverage. File/schema checks alone do not prove better strategy.

Bloat acceptance: zero new skills, providers or runtime dependencies; no new default stages or reports; no whole-framework import; optional maps only; narrow-route context must not grow. Measure loaded reference bytes/tokens where available, not just total repository lines. Broader strategy context growth requires an observed decision-quality benefit. Claim token savings only with measurements.

## Source register

All sources accessed 17 September 2026. Framework sources inform method, not proof that any venture has demand. Repository sources inform reuse candidates, not verified execution quality.

- [Requested YouTube video](https://www.youtube.com/watch?v=9fueVTU3Cig): English captions retrieved through `youtube_transcript_api`; publication date not verified. Raw capture kept locally in ignored `.firecrawl/need-operating-model-video-transcript.json`.
- [Speedwell: The Piton Network](https://www.speedwellmemos.com/p/the-piton-network-decisions-that): primary author explanation; publication date not transcribed in this audit.
- [Speedwell: Meta-Optimizations](https://www.speedwellmemos.com/p/meta-optimizations-knowing-when-a): 2 February 2024.
- [Operating Model Canvas](https://operatingmodelcanvas.com/): author site; book published 15 March 2017. Retrieved with web browsing and configured HGINVESTOR Firecrawl.
- [HBS: Fit Across the Value Chain](https://www.isc.hbs.edu/strategy/creating-a-successful-strategy/Pages/fit-across-the-value-chain.aspx): undated.
- [Strategyn: Outcome-Driven Innovation](https://strategyn.com/outcome-driven-innovation/): undated; methodology-provider claims are not independently verified success rates.
- [Christensen Institute: Four barriers](https://www.christenseninstitute.org/blog/to-build-a-new-market-overcome-these-4-barriers/): 19 December 2019.
- [Strategyzer: Value Proposition Canvas](https://www.strategyzer.com/library/the-value-proposition-canvas): undated; conceptual reuse, no copied proprietary template proposed.
- [Hamilton Helmer: 7 Powers](https://7powers.com/): undated author site.
- [Netflix: DVD—The Final Season](https://about.netflix.com/en/news/netflix-dvd-the-final-season): 18 April 2023.
- [interview-to-jtbd](https://github.com/lowwwbank/interview-to-jtbd), [actual skill](https://raw.githubusercontent.com/lowwwbank/interview-to-jtbd/main/SKILL.md), [Wardley skill](https://github.com/haberlah/wardley-mapping), [OnlineWardleyMaps](https://github.com/damonsk/onlinewardleymaps): live repository inspection; exact revisions not pinned because no code is being adopted in this planning task.
