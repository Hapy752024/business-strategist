# Meta, Google and TikTok campaign operations

This is the onboarding and operating contract for selected campaigns, not an installed live connector. Read with `marketing-campaign-operations.md` and `journey-activation-and-measurement.md`. Recheck the primary sources below at onboarding: permissions, supported objectives, API versions and product access can change.

## Asset and access inventory

Before creating accounts, list existing assets with platform, type, name/ID, owning business, named administrators/recovery owner, billing owner, assigned people/partners, linked assets and the purpose of each link. Record verification date and unresolved access. Linking for advertising identity, reporting, event sharing or administration does not imply ownership transfer. Avoid duplicate assets as a permission workaround.

| Platform | Keep distinct | Initial connection work |
|---|---|---|
| Meta | Business portfolio; Page/Instagram public identities; ad account; Pixel/dataset; Business Suite; Ads Manager; Events Manager | Verify asset ownership and assignments, Page/Instagram advertising identity and dataset access for the chosen ad account. |
| Google | Cloud project; Ads customer ID; optional manager/MCC; GA4 property/data stream; Google tag/GTM container; conversion actions | Record Ads/GA4 links and measurement destinations separately. Google Ad Manager is the publisher product, not Google Ads or its manager account. |
| TikTok | Business Center; public profile; advertiser account; Pixel/data source; Ads Manager; Events Manager | Verify advertiser/data-source access and the profile/content authorizations needed for the selected ads. |

Keep assets with the intended business and grant named/partner access as appropriate. Verify consequences before claim/transfer operations. Campaigns and experiments usually reuse existing assets; separate businesses when ownership, billing or access requires it. Public research providers and ad libraries are not authenticated own-account reporting connectors.

## Connection choices and setup

### Google

1. Select the Cloud project, enable Google Ads API and confirm an access level permitting the intended accounts. Google documents the developer-token sunset on 2026-09-09: current onboarding uses Cloud-project API access. Do not copy older token instructions into a new connection.
2. Configure the authorized identity through OAuth/ADC (or a separately reviewed supported service-account setup), explicit customer allowlist and manager login ID when needed. Keep credential material outside the workspace and model context.
3. Pin a reviewed official Google Ads MCP version; configure `GOOGLE_PROJECT_ID` and the protected credential location in the isolated runtime. Its documented tools are read-only account discovery, GAQL reporting and resource metadata. The broad OAuth scope is not itself a read-only credential boundary.
4. Test selected-account reads and denied other-account access; verify actual runtime tool exposure. A separate controlled Ads API adapter would be needed for campaign mutations. GA4/Search Console access is separately enrolled.
5. For new offline/CRM conversion integrations use Data Manager API as the starting route. The older `UploadClickConversions` path has restrictions for new adopters from 2026-06-15; grandfathered integrations are not proof a new integration is eligible.

### Meta

1. Select the existing business and ad account, identity assets and dataset. Use Meta's official connector setup, or the custom-app route when required by the chosen client. Owning a developer app is not universally required.
2. Official hosted endpoint: `https://mcp.facebook.com/ads`. Meta documents OAuth, user tokens and Employee-role system-user tokens; Admin-role system-user tokens are unsupported for this MCP.
3. For the reporting pilot request `ads_mcp_management` plus `ads_read`. Do not request `ads_management` or broader asset permissions without a concrete need. Inspect granted scopes, exposed tools and reachable accounts; documentation alone cannot establish that a credential cannot mutate assets.
4. Verify read access and enforce denied mutations in the adapter/test environment without risking a live write. If isolation cannot be demonstrated, use aggregate exports. Meta's broader connector supports writes, so keep write-capable operations out of routine reporting.
5. Enroll Pixel/CAPI/CRM delivery separately. An Ads MCP connection does not install tracking, deduplicate events or close the sales feedback loop.

### TikTok

1. Confirm the Business Center, advertiser and data source, then use an Ads Manager aggregate export for the initial local workflow.
2. For a connected pilot, verify API for Business developer-app eligibility, advertiser authorization, current API version, reporting permissions and token lifecycle against the app's actual access. The documented reporting API supports synchronous and asynchronous reports. No TikTok MCP implementation is verified by this repository.
3. Build or select an isolated reporting adapter for the allowed advertiser IDs, dimensions and metrics. Handle pagination, quotas, report completion/expiry and revocation explicitly. Token access for reporting must not be assumed to authorize Events API or campaign writes.
4. Connect Pixel/Events API as a separate implementation with deduplication QA. For Spark Ads, check content rights, account/post authorization and expiry through the campaign end; organic popularity is only a creative-test hypothesis.

## Evidence required for a connected pilot

Resolve the selected project's Marketing root. Store secret-free definitions in `connections.json`: provider, account IDs, optional manager/campaign scope, project-prefixed credential reference and transport. The local validator still reports `configured_for_local_exports_only`; it never resolves credentials or tests authentication. A token file under a project is not process isolation.

The future collector must enforce account/campaign scope before every request, use a protected identity, return sanitized aggregates, and retain permission/expiry/revocation checks. Verify denied out-of-scope access, pagination completeness, timezones/currencies, report filters, conversion definitions, stale data and partial failures. Record exact live evidence separately from schema validity. Do not globally install a write-capable connector to make a report work.

Connect only after the project/account and enrollment scope are selected. Planning and local definitions do not authorize account access, sending events/customer data, scheduling, publishing or advertising spend.

## Organize a reviewable campaign

Keep the journey hooks, event contract, asset inventory, sales process, creative/landing-page versions, attribution and operational decisions in the campaign's existing context. Store approved claims and owner work in the existing registry/execution queue. Use stable IDs plus a readable naming convention such as project/objective/market/offer/experiment/creative; never use names alone as joins.

| Platform | Draft structure and launch checks |
|---|---|
| Meta | Campaign objective → ad set with conversion location, performance goal/event, audience, placements, budget/schedule → ads with identity, concept, claim evidence, destination and CTA. Verify the selected dataset and event against the contract. |
| Google | Campaign type/objective, bidding goal, geographic intent, budget/schedule → intent-based ad groups and keywords/match types/negatives where applicable → ads/assets and relevant landing pages. Inspect actual search terms and campaign goal overrides. Verify currently supported language settings rather than copying old API fields. |
| TikTok | Campaign objective → ad group with destination, optimization event, audience/placement, bid/budget/schedule → videos/ads with hook, demonstration, proof, CTA, rights and optional Spark authorization. Check current budget minima and creative specs for the selected configuration. |

Choose a structure the learning budget can support; no fixed number of campaigns/ad sets or universal conversion threshold. Each test has a question, expected outcome, denominator, attribution/maturity window, affordable acquisition cost, maximum authorized spend, review date and stop/continue/scale criteria. Broad three-platform capability does not mean every project should launch all three.

Separate platform pacing settings from the owner's total spending ceiling. In particular, Google's average daily budget is not a hard daily cap; most campaigns can incur up to twice that daily amount and the documented monthly limit is 30.4 times it. Recheck exceptions and budget-change behavior. The current repo has no live spend controller, automatic pause or scheduler.

## Monitor the whole sales path

Recommended cadence, only after connection/scheduling authorization:

- **Daily health:** data freshness, delivery/disapprovals, spend/pacing, broken destinations, event-volume loss, duplicate counts, failed/late uploads, consent regressions, expired permissions and CRM handoff failures. Record an owner and urgency for each anomaly. Missing data is unknown, not zero.
- **Weekly review:** comparable mature windows by account/campaign and, when available, ad group/ad/creative/placement or search term. Explain metric definitions and denominators; separate attention, clicks, saved leads, qualified leads, attendance, customers and contribution. Review fatigue, frequency and query relevance only when the required breakdowns exist. Propose bounded changes with evidence, budget impact and rollback criteria.
- **Mature cohorts:** source/experiment to qualified customer, revenue/contribution, acquisition cost, payback, refunds and retention. Separate media-only from fully loaded CAC. Keep platform attribution, unique CRM outcomes and incrementality evidence as different views; never sum platform-attributed conversions as unique customers. Use holdouts when feasible before attributing causal lift.

The installed presets provide campaign-level aggregate reports only. They do not join CRM records or retrieve creative/search-term/event diagnostics. Obtain appropriate aggregate inputs or implement a reviewed adapter before making those claims. Preserve the existing weekly report's three-task limit, owner decisions, stale-context guards and immutable history. Approval of a task is not launch authority.

### Attribution composition and changes in definitions

Before a performance or scaling recommendation, record the selected conversion action, counting method, attribution model and click/engagement/view windows with their current definitions and effective dates. Distinguish optimization settings from reporting comparisons. Request component breakdowns where available; the standard aggregate presets do not supply them. Never sum nested windows (for example, 1-day and 7-day click) or overlapping columns. An attributed total is not a count of unique CRM customers or causal lift.

For Meta website/in-store conversions, the March 2026 announcement changed click-through credit to link clicks and moved non-link interactions into engage-through attribution. Verify the selected account's actual rollout/settings instead of assuming that identically named historical columns mean the same thing. Capture definition/model/counting changes in the existing `measurement.attribution` metadata and context; split the series or obtain comparable restated reports before claiming improvement. The importer compares supplied metadata, but cannot discover an undeclared platform change.

Do not automatically exclude view/engagement credit or prescribe one attribution window for every funnel. Diagnose which credited outcomes correspond to mature qualified sales, then use a suitable controlled lift test if causal impact is material. Pixel/CAPI deduplication fixes duplicate event delivery; it does not establish the causal value of the remaining attributed conversions.

## Sources and review date

Checked 2026-10-24. The [shared discussion](https://chatgpt.com/share/6adc84b1-679c-83ed-b212-14f00f327aa8) was retrieved in full as idea input; its advice and product labels are not independent evidence or authorization. The reusable improvements above are engineering recommendations; primary sources support the specified platform mechanics.

- [Google Ads MCP setup and read-only capabilities](https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server).
- [Google developer-token sunset](https://developers.google.com/google-ads/api/docs/api-policy/developer-token).
- [Google API deprecations and offline-conversion access restrictions](https://developers.google.com/google-ads/api/docs/deprecations).
- [Google primary/secondary conversion actions](https://support.google.com/google-ads/answer/11461796?hl=en).
- [Google budget behavior](https://support.google.com/google-ads/answer/6385083?hl=en).
- [Meta MCP setup and permission requirements](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-get-started/?locale=en_US) (retrieved through Firecrawl after the web reader failed).
- [Meta browser/server deduplication](https://developers.facebook.com/documentation/ads-commerce/conversions-api/deduplicate-pixel-and-server-events.md) (retrieved through Firecrawl).
- [TikTok API for Business endpoint reference](https://business-api.tiktok.com/portal/docs/api-reference/v2.0) (retrieved through Firecrawl after the web reader returned no page body; verify the app's active version at onboarding).
- [TikTok event deduplication](https://ads.tiktok.com/help/article/event-deduplication?lang=en) (page updated May 2025).
- [Google Consent Mode](https://developers.google.com/tag-platform/security/concepts/consent-mode).
- [Meta attribution-definition announcement](https://about.fb.com/ltam/news/2026/03/simplificando-la-medicion-de-anuncios-para-un-mundo-social-first/) (2026-03-03; account rollout is staggered).
- [Jon Loomer's attribution walkthrough](https://www.jonloomer.com/meta-ads-attribution-2026/) (2026; practitioner interpretation, checked against Meta's announcement for changed definitions).
