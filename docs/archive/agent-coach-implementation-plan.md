# Agent and business-coach implementation plan

Updated: 8 September 2026. **Post-review setup safety, opt-in bootstrap and outcome-first routing corrections implemented.** Live behavioral/cost validation remains unverified; the last attempt failed on expired Claude OAuth. Earlier revisions and their limits are preserved below.

## Post-review corrections — 8 September 2026

The prior green tests missed real failures: a dry-run executed a target sync script; bootstrap followed an external scripts-directory symlink; strategy components downgraded scope; independent-request routing varied with punctuation; and integrations remained compulsory. The first two were reproduced with harmless temporary-directory marker/escape fixtures before implementation. The original implementation was not safety-complete.

Replaced duplicated shell implementation with four thin entrypoints and one trusted bundled Python implementation. Isolated Python ignores target/PYTHONPATH modules; destination sync scripts are never executed. Audit/rendering use the bundled renderer and destination JSON as data. Preflight rejects external/internal/dangling links, unsafe ancestors, special files and output-type conflicts before mutation; writes are rechecked and atomic. The canonical internal Claude skills link is the only symlink exception. This assumes a stable owner-controlled target, not a hostile concurrent filesystem mutator. Unsupported MCP transports fail explicitly rather than losing configuration.

Bootstrap now creates only AGENTS.md by default. Independent `--harness claude|codex|opencode` options and separate `--mcp` opt-in select integrations; no sync script is copied or executed. The obsolete target.sh parser was removed as part of consolidation; the prior implementation is recoverable from `/tmp/strategist-p1-baseline.aWmcg4/` and repository history where tracked. Existing project research and assets were not modified by this correction.

Routing now prioritizes the requested strategy outcome over execution components. Include/with clauses belong to the parent outcome; separate action requests joined by punctuation, and, or then require resolution. Explicit caller scope remains authoritative. Added transfer and adversarial cases in `tests/test_setup_safety_and_scope.py`; the fallback remains deliberately bounded, not a general natural-language parser.

Validation: **198 Python tests passed**, including **47 new adversarial/transfer cases** with dry and non-dry entrypoints and hostile target/PYTHONPATH modules. Setup validation, all 25 existing offline routing scenarios, skill structure checks and `git diff --check` passed. These are local code/contract checks, not live model-quality or cost measurements.

## Current repair — proportional work and relocated projects

Implementation uses existing specialists, router, workspace helpers and test runners. No new skill, mandatory review agent or orchestration framework.

- **Workspace paths:** research creation/discovery, legacy-layout outputs, API-validation/provider-status paths, event output, brand defaults, templates, source references and compaction hooks now use `projects/research/` or `projects/brand-projects/`. Controller manifests remain `projects/<slug>/project-manifest.json`; the two container names are reserved. Old explicit creation paths are rejected with relocation guidance rather than silently recreating root folders.
- **Routing:** explicit intent is authoritative; active state is used only for continuation without a new routed action. A conservative phrase fallback handles common exclusions and punctuation; it is not a general language parser. The calling agent supplies semantic intent/scope for complex requests. Separate requested workflows require resolution before dispatch; packets keep route, skill and artifacts aligned.
- **Scope/loading:** shared `references/task-scope.md` distinguishes focused, execution and strategy independently of response length. Marketing copy and social execution bypass full strategy references; paid-social execution has one short task reference. New factual claims and external-action approvals retain their safeguards. Full strategies still use their detailed workflow.
- **Pruning:** removed the duplicated root specialist catalog and shared rules from the Claude shim; capability metadata and specialist pipeline rules remain canonical. Updated tests that incorrectly required duplicate root prose. AGENTS.md plus CLAUDE.md decreased from 15,865 to 12,624 bytes (20.4%). This is a file-byte measurement, not measured runtime tokens or billing savings.
- **Setup:** setup/bootstrap/audit/repair share validated `--target` parsing, default to the caller directory, print the resolved target and reject root/home/missing targets. Dispatch preserves the target. Bootstrap no longer assumes a stack, review agents or code-graph dependency; dry-run and existing-content preservation remain tested.
- **Benchmark:** the component-count criterion is replaced by identity/research/asset/app/website route availability. A consolidation fixture proves one implementation may serve all five capabilities. This remains structural coverage, not proof of design quality.

### Preservation and validation record

Pre-change code/instruction snapshot: `/tmp/strategist-scope-baseline.oltI5A/` (temporary local recovery aid, not a durable release). Existing dirty-worktree changes were retained. Four reproduced fallback probes fail in that snapshot and route to the requested scope after repair. All 25 existing offline routing scenarios pass. Python suite: **151 passed**; setup validation and **143 evaluation-definition structure checks** pass. Setup regression tests cover targets with spaces, cross-directory invocation, broad/missing-target rejection, dry-run, repeat bootstrap and audit. These are deterministic checks, not model evaluation.

Five relocated research manifests are discoverable. Repaired two brand `business_to_brand` links and five website `brand_refs`; all repaired targets resolve. Repaired the insurance executive README's relative link to the agent plan. The three changed manifests differ only in operational links and revision/date metadata; all other fields, including approvals and stages, were compared with the saved copies and preserved. No raw evidence, frozen run record, generated asset or historical research narrative was rewritten. No directories were moved again.

Live smoke attempt: `claude -p --tools '' --no-session-persistence --output-format json` on a supplied fictional two-copy task failed before inference: **Failed to authenticate: OAuth session expired and could not be refreshed**. Reported input/output tokens and cost were zero. No paired live comparison, observed task-loading reduction or model-quality improvement is claimed. Owner action: restore Claude authentication; then run baseline/candidate fixtures in clean same-model sessions, capture actual loaded references, tokens/cache usage, tools, elapsed time, artifacts and billing data, and prune only where quality is maintained. The remaining live gate is not waived by passing tests.

---

Start with the focused revision below. The broader [agent/strategy audit](audits/2026-09-05-agent-strategy-review.md) remains background backlog; this revision does not authorise restarting it. Preserve existing research and uncommitted work.

## Focused revision — 6 September 2026: better decisions with less machinery

**Status: A/B instructions and C new-workspace/lifecycle conventions implemented; D live validation incomplete.** This section is the current entry point for the founder-intake, recommendation, acquisition and document-usability improvements requested on 6 September. It narrows and updates P4–P6 below; it does not restart completed work or require unrelated P1–P3 infrastructure work. Preserve the existing dirty worktree. The earlier implementation record remains historical evidence, not proof that these new behaviours work.

Review corrections: removed missing-evidence KILL rules and mandatory strong-moat assumptions; connected comparable evidence coverage and founder context to discovery; aligned AGENTS/Claude resume instructions; added executive-document lifecycle and migration safeguards. Existing research topics were not migrated by this agent-infrastructure review. The 16 coaching fixtures now cover the planned scenarios, including four transfer cases; fixture structure is not model performance.

Validation: setup and Python suite passed, including a new resume test that checks local links, one root narrative, and byte-for-byte preservation of README, state and evidence. A tool-disabled Claude fixture smoke test was attempted and failed before inference with `Failed to authenticate: OAuth session expired and could not be refreshed` (zero model tokens). No paired baseline/candidate comparison or live behavioural pass is claimed. Repair authentication and run the stored fixtures in clean sessions to complete D; the original pre-implementation conversation baseline was not captured, so do not claim retrospective improvement against it.

### Outcome and scope

The agent should understand the decision-maker, compare viable alternatives from several relevant angles, assess economic entry and customer relationships, then recommend the smallest useful next decision. Business ambition, founder role, language, industry, channel preferences, budget and timeframe are runtime inputs. Insurance names, geography and pilot numbers belong only in optional examples or regression fixtures.

Keep the existing orchestrator, specialist skills, manifests, strategy schema and test infrastructure. Add **no specialist skill, mandatory panel, orchestration framework, database, dashboard or automatic deep-dive-per-question rule**. Multiple analytical perspectives are checks in one workflow; extra agents are optional only when a separately justified task warrants them. Replace conflicting instructions instead of accumulating caveats.

### Evidence and reproduced gaps

| Finding in the current checkout | Required correction |
|---|---|
| `idea-grill/references/workflow.md` and `templates/research-topic/startup-thesis.md` focus on business/customer inputs; founder preferences are incomplete | Establish decision context before significant opportunity-ranking research |
| `social-media-idea-validator/references/workflow.md` Gate 4 asks what incumbents are not covering; missing demand can cause KILL; a few posts can trigger rejection | Assess feasible entry and customer choice; distinguish missing evidence, failed exposure and negative response |
| Founder-format fit follows audience research; immediate conversion receives more emphasis than relationship formation | Bring founder capability forward; assess discovery, repeat engagement, trust and eventual purchase separately |
| Shared strategic-positioning rules already exist, but specialist paths differ | Strengthen one shared contract and route relevant owners to it; do not reproduce it in every skill |
| `scripts/run_behavioral_evals.py` invokes the router, not an LLM, and explicitly labels that limitation | Retain offline checks and add actual conversation trials; do not call routing success improved coaching |
| Topic README is a scope listing, while numerous narrative outputs accumulate at the root | Make README the complete executive document; put supporting narratives under deep-dives |

### Implementation sequence

Implement A before B/C, then D. Capture the baseline before any instruction changes. Each change set has an observable acceptance condition.

| Phase | Minimal changes | Acceptance |
|---|---|---|
| A. Founder context and recommendation discipline | Extend existing intake/template and shared positioning reference; thin links from relevant workflows | Agent asks only missing decision-changing questions, respects supplied answers and constraints, compares before selecting, and can return insufficient evidence |
| B. Economic entry, acquisition and relationships | Replace novelty/KILL language in existing risk/social workflows; extend existing GTM channel table | Proposal explains how an entrant gets discovered, why suitable people return/trust/choose it, full costs and a test suited to the buying cycle |
| C. One executive document | Update README template and writer/lifecycle conventions; minimal path handling only where needed | One current reader-facing document at root, linked deep dives, no contradictory current recommendations, old evidence preserved |
| D. Verify and prune | Reuse skill eval files and existing validation; conduct paired conversation trials | Transfer cases pass, no hard constraint/source failures, simple requests stay simple, costs and file output do not grow without justified benefit |

### A — Founder context and comparison

**Owners/files:** `AGENTS.md` and mirrored `CLAUDE.md` only for concise routing/precedence; `references/strategic-positioning.md` for the shared decision contract; `templates/research-topic/startup-thesis.md` for captured context; existing business-strategist, idea-grill, market-problem-discovery and opportunity-risk-designer workflows for role-specific links/corrections.

1. Reuse the conversation and active workspace before asking. Capture objectives and ambition, desired role, resources/capabilities/access, affordable downside, income/time horizon and acceptable acquisition/operating arrangements. Distinguish a hard constraint from a preference, an assumption and an unresolved input.
2. Ask a short decision-changing question when needed; do not enforce a fixed questionnaire length or approval after every answer. Founder preferences come from the founder, not web research. Cheap discovery can continue where it does not depend on the answer. Broad exploration does not require the user to invent a customer pain in advance.
3. For opportunity selection, compare viable alternatives on customer need/current behaviour, feasible entry/customer choice, acquisition/relationships, delivery/dependencies, cash/contribution and founder fit. Apply only relevant lenses. A factual question or fixed-scope execution request bypasses this comparison.
4. Give shortlisted alternatives a comparable initial evidence pass; report differences in research coverage. Do not equate repeated public complaints with market prevalence or give the most-researched option an automatic advantage. A demonstrated hard incompatibility may justify early elimination.
5. Prioritise the important assumption with the weakest support. Clearly distinguish a hypothesis worth investigating, a bounded test and an investment commitment. Preserve `insufficient_evidence`; no forced winner, invented numerical precision or universal minimum source count.
6. On a new fact/preference, identify the affected assumption and downstream decision. Explain why the ranking changes, or why it does not. Do not automatically favour the last segment mentioned.

**State:** use existing intake for founder context, existing strategy record for verdict/position/experiments, and manifest events for recommendation changes. Do not add a parallel decision database. Initially keep richer comparison reasoning in the executive document. Add optional schema fields only if an actual consumer or automated invariant requires them; preserve old records. No new mandatory strategy plan for a short answer.

**Acceptance examples:** a fully specified brief triggers no redundant intake; an unclear desired operating role triggers clarification before ranking; a narrow competitor lookup does not trigger a founder interview; a preference update changes only affected analysis.

### B — Economic entry and social relationships

**Owners/files:** `archetype-gtm-strategist/references/workflow.md` and its existing strategy template own the overall motion; `social-media-idea-validator/references/workflow.md` owns channel feasibility; `social-digital-marketing-planner/references/workflow.md` owns execution. Revise the risk designer's compulsory whitespace step into an optional coverage instrument. Use the existing evidence registry for shared evidence limits.

**Economic entry question:** can this founder acquire and serve enough suitable customers at acceptable cost and risk, given the alternatives? Include reasons to switch, first-time category buyers and existing relationships where relevant. Novelty and moats matter in proportion to the business's ambition and competitive exposure; they are not universal prerequisites. Several modest advantages may jointly support customer choice. Existing suppliers prove supply, not saturation. No visible supplier proves neither demand nor an opportunity.

For each proposed primary route, fill one existing channel table with:
- specific audience and buying context;
- discovery mechanism for an unknown entrant and supporting evidence;
- recurring reason to engage and credible human/brand voice where relevant;
- progression to enquiry, trial, purchase and subsequent service;
- founder capability, cash, labour, time-to-learn and dependencies;
- decisive unknown and a bounded test with predeclared interpretation.

**Explicit relationship question:** can an entrant become a familiar, useful and trusted source to the target segment before a buying event? Evaluate both current buyers and future buyers. Examine recurring audience concerns, the ability to answer and respond consistently, existing audience relationships, and room to earn attention. A narrow buying trigger may be appropriate for conversion but too narrow to sustain a relationship; test a broader relevant editorial promise without assuming every follower is a prospect.

Use three separate evidence layers in the same table, not three new systems:

| Layer | Suitable evidence | What it cannot establish alone |
|---|---|---|
| Discovery | Relevant exposure, customer-reported discovery paths, search/question activity | Trust or future sales |
| Relationship | Returning relevant viewers, substantive repeat questions, voluntary follow-up, customers' reasons for trusting/returning | Purchases or positive contribution |
| Business | Qualified enquiries, purchases, delivered outcomes and retained contribution | Causal incremental impact without a suitable comparison |

Repeat engagement is a proxy, not a trust score. Do not claim to identify individual cross-platform viewers from aggregate data. A credible public voice can be the founder, an employee or the brand; do not universally require a founder on camera. Measure response/moderation workload. Do not automatically create a community, influencer partnership or another channel.

Treat content-as-acquisition, content-as-relationship and content-as-sales-support as different candidate roles. The last interaction being a call does not mean social failed to acquire the customer. Conversely, self-reported video discovery is not an audited CAC or incrementality estimate. Count paid and organic separately; a paid boost cannot pass an organic feasibility test.

Backsolve required prospects/traffic from the founder's economics using explicit ranges and unknowns. Organic includes production, response and founder time. Set relationship-learning and commercial deadlines separately against runway and purchase cycle. Do not use a universal one-week/five-post KILL rule. Low exposure is an access result; relevant exposure with repeated rejection is different evidence. Avoid both premature rejection and indefinite content production justified by vanity metrics.

**Acceptance:** tests cover immediate-intent acquisition and relationship formation for a longer purchase cycle; provider failure cannot become absent demand; a crowded local service can remain feasible; a technically novel product can be unattractive because customers cannot be reached economically.

### C — One executive document and bounded detail

**Owners/files:** `templates/research-topic/README.md`, `references/workspace-lifecycle.md`, `scripts/evidence_scout/workspace.py` and affected narrative-writing references. Existing evidence/run outputs retain their authority.

Target reader layout:

```text
topic/
  README.md                 # complete current executive document
  deep-dives/               # supporting narratives, created only when useful
  evidence/                 # existing evidence storage
  decisions/                # existing dated decision history
  manifest.json             # existing machine state
  strategy-plan.json        # existing canonical plan, when applicable
```

“One document in the folder” means one reader-facing narrative at root. Preserve existing machine-state paths initially to avoid unrelated migrations. Additional existing run/raw folders may remain; they are not alternate executive reports.

README should contain: current status and date; founder objectives/constraints; options and material trade-offs; recommendation with evidence strength; why/why not alternatives; acquisition/relationship feasibility; decisive unknowns and next bounded action; direct links to sources and relevant deep dives. It must be understandable without opening an annex. Use detail proportional to the decision, not a fixed page quota.

Update relevant sections after follow-ups. Do not generate another latest memo for every question. Use one brief change note plus dated history for material reversals. Link player names to verified websites in the narrative or a linked directory; unavailable addresses remain explicit gaps.

For existing workspaces, inventory before moving. Consolidate current content into README; move supporting *narratives* into deep-dives, update inbound/relative links and manifest references, and retain historical wording in history. Leave frozen evidence and experiment baselines byte-for-byte unchanged. Validate the migration map before completing; do not recursively reorganise raw data or unrelated projects. New workspace behaviour comes first; migrate active workspaces explicitly and reversibly.

**Acceptance:** one root reader-facing Markdown document for a migrated/new fixture; all local links and manifest targets resolve; README agrees with current strategy verdict; source records/baselines unchanged; a continued session resumes from existing state without creating a duplicate workspace or demanding already-given choices.

### D — Verification, rollout and bloat control

Baseline first: snapshot only affected current files (including uncommitted changes), run existing relevant checks, and preserve same-model/harness/input conversation results. Define assertions before changing prompts.

Start with **12 authored scenarios plus four held-out transfer scenarios**, using local services, enterprise software, ecommerce and a marketplace as well as the seed conversation. These are an initial evaluation budget, not a universal skill rule. Include:
- missing versus fully supplied founder context;
- comparison before commitment versus a narrow factual request;
- hard constraints and preference changes;
- occupied markets and genuinely poor entry economics;
- demographics versus observed buying behaviour;
- sponsored reach versus organic acquisition;
- repeat engagement with no immediate purchase in a long-cycle service;
- relationship metrics that never become commercial outcomes;
- failed retrieval and insufficient exposure;
- coherent output updates and session resume;
- preferences that favour partnerships or paid acquisition, so the agent does not inherit this founder's exclusions.

Reuse existing `evals/evals.json` formats. The current `run_behavioral_evals.py` is explicitly an offline routing checker; retain that claim and role. Run actual baseline/candidate conversations in clean existing-host sessions, saving transcripts and human rubric judgments. Do not build a new model executor for this change; a small manifest of results or an existing-runner report extension is sufficient. Use the same fixtures/tool outcomes for controlled comparisons and a small live retrieval smoke test separately. Grade reasoning/observed actions, not whether the answer contains expected headings. Repeat fragile cases if variance could explain the result.

Release conditions:
- No tested hard constraint violation, unsupported fact promotion, evidence-gap-as-rejection, or source-specific policy leakage.
- Held-out cases demonstrate the same decision process with different business ambitions, channels and entities.
- No regression in simple requests, existing routing, valid old records or resume.
- Candidate materially improves failed baseline decisions under human review; report mixed results honestly.
- Inspect tokens, tool calls, time and document counts where observable; no invented cost claims. Remove duplicate rules and unconsumed fields. Any complexity increase needs a measured or concrete reliability benefit.
- Run `bash scripts/validate_setup.sh`, `python3 scripts/run_evals.py`, affected pytest cases and offline routing checks as appropriate. Separate inherited failures from new failures. These checks cannot establish coaching quality.

Do not block this focused improvement on unrelated provider, brand or harness refactors in the older backlog. Stop after the release conditions are met; further infrastructure needs its own demonstrated failure. Roll back only the introduced change set against the saved dirty-worktree baseline.

### Source basis and limits

All refreshed **6 September 2026**. These sources inform methods; the proposed file scope, phases and acceptance criteria are engineering judgments for this repository.
- **S1:** [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), 19 December 2024. Supports simple composable workflows and adding complexity only when outcomes justify it. The page itself notes older tooling details; no runtime API decision is based on those details.
- **S2:** [Agent Skills specification](https://agentskills.io/specification), maintained documentation. Supports concise entrypoints and progressively loaded references; no duplication of the shared contract across every skill.
- **S3:** [UVA Darden, Effectuation](https://www.darden.virginia.edu/effectuation), undated overview. Supports founder means and affordable downside; it does not prescribe a universal acquisition channel.
- **S4:** [Strategyzer, Assumptions mapping](https://www.strategyzer.com/library/how-assumptions-mapping-can-focus-your-teams-on-running-experiments-that-matter), 4 August 2020. Supports prioritising critical low-evidence assumptions across desirability, feasibility and viability.
- **S5:** [Lenny Rachitsky, Finding consumer early adopters](https://www.lennysnewsletter.com/p/consumer-business-find-first-users), 26 July 2022. Retrospective company examples support concrete, concentrated early routes; survivor selection and consumer context limit generalisation.
- **S6:** [YouTube, Co-creating culture](https://blog.youtube/culture-and-trends/how-viewers-influence-the-content-they-love/), 5 September 2023. Platform-published survey discussion supports investigating repeat creator/audience connection and feedback; commercial incentives and self-report limit causal and business-specific conclusions. No conversion forecast is derived.
- **S7:** [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 9 January 2026. Supports realistic failure cases, transcript/outcome review and small initial suites. Structural tests remain separate from model behaviour.
- A searched academic meta-analysis on creator relationships could not be opened reliably; it is not used to claim proven sales impact.

Historical planning self-review: this section originally described planned work only. The current implementation and remaining verification limits are recorded at the top; this historical note is not a completion claim.

---

## Implementation record — reviewed corrections

Implemented: shared stable legacy evidence IDs; conservative independence grouping across authors, content and duplicate clusters; unknown collector independence and source language; documented top-level hook blocking with a recursion guard; final-decision prerequisite and nonempty artifact checks; KPI direction, incomplete-data outcomes, optional window/currency scope checks and required cohort maturity; frozen baseline CLI checks; commitment completion/overdue reporting; shared timestamp-based provider readiness with a 24-hour TTL; and removal of duplicated test invocations inside setup.

Validation: the review regressions run within the ordinary root pytest suite and CI setup command. They cover the reproduced failures, changed experiment thresholds, invalid numeric observations, cohort maturity, currency mismatch, and stale/newer provider results. Test counts belong in the latest execution report, not a permanent acceptance claim.

Remaining acceptance work from the broader original plan: full route-specific prerequisites and upstream invalidation for every stage; environment-fingerprinted provider readiness; source-budget and cache enforcement; evidence-backed idea comparison and segment-selection artifacts; calibrated live coaching trials; observed token-efficiency comparisons; session-scoped compaction restoration; and live host/provider/MCP smoke checks. Catalog parity and passing offline tests do not establish these outcomes. This implementation is not the entire original plan completed.

The work strengthens the existing 38-skill system. Keep Python, existing manifests, existing catalogs, and specialist boundaries. New runtime components are limited to the shared strategy contract/helper described below and small shared functions where duplicated mechanics already exist. Do not add another agent framework, database, dashboard, default panel, or specialist skill.

## Implementation sequence

Each phase is a reviewable change set, not a calendar estimate. Complete its acceptance checks before advancing dependent work. The implementation owner is the coding agent; the existing specialist named below owns the future business workflow, not a new agent deployment.

| Phase | Outcome | Dependency | Primary files/modules |
|---|---|---|---|
| P0 | Reproducible baseline and reliable test collection | None | Existing audit checks, `tests/`, `scripts/evidence_scout/test_*.py`, CI |
| P1 | Truthful evidence, source outcomes, and synthesis | P0 | Collector, provider common helpers, evidence/claim schemas, ledger and synthesis validators |
| P2 | Complete skill/source routing and explicit language scope | P1 contracts | Existing catalogs, router, capability lookup, provider doctor, locale/query helpers |
| P3 | Enforced state transitions, working hooks, reproducible harness setup | P0; finalize against P1/P2 | Workspace helpers, checkpoint schemas, Claude hooks/settings, MCP config |
| P4 | Honest coaching, idea comparison, segment analysis, GTM and KPI execution | P1/P2; persistence uses P3 | Existing business skills/templates, one shared strategy record/helper |
| P5 | Lower context and execution overhead | P2/P3/P4 | Root instructions, conditional references, source selection, evaluation/CI entrypoints |
| P6 | Behavior, live integration, and release verification | P1–P5 | Existing evaluation runners, fixtures, host/source smoke checks, final audit crosswalk |

P2 and P3 can be developed independently after their inputs are stable. Keep one writer per shared file and one owner for each manifest. Parallel agent execution is optional, not required by this plan.

## P0 — Establish a trustworthy baseline

1. Capture the current tracked/untracked file inventory and an audit-scoped diff so existing user work remains attributable. Do not reset, stash, or commit someone else’s edits.
2. Convert the audit’s synthetic reproductions into focused regressions: source/schema mismatch, Reddit 429, engagement-only strength promotion, inflated independence, missing routes, missing stage artifacts, locale fallbacks, and documented hook payloads.
3. Make ordinary repository-root test collection include both `tests/` and `scripts/evidence_scout/test_*.py`, with imports configured once. Use an existing test configuration if present; otherwise add a small root pytest configuration. Do not require users to remember an environment-specific `PYTHONPATH`.
4. Record current router outputs and structural metrics. Define held-out behavioral cases and grading criteria before changing skill prose. Preserve a baseline skill/config snapshot for later same-harness comparisons.

Acceptance: the normal test command collects both directories; existing tests pass before fixes, and each new regression demonstrably reproduces its intended defect. Do not merge a knowingly failing CI state; keep failing regressions and their fixes in the same delivered change set. Audit counts are reference observations, not future hardcoded counts.

## P1 — Repair the evidence boundary

### P1.1 Source taxonomy and request outcomes

Touch `scripts/evidence_scout/collect.py`, `scripts/validate_apis/common.py`, the affected adapters, `schemas/evidence-record.schema.json`, and `config/source-capabilities.json`.

- Reconcile all six missing emitted source names: `hn`, `github`, `google_autocomplete`, `itunes_reviews`, `youtube_transcript`, and `xai_x_search`. Preserve their semantic distinctions; document legacy aliases where needed.
- Distinguish source kind, provider/backend, retrieval mode, and evidence role. A customer comment, creator transcript, search suggestion, and model-generated discovery summary are not interchangeable inputs to demand claims.
- Validate each normalized record before saving it as accepted evidence. Retain malformed raw responses for diagnosis, mark the affected provider partial/failed, and report rejection counts. Never silently discard failures or mark the entire run valid because one record survived.
- Share outcome aggregation across adapters: successful data, successful empty response, partial success, rate limit, insufficient credits, unavailable credentials, unsupported operation, malformed response, network failure. Derive outcomes from all attempted requests.
- Preserve request timestamps, actual backend/endpoint identity, query scope, and extraction method at the call site. Remove post-hoc assignment of a preferred family backend as if it made the request.
- Keep retries bounded and status-specific. Do not retry authentication or billing failures blindly or spend on a paid fallback without applicable authorization. Resume a failed provider without recollecting successful providers unnecessarily.

Acceptance: fixtures cover 200/data, 200/empty, 429, 402, malformed payload, timeout, mixed results, and rejected normalized data. Every enabled adapter emits schema-valid accepted records and accurate status; discovery-only material cannot be relabeled as customer behavior. A provider outage never becomes evidence of no demand.

### P1.2 Identity, independence, and confidence

Touch `normalize_record()`, `estimate_strength()`, `build_claim_ledger.py`, `validate_synthesis.py`, and evidence/claim schemas.

- Separate engagement metadata from evidence strength. Keep keyword heuristics for triage; require substantive directness, consequence, recency, relevance, and provenance for stronger classifications.
- Define a stable source-record identity using source-native ID or canonical locator; keep content version/hash and retrieval occurrence separate. Where no source identity exists, derive a documented content identity without retrieval time. Do not imply that a content match proves the same author or event.
- Compute independence from available author/event provenance and duplicate clusters. Same-author repetitions and syndicated copies must not count as independent support. Unknown independence stays unknown and cannot be inflated through a URL fallback.
- Recompute and compare ledger counts at validation. Reject inconsistent submitted counts, unknown IDs, duplicate IDs with conflicting content, and schema-invalid inputs.
- Separate confidence in an observation from confidence in demand, willingness to pay, or a recommended investment. No universal source-count threshold validates all claim types.
- Validate counter-evidence search scope semantically: a relevant query set, actual checked sources, time/geography scope, outcomes, and failed routes. Distinguish “not searched” from “searched with none found.”

Acceptance: changing engagement alone cannot change commercial evidence strength; duplicated/syndicated/same-author records do not inflate confidence; refetches preserve source identity; changed content preserves provenance; unsupported high-confidence demand claims fail. Hypotheses remain expressible without being mislabeled as facts.

## P2 — Complete routing, readiness, and locale handling

### P2.1 Skill routing and no-orphan enforcement

Touch `config/skill-catalog.json`, `config/workflow-routes.json`, `config/routing-evals.json`, `scripts/route_workflow.py`, `scripts/validate_registries.py`, and `scripts/run_evals.py`.

- Add the missing `competitor-monitoring` catalog entry. Classify every installed project skill as an entry workflow, declared child, or manual/setup utility.
- Add core intents for GTM, marketing, social execution, idea comparison, business planning, KPI/weekly review, pilots, interviews, case analysis, and monitoring. Explicitly declare valid child dispatches for the remaining skills.
- Separate intent selection from deterministic dispatch. Add a validated explicit intent/mode input; retain simple phrase matching as a convenience. The calling agent may classify a paraphrase into an allowed intent, but the dispatcher rejects invalid intents and incompatible modes. Do not add a second model call just to route every request.
- Cover negations, compound requests, near-misses, and relevant active-workspace context. Return one primary route with a bounded ordered follow-up when needed. Clarify only an ambiguity that changes execution.
- Emit the promised route packet from catalog metadata: selected skill/mode, prerequisites, needed references, expected artifacts, side effects, cost/authorization state, and next action. Unknown authorization is not permission.
- Extend registry validation to check the full graph: skills, child edges, local references/assets, executable entrypoints, declared output contracts, and eval coverage. Identify cycles and unused bundled resources. Exempt generated paths explicitly rather than suppressing all missing-link failures.

Acceptance: all current project skills are cataloged and have a valid use path; every advertised entry intent has a positive and near-miss test; the audit GTM/marketing/monitoring prompts route correctly. Brand-only requests remain independent of market validation. Catalog and route metadata cannot silently diverge.

### P2.2 Source catalog, readiness, and minimal collection

Touch `config/source-capabilities.json`, `scripts/capability_lookup.py`, `scripts/evidence_scout/provider_doctor.py`, `scripts/validate_apis/run_all.py`, and shared provider helpers.

- Represent each capability as an implemented collector, standalone CLI, or explicitly manual/optional route. Correct podcast metadata to its existing standalone script; remove its false `default` collector claim.
- Validate collector aliases, standalone command paths, emitted schema types, source roles, validator links, prerequisites, paid status, and fallback paths. Manual/optional capabilities must advertise their limitation, not appear executable.
- Consolidate readiness selection in one helper. Choose the newest valid result per backend, regardless of individual-versus-aggregate file order. Validate timestamps and use a configurable TTL plus sanitized endpoint/configuration/network-context identity. Never record key values or hash secrets to create identifiers.
- Keep readiness states separate: not checked, stale, credentials present, usable, degraded, failed. Unsupported checks and missing timestamps are not current success.
- Add targeted validator selection and output-directory controls; retain broad diagnostics as an explicit setup operation. Do not launch every paid validator to answer one source question.
- Select the smallest source plan justified by the segment and unanswered questions. Respect catalog exclusions. Preserve an explicit broad/manual mode for deliberate coverage audits.

Acceptance: newer individual results beat stale aggregate entries; environment changes invalidate applicability; credentials alone never imply successful retrieval. Every advertised source has a valid declared path, fixture coverage, and an honest live-readiness state. Nontechnical consumer cases do not automatically collect GitHub/HN. Podcast and optional fallbacks are visible without being falsely included in default collection.

### P2.3 Languages and geography

Touch locale/query helpers in `collect.py`, `capability_lookup.words()`, manifest/evidence schema fields, discovery commands, and GTM regional template rows.

- Persist separate geography, query language, source language, and output language. Explicit caller scope wins; missing consequential scope is unresolved or produces one focused question, not a silent US default.
- Make tokenization Unicode-aware and route provider-specific locale parameters explicitly. Reject unsupported locales or disclose a fallback; do not pretend one provider accepts every code.
- Retain original source text beside translations, with translation method/version, review status, and material ambiguity. Preserve currency/unit originals and distinguish translations from numeric conversions.
- Replace hardcoded Germany/China/Europe assumptions in shared mechanics with selected market inputs and conditional existing query registries. Keep useful domain examples clearly optional.
- Define the supported language matrix in configuration/documentation. Initial regression coverage: English, German, French, Italian, Arabic, and Chinese, with at least one cross-language/geography case. Passing routing tests does not establish translation quality.

Acceptance: audit locale examples no longer silently resolve to US/English; Arabic/Chinese lookup retains meaningful tokens; English-language Switzerland remains Switzerland. Local-language terms and translated evidence retain traceable origins, and unsupported coverage is disclosed.

## P3 — Enforce state and repair harness contracts

### P3.1 State transitions and migrations

Touch `scripts/evidence_scout/workspace.py`, `scripts/project_workspace.py`, stage/topic/project schemas, and callers that advance stages, including discovery/landscape builders and business-to-brand handoffs.

- Define route-specific stage prerequisites and artifact validators alongside existing workflow configuration. Preserve conditional branches and explicit skips with reasons; avoid a universal mandatory sequence.
- Perform transition checks inside the mutation boundary: prerequisite verdicts, artifact existence/schema/content revision, unresolved critical gaps, and any required owner decision.
- Separate artifact completion from business validation. A finished report does not prove demand; conditional completion cannot silently unlock scale or validated-business handoff.
- Add dependency revisions/hashes so an upstream change invalidates affected downstream conclusions and approvals. Do not invalidate unrelated brand/website work automatically.
- Protect read-check-write with a single-writer contract and an exclusive lock covering the transaction, plus expected revision checks and atomic replacement. The existing revision check by itself is not a concurrent compare-and-swap. Lock timeout/conflict returns an actionable error; do not silently break another writer’s lock.
- Make retries idempotent and reject path traversal or unapproved external artifact paths. Return a clear `next`/resume decision from current state.

Acceptance: missing artifacts, stale inputs, illegal transitions, unresolved critical gaps, conflicting writers, and replayed actions behave correctly. A legitimate optional stage can be skipped with a reason. An interruption resumes without invented approval or duplicated provider spending.

### P3.2 Hooks, permissions, and host setup

Touch `.claude/hooks/{precompact,postcompact,subagent_stop}.py`, `.claude/settings.json`, `.mcp.json`, `CLAUDE.md`, relevant setup/sync tooling, and `tests/test_claude_hooks.py`.

- Recheck the installed supported Claude version and official event contracts at implementation time. Correct input fields and event-specific outputs; test top-level blocking and documented feedback behavior.
- Keep hook validation bounded and task-aware. A truthful coverage failure or a code-only task must not be rejected merely for lacking a citation. Guard against recursive stop-hook retries.
- Save session-scoped state using the selected manifest and current task: last decision, pending work, blockers, artifact revisions, and applicable authorization. Load through the supported resume/compact lifecycle. Do not scan every research workspace or mix sessions.
- Preserve project-root anchoring and test root/nested working directories, absent state, corrupt state, simultaneous sessions, and actual restoration visibility.
- Pin tested MCP package versions; document only project-provided servers or clearly identified external prerequisites. Verify Firecrawl account-variable mapping without printing credentials.
- Replace unnecessarily broad command allowances with the scoped commands actually used. Test permissions against synthetic canary files, never real secrets. Distinguish read-pattern rules from sandbox isolation.
- Publish a host matrix for Claude Code, Codex, and OpenCode covering skill discovery, script execution, state resume, MCP setup, and permission behavior. Treat Gemini as an explicit optional setup target unless added to the supported runtime matrix. Use thin adapters only where needed.

Acceptance: documented hook payloads work and host-level smoke tests show intended context delivery; separate sessions cannot overwrite each other; pinned MCP startup and required source mapping work. Host capabilities lacking live validation are labeled unverified. Harness configuration changes belong to the implementation scope only when authorized; do not infer authorization from this planning request.

## P4 — Implement the honest business-coaching process

### P4.1 One shared business strategy record

Add the proposed `schemas/strategy-plan.schema.json` and a small `scripts/strategy_review.py` helper with validation, KPI calculation, comparison, and Markdown rendering commands. Reuse existing workspace revision/event helpers. This new contract is justified by the missing machine-checkable handoff between ideas, GTM, experiments, and weekly review.

Store one versioned `strategy/plan.json` per future active business workspace, with a generated concise review when needed. Optional mode-specific sections cover:

- Selected idea/segment and referenced evidence/claim IDs; founder objectives, constraints, and explicit exclusions.
- Positioning, offer, primary acquisition motion, current stage, and decisive uncertainty.
- Experiments and execution assets, with owners, dates, eligibility, budgets, and frozen decision thresholds.
- KPI definitions and dated observations with source references; commitments, decisions, and rationale.

Keep evidence in its existing store. Portfolio comparison references selected workspace manifests/revisions in a project-level comparison record using the same schema’s comparison mode; it does not copy all their evidence or create another topic database. Do not require unused full-plan sections for a narrow question.

Acceptance: scripts compute metrics from supplied observations and render the same canonical state consumed by GTM, marketing, social/digital, and operating review. Divergent copies cannot become independent sources of truth. Missing inputs remain null/unknown with reasons, never fabricated baselines.

### P4.2 Honest coaching and idea selection

Owners: `business-strategist`, `idea-grill`, `opportunity-risk-designer`, `startup-business-builder`, and `company-operating-system`.

- Put a concise coaching contract in the orchestrator and specialist-specific applications in existing workflows: provisional verdict, weakest assumption, opposing explanation, evidence that would change the view, next bounded test, and accountability at review.
- Use separate verdicts for insufficient evidence, investigate/test, commit, pivot, park, and stop; map them consistently into existing states without equating a strategic verdict with workflow completion.
- Remove the weak-evidence-means-stop contradiction. Challenge expensive avoidance, unsupported certainty, sunk-cost arguments, and moving targets when the evidence supports the critique. Change the recommendation when new facts warrant it.
- Add idea-comparison mode to `opportunity-risk-designer`: founder fit/constraints, attractiveness, confidence, buyer access, time/cash to test, delivery burden, contribution potential, switching friction, and opportunity cost.
- Use evidence-linked ordinal assessments and sensitivity checks. Rank tests rather than pretending unknown businesses have precise numeric valuations. Recommend one active priority by default; explain any parallel allocation.
- Preserve the user’s final decision and record a reasoned override without changing the evidence or adopting unsupported agreement.

Acceptance: founder pressure alone does not reverse a supported verdict; new evidence can reverse it; weak coverage is not called a failed business; idea comparison respects different founder goals and makes a concrete allocation decision.

### P4.3 Segment, positioning, GTM, and marketing

Owners: `market-problem-discovery`, `interview-bridge`, `service-customer-perspective-challenger`, `competitive-landscape-builder`, `archetype-gtm-strategist`, `marketing-strategy-builder`, and `social-digital-marketing-planner`.

- Extend the existing segment card/templates with buying episode, trigger, job, consequence of delay, user/buyer/payer/blocker, workaround, trust requirements, switching friction, and reachable buying context.
- Treat public-record frequency × severity as triage. Separate visibility/sampling bias from commercial priority. Compare switchers, retained customers, non-buyers, and lost deals where evidence exists.
- Build positioning from actual alternatives, including doing nothing: alternative → relevant advantage → outcome → proof → objection → test. Preserve the three competitor lanes and distinguish buyer shortlist evidence from discovery.
- Pass the same segment/offer revision through GTM and marketing; a specialist changes it explicitly and invalidates affected downstream work rather than silently rewriting it.
- Choose the motion from access, price, sales cycle, onboarding, trust, delivery capacity, and economics. Define owners and exit criteria from acquisition through sales, first value, retention, and expansion.
- Use archetype-specific gates: one-off services require delivered outcome/contribution/complaints; enterprise pilots require sponsor/procurement/implementation/value; recurring SaaS requires activation and mature cohorts. Do not impose subscription retention on every business.
- Preserve one primary acquisition motion and first-ten-customer work. Produce concrete test assets and tracking definitions. Test message relevance, comprehension, credibility, and qualified conversion before multiplying creative variants.
- Keep attribution distinct from incrementality; include labor, creative, delivery, refunds, and acquisition costs without double counting. No default marketing-mix or elaborate attribution tooling.

Acceptance: the agent can produce an executable first-customer test from a specific segment, explicitly reject unsuitable channels, and adapt the test to at least SaaS, enterprise pilot, and consumer-service fixtures. Founder stories and competitor messaging never become purchase proof.

### P4.4 KPI and weekly execution review

Owners: `company-operating-system` and `archetype-gtm-strategist`; calculations owned by `strategy_review.py`.

- Limit the current scorecard to 3–5 metrics, with explicit exceptions only when another metric changes a distinct decision.
- Each KPI defines formula/components, data source, segment/cohort, eligibility/exclusions, observation/maturation window, baseline, target, warning/stop/scale threshold, threshold rationale, owner, review date, and resulting action.
- Separate output measures from controllable activity commitments. No denominator is zero by default; no missing observation becomes failure or success. Guard against immature cohorts, mixed currencies/windows, duplicated costs, and unsupported lifetime-value extrapolation.
- Freeze experiment eligibility, duration, budget, and decision rules before results. Material changes create a new revision/test; keep the original result visible.
- Generate a one-page weekly review: commitments versus completion, actual versus target with caveats, bottleneck, changed evidence, verdict, and next commitments. Escalate repeated missed actions or target changes without moralizing.
- Prepare authorized assets and analysis autonomously. Outreach, publication, spending, and deployment require applicable authorization; prepare a concrete result before a final approval step.

Acceptance: synthetic KPI cases reproduce formulas, handle zero/missing denominators correctly, exclude immature cohorts, and preserve frozen thresholds. A weak acquisition week, failed activation cohort, successful one-off service, and missed-commitment week each produce different justified actions.

## P5 — Remove unnecessary overhead

Touch `AGENTS.md`, `CLAUDE.md`, affected skill entrypoints/workflows, `references/evidence-registry.md`, provider-policy/command references, setup validation, CI, and evaluation runners.

- Keep root instructions to stance, scope/state resolution, authorization, validation entrypoints, and pointers. Make clear that technical audits do not enter the research-workspace selection workflow. Reuse explicit workspace choices and only ask when ambiguity changes the task.
- Remove duplicated YAML frontmatter from workflow references and consolidate repeated channel/loop/founder-story policies into the existing shared reference. Keep direct conditional links from skill entrypoints.
- Retain short entrypoints and genuine specialist distinctions. Narrow overlapping descriptions using routing tests; do not delete skills merely to reduce a count.
- Offer brief, experiment, and full-strategy output depth as modes in existing workflows. Load only the needed sections/resources; do not replace short entrypoints with mandatory long reads.
- Implement per-run source/request budgets and reuse already-retrieved pages within declared freshness/scope. Add providers for named coverage gaps. Keep panels/tournaments optional with explicit effort caps.
- Separate cheap structural validation from one full offline suite. CI must execute the relevant suite once, including script tests; setup may remain a convenience wrapper without causing CI to rerun identical checks. Preserve brand/website fixture coverage appropriate to changes.
- Extend existing event/benchmark output with observed input/reference tokens, tool-result bytes, repeated retrievals, tool calls, latency, harness/model versions, and completion outcome. Store redacted references/hashes instead of raw customer text or credentials. If a host cannot expose a metric, report unavailable rather than a synthetic zero.

Acceptance: zero known orphan runtime resources/skills; no duplicate full test executions in the default CI path; no irrelevant source calls in the held-out segment fixtures. On matched successful tasks, loaded context and unnecessary calls decrease from baseline without degrading critical behavior. Set any quantitative reduction target before the optimization trial; do not invent a savings percentage from file length alone.

## P6 — Behavioral verification and release

Extend `scripts/run_behavioral_evals.py` with clearly separated offline-contract and opt-in live-agent modes; retain its existing CLI where practical. Reuse `scripts/run_evals.py` for dataset validation and `benchmark_agentic_process.py` for measurement/reporting. No evaluation SaaS dependency is needed.

Start with 12 scenario families: favorite-idea pressure; vanity traction; retrieval failure; noisy versus quiet segments; two ideas with different founder fit; one-off service; enterprise pilot; moving thresholds after results; missed commitments; new counter-evidence reversing an earlier verdict; multilingual/cross-geography work; interrupted execution/resume. Include unseen paraphrases and justified positive cases, not only skeptical answers.

Define each expected decision before the run. Evaluate actual routes, tool calls/parameters, artifacts, metric calculations, state transitions, authorization boundaries, and coaching usefulness. Use rubric/human-calibrated judgments for quality; keyword inclusion is insufficient. Run repeated live trials to expose variability and record failed/blocked attempts rather than dropping them. [Anthropic’s evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) supports evaluating both traces and resulting state.

Release gates:

1. **Offline contracts:** all audit regressions and normal Python checks pass; no missing catalog links, invalid accepted records, fabricated independence, or illegal transitions in the suite.
2. **Coaching behavior:** every trial respects critical evidence/authorization rules. Initial project target: at least 90% of scenario trials satisfy the predeclared usefulness rubric on each supported host. This is an engineering acceptance target, not statistical proof of real-world business quality; publish sample sizes and per-scenario failures.
3. **Live sources:** run one bounded check for every enabled, authorized adapter or standalone source path. Verify status, normalized schema, provenance, and role. Credit/login-blocked integrations remain covered offline and explicitly unverified live; do not call them fully wired-and-working.
4. **Live hosts:** verify discovery, routing, script execution, context restoration where supported, and state replay separately on each claimed host. Report unsupported capabilities explicitly; portable files alone do not satisfy this gate.
5. **Efficiency:** compare the same held-out tasks, harness/model, tool fixtures, and output depth. Report actual context/call/latency changes alongside task quality. Critical correctness gates cannot be traded for token savings.
6. **Delivery:** rerun setup/CI appropriately, `git diff --check`, local-link/registry checks, affected consumer fixtures, and confirm existing research outputs remain unchanged. Update the crosswalk below with evidence paths and actual status.

If a live gate lacks credentials, credit approval, or a working host, finish independent offline work and report the precise gap. Do not mark the entire implementation fully validated until the applicable live gates are met or the supported scope is explicitly narrowed.

## Compatibility, rollout, and rollback

- Version changed evidence, claim, stage, and strategy contracts. Implement adapters for known legacy shapes; preserve original records and identifiers plus an alias map where identity semantics change. Missing provenance cannot be inferred by migration.
- Existing research stays untouched. Exercise migration on synthetic/fixture copies. On a future authorized resume, read legacy state without rewriting it and create a new revision/run only when needed. Historical pass flags do not automatically satisfy new validation rules.
- Test every changed shared helper against its actual importers and downstream consumers, including landscape/whitespace generation and business-to-brand handoff. Keep business and brand state ownership distinct.
- Deliver small dependency-ordered changes. If a contract change fails, restore the previous code/config and select the prior immutable run; preserve newer outputs as non-authoritative. Avoid destructive resets or deletion of user work.
- This request authorizes plan preparation. At implementation time, honor explicit scope authorization for settings changes, paid providers, host configuration, and external actions. Prepare exact config diffs and bounded live commands before any required approval; do not introduce approval gates for ordinary local fixtures or reversible document/code work already authorized.

## Audit coverage and implementation tracking

All entries start **pending**. Mark complete only with the referenced acceptance evidence. A documented optional integration can be structurally complete while live verification remains explicitly open.

| ID | Audit finding/improvement | Work item | Acceptance evidence |
|---|---|---|---|
| F01 | Six missing source kinds and unenforced normalization | P1.1 | Per-adapter schema fixtures |
| F02 | Failed retrieval reported as empty success | P1.1 | Error/partial/empty outcome matrix |
| F03 | Wrong evidence role and preferred-backend decoration | P1.1 | Actual-path provenance and semantic-role tests |
| F04 | Engagement increases substantive strength | P1.2 | Engagement-invariance regression |
| F05 | Inflated independence, duplicate URLs, and confidence | P1.2 | Recomputed independence/claim tests |
| F06 | Retrieval-dependent identity and incomplete counter-search scope | P1.2 | Refetch/version and scope-validation fixtures |
| F07 | Catalog omission and missing business routes | P2.1 | Catalog parity and route scenarios |
| F08 | Incomplete route packet and no full orphan graph | P2.1 | Packet assertions and resource graph validation |
| F09 | Podcast/default and other source wiring drift | P2.2 | Adapter/CLI/validator graph checks |
| F10 | Stale readiness and aggregate overwriting newer results | P2.2 | Timestamp/environment selection tests |
| F11 | Excessive providers and all-provider validation | P2.2, P5 | Selected-source plans and call traces |
| F12 | Wrong geography, Unicode loss, and hardcoded regional defaults | P2.3 | Locale/provider mapping matrix |
| F13 | Missing translation provenance and localized evaluation | P2.3, P6 | Original/translation fixtures and live scope report |
| F14 | Caller-controlled stage success and nonexistent artifacts | P3.1 | Transition/artifact rejection tests |
| F15 | Stale downstream approvals, concurrent writes, and replay | P3.1 | Invalidation, concurrent writer, interruption tests |
| F16 | Hook input/output mismatch and weak output checks | P3.2 | Documented payloads and host smoke trace |
| F17 | Global resume state and unrelated workspace scans | P3.2 | Session isolation and restored-context checks |
| F18 | Unpinned MCPs, inaccurate server docs, permission breadth | P3.2 | Pinned startup, config parity, canary permission tests |
| F19 | Unverified cross-harness behavior | P3.2, P6 | Per-host capability/result matrix |
| F20 | Blunt stance without observable honest coaching | P4.2, P6 | Pressure/reversal/actionability trials |
| F21 | Weak evidence incorrectly triggers stop | P4.2 | Insufficient-evidence and failed-test distinction |
| F22 | Idea prioritization and founder constraints | P4.1/P4.2 | Evidence-linked comparison/allocation fixtures |
| F23 | Public visibility bias and shallow segment comparison | P4.3 | Buying-episode and quiet/noisy-segment cases |
| F24 | Positioning disconnected from actual buyer alternatives | P4.3 | Alternative/value/proof/test chain |
| F25 | Repeated strategy generation across GTM/marketing | P4.1/P4.3 | Shared revision handoff and invalidation |
| F26 | Archetype gates, first customers, marketing tests, economics | P4.3 | SaaS/service/enterprise execution fixtures |
| F27 | KPI definitions, frozen tests, and weekly accountability | P4.4 | Metric calculations and multi-week decision replay |
| F28 | Root/reference duplication, long outputs, panel overhead | P5 | Conditional load traces and baseline comparison |
| F29 | Script tests excluded/import errors and repeated CI suites | P0, P5 | One clean standard test/CI execution |
| F30 | Structural evals mistaken for behavior/token measurement | P6 | Held-out live trials and actual usage report |
| F31 | Preserve historical outputs and prevent migration fabrication | P1–P6 rollout | Legacy fixtures and unchanged-output verification |
| F32 | Future bloat/orphans returning | P2.1, P5 | Admission rule plus CI graph/efficiency checks |

Admission rule for future additions: identify the demonstrated failure, explain why an existing skill/helper cannot own it, name the consumer and acceptance test, and remove the redundant path when replacing one. Schema fields and adapters must have actual readers and writers. Architectural growth without a consumer is not completion.

## Plan review and handoff

Planning review checks: every audit finding is assigned; dependencies are ordered; ownership and data flow are explicit; state writes include a real concurrency boundary; migrations preserve uncertainty; paid/live work is separated from offline fixtures; new runtime artifacts have named consumers; and no change requires editing historic research. This is a local planning review, not an independent agent review or proof that implementation passes.

Plan completion requires this document and its link from the existing implementation plan. Implementation completion requires the P6 evidence and resolved crosswalk. No runtime changes are included in this planning deliverable.

Sources refreshed on **5 September 2026**:

- [Agent Skills specification](https://agentskills.io/specification), maintained documentation: progressive disclosure and portable resource references inform P2/P5.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 9 January 2026: traces, outcome checks, repeated trials, and calibrated graders inform P0/P6.
- [Strategyzer: Validate Your Ideas with the Test Card](https://www.strategyzer.com/library/validate-your-ideas-with-the-test-card), publication date not independently extracted: explicit hypothesis, test, metric, and threshold inform P4.4.
- The [original audit’s dated source list](audits/2026-09-05-agent-strategy-review.md#sources) supports the remaining coaching, positioning, portfolio, context, and hook recommendations. Recheck version-specific hook/provider contracts during implementation.
