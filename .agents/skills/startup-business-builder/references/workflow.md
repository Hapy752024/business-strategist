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

When selecting or revising the business position, use repo-root `references/strategic-positioning.md`; reuse the active `strategy-plan.json` when one exists. GTM owns business-position selection if a focused specialist step is needed. Do not create a competing positioning process or force a full GTM deliverable into a narrow startup question.

Be skeptical and founder-useful. Do not validate the idea by default. Most startup plans are too broad, too solution-led, and too optimistic about demand. Push the user toward real customer pain, observable behavior, and fast learning.

Separate:

- Evidence: customer behavior, interviews, payments, usage, retention, competitor/workaround evidence.
- Assumptions: pain, buyer, urgency, willingness to pay, channel, business model.
- Plan: concrete actions, tests, owners, cadence, and thresholds.
- Risks: product-market fit, timing, unit economics, channel, founder/team, legal/compliance, execution.

## Ambiguity and Unknowns

If missing context would materially change the plan, ask one focused question before creating the full plan. Highest-leverage unknowns are customer segment, problem, geography, business model, founder strengths, and whether the company is software, marketplace, service, ecommerce, local, hardware, regulated, or deep tech.

If the user wants a fast draft, state assumptions clearly and create a testable plan.

Use `market-problem-discovery` when the user wants to explore a market or discover which customer problems and segments to pursue. Use `idea-grill` when the user has chosen a candidate idea but needs to make it researchable. Use `evidence-scout` for demand validation. Use `competitor-scout` for alternatives and substitutes. Use `saas-fintech-pilot-designer` when the user needs detailed SaaS, fintech, or insurtech MVP, POC, paid pilot, sandbox trial, or regulated test design. Use `archetype-gtm-strategist` for stage-gated first-customer, launch, partnership, and regional GTM design. Use `company-operating-system` to derive delivery choices from the selected promise or set requested management cadence. Use `marketing-strategy-builder` or `social-digital-marketing-planner` for detailed campaign and channel execution.

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
5. Specific promise, delivery fit and competitive durability.

   Reuse repo-root `references/strategic-positioning.md`: connect reviewed need to a testable promise, feasible activities and separately assessed benefit/barrier/value capture. Preserve inherited evidence status. Assess an incumbent and a new entrant, formation costs and erosion. No moat is an exposure to judge against founder goals, not automatic MVP rejection. Do not impose business-type stereotypes or require invisible barriers to rank among customers' stated priorities. Reuse the selected decision rather than creating a second moat checklist.
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
- Competitive response, durability limits and formation costs are acceptable for the intended scale and investment horizon; a temporary advantage is not labelled a proven moat.

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
- Unsupported defensibility: recurring revenue, product quality or growth is presented as protection without benefit/barrier evidence. Report the exposure relative to founder goals and the next decision.

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
- Claimed economic benefits and imitation barriers are separately supported or labelled hypotheses; value capture and incumbent/new-entrant responses are assessed.
- No identified moat remains an explicit exposure, not an automatic rejection or invented claim.

## Suggested First Question

If needed, ask:

`Who is the first specific customer segment you want to serve, and what painful problem do they already try to solve today?`
