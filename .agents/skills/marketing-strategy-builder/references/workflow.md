---
name: marketing-strategy-builder
description: Build world-class marketing strategy from customer evidence: segmentation, positioning, messaging, offer design, funnel, channel strategy, launch plan, campaign calendar, proof assets, pricing signals, metrics, and testing roadmap. Use this skill whenever the user asks for marketing strategy, go-to-market, positioning, brand messaging, demand generation, growth campaigns, launch planning, funnels, acquisition channels, content strategy, paid ads strategy, or how to market a company or product.
---

# Marketing Strategy Builder Workflow

Use this skill when the user wants a marketing strategy, go-to-market plan, positioning, campaign plan, or growth plan.

## Stance

Marketing is not decoration. Treat it as the link between customer pain, offer design, distribution, proof, and revenue. Do not produce generic channel lists. Do not copy competitor claims without checking whether real customers care.

For social/content and digital-acquisition bets, ground recommendations in the practitioner evidence base at `.agents/skills/social-media-idea-validator/references/founder-playbooks.md` (Pain-Point SEO intent tiers, considered-purchase content economics, niche-first entry, broker/loan-officer channel reality), and validate untested channel ideas with `social-media-idea-validator` before committing them to the plan.

Separate:

- Evidence: customer words, behavior, search demand, sales calls, reviews, competitor pages, campaign data.
- Interpretation: what the evidence may mean.
- Hypotheses: what needs testing.
- Plan: what to do next with time, budget, and metrics.

## Weak-Evidence Check

Before treating any traction claim as a foundation for strategy, classify it against the weak-evidence list in the cross-skill registry (`references/evidence-registry.md` at repo root): downloads, signups, waitlists, views, likes, followers, subscribers, press spikes, and partnership announcements are weak until connected to retained customers or contribution economics.

When the brief leads with such claims, name them as weak evidence explicitly and re-anchor the strategy on proof: retention, repeat purchase, paid pilots, referral, and contribution margin. Positioning, funnel, and channel choices should target the next piece of real proof, not amplify the vanity signal.

## Ambiguity and Unknowns

If the customer segment, product, buyer, price, geography, or business model is unclear enough to change the strategy, ask one focused question before building the plan.

If the user wants a fast draft, state assumptions and create a testable strategy, not a definitive one.

If the user has not chosen a customer problem or segment and wants to discover opportunities, route first to `market-problem-discovery`. For unsupported demand claims about a chosen candidate, route to `idea-grill` and `evidence-scout`. For competitor positioning, route to `competitor-scout` and `competitor-marketing-analyzer`.

When business archetype, MVP/launch stage, first-customer motion, partnerships, or Europe/US/China expansion materially changes the strategy, route first to `archetype-gtm-strategist`; use this skill afterward for detailed positioning, funnel, channel, and campaign execution.

When a consumer service needs customer-role objections, trust/redress review, package boundaries, pricing presentation, reviews, privacy, cancellation, or Europe/Germany/US adaptation, route first to `service-customer-perspective-challenger`. Its simulated customer voice is a hypothesis input, not customer evidence.

## Minimum Inputs

Try to capture:

- Product or service.
- Target customer segment and buyer.
- Pain/job and trigger event.
- Current alternatives or competitors.
- Price point or monetization model.
- Geography and language.
- Current traction and channel data.
- Budget and time horizon.
- Marketing goal: awareness, leads, pipeline, sales, activation, retention, expansion, or repositioning.

## Strategy Sequence

Build strategy in this order:

1. Customer segment.
2. Pain and job-to-be-done.
3. Buyer and decision process.
4. Positioning.
5. Offer.
6. Proof.
7. Funnel.
8. Channels.
9. Campaigns.
10. Measurement and learning loop.

Do not start with channels unless the user explicitly asks for channel execution. Even then, state the positioning and offer assumptions the channel plan depends on.

## Procedure

1. Clarify the customer, buyer, product, business model, geography, budget, time horizon, and marketing goal.
2. State assumptions and evidence gaps before recommending channels or campaigns.
3. Narrow the early adopter segment and buyer trigger.
4. Build positioning from pain, promise, differentiation, and proof.
5. Design the offer and risk reversal.
6. Map the funnel and identify the conversion action.
7. Choose channels based on customer behavior and available proof.
8. Define campaign tests with budgets, thresholds, and stop conditions.
9. End with a seven-day action plan.

## Segmentation

Avoid broad segments such as "SMBs", "creators", "students", "families", or "everyone" unless narrowed by:

- Trigger event.
- Industry or use case.
- Budget or willingness to pay.
- Existing workaround.
- Urgency.
- Reachable community or channel.
- Buyer role.

Name the early adopter segment before the mass-market ambition.

## Positioning

Define:

- Category: what market the customer thinks this belongs to.
- Target: who it is for.
- Problem: what painful job or failure it fixes.
- Promise: the outcome.
- Differentiation: why this approach is meaningfully different.
- Proof: what makes the promise believable.
- Enemy: what outdated, painful, risky, or wasteful behavior the company stands against.

Use customer language when available. Do not overuse vague claims such as "simple", "AI-powered", "seamless", "all-in-one", "smarter", or "revolutionary" unless they are translated into concrete outcomes.

## Offer Design

Specify:

- Primary offer: demo, trial, audit, pilot, consult, sample, waitlist, purchase, subscription, or paid implementation.
- Risk reversal: guarantee, cancellation, proof before payment, fixed-scope pilot, or transparent scope.
- Activation moment: what the user must experience to believe.
- Pricing posture: transparent, starting price, custom quote, freemium, usage-based, tiered, paid pilot, or enterprise.
- Objection handling.

Offer design should reduce perceived risk without attracting the wrong customers.

## Funnel

Map:

- Awareness: how the customer first realizes or names the problem.
- Consideration: what they compare and what proof they need.
- Conversion: what action they take.
- Activation: how they experience value.
- Retention/expansion: why they return, renew, or refer.

For B2B, include buyer committee, champion, economic buyer, procurement, security, and implementation risk where relevant.

## Channel Strategy

Choose channels based on customer behavior, not founder preference. Before naming a platform, assign it one job: discovery, education/trust, demand capture, conversion, activation, lifecycle, referral, community, or recruiting. Consider:

- Search: existing intent, comparison queries, pain queries.
- Content/SEO: education-heavy markets with durable questions.
- Community: niche segments with active public discussion.
- Founder-led sales: high-ticket, ambiguous, early-stage, or relationship-heavy markets.
- Partnerships: trusted intermediaries or embedded workflows.
- Paid search/social: clear segment, offer, and conversion path.
- Outbound: identifiable buyer with acute trigger events.
- Events/webinars: complex categories requiring trust.
- Marketplaces/app stores: when buyer already searches there.

For each channel, answer the eight questions of the channel/loop recommendation protocol in `references/evidence-registry.md` (stage, customer context, channel job, mechanism, prerequisites, cohort gate, transfer limit, stop rule). Include the customer context and job; the asset, credibility, cadence, and operating capacity required; the conversion bridge; the first test and cost cap; the source-cohort metric; and the success/stop rule. Add a transfer warning when a founder example depends on unusual network, reputation, audience, product-workflow, timing, or regulatory advantages. A channel recommendation that cannot name its cohort gate and stop rule is a hypothesis — cap the budget and name the evidence that unlocks more.

Name one primary acquisition motion and one supporting/owned motion. Explicitly defer channels that lack audience fit, assets, capacity, retained-value evidence, or viable economics. Use the channel-job guidance in `references/evidence-registry.md`; retrieve current official platform details before prescribing formats, targeting, algorithms, costs, or regulated-advertising execution.

## Referral, Product, and Community Loops

Do not describe a share button, waitlist, follower audience, or branded group as a growth loop. Diagnose recipient exposure, collaboration, reciprocal reward, scarcity/invite, network utility, or repeated member-to-member exchange.

Recommend a loop only when value precedes the invitation, the recipient has a real job, every step is measurable, and retained contribution after rewards, fraud, support, refunds/claims, and complaints is plausible. For regulated services, include promotion/incentive, suitability, privacy, and abuse review.

For community, require a narrow member identity, recurring useful exchange, founder/operator stewardship, newcomer onboarding, roles/recognition, moderation, and a customer-outcome link. Track member-to-member help, return contribution, activity not initiated by staff, product/customer outcomes, and moderation load—not just member count or posts.

## Low-Cost Growth Guardrail

Interpret “growth hacks” as low-cash, high-learning, compounding distribution: founder recruitment/onboarding, useful participation in concentrated communities, customer-language content, high-intent SEO, native repurposing, post-activation invitations, product-currency rewards, recipient exposure, and manual partner handoffs. Reject spam, fake scarcity, manufactured controversy, mass unsolicited automation, dark patterns, and regulatory arbitrage.

## Customer-Perspective Challenge Pass

Before finalizing positioning, offer, messaging, or funnel for a consumer service, run the draft against the Service-Customer Decision and Trust checks in `references/evidence-registry.md`:

- Does the offer lead with uncertainty reducers (precise scope, process visibility, credentials, total price, human access, redress) when the service is consequential, unfamiliar, data-sensitive, or hard-to-reverse?
- Is the segment defined by trigger, job, and risk context rather than a nationality-based persona?
- Does the proof plan rely on review conditions that actually build trust (recent, specific, independently verifiable, provider responds to failure) rather than star averages or incentivized reviews?
- Is the commitment staged (diagnostic, fixed-scope pilot) when outcome variance and expertise asymmetry are high, instead of one large irreversible purchase?
- Are cancellation, refund, data-use, and complaint pathways clear in the funnel and messaging?

Escalate to `service-customer-perspective-challenger` for a full challenge when the service is high-risk (regulated, health, financial, legal, immigration, data-sensitive) or when the founder's messaging assumptions conflict with these checks. Its simulated customer voice is a hypothesis input, not customer evidence.

## Proof Assets

Recommend the smallest credible proof set:

- Customer quote or case study.
- Before/after demo.
- ROI model.
- Benchmark or teardown.
- Security/compliance proof.
- Expert endorsement.
- Review mining.
- Public examples.
- Comparison page.
- Pilot result.

If proof is missing, make proof collection part of the next marketing sprint.

## Metrics

Pick metrics based on goal and stage:

- Early validation: interviews booked, replies, qualified calls, paid pilots, conversion from problem copy.
- Demand generation: qualified traffic, conversion rate, lead quality, CAC, payback.
- Sales-led B2B: meetings, opportunities, win rate, sales cycle, ACV, pipeline source.
- Product-led: activation, retention, expansion, referral, product-qualified leads.
- Ecommerce: conversion rate, AOV, contribution margin, repeat purchase, refund rate.
- Brand/content: assisted pipeline, branded search, direct traffic quality, subscriber-to-lead conversion.
- Product/referral loops: invitation rate, recipient activation, reproduction by cohort, retained contribution, abuse/fraud, complaints.
- Community: useful member-to-member response, return contribution, staff-independent activity, activation/retention/referral influence, moderation load.

Do not treat impressions, views, likes, or follower count as success unless tied to a downstream behavior.
For meaningful paid budgets, recommend an incrementality design where feasible. Platform attribution is diagnostic; it is not by itself causal proof.

## Quality Checklist

Before finalizing, check:

- The target segment is narrow enough to reach.
- The buyer and user are separated when they differ.
- Positioning uses concrete outcomes rather than vague claims.
- The offer reduces risk for the right customer.
- Recommended channels match actual customer behavior or a stated hypothesis.
- Every channel has a named job, operating requirement, conversion bridge, source-cohort metric, and stop rule.
- Founder examples include prerequisites and transfer limits rather than copyable tactics.
- Any product/referral/community loop proves value before invitation and includes retained-economics and abuse gates.
- Proof assets are named, and missing proof becomes part of the plan.
- Metrics include decision thresholds and stop conditions.
- Traction claims were checked against the weak-evidence list and the strategy does not rest on attention metrics alone.
- For consumer services, the customer-perspective challenge pass was run: uncertainty reducers match the service's risk level, segments rest on trigger/job/risk rather than personas, proof uses authentic-review conditions, commitment is staged where outcome variance is high, and exit pathways are clear.

## Output

For a full strategy request, produce:

- Marketing diagnosis.
- Key assumptions and evidence gaps.
- Target segment and buyer.
- Positioning statement.
- Messaging hierarchy.
- Offer design.
- Funnel map.
- Channel strategy table.
- 30/60/90-day campaign plan.
- Proof assets to create.
- Metrics and decision thresholds.
- Risks and tests.
- Next seven-day action plan.

For campaign-only requests, include the strategic assumptions first, then the campaign plan.

## Suggested First Question

If needed, ask:

`Who is the specific buyer you want this marketing strategy to convert first?`
