# Pain-query calibration: plan, challenge, probe, review, refine

Use before substantive customer-problem collection when vocabulary is inferred,
when researching a new locale/source, or when prior results are mostly suppliers,
editorial material, duplicates or unrelated posts. Reuse current reviewed work.
A poor search can reflect wording, source/index coverage, access, extraction or
classification; it does not establish absence of pain.

## 1. Plan what and where to search

Reuse the source plan from `plan_customer_feedback.py --topic-cells-json` and
repo-root `references/voc-research-method.md`. Identify relevant locale, job,
role, journey moment, source family and query-intent cells; avoid a compulsory
Cartesian grid. Begin with supplied experiences, reviewed prior evidence, or a
small neutral discovery pass when local vocabulary/source locations are unknown.

Brainstorm distinct query families covering triggers/decisions, consequences,
workarounds, successful outcomes, non-adoption and switching. Include indirect
accounts of a problem, not only explicit complaints. As a starting point, try
3–6 complementary families; expand when a decision-relevant perspective is missing.
For each family record:

- Source-language phrases, local acronyms, everyday/technical terms, spelling
  variants and relevant dialect/code-switching. Translation can propose terms;
  do not depend solely on untested literal translation. Preserve source-derived
  phrases with locators and label invented/translated wording as hypotheses.
- Where those episodes may appear and why: candidate local forums, communities,
  Q&A, public comments, or verified entity-feedback sources. Check audience and
  access rather than treating a platform name or a `forum` suffix as coverage.
- A mixture of audience-anchored and unanchored searches. Source review establishes
  target membership; people need not name their audience category in every post.
- Expected useful evidence and likely false positives. Keep shared baselines
  separate from candidate comparisons, and keep topic/entity sampling frames separate.

Use existing community discovery and capture review where applicable. Indexed
community candidates are not automatically authorized or accessible capture targets.
Web indexes are retrieval routes; two indexes finding one post are one observation.

Treat geography, search language, original post language and displayed translation
as separate fields. A translated search result is not a new source-language
experience. Retrieve the original post where possible; retain useful local
acronyms/code-switching, and label unsupported-language or translation-only
coverage. Do not compare languages as if they necessarily sampled the same people.

Check ambiguity before adding emotion words: a local term may name several jobs
or industries. Use a concrete product, event or action to disambiguate it. Split
combined category phrases into separate customer episodes. For the actual first
scheduled queries, check distinct situations and sources, not only different
intent suffixes on the same broad topic. Generic positive wording can retrieve
supplier testimonials; seek successful episodes in discussion sources as well.

## 2. Review the plan before collection

For substantive studies, use a fresh independent reviewer when delegation is
available and authorized. Give it the research question, roles/locales, sampling
cells, query families, source candidates and known evidence, without telling it
which formulation should win. Ask for specific omissions and edits:

- Is local wording plausible? Are concepts and journey moments missing?
- Are audience constraints too restrictive, or phrases overly supplier-oriented?
- Does the plan cover consequences, workarounds and successful/contrary cases?
- Are source locations plausible for the audience, and provider syntax supported?
- Are apparently diverse candidates only paraphrases of one idea?

Resolve concrete defects, retain exploratory searches where uncertainty remains,
and record rationale. If delegation is unavailable, perform a separate inline
review and label it honestly; do not claim independence. Review checks plan quality,
not expected search performance. It does not require new user approval.

## 3. Execute exact, comparable probes

Use `collect.py --query-plan` for attributable calibration. The input follows
`schemas/pain-query-plan.schema.json`. Its exact queries replace generated queries;
no topic baseline, automatic suffix or audience term is added. Each row specifies
one provider. The selected provider set must exactly match the file, and all rows
must match explicit `--geo`/`--language`; run different locales separately.

Illustrative French relocation probe, not verified customer wording or a required
provider choice:

```json
{
  "schema_version": 1,
  "revision": "round-1",
  "review": {"mode": "inline", "notes": "Illustration only; complete substantive review for the actual study."},
  "queries": [
    {"query_id": "q1", "candidate_id": "deposit-delay", "query": "caution non rendue déménagement forum", "provider": "serper_search", "locale": "FR:fr", "intent": "pain", "source_family": "local_forums", "seed_origin": "generated"},
    {"query_id": "q2", "candidate_id": "successful-resolution", "query": "récupéré ma caution après déménagement", "provider": "serper_search", "locale": "FR:fr", "intent": "successful_alternative", "source_family": "local_forums", "seed_origin": "generated"}
  ]
}
```

Link rows to existing sampling cells with optional `cell_id`; record source-derived
vocabulary with `seed_origin: source_derived` and nonempty `seed_locators`.
Use provider-specific query rows when syntax differs. Query IDs and provider/query
pairs must be unique. `review` is analyst notes, not authenticated approval.
`source_family` and `intent` describe the planned search; inspect returned sources
before assigning their actual type, audience or experience.

Preview first (offline, no credentials, collection or workspace writes):

```bash
python3 scripts/evidence_scout/collect.py \
  --topic '<research question>' --customer-segment '<target segment>' \
  --query-plan '<query-plan.json>' --geo FR --language fr \
  --providers serper_search --query-limit 2 --results-per-query 5 --limit 10 \
  --query-preview
```

To collect, use the same arguments without `--query-preview`, add the actual
`--workspace`/`--case` or a unique `--out-dir`, and choose an appropriate `--days`
for recency-aware providers. Keep each round's artifacts separate.

Explicit plans support Reddit, Brave, Serper, Firecrawl, HN, GitHub, autocomplete,
YouTube, X, xAI discovery and ScrapeCreators keyword searches. Other routes retain
their existing workflows. xAI receives a seed prompt, not a verifiable exact
underlying search. See repo-root `references/research-query-calibration.md` for
provider allocation units and wrapper controls.
`--query-limit` selects the first N declared rows **per provider**. Every selected
query gets `--results-per-query` (1–10). `--limit` remains the per-provider record
cap and must cover all selected allowances; insufficient allocations fail before
collection. These bounds are reproducible sample allocations, not spending caps.

Compare candidates within the same provider/locale/source lane at the same depth
and relevant time window. Then compare source strategies separately. Do not pool
baseline results into each candidate's score. A query-limit omission or failed
provider is untested coverage, not a zero-quality candidate.

For a before/after test, freeze the current automatic schedule as well as any
historical baseline before inspecting results. Replay them with the same provider,
locale and depth; record actual search times. Separate the effects of wording,
source restrictions, extraction routes and classification changes. A later
source-derived round is a refinement check, not an independent causal benchmark.

The preview and saved `query_plan.json` contain provider schedules, allocations,
locale limitations, the input plan and its digest. `summary.json` contains the
actual per-provider `query_ledger`: query/candidate IDs, attempted/status,
returned/inspected counts, result URLs and record IDs. Evidence memberships retain
multiple discovery paths for a repeated record. `new_record_count` is marginal
within that provider's execution order, not independent-person or customer count.
The run snapshot is an output wrapper; pass its `input_plan` as a new input only
after intentional revision, not the entire wrapper.

For generated full-pass searches, use short `--topic-keywords`, review the mixed
anchored/unanchored schedule, and inspect any unsupported-language warning. Generic
preview explicitly lists providers outside its scheduling support. Exact plans
can include a short or long expression deliberately; the collector never rewrites it.

## 4. Review source evidence before scoring

Hydrate promising snippets, inspect complete pages and speakers, and apply the
existing experience ledger and source-review process. Classify reviewed firsthand
target/adjacent experiences, supplier/editorial material, unrelated results and
unresolved fit. Check a sample of rejected items for multilingual false negatives.
Automated relevance and `user_pain` labels are provisional.

Audit rejected leads in every language: a specialist keyword list may recognize
one language or acronym spelling and silently discard another. Preserve original
labels, record corrections with the shared source-review contract, and test the
exact failure before changing the classifier. Missing vocabulary is not negative
customer evidence. Retrieval quality and classifier retention are separate scores.

Check that extraction retained author/post boundaries and substantive text. HTTP
success can return only navigation; a forum can contain supplier replies, quoted
other speakers, or an AI-generated summary. None is automatically firsthand voice.
Use an available source API if the extractor explicitly does not support that site;
keep each attempt and the final capture provenance. Do not repeatedly retry a known
unsupported route. Thread pagination and API comment subsets remain coverage limits.

In the research plan's calibration notes record per candidate:

- Planned, attempted, fetched, unavailable, reviewed and unresolved counts.
- Reviewed target-experience precision with an explicit denominator; display
  unavailable/unreviewed counts separately rather than hiding them as negatives.
- Deduplicated useful experiences, marginal discoveries and source/role/journey
  coverage, including rare consequential episodes and contrary cases.
- Evidence IDs, source locators and existing review decisions supporting the counts.

Do not rank near-tied candidates confidently from five results or select solely
for precision. Retain complementary searches. Cross-provider duplicates and
unknown speaker independence require review; no automatic person deduplication
or convenience-sample prevalence estimate is justified.
Also report confirmed episode-bearing documents over all returned unique URLs as
a lower bound when review is partial, separately from precision among reviewed
documents. Retain query-result slots, unique documents and distinct speaker
episodes as different denominators. Old experiences may establish occurrence or
teach wording; record their dates and avoid treating them as current product facts.

## 5. Refine and validate on fresh searches

After each probe batch diagnose gaps: ambiguous wording, excessive constraints,
wrong source, unfamiliar local vocabulary, access failure, extraction loss,
unsupported locale, duplicates or unresolved target fit. Use reviewed material to
learn phrases, events, alternatives and source locations with their provenance.
Supplier pages may supply vocabulary but remain supplier context.

Write a revised query plan with stable candidate IDs for the same hypothesis,
new query IDs for changed searches, a new `revision`, `revision_notes`, and the
prior `input_plan_digest` as `previous_plan_digest`. Record dropped/retained/added
families and why in the research plan. Preserve original scope and contrary cases.
Try at least one evidence-driven revision when gaps remain; include fresh queries
or sources beyond those used to tune the plan. If no revision is useful, record why.
Record which reviewed documents are new to the study. Finding the seed thread again
does not validate the revised query; inspect off-topic returns and newly found
experiences, including successful and non-adoption cases. A refined query can be
worse or merely complementary; retain the evidence instead of declaring a winner.

Stop with an explicit reason: scoped questions sufficiently answered, mainly
repeat evidence, unresolved access, or a more informative next method. Do not
claim full-web recall or saturation. Carry the refined queries and source cells
into the broader topic-led pass; do not regenerate solely from the original brief.
Run the separate entity-led pass when verified alternatives exist. Reconcile
both with the source plan via `finalize_customer_feedback.py`; a provider selection
or successful capture cannot complete semantic feedback analysis.
