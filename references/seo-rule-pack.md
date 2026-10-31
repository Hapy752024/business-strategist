# SEO Rule Pack

Checkable hygiene rules for German/English sites. Rules are checks, not ranking promises: none of them claims a ranking, traffic or citation uplift. Evidence classes: **D** deterministic repo check; **G** search-engine or browser-vendor guidance; **O** observational or secondary study (state its limits); **U** unverified.

## Contents
- [Hreflang and locale variants](#hreflang-and-locale-variants)
- [Content drift](#content-drift)
- [Programmatic pages](#programmatic-pages)
- [Schema as hygiene](#schema-as-hygiene)
- [llms.txt and agent access](#llmstxt-and-agent-access)
- [Earned media and AI citations](#earned-media-and-ai-citations)
- [Search-visibility improvement decisions](#search-visibility-improvement-decisions)
- [Linkable assets: statistics, calculators and checklists](#linkable-assets-statistics-calculators-and-checklists)
- [Sources, attribution and licenses](#sources-attribution-and-licenses)

## Hreflang and locale variants

| Rule | What to check | How | Evidence |
|---|---|---|---|
| H1 | Every locale variant lists all variants including itself, and each target links back (reciprocal). | Manual crawl of the rendered head for each sitemap URL; `scripts/brand/seo_checks.py` covers canonical and sitemap signals only, not reciprocity. | G |
| H2 | Language codes are valid (`de`, `de-AT`, `en`), with an `x-default` only when a real fallback page exists. | Manual review against the planned locale list. | G |
| H3 | Each variant has a self-referencing canonical; no variant canonicalises to another language. | `python3 scripts/brand/site_gate.py` (`seo_signals`) | D |
| H4 | German and English pages are written for their audience, not machine-translated copies with identical keywords. Each locale gets its own keyword-map row. | `scripts/marketing/keyword_map.py` with a `locale` per cluster. | D (map validity), manual (quality) |

## Content drift

Drift means a published page no longer matches the query or cluster it was planned for, because the copy changed, the cluster moved, or searchers use other words.

| Rule | What to check | How | Evidence |
|---|---|---|---|
| C1 | Each live page maps to exactly one planned cluster; orphans and double-mapped pages are listed. | `keyword_map.py` validation, then compare page inventory with the map. | D |
| C2 | Planned clusters show impressions for their terms after launch; clusters with none are reported as "none observed in this export", not as proven zero. | `scripts/marketing/search_feedback.py` on a Search Console export; it proposes a `decision` and never writes the reviewed map. | D |
| C3 | Queries that match no cluster are reviewed as candidates for a new page or a page revision, not guessed into a cluster. | `search_feedback.py` unmatched-query list. | D |
| C4 | After any copy edit to a mapped page, re-run C2 on the next export and compare against the previous one. Record the comparison, not a causal claim. | Keep dated exports with the case workspace. | O |
| C5 | Keep dated SEO audits so changes between releases can be compared, without a ranking claim. | `scripts/brand/compare_seo_audits.py` on two compatible audit outputs. | D |

## Programmatic pages

| Rule | What to check | How | Evidence |
|---|---|---|---|
| P1 | Generate a page only when it has its own data (a real attribute, price, listing, local fact) that a visitor cannot get from a sibling page. | Review the data source per template before generating. | G |
| P2 | Pages in one template differ in more than a swapped keyword; sample ten and compare the body text. | Manual diff of a sample; flag near duplicates. | G |
| P3 | Start with a small batch, review the search feedback (C2), and only then widen. No batch ships without a deletion or `noindex` plan for pages that stay empty. | `search_feedback.py` per batch. | O |
| P4 | Each page is reachable from a hub, appears once in the sitemap and has a unique canonical. | `site_gate.py` `seo_signals`. | D |
| P5 | Do not invent per-page facts, reviews or statistics. Claims follow the repo's claim and evidence rules. | `scripts/marketing/claims.py`, case insights. | D |

## Schema as hygiene

Structured data is valid markup for rich-result eligibility and parse clarity. It is not a lever for AI citations.

| Rule | What to check | How | Evidence |
|---|---|---|---|
| S1 | Markup matches visible content and uses types Google documents for rich results (Organization, Product, Article, LocalBusiness, FAQ only where policy allows). | Google Rich Results Test; manual comparison with the page. | G |
| S2 | JSON-LD parses, has no placeholder values and no fields the page does not show. | Manual validation; no repo script validates schema content. | G |
| S3 | Do not report schema work as a GEO or AI-citation improvement. | Reports use the observation wording of `references/ai-answer-recordings.md`. | O |

Evidence for S3 (retrieved 2026-10-31, via secondary write-ups; Ahrefs' own report was not opened): an Ahrefs controlled study published May 2026 compared pages that added JSON-LD with control pages and found citation changes in Google AI Overviews, AI Mode and ChatGPT within noise. The reported counts (about 1,885 treated pages, about 4,000 controls) and percentages are **U** until checked against the primary report. A limit reported by the same write-ups: it measured pages already being cited. Google's documentation says structured data is not required for generative AI search and no special markup is needed (quoted by the same secondary sources; check Search Central directly).

## llms.txt and agent access

| Rule | What to check | How | Evidence |
|---|---|---|---|
| L1 | Treat `/llms.txt` as optional agent-readiness hygiene. Report presence and parse errors only. | `site_gate.py` check `llms_txt` and `agentic_browsing`. | D |
| L2 | If the file exists, it is Markdown with an H1 and Markdown-style links; a server error on it is a defect. | Manual and `site_gate.py`. | O |
| L3 | Do not claim it affects Google ranking or AI-answer inclusion. | Wording check in reports. | G |

Evidence (retrieved 2026-10-31, secondary coverage; U for details): Google's guidance is reported to say llms.txt has no bearing on AI Overviews or AI Mode, and John Mueller is quoted saying AI services do not use it. Lighthouse 13.x (about 13.3, **U**) adds an llms.txt audit in an experimental agentic-browsing category aimed at browser agents, with a missing file reported as not applicable. Verify against Search Central and Lighthouse docs before citing.

## Earned media and AI citations

| Rule | What to check | How | Evidence |
|---|---|---|---|
| E1 | For a visibility goal, plan third-party coverage (press, directories, communities, reviews) before more on-site markup. | `earned-media-builder` route; the "Search-visibility improvement decisions" section below. | O |
| E2 | Measure with recorded AI answers over time and report observations, not causes. | `geo-audit` route and `references/ai-answer-recordings.md`. | D |
| E3 | Treat paid placement and advertorial as a separate category; do not count it as earned. | Keep the source type per placement. | O |

Evidence (retrieved 2026-10-31, secondary coverage; Muck Rack's primary report not opened): Muck Rack's "What Is AI Reading?" series is reported to attribute about 84% of ChatGPT, Claude and Gemini citations to earned sources in a May 2026 edition (over 25 million links), with paid content near 0.3%. Muck Rack's "earned" category is broad (academic, government, encyclopedic, social and third-party corporate sources as well as journalism), and the sample measures source composition, not that earned media causes a given brand to be cited. A later October 2026 edition (journalism share about 22%) appeared in one source only: **U**.

## Search-visibility improvement decisions

Use inside the existing scoped audit/strategy deliverable, after loading the relevant website or monitoring procedure. No new research workspace, strategy or recurring program for a focused technical task or supplied-copy rewrite.

1. Name the observed problem, affected customer task/page and intended outcome. If visibility, audience behavior or attribution is unknown, say so. A visible broken route, conflicting offer or inaccessible answer can justify a bounded fix without a market-wide demand claim.
2. Inventory available evidence: rendered site/content, authorized Search Console/Bing data, referral/conversion records or server logs if available, recorded answer panels, and existing approved owner facts. Do not connect accounts or activate tracking implicitly. For commercial facts, current explicit owner corrections override repository values. Existing code/constants show what is implemented; they do not by themselves prove approval. Reconcile conflicts before improving offer copy; omit disputed prices and ask only about unresolved deliverable scope. Keep each metric's surface and denominator separate. Export placeholders converted to zeros must retain an availability flag.
3. Select the few changes supported by evidence, prioritizing user-facing obstruction and inaccurate/misleading information. Check existing assets first. Clear answers, reliable claims, accessible navigation and a usable conversion path may be enough; schema, posting, feeds and API monitoring are conditional. No action warranted is a valid finding.
4. For each selected change produce: **page/customer task | dated observation + uncertainty/source | change | expected customer benefit/outcome | agent work | owner-only dependency | effort/priority | acceptance check | review date/stop rule**. A statement about likely benefit is a hypothesis until observed.
5. Prepare reviewable local changes, run applicable QA, and record source revision, routes and limitations. Keep launch blockers intact. Owner publication/connection decisions remain governed by the existing authorization, not repeated approval requests.
6. Apply `references/marketing-execution.md` (owner-action contract). On resume read the active track manifest, reconcile accepted owner rows and their linked details, and continue agent-verifiable work independently. Do not turn optional recommendations into blockers.
7. At the agreed review point compare like-for-like measurements and record continue/change/stop. If no live baseline or authorized launch exists, report local acceptance separately and the outcome as pending. Expand automation only when the manual workflow repeatedly changes a decision or saves demonstrated effort.

For a quote-based service, preserve the commercial model; explain scope and the path to an estimate. For e-commerce, reconcile authoritative prices/stock before markup/feed work. For a site with no analytics, use authorized logs/first-party exports if available; otherwise retain the measurement gap. A two-heading rewrite returns two headings, not this full queue.

For content priorities consume the versioned keyword/page map: inspect existing pages before creation and choose retain/improve/create/consolidate/retire with evidence and a conversion path. Research-backed public resources retain original-versus-compiled contribution, source limitations, public-use review and maintenance ownership. A resource's publication does not automatically start external promotion.

For off-site references use the earned-media discovery/preparation/verification routes. Measure prepared pitches, sent receipts, responses, live placements, referrals and qualified outcomes separately. Keep rel attributes, provider observations, indexing and ranking changes distinct. Use the existing `decision_record()` for matched aggregate windows and continue/change/stop decisions; no default cadence or allocation is imposed.

## Linkable assets: statistics, calculators and checklists

Read when planning website content, SEO pages or earned media for a chosen idea. Technical SEO (speed, security, mobile, indexability) is hygiene; what earns links, citations in AI answers and return visits is original, checkable, useful material. Plan it from the customer journey, not from keyword lists alone.

### What to propose, per journey stage

For each stage of the customer journey already recorded (awareness, consideration, decision, onboarding/after purchase), name the one question the customer must answer there and the smallest asset that answers it:

- **Statistics page**: the numbers the customer and the writers covering the topic keep looking up. Prefer official sources already wired in `config/source-capabilities.json` (Eurostat, Istat and national statistics, census, BLS, ECB, FRED, World Bank, company registers). Each figure carries source, date and retrieval date; one complete sentence per finding so it can be quoted; a stable URL; a visible "last checked" date and a refresh owner. Compiled statistics from other sources are allowed when labelled compiled, not original.
- **Calculator or checker**: a calculation the customer repeats by hand (income against a visa bar, eligibility for a tax regime, a cost comparison between two places). Inputs the customer actually has, a result with its rule and source, and the cases the tool cannot decide said plainly. Test normal and odd inputs; give it a permanent page.
- **Checklist or order of operations**: the steps in the order that avoids rework, with the document, authority and typical duration per step, and the failure that step prevents.
- **Comparison table**: the few alternatives the customer actually weighs, on the criteria they use, with the trade-off stated rather than a winner declared.

### Rules

- Evidence first: a statistic without a dated primary source is a draft, not a page. Unknown stays "not checked", never zero.
- One asset per journey question; say why that question and what evidence (search journey, customer voice, competitor content inventory) shows people ask it.
- State the maintenance cost: who refreshes which number, when, and what the page says when it is stale.
- Promotion (earned-media-builder) is a separate task; building the asset does not authorize outreach or publication.
- Record proposed assets as public-resource briefs (marketing-strategy-builder keyword research) so the website build consumes a reviewed brief, not a chat idea.

## Sources, attribution and licenses

Retrieved 2026-10-31. Rules above are written in this repository's own words; no text was copied.
- `AgriciDaniel/claude-seo`, https://github.com/AgriciDaniel/claude-seo, MIT License (LICENSE file checked). Ideas borrowed: separate audits for hreflang, drift baselines, programmatic pages, schema and agentic access. Only the repository front page was read, not the individual skill files.
- `coreyhaines31/marketingskills`, https://github.com/coreyhaines31/marketingskills, MIT License (LICENSE file checked). Idea borrowed: one shared product-marketing context document that every marketing skill reads first.
- Ahrefs JSON-LD study (May 2026): secondary write-ups, e.g. https://www.techwyse.com/news/ai-search/schema-markup-ai-citations-ahrefs-study
- llms.txt: https://www.searchenginejournal.com/googles-llms-txt-guidance-depends-on-which-product-you-ask/575431/ and https://www.techwyse.com/news/ai-search/google-ai-search-optimization-guide-llms-txt-lighthouse-audit
- Muck Rack "What Is AI Reading?": https://martechseries.com/content/generative-pulse-earned-media-consistently-drives-ai-citations-holding-at-84/ and https://www.contentgrip.com/what-muck-racks-what-is-ai-reading-report-reveals-about-ai-brand-visibility/
