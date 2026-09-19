# Case assessment and selected-plan contract

For new projects, this contract lives inside `business-analysis/`; see [subprojects.md](subprojects.md) for independent Branding and Digital Assets. Older version-2 projects retain their existing root.

Use for version-2 case appraisal and selected business-plan assembly. Reuse strategic-positioning.md for entrant fit, evidence definitions and economics. This is the shared output contract, not an additional stage machine.

## Resolve before writing

New projects use `init_project.py --project <name> [--case <id>]`. Register another case with `python3 scripts/case_workspace.py add --workspace projects/<project> --case <id> --title <title>`. Existing unversioned projects keep their research paths until explicitly migrated. Never infer selection from research focus or an old umbrella pass.

Route with `route_workflow.py --project <slug> --case <id> --intent case-appraisal --task-scope strategy --check-skill opportunity-risk-designer`. The existing checked envelope carries `case`. A registered case needs initial sourced segment, journey and pain research; those findings may be weak or unresolved. Appraisal needs no passed pain gate. It does not authorize commitments, outreach, payment collection or paid recruitment. Do not invoke full GTM/pilot/startup workflows to bypass their prerequisites.

## Research content

For each relevant dimension explain evidence, inference, assumptions, counter-evidence and what remains unknown:

- Customer choice: trigger, user/buyer/payer, workaround including doing nothing, switching friction, trust and why this entrant might be chosen.
- Commercial evidence: current spend and prices separately from stated intent. A complaint, job posting, supplier claim or signup does not establish a completed purchase or willingness to pay this entrant.
- Reach and repeat value: concrete access, acquisition funnel denominators and founder effort; time to value, renewal/repeat/referral and reasons to cancel. Use windows appropriate to the service; annual needs do not require daily app use.
- Feasibility: build/buy/partner, people/data/permissions, lead times, capacity, manual review/rework/support, cash and founder dependence. Investigate AI reliability only where material.
- Decision: strongest support and counter-evidence, consequential failure paths, pivotal unknown, proportionate next test and its predeclared interpretation. Insufficient evidence permits continued investigation, not a forced winner or automatic rejection.

Keep need, specific promise, feasible operating configuration and defensibility as separate provisional findings within these existing documents. Apply `strategic-positioning.md` for customer choice, available-assets/clean-sheet/transition comparisons and benefit/barrier/value capture; use reviewed need locators and existing test references. No new report or lifecycle stage. Adequate service, insufficient evidence and a viable business with no identified moat are distinct valid findings; appraisal never selects execution.

Compare cases at comparable evidence coverage and founder constraints. Corrections change ranking only when their implications justify it. Current documents must agree; archive superseded advice rather than appending contradictory recommendations.

## Publication and ownership

The appraisal owner assembles `README.md`, `feasibility.md`, `business-case.md`; other specialists own their research artifacts and contribute evidence/section drafts. Use the three `templates/project/case-*.md` templates proportionately. Do not create all files for a dormant case. Publish with:

`python3 scripts/case_workspace.py appraise --workspace projects/<project> --case <id> --input <draft.json> --decision-id <unique-id> --reason <change>`

The draft contains current `assessment_revision` and `manifest_revision` (write-conflict check, including cosmetic edits), `documents` keyed by allowed filename, `source_bindings` and optional `economics_inputs`. A `comparison` object requires `summary`, `principal_uncertainty` and `next_action`; these current case-owned findings generate the Business overview. Each source binding contains project-relative `path`, its SHA256 `digest`, a source/claim `locator`, and scope-specific `applicability`. Read the current manifest and source bytes; never invent bindings. Material changes increment the assessment revision and invalidate prior passes. Retain unspecified sections only if still valid; otherwise update them together. Do not use `material_change: false` for altered evidence, concepts or economic assumptions.

The helper calculates economics results; agents author inputs, never results. Use `python3 scripts/case_economics.py <inputs.json>` to inspect a model. Numeric unknowns are null. Inputs require model (`transactional`/`recurring`), currency, monthly period, a nonempty `unit` definition, venture-receipt revenue basis, acquisition basis and explicit revenue/service/partner/refund/acquisition/fixed/owner-cash/capacity values. Provenance labels are assumptions unless supported. Cash claims also need opening cash, horizon, explicit startup cash cost, cash lags and a monthly sales/new-customer schedule; recurring models need opening customers, retention and billing timing. Never use pass-through premiums as revenue or imputed founder labor twice. No arbitrary price multipliers, retention defaults, or unsupported lifetime-value forecast.

## One selected business

Select only from an explicit user choice: `case_workspace.py select --workspace <project> --case <id> --configuration <chosen-scope> --decision-id <id> --reason <user-decision>`. Clearing or switching selection changes its generation; selection does not validate the idea. Researching B must not select it or invalidate unrelated A.

Only startup-business-builder assembles the root `strategy/business-plan.md` from current case research and the existing structured `strategy-plan.json`. Its `publication_base_digest` is the SHA256 of the existing root structured plan, or null if none exists, and rejects overlapping stale drafts. Its `execution_binding` must match the selected case/configuration/generation/assessment revision and economics input digest. `business_plan_sections` covers business, customer_market, competitive_choice, product_revenue, acquisition_sales, delivery_team, finances, milestones_risks and funding_legal_ip; each has status supported/provisional/missing/not_applicable, explanatory text, and source bindings for supported claims. Missing sections remain visible. Publish with `case_workspace.py plan --workspace <project> --case <id> --input <strategy-plan.json> --decision-id <id> --reason <change>`. Existing startup prerequisites still apply. A complete document is not evidence of business viability or external-action approval.

## Current, history and recovery

One generated project overview points to each current case and the selected plan. The publisher owns metadata, snapshots and the single evolution timeline. Never edit manifests, generated timeline, selection generations or calculation results directly. Use `case_workspace.py correct ... --case <id> [--source <project-relative-path>]` for a material interpretation correction; a shared-source correction includes its declared consuming cases. Old handoffs cannot be reused after A→B→A.

If `history/pending.json` exists, current state is unavailable to dispatch/consumers. Run `case_workspace.py recover --workspace <project>` before resuming; it completes a committed publication or restores before-images, preserving outside edits by stopping on conflicts. Original runs remain immutable. These CLI/hook contracts are not a filesystem sandbox, and declared bindings cannot detect all semantic dependencies automatically.

Economics may include `scenarios` with `downside` and optional `upside` input overrides; each is recalculated from the base inputs, without invented probabilities. Leave unsupported values unknown. `provenance` entries marked evidence_backed need `source_refs` matching a declared binding path or `path#locator`. Conditional arithmetic never establishes purchase demand. Service costs begin when recurring customers are served even if billing is deferred. Owner cash compensation is separate from imputed opportunity cost; do not include the same labor in both service expense and owner compensation.

Stage publication in case mode requires the run's captured context (`run_dir`) or explicit `expected_assessment_revision`, checked under the project lock. After a correction, re-review the affected evidence; never copy old passes. Business-to-brand context must itself carry the selected `execution_binding`; use the current root structured plan and publish snapshots under root `branding/`. Consumers reject old or mismatched bindings even after switching back to the same case.

## Numerical prose and derived-input corrections

When prose makes model-derived claims, supply the author-reviewed `economics_input_digest` from the calculator and use placeholders such as `{{economics.results.contribution_per_unit}}`, `{{economics.results.required_sales}}`, `{{economics.inputs.capacity_per_month}}`, or `{{economics.results.cash.months.0.contribution}}`. Apply this to comparison summaries as well as case documents. Business-plan sections carry their own `economics_input_digest` for model claims. Literal model values, including multi-line values, stale digests and invalid references fail publication. Historical/source-attributed observations remain ordinary evidence prose; numerical checks do not prove unrestricted natural-language consistency. After a correction, reassess conclusions as well as refreshing the digest.

Direct research builders retain their actual local inputs in `.case-context.json` and stage source bindings. Use `--source-bindings <bindings.json>` to declare project-relative paths, digests, locators and applicability for shared inputs. Case-local input files are bound automatically to the same case use. Explicit upstream run bindings are retained recursively; cycles and changed inputs fail closure. This records declared dependencies, without inventing applicability or moving raw runs.

`owner_cash_per_month` is additional cash compensation, excluding amounts already included in service expense. Declare `owner_cash_in_service_cost`; true with additional owner cash is rejected as ambiguous double counting. `imputed_owner_labor_per_month` is unpaid opportunity cost, separate from cash payments; null stays unresolved. Monthly recurring `contribution` includes period service and new-customer acquisition costs independently of receipt/payment lags. `surplus_after_imputed_labor` is separately reported.

Supported `sensitivities` map at most three drivers (revenue_per_unit, service_per_unit, acquisition_per_new_customer, lead_to_customer, monthly_retention, capacity_per_month) to one to three explicit values each. Base/downside scenarios and decision-changing sensitivities remain visibly unresolved when unavailable; explain with `scenario_limit_reason` and `sensitivity_limit_reason`. No guessed ranges or probabilities are required to get provisional arithmetic. Unknown input keys fail rather than being silently digested.
