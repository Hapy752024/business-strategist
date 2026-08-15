---
name: competitor-scout
description: Identify potential direct, indirect, and substitute competitors for a business idea or customer problem using script-based web discovery, then separate real solution providers from blogs, marketplaces, agencies, and review sites.
---

# Competitor Scout Workflow

Use this skill when the user wants to know who already offers similar solutions, what alternatives customers use, or whether a market/category already has competitors.

## Stance

Be skeptical. Search results are candidate evidence, not truth. A competitor can be:

- Direct: solves the same problem for the same segment.
- Indirect: solves part of the job or targets a neighboring segment.
- Substitute: spreadsheet, agency, marketplace, manual workflow, incumbent tool, or "do nothing".

Do not confuse review sites, blogs, app stores, directories, consultants, affiliate pages, SEO guides, or integration partners with direct competitors.

Use stricter candidate classes: `direct_broker_candidate`, `indirect_broker_candidate`, `direct_insurer_candidate`, `indirect_insurer_candidate`, `marketplace_comparison_portal`, `lead_gen_affiliate`, `editorial_resource`, `service_substitute_candidate`, `substitute_candidate`, `future_threat_candidate`, `known_competitor_unverified`, `uncertain_candidate`, and false positives/exclusions. SEO guides, affiliate content, and editorial resources are not direct competitors unless the page evidence shows they sell, underwrite, broker, or manage the product for the target customer.

## Ambiguity and Unknowns

If the category, segment, geography, or competitor definition is ambiguous enough to change classification, ask one focused clarification question before running or interpreting discovery. If a candidate cannot be classified from the available title, snippet, URL, or page evidence, say "I don't know" for that field and mark the candidate `uncertain` rather than guessing.

## Procedure

1. Define the category/job, target segment, geography, and what counts as direct, indirect, substitute, future threat, or false positive.
2. Preserve and pass any user-supplied known competitors into discovery.
3. Run competitor discovery with the documented script.
4. Review the script-generated `competitor_plan.md` (objective, scope, questions, limits) and confirm the stated classification rules still match the request.
5. Inspect `competitors.json`, `summary.json`, `report.md`, and raw source evidence.
6. Canonicalize known brands to product/entity URLs when search returns noisy blog, cancellation, or unrelated pages.
7. Classify each candidate using title, snippet, URL, source query, page evidence, and segment fit.
8. Separate entity classification from source-page classification.
9. Rate evidence quality before rating competitor strength.
10. Report direct competitors, indirect competitors, substitutes, future threats, false positives, and candidates to pass to marketing analysis.

## Command

Run:

```bash
python3 scripts/evidence_scout/discover_competitors.py --topic "<problem/category>" --customer-segment "<segment>" --known-competitors "<comma-separated optional names>" --limit 20
```

Before interpreting candidates, state the competitor plan in one paragraph: category/job, segment, known competitors supplied, provider sources, and what will count as direct, indirect, substitute, future threat, or false positive.

Always pass user-supplied known competitors. The script must force them into the candidate set or mark them `known_competitor_unverified` if URL evidence was not found, rather than silently omitting them.

Before marking a known competitor unverified, run a direct lookup for that name plus the category/geography, for example `CLARK insurance app Germany`, `Getsafe private health insurance Germany`, or `Verivox PKV Vergleich`. If the direct lookup finds a URL, annotate the candidate as known rather than adding a duplicate unverified row.

For known brands, prefer canonical product/entity URLs over accidental blog or cancellation-provider results. Reject noisy lookup hits about `kündigen`, cancellation, or contract termination when the research topic is PKV/BU brokerage. If search returns a blog page for a known broker/platform, canonicalize to the known product/home URL and mark that the evidence was canonicalized.

The script writes:

- `research/topics/<topic>/competitors/runs/<run>/competitor_plan.md` — objective, scope, questions, limits, and the verification checkpoint for the run
- `research/topics/<topic>/competitors/runs/<run>/competitors.json`
- `research/topics/<topic>/competitors/runs/<run>/summary.json`
- `research/topics/<topic>/competitors/runs/<run>/report.md`
- `research/topics/<topic>/competitors/runs/<run>/raw.json`

## Analysis Rules

Classify each candidate using the stricter candidate classes above. Use the candidate URL, snippet, title, source query, and known customer segment. If classification is uncertain, say so. Treat query-only overlap as weak evidence; a page found through a competitor query is not a direct competitor unless its own title/snippet/page evidence confirms the job and business model.

For insurance topics, classify with these defaults unless page evidence says otherwise:

- Licensed/digital broker or insurance manager selling multiple insurers: `direct_broker_candidate` or `indirect_broker_candidate`.
- Single insurer or carrier selling its own tariff: `direct_insurer_candidate` or `indirect_insurer_candidate`.
- Comparison portal such as CHECK24/Verivox-style flow: `marketplace_comparison_portal`.
- Blog, guide, expat information site, SEO comparison article, or review page: `editorial_resource` unless it clearly captures leads or brokers policies.
- "We connect you with a broker", affiliate links, recommended broker pages, and quote-request funnels without clear own advisory operation: `lead_gen_affiliate`.
- Broad insurance manager apps that do not show PKV/BU brokerage evidence, such as a generic policy-management homepage, should be `future_threat_candidate` / adjacent app rather than `direct_broker_candidate`.

Prefer structured page evidence over domain memory when possible: homepage vs article path, first-party "we/our" claims, regulated entity/imprint cues, own CTA ownership, and whether the page actually sells/brokers/underwrites the product.

Keep entity classification separate from source-page classification. `entity_type_hint` describes the business/entity; `source_page_type_hint` describes the discovered page evidence, such as `product_or_comparison_page`, `product_or_homepage_candidate`, `blog_or_resource_page`, or `adjacent_app_homepage`. A real broker found via a blog page is still a broker, but the page evidence is weaker than a product/quote page.

When changing competitor classification logic, run:

```bash
python3 scripts/evidence_scout/test_classification.py
```

The tests include known-competitor noise rejection, entity/page separation, and broad insurance-app classification.

Use a competitor-array frame:

- Define the category/job and customer segment in one sentence.
- Identify current competitors and future threats.
- List the customer benefits expected: price, speed, convenience, reliability, support, integrations, trust, and measurable outcomes.
- Rate evidence quality before rating competitor strength.
- Preserve source URLs and snippets so the user can inspect every claim.

For each plausible competitor, identify:

- Who they appear to target.
- What problem/job they claim to solve.
- Category language they use.
- Whether they are likely direct, indirect, or substitute.
- Whether they are a future threat because they serve the same segment, use adjacent technology, own distribution, or could add the feature cheaply.
- Which key success factors appear relevant and which are still unknown.
- Evidence quality: strong, medium, weak.
- Human review status: verified, likely, uncertain, or excluded.

Do not overfit to software companies. For a real business idea, substitutes can include agencies, consultants, spreadsheets, templates, marketplaces, communities, internal teams, manual workflows, and doing nothing.

## Output

Report:

- Top plausible direct competitors.
- Indirect competitors and substitutes.
- Future threats and adjacent players.
- False positives excluded.
- Category language and positioning patterns.
- Competitor-array matrix: candidate, type, segment fit, job fit, key success factors, evidence quality.
- Gaps where the user's idea may still differ.
- Recommendation for which competitors to pass to `competitor-marketing-analyzer`.

When asking the user for input, ask exactly one question at a time. Recommended first question after competitor discovery: `Which candidate do you most want to understand as a threat or positioning reference?`

## Quality Checklist

Before finalizing, check:

- The category/job and customer segment are specific enough for classification.
- Known competitors supplied by the user are included or explicitly marked unverified.
- Search-result candidates are not treated as competitors without supporting page evidence.
- Editorial, affiliate, directory, review, and app-store pages are not mislabeled as direct competitors.
- Entity type and source-page type are kept separate.
- False positives and uncertain candidates are explicitly labeled.
- Evidence quality is rated before competitor strength.
- Source URLs and snippets are preserved for inspection.
