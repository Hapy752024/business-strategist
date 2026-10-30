# From customer journey to acquisition and sales measurement

Use when reconstructing a customer journey, selecting growth interventions, planning paid campaigns, or implementing campaign tracking. In research, apply only the opportunity-mapping section: keep observed behavior separate from proposed interventions. Marketing owns campaign selection; Website owns implementation; the campaign operator owns reporting. A map does not pass the Business pain gate or authorize launch.

## 1. Identify where an intervention can help

Keep the sourced journey in its existing research artifact. For each material stage, add the following fields, or explain why no useful intervention is supported:

| Field | Required decision |
|---|---|
| Segment, trigger and stage | Who experiences the need, when, and what they are trying to accomplish. Preserve different buyer/user branches. |
| Observed touchpoint | Exact search context, community, partner workflow, product moment or offline setting, with reviewed source/date and uncertainty. |
| Obstacle and hook | The question, friction or objection; the proposed useful promise or assistance. Distinguish the placement opportunity from the ad's opening line. |
| Intervention and tool | Ad, calculator, checklist, comparison, demo, migration help, booking tool, partner embed, onboarding aid or referral after value. Explain how it solves the stage's problem. |
| Access and distribution | Where the first suitable users encounter it; targeting/inventory or partner access, owner, production/maintenance cost, and permissions still needed. A platform named in a report is not an access route. |
| Next action and sales path | CTA, destination, qualification, follow-up owner, response expectation, and next commercial milestone. |
| Measurement and decision | Event, denominator, qualified/retained outcome, maturity window, affordable cost and test/stop rule. |

For a pure customer-problem study, record touchpoints and optional intervention hypotheses without choosing offers, budgets or a business. Never infer advertising eligibility or targeting availability from a customer's public post. Keep topic-led customer evidence independent from supplier claims and ad-library examples.

In selected Marketing work, compare the most plausible placements. Illustrative mechanisms include a checklist in a partner's onboarding, a calculator answering an evaluation question, migration help at switching, a saved-progress recovery step, and a referral request after verified value. Require a distribution route before building a tool. Keep outcome evidence separate from resource downloads, views and signups. Manual outreach, messaging, paid creators, rewards and paid distribution retain their applicable authorization; research-participant recruitment remains unpaid by default.

## 2. Specify the sales path before the tags

Separate the acquisition source (Meta, Google, TikTok, partner, organic) from the sales destination (website checkout, native lead form, booked consultation, phone, messaging, app or store). Record the actual path and system of record. A native lead form or chat enquiry must not be represented as a website form success.

Define the applicable stages, for example: accepted enquiry → qualified → appointment booked → attended → customer/payment confirmed → activated → retained/refunded. These are examples, not a mandatory funnel. State qualification criteria, stage owner, timestamp, status-transition rule and source-of-truth record. A provider's message acceptance does not prove the sales team received the lead; booking does not prove attendance; a click does not prove a saved enquiry.

Record the selected optimization stage separately from diagnostic events. Use the deepest reliable, sufficiently frequent outcome that predicts business value, with a documented reason for any upstream proxy and a later quality check. Do not inflate the signal by counting several stages of one lead as equivalent customers.

## 3. Write the event contract

Put the following tables in the selected campaign's existing `campaign-context.md` under reviewed Marketing publication, so context changes invalidate old task recommendations. For a website-only request use its existing implementation/QA brief. Do not create a competing strategy document or copy private event payloads into research.

Each event row must contain:

- Canonical business event, exact successful trigger and non-triggers; owning backend/CRM system and sales stage.
- Stable business occurrence ID and generation point, business timestamp, retry/idempotency rule, and separate identity for later milestones.
- Destination account plus dataset/pixel/property/conversion-action IDs; per-platform event names and browser/server/native/CRM delivery paths.
- Value definition, currency and refund/cancellation treatment. Use actual revenue/contribution definitions appropriate to the business; never equate an insurance premium with broker revenue.
- Allowed parameters, matching identifiers, consent/permission conditions, prohibited fields, retention and responsible owner.
- Optimization versus observation role, attribution window/model, expected conversion/upload delay and QA evidence/status.

Keep one canonical business ledger and explicit provider mappings; do not force identical event names across platforms. Record a separate routing/UTM convention using stable campaign, creative and experiment IDs; retain platform IDs even when names change. UTMs must not contain personal data. Preserve permitted click identifiers through the selected sales path in restricted systems, not public reports. Unknown source stays unknown; later CRM imports must not invent click attribution.

## 4. Align Meta Pixel and CAPI

For copies of the same action, use the same destination Pixel/dataset, exact event name and identifier: browser `eventID` equals CAPI `event_id`. Generate once after the business action succeeds, return the ID to the browser, and persist it for server delivery/retries. Meta documents a 48-hour deduplication window; avoid late blind replay. Matching fields such as `fbp`, `fbc` or hashed contact data have a different job from the event ID. See [Meta deduplication](https://developers.facebook.com/documentation/ads-commerce/conversions-api/deduplicate-pixel-and-server-events.md), checked 2026-10-24.

Synthetic identity example (not a complete API payload):

```text
Backend commits enquiry: canonical occurrence = enquiry-7f3
Pixel: event Lead, eventID enquiry-7f3
CAPI:  event_name Lead, event_id enquiry-7f3
Retry: same occurrence ID and original business timestamp
Later qualification: new occurrence ID and reviewed CRM event mapping
```

Implementation requirements: persist the event with the successful transaction (or equivalent durable handoff), send asynchronously, track attempts and expiry, and prevent duplicate business writes on form/webhook retries. Check consent again before dispatching queued work. Failed writes emit no completion event. A refreshed thank-you page must not create another occurrence. Choose one owner per tag/event; inspect partner integrations, GTM, custom code and automatic events for overlap. Keep CAPI credentials server-side. Use the correct action source and sanitized source URL for the actual sales path.

## 5. Map Google and TikTok deliberately

- **Google:** select the native Ads or imported GA4 conversion action that represents the outcome. Avoid making both measurements of the same action biddable. Primary actions are used for bidding when the corresponding goal is selected; secondary actions in a custom goal can also be used for bidding. Audit campaign-specific and account-default goals, counting rules and values. A Meta-style `event_id` is not a universal Google deduplication solution. Use the applicable transaction/order identifier and upload retry semantics, and inspect duplicate conversion actions. [Google conversion roles](https://support.google.com/google-ads/answer/11461796?hl=en), checked 2026-10-24.
- **TikTok:** map to currently supported standard/custom events for the selected objective. If Pixel and Events API describe the same action, send matching `event` and `event_id` to the intended data source. Maintain stable IDs across retries and check provider timing rules. Confirm browser/server overlap in Events Manager; a successful API response alone is insufficient. [TikTok deduplication](https://ads.tiktok.com/help/article/event-deduplication?lang=en) (updated May 2025) and [setup verification](https://business-api.tiktok.com/portal/docs/verify-events-setup/v1.3), checked 2026-10-24. The latter is a version-specific guide; verify the active API version before implementation.

## 6. Verify consent, event integrity and business outcomes separately

Before launch spend, compare the event contract with events actually observed: run `scripts/marketing/verify_tracking.py` (procedure: "Verify tracking before launch" in the campaign operations reference).

Use the project's consent/privacy design for browser, server and CRM paths. Do not add server tracking to bypass a refusal. Minimize URL, title, automatic-event and matching data; exclude sensitive questionnaire answers and free text. Hashing does not make prohibited data permissible. Confirm current platform and jurisdiction requirements before activating a regulated campaign.

For Google, distinguish the consent interface from Consent Mode. Configure `ad_storage`, `analytics_storage`, `ad_user_data` and `ad_personalization` deliberately. Advanced mode can send cookieless pings after denial; it is not equivalent to blocking all requests. Choose the implementation against the project's documented policy and verify initial refusal and later withdrawal with real network/provider behavior. [Consent Mode overview](https://developers.google.com/tag-platform/security/concepts/consent-mode), checked 2026-10-24.

Before launch, retain evidence for successful action, failed action, double submit, refresh/back navigation, webhook retry, delayed server delivery, browser-only/server-only paths where applicable, consent grant/refusal/withdrawal, new CRM milestone, and wrong-account prevention. Test purchases/refunds need the correct value/currency treatment. Keep tests out of production optimization and reporting using the provider's supported test mechanism or isolated assets; never assume every debug flag excludes production reporting.

Report these as separate checks: business record exists; delivery accepted; event visible; duplicates reconciled; identity matching; ad attribution; actual customer quality. High Event Match Quality is not proof of deduplication, attribution or profit. Reconcile platform event counts with eligible backend occurrences for comparable time windows, accounting for consent, delays and attribution differences. Do not expect attributed conversions to equal all business events. Only call tracking verified after the relevant real-provider checks; mocks and structural review remain local evidence.
