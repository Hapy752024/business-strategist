---
name: evidence-scout
description: Search script-accessible web, forum, Google Trends, YouTube, Reddit, X, and paid social fallback sources for real user pain, demand signals, counter-evidence, and reachable early adopter communities for a business idea.
---

# Evidence Scout Workflow

Use this skill after `idea-grill` has produced a clear topic, customer segment, and hypothesis.

After collecting and auditing evidence for a consumer service, route to `service-customer-perspective-challenger` to test the idea, package, trust design, and message through evidence-grounded buying contexts. Keep its simulated customer voice out of `evidence.jsonl`; only real sourced statements and behavior are evidence.

## Ambiguity and Unknowns

If ambiguity materially changes provider choice, query wording, geography, language, or interpretation, ask one focused clarification question before spending meaningful API or scraping credits. If the answer is not available from user input, local files, provider output, or cited sources, say "I don't know" and state what evidence is missing. Do not fill gaps with plausible-sounding claims.

## Procedure

1. Confirm the topic, customer segment, geography/language, hypothesis, and likely pain/workaround terms.
2. Verify the documented scripts exist, run capability lookup for the research need, and validate API access before collection.
3. Choose provider set from capability lookup: default first, social or paid enrichment only when justified or approved.
4. Translate solution-led language into user pain, workaround, comparison, and search-intent terms.
5. Run the collector with scoped topic, segment, problem keywords, workaround keywords, hypothesis ID, date range, limit, and providers.
6. Inspect `research_plan.md`, `summary.json`, `report.md`, `evidence.jsonl`, raw provider outputs, and provider alerts.
7. Exclude irrelevant records and verify the strongest records materially match topic, geography, pain, and segment.
8. Separate evidence, interpretation, counter-evidence, missing evidence, source intent, and comment intent.
9. Report the truth about evidence strength, provider gaps, unresolved risks, and next low-cost tests.

## Execution Rule

Use scripts, not MCPs, as the execution layer.

Before running commands, verify that the documented script paths exist. If `scripts/` is missing but a recovered/staged copy exists elsewhere in the repository, restore it to the documented path before running. If scripts cannot be found, stop and report that the evidence workflow is unavailable; do not silently replace the scripted workflow with ad hoc web browsing.

Start by validating APIs:

```bash
python3 scripts/validate_apis/run_all.py
```

Then make source routing explicit and token-efficient:

```bash
python3 scripts/capability_lookup.py --question "<research need>" --compact
```

Use the lookup before substantial research, source enrichment, app-store work, China coverage, document ingestion, or paid fallbacks. It reads `config/source-capabilities.json` and the latest live validation output. If a selected capability is `degraded`, `unavailable`, `failed`, or `not_checked`, state the coverage impact and fallback before synthesis.

When setup/routing matters, especially for China sources or fallback selection, run the provider doctor:

```bash
python3 scripts/evidence_scout/provider_doctor.py --json
```

It writes `research/evidence-scout/provider-doctor/doctor.summary.json` and `doctor.md`. Inspect `source_families.*.active_backend` and `needs_user_attention` before interpreting source coverage. The doctor consumes the latest live API validation summary when available; credentials alone are not proof that a provider is usable.

If any requested or important provider reports `missing_credentials`, `billing_required`, `permission_denied`, `rate_limited`, `unsupported`, or `failed`, notify the user before interpreting the evidence. Explain which source was unavailable, why it matters, and how to fix or bypass it. Do not bury API failures in the final caveats.

Then collect evidence with currently available providers:

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain phrase 1>,<pain phrase 2>" --workaround-keywords "<workaround 1>,<workaround 2>" --hypothesis-id H1 --days 30 --limit 20 --providers default
```

The collector writes `research_plan.md` before provider calls. Inspect it before interpreting results. It should state assumptions, provider plan, query strategy, Google Trends preview terms, a query sample, and the planned single-question user checkpoint.

Provider sets:

- `default`: Reddit, SerpAPI Google Trends, YouTube Data API, Firecrawl, Brave Search.
- `social`: direct X API and ScrapeCreators. Grok/xAI X Search is explicit only via `xai_x_search`.
- `local_web`: crawl4ai local page extraction after lightweight URL discovery.
- `china_public`: Bilibili public search with Serper/Brave/Firecrawl site-search fallback, V2EX topic search/public fallback, and China web/domain search.
- `china_social`: XiaoHongShu through OpenCLI/browser-session access. Requires explicit approval because it is login/cookie-backed.
- `china`: `china_public` plus `china_social`.
- `all`: default plus social.
- Explicit: comma-separated provider names such as `reddit,youtube,crawl4ai,markitdown,scrapling,x,xai_x_search,scrapecreators,sonar,china_bilibili,china_bilibili_comments,china_v2ex,china_web,china_xiaohongshu`.

Use `default` first. Add `social` only when consumer, creator, trend, local community, or brand-comment evidence is material enough to spend paid credits.

Use local extraction only when it adds concrete coverage:

- `crawl4ai`: use as the first local fallback when Firecrawl scrape credits are constrained or when richer page Markdown is needed from a small discovered URL set. Keep `--local-extract-url-limit` low.
- `markitdown`: use only with explicit `--document-paths` for PDFs, Office files, CSV/JSON/XML, local HTML, images/OCR-capable installs, or other supplied evidence documents.
- `scrapling`: use only as an explicit hard-page fallback when normal HTTP/API/Firecrawl/crawl4ai extraction cannot reach or parse a page. Do not include it in default runs.

For China-market, Chinese-language, or Chinese-platform evidence, add `china_public` only when the target segment plausibly uses Chinese platforms or the user requested China coverage. Use `--geo CN --language zh` unless the market is explicitly overseas Chinese or bilingual. Treat Bilibili metadata, V2EX hot topics, and China web/domain search as discovery/context unless the record contains direct complaint, decision uncertainty, workaround, or spend language. For Google-indexed site-search, prefer Serper.dev first; use SerpApi/DataForSEO only when Serper's Google-only coverage is not enough.

Use `china_bilibili_comments` only as explicit enrichment after Bilibili video results look relevant. It fetches a capped set of public comments from selected videos. Treat comments as interview leads unless repeated independent comments show pain, urgency, workaround, or spend language.

Ask the user exactly one question before running `china_social`:

`Do you want login-backed China social enrichment via XiaoHongShu/OpenCLI? It may require browser session/cookies and should use a non-primary account.`

If the user says yes, run with explicit `--providers china_social` or `--providers default,china_public,china_social`. If the source fails with `missing_cli` or `login_required_or_failed`, report that China social coverage is missing before interpreting the evidence.

For app-store or mobile-app markets, ask the user exactly one question before running paid app-market enrichment:

`Do you want app-store enrichment via Sonar for keyword demand, app reviews, and competitor app context?`

If the user says yes, rerun or extend collection with explicit `--providers default,sonar`. If known competitor app IDs are available, pass them with `--sonar-apps ios:<app_id>,android:<package_name>`. Treat Sonar keyword metrics as weak search-demand context and Sonar revenue estimates as weak monetization context. Treat Sonar app reviews as app-review evidence, but remember store reviews are biased toward existing app users.

Do not add `enrichment` or `competitor_monitoring` as `--providers` aliases. Enrichment is a user checkpoint; competitor monitoring belongs to the separate `competitor-monitoring` skill.

For local, physical-location, retail, restaurant, clinic, hospitality, property, or REIT-style markets, ask one question before running Google Maps-style enrichment:

`Is physical-location evidence important enough to run Google Maps enrichment for ratings, review counts, review text, locations, and popular-times context?`

If the user says yes, use the separate `competitor-monitoring` skill with the `compass/crawler-google-places` actor rather than adding it to the default Evidence Scout provider set. Treat Google Maps ratings, review volume, and occupancy as market context. Treat repeated review complaints across independent locations as possible local pain evidence, not proof of willingness to pay.

If the topic is written as a solution, translate it into user language before collecting evidence. Example: do not only search "AI client status reporting assistant"; also search phrases like "client updates", "status reports", "client communication", "project tracking", "scattered email", and "manual follow up".

Search terms must reflect how the target segment would actually search, complain, compare, or ask for help. Do not use the full `--customer-segment` value as a keyword. The segment is for scoping evidence and judging fit, not for Google Trends or social queries.

For solution-led topics, include a separate problem-first query set. For German insurance, include terms like `PKV Entscheidung`, `PKV wechseln`, `BU Gesundheitsfragen`, `anonyme Risikovoranfrage`, `Makler Provision Vertrauen`, and `Honorarberater Versicherung` before solution phrases like `digital insurance advice`.

For German PKV/BU research, expand Reddit coverage beyond `r/Finanzen` when available. Include source-pack queries for `r/Versicherung`, `r/Krankenkassen`, `r/beamte`, and `r/germany`, and keep German forum/source discovery in the web providers. Do not treat narrow Reddit coverage as evidence that there is no community pain.

If `--problem-keywords` or `--workaround-keywords` are missing, infer likely terms before running. Use the topic, customer segment, geography/language, trigger event, alternatives, competitors, and current workaround if available. Ask the user for keywords only when inference would be low-confidence, the segment could use very different vocabulary, or paid social/scraping credits would be spent.

Use `--geo AUTO --language AUTO` unless the user specifies geography/language. Germany-specific topics must run Google Trends and search providers with German geography (`DE`) and German language (`de`), and must preserve both German umlaut and ASCII variants such as `Rückkehr in GKV` / `Rueckkehr in GKV` and `Berufsunfähigkeit` / `Berufsunfaehigkeit`. If a Germany-specific run produces `geo=US` or long English segment prose in Google Trends terms, mark the run invalid and rerun before interpretation.

Separate irrelevant results from weak evidence. Irrelevant records must be written to `irrelevant.jsonl` and excluded from pain/community/competitor-gap counts. A high-engagement unrelated Reddit post is still irrelevant; do not upgrade it to medium evidence because of comments or upvotes. Before summarizing, inspect the top records and verify that each one materially matches the topic, problem/workaround keywords, and geography.

For each source type:

- Google Trends: use short search-intent phrases, category names, pain terms, comparison terms, workaround terms, and competitor names. Never use long segment prose.
- Reddit/forums/web search: use pain/workaround phrases plus short natural qualifiers only when users would type them, such as `expats Germany`, `freelancers`, `parents`, or a named community.
- YouTube: use explainer/tutorial/review-style phrases that users would search to learn the topic.
- Direct X API and paid social: use compact phrases, hashtags, competitor names, and complaint language. Avoid demographic sentences; social platforms rarely match those well. Use `xai_x_search` only when semantic/cited discovery over X is materially better than direct search.
- Local extractors: normalize only capped excerpts into `evidence.jsonl`; inspect `raw/` before treating extracted pages or documents as direct user evidence.

## Sources

Prefer sources in this order:

- Reddit for complaints, workarounds, repeated questions, and communities.
- SerpAPI Google Trends for search-demand proxy. Treat it as weak evidence.
- YouTube official API for videos and comments.
- Firecrawl and Brave Search for forums, niche communities, and source discovery.
- crawl4ai for local LLM-ready page extraction after URL discovery when Firecrawl credits or extraction coverage are limiting.
- MarkItDown for explicit document ingestion from local files or supplied URLs.
- Scrapling for explicit hard-page extraction fallback; avoid by default because browser/stealth scraping is heavier and more fragile.
- Direct X API for recent public text evidence when the query is likely to match.
- Grok/xAI X Search for cited discovery over X when investor/operator/customer discussion is likely but direct keyword search may miss threads, handles, or multimedia posts. Treat output as model-mediated leads; inspect cited posts before using claims.
- ScrapeCreators for public TikTok, Instagram, Threads, YouTube, Facebook, X/Twitter profile/user-tweet fallback, Reddit, LinkedIn, Pinterest, and Bluesky fallback evidence.
- Sonar for app-store keyword demand, app reviews, competitor app context, and revenue estimates when the user approves app-market enrichment.
- China public sources for China-specific markets: Bilibili for video/creator discussion, optional Bilibili comments for direct user-comment leads, V2EX for developer/tech community signals, and Chinese web/domain search across Zhihu, Weibo, Douban, Tieba, 36Kr, Huxiu, and XiaoHongShu public pages.
- China social sources such as XiaoHongShu only after explicit approval, because browser-session/cookie-backed collection is fragile and can risk account restriction.
- Apify for actor-specific fallback after choosing an actor/schema. For local/physical-location enrichment, use `compass/crawler-google-places` through `competitor-monitoring` after user approval. For recurring competitor monitoring and traffic estimates such as `tri_angle/fast-similarweb-scraper`, use the separate `competitor-monitoring` skill rather than this evidence collection flow.
- Bright Data only for high-volume or hard-source work after permission issues are resolved.

Do not use stock-trading sentiment actors such as Reddit ticker sentiment or Stocktwits sentiment for general business-idea validation. They are not customer pain evidence unless the target segment is explicitly active traders, investors, or users of trading/investment products.

## Quality Gates

Before interpreting the run, check:

- `summary.json.needs_user_attention`.
- `scripts/capability_lookup.py --question "<research need>" --compact` output for the selected source route.
- Provider Alerts in `report.md`.
- Provider doctor `needs_user_attention` when run, especially `china_public_search`, `china_web`, and `china_social`. `china_public_native` can be unavailable while site-search fallbacks still provide limited public-source discovery.
- Whether Germany-specific runs used `geo=DE` and German/Germany-specific language.
- Whether China-specific runs used `geo=CN` and `language=zh`, unless the user explicitly requested overseas/bilingual evidence.
- Whether `irrelevant.jsonl` exists when irrelevant results were found.
- Whether the strongest records are genuinely relevant, not merely high engagement.
- Whether provider status means only API success or actually usable evidence.
- Whether `active_backend` indicates a full topic-search route or a limited fallback such as V2EX public hot.
- Whether the run has direct user-pain records, not only provider/editorial/competitor content.
- Whether `summary.json.quality_flags` warns about zero Reddit/forum pain, weak Trends signals, or mostly competitor/editorial evidence.
- Whether `summary.json.quality_flags` warns about mostly weak records, low direct user-pain share, or many `unknown` source-intent records.
- Whether paths in `summary.json.outputs` exist. If `.evidence-scout/...` and `research/evidence-scout/...` differ, inspect the path that exists and report the mismatch as a workflow issue.
- Whether `research_plan.md`, `assumptions.md`, and `user_review_plan.md` exist. These are part of the flow, not optional notes.

If any quality gate fails, say so before interpreting the evidence. Do not describe a run as healthy just because provider status is `ok`.

## Analysis Rules

Separate:

- Evidence: what users actually said or did.
- Interpretation: what the agent thinks it means.
- Counter-evidence: signs the problem is solved, not urgent, too niche, or not monetizable.
- Missing evidence: places not yet searched because credentials or access are missing.
- Irrelevant records: source results that do not materially match the topic, pain, workaround, or target geography.
- Source intent: distinguish `user_pain` from `official_provider`, `editorial_content`, `competitor_content`, `social_comment`, and `search_demand`.
- Comment intent: for Reddit, YouTube comments, X, and paid social, inspect `comment_intent` counts such as `decision_question`, `complaint`, `provider_question`, `provider_praise`, `social_context`, and `offtopic`. Treat comments as interview leads unless they show repeated pain and urgency.

For German insurance records, classify decision uncertainty before generic spend. Posts about `PKV oder GKV`, `Rückkehr/Rueckkehr`, `Gesundheitsfragen`, `Risikovoranfrage`, tariff choice, or being `überfragt` are decision/pain evidence even if they mention `€`, `Beiträge`, `Provision`, or `Zuschlag`. Generic money words alone are not enough to infer willingness to pay.

Never claim demand from views, likes, search volume, or one complaint alone. Demand requires repeated pain, urgency, workaround/spend, and a reachable segment.

Evidence strength:

- `strong`: repeated independent pain plus workaround/spend plus a reachable community.
- `medium`: repeated pain but weak urgency, buyer, or willingness-to-pay signal.
- `weak`: search interest, likes/views, isolated complaints, generic blog content, or founder interpretation.

The collector writes:

- `research/topics/<topic>/evidence/runs/<run>/raw/`
- `research/topics/<topic>/evidence/runs/<run>/evidence.jsonl`
- `research/topics/<topic>/evidence/runs/<run>/summary.json`
- `research/topics/<topic>/evidence/runs/<run>/report.md`

Use `--legacy-output` only when a downstream consumer still requires the former global layout.

Always inspect `summary.json.needs_user_attention` and the Provider Alerts section in `report.md`. If either is non-empty, include those alerts in the response to the user.

## User Interaction

When involving the user, ask exactly one question at a time. Start with the highest-leverage unresolved assumption or the strongest evidence item. Where relevant, include a recommendation for the next or extended research step, but do not bundle multiple questions in one message.

When improving this skill or the collector, run:

```bash
python3 scripts/evidence_scout/test_classification.py
```

The fixture tests cover German PKV/BU decision uncertainty, social source intent, comment intent, quality flags, known-competitor lookup noise, and marketing extraction edge cases.

## Output

Report:

- Provider access status.
- API failures, missing credits, permission errors, or missing keys that reduced source coverage.
- Sources searched and why.
- Strongest supporting evidence.
- Strongest counter-evidence.
- Candidate early-adopter communities.
- Key risks still unresolved.
- Next low-cost tests.

When summarizing results, lead with the truth:

- If evidence is weak, say it is weak.
- If evidence supports a different segment than the user proposed, say so.
- If source access failed or was not run to avoid cost, name the gap.

## Quality Checklist

Before finalizing, check:

- API validation and requested provider statuses are reported.
- `summary.json.needs_user_attention` and Provider Alerts were inspected.
- `research_plan.md`, `assumptions.md`, and `user_review_plan.md` exist or their absence is disclosed.
- Query terms reflect user language, not long segment prose.
- Geography/language settings match the market being researched.
- Irrelevant records are excluded rather than counted as weak support.
- Strongest records show actual user behavior or pain, not only content volume.
- Google Trends, likes, views, and comments are treated as weak signals unless paired with pain and workaround/spend.
- Evidence, interpretation, counter-evidence, and missing evidence are separated.
- The recommended next step reduces the riskiest unresolved assumption.
