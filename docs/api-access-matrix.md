# API Access Matrix

This file tracks the intended evidence sources, direct script access paths, and fallback choices. Runtime truth comes from `research/evidence-scout/api-validation/*.summary.json`.

| Evidence Source | Primary Script | Required Env | API / Provider URL | Fallback | Current Status |
|---|---|---|---|---|---|
| Google Trends | `validate_serpapi_google_trends.py` | `SERPAPI_API_KEY` | https://serpapi.com/google-trends-api | DataForSEO, pytrends | OK |
| Google Trends | `validate_dataforseo_google_trends.py` | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | https://docs.dataforseo.com/v3/keywords_data/google_trends/overview/ | SerpAPI, pytrends | Permission denied |
| Reddit | `validate_reddit.py` | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | https://www.reddit.com/dev/api/ | Apify, Bright Data | OK |
| YouTube | `validate_youtube.py` | `YOUTUBE_API_KEY` | https://developers.google.com/youtube/v3/getting-started | SerpAPI YouTube APIs, ScrapeCreators | OK |
| Forums/Web | `validate_firecrawl.py` | `FIRECRAWL_API_KEY_HGINVESTOR` | https://docs.firecrawl.dev/api-reference/introduction | SerpAPI/Google Search, direct crawl | OK |
| Forums/Web Search | `validate_brave_search.py` | `BRAVE_SEARCH_API_KEY` | https://api-dashboard.search.brave.com/app/documentation/web-search/get-started | Firecrawl, SerpAPI/Google Search | OK |
| X | `validate_x.py` | `X_BEARER_TOKEN` | https://docs.x.com/x-api/introduction | Apify, Bright Data | OK, zero-result test query |
| TikTok | `validate_tiktok.py` | `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` | https://developers.tiktok.com/doc/research-api-get-started | Apify, Bright Data | Missing credentials |
| Instagram/Facebook | `validate_meta.py` | `META_ACCESS_TOKEN` | https://developers.facebook.com/docs/graph-api/ | Apify, Bright Data, explicit exports | Missing credentials |
| ScrapeCreators social fallback | `validate_scrapecreators.py` | `SCRAPE_CREATORS_API_KEY` | https://docs.scrapecreators.com/ | Apify, Bright Data, direct APIs | OK |
| App reviews | `validate_app_reviews.py` | Google/Apple app credentials | https://developers.google.com/android-publisher/reply-to-reviews | Apify, SerpAPI, Bright Data | Missing credentials |
| App-store enrichment / ASO | `validate_sonar.py` | `SONAR_API_KEY` | https://trysonar.app/docs/api | Apify app-store actors, owned app APIs | OK |
| Provider/backend doctor | `scripts/evidence_scout/provider_doctor.py` | varies by backend | local env/CLI/public probes | ordered provider fallbacks | Added |
| China public: Bilibili | `collect.py --providers china_bilibili` | none for public search | https://api.bilibili.com/x/web-interface/search/type | Agent Reach / bili-cli, Firecrawl/Brave domain search | Optional, network-dependent |
| China public: V2EX | `collect.py --providers china_v2ex` | `BRAVE_SEARCH_API_KEY` or `FIRECRAWL_API_KEY_HGINVESTOR` for topic search; none for public hot fallback | https://www.v2ex.com/api/topics/hot.json | Brave/Firecrawl site search, Agent Reach | Optional |
| China web/domain search | `collect.py --providers china_web` | `FIRECRAWL_API_KEY_HGINVESTOR` or `BRAVE_SEARCH_API_KEY` | Firecrawl/Brave search | Apify/Bright Data/custom actors | Optional |
| China social: XiaoHongShu | `collect.py --providers china_xiaohongshu` | `opencli` browser-session setup | OpenCLI / browser session | Agent Reach, paid social scrapers | Explicit approval only |
| Competitor web traffic estimates | `validate_apify.py` then actor smoke test | `APIFY_TOKEN` | https://apify.com/tri_angle/fast-similarweb-scraper | Similarweb alternatives, SEO tools | Optional monitoring only |
| Local / physical-location market context | `validate_apify.py` then actor smoke test | `APIFY_TOKEN` | https://apify.com/compass/crawler-google-places | Google Places API, local directories | Optional local-market enrichment only |
| Apify fallback | `validate_apify.py` | `APIFY_TOKEN` | https://docs.apify.com/api/v2 | Bright Data | OK |
| Bright Data fallback | `validate_brightdata.py` | `BRIGHTDATA_SELENIUM_URL` or `BRIGHTDATA_BROWSER_WS_URL` or `BRIGHTDATA_API_KEY` | https://docs.brightdata.com/ | Apify, ScrapeCreators, direct APIs | OK via Browser API/Selenium |

## Credential Setup

Preferred setup is environment variables:

```bash
export SERPAPI_API_KEY='...'
export REDDIT_CLIENT_ID='...'
export REDDIT_CLIENT_SECRET='...'
export YOUTUBE_API_KEY='...'
export FIRECRAWL_API_KEY_HGINVESTOR='...'
export SCRAPE_CREATORS_API_KEY='...'
export SONAR_API_KEY='aso_...'
export BRIGHTDATA_SELENIUM_URL='https://USER:PASS@HOST:9515'
export BRIGHTDATA_BROWSER_WS_URL='wss://USER:PASS@HOST:9222'
```

The scripts also read `~/.secrets` if it contains simple `KEY=VALUE` or `export KEY=VALUE` lines.

## Validation Commands

Run all validators:

```bash
python3 scripts/validate_apis/run_all.py
```

Check active backend routes:

```bash
python3 scripts/evidence_scout/provider_doctor.py --json
```

Run one validator with a custom query:

```bash
python3 scripts/validate_apis/validate_serpapi_google_trends.py --query='meal planning,meal prep,healthy eating'
```

## Interpretation

Statuses:

- `ok`: credentials and endpoint worked.
- `missing_credentials`: key not found in env or `~/.secrets`.
- `permission_denied`: key exists but lacks access or is invalid.
- `account_verification_required`: credentials are valid enough to reach the provider, but the provider requires account verification before API use.
- `rate_limited`: account is over quota.
- `billing_required`: key exists, but the account plan, billing status, or monthly free quota blocks access.
- `unsupported`: endpoint/resource unavailable for this account or use case.
- `missing_cli`: an optional CLI/backend such as `opencli`, `yt-dlp`, or `agent-reach` is not installed or not on PATH.
- `login_required_or_failed`: a browser-session/cookie-backed source did not return usable records; verify login state and account restrictions before relying on coverage.
- `warn`: the provider ran through a limited fallback route. Inspect `active_backend` before interpreting zero results.
- `network_blocked_or_sandboxed`: the provider could not be reached from the current execution environment; this is not proof that credentials are bad.
- `failed`: network, provider, or unexpected error.

Treat social media access as unstable. If official access fails for TikTok, Instagram, Facebook, or X, validate Apify or Bright Data next before changing the product scope.

## Current Local Validation Snapshot

The last local validation found:

- Reddit: `ok` with existing `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`.
- Firecrawl: `ok` using the existing Firecrawl key alias.
- Brave Search: key found, but access returned a billing/plan error.
- Google Trends: SerpAPI works; DataForSEO credentials are present but denied.
- YouTube: official YouTube API key works.
- Brave Search: works after billing/quota update.
- X: bearer token works, but the low-cost validation query returned zero tweets.
- Apify: account API works.
- Sonar: API key works for the low-cost keyword suggestions endpoint.
- ScrapeCreators: works.
- Bright Data: REST API key was denied on the account balance endpoint. Browser API/Selenium validation works through `BRIGHTDATA_SELENIUM_URL`; `BRIGHTDATA_BROWSER_WS_URL` is validated for URL shape and reserved for Playwright/Puppeteer integration.
- TikTok official, Meta, app reviews: no usable credentials found.

Add new keys to environment variables or to `~/.secrets`, then rerun:

```bash
python3 scripts/validate_apis/run_all.py
```

Do not paste Bright Data URLs with embedded credentials into prompts or committed files. Rotate pasted credentials, then put the new URL in `~/.secrets`.
