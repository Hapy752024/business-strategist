# Digital-Marketing Optimization Plan — The Six-Layer Search Stack

Status: plan, compiled 2026-09-19 from seven sourced research reports (web research, sources with dates at the end of each section).
Framework source: James Dooley, "Modern Search Optimisation Stack" (x.com/james_dooley/status/2100907455890800881, 2026-09-18).

## 0. Framework and honest caveats

Discovery has fragmented: a buyer may find a brand on TikTok, research it on Google, compare it via ChatGPT, check Reddit, and ask an AI assistant to decide. The stack:

- **SEO** — be found (crawled → indexed → ranked → clicked)
- **SMO** — be discovered and discussed (parallel social/community layer)
- **AEO** — be the answer (extractable answers: snippets, PAA, AI Overviews)
- **GEO** — be understood, mentioned and cited by generative systems
- **DEO** — be evaluated, recommended and chosen by AI agents (emergent term)
- **SXO** — convert that visibility into customers on owned interfaces

Shared foundation: **entities + content + data + authority + trust**. One presence performing across six environments, not six separate strategies.

Evidence honesty rules for everything below:

- DEO as a named discipline was coined 2026-09-03 in a press release; the term is emergent, but its mechanics (agentic commerce protocols, machine-readable attributes) are real and shipped (OpenAI/Stripe ACP 2025-09-29, Google UCP 2026-01-11).
- Schema markup shows **no causal AI-citation lift** in controlled testing (Ahrefs, 1,885 pages, May 2026) — keep it for entity clarity and rich results, never promise citations from it.
- `llms.txt` has ~zero measured impact (0.1% of AI-bot visits, OtterlyAI 90-day experiment; Google says it is unused) — near-zero priority.
- Vendor conversion/citation percentages are directional (small, US/English-skewed samples). Controlled studies (Princeton KDD 2024, Ahrefs, Google/Deloitte, Baymard) are the strongest evidence.

## 1. The strongest cross-layer findings (what actually moves the needle)

1. **Off-site brand mentions dominate AI visibility**: web mentions correlate 0.664 with AI Overview visibility vs 0.218 for backlinks; YouTube mentions are the single strongest signal (0.737). 82–89% of AI citations come from earned media, not owned sites; ~1% from brand-owned sites. (Ahrefs 75k-brand study Aug/Dec 2025; Muck Rack Dec 2025/May 2026.)
2. **On-page levers that replicate**: adding citations, statistics and expert quotations lifts generative visibility up to ~40% (Princeton KDD 2024); answer-first structure (40–60-word capsules) beats length (word-count correlation 0.04, Ahrefs 174k pages); freshness matters (AI-cited URLs ~25% fresher; ~50% of citations under 13 weeks old).
3. **AI-referred traffic converts 4–9x organic** (Seer Jun 2025: ChatGPT 15.9% vs 1.76% organic; Adobe Q1 2026: +42% vs non-AI). SXO for AI arrivals is high-value: the landing page must continue the recommendation the AI made.
4. **Measurement is the cheapest gap to close**: AI citation share, AI-referral analytics, mention velocity and crawler access are all programmatically measurable today; nothing in this repo measures any of them.
5. **Platform rules define the automation boundary**: Reddit pre-approval + 90/10 rule (Nov 2025 Responsible Builder Policy), Meta browser-automation bans, LinkedIn ToS — autonomous community posting is prohibited; the compliant pattern is agent-as-research-assistant, human posts.

## 2. Per-layer program: what the agent does vs. what the owner must do

Every skill output that touches these layers must end with a structured **Owner actions** block (see §3.4): action, layer, cadence, effort, evidence payoff. Missing owner inputs stay pending — same discipline as the website launch contract.

### 2.1 SEO (foundation layer)

**Agent-executable (end-to-end or with deploy gate):**
- Technical audits: crawlability, indexation, canonicals, redirect chains, orphan pages (Screaming Frog headless / open crawlers / GSC URL Inspection API).
- Keyword research, intent clustering, SERP/PAA analysis → prioritized content backlog (Ahrefs/Semrush/DataForSEO APIs, Serper, autocomplete).
- Schema generation + validation (attribute-rich Article/Organization/Product), internal-link proposals, content briefs, freshness-decay detection via GSC API, rank/impression pipelines, CWV measurement + code fixes with Lighthouse CI gates.

**Owner actions (non-delegable):**
- Approve every published content change (Google's scaled-content enforcement — March 2026 update caused 50–80% traffic drops at mass-AI publishers — makes unreviewed publishing the single biggest agentic SEO risk).
- Supply authentic E-E-A-T inputs: real credentials, firsthand experience, proprietary data.
- Digital PR and link earning: journalist relationships, expert commentary. Agent prepares prospect lists and drafts pitches; owner sends/authorizes (domain reputation + spam-law compliance).
- Cadence example: approve/publish **1 substantive content piece per week**; quarterly technical-audit review; monthly GSC review.

### 2.2 SMO (discovery/authority layer)

**Agent-executable:**
- Profile/entity consistency audit across platforms (handles, bios, descriptions) with drafted fixes.
- Social listening + own-brand mention monitoring, sentiment, share of voice (licensed APIs only — never ToS-violating scraping).
- Cross-platform repurposing (one pillar asset → platform-native derivatives), caption/keyword drafting, scheduling queues (publish via official APIs after owner authorization).
- Reddit/forum opportunity surfacing: find high-intent threads that rank on Google/feed AI answers, draft disclosed replies.

**Owner actions:**
- **Authentic posting is non-delegable**: founder/employee voice (own-words posts outperform pre-written shares ~9x; founder storytelling is the top B2B trust signal in 2026). Cadence example: **1 founder post per week** on the primary platform; agent provides the topic queue from listening data.
- Community participation (Reddit/Discord/forums): human posts from genuine aged accounts; agent only researches and drafts.
- Podcast/YouTube appearances — the strongest single GEO correlate (0.737) is YouTube mentions; creator outreach is human relationship work, agent prepares targets and drafts.
- UGC incentive/legal design (contest rules, rights contracts).

### 2.3 AEO (answer extraction)

**Agent-executable:**
- Question mining at scale: PAA harvesting (AlsoAsked/SerpWow/HasData APIs), GSC question-regex pulls (`^(who|what|...)`), Reddit/Quora phrasing — output: clustered question→URL map.
- Answer-first restructuring drafts: 40–60-word answer capsules after question-shaped H2/H3, comparison tables, HowTo steps, self-contained passages.
- FAQPage/HowTo/Article/Speakable schema generation + validation; freshness flags per page-type cadence (comparisons 60–90 days, evergreen ~6 months).
- Snippet/PAA ownership tracking via SERP APIs; Bing Webmaster Tools AI Performance (only first-party AI citation feed).

**Owner actions:**
- **SME fact-check of every extractable fact** — definitions, prices, stats, comparison rows. Answer engines cross-verify; a confident wrong capsule propagates verbatim. This review is the gate, not a formality.

### 2.4 GEO (AI citations)

**Agent-executable:**
- **AI visibility probe harness** (buildable today, replaces $29–499/mo tools): 15–30 fixed buyer-intent prompts run monthly against ChatGPT/Perplexity/Gemini/Claude APIs + AI Overviews; log mention/citation/sentiment/competitors; trend over ≥12 weeks (answers are stochastic; single runs mislead).
- AI-crawler policy audit: robots.txt training-vs-retrieval split (mainstream 2026 config: block GPTBot/ClaudeBot/CCBot/Google-Extended training crawlers, allow OAI-SearchBot/ChatGPT-User/PerplexityBot retrieval bots — they are independent infrastructures); detect CDN-level blocks (Cloudflare blocks AI crawlers by default since Jul 2025); verify via server-log user-agent analysis.
- Entity-consistency audit + corrections (site schema `sameAs`, LinkedIn, Crunchbase, G2, directories); Wikidata entry creation/maintenance (lower notability bar than Wikipedia).
- Competitive citation analysis: run competitor brands through the same prompt panels; map which sources earn their citations → gap list.
- GA4 AI-referrer channel group (chatgpt.com, perplexity.ai, claude.ai, gemini.google.com, copilot.microsoft.com — the native GA4 AI channel misses Perplexity and dark traffic).

**Owner actions:**
- Digital PR / earned media (84% of AI citations): data-driven PR campaigns, expert quotes with real credentials (agent cannot invent them), journalist relationships. Cadence: **1 original-insight or data asset per month/quarter** feeding PR.
- Authentic Reddit/Quora participation (as in SMO).
- Wikipedia notability is earned through 6–12 months of coverage — never force an article.
- Strategic decision: block or allow AI *training* crawlers (IP trade-off; blocking all AI crawlers correlates with −23% visits, Rutgers/Wharton Dec 2025). Agent executes, owner decides.

### 2.5 DEO (machine-comparable, decision-ready)

**Agent-executable (~70% of the layer is mechanical):**
- Product/Offer JSON-LD with identifiers (GTIN/MPN/SKU/brand), price, availability, aggregateRating; Organization-level `MerchantReturnPolicy` + `OfferShippingDetails` — encoded only from owner-confirmed facts (inaccurate structured data is penalized harder than absent).
- Plain-HTML pricing/comparison pages (view-source test; JS-rendered pricing makes ChatGPT fall back to G2).
- Feed generation: Google Merchant Center feed → OpenAI product-feed transform (9 required fields, 15-min push cadence); UCP attribute mapping.
- Discovery files: robots.txt AI rules, `/.well-known/api-catalog`, MCP commerce server scaffolding where a real backend API exists (low proven value today, cheap to do).
- Decision-stage measurement: shortlist/selection prompts ("which X under €300 with A and B") tracked separately from educational prompts.

**Owner actions:**
- Platform approvals: OpenAI merchant application, Merchant Center/UCP onboarding, Google Business Profile verification — identity-gated, human-only.
- **Truth inputs**: real prices, stock, return windows, guarantees, cancellation terms — legal/commercial commitments the owner sets; the agent only encodes them.
- Reputation footprint: G2/Capterra/Trustpilot reviews come from real customers (99% of ChatGPT-recommended tools had G2 reviews) — agent audits presence and drafts review-request campaigns; owner approves and delivers a product worth reviewing. Fake reviews = fraud, never an option.
- Local/service businesses: a sub-30-second phone script for Google's agentic "Have AI check pricing" calls.

### 2.6 SXO (conversion on owned interfaces) — already strongest in this repo

Existing coverage: launch contract (26 checks), Lighthouse budgets, experimentation route, consent-compliant analytics, conversion-first content rules. Incremental additions only:

**Agent-executable additions:**
- Message-match audit: map GSC queries / ads / AI-citation contexts to landing pages, flag mismatches, draft intent-matched hero variants (AI arrivals must see the recommendation confirmed immediately).
- CrUX field-data collection automation (field CWV is currently honestly "unknown" in our launch evidence).
- Scheduled funnel-drop review loop connecting PostHog/GA4 data back into site iteration.
- Form/checkout friction fixes (multi-step forms, wallet buttons, field reduction) with Playwright E2E purchase tests.

**Owner actions:**
- Experiment launch and winner promotion stay human-approved (revenue risk).
- Pricing/guarantee/certification wording — legal sign-off.
- Consent architecture decisions.

## 3. Agent-setup changes (concrete)

### 3.1 Extend `competitor-monitoring` → add an own-brand visibility lane
Reuses its watchlist/snapshot/diff machinery — cheapest high-value move.
- New script `scripts/monitoring/ai_answer_probe.py`: fixed prompt panel × LLM APIs → normalized rows `(engine, query, brand_mentioned, url_cited, sentiment, competitors_cited)` → `evidence.jsonl` + diff reports, evidence-scout output conventions (`raw/`, `summary.json`, `report.md` under a run folder).
- New script `scripts/monitoring/brand_mentions.py`: own-brand mention watch (licensed listening APIs, Reddit search, Serper) with sentiment and source classification (earned/owned/paid).
- Follow the community-review signed-gate pattern if probing needs authorization controls.

### 3.2 Extend `brand-website-designer-builder` references
- `references/aeo-geo-visibility.md`: question-mining workflow, answer-capsule patterns, evidence-injection rules (citations/statistics/quotes), freshness cadences, AI-citation measurement protocol, schema honesty note (no citation-lift promises), llms.txt deprioritized.
- `references/deo-agent-readiness.md`: machine-comparable attribute checklist per page type, feed/protocol landscape with platform-approval gates marked as owner actions, decision-stage prompt measurement.
- Update `references/seo-performance.md` to point at both (it currently carries the only AEO/GEO paragraph).
- Optional (deferred decision): new launch-contract check `structured_data_coverage` — requires contract revision + legacy manifests adding it as `pending`, like the 2026-09-19 `https_enforcement`/`spam_protection`/`broken_links` revision.

### 3.3 New validation script
- `scripts/brand/check_structured_data.py` (mirrors `check_lighthouse.py`): parse a crawl/report, fail on missing Product/Offer/FAQ/Organization markup per page type and on markup/visible-text mismatches (prices, ratings).

### 3.4 Owner-action output contract (the cross-cutting addition)
- Convention: every strategy/planning/audit output in scope (`marketing-strategy-builder`, `social-digital-marketing-planner`, the new monitoring reports, website audits) ends with an **Owner actions** section, one row per action: `action | layer (SEO/SMO/AEO/GEO/DEO/SXO) | cadence (weekly/monthly/quarterly/one-off) | effort | expected evidence payoff | status (pending/done)`.
- Persist per project as `owner-actions.md` next to the run/plan; unresolved owner actions stay `pending` and are re-surfaced on resume — same pattern as launch-contract pending checks and `contact_address` owner confirmation.
- Example rows the skills should generate: "Publish 1 founder post/week on LinkedIn from the listening-driven topic queue (SMO→GEO corroboration)"; "Record 30-second price/availability phone script and train staff (DEO local)"; "Provide real return-window terms for schema encoding (DEO)"; "Fact-check 12 answer capsules drafted for /pricing and /compare (AEO)".

### 3.5 Routing and catalog
- `config/workflow-routes.json`: add match terms — `competitor-monitoring` absorbs "brand mentions", "social listening", "AI citation tracking"; `website-build` absorbs "AEO", "answer engine", "structured data audit", "agent readiness" (already has "GEO audit").
- If the monitoring lane grows into a standalone skill (`search-visibility-monitor`), add route + `config/skill-catalog.json` entry together — `scripts/validate_skill_routes.py` enforces parity.
- Pain-gate: measurement for an existing site is execution/monitoring (no gate); using findings to reshape marketing strategy stays behind the existing `requires_pain_gate` pattern.

## 4. Sequencing

1. **Phase 1 — measurement first** (pure agent work, no site changes): AI-answer probe harness, GA4 AI-referrer channel, brand-mention monitoring, question-mining script, AI-crawler/robots audit. Output: baseline visibility report + first owner-actions list.
2. **Phase 2 — on-site levers**: `aeo-geo-visibility.md` applied to existing pages (answer capsules, evidence injection, freshness program), `check_structured_data.py` in CI, message-match audit for AI arrivals.
3. **Phase 3 — off-site authority** (owner-heavy): digital-PR workflow with agent-prepared prospecting, founder-content cadence, review-platform presence, Wikidata entry. Owner actions tracked via the new contract.
4. **Phase 4 — DEO, conditional**: only for businesses with commerce/comparable offers; feeds and protocols after platform approvals; decision-stage prompt measurement folded into the probe harness.

## 5. Key sources (all accessed 2026-09-19)

- Dooley stack post (2026-09-18); DEO term origin: USA Today press release (2026-09-03).
- Princeton/Georgia Tech/IIT Delhi "GEO" KDD 2024 (arXiv:2311.09735) — citations/stats/quotes ~+40%.
- Ahrefs: 75k-brand mention/backlink correlations (Aug/Dec 2025); schema null-result (2026-05-11); AI-citation freshness (2026); AIO top-10 overlap collapse to 17–38% (2026).
- Muck Rack "What Is AI Reading?" (Dec 2025, May 2026) — 82–84% earned media.
- Seer Interactive (Jun 2025) — AI-referral conversion rates; Adobe Q1 2026; Rutgers/Wharton crawler-blocking cost (Dec 2025); OtterlyAI llms.txt experiment.
- Google Search Central AI-features guidance (2026-05-15); Bing WMT AI Performance (Feb 2026); GSC generative-AI reporting (Jun 2026).
- OpenAI/Stripe ACP (2025-09-29); Google UCP (2026-01-11); OpenAI product-feed spec (2026-01-30).
- Reddit Responsible Builder Policy (2025-11-11); Meta/Instagram API enforcement changes (2025–2026).
- Google/Deloitte "Milliseconds Make Millions"; Rakuten 24 A/B (web.dev); Baymard checkout meta-analysis (Sept 2025).
- Full per-layer source lists are in the seven research reports underlying this plan (available in session; regenerate on request).
