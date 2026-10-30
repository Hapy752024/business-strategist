# Paid campaign planning

Use for paid plans and budget questions. Retrieve current official documentation before relying on platform thresholds, objective availability, budget minima or bidding rules; record source and date. The platform setup/monitoring contract is repo-root `references/ad-platform-connections.md`.

## Preconditions

A launch recommendation requires a working conversion path, consent-aware event verification, useful message evidence and economics defining affordable acquisition cost. Planning can proceed with gaps labeled. Without retained-value evidence, design a capped learning experiment with explicit unlock criteria.

Apply repo-root `references/journey-activation-and-measurement.md`: source-backed touchpoint → obstacle/hook → ad or useful tool → accessible distribution → CTA/sales path → confirmed event → qualification/customer outcome. Advertising account access and event delivery are separate integrations.

## Channel selection

Select by evidenced customer behavior, buying context, creative capacity and economics. Search may capture demonstrated query intent; social/video may reach people through a relevant demonstration or explanation. Retargeting requires eligible audiences and incremental-value scrutiny. Automated cross-channel campaigns (for example Google Performance Max) need reliable signals and suitable assets. These are conditional hypotheses, not a universal ranking.

Use one primary and at most one supporting channel unless the selected scope and learning budget justify more. Capability on Meta, Google and TikTok does not require spending on all three.

## Learning feasibility

Calculate expected optimization events from affordable spend and an explicitly assumed/observed cost per event. Check current platform learning guidance for the selected objective, but do not treat one event-volume threshold, dollar minimum or fixed number of weeks as a guarantee. Account for conversion/upload delay, sparse outcomes and uncertainty.

If useful learning is unaffordable, consolidate, extend observation, use a justified upstream event that predicts customer quality, choose a cheaper access route, or defer the channel. Never increase spend merely to satisfy an algorithm. Recheck downstream quality when using a proxy.

## Structure and creative

Prepare the selected platform's hierarchy with objective, actual sales destination, optimization event, account/data-source IDs, geography, supported language settings, budget/schedule and exclusions. Group audiences/intents only when the budget supports interpretable comparisons. Distinguish concepts (problem, demonstration, proof, objection) from cosmetic variants; record creative/landing-page versions and the test question. Confirm creator usage rights and authorization expiry where applicable.

For creative comparisons apply repo-root `references/comparative-creative-analysis.md`: distinguish platform allocation from controlled tests, inspect exposure per variant, and leave underexposed ads unproven. Use current product experience and prior learnings in creator briefs; scale creative volume only as the learning budget permits.

## Measurement, budget and decisions

Put the event contract and sales-stage ownership in campaign context. For Meta, browser eventID must equal CAPI event_id for the same action/name/destination; retries preserve it and later CRM milestones get new IDs. For Google, audit native/imported conversion actions and primary/secondary/custom-goal bidding. For TikTok, align Pixel/Events API event and event_id, and verify actual deduplication.

Record total learning budget, platform pacing setting, duration, maximum exposure, owner and decision in the existing budget approval artifact. A Google average daily budget is not a hard daily cap. Document alert/stop ownership and any implementation limits; the current local operator cannot automatically stop spend. Require owner authorization before launch.

Review comparable, sufficiently mature cohorts. Set a stop rule plus continue/scale rules from affordable qualified-customer acquisition, contribution and minimum useful evidence; health failures can require immediate action while commercial results may remain immature. Low exposure is an access finding, not absent demand. Report unknowns and request the missing breakdown/CRM aggregate instead of inventing it. Never add providers' attributed conversions as unique sales.

Before proposing further changes, apply the intervention review in repo-root `references/marketing-campaign-operations.md`. Record what actually changed and when, allow an appropriate observation window, and retain a justified no-change decision. Apply the attribution-composition check in `references/ad-platform-connections.md`; matched column names or successful event deduplication do not establish comparable attribution or causal lift.
