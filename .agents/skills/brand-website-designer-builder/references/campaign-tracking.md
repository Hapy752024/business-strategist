# Optional campaign measurement: PostHog, Google and Meta

Use only for user-selected website tracking implementation or measurement repair. This is not campaign strategy, ad creation, spend authorization or autonomous publishing. Route technical work via website-build; broader strategy remains marketing-strategy-builder/social-digital-marketing-planner. Analytics can be disabled. Advertising measurement is a separate opt-in from product analytics and each destination requires purpose-specific consent.

## Select the smallest topology

Clarify actual product names: GA4 uses a web-stream measurement ID (`G-...`); Google Tag Manager uses a container ID (`GTM-...`); Google Ads uses conversion IDs/labels. Meta uses a Pixel/dataset ID, with optional server-side Conversions API (CAPI). These identifiers are not interchangeable access tokens. PostHog is optional product/website analytics. None must all be installed together.

Inventory existing tags, GTM containers, consent manager, proxies and server destinations before changes. Choose one owner for each event/destination: direct browser integration, GTM, or PostHog/server forwarding. Never simultaneously forward the same conversion through multiple paths without documented deduplication. PostHog can forward selected events to destinations, but does not automatically connect every analytics or ads account.

Two distinct flows need separate configuration and permissions:
- Event delivery: website -> selected analytics; consent-approved conversions -> Meta/Google destinations. This supplies signals for campaign optimization.
- Campaign reporting: authorized read-only ads cost/click/impression imports into PostHog marketing analytics or an approved reporting store. Conversion forwarding alone does not import spend or prove ROAS.

Before any connection record selected account/property/dataset/project IDs, region, least-privilege role/OAuth scopes, owner, budgets, retention and revocation procedure. Keep access tokens, CAPI credentials, GA Measurement Protocol secrets and PostHog personal keys server-side in environment/secret storage; never request them in chat or expose through NEXT_PUBLIC. Client measurement IDs/project tokens are public identifiers, not admin credentials. Prepare code, event mapping and test plan first; request connection/activation only when concrete and not already authorized. Do not create accounts, publish GTM containers, start ads or spend by implication.

## Consent and collection

Apply consent-eu.md. Product analytics and advertising consent are separate. Default all optional collection off; analytics opt-in alone must not forward to Meta/Google Ads. For Google use Basic Consent Mode as the default no-request-before-consent design. Set consent defaults before any tags and update analytics_storage, ad_storage, ad_user_data and ad_personalization correctly. Advanced mode can transmit denied-state pings and is outside this default unless the owner explicitly revises the reviewed policy. Consent Mode is not a consent banner or a legal certification.

Block Meta Pixel/CAPI, Google tags/server events and PostHog destinations before relevant consent and after withdrawal. Server-side tracking, hashing and proxies do not bypass privacy requirements. Do not persist or transmit click IDs/UTMs containing personal data without the reviewed purpose/retention. Remove personal query parameters from page URLs. Never send form values as generic event properties. Enhanced conversions/customer matching is separate personal-data processing; enable only with explicit scope/legal review and official normalization rules.

## Event and attribution contract

Create a project-owned measurement-plan.json or table: canonical event, trigger, required properties/types, consent purpose, destinations, event ID, source, test expectation and owner. Examples are view_page, cta_click, lead_confirmed and purchase_confirmed; map to each platform's actual recommended event names. Conversion is backend-confirmed success, not clicking Submit or loading Thank you. Use consistent value/currency units and a stable non-PII transaction/event ID; retries reuse it.

Define UTM naming and approved click-ID handling, first/last touch choice, attribution windows, timezone/currency, bot/internal/QA exclusions and anonymous-to-known identity policy. Avoid duplicate SPA pageviews by choosing automatic OR manual navigation capture. A user refusing measurement is absent from tracked cohorts; report coverage/bias, not invented attribution.

For Pixel+CAPI dual delivery use the same event_name and event_id for the same outcome, preserving event time and source URL/action_source as required by current Meta docs. CAPI retries must be bounded and idempotent; validate actual Events Manager deduplication. Hashing personal fields does not anonymize them. For GA4 and Google Ads use documented destination-specific transaction/dedup rules; do not assume Meta event_id semantics apply everywhere. PostHog destination filtering must require the right consent, not merely the existence of a product analytics event.

## Tests and connection proof

Start with disabled configuration and sandbox/stub destinations. Assert no traffic/storage under no choice/reject, analytics-only does not trigger ads, advertising opt-in triggers only selected tags, and withdrawal stops browser/server forwarding. Test SDK-load races, SPA reloads, repeated submit, webhook retries and direct thank-you visits. Inspect payload redaction and duplicate conversion prevention.

Then use authorized GA4 DebugView/Realtime, Google Tag Assistant Preview and Meta Test Events/Pixel Helper, plus PostHog live/test events and destination logs. Validate GA Measurement Protocol with its validation endpoint; HTTP success alone does not prove an event was processed. Confirm exactly-once outcomes and identifiers in each selected account, destination failure/retry handling and real consent boundaries. Exclude test traffic from campaign decisions and remove debug/test flags before production. Never claim account linkage from a snippet or local stub.

For reports reconcile spend imports and event totals across platforms, date ranges/currency/attribution windows and consent coverage. Cross-platform counts differ by design; do not add attributed conversions together as unique sales. Record observable discrepancies and latency. An account connection or ROAS dashboard does not prove causal campaign uplift. A/B causal analysis follows experimentation.md.

Sources checked 2026-09-14: [Google consent](https://developers.google.com/tag-platform/security/guides/consent), [GA4 events](https://developers.google.com/analytics/devguides/collection/ga4/events), [GA4 validation](https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events), [PostHog pipelines](https://posthog.com/docs/cdp), [PostHog Meta destination source](https://github.com/PostHog/posthog.com/blob/master/contents/docs/cdp/destinations/meta-ads.md). Direct Meta deduplication documentation retrieval failed in this audit; re-fetch current official Meta CAPI requirements before implementation. No accounts or live tracking connected here.


## Robust server-side delivery (when selected)

Prefer a hybrid topology: consented browser page views/real experiment exposures; server-confirmed lead/signup/purchase events from authoritative business outcomes. A server cannot infer that a page/variant was actually seen from a request alone. Do not replace all browser measurement with server logs or model missing conversions as observed attribution.

Use the existing backend/job infrastructure where available. For meaningful conversions, persist an outbox event atomically with the business outcome (or through a documented reliable handoff). Include a stable event/transaction ID, schema version, event time, consent-purpose/version and destination eligibility. Gate enqueue AND dispatch on valid relevant consent; if consent is withdrawn before delivery, cancel eligible pending forwarding. Define the lookup/propagation and retention policy without creating an unnecessary tracking identity. Do not replay historical pre-consent events after opt-in.

Worker delivery: bounded exponential backoff with jitter, timeout handling, documented retryable versus permanent errors, provider retry hints, dead-letter/alert handling and controlled replay. Reuse event IDs on retries, respect provider event-age limits, inspect response bodies/rejections as well as status, and store redacted delivery receipts. Report accepted, failed, pending and unknown distinctly. A provider timeout is not proof of rejection. Do not promise exactly-once transport; implement idempotent outcomes and verify destination deduplication.

Trust actual backend transactions or authenticated/verified webhooks for revenue/conversions, not client-supplied amounts or success flags. Verify webhook signatures/replays and authorization at capture endpoints, validate event schemas/size, rate-limit abuse, allowlist destinations and keep tokens server-side. Reject arbitrary forwarding URLs and personal fields outside the approved schema. Never expose a generic open tracking proxy or treat browser consent fields as authorization for backend operations.

Use PostHog server SDK, PostHog destination pipelines, direct Meta CAPI, GA4 Measurement Protocol or server-side GTM only where the chosen mapping needs them. Select one delivery owner per destination/event to avoid duplicates. GA4 server events require documented session/client attribution handling; do not invent identity when consent is absent. Meta browser+CAPI pairs use shared event identity. Google Ads and GA4 remain different destinations. Do not introduce a new queue/server container merely for a static site's basic pageviews.

Acceptance tests: backend success then process crash/restart, duplicate webhook/outcome, timeout/retry, permanent provider rejection, provider outage, delayed dispatch after withdrawal, stale event expiry, malformed/untrusted payload, duplicate browser/server paths and dead-letter replay. Prove no double conversion and no forwarding without relevant consent using controlled fake providers first. Authorized provider test events and receipts are a separate integration proof; no current live service is enabled by these instructions.

Verified connector sources (2026-09-14): [PostHog Meta destination](https://posthog.com/docs/cdp/destinations/meta-ads), [Google Ads destination](https://posthog.com/docs/cdp/destinations/google-ads), [campaign cost reporting](https://posthog.com/docs/web-analytics/marketing-analytics). A native PostHog-to-GA4 destination was not verified; use direct documented GA4/GTM or verify an appropriate adapter before promising that path.

## Reference implementations and practical implementation sequence

Use these official references after inspecting the target site's versions. Checked 2026-09-14; source/docs inspected, not installed or run. Pin an appropriate stable release/revision and review licenses before copying. Vendor quickstarts are API examples, not our consent/secret/production contract.

| Concern | Verified reference | Apply carefully |
| --- | --- | --- |
| Next.js client integration | [PostHog Next.js playground](https://github.com/PostHog/posthog-js/tree/main/playground/nextjs), linked by official Next.js docs | Adapt only after consent; do not copy unconditional initialization, US hosts or default capture features. |
| Server capture | [PostHog Node package](https://github.com/PostHog/posthog-js/tree/main/packages/node), [Node docs](https://posthog.com/docs/libraries/node) | SDK memory queue is not a durable outbox. In short-lived/serverless workers await documented flush/shutdown before exit and retain durable retry state; use EU host and minimal profiles. Old posthog-js-lite moved to posthog-js. |
| Meta CAPI | [Meta Node Business SDK](https://github.com/facebook/facebook-nodejs-business-sdk), [ServerEvent source](https://github.com/facebook/facebook-nodejs-business-sdk/blob/main/src/objects/serverside/server-event.js), [EventRequest source](https://github.com/facebook/facebook-nodejs-business-sdk/blob/main/src/objects/serverside/event-request.js) | Source confirms event-ID and Test Events support. Preserve same event_name/event_id, inspect delivery responses. Example personal fields/debug logging are not authorized defaults; keep tokens server-only. Current API/version and policy still need checking. |
| GA4 server events | [GA4 Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4), [validation examples](https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events) | Complements browser collection; preserve consented client/session attribution and validate payloads. Validation does not ingest an event or prove live delivery. |
| Google consent | [Official consent implementation](https://developers.google.com/tag-platform/security/guides/consent) | Use Basic/no-request default, independent analytics/ads choices and consent updates before tags. |
| Reliable handoff | [AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | Adapt to the existing database/queue, do not install AWS infrastructure by default; idempotent consumption is still required. |
| External experiment assignment | [PostHog custom exposures](https://posthog.com/docs/experiments/running-experiments-without-feature-flags) | Explicitly configure exposure mapping from the single assignment authority; conversion properties alone are insufficient. |

Implementation sequence in the selected website project:

1. Capture the user's independent choices: analytics disabled/provider, experiment off/on, ads destinations off/on. Inspect existing code/tags/backend and consent inventory; identify exact account/property/dataset IDs and environment. Persist choices and scope in the website manifest/linked measurement plan.
2. Draft the event map and chosen topology, including pseudonymous identity joins, allowed properties, consent purposes, destination credentials/scopes, deduplication, retention and rollback. Choose direct integrations or forwarding, not both accidentally. Supply a configuration template containing names/placeholders only, never credentials.
3. Build consent adapter and disabled provider interfaces locally. Add browser page/exposure capture only after valid consent. For confirmed backend outcomes add the smallest reliable handoff supported by existing infrastructure; keep SDK memory batching separate from durable delivery state.
4. Implement selected stable SDK/API adapters and platform-specific mappings. For PostHog pipelines prepare the destination filters/mapping as a reviewable artifact; for GTM prepare an unpublished container change. Account operations remain pending until authorized. Missing native GA4 destination support is not filled with an invented connector.
5. Run the stated fake-provider/consent/outbox/duplicate/retry tests and production-build browser regressions. Review network/payload artifacts and failure behavior. A passing local test is not account connection proof.
6. With authorization, connect only selected accounts using scoped credentials/OAuth; run provider test events and inspect actual ingestion/deduplication. Verify ad-cost imports separately, including date/timezone/currency and account identity. Keep unresolved provider rejection or authorization failure explicit.
7. Review the concrete configuration/QA before activation, then update launch evidence for that production URL/configuration. Handoff monitoring/retention/revocation, retry/dead-letter owner, event schema and attribution limitations. Do not launch campaigns or auto-promote an experiment winner.

Destination deduplication tests verify one counted logical conversion despite repeated transport attempts; no generic exactly-once delivery guarantee is made. Unconsented or unjoinable activity stays unmeasured rather than being reconstructed.
