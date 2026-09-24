# Implementation plan: analysis quality, evidence integrity and module ownership

Date: 23 September 2026. Status: partially implemented; see [implementation record](analysis-quality-implementation-record.md).

Revised after the [independent adversarial review](../audits/2026-09-23-analysis-quality-plan-adversarial-review.md). The revisions below address concrete failure modes and bring the research-quality decision forward; they do not add new agents or a separate governance system.

This is the consolidated plan for the six analysis/output improvements, the four module boundaries, and the supporting defects identified in the [agent review](../audits/2026-09-23-agentic-evidence-and-modularity-review.md). It incorporates the existing [provider-retention plan](2026-09-23-provider-retention-fix-plan.md) as the detailed specification for capture repairs. The review's web addendum contains the research sources and their limitations; those sources were retrieved earlier in this conversation and were not fetched again for planning.

**Intended outcome**

An agent should produce findings that identify a specific customer situation, distinguish observation from explanation, preserve counterexamples, explain uncertainty, and help the user make the intended decision. It should retain the material it fetched and carry checked evidence into subsequent work. Branding, Marketing and Website should each receive the context and quality criteria appropriate to their own deliverable.

Implementation completion and demonstrated analytical improvement are separate milestones. Passing code tests establishes contract behavior. Improved interpretation and decision usefulness require actual comparative evaluations.

**Scope and implementation decisions**

- Extend the current skills, evidence ledger, source review, U/R synthesis, claim ledger, manifests and router. Keep the current skill names and host discovery paths.
- One router selects a module and specialist. Module boundaries do not automatically create parallel agents. Business positioning and feasibility retain their existing strategy owners.
- Existing project research, selections, approval history and artifacts remain historical inputs. Implement and exercise changes in fixtures and isolated workspaces. Existing studies can be explicitly upgraded later.
- Retain topic/entity separation, source-language distinctions, unpaid recruitment, standing authorization for customer-evidence APIs, and existing community capture controls. Advertising, outreach, paid generation and deployment retain their distinct authorization rules.
- Implementation is authorized. Live model runs and project migration remain separate work; no project research has been rewritten as part of this implementation.
- Preserve unrelated untracked work visible in the current checkout. Record content hashes for the touched baseline because Git HEAD alone does not capture that work.

**Coverage of every recommendation**

| ID | Recommendation or defect | Delivery phase | Observable completion evidence |
| --- | --- | --- | --- |
| Q1 | Decision-led questions and competing explanations | P2 | Each substantive question has a decision purpose and discriminating observations; queries preserve question associations |
| Q2 | Compare full customer episodes before themes | P3 | Reproducible comparison view with chronology, source spans, contrasts and unknowns |
| Q3 | Bounded explanatory findings and separate confidence judgments | P3 | Findings retain support, exceptions, interpretation and claim-specific uncertainty |
| Q4 | Source verification separate from writing | P4 | Reviewed claims resolve to exact evidence; changed inputs invalidate verification |
| Q5 | Decision-focused final output | P5 | Report states answer, decisive findings, contrary evidence, limits and next action |
| Q6 | Direct evaluation of analytical quality | P0, P7 | Baseline/revised outputs and blinded dimension-by-dimension assessments |
| E1 | Placeholder pain gate | P4 | Ordinary closure rejects placeholder-only evidence and insufficient findings |
| E2 | Unrelated discovery pack accepted | P4–P5 | Study/case/scope and candidate/report associations are verified |
| E3 | Transcript discarded after capture | P1 | Fetched transcript text persists and its retention counts reconcile |
| E4 | Social platforms starved/mislabelled | P1 | Allocation treats requested platforms explicitly and retains eligible comments |
| E5 | Interrupted collection loses normalized progress | P1 | Resume preserves completed captures and memberships without duplication |
| M1 | Research, Branding, Marketing, Website ownership | P6 | Catalog, routing and output destinations consistently express module ownership |
| M2 | Independently startable Marketing | P6 | Supplied-brief work starts independently; linked venture commitments keep their gates |
| M3 | Smaller context and reliable handoffs | P6 | Only applicable references load; stale upstream artifacts require review |
| M4 | Module-specific output quality | P6–P7 | Representative deliverables are assessed using domain-specific criteria |
| S1 | Conflicting paid-provider approval instructions | P2, P6 | Entry skills consistently honor standing customer-evidence authorization |
| S2 | Legacy-only, shared compaction snapshot | P6 | Modern paths and session-specific continuation survive snapshot/restore checks |
| S3 | Monolithic provider implementation | P8, optional | Extract only where a named maintenance/reliability problem justifies it; preserve checked capture semantics |
| S4 | Optional bounded source workers | P6, P8 | Documented isolated inputs, outputs, allocation and merge responsibilities; no automatic launch |
| T1 | Template still promotes severity × frequency score | P5 | Generated report guidance and examples no longer request that unsupported ranking |

**Order and dependencies**

```text
P0 Baseline and acceptance examples
 ├─ P1 Capture integrity and recovery
 └─ P2 Research questions → P3 Episodes and findings
                         P1 + P3 → P4 Verification and closure → P5 Reports
P5 → P7a Research comparison and adoption decision
P6 Modules and handoffs → P7b Module comparisons
P1 + relevant comparisons → P8 Optional, justified provider extraction
```

Capture fixes and method improvements can be developed independently on isolated changes. Sequence shared schema/validator/producer changes together. Research evaluation does not depend on Marketing paths, compaction hooks or module handoffs. Build the minimal comparison runner with P0; use it after P5, and evaluate modules as their outputs become available. The optional scheduling above does not authorize subagent execution.

**P0 — Establish the baseline and acceptance examples**

Owner: evaluation work within existing `evals/voc/`; no new specialist.

1. Record baseline versions/hashes of prompts, references, templates, schemas and relevant scripts, plus model/harness details when a live comparison is run.
2. Preserve the four review reproductions as regression scenarios: dropped transcript, social starvation, placeholder pain pass, and unrelated study finalization. Use isolated temporary workspaces and synthetic responses.
3. Build an initial 12-task research evaluation bank: eight development tasks and four held-out tasks, with a spread of discovery, entity feedback, multilingual episodes, resolved complaints, conflicting accounts, supplier contamination, unknown independence and insufficient evidence. Assign connected study/source/incident groups wholly to one split, including translated, quoted or paraphrased duplicates; different websites alone do not establish independence. Record split membership and known overlap, and do not force the 8/4 target if independent groups are unavailable. This is an engineering starting size, not a statistical claim or research sample quota.
4. Include paired weak/strong outputs with reasons. A reference interpretation is one defensible reading; list acceptable alternatives and clearly unsupported conclusions. Genuine reviewer disagreement remains recorded.
5. Preserve full source packets and exact locators where permitted. Keep supplied synthetic fixtures clearly separate from live-retrieved material. Existing `evals/voc/live/` examples are development material, not newly independent gold labels.
6. Before changing the analytical workflow, run and save baseline outputs if the configured model provider is authorized. If model access is unavailable, finish the fixture/harness work and mark the comparison unrun. Do not substitute deterministic test results for this baseline.
7. Freeze the P7 rubric, critical-error rules, primary improvement dimensions, task-level win/tie/loss rules and adoption criteria before tuning prompts or methods. A useful gain must improve an identified analytical weakness, with no critical failures in the revised outputs and no material regression on the protected fidelity/uncertainty dimensions. State the required task-level improvement and treatment of reviewer disagreement in the evaluation manifest before seeing revised results. Preserve all comparisons, including losses; rule changes create a new evaluation version and require fresh held-out material if prior results informed the change.

Files: `evals/voc/`, relevant skill `evals/evals.json`, `docs/agentic-evaluation.md`; regression cases in existing VOC, workspace, discovery and query-expansion test modules.

Acceptance: task input versions, frozen output/adoption criteria, split membership and known limitations are explicit. A split check rejects overlapping study/source/incident groups; semantic duplicate review supplements ID checks. Held-out packets and answers are excluded from development context; only the evaluation run receives its task inputs. Later tuning on a held-out task reclassifies its connected group as development material.

**P1 — Preserve collection and make recovery explicit**

Implement the existing provider-retention plan through `scripts/evidence_scout/collect.py` and the run-manifest helpers in `workspace.py`; extend `scripts/validate_apis/common.py` only as needed to restore and checkpoint the shared request allowance. This plan's recovery/accounting requirements supplement the provider-retention specification.

1. Persist transcript content and provenance immediately after retrieval. Separate requested transcript enrichment from search/comment retention allowance, retain creator attribution, and track attempted/fetched/persisted/retained/failed independently.
2. Allocate TikTok, Instagram and Threads as explicit source lanes before retaining records. Use balanced selection among valid available results. Distinguish empty/missing-text responses, duplicate results and allocation exclusions. Schedule comments from eligible retained parents.
3. Persist completed query captures and normalized record batches before the next provider. Aggregate outputs are reproducible from completed captures; they are not the sole copy of progress.
4. Add an explicit resume option to the existing CLI. Bind a run to the normalized query-plan digest, study/case identity and allocation settings. Resume accepts an identical capture plan; changed queries create a linked follow-up run.
5. Reuse stable evidence/capture IDs. Duplicate discoveries add memberships. Use same-directory atomic replacement for manifests/checkpoints and idempotent batch assembly for evidence; do not blindly append the same batch twice.
6. Record failed/incomplete/uncertain operations in the existing run checkpoint. Persist request attempts/reservations and consumed transcript/enrichment allowances before the corresponding external operation, then settle their status after capture. Restore consumed allowances before scheduling resumed work; local reprocessing consumes no additional retrieval allowance. An operation interrupted after reservation remains uncertain and consumes its allowance until resolved; retries are explicit new attempts within the remaining allowance. Reconcile counters from operation IDs so resumed assembly cannot count one attempt twice. Preserve the existing meaning and scope of each limit, including the shared HTTP helper's exclusions for SDK/subprocess calls. These are reproducibility and execution bounds, not a new monetary cap or paid-evidence approval step; exactly-once remote billing is not promised.
7. Keep previews free of network and workspace mutations; show excluded lanes before execution when allowances cannot cover them.

Acceptance: exact retained text and counts pass both existing failure examples; source-order changes do not starve a requested lane; duplicate/retry cases preserve memberships; interruption before dispatch, after raw capture and after normalized persistence resumes correctly. Resumed and uninterrupted runs exhaust the same configured allowances when operation outcomes are known; uncertain attempts are reported and cannot silently refill an allowance. Existing entity/community capture gates still apply on resumed requests and are rechecked for freshness.

**P2 — Make the decision and research questions explicit**

Owner: `evidence-scout` and `market-problem-discovery`.

1. Extend the current customer-feedback plan with a `research_design` object: decision, question IDs/text, known facts, hypotheses, plausible alternative explanations, and observations that would change the decision. A broad discovery task may start with open questions; do not manufacture a founder thesis or force competing explanations when none are yet meaningful.
2. Add optional `question_ids` to the existing query-plan rows and retain the current `rationale`, `cell_id`, locale, source-family and seed fields. Require valid question associations for new substantive studies; focused factual queries retain their small contract.
3. Carry question associations through query schedules, capture memberships and subsequent source review. A keyword match is not an answer to a question.
4. Before each additional batch, record the material gap, intended information gain and the reason for the selected source/query change. Stop with an explicit coverage/method decision when another search is unlikely to help.
5. Include successful alternatives, non-adoption and contradictory accounts where relevant. Inspect rejected records for missed local vocabulary. Preserve prior query rounds and explanations for added/dropped questions.
6. Update entry skills and workflows to reuse standing paid-evidence authorization; eliminate instructions that ask again simply because a valid evidence query uses paid credits.

Files: `plan_customer_feedback.py`, `collect.py`, `research_queries.py`, affected wrappers; `schemas/pain-query-plan.schema.json`; `references/research-query-calibration.md`, `references/voc-research-method.md`, and the selected research skill workflows.

Acceptance: a substantive preview shows the decision/questions and allocated source coverage; executable ledgers preserve the associations. A new question can arise from the sources without rewriting historical research intent. No new mandatory interview or permission step is introduced.

**P3 — Compare episodes and produce defensible findings**

1. Extend `build_experience_ledger.py` to preserve episode sequence, source-local speaker identity, incident identity where known, and explicit links to later updates/resolutions. Do not infer cross-site identity or independent-person counts from matching display names.
2. Add a comparison-output option to that existing command: a generated Markdown/JSON view of reviewed episodes by role, trigger, alternative, behavior, outcome and consequence. The evidence/review artifacts remain authoritative; editing the view does not alter evidence.
3. Reuse the existing codebook with clear inclusion/exclusion rules, examples, revision notes and provisional unexpected codes. Compare meaningful differences before grouping. A rare consequential incident remains visible even if it does not form a repeated theme.
4. Introduce synthesis contract v3 within `schemas/customer-voc-synthesis.schema.json`, keeping v1/v2 readable. Require study identity, question associations, bounded finding text, support, contrary cases or actual counter-search scope, applicability limits and next investigation for new substantive completion.
5. Reuse U/R item `context`, `scope`, `assessment`, `inference_rationale` and `code_ids`. Add only absent fields such as explicit alternative explanations, distinguishing observations and question IDs. Allow `unknown`/`not_assessed` with reasons. A finding can be occurrence, adequate service or unresolved uncertainty.
6. Extend existing claim-specific confidence assessment to explain relevance, source limitations, data richness and fit with exceptions. Keep recurrence, importance, unmetness and payment as separate claims/assessments; do not average them into an opportunity score or label this formal CERQual.
7. Add a small example set to the research reference: vague topic versus bounded finding; unjustified causal claim versus plausible explanation; one event versus repeated pattern; feature request versus independent need; failed workaround later resolved.

Acceptance: exact spans remain checkable; chronology and negation survive extraction; combined themes have a reason; contradictory contexts remain visible; a single account cannot quietly become a population or payment conclusion. Validators check structure and provenance, while semantic quality is measured in P7.

**P4 — Verify claims and bind completion to the correct evidence**

1. Add a `verification` object to existing claim records: claim-text digest, evidence/source-review digests, verification question, supporting/contrary passage locators, support assessment (`supported`, `contradicted`, `unsupported`, `unresolved`), rationale, reviewer type and review mode. Keep epistemic type (observation/inference/hypothesis) separate from support status.
2. Prepare a separate review pass from the claim, question, declared scope and original evidence, with minimal author rationale. Record inline review honestly; a fresh context is not automatically an independent person or provider. The reviewer can identify missing evidence and unresolved alternatives.
3. Extend `validate_synthesis.py` to check the new verification contract and source spans. Material factual claims with unresolved support cannot be published as established. Explicit hypotheses can remain in exploratory outputs. An inference needs reviewed premises and a rationale, not a fabricated direct quotation.
4. Extract reusable pure validation functions from the current VOC/claim CLI entrypoints. Add one thin `validate_research_pack.py` orchestrator that calls them and checks cross-artifact associations; it must not duplicate their rules. Every material U/R finding and candidate assertion must reference current claim IDs covering its actual statement and scope. Material means an assertion used to establish customer need, consequence, unmetness, recurrence, payment, candidate ranking or a proposed commitment. Require corresponding verification records even for unresolved claims; only supported claims can be presented as established. An empty/unrelated claim ledger cannot validate nonempty material findings. A genuine zero-finding conclusion remains valid when its coverage and limits are documented and it makes no unsupported absence-of-demand claim. Mechanical ID checks establish association; the separate review checks semantic coverage and missing claims.
5. Bind the pack to the run's independently supplied study/case/question/locale identity. Use existing source bindings for imported/shared/foreign evidence and state its applicability. Matching titles or a segment copied from the pack itself is insufficient.
6. Both legacy and modern `workspace.update_stage` closure paths invoke the shared validator for ordinary `problem_validation` completion. Require current segment/journey/pain artifacts, applicable topic/entity coverage dispositions, and reviewed findings. Preserve explicit scoped overrides and revision checks.
7. Store a validation receipt inside the existing checkpoint: contract version, target identity, exact input hashes, validator result, claim readiness and material-gap disposition. Persist decision scope (case, customer segment/job, market/locale and material limits) and completion basis (`evidence_validated` or `owner_override`) in that checkpoint. For an override, reference its existing decision/event ID, authorized stages/routes, reason, current assessment revision and selection generation where applicable; do not create a second approval ledger or invent a passing evidence receipt. Legacy work uses manifest revision/input hashes where those modern identifiers are absent. The receipt's inputs exclude the receipt/checkpoint itself to avoid hash cycles. Recheck hashes/revisions before commit and at downstream consumption.
8. Keep discovery completion distinct from validated pain. An `insufficient_evidence` study may finish with that honest result. It cannot yield an ordinary problem-validation pass. A `scoped` pack can support a scoped pain decision only when that scope matches the proposed commitment and remaining gaps are explicitly nonmaterial; otherwise retain the block or explicit owner override.

Use one shared applicability check in routing and downstream stage/publication paths; a project-wide Boolean pain pass is insufficient. Derive the requested commitment scope from the current selected brief/decision, not an arbitrary caller label. Exact scope matches are straightforward; narrower use requires explicit reviewed applicability against the recorded material limits. Do not build a general segment ontology. If scope is unknown, report the missing decision information rather than treating it as covered.

| Current basis | Requested downstream use | Result |
| --- | --- | --- |
| Current evidence receipt, ordinary or scoped | Same scope, or explicitly reviewed narrower application; gaps nonmaterial to this commitment | Permit that use and carry its limits |
| Current evidence receipt | Broader/different scope, material unresolved gap or unknown applicability | Block the commitment pending targeted evidence/applicability review or an explicit owner override |
| Current owner override | Same authorized case/scope/stage/route and current revision/selection | Permit the authorized exception, labelled as override; do not claim validated pain |
| Missing/stale receipt or stale/out-of-scope override | New linked commitment | Report the specific re-review or current-scope authorization needed; preserve historical artifacts |
| Insufficient evidence, including zero findings | Complete discovery/reporting | Permit honest research completion; do not unlock ordinary Business commitments |

Files: `build_claim_ledger.py`, `validate_synthesis.py`, `validate_customer_voc_synthesis.py`, `workspace.py`, `route_workflow.py`, `discover_market_problems.py`; `schemas/claim-record.schema.json`, `schemas/stage-checkpoint.schema.json`, `schemas/customer-voc-synthesis.schema.json` and relevant manifest validation.

Acceptance: placeholder-only closure, findings with an empty/unrelated claim ledger, wrong-study/case import, edited reviewed evidence, edited claim, stale revision and replayed receipt are rejected through normal producer/consumer paths. Exercise same-scope and reviewed narrower use, narrow-to-broad misuse, current authorized override, and stale/out-of-scope override through both routing and publication. Genuine zero-finding/scoped/insufficient outputs retain their distinct meanings. Receipt validity does not prove the analyst's interpretation or owner authorization.

**P5 — Make the report decision-focused and consistent with its evidence**

1. Revise `templates/project/market-discovery-report.md` and relevant skill output guidance. Remove the current severity × frequency formula and its S×F column. Replace them with evidenced consequence, observed alternative performance, uncertainty, comparison limits and why another investigation matters.
2. Put answer/scope, decisive findings, strongest contrary evidence, consequential unknowns and next action first. Keep detailed source/coverage logs linked and accessible. Include fewer or no candidates when that is the result.
3. Give every candidate a stable ID, structured statement, associated question IDs and U-need/claim IDs. Generate candidate summaries from this checked structure. Analyst narrative remains possible, but new material claims enter the same claim ledger.
4. Update discovery finalization and report-template checks together. Validate candidate identities and actual associations, not just count/headings. Generate from the checked findings/claim IDs and include every additional material narrative assertion in that mapping. The final source-review pass explicitly checks for omitted claims and meaning/scope changes; it cannot mark the report reviewed solely because its linked subset passes. Review and bind the final report bytes after rendering; later edits require re-review before the result is reused as current.
5. Offer concise and detailed renderings of the same validated findings. They must preserve the same conclusions, scope and material uncertainty. Avoid a second source of decision state.
6. Keep the existing one-decision-question coaching rule when the next step depends on the founder. Do not end every completed factual answer with a compulsory question.

Acceptance: no S×F ranking survives generated outputs; unrelated candidate text cannot finalize against another need; removing a material qualification from the short report fails semantic review; useful negative or inconclusive results render without manufactured opportunities.

**P6 — Establish four modules, compact context and explicit handoffs**

| Module | Entry and ownership | Completion evidence |
| --- | --- | --- |
| Market research | Existing discovery/evidence skills, case-local or declared shared research roots | Reviewed bounded findings, coverage limits and source-verification result |
| Branding | Existing `brand-designer` and specialists, `branding/` | Coherent approved identity/assets, applicable visual and accessibility review |
| Marketing | Existing `marketing-strategy-builder` and social/monitoring skills, explicit `marketing/` destination for new independent work | Evidence-linked message/offer application, testable campaign hypothesis and measurement plan |
| Website | Existing website/UI skills, `digital-assets/website/` | Rendered user-task evidence, content/claim fidelity and applicable functional/accessibility checks |

1. Add module ownership and module-entry-reference metadata to `config/skill-catalog.json`, consumed by the existing router and route validator. Shared specialists may be usable by several modules but each artifact has one owner. Strategy/operations remain explicit specialist ownership; they are not forced into a misleading research label.
2. Add four short module references under `references/modules/`. Keep shared scope, authorization, provenance and routing principles in `AGENTS.md`; move detailed research procedures behind the research entry. Existing `.agents/skills/<name>/SKILL.md` paths remain discoverable. Catalog checks verify reference existence and ownership, not token savings.
3. Add `marketing` to `subprojects.py` and the strict layout-3 schema alternatives. Keep old layouts valid. Extend start/resolve/publication code to honor registered destination paths instead of reconstructing them from hardcoded defaults.
4. Specify Marketing entry explicitly: `standalone` consumes a supplied established-business brief/position; `business_linked` consumes a selected current venture decision. Route checks continue to enforce business-linked strategy prerequisites. A caller flag alone cannot relabel the continuation of a blocked venture as independent work. Add positive/negative routing examples for supplied-brief execution and linked launch work.
5. Store Marketing workstream state using the existing umbrella manifest/publication machinery. Add only a versioned workstream record for brief, status, artifact refs and imported decisions. Do not introduce a second Business stage machine or duplicate the business strategy. New standalone Marketing can start without scaffolding research/branding/site contents.
6. Extend existing source bindings and module manifests with explicit handoff purpose and accepted decision references: owner, revision, artifact path/hash, applicability, unresolved limits and destination. Reuse Business-to-Brand tooling for its existing boundary; other consumers use shared binding validation.
7. A changed upstream input makes downstream consumption require review; it does not silently rewrite outputs or relaunch other modules. Consumers access original evidence when a claim matters, rather than relying only on a compressed handoff.
8. Give each module a representative good/poor example and a focused review rubric. Branding reviews actual rendered uses; Marketing checks buying context, proof, hypothesis and learning; Website checks the rendered key user task; Research checks source/interpretation/uncertainty. Evaluation includes these outputs in P7.
9. Make compaction snapshots session-specific and use current workspace resolvers for legacy, case and layout-3 locations. Save selected module/case/run, open question, accepted decisions and next action. Do not dump every workspace into every session. Test two sessions and moved/stale references. Existing hook scripts can change without editing hook registration; any later settings edit follows the repo's explicit-approval rule.
10. Document optional source-worker packets: question/scope, relevant evidence, allowed retrieval, allocation, exclusive output directory and required handoff. Only the coordinator writes shared synthesis. No worker or additional model is launched automatically by module entry.

Files: `AGENTS.md`, `references/subprojects.md`, `references/runtime-routing.md`, `references/modules/` (new); `config/skill-catalog.json`, `config/workflow-routes.json`; `scripts/subprojects.py`, `scripts/project_workspace.py`, `scripts/case_workspace.py`, `scripts/route_workflow.py`, `scripts/enforce_skill_route.py`, `scripts/validate_skill_routes.py`; existing brand/website workspace tools; `.claude/hooks/precompact.py`, `.claude/hooks/postcompact.py`; applicable schemas and skill workflows.

Acceptance: four independent entry scenarios and their explicit handoffs work in fixtures; no module writes another module's authoritative artifacts; stale handoffs are detected; standalone Marketing does not waive linked venture gates; legacy paths remain resolvable; session snapshots remain isolated. Live host behavior is reported separately from local hook tests.

**P7 — Run the quality comparison and decide whether to adopt**

Execute P7a for Research immediately after P5. Execute P7b for each other module after its P6 changes, using its pre-change baseline and criteria fixed before tuning. These are two uses of the same evaluation tooling, not two new systems.

1. Add a small runner under the existing evaluation tooling, with separate modes for fixture validation, importing/scoring saved model outputs, and explicitly configured live runs. Normal setup/CI runs offline; it must never start paid model calls implicitly.
2. Run baseline and revised research workflows against the same frozen packets with comparable information, tools and effort. Record models, prompts, source hashes, tool traces, latency and usage. Then evaluate fresh-web tasks separately, retaining their variable coverage.
3. Use four-point anchored ratings for source fidelity, consequential-episode coverage, explanatory usefulness, theme boundaries, counterexample handling, uncertainty and decision usefulness. Record comments/evidence for each rating. Do not let a weighted mean conceal a critical error.
4. Critical failures: fabricated/meaning-altered quotation, supplier voice presented as customer proof, unsupported payment/prevalence claim, or wrong-study attribution. A run with one cannot receive an overall quality pass. Valid disagreement over theme interpretation is not automatically an error.
5. Blind version identity, randomize output order, repeat representative tasks, and record independent versus inline/model review accurately. Calibrate model graders with human/expert assessments when available. Without that calibration, publish provisional automated results, not human-validated gains.
6. Add two representative tasks per other module: Branding (direction-to-assets consistency and revision consistency), Marketing (message/proof and campaign learning), Website (offer comprehension/claim fidelity and key-task completion on the rendered fixture). Preserve subjective alternatives and actual visual/user-task evidence.
7. Use task-level wins/ties/losses and dimension changes against the criteria frozen in P0 to choose revisions. Keep unsuccessful outputs and reviewer disagreements in the report; do not revise the threshold after observing results. Claim improvement only for the measured tasks/dimensions; a small evaluation does not establish general superiority.

Acceptance: a reproducible comparison report includes failures, reviewer disagreements and cost/coverage limitations. Adopt changes that demonstrate a useful improvement without critical regressions. If evidence is inconclusive, retain proven integrity fixes and iterate on the implicated prompt/method; do not claim the analytical goal achieved.

**P8 — Optional provider extraction justified by maintenance benefit**

This is deferred maintenance, not a prerequisite for the analysis-quality milestone. Before each extraction, identify a concrete benefit such as eliminating duplicated retention logic implicated in a defect or isolating a provider that cannot otherwise be changed safely. Keep an extraction only if its benefit outweighs the migration/regression surface. File length, folder symmetry and completion of an adapter catalog are insufficient reasons. Small helpers required by P1–P4 remain part of those fixes.

1. Keep `collect.py` as the CLI/import compatibility facade. Extract only the scheduling/allocation, normalization/provenance or persistence helpers needed for the justified change under `scripts/evidence_scout/`.
2. Move only the provider implementations justified by that benefit into `scripts/evidence_scout/providers/`; assess repaired YouTube/social paths first. Do not precommit to extracting every provider. Preserve the exact-plan schedule, capture authorization, status semantics and source memberships.
3. Pass shared request/credential/capture services explicitly. Retain their central policy; no provider adapter obtains a broader permission path or independent request budget.
4. Run provider contract checks after each extraction and a representative full collection fixture at the end. Compare output content and metadata, allowing only declared version/timestamp changes. Recheck research-quality tasks if the data supplied to analysis changes.
5. Keep source workers optional. Their coordination protocol can be exercised synthetically; live parallel use remains selected per task and authorization.

Acceptance: imports, wrapper flags and CLI behavior remain compatible; no output-quality regression from changed ordering, truncation, attribution or recovery. Reduced file size alone is not a success measure.

**Compatibility, publication and recovery**

- New contracts are versioned. v1/v2 VOC packs remain readable as historical/unassessed data for the new completion policy. Existing checkpoints are not silently rewritten or grandfathered into verified status; a new linked commitment applies the P4 decision table, accepting a current applicable evidence receipt or a current explicitly authorized exception. Historical overrides without enough scope/revision information do not become reusable authorization automatically.
- Updating a study uses explicit conversion that retains old inputs, carries unresolved fields and never synthesizes missing review decisions. Use immutable source copies plus versioned output paths for fixture rehearsals.
- Existing Marketing files stay at their current paths. Independent `marketing/` destinations are created only for requested new work. Moving existing artifacts is a separate explicit migration, rehearsed on a copy with maps/digests/journals; it is not part of this implementation's default execution.
- Publication helpers remain the state authority. Check current revision and content hashes under the relevant lock before committing completion; a failure leaves prior current state intact and recoverable through the existing journal.
- Roll back code/template phases independently while retaining versioned evidence and reports. Never delete research or restore old checkpoint files to force a pass. A reader encountering an unsupported contract version reports that incompatibility.

**Validation sequence during implementation**

Use relevant subsets first: query-expansion/calibration and VOC collection tests for P1–P2; VOC quality/feedback/claim fixtures for P3–P4; workspace/case/discovery tests for P4–P5; setup/scope/runtime-routing/Claude-hook and module workspace tests for P6; evaluation fixture validation and saved-output runs for P7; adapter/collector contracts for P8. Add regressions for the exact newly established failures and meaningful order/interruption edges.

At integrated milestones run `python3 scripts/validate_skill_routes.py`, `python3 scripts/run_evals.py`, and `bash scripts/validate_setup.sh`, plus the applicable existing website fixture checks if its output workflow changes. Report environment failures separately and rerun with the required permissions where necessary. `run_evals.py` remains labelled structural; semantic comparison results have their own report. No tests were run merely to write this plan.

**Implementation batches**

| Batch | Contents | Ready to hand off when |
| --- | --- | --- |
| 1 | P0 baseline assets + P1 capture fixes | Four failure scenarios are preserved; retention/recovery fixes pass their focused checks |
| 2 | P2 research design + P3 episode/finding contracts | Producers, schemas, references and examples agree; historical inputs remain readable |
| 3 | P4 verification/closure + P5 report rendering | All material findings map to verified claims; scope/override rules govern routing and publication |
| 4 | P7a research comparison | Research gains/failures are measured against the frozen criteria before broader architecture work |
| 5 | P6 module ownership, Marketing entry, handoffs, resume + P7b module comparisons | Independent/linked paths work and module-specific quality outcomes are recorded |
| Optional 6 | Only justified P8 adapter extraction + integrated checks | A named maintenance benefit is delivered without changing evidence behavior |

**Review disposition and practical benefit**

The independent review rated the earlier plan **FLAG, 75/100**. Its five findings are incorporated here; that historical score is not a review of this revision. The earlier positive inline self-score is superseded, with no replacement self-score.

| Review finding | Change retained | Practical benefit |
| --- | --- | --- |
| Unverified findings can coexist with a valid claim ledger | P4 exhaustive finding/claim coverage and P5 final narrative review | Prevents approving conclusions that verification never examined |
| Scoped evidence and overrides have ambiguous downstream meaning | P4 persisted scope/basis and shared consumer decision table | Prevents expanding narrow evidence into broad commitments while preserving authorized exceptions |
| Resume resets consumed allowances | P1 persistent operation accounting inside existing checkpoints | Makes resumed coverage/retries reproducible without new spending gates |
| Held-out tasks may share source episodes; criteria can move | P0 grouped splits and criteria frozen before tuning | Reduces misleading gains from leakage or post-result threshold changes |
| Architecture delays the quality decision | P7a after P5; P7b with modules; P8 optional | Establishes whether research improves before investing in broader restructuring |

No new agents, general-purpose policy engine or standalone accounting service are required. Automated dependency-graph analysis was unavailable during review; relevant callers were inspected directly. This revision has not received a fresh independent review. Implementation checks, human-calibrated quality comparisons and live host evidence remain work to perform, not assumed results.
