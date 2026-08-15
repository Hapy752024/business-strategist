---
name: social-digital-marketing-planner
description: Create detailed, actionable social media and digital marketing plans grounded in audience research, platform fit, content strategy, paid/organic channel mix, creative testing, campaign calendars, measurement, and risk review. Use this skill whenever the user asks for a social media plan, digital marketing plan, content calendar, paid social strategy, organic social strategy, influencer or creator strategy, campaign launch plan, Meta/TikTok/LinkedIn/Instagram/YouTube/X/Pinterest strategy, social audit, digital acquisition roadmap, or examples of good and bad social marketing to apply to their business.
---

# Social / Digital Marketing Planner Workflow

Use this skill when the user wants a detailed, actionable social or digital marketing plan. The goal is not to produce a list of post ideas; the goal is to connect audience behavior, offer, creative, channel execution, measurement, and learning cadence.

## Reference

Before creating a substantial plan, read:

- `references/social-digital-marketing-research.md`
- If the user arrives with an untested channel/content idea, validate it first with `social-media-idea-validator`; its `references/founder-playbooks.md` holds the practitioner evidence base (SaaS, insurtech, professional services) for what actually works.

If the user asks for latest platform-specific specs, ad formats, targeting features, algorithm changes, or benchmarks, search current official platform documentation before giving precise advice.

## Stance

Be practical and skeptical. Do not assume social media activity equals business progress. Do not recommend posting everywhere. Do not recommend paid spend until the audience, offer, conversion path, creative testing plan, and success threshold are clear.

Separate:

- Evidence: current assets, customer language, analytics, past campaign data, competitor examples, platform docs.
- Assumptions: audience, channel behavior, creative angle, offer, conversion path.
- Plan: concrete actions, owners, cadence, budget, and thresholds.
- Risks: brand safety, claims, cultural context, compliance, privacy, accessibility, and creative fatigue.

## Sequencing Gate

Before building any paid-scale plan, apply the sequencing rule from the cross-skill evidence registry (`references/evidence-registry.md` at repo root): manual learning → retained-value proof → one repeatable acquisition motion → broader marketing scale.

When the user cites traction, classify every claim against the registry's weak-evidence list — downloads, signups, waitlists, views, likes, followers, subscribers, press spikes, and partnership announcements are weak until tied to retained customers or contribution economics (Socialcam is the canonical counterexample).

If no retained-value evidence exists, do not produce a scale plan. Produce a capped learning-budget experiment plan with explicit unlock gates (activation/retention targets) that release larger paid spend only when the evidence arrives. Name the gate, the metric, and the threshold.

## Ambiguity and Unknowns

If missing information would materially change the plan, ask one focused question before creating the full plan. Highest-leverage unknowns are target customer, offer, business goal, geography/language, budget, existing channels, and whether the plan is B2B, B2C, local, ecommerce, SaaS, marketplace, service, or creator-led.

If the user wants a fast draft, state assumptions clearly and create a testable plan that can be refined.

If the user is still exploring which customer problem or segment to pursue, use `market-problem-discovery` before planning channels. For unsupported demand claims about a chosen candidate, use `idea-grill` and `evidence-scout`. For competitor positioning or channel examples, use `competitor-scout` and `competitor-marketing-analyzer`. For broader marketing strategy, coordinate with `marketing-strategy-builder`.

## Minimum Inputs

Try to capture:

- Business model and offer.
- Target customer, buyer, and geography/language.
- Primary goal: awareness, trust, community, leads, sales, bookings, app installs, retention, referrals, or hiring.
- Current assets: website, landing page, profiles, email list, customer stories, reviews, product photos/videos, founder/expert voices.
- Current channels and performance baselines.
- Budget and team capacity.
- Time horizon.
- Constraints: regulated claims, sensitive categories, brand voice, approval workflow, legal/compliance.

## Procedure

1. Diagnose the goal, stage, audience, offer, channel history, budget, and constraints.
2. State assumptions and gaps before recommending platforms or budget.
3. Define the audience and buyer trigger in concrete language.
4. Map platform roles by funnel stage instead of listing every social network.
5. Define content pillars and creative angles tied to audience pain, desire, proof, objections, and identity.
6. Build the organic plan: cadence, formats, calendar, engagement routine, repurposing system.
7. Build the paid plan only when conversion path and creative testing logic are clear.
8. Define measurement: baselines, KPIs, thresholds, reporting cadence, and experiments.
9. Add a risk review before launch.
10. End with a 7-day action list and 30/60/90-day roadmap.

## Strategic Planning Frame

Use this order:

1. Business objective.
2. Audience and buyer.
3. Offer and conversion path.
4. Message and proof.
5. Platform roles.
6. Content system.
7. Paid/organic mix.
8. Creative testing plan.
9. Measurement.
10. Risk review.
11. Roadmap.

If the user starts with a channel request such as "make a TikTok strategy" or "spend on Meta ads", still state the audience, offer, and measurement assumptions first.

## Platform Roles

Choose platforms by audience behavior, content fit, and operational capacity:

- Instagram: visual storytelling, Reels, lifestyle, product proof, creator/UGC, community, local discovery.
- TikTok: platform-native short video, entertainment, education, founder/employee/customer presence, trend-aware storytelling, creative testing.
- LinkedIn: B2B trust, thought leadership, founder/executive voice, hiring brand, demand generation, account targeting.
- YouTube: search-led education, product demos, tutorials, reviews, long-form proof, Shorts repurposing.
- Meta/Facebook: broad paid reach, retargeting, local/community, groups, older demographics, conversion campaigns.
- X: real-time commentary, founder voice, tech/media niches, customer support, industry conversation.
- Pinterest: visual search, evergreen discovery, shopping inspiration, DIY, home, fashion, food, events.
- Email/SMS: conversion, retention, owned audience, launch follow-up, lifecycle campaigns.
- Search/SEO/paid search: demand capture when users already search for the problem, category, or competitor.

Do not recommend a platform unless you can explain its role, audience fit, content requirement, and success metric.

## Content System

Define content pillars. Common pillars:

- Pain/problem education.
- How-to and utility.
- Proof: case studies, reviews, before/after, demos, numbers.
- Objection handling.
- Founder/expert point of view.
- Community/customer stories.
- Product/service spotlight.
- Behind the scenes.
- Timely/trend response.
- Offer or conversion content.

For each pillar, specify:

- Audience job.
- Format.
- Example topics.
- CTA.
- Funnel stage.
- KPI.
- Repurposing path.

## Creative Testing

For paid social and high-priority organic campaigns, define test variables:

- Hook.
- Audience angle.
- Pain vs desire.
- Proof type.
- Format: UGC, founder video, demo, carousel, static, testimonial, before/after, explainer.
- CTA.
- Offer.
- Landing page or conversion path.

Use a test matrix instead of random content. Start with large differences between creatives before fine-tuning small details.

For TikTok-style short video, include native-feeling vertical video, early hook, human presence, text overlays, clear proposition, and CTA.

For Meta-style paid campaigns, include concise copy, motion or vertical/square formats, placement-aware assets, clear CTA, and creative refresh triggers.

For B2B LinkedIn, prioritize relevance, trust, intent, thought leadership, proof, and quality of leads over raw lead volume.

## Measurement

Tie metrics to the goal:

- Awareness: reach, frequency, video views, share of voice, branded search lift.
- Trust/community: comments quality, saves, shares, DMs, repeat engagement, sentiment, community growth.
- Traffic: CTR, landing-page views, engaged sessions, source quality.
- Leads: qualified leads, cost per qualified lead, meeting rate, lead-to-opportunity rate.
- Sales/ecommerce: conversion rate, CAC, contribution margin, ROAS, payback, repeat purchase.
- B2B pipeline: account engagement, MQL/SQL quality, opportunity creation, pipeline value, sales cycle, win rate.
- Retention: repeat purchase, renewal, churn reduction, referral, lifecycle engagement.

For meaningful paid budgets, recommend incrementality or lift testing when feasible. Do not treat attribution reports as the full truth.

## Risk Review

Before recommending publication or launch, check:

- Does the claim require proof, regulatory review, or substantiation?
- Could the message be misunderstood when seen without context?
- Is the campaign borrowing from a sensitive social issue, tragedy, identity, or movement?
- Has anyone outside the core team reviewed it from the audience's perspective?
- Does humor punch down or alienate the buyer?
- Are testimonials, before/after claims, AI claims, health/finance/legal claims, or environmental claims compliant?
- Are accessibility basics covered: captions, readable contrast, alt text where relevant?
- Are privacy and consent handled for UGC, customer data, tracking, and retargeting?
- Is there a crisis response owner if the campaign receives backlash?

## Good And Bad Examples

When the user asks for examples, present them as reusable mechanics:

- Good example mechanics: personalized shareability, distinctive brand asset, native platform behavior, useful thought leadership, community participation, proof-led conversion.
- Bad example mechanics: tone-deaf cultural borrowing, context-dependent shock copy, trend-jacking without brand permission, unsupported claims, vanity metrics, over-polished content on native platforms, paid spend before offer validation.

Do not advise copying another brand's tone unless the user's brand has permission to behave that way.

## Output

For a full plan, produce:

- Executive diagnosis.
- Key assumptions and missing inputs.
- Target audience and buyer trigger.
- Goal and KPI hierarchy.
- Platform-role map.
- Messaging and content pillars.
- Organic social plan.
- Paid digital/social plan, if relevant.
- Creative testing matrix.
- Content calendar outline.
- Measurement dashboard.
- Experiment backlog.
- Risk and approval checklist.
- 7-day action plan.
- 30/60/90-day roadmap.

For a narrower request, produce the relevant slice but keep the same evidence, measurement, and risk discipline.

## Quality Checklist

Before finalizing, check:

- The plan starts from business objective and audience, not platform preference.
- Each recommended channel has a role, content requirement, and KPI.
- The content pillars connect to pain, proof, objections, desire, or identity.
- The plan includes a feasible cadence based on team capacity.
- Paid spend has a conversion path, creative test plan, and stop/scale threshold.
- Traction claims were classified against the weak-evidence list; a scale plan was only produced when retained-value evidence exists.
- Metrics distinguish attention from business impact.
- Risk review catches cultural, legal, claim, privacy, and accessibility issues.
- Next actions are specific enough to execute this week.

## Suggested First Question

If needed, ask:

`What is the primary business outcome this social/digital plan must drive in the next 90 days: awareness, qualified leads, sales/bookings, retention, or community?`
