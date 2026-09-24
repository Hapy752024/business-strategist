# Query design and refinement across research workflows

Use for substantive market, operator, competitor and community discovery. A focused factual lookup does not require a full calibration experiment. Reuse current sources and reviewed vocabulary before collecting again.

## Before collection

1. Separate the research brief from short search phrases. Record target country, search language, original source language and intended audience independently. A translated result or English-language author does not establish residence or native language.
2. Brainstorm both vocabulary and source locations: local category names, acronyms, customer/operator situations, substitutes, counterexamples, and places where the relevant people or organizations publish. Disambiguate terms that name unrelated industries. Do not translate one long English sentence and call it coverage.
3. Review the candidate set for distinct questions, native terminology, source fit, missing lanes and confirmation bias. This is an analyst review, not another user permission gate. Preserve rationale and unresolved language judgments; do not label inline review independent.
4. Preview the executable schedule. Give each selected candidate an allocation; retain skipped and failed queries. Keep geography, provider, depth and period comparable when comparing strategies. An expanded source set is a changed sampling frame, not a language-only improvement.

## Evidence questions differ by workflow

| Workflow | What to search and review | What counts as useful evidence |
|---|---|---|
| Market problems | Jobs, triggers, workarounds, satisfactory outcomes and non-adoption; independent topic discovery before known-company feedback | Located original customer experiences, with situation, outcome and speaker boundaries |
| Founder/operator | First customers, decisions, economics, retention, failed channels and early-stage constraints; named operators and local interview/podcast vocabulary | Attributed operator actions and dated outcomes; corroborate success claims and preserve survivorship bias |
| Competitors | Same-market providers, non-software substitutes, explicit cross-market analogs and named capability references | Verified entity/job/segment fit from source pages; supplier claims remain supplier claims |
| Communities | Local member vocabulary and source names, separately for forums, Facebook groups and pages | Verified source shape, audience, activity, locale and access route; indexed URLs alone are leads |

## Execution controls

- `collect.py`, `discover_market_problems.py`, and `research_founder_playbooks.py` support `--topic-keywords`, `--segment-keywords`, `--query-plan`, `--query-limit`, `--results-per-query`, `--max-http-requests`, and `--query-preview`. A preview performs no provider calls or project writes.
- Exact plans use `schemas/pain-query-plan.schema.json` (shared for customer, operator and competitor searches). Each query binds provider, locale, candidate ID, intent and seed origin. Run locales separately. Source-derived seeds require locators; use `previous_plan_digest` and revision notes for a follow-up round.
- Collector allocations apply per provider. Set `--limit` high enough for every selected exact query's allocation. HN, GitHub, autocomplete, YouTube, X and ScrapeCreators accept these plans. Query caps retain unexecuted rows. GitHub appends issue/date filters; X appends language/retweet filters. These transformations are retained in raw requests. YouTube allocations cap retained records including metadata/comments/transcripts; raw captures preserve the larger response. Optional ScrapeCreators comments have a separate cap, and requested entity/community captures retain their own controls.
- xAI receives one seed per prompt; its underlying searches are not observable exact-query execution. Its output remains model-mediated discovery requiring inspection of cited posts.
- Operator defaults use separate source-language situations in English, German, French, Spanish and Italian. For another language supply `--operator-keywords` and a local `--topic-keywords`, or an exact plan. Non-English automatic runs require local topic keywords. The default provider set is `serper_search,youtube,hn`; choose alternatives explicitly. Seed translation and query quality still need review.
- Competitor discovery supports the same exact plan format with mandatory `lane_scope` (`competitive_market`, `similar_company`, `capability_reference`) and `scope_value` on each row. Providers are `brave_search` and `firecrawl`. Its `--query-limit` applies per provider per lane; `--results-per-query` is search depth. Existing lane limits control the final shortlist, not which queries run. All discovered candidates and query outcomes remain in the raw audit. Firecrawl requests country, but does not enforce original language.
- Community discovery keeps its locale-specific seed/source-term controls and complete lane coverage check. Use `--query-preview` before execution. Optional `--query-review` binds analyst notes and source-derived vocabulary to the signed discovery audit; it does not authorize capture or replace direct source review.

Community review JSON shape:

```json
{
  "revision": "round-2",
  "previous_plan_digest": "<SHA256 from prior query_plan.json>",
  "review_notes": "Why these vocabulary/source changes address observed misses",
  "seeds": [{
    "locale": "<COUNTRY:language>",
    "seed": "<exact locale seed passed on the CLI>",
    "seed_origin": "source_derived",
    "seed_locators": ["<source URL plus post/paragraph locator>"]
  }]
}
```

## After a probe

Inspect relevant and rejected leads, actual outbound requests, failures, duplicates and source content. Separate query-result slots, unique URLs, original speakers and verified entities. Successful extraction may contain only navigation, supplier replies, AI summaries or copied quotations. Check original pages/API units before accepting an experience or operator account.

Refine with vocabulary and locations observed in reviewed sources. Keep the original run immutable, bind the new revision to its parent digest, and compare newly useful sources against rediscovered seed pages. Record negative and satisfactory outcomes. Refinement may worsen results; retain the failure rather than implying improvement from more queries. Stop when the decision has sufficient coverage or name the unresolved gap. None of these mechanics proves prevalence, demand, competitor strength or a successful business.
