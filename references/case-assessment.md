# Case assessment and selected-plan contract

For new projects, this contract lives inside `business-analysis/`; see [subprojects.md](subprojects.md) for independent Branding and Digital Assets. Older version-2 projects retain their existing root.

Use for version-2 case appraisal and selected business-plan assembly. Reuse strategic-positioning.md for entrant fit, evidence definitions and economics. This is the shared output contract, not an additional stage machine.

## Resolve before writing

New projects use `init_project.py --project <name> [--case <id>]`. Register another case with `python3 scripts/case_workspace.py add --workspace projects/<project> --case <id> --title <title>`. Existing unversioned projects keep their research paths until explicitly migrated. Never infer selection from research focus or an old umbrella pass.

Route with `route_workflow.py --project <slug> --case <id> --intent case-appraisal --task-scope strategy --check-skill opportunity-risk-designer`. The existing checked envelope carries `case`. A registered case needs initial sourced segment, journey and pain research; those findings may be weak or unresolved. Appraisal needs no passed pain gate. It does not authorize commitments, outreach, payment collection or paid recruitment. Do not invoke full GTM/pilot/startup workflows to bypass their prerequisites.

## Research content
- Scorecard: keep the opinion/behavior/money assessment in supporting appraisal material. Translate its decision implications into plain language in `case_insights.md` after reviewing all case inputs.

For each relevant dimension explain evidence, inference, assumptions, counter-evidence and what remains unknown:

- Customer choice: trigger, user/buyer/payer, workaround including doing nothing, switching friction, trust and why this entrant might be chosen.
- Commercial evidence: current spend and prices separately from stated intent. A complaint, job posting, supplier claim or signup does not establish a completed purchase or willingness to pay this entrant.
- Reach and repeat value: concrete access, acquisition funnel denominators and founder effort; time to value, renewal/repeat/referral and reasons to cancel. Use windows appropriate to the service; annual needs do not require daily app use.
- Feasibility: build/buy/partner, people/data/permissions, lead times, capacity, manual review/rework/support, cash and founder dependence. Investigate AI reliability only where material.
- Decision: strongest support and counter-evidence, consequential failure paths, pivotal unknown, proportionate next test and its predeclared interpretation. Insufficient evidence permits continued investigation, not a forced winner or automatic rejection.

Keep need, specific promise, feasible operating configuration and defensibility as separate provisional findings within these existing documents. Apply `strategic-positioning.md` for customer choice, available-assets/clean-sheet/transition comparisons and benefit/barrier/value capture; use reviewed need locators and existing test references. No new report or lifecycle stage. Adequate service, insufficient evidence and a viable business with no identified moat are distinct valid findings; appraisal never selects execution.

Compare cases at comparable evidence coverage and founder constraints. Corrections change ranking only when their implications justify it. Current documents must agree; archive superseded advice rather than appending contradictory recommendations.

## Publication and ownership

The appraisal owner assembles supporting `feasibility.md` and `business-case.md`; other specialists own their research artifacts and contribute evidence/section drafts. `case_insights.md` is the single current reader assessment and must be refreshed through the reviewed insights publication contract after a material appraisal. Existing cases may retain an old README until explicitly converted; new cases do not create one. Use the supporting templates proportionately. Do not create all files for a dormant case. Publish the appraisal with:

`python3 scripts/case_workspace.py appraise --workspace projects/<project> --case <id> --input <draft.json> --decision-id <unique-id> --reason <change>`

The draft contains current `assessment_revision` and `manifest_revision` (write-conflict check, including cosmetic edits), `documents` keyed by allowed filename, `source_bindings` and optional `economics_inputs`. A `comparison` object requires `summary`, `principal_uncertainty` and `next_action`; these current case-owned findings generate the Business overview. Each source binding contains project-relative `path`, its SHA256 `digest`, a source/claim `locator`, and scope-specific `applicability`. Read the current manifest and source bytes; never invent bindings. Material changes increment the assessment revision and invalidate prior passes. Retain unspecified sections only if still valid; otherwise update them together. Do not use `material_change: false` for altered evidence, concepts or economic assumptions.

A researched appraisal now needs an eligible reviewed case run, with its exact `customer-feedback/claim-ledger.json` in `source_bindings`. Three authored segment/journey/pain summaries are not research proof. Reviewed partial evidence permits a bounded provisional appraisal; an intake hypothesis belongs in progress insights until that evidence exists. A shared run needs explicit case applicability and a current ledger binding. Use the same research assessment in router and publisher; direct publisher calls do not waive it.

For a renewed appraisal set `publication_contract_version: 2`, `publication_status: progress|final`, `publication_claims`, and all nine `business_plan_sections` in the existing order. Each section has `status` and decision-useful `text`; `missing` and `not_applicable` also need `next_action` explaining the consequence. The publisher generates `business-case.md` from those sections. Put `{{evidence_claim.<id>}}` beside each material reviewed VOC fact; the corresponding reference names `document`, reviewed `claim_id`, `evidence_id`, bound ledger, `source_kind` and any secondary limitation. Bind the ledger, evidence JSONL and source review. The renderer takes the URL from the reviewed evidence record, never from an arbitrary authored link. For official/contextual facts use the same marker with a bound `manual-captures.json`, `capture_index`, and exact `supporting_passage`; the renderer verifies the retained raw source hash and inserts its source URL and capture date. Semantic review still judges whether that passage supports the statement and whether the source classification is correct. Founder statements, assumptions, inferences and model results must be labeled as such; their own evidence/model bindings still apply. Do not classify a search snippet or secondary account as an inspected original. A legacy packet remains readable, but does not earn v2 publication quality.

For a final v2 appraisal, first run `case_workspace.py prepare-appraisal --workspace <business-root> --case <id> --input <draft.json> --out <fresh-dir>`. Give its rendered outputs, `review-bundle.json`, original passages, contrary evidence and founder constraints to a separate reviewer. Store the review under `cases/<id>/market_research/appraisal/reviews/` with author/reviewer/task identities, exact `bundle_digest`, `reviewed_sources`, outcome and material findings. Bind that file as `independent_review`; the publisher re-renders under lock and rejects changed inputs. A progress appraisal can publish without separate final review, with its limits stated. The local identity record is inspectable metadata, not cryptographic attestation.

The helper calculates economics results; agents author inputs, never results. Use `python3 scripts/case_economics.py <inputs.json>` to inspect a model. Numeric unknowns are null. Inputs require model (`transactional`/`recurring`), currency, monthly period, a nonempty `unit` definition, venture-receipt revenue basis, acquisition basis and explicit revenue/service/partner/refund/acquisition/fixed/owner-cash/capacity values. Provenance labels are assumptions unless supported. Cash claims also need opening cash, horizon, explicit startup cash cost, cash lags and a monthly sales/new-customer schedule; recurring models need opening customers, retention and billing timing. Never use pass-through premiums as revenue or imputed founder labor twice. No arbitrary price multipliers, retention defaults, or unsupported lifetime-value forecast.

## One selected business

Select only from an explicit user choice: `case_workspace.py select --workspace <project> --case <id> --configuration <chosen-scope> --decision-id <id> --reason <user-decision>`. Clearing or switching selection changes its generation; selection does not validate the idea. Researching B must not select it or invalidate unrelated A.

Only startup-business-builder assembles the root `strategy/business-plan.md` from current case research and the existing structured `strategy-plan.json`. Its `publication_base_digest` is the SHA256 of the existing root structured plan, or null if none exists, and rejects overlapping stale drafts. Its `execution_binding` must match the selected case/configuration/generation/assessment revision and economics input digest. `business_plan_sections` covers business, customer_market, competitive_choice, product_revenue, acquisition_sales, delivery_team, finances, milestones_risks and funding_legal_ip; each has status supported/provisional/missing/not_applicable, explanatory text, and source bindings for supported claims. Missing sections remain visible. Publish with `case_workspace.py plan --workspace <project> --case <id> --input <strategy-plan.json> --decision-id <id> --reason <change>`. Existing startup prerequisites still apply. A complete document is not evidence of business viability or external-action approval.

The selected plan also checks current selected-case insights. A newly answered question or deep dive makes those insights pending and blocks current plan use until reconciled. A v2 plan uses the same `publication_claims` references within `section.<key>` text and renders reviewed links into the generated plan. Use `prepare-plan` and store a separate final review under `strategy/reviews/<case-id>/` before `publication_status: final`; changes to text or sources invalidate its bundle digest. A nine-heading document with generic filler remains a semantic-review failure even if the publisher accepts its structure.

## Current, history and recovery

One generated project overview points to each current case and the selected plan. The publisher owns metadata, snapshots and the single evolution timeline. Never edit manifests, generated timeline, selection generations or calculation results directly. Use `case_workspace.py correct ... --case <id> [--source <project-relative-path>]` for a material interpretation correction; a shared-source correction includes its declared consuming cases. Old handoffs cannot be reused after A→B→A.

If `history/pending.json` exists, current state is unavailable to dispatch/consumers. Run `case_workspace.py recover --workspace <project>` before resuming; it completes a committed publication or restores before-images, preserving outside edits by stopping on conflicts. Original runs remain immutable. These CLI/hook contracts are not a filesystem sandbox, and declared bindings cannot detect all semantic dependencies automatically.

Economics may include `scenarios` with `downside` and optional `upside` input overrides; each is recalculated from the base inputs, without invented probabilities. Leave unsupported values unknown. `provenance` entries marked evidence_backed need `source_refs` matching a declared binding path or `path#locator`. Conditional arithmetic never establishes purchase demand. Service costs begin when recurring customers are served even if billing is deferred. Owner cash compensation is separate from imputed opportunity cost; do not include the same labor in both service expense and owner compensation.

Stage publication in case mode requires the run's captured context (`run_dir`) or explicit `expected_assessment_revision`, checked under the project lock. After a correction, re-review the affected evidence; never copy old passes. Business-to-brand context must itself carry the selected `execution_binding`; use the current root structured plan and publish snapshots under root `branding/`. Consumers reject old or mismatched bindings even after switching back to the same case.

## Numerical prose and derived-input corrections

Source-attributed decision-relevant figures in current case appraisals use
`{{source_numeric.<id>}}` markers and the draft packet's optional `numeric_claims`
list. Inspect the original source first, then put its checked figure into a local
JSON observation. A claim names its `document` (`case_insights.md`, legacy `README.md`, `feasibility.md`,
`business-case.md`, or `comparison.<field>`), decimal-string `value`, canonical
snake-case `metric`, `period`, `currency` (three-letter uppercase or null),
`unit`, `scope`, and `status` (`verified` or `unverified`). A verified claim also
supplies one of the packet's checked `source_bindings`; that binding's `locator`
must be a JSON Pointer to the observation. The observation needs `value`,
`metric`, `period`, `currency`, `unit`, and `scope` with exactly matching context.
Use `python3 scripts/verify_numeric_claims.py --workspace <business-root> --packet <draft.json>`
for a read-only check before `case_workspace.py appraise`. The publisher repeats
the check under its lock and writes `numeric-claims.json` with the current case
documents. Missing, stale, contradictory or misplaced verified claims stop the
entire publication. Unverified claims need a reason and render as an explicit
unverified marker instead of a number. A cosmetic revision must explicitly
retain existing numeric claims; removing them is a material change.

The check compares declared fields against structured local source data. It
does not certify the extraction from a PDF or webpage, the meaning of surrounding
prose, or unmarked numbers. Keep semantic source review and source-use bindings;
never make a structured observation from a source without checking its locator.
Model-derived numbers still use `{{economics.…}}` and their separate digest check.

## Viability verdict

`economics_inputs.viability_targets` records the founder's test: `profitable_by_month` (default proposal 24–36 months, confirmed by the founder), `max_cash_need`, and `owner_income_per_month`. The helper returns `results.viability` with status pass/fail/unresolved and reasons. Quote it with `{{economics.results.viability.status}}` and `{{economics.results.viability.first_profitable_month}}`; never hand-write the verdict. Unresolved means the schedule or targets are missing, not that the business is unviable.

When prose makes model-derived claims, supply the author-reviewed `economics_input_digest` from the calculator and use placeholders such as `{{economics.results.contribution_per_unit}}`, `{{economics.results.required_sales}}`, `{{economics.inputs.capacity_per_month}}`, or `{{economics.results.cash.months.0.contribution}}`. Apply this to comparison summaries as well as case documents. Business-plan sections carry their own `economics_input_digest` for model claims. Literal model values, including multi-line values, stale digests and invalid references fail publication. Historical/source-attributed observations remain ordinary evidence prose; numerical checks do not prove unrestricted natural-language consistency. After a correction, reassess conclusions as well as refreshing the digest.

Direct research builders retain their actual local inputs in `.case-context.json` and stage source bindings. Use `--source-bindings <bindings.json>` to declare project-relative paths, digests, locators and applicability for shared inputs. Case-local input files are bound automatically to the same case use. Explicit upstream run bindings are retained recursively; cycles and changed inputs fail closure. This records declared dependencies, without inventing applicability or moving raw runs.

`owner_cash_per_month` is additional cash compensation, excluding amounts already included in service expense. Declare `owner_cash_in_service_cost`; true with additional owner cash is rejected as ambiguous double counting. `imputed_owner_labor_per_month` is unpaid opportunity cost, separate from cash payments; null stays unresolved. Monthly recurring `contribution` includes period service and new-customer acquisition costs independently of receipt/payment lags. `surplus_after_imputed_labor` is separately reported.

Supported `sensitivities` map at most three drivers (revenue_per_unit, service_per_unit, acquisition_per_new_customer, lead_to_customer, monthly_retention, capacity_per_month) to one to three explicit values each. Base/downside scenarios and decision-changing sensitivities remain visibly unresolved when unavailable; explain with `scenario_limit_reason` and `sensitivity_limit_reason`. No guessed ranges or probabilities are required to get provisional arithmetic. Unknown input keys fail rather than being silently digested.


## Commit decision review

A strategy plan with `verdict: commit` must include `decision_review` under
`schemas/strategy-plan.schema.json`. Selecting a provisional position does not
imply commitment. Record at least two causally distinct failure stories with
trigger category, trigger, transmission, failed defense, leading indicator and
probability basis (dated source or explicit unknown; never invent a base rate).
Link each stop rule to a defined KPI, numeric threshold, comparison operator,
measurement window, responsible owner and pre-committed action. Record a bias,
disconfirmation trigger, action and verification in each behavioral precommitment.
Use the existing `scripts/strategy_review.py validate` check before publication.
These are manual review rules; they create no monitoring job or spending authority.
Schema checks validate structure and links, not causal independence or truth.

## Economics charts

After calculating economics, optionally run
`python3 scripts/chart_case_economics.py --economics <economics.json> --out <fresh-directory>`.
Use `--csv-only` without matplotlib. For a versioned case, choose a fresh directory
under that case's `market_research/.../runs/`; the exporter binds the source digest.
Link the resulting charts from the business case through the normal publication
helper. CSVs preserve supplied monthly amounts and sensitivity points. Charts are
conditional arithmetic, not forecasts. Missing sensitivities remain an explicit gap.
