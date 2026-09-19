# Website skill research — checked 2026-09-14

This is an agent-infrastructure audit, not venture research. Direct X retrieval failed. The supplied [2026-09-12 tweet](https://x.com/cyrilXBT/status/2098652326248493447) was recovered via [FxTwitter](https://api.fxtwitter.com/status/2098652326248493447); repository pages were checked separately. Replies were not retrieved. No third-party installers or repository scripts were executed. Decisions below are our assessment, not upstream endorsements. Firecrawl CLI status was inspected only; web retrieval used the available browser and public HTTP instead.

## All unique GitHub repositories linked in the tweet

| Repository | Relevant capability observed | Decision for this setup |
| --- | --- | --- |
| [obra/superpowers](https://github.com/obra/superpowers) | Engineering workflow and review skills | Defer installation: existing plan/review and regression workflow already covers the need. |
| [upstash/context7](https://github.com/upstash/context7) | Current library documentation access | Optional reference retrieval; use version-matched Next.js docs first. No new mandatory MCP. |
| [anthropics/skills](https://github.com/anthropics/skills) | Frontend design, webapp testing, artifacts, skill authoring | Adapt design critique and browser evidence principles. Existing builder already owns these. Web artifacts are not a Next.js production scaffold; brand-guidelines is not our brand identity. |
| [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | Persistent agent context | Defer: unrelated to site quality, adds persistence/service surface. |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Cross-stack UI/UX design guidance | Reference only; preserve the approved brand rather than install a competing design orchestrator. |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | Visual taste guidance | Reference only; existing creative-direction and anti-template review cover this. |
| [Jakubantalik/transitions.dev](https://github.com/Jakubantalik/transitions.dev) | Transition examples and agent guidance | Optional motion reference, subject to reduced motion and performance budget. |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | CRO, SEO, AI SEO, analytics and marketing workflows | Selectively adapt SEO/consent-aware measurement principles; defer marketing automation to separate backlog. |
| [charlie947/social-media-skills](https://github.com/charlie947/social-media-skills) | Social-media workflows | Document for later digital marketing; outside website implementation. |

Finance, small-business and legal links in the tweet are plugin pages, not GitHub repositories; no installation or legal-compliance claim follows from them.

## Additional sources and decisions (accessed 2026-09-14)

- [Vercel React performance skill](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md): prioritize request waterfalls, client payload and server rendering before micro-optimizations. Adapt principles; do not vendor its rule collection.
- [Vercel web design guidance collection](https://github.com/vercel-labs/agent-skills): browser accessibility, focus, forms and image review reinforces current QA ownership.
- [Next skills migration notice](https://github.com/vercel-labs/next-skills) and [current workflows](https://github.com/vercel/next.js/tree/canary/skills): old standalone guidance moved; retrieve documentation matching the site's installed version. Do not treat canary code as a stable install recommendation.
- [React SEO skill source](https://github.com/daniel-amekpoagbe/react-seo-skills/blob/main/skill/SKILL.md): useful framework detection and focused references. Keep our own smaller launch contract; do not inherit blanket AI-crawler or llms.txt recommendations.
- [Next.js metadata and OG images](https://nextjs.org/docs/app/getting-started/metadata-and-og-images): use framework metadata/file conventions and verify rendered output, including dynamic pages.
- [Google AI features](https://developers.google.com/search/docs/appearance/ai-features): normal SEO remains relevant; special AI files or schema are not required. No promise of ranking, crawling or AI citations.
- [Google robots guidance](https://developers.google.com/search/docs/crawling-indexing/robots/intro): robots controls crawling, not authentication or guaranteed exclusion from indexing.
- [Core Web Vitals](https://web.dev/articles/vitals): LCP, INP and CLS are the field metrics; lab results are separate evidence.
- [EDPB cookie banner taskforce, adopted 2023-01-17](https://www.edpb.europa.eu/system/files/2023-01/edpb_20230118_report_cookie_banner_taskforce_en.pdf) and [CNIL dark-pattern guidance](https://cnil.fr/en/dark-patterns-cookie-banners-cnil-issues-formal-notice-website-publishers): underpin consent requirements. Country-specific application and the actual processing inventory still require review.

No code copied; upstream license compatibility has not been audited for redistribution. Re-check source contents and licenses at a pinned revision before any future import. This review assesses fit, not live comparative model performance.

## Optional measurement additions — checked 2026-09-14

User clarified analytics itself is optional; PostHog is one provider, not required. Optional A/B experiments and campaign tracking extend the existing website skill; broad marketing automation stays deferred.

- [PostHog Next.js](https://posthog.com/docs/libraries/next-js) and [GDPR guidance](https://posthog.com/docs/privacy/gdpr-compliance): use selected EU project settings, consent-controlled initialization and minimal data. No live integration verified.
- [Experiments](https://posthog.com/docs/experiments), [custom assignment](https://posthog.com/docs/experiments/running-experiments-without-feature-flags), [exposures](https://posthog.com/docs/experiments/exposures): keep one assignment authority and explicitly bind exposure/conversion events. No automatic winner or claim of optimal results.
- [Google consent](https://developers.google.com/tag-platform/security/guides/consent), [GA4 events](https://developers.google.com/analytics/devguides/collection/ga4/events), [GA4 validation](https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events): Basic Consent Mode fits our no-optional-request default; HTTP response alone cannot establish processing.
- [PostHog to Meta](https://posthog.com/docs/cdp/destinations/meta-ads) and [PostHog to Google Ads](https://posthog.com/docs/cdp/destinations/google-ads): verified destination documentation. These are conversion exports, not automatic ad-cost imports or GA4 destinations.
- [PostHog marketing analytics](https://posthog.com/docs/web-analytics/marketing-analytics): separate account/source setup for campaign costs. Verify current connectors/scopes at implementation.
- [Meta-maintained archived API schema](https://github.com/facebookincubator/Facebook-Server-Side-API-Swagger/blob/main/server-side-api.yaml): event_name/event_id deduplication reference. Direct current Meta documentation retrieval failed; re-verify current official API before implementation. Do not treat the archived schema as a current API-version contract.

A guessed PostHog GA4 destination page was unavailable and no native GA4 destination was verified. Use documented direct GA4/GTM collection or a separately verified server integration; never claim a built-in PostHog-to-GA4 connector without checking it.

## Robust delivery reference implementations — checked 2026-09-14

- [PostHog official Next.js playground](https://github.com/PostHog/posthog-js/tree/main/playground/nextjs): directory/integration guide inspected; not executed. Do not inherit its development certificate or unconditional capture setup.
- [PostHog Node package](https://github.com/PostHog/posthog-js/tree/main/packages/node) and [Node documentation](https://posthog.com/docs/libraries/node): SDK queue/flush and serverless lifetime guidance; memory batching is not durable delivery. Old posthog-js-lite explicitly moved into this repository. Direct example.mjs retrieval failed, so it is not claimed as an inspected implementation.
- [Meta Business SDK](https://github.com/facebook/facebook-nodejs-business-sdk), [event request implementation](https://github.com/facebook/facebook-nodejs-business-sdk/blob/main/src/objects/serverside/event-request.js), [server event implementation](https://github.com/facebook/facebook-nodejs-business-sdk/blob/main/src/objects/serverside/server-event.js): inspected request/test-event and event-ID APIs. No SDK executed; no vendor token used.
- [GA4 Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4): documented server-side complement; preserve consented attribution and separately verify ingestion.
- [AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html): supports durable handoff/idempotent consumption approach, not a requirement to deploy AWS.

The expanded measurement plan passed a fresh plan review before final reference/sequence integration. Skills prescribe project-specific fake-provider and live authorized acceptance tests; no live analytics or advertising connection is claimed from this infrastructure change.
