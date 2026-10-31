# Meta, Google and TikTok campaign operations

This is the onboarding and operating contract for selected campaigns, not an installed live connector. Read with `marketing-execution.md` and `journey-activation-and-measurement.md`. Recheck the primary sources below at onboarding: permissions, objectives, API versions and product access change. Owner setup steps per provider live in `config/marketing/providers.json`.

## Asset and access inventory

Before creating accounts, list existing assets with platform, type, name/ID, owning business, administrators/recovery owner, billing owner, assigned people/partners and linked assets with the purpose of each link. Record verification date and unresolved access. Linking for advertising identity, reporting or event sharing does not transfer ownership. Avoid duplicate assets as a permission workaround.

| Platform | Keep distinct |
|---|---|
| Meta | Business portfolio; Page/Instagram identities; ad account; Pixel/dataset; Ads Manager; Events Manager |
| Google | Cloud project; Ads customer ID; optional manager/MCC; GA4 property/data stream; tag/GTM container; conversion actions (Google Ad Manager is the publisher product, not Google Ads) |
| TikTok | Business Center; public profile; advertiser account; Pixel/data source; Ads Manager; Events Manager |

Public research providers and ad libraries are not authenticated own-account reporting connectors.

## Connection choices and setup

### Google

1. Select the Cloud project, enable Google Ads API and confirm access for the intended accounts. Google documents the developer-token sunset on 2026-09-09; do not copy older token instructions into a new connection.
2. Use OAuth/ADC with an explicit customer allowlist; keep credential material outside the workspace and model context.
3. The pinned Google Ads MCP is read-only by its exposed tools; the broad OAuth scope is not itself a read-only boundary. Campaign mutations would need a separate controlled adapter.
4. For new offline/CRM conversion integrations start with Data Manager API; `UploadClickConversions` is restricted for new adopters from 2026-06-15.

### Meta

Checked 2026-10-31. `meta-ads` in `.mcp.json` is Meta's official hosted server (`https://mcp.facebook.com/ads`, client-side OAuth); it stays disabled until the owner lists it in the gitignored `.claude/settings.local.json`, and no token is stored in the repository.

1. Select the existing business, ad account, identity assets and dataset. A developer app is not required; with your own app, add the **Create & manage ads with ads MCP server** use case and register `http://localhost:8976/callback`.
2. Grant exactly `ads_mcp_management` plus `ads_read`. The repository does not request `ads_management`, `catalog_management`, `business_management`, `pages_show_list` or `instagram_basic` (they unlock writes). After sign-in check granted scopes (`GET /me/permissions`), exposed tools (`/mcp`) and reachable accounts.
3. Read/write split: use the MCP for reporting (`ads_get_ad_entities` is the primary tool; `ads_insights_*`, `ads_get_errors`, `ads_account_get_activity_logs`). Every documented write tool, plus glob denies on create/update/delete/activate/boost/connect verbs, is in `permissions.deny` in `.claude/settings.json`; nothing is in `allow`. Compare `/mcp` against the deny list when the server changes, because a write tool with a new verb would not be caught.
4. The only campaign write path is `scripts/marketing/execute.py` (`create_campaign`) with a signed founder approval: always `PAUSED`, positive `spend_cap`. Activation stays a manual founder step in Ads Manager. The executor's `META_ACCESS_TOKEN` is a separate write credential: never reuse it for the MCP and do not grant it before a campaign is approved.
5. Enroll Pixel/CAPI/CRM delivery separately; an Ads MCP connection does not install tracking or deduplicate events.

### Scheduling (Postiz, self-hosted)

Checked 2026-10-31. `postiz` in `.mcp.json` (status `documented_not_connected`) uses `${POSTIZ_BASE_URL:-http://localhost:4007/api}/mcp` and sends the key as `Authorization: Bearer ${POSTIZ_API_KEY:-}`, never in the URL or file. It stays disabled until the owner enables it in `.claude/settings.local.json`.

Owner steps: self-host from `gitroomhq/postiz-docker-compose` behind HTTPS (the proxy must stream the `/mcp` path); connect channels in the Postiz UI; copy the API key from **Settings > Developers > Public API** (never paste it into the repository or chat); export `POSTIZ_BASE_URL` and `POSTIZ_API_KEY` in the launching shell and add the names (no values) to `.env.example`; enable the server and check `integrationList`.

Read tools (`integrationList`, `postsListTool`, `mediaListTool` and other list/status tools) are allowed; posting, media-generation and generic function tools are denied as `mcp__postiz__<tool>`. The only posting path is `scripts/marketing/execute.py` (`schedule_post`) with a signed founder approval: it POSTs `{POSTIZ_BASE_URL}/public/v1/posts` with `type: schedule` and a future date, and refuses `now`.

### TikTok

Start with an Ads Manager aggregate export. A connected pilot needs verified API for Business eligibility, advertiser authorization, current API version and token lifecycle; no TikTok MCP is verified here. Reporting access does not authorize Events API or campaign writes. For Spark Ads check content rights and authorization expiry through the campaign end.

## Read connectors (Google)

Checked 2026-10-31. Three read-only connectors are defined in `.mcp.json` and disabled until the owner enables them: `analytics-mcp==0.7.0`, `google-ads-mcp==0.0.5` and `search-console-mcp@2.1.3`. Until an account is connected, `python3 scripts/marketing/connections.py probe <gsc|ga4|google_ads>` reports `unconnected` with the exact owner steps and makes no network call; a passing probe shows one account is reachable, not property scope. Search Console MCP also exposes write and AdSense tools: read-only rests on `permissions.deny` plus the `webmasters.readonly` scope, so never run its setup with the indexing scope, never use owner-level service-account credentials and do not set `BING_API_KEY`. Use `analytics-mcp` for GA4. MCP output is read for review, not citable customer evidence; for the keyword map use an exported query report through `gsc-queries-v1`.

## Evidence required for a connected pilot

Store secret-free definitions in `connections.json` (schema `schemas/marketing-connections.schema.json`); the local validator never resolves credentials or tests authentication. A future collector must enforce account/campaign scope before every request, use a protected identity and return sanitized aggregates; verify denied out-of-scope access, pagination, timezones/currencies and partial failures. Do not globally install a write-capable connector to make a report work. Planning and local definitions do not authorize account access, sending events/customer data, scheduling, publishing or advertising spend.

## Organize a reviewable campaign

Keep journey hooks, event contract, asset inventory, sales process, creative/landing-page versions and attribution decisions in the campaign context. Use stable IDs plus a readable naming convention; never use names alone as joins. Each test has a question, expected outcome, denominator, attribution/maturity window, affordable acquisition cost, maximum authorized spend, review date and stop/continue/scale criteria. Broad three-platform capability does not mean every project should launch all three.

Separate platform pacing settings from the owner's total spending ceiling: Google's average daily budget is not a hard daily cap (up to twice the daily amount; monthly limit 30.4 times it). The repo has no live spend controller, automatic pause or scheduler.

## Monitor the whole sales path

Only after connection/scheduling authorization:

- **Daily health:** data freshness, delivery/disapprovals, spend/pacing, broken destinations, event loss, duplicates, consent regressions, expired permissions, CRM handoff failures. Missing data is unknown, not zero.
- **Weekly review:** comparable mature windows; explain metric definitions and denominators; separate clicks, leads, qualified leads, customers and contribution. Propose bounded changes with evidence, budget impact and rollback criteria.
- **Mature cohorts:** source to qualified customer, revenue, acquisition cost, payback and retention. Never sum platform-attributed conversions as unique customers; use holdouts when feasible before attributing causal lift.

The installed presets give campaign-level aggregates only; they do not join CRM records or retrieve creative/search-term diagnostics. Approval of a task is not launch authority.

### Attribution composition and changes in definitions

Before a performance or scaling recommendation record the conversion action, counting method, attribution model and windows with their effective dates. Never sum nested windows or overlapping columns. For Meta, the March 2026 change moved non-link interactions into engage-through attribution: verify the account's rollout and split the series before claiming improvement. Pixel/CAPI deduplication fixes duplicate delivery; it does not establish causal value.

## Sources and review date

Checked 2026-10-24 unless noted. A shared ChatGPT discussion was idea input only, not evidence or authorization.

- [Google Ads MCP](https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server); [developer-token sunset](https://developers.google.com/google-ads/api/docs/api-policy/developer-token); [deprecations](https://developers.google.com/google-ads/api/docs/deprecations); [budget behavior](https://support.google.com/google-ads/answer/6385083?hl=en); [Consent Mode](https://developers.google.com/tag-platform/security/concepts/consent-mode).
- [Meta Ads MCP tools](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-tools-ad-creation-and-management) and [setup](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-get-started/?locale=en_US); [Graph API changelog](https://developers.facebook.com/docs/graph-api/changelog/) (2026-10-31); [deduplication](https://developers.facebook.com/documentation/ads-commerce/conversions-api/deduplicate-pixel-and-server-events.md); [attribution announcement](https://about.fb.com/ltam/news/2026/03/simplificando-la-medicion-de-anuncios-para-un-mundo-social-first/) (2026-03-03).
- [Postiz MCP](https://docs.postiz.com/mcp/introduction), [public API](https://docs.postiz.com/public-api/introduction), [Docker Compose install](https://docs.postiz.com/self-host/installation/docker-compose) (2026-10-31).
- [Claude Code MCP permission rules](https://code.claude.com/docs/en/permissions) (2026-10-31).
- [TikTok API for Business](https://business-api.tiktok.com/portal/docs/api-reference/v2.0); [TikTok event deduplication](https://ads.tiktok.com/help/article/event-deduplication?lang=en) (May 2025).
