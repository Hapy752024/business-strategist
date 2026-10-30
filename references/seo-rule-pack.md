# SEO Rule Pack

Checkable hygiene rules for German/English sites. Rules are checks, not ranking promises: none of them claims a ranking, traffic or citation uplift. Evidence classes: **D** deterministic repo check; **G** search-engine or browser-vendor guidance; **O** observational or secondary study (state its limits); **U** unverified.

## Contents
- [Hreflang and locale variants](#hreflang-and-locale-variants)
- [Content drift](#content-drift)
- [Programmatic pages](#programmatic-pages)
- [Schema as hygiene](#schema-as-hygiene)
- [llms.txt and agent access](#llmstxt-and-agent-access)
- [Earned media and AI citations](#earned-media-and-ai-citations)
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
| E1 | For a visibility goal, plan third-party coverage (press, directories, communities, reviews) before more on-site markup. | `earned-media-builder` route; `references/search-visibility-decisions.md`. | O |
| E2 | Measure with recorded AI answers over time and report observations, not causes. | `geo-audit` route and `references/ai-answer-recordings.md`. | D |
| E3 | Treat paid placement and advertorial as a separate category; do not count it as earned. | Keep the source type per placement. | O |

Evidence (retrieved 2026-10-31, secondary coverage; Muck Rack's primary report not opened): Muck Rack's "What Is AI Reading?" series is reported to attribute about 84% of ChatGPT, Claude and Gemini citations to earned sources in a May 2026 edition (over 25 million links), with paid content near 0.3%. Muck Rack's "earned" category is broad (academic, government, encyclopedic, social and third-party corporate sources as well as journalism), and the sample measures source composition, not that earned media causes a given brand to be cited. A later October 2026 edition (journalism share about 22%) appeared in one source only: **U**.

## Sources, attribution and licenses

Retrieved 2026-10-31. Rules above are written in this repository's own words; no text was copied.
- `AgriciDaniel/claude-seo`, https://github.com/AgriciDaniel/claude-seo, MIT License (LICENSE file checked). Ideas borrowed: separate audits for hreflang, drift baselines, programmatic pages, schema and agentic access. Only the repository front page was read, not the individual skill files.
- `coreyhaines31/marketingskills`, https://github.com/coreyhaines31/marketingskills, MIT License (LICENSE file checked). Idea borrowed: one shared product-marketing context document that every marketing skill reads first.
- Ahrefs JSON-LD study (May 2026): secondary write-ups, e.g. https://www.techwyse.com/news/ai-search/schema-markup-ai-citations-ahrefs-study
- llms.txt: https://www.searchenginejournal.com/googles-llms-txt-guidance-depends-on-which-product-you-ask/575431/ and https://www.techwyse.com/news/ai-search/google-ai-search-optimization-guide-llms-txt-lighthouse-audit
- Muck Rack "What Is AI Reading?": https://martechseries.com/content/generative-pulse-earned-media-consistently-drives-ai-citations-holding-at-84/ and https://www.contentgrip.com/what-muck-racks-what-is-ai-reading-report-reveals-about-ai-brand-visibility/
