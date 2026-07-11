# Evidence Scout Agent Implementation Plan

## Objective

Build a portable evidence-scout skill/agent for Codex, OpenCode, and Claude Code that helps founders validate whether real users have a painful problem, whether demand exists, and where early adopters gather.

The agent must not act as a cheerleader. It must challenge weak assumptions, separate evidence from interpretation, and identify supporting evidence, counter-evidence, risks, and low-cost validation tests.

## Core Constraint

Start by validating APIs with scripts. Do not rely on MCPs as the execution layer.

MCPs may be used as inspiration for source coverage, schemas, and workflow design, but the implementation must call provider APIs directly from scripts so it works across Codex, OpenCode, Claude Code, CI, and normal terminals.

## What To Reuse From Existing Work

Reuse the strong parts of the identified skills and MCP-style projects:

- `customer-discovery-coach`: hypothesis framing across Customer, Problem, and Solution; risk-ranked hypothesis stack; Mom Test interview discipline.
- `grill-me` / `grill-hard`: relentless one-question-at-a-time interrogation; pushback when assumptions are vague, circular, or overconfident.
- `reddit-pain-point-scanner`: complaint clustering, urgency/frequency scoring, workaround detection, opportunity gap scoring, and verbatim evidence capture.
- `trends-agent-market-research` / TrendsMCP: source taxonomy and demand-signal categories across Google Search, YouTube, TikTok, Reddit, Amazon, App Store, Google Shopping, news, and app downloads.
- Firecrawl-style workflows: search -> scrape -> map -> crawl -> extract, but implemented through direct API scripts rather than MCP tool calls.
- `mvanhorn/last30days-skill`: multi-harness Skill packaging, "agent resolves where to search before searching" behavior, engagement-aware multi-source ranking, configurable recency windows, source degradation when keys are missing, and raw artifact output for auditability.
- `mvanhorn/cli-printing-press`: agent-first CLI ergonomics, offline/cache-friendly outputs, and compound commands that produce useful summaries without requiring a model-specific runtime.
- `mvanhorn/agentcookie`: relevant only as a future optional path for user-approved authenticated browser sessions. It is not a v1 dependency because this project should validate official APIs and paid providers first.

Key product distinction from `last30days`: Evidence Scout is not a general recency brief. It is a demand-validation and opportunity-discovery workflow. It must formulate hypotheses, search for user pain and counter-evidence, identify reachable early adopters, and propose low-cost risk-reduction tests.

## Required Data Sources

### Tier 1: Must Support First

These sources provide the highest signal-to-effort ratio for business idea validation.

| Source | Evidence Type | Access Method | Notes |
|---|---|---|---|
| Reddit | complaints, workarounds, repeated questions, community discovery | Reddit API, public JSON endpoints where allowed, paid fallback via Apify/Bright Data | Best source for raw pain language and early adopter communities. |
| Google Trends | search interest, seasonality, geography, related queries | SerpAPI Google Trends API, DataForSEO Google Trends API, optional pytrends fallback | Demand proxy only. Never treat as proof of willingness to pay. |
| YouTube | video topics, comments, creator narratives, tutorial gaps | YouTube Data API v3 | Good for creator-led niches and "how do I fix X" behavior. |
| Search/Web/Forums | community discovery and niche forums | Firecrawl API, SerpAPI/Google Search API, direct site crawlers where allowed | Used to identify where the audience actually talks. |
| App Store / Google Play Reviews | product gaps, complaints about existing solutions | Apple App Store Connect API for owned apps; Google Play Developer API for owned apps; third-party providers for arbitrary competitor apps | Official APIs are limited for competitor review mining. |

### Tier 2: Support After Tier 1 Works

| Source | Evidence Type | Access Method | Notes |
|---|---|---|---|
| X | fast-moving professional complaints, operators, founders, experts | X API, paid data provider fallback | Cost and access may change. Validate before committing. |
| TikTok | trend language, hashtags, consumer behavior, comments | TikTok Research API if eligible; Apify/Bright Data fallback | Official access can be limited and research-gated. |
| Instagram | creator comments, visual consumer niches, brand complaints | Meta Graph API for owned/permitted assets; paid public-data provider fallback | Arbitrary public content access is constrained. |
| Facebook Pages/Groups | local/community needs, hobby groups, parenting/health/local service pain | Meta Graph API for public pages and owned assets; explicit user-provided exports for private groups | Do not scrape private groups without permission. |
| Amazon / Google Shopping | review pain, purchase intent, category demand | SerpAPI, DataForSEO, Bright Data, Apify | Useful for product categories and physical goods. |
| News / Blogs | category momentum and expert framing | SerpAPI, Firecrawl API, NewsAPI/GDELT optional | Supporting context, not primary user pain. |

## API Validation Phase

The first implementation phase must build scripts that answer: "Can we access enough useful data, legally and reliably, at acceptable cost?"

Create `scripts/validate_apis/` with one script per provider. Each script must:

- Load credentials from environment variables, with optional local loading from `~/.secrets` if the user has configured it.
- Run one low-cost test query.
- Write raw JSON to `research/evidence-scout/api-validation/<provider>.json`.
- Write a normalized summary to `research/evidence-scout/api-validation/<provider>.summary.json`.
- Report access status: `ok`, `missing_credentials`, `permission_denied`, `account_verification_required`, `billing_required`, `rate_limited`, `unsupported`, `network_blocked_or_sandboxed`, or `failed`.
- Record estimated cost, quota headers if available, and data fields returned.
- Avoid storing secrets in outputs.

### Validation Scripts

Implement in this order:

1. `validate_serpapi_google_trends.py`
   - Env: `SERPAPI_API_KEY`
   - Query: 2-3 problem keywords and one competitor/category keyword.
   - Validate: interest over time, related queries, region breakdown.

2. `validate_dataforseo_google_trends.py`
   - Env: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`
   - Same query shape as SerpAPI.
   - Validate whether DataForSEO is a better cost/reliability option.

3. `validate_reddit.py`
   - Env: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, optional `REDDIT_USERNAME`, `REDDIT_PASSWORD`.
   - Query: subreddit search, post search, comments for one thread.
   - Validate public read access and rate limits.

4. `validate_youtube.py`
   - Env: `YOUTUBE_API_KEY`
   - Query: video search for a problem keyword, fetch comments for top videos.
   - Validate quota cost and comment availability.

5. `validate_firecrawl.py`
   - Env: `FIRECRAWL_API_KEY_HGINVESTOR` (canonical account; do not fall back to a generic Firecrawl key)
   - Query: search for forums around a topic, scrape one result.
   - Validate search quality, scrape quality, and cost.

6. `validate_brave_search.py`
   - Env: `BRAVE_SEARCH_API_KEY`
   - Query: search for forums and complaint-language pages around a topic.
   - Validate source discovery quality as a low-friction fallback to Firecrawl search.

7. `validate_x.py`
   - Env: `X_BEARER_TOKEN`
   - Query: recent search for complaint-language keywords.
   - Validate plan access and whether returned fields are sufficient.

8. `validate_tiktok.py`
   - Env: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, or provider-specific credentials.
   - First try official Research API if eligible.
   - If not eligible, validate Apify/Bright Data actor/API fallback.

9. `validate_meta.py`
   - Env: `META_ACCESS_TOKEN`
   - Validate Instagram/Facebook page access only where the token has permission.
   - Do not assume arbitrary public scraping is available through official Meta APIs.

10. `validate_app_reviews.py`
   - Env: Apple/Google credentials if owned apps exist.
   - Validate Google Play Developer API for owned apps.
   - Validate third-party provider for arbitrary competitor review extraction.

11. `validate_apify.py`
    - Env: `APIFY_TOKEN`
    - Test one low-cost Actor for Reddit/TikTok/Instagram/YouTube or app reviews.
    - Record dataset schema and per-run cost.

12. `validate_scrapecreators.py`
    - Env: `SCRAPE_CREATORS_API_KEY`
    - Validate credit/account access and document coverage for TikTok, Instagram, YouTube, X/Twitter, Reddit, Threads, LinkedIn, Facebook, Pinterest, Bluesky, and related endpoints.
    - Prefer as a pragmatic paid social-data fallback when official APIs are gated or too limited.

13. `validate_brightdata.py`
    - Env: `BRIGHTDATA_SELENIUM_URL`, `BRIGHTDATA_BROWSER_WS_URL`, or `BRIGHTDATA_API_KEY`
    - Prefer validating the Browser API Selenium `/status` endpoint when the user has Browser API credentials.
    - Treat pasted Browser API URLs as secrets and rotate them before storing.
    - Validate only if the use case needs high-volume, browser-rendered, or hard-to-access sources.

## Implementation Phases

### Phase 1: API Validation Harness

Deliverables:

- `scripts/validate_apis/*.py`
- `research/evidence-scout/api-validation/` output folder
- `docs/api-access-matrix.md`
- `config/providers.example.json`

Acceptance criteria:

- At least Google Trends, Reddit, YouTube, and Firecrawl/API search are validated.
- Each provider has a clear status and failure reason.
- The plan recommends a default provider stack based on actual API test results, not assumptions.

### Phase 2: Evidence Schema and Normalization

Create a normalized evidence model:

```json
{
  "source": "reddit|youtube|google_trends|forum|x|tiktok|instagram|facebook|app_review|amazon|news",
  "source_url": "...",
  "retrieved_at": "ISO-8601",
  "query": "...",
  "customer_segment": "...",
  "hypothesis_id": "...",
  "evidence_type": "pain|workaround|switching_cost|spend|search_demand|counter_evidence|community|competitor_gap",
  "text": "...",
  "verbatim_quote": "...",
  "author_context": "...",
  "engagement": {
    "upvotes": null,
    "comments": null,
    "views": null,
    "likes": null
  },
  "strength": "strong|medium|weak",
  "confidence_notes": "..."
}
```

Rules:

- Keep raw provider responses for auditability.
- Store normalized JSONL separately.
- Never paraphrase away the user's language; preserve verbatim quotes when allowed.
- Deduplicate near-identical posts and reposted content.
- Mark platform limitations explicitly.

Current implementation:

- `scripts/evidence_scout/collect.py` collects normalized JSONL from validated Reddit and Firecrawl access.
- Outputs default to a durable `research/topics/<topic-slug>/` workspace with a manifest, canvases, and stage-specific run folders. Use `--legacy-output` only for compatibility.
- Each run writes raw redacted provider responses, `evidence.jsonl`, `summary.json`, and `report.md`.
- The collector accepts `--days`, following the useful recency-window pattern from `last30days`, but does not hardcode "last 30 days".

### Phase 3: Source Discovery Engine

Build scripts that identify where to search before collecting evidence.

Inputs:

- Topic
- Target customer segment
- Geography/language
- B2B/B2C
- Known competitors
- Problem keywords
- Workaround keywords

Discovery outputs:

- Candidate subreddits
- Forums and communities
- YouTube channels/videos
- TikTok hashtags/search terms
- X search queries
- Instagram/Facebook public pages where accessible
- Review sites and app/product pages
- Google Trends keyword set

Discovery query patterns:

- `"I hate" + problem`
- `"how do you deal with" + problem`
- `"alternative to" + competitor`
- `"best way to" + job`
- `"why is it so hard to" + job`
- `"site:reddit.com/r/ keyword"`
- `"site:forum.* keyword"`
- `"site:youtube.com keyword tutorial problem"`

### Phase 4: Evidence Collection

Implement provider adapters:

- `providers/reddit.py`
- `providers/google_trends.py`
- `providers/youtube.py`
- `providers/web_search.py`
- `providers/firecrawl.py`
- `providers/brave_search.py`
- `providers/x.py`
- `providers/tiktok.py`
- `providers/meta.py`
- `providers/app_reviews.py`
- `providers/apify.py`
- `providers/brightdata.py`

Each adapter must expose:

- `validate_credentials()`
- `discover(query, options)`
- `collect(target, options)`
- `normalize(raw_record)`
- `estimate_cost(plan)`

### Phase 5: Evidence Analysis

Use the reused frameworks:

- Complaint clustering from `reddit-pain-point-scanner`.
- Hypothesis risk ranking from `customer-discovery-coach`.
- Search-demand comparison from TrendsMCP-style source categories.
- One-question-at-a-time challenge discipline from `grill-me`.

Scoring model:

| Dimension | Meaning |
|---|---|
| Frequency | How often distinct users mention it. |
| Urgency | Emotional intensity, time loss, money loss, operational pain. |
| Workaround | Whether users already spend effort or money to solve it. |
| Solution gap | Whether current tools fail, are too expensive, or are hard to use. |
| Search demand | Whether people actively search for the problem/category. |
| Counter-evidence | Evidence that the problem is solved, niche, or low priority. |
| Reachability | Whether early adopters can be found and contacted ethically. |

Evidence strength rules:

- `strong`: repeated independent pain + workaround/spend + recent evidence + reachable community.
- `medium`: repeated pain but unclear urgency, buyer, or willingness to pay.
- `weak`: trend/search interest only, likes/views only, isolated complaint, or founder interpretation.
- `negative`: users say the problem is solved, low priority, not worth paying for, or not their job.

### Phase 6: Agent/Skill Packaging

Create five portable skills:

1. `idea-grill`
   - Interviews the user relentlessly.
   - Extracts target customer, problem, current workaround, buyer/user split, and hypotheses.

2. `evidence-scout`
   - Discovers sources.
   - Runs script-based data collection.
   - Produces supporting evidence, counter-evidence, and early adopter communities.

3. `opportunity-risk-designer`
   - Turns evidence into opportunity areas.
   - Ranks risks.
   - Designs low-cost validation tests and outreach targets.

4. `competitor-scout`
   - Discovers direct, indirect, substitute, and future-threat competitors.
   - Separates real solution providers from directories, blogs, marketplaces, agencies, and false positives.
   - Produces a competitor-array style view with segment fit, job fit, key success-factor gaps, evidence quality, and source URLs.

5. `competitor-marketing-analyzer`
   - Analyzes competitor positioning, audiences, offers, CTAs, pricing posture, proof points, SEO/content clues, distribution clues, and product-change clues.
   - Supports optional deep scraping of common pricing, features, customer, blog, docs, integrations, and changelog paths when worth the credits.
   - Treats competitor copy as positioning evidence, not proof of performance.

For portability:

- Codex: package each as a `SKILL.md` folder with references and scripts.
- Claude Code: package as Claude-compatible skill bundles or instructions.
- OpenCode: expose as Markdown agent prompts plus callable scripts.
- Keep all executable logic in scripts, not platform-specific tool calls.

## Default Provider Recommendation

Start with this default stack:

1. Google Trends: SerpAPI first, DataForSEO second, pytrends fallback.
2. Reddit: official API first, Apify/Bright Data fallback.
3. YouTube: official YouTube Data API.
4. Web/forums: Firecrawl API and search API scripts.
5. TikTok/Instagram/Facebook/X: validate official API eligibility first; otherwise use Apify or Bright Data if legally and economically acceptable.
6. App/product reviews: official owned-app APIs where possible; third-party providers for competitor reviews.

## Secrets Handling

Do not hardcode credentials.

Credential lookup order:

1. Environment variables.
2. Optional local `~/.secrets` files, read only by validation scripts.
3. Interactive prompt only if running manually.

Never print full credentials. Validation summaries may show only masked key fingerprints, e.g. `sk_...abcd`.

## Deliverables Checklist

- [x] API validation scripts.
- [x] Provider access matrix.
- [x] Normalized evidence schema.
- [ ] Source discovery engine.
- [ ] Provider adapters.
- [ ] Evidence scorer and clusterer.
- [x] Portable `idea-grill` skill.
- [x] Portable `evidence-scout` skill.
- [x] Portable `opportunity-risk-designer` skill.
- [x] Portable `competitor-scout` skill.
- [x] Portable `competitor-marketing-analyzer` skill.
- [x] Example end-to-end run on one business idea.
- [ ] Cost and compliance notes for every enabled provider.

Implementation status:

- [x] API validators created for Reddit, Google Trends providers, YouTube, Firecrawl, Brave Search, X, TikTok, Meta, app reviews, Apify, and Bright Data.
- [x] Reddit access validated with existing credentials.
- [x] Firecrawl access validated with existing credentials.
- [x] SerpAPI Google Trends access validated.
- [x] YouTube Data API access validated.
- [x] Brave Search access validated.
- [x] X API bearer token validated, but sample query returned zero tweets.
- [x] Apify account access validated.
- [ ] DataForSEO credentials are present but permission denied.
- [x] Bright Data REST API key is permission denied; Browser API/Selenium validation works with local secret configuration.
- [ ] TikTok official, Meta, and app-review providers need credentials if they are in scope.
- [x] ScrapeCreators access validated.
- [x] First collection script implemented for Reddit and Firecrawl.
- [x] Competitor discovery script implemented with Brave Search and Firecrawl search.
- [x] Competitor marketing analysis script implemented with Firecrawl scrape and optional deep page discovery.
- [x] Example run completed for `project management for freelancers`, producing 8 normalized records and a report.

## Open Decisions

- Whether to use SerpAPI or DataForSEO as the default Google Trends provider.
- Whether Reddit official API access is sufficient for the expected research volume.
- Whether the user has TikTok Research API eligibility.
- Whether paid providers like Apify or Bright Data are acceptable for Instagram/TikTok/Facebook/X.
- Whether competitor app/product reviews are in scope for the first version.
