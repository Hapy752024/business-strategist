# Multilingual pain-query calibration review

Reviewed 2026-09-21. Scope: the current uncommitted collector and skill changes described by the other agent. This is a review and proposed design; implementation files were left unchanged. External retrieval informs the design, but no live customer-VOC comparison was run.

## Verdict

Keep the short topic seed, offline preview, explicit calibration step, source-language vocabulary, and reminder to cover entity feedback. Do not describe the multilingual search problem as fixed. The recommended probe can fail to execute the candidate it is supposed to evaluate. Other code paths contradict the new instructions.

The missing capability is an observable learning loop over both queries and sources: plan diverse searches, challenge the plan, execute attributable probes, review actual experiences, learn vocabulary and source locations, then search again. A judge helps check coverage and interpretation; its confidence cannot establish retrieval quality.

## Findings

### P1: Candidate calibration can measure identical baseline searches

`scripts/evidence_scout/collect.py:460` limits Reddit to the first five queries when explicit pain/workaround seeds exist. `collect_reddit` stops once its overall record cap is reached. `collect_brave_search`, at line 1400, selects positions 0, 3 and 6, and also stops at the overall cap. Neither uses `scheduled_queries` or honors `--query-limit` as the new probe instructions imply.

I ran both collectors with synthetic HTTP responses, `--query-limit 4`, `--limit 5`, the short topic `Versicherungsberatung`, audience `Selbstständige`, and two candidates: `Leistung abgelehnt` and `Makler meldet sich nicht`. For each candidate:

| Provider | Actually executed queries | Records | Candidate executed |
|---|---|---:|---|
| Brave | `Versicherungsberatung Selbstständige` | 5 | No |
| Reddit | `Versicherungsberatung Selbstständige`; `"why is it so hard to" Versicherungsberatung Selbstständige` | 5 | No |

The intended candidate is present later in the generated plan, but the collectors never reach it under this fixture. This proves a possible execution failure, not its frequency in live research. The provider behavior predates this patch; the new calibration recipe relies on it and therefore does not deliver the promised comparison.

Fix: allow probes to execute an explicit candidate query or query family, with per-query result allocation. Record planned, sent, failed, skipped and returned queries per provider. Keep shared baseline results separate from candidate scores. Preview the provider-specific schedule and allocation, not just the generic list. An adaptive scheduler may still stop early, but must report untested candidates as untested.

### P1: Validation still injects English into non-English queries

At `collect.py:343`, all validation languages receive English prompts including `"why is it so hard to"`, `"how do you deal with"`, `complaints` and `reviews problems`. Localized suffixes apply only to other expansions. These English prompts occupy early query slots.

Unsupported validation languages also use English fallback suffixes at line 335. For example, a Japanese validation plan contains `"why is it so hard to" 引越し 家族`. The existing discovery path deliberately preserves supplied seeds for unsupported languages; validation now behaves differently.

Fix: build locale-aware query objects before provider scheduling. Preserve supplied language when no pack exists and report the unsupported expansion. Keep bilingual/code-switching searches explicit when appropriate to the audience. English brand names and legitimate loanwords are not automatically errors.

### P1: Audience constraints still narrow every pain query

`collect.py:378` appends every `--segment-keywords` value to every validation query. This contradicts the new flag help, code comments and calibration anti-pattern list. Automatic audience inference also supplies these anchors.

Requiring an explicit audience label can miss accounts where membership is apparent from the source or surrounding thread. The appropriate repair is a declared mix of anchored and unanchored queries, followed by source-level segment review. Do not simply remove every anchor. Existing tests assert that every query contains the audience term; this contract needs an intentional update.

### P2: Entity coverage is inferred from provider names

At `collect.py:3817`, the new flag checks whether a review-provider name appears in `provider_summaries`. With `{'trustpilot_reviews': {'status': 'missing_credentials'}}`, the entity-pending warning disappears. Conversely, Firecrawl can perform legitimate entity-bound capture but is not in this set.

Fix: derive pending, attempted, failed and completed scope from the existing entity source plan, capture bindings and reviewed coverage. Selecting a provider proves none of these. An empty or inaccessible entity lane remains a gap.

### P2: The calibration method optimizes too narrow a target

`pain-query-calibration.md` asks for 3–6 formulations and selects the best precision. It does not explicitly require a second feedback-driven search round, pre-search independent review, or a source-selection experiment. It also asserts that low precision is a query problem; that diagnosis is too certain. Other causes include index coverage, access, source choice, extraction failures, locale handling and evidence classification.

Precision alone can favor one easy-to-find complaint, platform or segment while losing distinct episodes and contrary experiences. Five results are a useful smoke test, not a dependable ranking of near-tied candidates. Brave returns snippets here, so scoring them as verified firsthand voice would violate the existing hydration/source-review contract.

Fix: evaluate reviewed unique experiences, marginal discoveries, source and journey coverage, duplication and countercases alongside precision. Keep unresolved results visible. Never infer full-web recall from a convenience sample.

## Proposed workflow

### 1. Define coverage and ground the initial vocabulary

Reuse `plan_customer_feedback.py --topic-cells-json` and `references/voc-research-method.md`: locale, job, role, journey moment, source family and query intent. Start from supplied customer accounts, existing verified evidence, or a small neutral discovery pass. Preserve original phrases with source locators. Mark model-generated synonyms and translated wording as hypotheses.

Brainstorm in the target language, including local acronyms, everyday terms, technical terms, spelling variants, dialect/code-switching when applicable, and indirect accounts of consequences. Translation can generate useful candidates; the rule should prohibit untested literal translation as the sole method, rather than prohibiting translation altogether.

Illustrative German insurance phrases below are hypotheses, not collected customer quotations:

- Trigger/decision: `BU Gesundheitsfragen unsicher`.
- Consequence: `Versicherung zahlt nicht`.
- Workaround: `anonyme Risikovoranfrage selbst machen`.
- Indirect account: `seit Wochen keine Antwort vom Makler`.
- Countercase: `Versicherung ohne Makler abgeschlossen Erfahrungen`.

Use query families for decision, consequence, workaround, successful resolution, non-adoption and switching. Include both vocabulary expansion and concept expansion: a different phrase for the same problem is not coverage of a different journey stage.

### 2. Brainstorm where to search

For each important family, propose a source location and explain why it may contain this audience and experience: local discussion forums, relevant communities, Q&A, public comments or verified entity reviews. Treat locations as candidates until checked. Use the existing community discovery/review path where applicable.

Distinguish web indexes from evidence sources. Two search engines finding the same thread do not produce two independent experiences. Adding `Forum` to a query is only one discovery technique. Adapt syntax and query length to each provider, and retain explicit language/geography support limitations.

### 3. Challenge the plan before running it

For substantive research, use one fresh reviewer with a small packet containing the research question, target roles/locales, coverage cells, query families and source candidates. It should identify omitted vocabulary/roles, excessive constraints, duplicate ideas, supplier-biased language, implausible local wording, and missing contrary cases.

Require concrete edits or reasons to retain a query, rather than a generic quality score. Preserve an exploratory family even if the reviewer is uncertain. A plan reviewer can reject malformed searches; it cannot reliably know the winning search before retrieval. A second agent is optional for small lookups and adds no proof of native-language expertise by itself.

### 4. Execute attributable probes and review evidence

Execute the actual approved candidate families with recorded query IDs and provider parameters. Compare candidates within the same provider/locale/source lane before comparing different source strategies. A practical first batch might use 5–10 results per candidate, with follow-up for uncertain or consequential cases; these are starting allocations, not proof thresholds or spending caps.

Hydrate promising source pages, split speakers/episodes where needed, and apply the existing evidence review. Record:

- Relevant reviewed firsthand target experiences, adjacent experiences and unresolved fit.
- Supplier/editorial material and unrelated results.
- Planned, fetched, successfully reviewed and unavailable counts.
- Unique experiences and the additional ones contributed by each candidate.
- Decision-relevant source, role, journey and contrary-case coverage.

Compute precision only with a named denominator and keep unavailable/unreviewed counts alongside it. Do not substitute heuristic `user_pain` labels for review or silently treat inaccessible pages as irrelevant. Review a small sample of rejected results to check multilingual false negatives.

### 5. Learn from results and search again

Extract new vocabulary, named workarounds, institutions, events and community locations from reviewed source material. Preserve their provenance; supplier material may teach terminology but remains supplier context. Add targeted follow-ups for missing cells, remove diagnosed noise and preserve the original scope.

Classify why a query failed before rewriting it: ambiguity, excessive anchors, missing local phrase, wrong source, inaccessible content, extraction loss, unsupported locale, duplicate results, or unresolved audience fit. This avoids repeatedly polishing keywords when the source route is the problem.

Keep a mixture of productive searches and exploratory/contrary searches. Reserve fresh queries or sources for validation so the selected plan is not evaluated only on the material used to tune it. Start with one revision round; continue when new evidence or unresolved decision-relevant cells justify it. Stop with a reason and explicit gaps, never a generic declaration of saturation.

### 6. Keep implementation small and test the claimed behavior

Extend the existing source plan and query ledger with `query_id`, `candidate_id`, `locale`, `intent`, `source_family`, `seed_origin`, provider execution status and result/evidence IDs. A small `--query-plan` or equivalent explicit-query input would make candidate execution testable; this interface is proposed, not implemented.

Keep a single search-planning role, one optional independent reviewer, and the existing collector/evidence reviewer. Avoid a new general orchestration framework or a duplicate evidence-quality scoring system.

Implementation order:

1. Repair candidate execution, provider schedules, locale fallbacks and audience constraints.
2. Make preview and execution use the same plan and limits; repair entity-gap reporting.
3. Add structured planning/review and one evidence-driven revision step through existing artifacts.
4. Compare the previous implementation, current patch and revised loop on matched studies.

Regression acceptance should include exact outbound candidate queries, non-English validation and discovery, unsupported-language behavior, no network during preview, short query lists, skipped-query reporting, per-provider limits, failed entity lanes and protection from duplicated evidence. For live evaluation include German, another supported language, an unsupported language and an English control. Compare deduplicated reviewed experience yield and relevant coverage under matched retrieval allocations, with reviewer order blinded where feasible. Stable fixtures test mechanics; live comparisons test retrieval quality. Neither proves population demand.

## Verification performed

- `pytest -q tests/test_voc_collection_quality.py tests/test_collection_limits.py tests/test_entity_review_collectors.py`: **33 passed**.
- `python3 scripts/evidence_scout/test_classification.py`: **17 passed**.
- Direct query-plan probes reproduced English leakage and all-query audience anchoring.
- Synthetic collector execution reproduced candidate starvation for both suggested probe providers.
- Direct quality-summary probes reproduced the missing-credential entity-warning problem.

The existing tests passing does not establish calibration effectiveness. No implementation changes or live VOC benchmark were performed during this review.

## External sources

Retrieved 2026-09-21. These support design principles from information retrieval and evidence synthesis; they do not validate this repository's VOC performance.

1. McGowan et al., **PRESS Peer Review of Electronic Search Strategies: 2015 Guideline Statement**, published July 2016. Structured review covers question translation, search terms, syntax and filters. This informs the plan-review checklist; its original setting is literature searching. https://pubmed.ncbi.nlm.nih.gov/27005575/
2. Chuang et al., **Expand, Rerank, and Retrieve**, July 2023. Generates diverse query expansions and reranks them for passage retrieval. Supports separating generation from selection, without establishing that an untrained LLM judge improves customer research. https://aclanthology.org/2023.findings-acl.768/
3. Manning, Raghavan and Schütze, **Introduction to Information Retrieval**, 2008, pseudo-relevance feedback section. Warns about drift when top-ranked documents are treated as relevant without review. https://nlp.stanford.edu/IR-book/html/htmledition/pseudo-relevance-feedback-1.html
4. Weller et al., **When do Generative Query and Document Expansions Fail?**, March 2024. Reports that expansion benefits vary by retrieval setting and can introduce noise. Supports retaining simple baselines and empirical evaluation. https://aclanthology.org/2024.findings-eacl.134/
5. **Generative Query Expansion with Multilingual LLMs for Cross-Lingual Information Retrieval**, preprint submitted November 24, 2025. Reports dependence on query length, model/data conditions and language/script, with more elaborate prompts not consistently helping. Supports evaluation by locale rather than assuming a larger brainstorming prompt is sufficient. Its cross-lingual benchmark differs from source-language web VOC search. https://arxiv.org/abs/2511.19325
