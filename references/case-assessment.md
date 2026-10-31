# Case assessment and selected-plan contract

For new projects this contract lives inside `business-analysis/`; see [subprojects.md](subprojects.md) for Branding and Digital Assets. Older version-2 projects keep their existing root.

Use for version-2 case appraisal and selected business-plan assembly. Reuse strategic-positioning.md for entrant fit, evidence definitions and economics. This is the shared output contract, not an additional stage machine. The publisher and validators enforce the field-level contract; each command's `--help` and the schemas under `schemas/` are the procedure.

## Resolve before writing

New projects use `init_project.py --project <name> [--case <id>]`; add a case with `scripts/case_workspace.py add`. Never infer selection from research focus or an old umbrella pass.

Route with `route_workflow.py --project <slug> --case <id> --intent case-appraisal --task-scope strategy --check-skill opportunity-risk-designer`. A registered case needs initial sourced segment, journey and pain research; findings may be weak or unresolved. Appraisal needs no passed pain gate, and it does not authorize commitments, outreach, payment collection or paid recruitment. Do not invoke GTM/pilot/startup workflows to bypass their prerequisites.

## Research content

Keep the opinion/behavior/money scorecard in supporting appraisal material and translate its implications into plain language in `case_insights.md`. For each relevant dimension explain evidence, inference, assumptions, counter-evidence and unknowns:

- Customer choice: trigger, user/buyer/payer, workaround including doing nothing, switching friction, trust, why this entrant might be chosen.
- Commercial evidence: current spend and prices separately from stated intent. A complaint, job posting, supplier claim or signup does not establish a purchase or willingness to pay this entrant.
- Reach and repeat value: concrete access, funnel denominators, founder effort, time to value, repeat/referral and reasons to cancel.
- Feasibility: build/buy/partner, people/data/permissions, lead times, capacity, support, cash and founder dependence.
- Decision: strongest support and counter-evidence, failure paths, pivotal unknown, proportionate next test and its predeclared interpretation. Insufficient evidence permits continued investigation, not a forced winner or automatic rejection.

Keep need, promise, operating configuration and defensibility as separate provisional findings. Adequate service, insufficient evidence and a viable business with no moat are distinct valid findings; appraisal never selects execution. Compare cases at comparable evidence coverage; archive superseded advice rather than appending contradictory recommendations.

## Publication and ownership

The appraisal owner assembles supporting `feasibility.md` and `business-case.md`; other specialists contribute evidence. `case_insights.md` is the single current reader assessment and is refreshed through the insights publication contract after a material appraisal. Do not create all files for a dormant case. Publish with `case_workspace.py appraise --workspace projects/<project> --case <id> --input <draft.json> --decision-id <id> --reason <change>`.

Read the current manifest and source bytes; never invent source bindings. Material changes increment the assessment revision and invalidate prior passes; never mark altered evidence, concepts or economic assumptions `material_change: false`. A researched appraisal needs an eligible reviewed case run with its claim ledger bound; authored summaries are not research proof, and an intake hypothesis belongs in progress insights until reviewed evidence exists.

Renewed appraisals use publication contract version 2 with all nine `business_plan_sections`. Put `{{evidence_claim.<id>}}` beside each material reviewed fact; the renderer takes URLs from reviewed evidence or bound manual captures, never from authored links. Label founder statements, assumptions, inferences and model results as such. A search snippet or secondary account is never an inspected original.

For a final appraisal run `case_workspace.py prepare-appraisal`, give the rendered outputs, `review-bundle.json`, original passages, contrary evidence and founder constraints to a separate reviewer, and bind the stored review as `independent_review`. A progress appraisal can publish without final review, with its limits stated.

## Economics

The helper calculates economics results; agents author inputs, never results (`python3 scripts/case_economics.py <inputs.json>`). Numeric unknowns are null. Provenance labels are assumptions unless supported by a declared binding. Never use pass-through premiums as revenue or count founder labor twice (owner cash compensation is separate from imputed opportunity cost). No arbitrary price multipliers, retention defaults, guessed ranges, invented probabilities or unsupported lifetime-value forecasts. Conditional arithmetic never establishes purchase demand.

Quote model-derived claims only through `{{economics.…}}` placeholders with the reviewed `economics_input_digest`; literal model values fail publication. `economics_inputs.viability_targets` records the founder's test (profitable-by month, maximum cash need, owner income); quote `{{economics.results.viability.status}}`, never hand-write the verdict. Unresolved means schedule or targets are missing, not that the business is unviable. Missing scenarios or sensitivities stay visibly unresolved with a reason. Optional charts: `scripts/chart_case_economics.py` (conditional arithmetic, not forecasts).

Source-attributed decision-relevant figures use `{{source_numeric.<id>}}`; inspect the original source first, then check with `python3 scripts/verify_numeric_claims.py --workspace <business-root> --packet <draft.json>`. Unverified claims need a reason and render as unverified. The check compares declared fields only; it does not certify extraction or surrounding prose.

## One selected business

Select only from an explicit user choice: `case_workspace.py select ... --reason <user-decision>`. Selection does not validate the idea; researching B must not select it or invalidate unrelated A.

Only startup-business-builder assembles the root `strategy/business-plan.md`, publishing with `case_workspace.py plan`. Missing sections remain visible. A complete document is not evidence of viability or external-action approval. A newly answered question or deep dive makes selected-case insights pending and blocks plan use until reconciled. Final plans need `prepare-plan` and a separate review. A nine-heading document with generic filler remains a semantic-review failure even if the publisher accepts its structure.

## Current, history and recovery

The publisher owns metadata, snapshots and the evolution timeline. Never edit manifests, generated timeline, selection generations or calculation results directly. Use `case_workspace.py correct` for a material interpretation correction, then re-review affected evidence; never copy old passes. If `history/pending.json` exists, run `case_workspace.py recover --workspace <project>` before resuming. Declared bindings cannot detect all semantic dependencies.

## Commit decision review

A strategy plan with `verdict: commit` must include `decision_review` (`schemas/strategy-plan.schema.json`): at least two causally distinct failure stories with a probability basis (dated source or explicit unknown; never invent a base rate), stop rules tied to a KPI, threshold, window, owner and pre-committed action, and behavioral precommitments. Validate with `scripts/strategy_review.py validate`. These create no monitoring job or spending authority, and schema checks do not establish causal independence or truth.

## Per-case business plan extension

V2 appraisal generates a provisional `business-plan.md` (`appraisal_draft`). Full per-case publication uses startup-business-builder's `case-business-plan` mode: `case_workspace.py prepare-case-plan` then `case-plan`, against `schemas/case-business-plan.schema.json`. Prerequisites: initial reviewed case research, a bound eligible claim ledger and current reviewed `case_insights.md`; case selection and a passed pain gate are not prerequisites for a conditional planning document.

The nine section keys: `business`, `customer_market`, `competitive_choice` (including international commercial precedents and failed examples), `product_revenue`, `acquisition_sales` (separate unpaid learning recruitment from selling), `delivery_team`, `finances`, `milestones_risks`, `funding_legal_ip`. Supported sections need their original sources; missing/not-applicable sections explain the consequence and next action. Document publication (`progress`/`final`) and evidence basis (`desk_research`/`offer_tested`/`pilot_informed`) are independent; signups, interviews, purchases and repeat use are distinct observations. A `final` case plan needs an independent review with different author and reviewer identities; the plan cannot cite itself.

Plan use checks insight/source/economics digests; research completion does not imply the plan is current. Do not bulk-rename legacy files. A selected strategy plan for a case with a canonical plan binds it via `case_plan_binding`; final execution-plan publication requires the case's final plan review.
