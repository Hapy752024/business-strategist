# Strategic positioning

Load only when selecting/revising a business position, deriving its operating model, or checking a material contradiction. For routine copy, campaign, design, or cadence work, use the supplied position without reopening this exercise.

## Select a feasible position

For venture discovery or validation, first express the customer/need hypothesis: `[segment] in [situation/trigger] needs [outcome], currently uses [alternative], and experiences [evidenced consequence or unresolved shortfall]`. Do this even for a feature-first pitch; keep the proposed product as a separate hypothesis. Reuse known inputs, mark inferences, and ask only decision-changing gaps. Narrow execution for an already selected business does not restart discovery.

Before a material opportunity ranking, reuse any supplied founder decision context. Capture only missing items that could change the decision: objective/ambition, desired role and exclusions, capabilities/access, affordable downside, time or income horizon, and acquisition/operating constraints. Mark each as a founder hard constraint, preference, assumption or unresolved input. Do not ask this intake for a narrow factual lookup or fixed-scope execution task.

Give viable alternatives a comparable initial evidence pass before selecting one for deeper research. Show coverage differences; more research on one option does not make it better. A demonstrated hard incompatibility can justify early elimination. Rank the important assumptions with weakest support, and explicitly distinguish `insufficient_evidence`, `investigate`, `test` and `commit`. No forced winner or universal source-count threshold.

1. Identify the buying situation: trigger, user/buyer/payer, current alternative (including doing nothing), minimum requirements, deciding preferences, and acceptable sacrifices. Cite customer evidence; mark inferred priorities and missing evidence. Frequency in public posts is not willingness to pay.
2. If unresolved, compare a few materially different positions using customer need/current behaviour, actual alternatives, feasible entry and customer choice, acquisition and relationship formation, founder capabilities/access, delivery cost/capacity, cash/contribution and exclusions. Apply only relevant lenses. Explain why an option loses; do not manufacture precise scores or extra options for an already-supported choice. Existing suppliers prove supply, not saturation; no visible supplier proves neither demand nor an opportunity.
3. Recommend the best-supported hypothesis under current constraints, or the cheapest test that distinguishes the options. State whom to serve, the promised outcome, why the alternative is less suitable, and customers/services deliberately excluded. Founder selection does not validate demand.
4. Challenge inconsistent promises with a concrete constraint or calculation. Do not dismiss every ambitious combination as impossible: a distinctive activity or credible new evidence may resolve the tension. Change your recommendation only when affected evidence, assumptions or founder constraints change; say why the ranking changes or does not.

## Assess whether an entrant can succeed

Use 12–24 months as the default entrant-assessment horizon, overridden by the founder's explicit deadline. Check early cash needs as well as the eventual steady state. A plausible two-year business may still be incompatible with a six-month income requirement.

Define success at the founder's intended scale and time horizon before judging competition. Separate **served** (credible offers exist), **well served** (observed customer outcomes are satisfactory for a defined job), **saturated** (evidence suggests insufficient profitable access for this entrant), and **entrant feasibility** (this venture can acquire, serve and retain enough customers within its resources). Avoid “fully served” as a market-wide verdict; specify the segment, job, outcome, date and evidence. Supplier lists, feature overlap, funding, followers or brand size alone establish neither saturation nor easy entry.

Assess customer need, visibility, trust/customer choice, delivery and economics independently. A new entrant can succeed with familiar products and a cumulative service advantage; a novel feature or proprietary moat is not mandatory for a small profitable business. Conversely, a small incumbent does not prove customers are easy to reach. Estimate required customers from contribution after variable acquisition/service costs and fixed costs, with assumptions and sensitivity. Match the result to achievable funnel throughput and founder capacity; leave unavailable inputs unresolved.

For content acquisition, specify the audience's existing destinations, search/question intent, platform, credible presenter, content angle, discovery mechanism, repeat-contact mechanism, call to action, conversion path, production effort, cash/time cap and attribution. Publishing pages is not a distribution plan. Distinguish exposure, relationship signals and commercial conversion; explain recruitment for interviews too. Respect the founder's permitted channels.

Before changing a recommendation, record the previous view, changed fact/constraint or corrected reasoning, affected comparison and remaining uncertainty. A user's objection triggers examination; it does not automatically justify reversing the ranking. Different evidence coverage or unresolved inputs may require `investigate` or `park`, rather than forced scores or `stop`.

## Derive delivery and consequences

For the commercial model, show the applicable customer requirement: fixed operating cost plus target owner compensation divided by contribution per active customer per period, or by net contribution per completed sale for transactional businesses. Define the period and gross/net treatment. Include acquisition and service labor, churn/cancellations, partner shares and cash-collection timing without double counting. Model ramp, retained cohorts and downside with ranges; do not invent conversion rates or treat recurring and upfront revenues as interchangeable.

Map only activities that change a decision. Explain which capabilities, people, technology, partners, service boundaries, capacity, and costs the promise requires. For each consequential choice, state what it enables and constrains, the next decisions it creates, interactions with other activities, and expensive-to-reverse commitments. Deliberate sacrifices can reinforce the position; operational excellence alone does not establish differentiation.

Use this table within the existing positioning section, not a separate business deliverable:

| Customer priority and evidence | Promise and exclusion | Operating choice | Consequences and trade-offs | Service, brand and marketing implications | Test/KPI reference |
|---|---|---|---|---|---|

If delivery is infeasible or customers do not value the promise, revisit the position. Do not force the operating model to rationalize the founder's preferred answer. `archetype-gtm-strategist` owns business-position selection; `company-operating-system` develops delivery and management implications. Neither requires a full GTM/company blueprint for a narrow request.

## Keep execution aligned

Use the selected position for service scope, price, proof, messages, channels, and brand expression. Creative territories may vary expression; they cannot silently change the buyer or business promise. Flag a material conflict, explain the consequence, and propose either a consistent execution change or an explicit strategy revision. Preserve standalone branding and user-requested scope.

Reuse existing experiments and KPIs: a customer-outcome measure plus relevant delivery/economic guardrails, with owner, formula, cohort/window, target, review cadence, and stop/change rule. Explain threshold assumptions. No KPI per activity by default. At review, identify disconfirming evidence and the affected downstream outputs; retain frozen experiment baselines and archived snapshots.

## Saved decision and handoff

For an execution-ready plan, reuse the active workspace's `strategy-plan.json`; marketing and operations update that selected record rather than creating competing copies. Its optional `positioning` object contains:

- `decision_status`: `proposed`, `selected`, or `revisit`; `statement`; `exclusions`; optionally `alternatives` with rejection reasons.
- `provenance`: `evidence_backed`, `user_confirmed`, `inference`, `assumption`, or `unresolved`; `evidence_refs` contains source/claim locators. Selection and evidential support are separate.
- `activities`: consequential rows with `customer_priority`, `promise`, `choice`, `consequences`, `implications`, `provenance`, and `evidence_refs`. Preserve mixed evidence labels per row; use optional `experiment_ids`/`kpi_names` to link specific rows.
- `experiment_ids` and `kpi_names`: references to existing experiment IDs and KPI names testing the position; do not duplicate their definitions.

Validate with `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>`. The validator checks structure/references, not strategic truth. Markdown presents the same saved decision. A short advisory answer need not create an execution plan; legacy plans can omit positioning.

Only for explicitly business-linked branding, build an immutable snapshot with:

```bash
python3 scripts/brand/build_business_to_brand_handoff.py <business-context.json> <new-snapshot.json> --strategy-plan <strategy-plan.json>
python3 scripts/brand/validate_business_to_brand_handoff.py <new-snapshot.json> --check-sources
```

Run the source check before downstream generation/review. If a source changed or cannot be checked, report the affected work and refresh through the existing handoff workflow; do not overwrite the old snapshot. Missing provenance remains unresolved. Explicitly provisional work may proceed with its limitations, but cannot be called validated positioning.

Sources (accessed 6 September 2026; undated): [HBS distinctive value chain](https://www.isc.hbs.edu/strategy/creating-a-successful-strategy/Pages/distinctive-value-chain.aspx) connects customer value to differentiated activities; [HBS activity fit](https://www.isc.hbs.edu/strategy/creating-a-successful-strategy/Pages/fit-across-the-value-chain.aspx) explains reinforcement among activities. The workflow and record conventions here are project design decisions.
