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

Checked 2026-10-31 against Meta's Ads MCP pages (sources below). The repository defines `meta-ads` in `.mcp.json` as Meta's official hosted server; it is disabled until the owner lists it in the gitignored `.claude/settings.local.json`, and no token is stored in the repository.

1. Select the existing business and ad account, identity assets and dataset. Owning a developer app is not required ([Meta's no-app connector setup](https://www.facebook.com/business/help/1456422242197840)); with your own app, add the **Create & manage ads with ads MCP server** use case.
2. Endpoint `https://mcp.facebook.com/ads`. Authentication: OAuth through Facebook Login for Business in the client (the repository's choice), a user access token, or an Employee-role system-user token sent as `Authorization: Bearer`; Admin-role system-user tokens are unsupported. For OAuth with your own app, register `http://localhost:8976/callback` (the entry's fixed `oauth.callbackPort`) as the app's redirect URL; if dynamic client registration is refused, set `oauth.clientId` to the Meta app ID (Meta's own instruction is `claude mcp add --transport http --client-id <META_APP_ID> meta-ads https://mcp.facebook.com/ads`). An app ID is not a secret; a token never goes into `.mcp.json`.
3. Grant exactly `ads_mcp_management` plus `ads_read`. Meta's minimum is `ads_mcp_management` plus `ads_read` (Meta would also accept `ads_management`, which this repository does not request), and the repository does not request `catalog_management`, `business_management`, `pages_show_list` or `instagram_basic` (they unlock more tools, including writes). After sign-in, check the granted scopes (Graph `GET /me/permissions`), exposed tools (`/mcp`) and reachable accounts. Documentation alone cannot establish that a credential cannot mutate assets.
4. Read/write split. Use the MCP for reporting: `ads_get_ad_accounts`, `ads_get_ad_entities` (the primary reporting tool), `ads_get_opportunity_score`, `ads_insights_*`, `ads_get_errors`, dataset/pixel/catalog/experiment `get`/`list`/`read` tools and `ads_account_get_activity_logs`. Every documented write tool is in `permissions.deny` in `.claude/settings.json` as `mcp__meta-ads__<tool>`: `ads_create_campaign`, `ads_create_ad_set`, `ads_create_ad`, `ads_update_entity`, `ads_activate_entity`, `ads_create_creative`, `ads_boost_ig_post`, the custom-audience create/update/update-users/delete tools, every `ads_catalog_*` create/update/delete/connect/disconnect tool, the `ads_pixel_event_*` and `ads_pixel_parameter_*` create/update/delete tools, and `ads_experiment_abtest_create_test`, `ads_experiment_abtest_update_test`, `ads_experiment_lift_create_test`. Glob denies (`*create*`, `*update*`, `*delete*`, `*activate*`, `*boost*`, `*connect*`) also cover similarly named tools Meta adds later; a new write tool with another verb would not be caught, so compare `/mcp` against this list when the server changes. Nothing is in `allow`.
5. The only campaign write path is `scripts/marketing/execute.py` (`create_campaign`) with a signed founder approval: Graph API v26.0, always `PAUSED`, positive `spend_cap`, explicit `is_adset_budget_sharing_enabled`. Activation stays a manual founder step in Ads Manager. The executor's `META_ACCESS_TOKEN` is a separate credential from the MCP sign-in; Meta requires write permission for campaign creation, so never reuse that token for the MCP and do not grant it before a campaign is actually approved. An `ads_read` token suffices for reporting. A write-capable token in the agent's environment can still be used outside the executor by the same OS user (the residual risk in `marketing-execution.md`).
6. Enroll Pixel/CAPI/CRM delivery separately. An Ads MCP connection does not install tracking, deduplicate events or close the sales feedback loop.

### Scheduling (Postiz, self-hosted)

Checked 2026-10-31 against the Postiz docs (sources below). The repository defines `postiz` in `.mcp.json` (status `documented_not_connected`): `url` is `${POSTIZ_BASE_URL:-http://localhost:4007/api}/mcp` (the default is a placeholder) and the key is sent as `Authorization: Bearer ${POSTIZ_API_KEY:-}`, never written into the URL or file (the empty default keeps an unset key from being sent to the server as the literal placeholder text). It stays disabled until the owner lists it in `.claude/settings.local.json`.

Owner steps:

1. Self-host: `git clone https://github.com/gitroomhq/postiz-docker-compose` (Postiz's canonical compose repository), set `MAIN_URL`, `FRONTEND_URL`, `NEXT_PUBLIC_BACKEND_URL` (for example `https://postiz.example.com/api`) and `JWT_SECRET` in its compose file, run `docker compose up` (frontend on `http://localhost:4007` by default) and put it behind HTTPS. The reverse proxy must forward the backend's `/mcp` path with streaming HTTP (`Transfer-Encoding: chunked`).
2. Connect the social channels in the Postiz UI; each platform needs its own developer app on a self-hosted instance (Postiz *Provider API keys* page).
3. Copy the API key from Postiz **Settings > Developers > Public API**. Keys do not expire; rotate there if one leaks. Never paste it into the repository or chat.
4. Export `POSTIZ_BASE_URL` (the backend URL, `NEXT_PUBLIC_BACKEND_URL`) and `POSTIZ_API_KEY` in the shell that launches Claude Code (the MCP entry expands only the process environment; the executor also reads `~/.secrets`), and add both names (no values) to `.env.example`.
5. Enable `postiz` in `.claude/settings.local.json` (`enabledMcpjsonServers`), run `/mcp` and check that `integrationList` returns the connected channels.

Read/write split. Read tools: `integrationList`, `groupList`, `integrationSchema`, `postsListTool`, `mediaListTool`, `mediaStatusTool`, `generateVideoOptions`, `clippingStatusTool`. Denied as `mcp__postiz__<tool>`: `schedulePostTool` (it can also publish `now`), `postSettingsTool`, `triggerTool` and `videoFunctionTool` (generic provider/function executors), `uploadFromUrlTool`, `generateImageTool`, `generateVideoTool` and `clippingTool` (create media or draft posts and may use credits). The only posting path is `scripts/marketing/execute.py` (`schedule_post`) with a signed founder approval: it POSTs `{POSTIZ_BASE_URL}/public/v1/posts` (self-hosted OpenAPI server `https://{your-domain}/api/public/v1`) with `type: schedule` and a future date, and refuses `now`. The public API's create-post endpoint is limited to 90 requests per hour per instance (`API_LIMIT`).

### TikTok

1. Confirm the Business Center, advertiser and data source, then use an Ads Manager aggregate export for the initial local workflow.
2. For a connected pilot, verify API for Business developer-app eligibility, advertiser authorization, current API version, reporting permissions and token lifecycle against the app's actual access. The documented reporting API supports synchronous and asynchronous reports. No TikTok MCP implementation is verified by this repository.
3. Build or select an isolated reporting adapter for the allowed advertiser IDs, dimensions and metrics. Handle pagination, quotas, report completion/expiry and revocation explicitly. Token access for reporting must not be assumed to authorize Events API or campaign writes.
4. Connect Pixel/Events API as a separate implementation with deduplication QA. For Spark Ads, check content rights, account/post authorization and expiry through the campaign end; organic popularity is only a creative-test hypothesis.

## Read connectors (Google)

Checked 2026-10-31. Three read-only Google connectors are defined in `.mcp.json` and disabled until the owner lists them in the gitignored `.claude/settings.local.json`. No credentials exist in the repository; until the owner connects an account, `python3 scripts/marketing/connections.py probe <gsc|ga4|google_ads>` reports `unconnected` with the exact steps and makes no network call. With credentials it makes one read request (Search Console `sites.list`, GA4 Admin `accountSummaries.list`, Google Ads `listAccessibleCustomers`), records `connected|unconnected|error` in the gitignored `.research-infra/marketing-connections.json` and never prints tokens. A passing probe shows one account is reachable; it does not verify property or customer scope.

| Server (pinned) | Source | Can do | Owner steps |
|---|---|---|---|
| `analytics-mcp==0.7.0` (pipx) | [googleanalytics/google-analytics-mcp](https://github.com/googleanalytics/google-analytics-mcp) | Account/property summaries, `run_report`, realtime reports, custom dimensions. Version 0.7.0 exposes no write tools and requests only the `analytics.readonly` scope. | `gcloud auth application-default login --scopes https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform`; enable the Analytics Admin and Data APIs; Viewer access to the property. |
| `google-ads-mcp==0.0.5` (pipx) | [googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp) | `search` (GAQL), `get_resource_metadata`, `list_accessible_customers`. No mutation tools. | ADC with scope `https://www.googleapis.com/auth/adwords` (broad: read-only rests on the exposed tools, so keep the tool list and verify it), Google Ads API enabled in the Cloud project, `GOOGLE_PROJECT_ID` exported in the launching shell. No developer token is configured (see the sunset note above). |
| `search-console-mcp@2.1.3` (npx) | [saurabhsharma2u/search-console-mcp](https://github.com/saurabhsharma2u/search-console-mcp) (tag commit `ec9cf15`) | Search analytics queries, URL inspection, sitemaps list, SEO audits. It also exposes write tools (`sites_manage`, `sitemaps_submit/delete`, `indexing_submit`) and Bing, GA4 and AdSense engines. | `npx search-console-mcp@2.1.3 setup` (user OAuth, default `webmasters.readonly` scope only) and add the account to the Search Console property. Its setup OAuth does not create ADC, so `probe gsc` stays `unconnected` unless ADC with `webmasters.readonly` is also set (an `unconnected` probe then does not mean the MCP is unusable). Do not use owner-level service-account credentials (the server requests the indexing scope itself with them), do not run setup with the indexing scope, do not set `BING_API_KEY`, and do not enable its GA4/AdSense engines. |

Pins are the newest releases at least two weeks old on 2026-10-31 (analytics-mcp 0.8.0 and search-console-mcp 2.1.4 were newer). Overlap: GA4 data is reachable through both `analytics-mcp` and Search Console MCP's GA4 engine; use `analytics-mcp` for GA4 and Search Console MCP for Search Console only. For Search Console, read-only is enforced by the `permissions.deny` entries in `.claude/settings.json` (write and AdSense tools) plus the OAuth scope, because the server has no read-only flag. For Ads the `adwords` scope is broad and read-only rests on the exposed tool list; inspect the tools a runtime actually exposes. MCP output is read for review, not citable customer evidence; for the keyword map use an exported query report through `gsc-queries-v1`.

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
- [Meta Ads MCP tool pages](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-tools-ad-creation-and-management) (plus the reporting, catalog, signals, help, A/B-test and activity-log pages; checked 2026-10-31).
- [Graph API changelog: v26.0 is the latest version](https://developers.facebook.com/docs/graph-api/changelog/) (checked 2026-10-31).
- [Postiz MCP introduction](https://docs.postiz.com/mcp/introduction), [client setup](https://docs.postiz.com/mcp/setup), [tools reference](https://docs.postiz.com/mcp/tools), [public API](https://docs.postiz.com/public-api/introduction), [create post](https://docs.postiz.com/public-api/posts/create), [Docker Compose install](https://docs.postiz.com/self-host/installation/docker-compose), [configuration reference](https://docs.postiz.com/self-host/configuration/reference) and [developer settings](https://docs.postiz.com/general/settings/developers) (checked 2026-10-31).
- [Claude Code MCP permission rules and tool-name wildcards](https://code.claude.com/docs/en/permissions) (checked 2026-10-31).
- [Meta MCP setup and permission requirements](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-get-started/?locale=en_US) (retrieved through Firecrawl after the web reader failed).
- [Meta browser/server deduplication](https://developers.facebook.com/documentation/ads-commerce/conversions-api/deduplicate-pixel-and-server-events.md) (retrieved through Firecrawl).
- [TikTok API for Business endpoint reference](https://business-api.tiktok.com/portal/docs/api-reference/v2.0) (retrieved through Firecrawl after the web reader returned no page body; verify the app's active version at onboarding).
- [TikTok event deduplication](https://ads.tiktok.com/help/article/event-deduplication?lang=en) (page updated May 2025).
- [Google Consent Mode](https://developers.google.com/tag-platform/security/concepts/consent-mode).
- [Meta attribution-definition announcement](https://about.fb.com/ltam/news/2026/03/simplificando-la-medicion-de-anuncios-para-un-mundo-social-first/) (2026-03-03; account rollout is staggered).
- [Jon Loomer's attribution walkthrough](https://www.jonloomer.com/meta-ads-attribution-2026/) (2026; practitioner interpretation, checked against Meta's announcement for changed definitions).
