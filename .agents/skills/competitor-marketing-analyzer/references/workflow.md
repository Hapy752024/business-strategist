---
name: competitor-marketing-analyzer
description: Analyze competitor marketing approaches from public landing pages, positioning copy, CTAs, audience language, pricing signals, proof points, and channel clues.
---

# Competitor Marketing Analyzer Workflow

Use this skill after entities have been identified, or when the user provides URLs and wants a narrow marketing teardown. For lane assignment and full competitive/analog/reference synthesis, use `competitive-landscape-builder`.

## Ambiguity and Unknowns

If competitor identity, URL ownership, target geography, or category scope is ambiguous enough to change the analysis, ask one focused clarification question before proceeding. If a claim is not visible in the scraped/source material, say "I don't know" or "not found" and preserve the source gap. Do not infer pricing, conversion performance, channel success, ad spend, or customer traction from marketing copy alone.

## Procedure

1. Clarify the category/problem, target customer segment, geography, and competitor URL ownership when ambiguous.
2. State the marketing-analysis plan before scraping: competitor types prioritized, page types to treat as product evidence, and claims that will not be inferred.
3. Run the marketing analyzer on explicit URLs or a `competitors.json` from `competitor-scout`; review the script-generated `marketing_plan.md` for the run's scope, limits, and checkpoint.
4. Run the ads collector for paid-acquisition evidence when competitor Meta/Instagram presence matters: `python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --competitors-json "<competitors.json>" --countries <ISO codes> --limit 20`. Free official Meta Ad Library for EU/UK/EEA audiences; non-EU markets fall back to paid Apify (`--providers auto`, ask before `--approve-paid`). If `validate_meta.py` reports missing credentials, tell the user the one-time Meta app + identity-verification setup is pending instead of skipping ad evidence silently.
5. Inspect provider failures, fallback evidence, page types, source URLs, and pricing-token extraction before interpreting results.
6. Separate scraped landing-page evidence from direct HTTP fallback and cached snippets.
7. Analyze positioning, audience, pain language, every service/package, CTA, pricing posture, proof, product clues, website clues, and public social presence/usage.
   Extract explicit social URLs from first-party pages as unverified hints; verify profiles and activity with the approved public-platform workflow before reporting presence.
8. Compare ad messaging against landing-page positioning: same promise or segmented funnels? Long-running ads signal what keeps working, but never report longevity as proven performance — the Ad Library exposes no conversion or engagement data, and EU spend/impressions are coarse ranges.
9. Compare competitor promises against user-pain evidence rather than assuming copy reflects demand.
10. Produce an entity-by-entity summary, lane-aware differentiation opportunities, analog transfer notes where applicable, and follow-up evidence gaps.

## Command

Analyze explicit URLs:

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<category/problem>" --competitor-url "https://example.com" --competitor-url "https://competitor.com"
```

Analyze candidates from `competitor-scout`:

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<category/problem>" --competitors-json "projects/research/topics/<topic>/competitors/runs/<run>/competitors.json" --limit 10
```

Use deeper page discovery only when worth the credits:

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<category/problem>" --competitors-json "projects/research/topics/<topic>/competitors/runs/<run>/competitors.json" --limit 5 --deep
```

When analyzing a `competitors.json`, prioritize `direct_broker_candidate`, `direct_insurer_candidate`, and `marketplace_comparison_portal` before editorial resources. Analyze editorials separately unless the user explicitly wants SEO/content strategy.

Before scraping/analyzing pages, state the marketing-analysis plan in one paragraph: which competitor types will be prioritized, which pages will be interpreted as product/homepage evidence versus editorial evidence, and what claims will not be inferred from copy alone.

If Firecrawl fails or returns `billing_required`, use fallback evidence before giving up: direct HTTP fetch of the page, then cached snippets from `competitors.json` when available. Clearly state when full landing-page scraping was not performed and the analysis relies on fallback content. A report with `Competitors analyzed: 0` is not acceptable when competitor URLs or snippets are available; rerun with fallback or manually inspect cached snippets.

The script writes:

- `projects/research/topics/<topic>/competitors/marketing/<run>/marketing_plan.md` — objective, scope, questions, limits, and the comparison checkpoint for the run
- `projects/research/topics/<topic>/competitors/marketing/<run>/marketing_analysis.json`
- `projects/research/topics/<topic>/competitors/marketing/<run>/summary.json`
- `projects/research/topics/<topic>/competitors/marketing/<run>/report.md`
- `projects/research/topics/<topic>/competitors/marketing/<run>/raw.json`

## What To Analyze

For entry/strategy research, assess the four stages below against the researched customer journey. Narrow requests for a price or CTA do not require the full review. Use `stage | customer need | observed strength/weakness | source/date | proposed entrant advantage | test | confidence` in the existing report. Distinguish observed design from performance and company claims from customer outcomes.

- Visibility: target-customer search results, relevant social profiles/content, audience fit, referrals and other observed distribution. A dormant social profile does not establish low total visibility; a small brand does not establish easy acquisition.
- Sales: follow content to offer, contact/application and purchase as publicly accessible; assess clarity, objections, friction and trust. Do not infer conversion rates from website design or ad longevity.
- Service: inspect onboarding, help, responsiveness, problem resolution and balanced customer reviews. Attribute supplier versus intermediary failures correctly. Missing public service data stays unknown.
- Retention/engagement: investigate return use, helpful reminders/content, renewal, referrals, cancellation and reasons for leaving. Quiet social accounts are not evidence of low retention; some customers value reliable service with little ongoing contact.

Social content can build both visibility and relationships. State the initial exposure mechanism, reason to return, path to consent/contact and commercial action; followers and engagement are proxies. Treat a competitor weakness as an entry hypothesis only when it matters to the customer and the entrant can address it economically. Apply the served/entrant-feasibility rules in repo-root `references/strategic-positioning.md`.

Look for:

- Positioning: headline, category, promise, enemy/problem.
- Audience: who the copy is clearly for.
- Pain language: what pain they emphasize.
- Offer: free trial, demo, self-serve, sales-led, community, services.
- CTA strategy: primary and secondary calls to action.
- Pricing posture: transparent pricing, freemium, trial, enterprise, hidden pricing.
- Trust proof: logos, testimonials, case studies, security, metrics.
- Feature emphasis: what they make look easy or differentiated.
- Funnel/channel clues: SEO pages, comparison pages, alternatives pages, templates, reports, blog topics, ad-library evidence, social proof.
- Product-change clues: changelog, release notes, docs, integrations, and roadmap language.
- Distribution clues: partner pages, marketplaces, app stores, integrations, affiliate/referral pages, community.
- Paid-acquisition clues where available: Google SERP ads, Meta/TikTok ad libraries, X posts, YouTube sponsorships, and influencer mentions.

For German insurance pages, look for German and insurance-specific CTAs and pricing claims such as `Angebot anfordern`, `Beratung vereinbaren`, `Vergleich starten`, `kostenlos vergleichen`, `Jetzt berechnen`, `Beitrag berechnen`, `Get a free quote`, monthly premium examples, annual savings, GKV comparisons, deductibles, tariff names, `Stiftung Warentest`, `BaFin`, `IHK`, Trustpilot, and ProvenExpert.

Separate generic pricing language from structured price tokens. Extract and report currency amounts, monthly/annual periods, savings claims, deductibles, salary thresholds, and tariff/premium terms so the user can see whether "pricing evidence" is a real price signal or just generic transparency copy. Use `pricing_language_only` when a page mentions tariffs, premiums, contributions, prices, or transparency without extractable monetary/period/savings/deductible/threshold tokens.

Preserve raw price tokens and inspect normalized price tokens. The normalized values are convenience fields only; keep the raw token visible because German and English separators can be ambiguous in scraped copy.

Label page type for every analyzed URL: `homepage`, `product_page`, `blog_article`, `comparison_article`, or `other_page`. Do not interpret a blog article or SEO comparison page as equivalent to a broker landing page.

## Interpretation Rules

Do not assume marketing claims are true. Treat copy as evidence of how the competitor wants to be perceived, not proof that users care or that the channel converts.

Classify competitor traction signals against the weak-evidence list in `references/evidence-registry.md`: a competitor's downloads, follower counts, press coverage, waitlist size, review volume, or partnership announcements are weak evidence of demand. Do not report "competitor X is winning" from attention signals; report what their positioning and proof choices reveal, and note that even their retained economics are invisible from public marketing.

Assess competitor trust practices against the Service-Customer Decision and Trust section of the registry: hidden fees, hard cancellation, incentivized or generic-star reviews, and missing scope/credential/redress information are weaknesses to differentiate against for consequential services — not tactics to copy. Where competitors lack uncertainty reducers (precise scope, total price, credentials, human access, redress) for a high-risk service, name that gap as a differentiation opportunity.

Compare competitor promises against user-pain evidence. A competitor's positioning is most useful when it maps to repeated customer pain, willingness-to-pay signals, or reachable communities.

Preserve the source page for every extracted claim. Mark "not found" rather than inventing pricing, features, traffic, ad spend, or conversion performance.

If a provider fails because of missing credentials, no credits, rate limit, permission denied, or blocked scraping, tell the user before interpreting the competitor set. A thin data set can make a weak competitor look stronger than it is.

When Firecrawl returns HTTP 402 / `billing_required`, state that landing-page marketing analysis was not fully performed for affected pages. Do not describe fallback snippets as complete landing-page evidence. Separate `scraped_page_evidence`, `direct_http_fallback`, and `cached_snippet_only` in the analysis so weak fallback evidence is not mistaken for a full teardown.

When changing CTA, pricing, or page-type extraction, run:

```bash
python3 scripts/evidence_scout/test_classification.py
```

The tests include structured insurance price tokens, normalized price tokens, `pricing_language_only`, and page-type classification.

## Output

Report:

- Competitor-by-competitor positioning table.
- Shared category language.
- Marketing-mix table: audience, offer, CTA, pricing, proof, content/SEO, social/paid clues, product-change clues.
- Differentiation opportunities.
- Weak or overused claims to avoid.
- Suggested landing-page messaging hypotheses for the user's idea.
- Follow-up evidence needed before copying any competitor strategy.

When asking the user for input, ask exactly one question at a time. Recommended first question after marketing analysis: `Which competitor promise should we test against real customer interviews first?`

## Quality Checklist

Before finalizing, check:

- Competitor identity, URL ownership, geography, and category scope are clear enough.
- Every extracted claim has a source page or is marked "not found".
- Page type is labeled for every analyzed URL.
- Blog, editorial, and SEO pages are not interpreted as product-homepage evidence.
- Pricing evidence distinguishes raw price tokens from generic pricing language.
- Provider failures, billing issues, rate limits, or fallback-only evidence are disclosed.
- Marketing claims are treated as positioning claims, not proof of performance.
- Competitor attention signals (downloads, followers, press, review volume) are classified as weak evidence, not reported as demand proof.
- Competitor trust practices (reviews, fees, cancellation, uncertainty reducers) are assessed, with gaps named as differentiation opportunities and dark patterns flagged as do-not-copy.
- Differentiation advice is tied to evidence gaps or repeated customer pain.
