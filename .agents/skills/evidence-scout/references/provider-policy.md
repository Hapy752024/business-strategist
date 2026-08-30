# Provider Policy — Evidence Scout

Full provider routing rules for evidence collection. The root `AGENTS.md` carries only the durable policy bullets; this reference has the operational detail.

## Default Providers

Default providers: Reddit, SerpAPI Google Trends, YouTube Data API, Serper.dev Google SERP, Firecrawl, Brave Search, plus the zero-credential set HN Algolia (`hn`), GitHub issue search (`github`), and Google autocomplete (`google_autocomplete`) included in `default`. iTunes review RSS (`itunes_reviews`) is free but explicit (needs `--itunes-app-ids`).

Use Serper.dev before SerpApi for ordinary Google-only SERP/news/site-search because it is cheaper and sufficient for standard discovery. Keep SerpApi for non-Google engines and deep Google edge-case parsers. Use DataForSEO for SEO/backlink/search-volume, historical SERP, app/e-commerce datasets, and Trends-style data where that specific API is the right source.

## Zero-Credential Sources

These cost nothing, need no keys, and are part of `default` runs:

- `hn` — HN Algolia search over stories and comments. Strongest for founder/operator, dev-tool, B2B, and tech-adjacent pain language. Tech-skewed; do not generalize to non-technical consumers.
- `github` — public issue search. Reaches developer-audience tooling gaps and workaround chains; issue text is bug-shaped, not buyer-shaped. Anonymous rate is ~10 search requests/min; a no-scope `GITHUB_TOKEN` raises it to ~30/min.
- `google_autocomplete` — real user query phrasing around problem seeds. Language proxy only, never volume or intent strength.
- `itunes_reviews` — public App Store customer-review RSS per app/storefront. Free alternative to paid Sonar for competitor review mining; requires `--itunes-app-ids` and is therefore opt-in. Public reviews only; revenue estimates still need Sonar.

Use `--providers free_community` to run just the three zero-credential collectors without spending any paid credits.

## YouTube Transcripts

`collect.py --youtube-transcripts` fetches transcripts for the top `--youtube-transcript-max` videos (default 5) via `youtube_transcript_api` — free, no API key or quota. Records use source `youtube_transcript`; per-video fetch statuses (`ok`, `disabled`, `unavailable`, `blocked`, `missing_module`) land in `raw/youtube.json` and `summary.json` under `transcripts`.

- Transcripts are **creator voice**, not customer voice. Mine them for quoted user stories, mentioned workarounds, and linked products — never as demand proof. Customer pain on YouTube still comes primarily from comments.
- Keep `--youtube-transcript-max` low: YouTube IP-throttles transcript requests (`blocked` status means throttled from this IP, not that transcripts are unavailable everywhere).
- `validate_youtube.py` reports `transcript_status` so `run_all.py` stays the runtime truth for transcript access too.

## Agent Reach (optional capability layer)

[Agent Reach](https://github.com/Panniantong/Agent-Reach) is an external CLI that maintains live-probed backend routes per platform (YouTube transcripts via yt-dlp, web reading via Jina Reader, Bilibili, XHS, Twitter/X, Reddit via login state). `provider_doctor.py` already probes `agent-reach doctor --json` as candidate backends for `reddit`, `china_public_native` (bilibili), and `china_social` (xiaohongshu) — installing it lights those routes up automatically.

Install (user-initiated): `pip install agent-reach && agent-reach install --env=auto` then `agent-reach doctor --json`. Cookie/login-state channels carry account-ban risk — treat them like `china_social`: use burner accounts and get explicit user approval before any collection run through them. Never route a default run through a cookie-backed channel.

## Social Providers

Firecrawl always uses `FIRECRAWL_API_KEY_HGINVESTOR`; do not silently fall back to another Firecrawl account.

## Social Providers

Social providers: direct X API, optional Grok/xAI X Search discovery, and ScrapeCreators.

Use direct X API as the default source-of-record route for recent public X/Twitter posts. Use Grok/xAI X Search only as cited discovery/synthesis and verify cited post URLs before treating claims as evidence. Use ScrapeCreators X profile/user-tweet pulls only for named-handle enrichment or fallback; use Apify only for capped bulk/historical actor-backed gaps after actor/schema review.

ScrapeCreators is valuable for public TikTok, Instagram, Threads, Facebook, X/Twitter, Reddit, YouTube, LinkedIn, Pinterest, and Bluesky evidence, but it spends credits (1 credit per call observed).

ScrapeCreators Facebook/Instagram routes (verified 2026-07-21):

- `--fb-groups <url-or-id,...>`: public Facebook group posts (3 posts/call, cursor-paginated up to `--fb-max-posts`, default 12, hard cap 60). **Public groups only.** An empty response means the group is private OR inactive — report "no accessible public posts", never "no posts exist".
- `--fb-pages <url-or-id,...>`: public page posts + reels (same pagination).
- `--ig-handles <handle,...>`: Instagram profile posts (`/v2/instagram/user/posts`).
- `--ig-hashtags <tag,...>`: Instagram hashtag search (`/v1/instagram/search/hashtag`, 10 posts/call).
- `--social-comments`: also fetch comments on the top `--comments-max` (default 5) collected FB/IG posts. Pain language often lives in comments; treat comments as interview leads unless repeated.
- `--social-per-endpoint` (default 10) caps records per endpoint so one productive platform cannot starve the others.

## Ads Intelligence Providers

Competitor paid-ads evidence uses `scripts/evidence_scout/collect_ads.py`, not `collect.py`:

- `meta_ad_library` (default, free): official Meta Ad Library API. Requires one-time Meta developer app + government ID verification and `META_ACCESS_TOKEN` with `ads_read` scope; tokens expire ~60 days. Commercial ads only for EU/UK/EEA audiences (DSA, ~1-year retention); coarse spend/impression ranges; no engagement metrics. Ad longevity is a judgment signal, not performance proof.
- `apify_ads` (paid fallback, `approval_required`): for non-EU/UK/EEA markets or a missing/expired Meta token. The script hard-requires `--approve-paid` as a deterministic spend gate; ask the user first. Use `--providers auto` to let the script route (Meta primary, Apify on non-EU countries or token failure).

## Provider Sets

- `default`: Reddit, SerpAPI Google Trends, YouTube Data API, Firecrawl, Brave Search, HN Algolia (`hn`), GitHub issues (`github`), Google autocomplete (`google_autocomplete`).
- `free_community`: only the zero-credential collectors — `hn`, `github`, `google_autocomplete`. Zero cost; use for cheap first passes.
- `social`: direct X API and ScrapeCreators. Grok/xAI X Search is explicit only via `xai_x_search`.
- `local_web`: crawl4ai local page extraction after lightweight URL discovery.
- `china_public`: Bilibili public search with Serper/Brave/Firecrawl site-search fallback, V2EX topic search/public fallback, and China web/domain search.
- `china_social`: XiaoHongShu through OpenCLI/browser-session access. Requires explicit approval because it is login/cookie-backed.
- `china`: `china_public` plus `china_social`.
- `all`: default plus social.
- Explicit: comma-separated provider names.

Use `default` first. Add `social` only when consumer, creator, trend, local community, or brand-comment evidence is material enough to spend paid credits.

## Firecrawl, Local Extraction, and Fallback Routing

- Firecrawl always uses `FIRECRAWL_API_KEY_HGINVESTOR`; do not silently fall back to another Firecrawl account.
- Use `crawl4ai` before heavier hard-page fallbacks when local extraction can reduce Firecrawl credit spend. Keep `--local-extract-url-limit` low and treat output as page evidence.
- Use `markitdown` only with explicit `--document-paths`; it is for supplied PDFs, Office files, local HTML, CSV/JSON/XML, and other documents, not broad web discovery.
- Use `scrapling` only after normal providers or crawl4ai are insufficient for a concrete source; do not add it to default runs.
- Treat `scripts/validate_apis/run_all.py` as runtime truth for whether a provider currently works. `provider_doctor.py` may route families, but environment variables alone are not proof that an API endpoint is usable.

## China Coverage

China public providers: Bilibili public search with Serper/Brave/Firecrawl site-search fallback, explicit Bilibili comment enrichment, V2EX public/search fallback, and Chinese web/domain search across Zhihu, Weibo, Douban, Tieba, 36Kr, Huxiu, and XiaoHongShu public pages via Serper/Firecrawl/Brave when available.

China social providers: XiaoHongShu via OpenCLI/browser-session access. This is login/cookie-backed and must be explicitly approved before running.

Do not treat China-source zero results as absence of demand unless the provider doctor shows a topic-search backend was actually available. `china_public_native` is optional native coverage; `china_public_search` is the practical fallback for Bilibili/V2EX topic discovery. V2EX public hot is a limited fallback, not a topic-complete search.

Use `china_bilibili_comments` only as explicit enrichment after relevant Bilibili videos are found. Treat comments as interview leads unless repeated independent comments show pain, urgency, workaround, or spend language.

Chinese platform likes, views, saves, danmu/comment counts, and reposts are weak engagement context unless paired with repeated pain, decision uncertainty, workaround, or spend language.

## Sonar / App-Store Enrichment

Sonar is valuable for app-store keyword demand, app reviews, competitor app context, and revenue estimates, but it spends credits. Ask the user before running it unless they explicitly requested Sonar.

## Competitor Monitoring (Separate Skill)

Similarweb-style traffic actors are useful for web-first competitor monitoring, but traffic estimates and bounce rates are not proof of churn or demand.

Google Maps actors are useful for local/physical markets, restaurants, retail, clinics, hospitality, property, and REIT-style research, but ratings and review counts are context unless repeated review text shows real pain.

Do not use stock sentiment or Stocktwits actors for general market research unless the target segment is explicitly active traders, investors, or trading/investment-product users.

## Weak Evidence Rules

- Google Trends is a search-demand proxy only. It is never proof of willingness to pay.
- Likes, views, and comments are weak evidence unless paired with repeated pain, urgency, and workaround/spend.
- Do not treat China-source zero results as absence of demand unless the provider doctor shows a topic-search backend was actually available.

## Provider Failure Reporting

If a provider fails because of missing credentials, no credits, permission denied, rate limit, unsupported endpoint, or a generic failure, tell the user clearly before interpreting the evidence.

If capability lookup or provider validation reports `rate_limited`, `missing_credentials`, `missing_cli`, `billing_required`, `insufficient_credits`, `permission_denied`, `unsupported`, or `failed`, record the fallback and confidence impact before synthesis. Do not interpret an unavailable provider as absence of demand.

Always check `summary.json.needs_user_attention` and the Provider Alerts section in `report.md`.

## Insufficient Credits Protocol (paid providers)

When a paid provider (ScrapeCreators, Apify, Sonar, DataForSEO, Bright Data) reports `insufficient_credits` or `billing_required` — in validation output, `summary.json.needs_user_attention`, or `report.md` Provider Alerts — do NOT silently continue:

1. **Pause and notify the user.** Name the provider, the current balance if reported (`credits_remaining_at_start`), and what coverage is lost (e.g. Instagram/Facebook/TikTok evidence).
2. **Ask exactly one question:** "Add credits/top up, or continue without this source?"
3. **If the user says credits were added:** rerun `python3 scripts/validate_apis/run_all.py` (or the single validator, e.g. `validate_scrapecreators.py`) to confirm the balance, then rerun the collection for that provider before interpreting evidence.
4. **If the user says continue without it:** record the source as unavailable in the run notes, lower confidence for any claim that needed it, and never treat the missing source as absence of demand.

ScrapeCreators specifics: `collect_scrapecreators` does a free pre-flight credit-balance check before any paid call and aborts mid-run if credits exhaust (remaining endpoints are marked `skipped:insufficient_credits`), so a depleted balance can never silently look like "no evidence found". Top up at https://app.scrapecreators.com/.

## Source Priority Order

Prefer sources in this order:

1. Reddit for complaints, workarounds, repeated questions, and communities.
2. SerpAPI Google Trends for search-demand proxy (weak evidence).
3. YouTube official API for videos and comments.
4. Firecrawl and Brave Search for forums, niche communities, and source discovery.
5. crawl4ai for local LLM-ready page extraction after URL discovery.
6. MarkItDown for explicit document ingestion from local files or supplied URLs.
7. Scrapling for explicit hard-page extraction fallback.
8. Direct X API for recent public text evidence.
9. Grok/xAI X Search for cited discovery over X (model-mediated; verify cited posts).
10. ScrapeCreators for public social platform fallback evidence.
11. Sonar for app-store enrichment (user-approved only).
12. China public sources for China-specific markets.
13. China social sources (XiaoHongShu) only after explicit approval.
14. Apify for actor-specific fallback after actor/schema review.
15. Bright Data only for high-volume or hard-source work after permission issues are resolved.

## Competitor Discovery Policy

- Competitor search results are only candidates. Classify false positives explicitly.
- Use competitor discovery as a competitor-array exercise: direct competitors, indirect competitors, substitutes, future threats, key success factors, evidence quality, and source URLs.
- Marketing analysis must preserve sources and distinguish positioning claims from proof of performance.
