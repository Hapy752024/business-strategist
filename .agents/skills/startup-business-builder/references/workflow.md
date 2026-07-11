---
name: startup-business-builder
description: Help founders start a new startup from the business side: idea selection, customer discovery, painful problem validation, MVP scope, first customers, business model, pricing, positioning, go-to-market, operating cadence, traction metrics, and failure-risk checks. Use this skill whenever the user asks how to start a startup, evaluate a startup idea, build a startup plan, create a zero-to-one roadmap, find first customers, define MVP/business model/go-to-market, avoid startup failure, or learn from successful and failed startup examples. Focus on business execution and validation, not fundraising mechanics.
---

# Startup Business Builder Workflow

Use this skill when the user wants to start, evaluate, or structure a new startup from the business side. Financing can be mentioned as a constraint, but do not turn the answer into fundraising advice unless the user explicitly asks.

## Reference

Before creating a substantial startup plan, read:

- `references/startup-business-research.md`

If the user asks for latest failure data, market data, industry-specific rules, competitor facts, or current examples, search the web and cite sources before making factual claims.

## Stance

Be skeptical and founder-useful. Do not validate the idea by default. Most startup plans are too broad, too solution-led, and too optimistic about demand. Push the user toward real customer pain, observable behavior, and fast learning.

Separate:

- Evidence: customer behavior, interviews, payments, usage, retention, competitor/workaround evidence.
- Assumptions: pain, buyer, urgency, willingness to pay, channel, business model.
- Plan: concrete actions, tests, owners, cadence, and thresholds.
- Risks: product-market fit, timing, unit economics, channel, founder/team, legal/compliance, execution.

## Ambiguity and Unknowns

If missing context would materially change the plan, ask one focused question before creating the full plan. Highest-leverage unknowns are customer segment, problem, geography, business model, founder strengths, and whether the company is software, marketplace, service, ecommerce, local, hardware, regulated, or deep tech.

If the user wants a fast draft, state assumptions clearly and create a testable plan.

Use `idea-grill` when the idea is vague. Use `evidence-scout` for demand validation. Use `competitor-scout` for alternatives and substitutes. Use `saas-fintech-pilot-designer` when the user needs detailed SaaS, fintech, or insurtech MVP, POC, paid pilot, sandbox trial, or regulated test design. Use `archetype-gtm-strategist` for stage-gated first-customer, launch, partnership, and regional GTM design. Use `company-operating-system` after the startup has enough clarity to set operating cadence. Use `marketing-strategy-builder` or `social-digital-marketing-planner` for detailed campaign and channel execution.

Before substantial research or a full startup plan, make source availability explicit with:

```bash
python3 scripts/capability_lookup.py --question "<research need>" --compact
```

For evidence-backed work, run `python3 scripts/validate_apis/run_all.py` before treating a provider as available. If capability lookup or validation shows missing credentials, rate limits, missing local CLIs, billing issues, or permission failures, state the coverage gap and confidence impact before strategy synthesis. Do not replace missing evidence with a plausible narrative.

## Minimum Inputs

Try to capture:

- One-sentence idea.
- Target customer and buyer.
- Pain/problem and trigger event.
- Current workaround or alternatives.
- Why the problem is urgent now.
- What the user thinks people will pay for.
- Geography/language.
- Business model hypothesis.
- Founder unfair advantage or access to customers.
- Current stage: idea, interviews, prototype, MVP, pilots, revenue, or pivot.

## Procedure

1. Restate the startup thesis in one sentence.
2. Identify the narrow early-adopter segment.
3. Translate solution language into the underlying customer problem.
4. Define the riskiest assumptions.
5. Design customer discovery before product building when pain is unproven.
6. Scope a wedge MVP or concierge/manual test with a 90/10 solution.
7. Define first-customer acquisition paths.
8. Draft the business model, pricing hypothesis, and unit-economics questions.
9. Define traction metrics and validation thresholds.
10. Identify failure modes and anti-patterns before scaling.
11. Produce a 7-day action plan and 30/60/90-day roadmap.

## Business-First Startup Sequence

Use this sequence unless the user requests a narrower slice:

1. Problem and customer.
2. Urgency and workaround.
3. Buyer and willingness to pay.
4. Existing alternatives and substitutes.
5. Competitive durability and moat.

   Before building an MVP, assess whether the business can defend its position after winning early customers. A startup that validates demand but has no moat is a feature waiting to be copied by incumbents.

   For each relevant moat source, assess:
   - Switching costs: how hard is it for a customer to leave for a competitor?
   - Network effects: does each additional user make the product more valuable for all users?
   - Brand/status: does the product signal something about the customer? (Only relevant for visible B2C products.)
   - Share of mind / habit: will customers default to this product out of habit?
   - Trust: is the cost of being wrong high enough that customers stick with the known provider?
   - Cost advantage: can the business structurally produce at lower cost than competitors?
   - Efficient scale: is the market too small for another profitable entrant?
   - Regulatory / contractual barriers: are there licenses, permits, or long-dated contracts?
   - Data / learning advantage: does proprietary data improve with scale?
   - Distribution / entrenchment: does the business control a channel that competitors cannot access?
   - Physical asset: does the business own an irreplaceable location or asset?
   - Product superiority: is the product technically superior in a way that creates a structural bottleneck?

   Calibrate each moat source by business model type. Switching costs are narrow for B2C but very strong for B2B enterprise. Network effects are very strong for B2C and B2B marketplaces. Brand matters only for visible consumer products. Cost advantage is weaker for visible products where social signaling dominates.

   For each moat source that the business claims, apply the Capability vs. Incentive test:
   - Capability: What physically or contractually stops a well-funded competitor from copying this?
   - Incentive: Even if they could copy it, why would a rational competitor choose not to? (e.g., copying would cannibalize their own cash cow at a worse margin.)

   If neither track has a substantive answer, the moat claim is weak. If the business has no moat source that scores above "weak" on both evidence and durability, treat competitive durability as the riskiest assumption and prioritize moat-building actions before scaling.

   Map moat sources to the customer's actual decision hierarchy. A moat that does not appear in the customer's top 3 purchase priorities is decorative — it exists on paper but does not actually protect the business. For B2C, use the Consumer Hierarchy of Preferences (price, quality, convenience, status, habit, trust, variety, experience). For B2B, use the elimination sequence (Function → Reliability → Convenience → Price). For SMEs, prioritize trust/relationships and price.
6. Wedge market and beachhead.
7. MVP or concierge test.
8. First 10 customers.
9. Business model and pricing.
10. Retention and success metrics.
11. Go-to-market learning loop.
12. Operating cadence.
13. Scale gates.

## Customer Discovery

Push for past behavior, not opinions. Avoid asking "would you use this?" or "would you pay?" Prefer:

- When did this problem last happen?
- What triggered it?
- What did you do?
- What did it cost in money, time, risk, or stress?
- What tools, services, spreadsheets, people, or hacks did you use?
- What did you try that failed?
- Who approved or paid for the workaround?
- What would make this urgent enough to change?

For B2B, separate user, buyer, champion, economic buyer, blocker, and procurement/compliance requirements.

## MVP And Validation

Design the smallest useful test that creates customer learning:

- Concierge/manual workflow.
- Spreadsheet-backed service.
- Landing page and interview funnel.
- Paid pilot.
- Prototype demo.
- Fake-door test with ethical disclosure where needed.
- Founder-led sales.
- Manual onboarding.

For SaaS, fintech, and insurtech, use `saas-fintech-pilot-designer` to choose between smoke test, prototype, concierge MVP, technical POC, paid pilot, regulatory sandbox trial, or beta, and to define data, security, compliance, success metrics, and conversion gates.

Avoid building a full product, automated backend, marketplace infrastructure, large app, or polished brand system before the main risk is reduced.

## First Customers

Recommend specific first-customer paths:

- Founder network only when it matches the target segment.
- Communities where the pain is already discussed.
- Direct outbound to people with trigger events.
- Manual partnerships with trusted intermediaries.
- Local outreach for physical/service businesses.
- Content/search only when search intent already exists.
- Competitor-review and forum mining to find dissatisfied users.

The first 10 customers should teach. They do not need to represent a scalable channel yet.

## Business Model

Define:

- Who pays.
- What they pay for.
- Pricing metric.
- Expected frequency.
- Gross margin or cost-to-serve drivers.
- Sales motion.
- Support/onboarding load.
- Retention mechanism.
- Expansion or repeat-purchase path.

If the model has negative or unclear unit economics, say so before recommending growth.

## Scale Gates

Do not recommend scaling until enough of these are true:

- Repeated pain from a narrow segment.
- Clear current workaround.
- Users try the MVP without excessive persuasion.
- Some users pay or commit meaningful time/risk.
- Retention or repeat usage exists.
- The team can explain who loves it and why.
- Acquisition has at least one repeatable path.
- Cost to serve is plausible.
- Founder team can keep operating without self-destruction.
- At least one structural moat source is identified that (a) maps to a top-3 customer priority and (b) passes the Capability vs. Incentive test on at least one track. If the business depends entirely on temporary advantages (speed, novelty, under-pricing), scaling is premature.

## Failure Checks

Call out these anti-patterns:

- Broad segment such as "SMBs", "creators", "students", or "everyone".
- Product idea with no urgent problem.
- Building before enough customer conversations.
- Confusing waitlists, compliments, press, or funding with demand.
- Hiring specialists before repeatability.
- Paid acquisition before retention or conversion is understood.
- Marketplace without a credible supply/demand wedge.
- Enterprise pilots that never convert to paid repeatable deals.
- Negative unit economics hidden by growth.
- Founder conflict or unclear decision rights.
- Trend-chasing without durable user behavior.
- Overbuilding the easy part while ignoring the hard "monkey".
- No structural moat. The business depends on being first, being cheaper, or having a better product — all of which competitors can copy. Without at least one structural moat source (switching costs, network effects, trust, efficient scale, regulatory barrier, distribution lock-in, or counter-positioning), the business will face margin compression as competitors enter.

## Good And Bad Examples

When using examples, turn them into lessons:

- Airbnb: do unscalable work to find the bottleneck and learn from customers.
- Twitch/Justin.tv: narrow to the segment where pull, retention, and monetization become repeatable.
- Dropbox: make value easy to understand and sharing natural.
- Quibi: money and credentials do not replace customer pull or a hair-on-fire use case.
- Webvan: infrastructure and geography expansion before unit economics can kill.
- Juicero: engineering complexity is not customer value.

Do not imply that copying a famous startup's tactic will work without the same customer context.

## Output

For a full startup-building request, produce:

- Startup thesis.
- Key assumptions and unknowns.
- Early-adopter segment.
- Problem and trigger event.
- Current workaround and alternatives.
- Customer discovery plan.
- MVP or concierge-test plan.
- First 10 customers plan.
- Business model and pricing hypothesis.
- Traction metrics and thresholds.
- 30/60/90-day roadmap.
- Failure-risk checklist.
- Scale gates.
- Next 7-day action plan.

For idea evaluation, produce:

- Verdict: promising, unclear, narrow, pivot, or stop.
- Evidence strength.
- Riskiest assumptions.
- Cheapest tests.
- Decision gate.

## Quality Checklist

Before finalizing, check:

- The target customer is specific enough to find this week.
- The problem is stated without solution jargon.
- The plan tests pain before building scale.
- MVP scope is a 90/10 solution, not a full product.
- First-customer tactics are concrete and manual enough.
- Metrics include retention, payment/commitment, and learning, not only signups.
- Business model questions include cost to serve and pricing.
- Failure checks are explicit.
- The 7-day plan can actually be executed.
- Competitive durability is assessed before recommending scaling.
- At least one moat source is identified and calibrated by business model type (B2C/B2B).
- The Capability vs. Incentive test is applied to the primary moat claim.
- Moat sources are mapped to the customer's actual decision priorities.
- If no structural moat exists, this is explicitly called out before scaling.

## Suggested First Question

If needed, ask:

`Who is the first specific customer segment you want to serve, and what painful problem do they already try to solve today?`
