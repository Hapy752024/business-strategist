# Provisional case plans and selected execution plans

Use `case-business-plan` with startup-business-builder for a registered researched case. Initial reviewed case research, a bound eligible claim ledger and current reviewed `case_insights.md` are required. Case selection and a passed pain gate are not prerequisites for a conditional planning document. Business execution retains its existing gate.

## Case output contract

V2 appraisal automatically creates `cases/<id>/business-plan.md` and `business-plan.json` as an `appraisal_draft`; these are not current reviewed plans. Refresh insights, develop the full plan and publish through:

```bash
python3 scripts/case_workspace.py prepare-case-plan --workspace <business-root> --case <id> --input <packet.json> --out <fresh-review-directory>
python3 scripts/case_workspace.py case-plan --workspace <business-root> --case <id> --input <packet.json> --decision-id <id> --reason <change>
```

Use `schemas/case-business-plan.schema.json`. Supply case/revision metadata, the existing plan's `publication_base_digest` (or null), the current insight digest, economics input digest (or null), source bindings, numeric/publication claims and nine `business_plan_sections`. Numeric and publication marker targets are `section.<key>`. Source-derived numbers use `{{source_numeric.<id>}}`; calculated values use the existing economics placeholders and input digest. Supported sections require their original sources; missing/not-applicable sections explain the consequence and next action.

The nine keys cover:

- `business`: executive decision, customer problem, business thesis, founder objective/resources and pivotal uncertainty.
- `customer_market`: user/buyer/payer, segments/jobs/journey, pain/current spend, properly scoped bottom-up market and attainable initial market.
- `competitive_choice`: local competitors, substitutes/doing nothing, international commercial precedents, failed examples and entrant choice/switching conditions.
- `product_revenue`: offer/exclusions, delivery promise, MVP/manual starting scope, pricing and revenue mechanics; label proposals and tests.
- `acquisition_sales`: first-customer access, channels, funnel denominators, sales effort/cycle, repeat value; separate unpaid learning recruitment from selling.
- `delivery_team`: operating workflow, build/buy/partner, capacity, suppliers/data, quality/support, founder work, roles and hiring triggers.
- `finances`: startup/unit costs, owner cash and imputed labor, cash timing/runway, break-even, base/downside and sensitivity assumptions.
- `milestones_risks`: dated learning/delivery milestones, owners, costs, measurements, dependencies, stop/pivot criteria and unresolved assumptions.
- `funding_legal_ip`: funding need/use/timing, bootstrap/outside capital, relevant investor activity, legal/regulatory/data/IP dependencies and verification gaps.

The shared renderer produces financial tables from `economics.json`. A short generic paragraph under each heading does not establish content quality: review the exact rendered document and original evidence. Document publication (`progress`/`final`) and evidence basis (`desk_research`/`offer_tested`/`pilot_informed`) are independent. Signups, interviews, purchases and repeat use are distinct observations; explain what a test actually established.

For `final`, provide a current independent review under `cases/<id>/plan-reviews/`, with the existing review fields and the exact prepared bundle digest. Author and reviewer identities must differ. The publisher commits under the project lock and records history. The plan cannot cite itself.

## Freshness, legacy and selection

Plan use checks insight/source/economics/document digests and assessment revision. New findings or changed assumptions require updated insights/economics and republished affected sections. Research completion does not imply the plan is current. Keep existing `business-case.md` as the retained supporting appraisal/legacy projection; converting an existing case happens through reviewed appraisal and case-plan publication, preserving history and old links. Do not bulk-rename legacy files.

For a case with a canonical plan, selected `strategy/strategy-plan.json` must carry `case_plan_binding` to its current JSON `/business_plan_sections`, with applicability `Selected case business plan`; its sections must match that canonical authority. The root readable plan is derived from those sections plus approved execution context. Final execution-plan publication requires the case's final plan review. Selection/configuration/generation, strategy prerequisites and downstream checks remain mandatory. Legacy selected plans remain readable until explicitly converted.
