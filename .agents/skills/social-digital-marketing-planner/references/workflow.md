---
name: social-digital-marketing-planner
description: Create detailed, actionable social media and digital marketing plans grounded in audience research, platform fit, content strategy, paid/organic channel mix, creative testing, campaign calendars, measurement, and risk review. Use this skill whenever the user asks for a social media plan, digital marketing plan, content calendar, paid social strategy, organic social strategy, influencer or creator strategy, campaign launch plan, Meta/TikTok/LinkedIn/Instagram/YouTube/X/Pinterest strategy, social audit, digital acquisition roadmap, or examples of good and bad social marketing to apply to their business.
---

# Social / Digital Marketing Planner Workflow

Use this skill when the user wants a detailed, actionable social or digital marketing plan. The goal is not to produce a list of post ideas; the goal is to connect audience behavior, offer, creative, channel execution, measurement, and learning cadence.

## Reference

Before creating a substantial plan, read:

- `references/social-digital-marketing-research.md`
- The channel jobs, founder prerequisites, loop gates, community operating model, and incrementality rules in `references/evidence-registry.md` at repo root.
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

If the user is still exploring which customer problem or segment to pursue, use `market-problem-discovery` before planning channels. For unsupported demand claims about a chosen candidate, use `idea-grill` and `evidence-scout`. For competitor positioning or channel examples, use `competitor-scout` and `competitor-marketing-analyzer`. For broader marketing strategy, coordinate with `marketing-strategy-builder`. For consumer services that are regulated, data-sensitive, or hard to reverse, challenge the offer and message with `service-customer-perspective-challenger` before committing creative and spend.

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
4. Map platform roles by customer job—discovery, education/trust, capture, conversion, activation, lifecycle, community, or recruiting—instead of listing every social network.
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

Choose platforms by audience behavior, customer job, content fit, conversion bridge, and operational capacity:

- Instagram: visual proof, identity/lifestyle, Reels, creator/customer stories, and local discovery. Do not use it as the sole explanation/conversion path for complex high-trust finance.
- TikTok: discovery, native short-video creative learning, human demos, and founder/employee/customer presence. It needs sustained creative cadence and an education/conversion bridge for considered purchases.
- LinkedIn: B2B trust, founder/expert point of view, account education, trigger-based outreach, hiring, and qualified pipeline. Generic corporate posting and broad B2C reach are weak fits.
- YouTube: searchable education, product demos, comparisons, customer stories, and long-form proof; Shorts can support discovery. Production and compounding are slower than direct first-customer work.
- Meta/Facebook: paid reach, retargeting, local services, older audiences, conversion campaigns, and participation in some established groups. An organic page is not a community, and paid scale requires retained-value and incrementality gates.
- X: real-time commentary, founder voice, tech/media niches, customer support, and industry conversation. Use only where the target audience and founder operating style fit.
- Reddit/Hacker News/specialist forums: problem learning, feedback, and credible niche entry through useful participation. Promotion-first posting, lead scraping, and treating votes as demand are anti-patterns.
- Pinterest: visual search, evergreen discovery, shopping inspiration, DIY, home, fashion, food, events.
- Email/SMS: conversion, retention, owned audience, launch follow-up, lifecycle campaigns.
- Search/SEO: explicit problem/category/comparison intent and durable education; an unknown category first needs category education.
- Paid search: explicit demand capture with source-cohort and incrementality measurement; check whether brand ads merely intercept organic users.
- Creators/podcasts: borrowed niche trust, education, and demonstrations; select for audience/product fit and qualified downstream behavior, not follower count.
- Product surfaces: recipient exposure, collaboration, referral, and network utility. These are loops rather than media channels and require value before invitation.

Do not recommend a platform unless you can explain its customer job, audience/context fit, operating requirement, conversion bridge, source-cohort metric, and stop rule. Run the eight-question channel/loop recommendation protocol in `references/evidence-registry.md` (stage, customer context, channel job, mechanism, prerequisites, cohort gate, transfer limit, stop rule) for each primary and supporting platform. Name one primary platform and one supporting/owned motion; explicitly defer the rest.

## Product, Referral, And Community Loops

Do not call a share button, contact upload, waitlist, follower base, or branded group a loop by default. Diagnose:

- Recipient exposure: a necessary participant experiences immediate value.
- Collaboration: a shared job becomes more useful with a relevant participant.
- Reciprocal reward: both parties receive product-relevant value.
- Scarcity/invite: access is genuinely limited and invitations follow qualification or activation.
- Network utility: relevant connections improve recurring product value.
- Community: members repeatedly create value for one another.

For each proposed loop, map every step, value before the ask, recipient relevance, activation/retention by source, reward economics, attribution, fraud/abuse, complaints, privacy, and compliance. Defer the loop when single-user value or retained economics are unproven.

For community, specify the member identity, recurring exchange, founding cohort, ritual, founder/operator role, newcomer path, roles/recognition, moderation, safety, and link to customer outcomes. Track useful member-to-member response, return contribution, staff-independent activity, product/customer outcomes, and moderation load—not member count alone.

## Founder-Pattern Transfer Check

When borrowing a founder story, name the mechanism and the prerequisite. Dropbox's demo had technical-community fit; Stripe had dense YC access and technical credibility; Buffer had a relevant founder audience; Monzo had a strong mission, timing, media access, and an early-adopter cohort willing to tolerate an incomplete product. If the prerequisite is missing, test the underlying mechanism at small scale or reject the tactic.

Treat “growth hacking” as low-cash, high-learning, compounding distribution: founder onboarding, useful community participation, customer-language content, high-intent SEO, native repurposing, post-activation invitations, product-currency rewards, recipient exposure, and manual partner handoffs. Reject spam, fake scarcity, manufactured controversy, mass unsolicited automation, dark patterns, and regulatory arbitrage.

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
- Product/referral loops: invitation rate, recipient activation, loop conversion, retained contribution, abuse/fraud, complaints.
- Community: useful response, return contribution, staff-independent activity, activation/retention/referral influence, moderation load.

For meaningful paid budgets, recommend incrementality or lift testing when feasible. Do not treat attribution reports as the full truth.

## Risk Review

Before recommending publication or launch, check:

- Does the claim require proof, regulatory review, or substantiation?
- Could the message be misunderstood when seen without context?
- Is the campaign borrowing from a sensitive social issue, tragedy, identity, or movement?
- Has anyone outside the core team reviewed it from the audience's perspective?
- Does humor punch down or alienate the buyer?
- Are testimonials, before/after claims, AI claims, health/finance/legal claims, or environmental claims compliant?
- Are reviews and testimonials authentic, unincentivized (or disclosed per FTC material-connection rules), recent, and specific? Never recommend buying, faking, or suppressing reviews as a tactic — it is both a documented trust-destroyer and a legal violation.
- Are fees, total price, cancellation, and refund terms clear in every ad, landing page, and funnel step? Hidden fees and hard cancellation are compliance constraints and trust failures, not conversion tactics.
- For consequential, data-sensitive, or hard-to-reverse services, do the ads and landing pages carry the uncertainty reducers (precise scope, credentials, total price, human access, redress) from the Service-Customer Decision and Trust section of the evidence registry — or do they only promise lifestyle outcomes?
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
- Each recommended channel also has a conversion bridge, source-cohort metric, and stop rule; deferred channels are named.
- Founder examples include prerequisites and transfer limits rather than copyable surface tactics.
- Product/referral/community loops prove value before invitation and include retained-economics, abuse, and compliance gates.
- The content pillars connect to pain, proof, objections, desire, or identity.
- The plan includes a feasible cadence based on team capacity.
- Paid spend has a conversion path, creative test plan, and stop/scale threshold.
- Traction claims were classified against the weak-evidence list; a scale plan was only produced when retained-value evidence exists.
- Metrics distinguish attention from business impact.
- Risk review catches cultural, legal, claim, privacy, and accessibility issues.
- Review/testimonial tactics meet authenticity and disclosure rules; fees, cancellation, and refund terms are clear in ads and landing pages; high-risk service creative carries uncertainty reducers, not just lifestyle promises.
- Next actions are specific enough to execute this week.

## Suggested First Question

If needed, ask:

`What is the primary business outcome this social/digital plan must drive in the next 90 days: awareness, qualified leads, sales/bookings, retention, or community?`
