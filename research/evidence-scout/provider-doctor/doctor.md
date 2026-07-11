# Evidence Scout Provider Doctor

- Generated at: 2026-07-10T07:07:55Z

## Source Families

### reddit

- Status: `ok`
- Active backend: `reddit_api`
- Candidates:
  - `reddit_api`: `ok` (api, risk: `normal`) - Latest live validator `reddit` returned `ok`; HTTP 200
  - `agent_reach_reddit`: `missing_cli` (cli, risk: `login_or_cookie_backed`) - `agent-reach` is not installed
  - `scrapecreators_reddit`: `ok` (api, risk: `paid_credits`) - Latest live validator `scrapecreators` returned `ok`; HTTP 200

### google_trends

- Status: `unavailable`
- Active backend: `none`
- Candidates:
  - `serpapi_google_trends`: `rate_limited` (api, risk: `paid_or_quota_limited`) - Latest live validator `serpapi_google_trends` returned `rate_limited`; HTTP 429
  - `dataforseo_google_trends`: `network_blocked_or_sandboxed` (api, risk: `paid_credits`) - Latest live validator `dataforseo_google_trends` returned `network_blocked_or_sandboxed`

### web_search

- Status: `ok`
- Active backend: `serper_search`
- Candidates:
  - `serper_search`: `ok` (api, risk: `paid_credits_google_only`) - Latest live validator `serper` returned `ok`; HTTP 200
  - `firecrawl_search`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `firecrawl` returned `ok`; HTTP 200
  - `brave_search`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `brave_search` returned `ok`; HTTP 200

### local_extraction

- Status: `optional_unavailable`
- Active backend: `none`
- Candidates:
  - `crawl4ai_cli`: `missing_cli` (cli, risk: `local_optional`) - Latest live validator `crawl4ai` returned `missing_cli`
  - `markitdown_cli`: `missing_cli` (cli, risk: `local_optional`) - Latest live validator `markitdown` returned `missing_cli`
  - `scrapling_cli`: `missing_cli` (cli, risk: `explicit_hard_page_fallback`) - Latest live validator `scrapling` returned `missing_cli`

### youtube

- Status: `ok`
- Active backend: `youtube_data_api`
- Candidates:
  - `youtube_data_api`: `ok` (api, risk: `normal`) - Latest live validator `youtube` returned `ok`; HTTP 200
  - `scrapecreators_youtube`: `ok` (api, risk: `paid_credits`) - Latest live validator `scrapecreators` returned `ok`; HTTP 200
  - `yt_dlp_cli`: `missing_cli` (cli, risk: `normal`) - `yt-dlp` is not on PATH

### social

- Status: `ok`
- Active backend: `x_api`
- Candidates:
  - `x_api`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `x` returned `ok`; HTTP 200
  - `xai_x_search`: `ok` (api, risk: `model_tool_costs`) - Latest live validator `xai_x_search` returned `ok`; HTTP 200
  - `scrapecreators_social`: `ok` (api, risk: `paid_credits`) - Latest live validator `scrapecreators` returned `ok`; HTTP 200

### app_store

- Status: `ok`
- Active backend: `sonar`
- Candidates:
  - `sonar`: `ok` (api, risk: `paid_credits`) - Latest live validator `sonar` returned `ok`; HTTP 200

### china_public_native

- Status: `ok`
- Active backend: `v2ex_public_hot`
- Candidates:
  - `bilibili_public_search`: `failed` (public_http, risk: `normal`) - Public HTTP probe failed: 412
  - `v2ex_public_hot`: `ok` (public_http, risk: `normal`) - Public HTTP probe succeeded
  - `agent_reach_bilibili`: `missing_cli` (cli, risk: `login_or_cookie_backed`) - `agent-reach` is not installed

### china_public_search

- Status: `ok`
- Active backend: `serper_bilibili_v2ex_site_search`
- Candidates:
  - `serper_bilibili_v2ex_site_search`: `ok` (api, risk: `paid_credits_google_only`) - Latest live validator `serper` returned `ok`; HTTP 200
  - `brave_bilibili_v2ex_site_search`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `brave_search` returned `ok`; HTTP 200
  - `firecrawl_bilibili_v2ex_site_search`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `firecrawl` returned `ok`; HTTP 200

### china_social

- Status: `ok`
- Active backend: `scrapecreators_china_social`
- Candidates:
  - `agent_reach_xiaohongshu`: `missing_cli` (cli, risk: `login_or_cookie_backed`) - `agent-reach` is not installed
  - `scrapecreators_china_social`: `ok` (api, risk: `paid_credits`) - Latest live validator `scrapecreators` returned `ok`; HTTP 200

### china_web

- Status: `ok`
- Active backend: `serper_china_web`
- Candidates:
  - `serper_china_web`: `ok` (api, risk: `paid_credits_google_only`) - Latest live validator `serper` returned `ok`; HTTP 200
  - `firecrawl_china_web`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `firecrawl` returned `ok`; HTTP 200
  - `brave_china_web`: `ok` (api, risk: `paid_or_quota_limited`) - Latest live validator `brave_search` returned `ok`; HTTP 200

## Needs User Attention

- `google_trends` has no usable backend. Configure one candidate or avoid interpreting this source family.
