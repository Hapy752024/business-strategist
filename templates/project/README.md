# {{TOPIC}} — current decision

**Status:** intake / no recommendation yet
**Last updated:** {{CREATED_AT}}
**Machine state:** [`market_research/manifest.json`](market_research/manifest.json)

This is the current reader-facing decision document. It must remain understandable on its own. Keep supporting narratives in [`market_research/deep_dives/`](market_research/deep_dives/); keep raw runs and machine state in their existing folders. Treat canvases as versioned hypotheses: customer-side claims require evidence IDs; value-side entries remain design choices until tested.

## Foundation: segment, journey, pain points (pain-first rule)

Before any solution, strategy, brand, or website work, this venture needs its three foundations pinned with web-searched evidence:

1. **Customer segment** — who exactly: [`market_research/customer_segments/`](market_research/customer_segments/)
2. **Customer journey** — how they move through the topic today: [`market_research/customer_journey/`](market_research/customer_journey/)
3. **Pain points** — detected/validated from public evidence: [`market_research/pain_points/`](market_research/pain_points/) (collection runs under `pain_points/runs/`)

Even when the founder arrives with a solution, these come first. Downstream commitment stages (business model, offer, GTM, brand, website) stay gated until `problem_validation` passes in the manifest — or the founder records an explicit override.

- Initial customer segment: {{CUSTOMER_SEGMENT}}
- Segment status: [UNRESOLVED]
- Journey coverage: [UNRESOLVED]
- Strongest evidence-backed pain: [UNRESOLVED]

## Decision context

- Founder objective / ambition: [UNRESOLVED]
- Desired role and work to avoid: [UNRESOLVED]
- Means: capabilities, access, time and cash: [UNRESOLVED]
- Affordable downside and income/time horizon: [UNRESOLVED]
- Acquisition and operating constraints: [UNRESOLVED]

Label each item as a founder hard constraint, founder preference, assumption, or unresolved input. Do not research a founder preference as though it were a market fact.

## Options and current assessment

Customer/need hypothesis: [segment] facing [trigger] needs [outcome], currently uses [alternative], with [observed consequence or unresolved shortfall]. Keep the founder's solution separate. Summarize the sourced journey and its material branches, including counter-evidence and source gaps.

| Option | Customer need and current behaviour | Entry, acquisition and relationship feasibility | Delivery and economics | Evidence strength | Current decision |
|---|---|---|---|---|---|
| [UNRESOLVED] |  |  |  |  | investigate |

Compare only viable options. Existing suppliers are not proof of saturation; no visible suppliers are not proof of demand.

Assess competitor visibility, sales, service and retention against that journey, preserving strengths and unknowns. A quiet social account does not establish poor acquisition or retention. Social is one possible discovery and relationship mechanism.

## Current recommendation

**Decision:** insufficient evidence.

State the best-supported next decision, not a forced winner. Explain why the alternatives do or do not lose under the stated constraints. Distinguish evidence, inference, hypothesis, and founder preference.

## Acquisition and relationship feasibility

For the leading option, state how a suitable customer first discovers an unknown entrant; why they would return, engage or trust it before a buying event; and how that becomes an enquiry, purchase and subsequent service. Separate discovery, relationship and commercial evidence. Attention alone is not willingness to pay.

State the specific audience destination, initial exposure mechanism, content angle, presenter, repeat-contact path, CTA, recruitment method, production effort and attribution. Compare required customers/sales and service capacity with funnel and contribution scenarios over 12–24 months (or the founder's deadline), including earlier income/cash constraints. Mark every unverified input. Summarize comparable foreign entrants' early customer acquisition, starting advantages and verified outcomes; explain transfer limits.

## Decisive unknowns and next bounded action

1. [UNRESOLVED] — cheapest test, threshold, stop/pivot condition, owner and deadline.

## Supporting material

Recommendation change: previous view → changed evidence/constraint or corrected reasoning → effect on ranking → remaining uncertainty. Completion: distinguish delivered scope, audited claims, missing research and validation actually run; generated reports or passing code tests do not establish research completion.

- Founder and customer hypothesis: [`strategy/intake/startup-thesis.md`](strategy/intake/startup-thesis.md)
- Deep dives: [`market_research/deep_dives/`](market_research/deep_dives/)
- Evidence runs: [`market_research/pain_points/runs/`](market_research/pain_points/runs/)
- Solution alternatives (competitors/workarounds): [`market_research/solution_alternatives/`](market_research/solution_alternatives/)
- Decisions and dated reversals: [`strategy/decisions/`](strategy/decisions/)

## Working rules

- Store provider runs under the relevant `runs/` directory.
- Separate evidence, hypotheses, judgments, and decisions.
- Update the manifest at each stage gate.
- Do not infer willingness to pay from attention or engagement alone.
