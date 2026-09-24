# Pain-query calibration implementation plan

Status: implemented and verified on 2026-09-21. The plan was written and reviewed inline before implementation.

## Objective and scope

Implement the findings in `docs/audits/2026-09-21-pain-query-calibration-review.md` while preserving the other agent's useful changes and unrelated research. Deliver a reusable search-planning and refinement procedure plus mechanically reliable calibration probes. No live research workspace, external outreach, deployment, new model integration or automatic evidence approval is required.

## Implementation sequence

1. **Locale and audience behavior.** Keep short topic keywords and preview. Remove unconditional English scaffolding from non-English validation, preserve supplied seeds when no locale pack exists, and report that limitation. Generate both unanchored and audience-anchored search families. Make automatic audience inference locale-aware before validation; explicit query plans supply their own exact constraints.
2. **Executable candidates.** Add a validated `--query-plan` JSON input with query/candidate IDs, exact query, provider, locale, intent, source family and seed origin. Support the four text-search backends used for calibration: Reddit, Brave, Serper and Firecrawl. Explicit plans replace generated queries, preserve declared order and may not silently fall back to other providers or locales. Keep topic/entity sampling boundaries intact.
3. **Fair, visible execution.** Add `--results-per-query` for explicit plans. Retain `--limit` as a hard per-provider record maximum; reject allocations that cannot give each selected query its declared allowance. Use the same per-provider schedule in preview and collection. Honor `--query-limit`, represent omitted/failed/blocked queries explicitly, and retain per-query returned counts, result locators and evidence memberships. A provider failure is a gap, never zero customer pain. Keep duplicate discoveries attributable without counting them as independent experiences.
4. **Coverage honesty.** Replace provider-name entity-gap inference with evidence-bound capture reporting. Always keep semantic review and study-wide entity coverage pending at collection time; a successful reviewed-locator fetch alone cannot establish completed VOC analysis. Preserve existing source-plan/review validators as coverage authority.
5. **Agent workflow.** Update the calibration reference and its direct callers: source-language and source-location brainstorming; an independent plan reviewer when available/authorized (otherwise an explicitly labeled separate inline review); exact candidate probes; hydration and existing evidence review; vocabulary/error diagnosis; revised queries and fresh-source validation; scoped stop reasons. Use existing source cells, query ledgers and research-plan notes rather than a second evidence-scoring system. Translation is a candidate-generation aid, with source-language verification.
6. **Regression and repository verification.** Test exact outbound queries, supported/unsupported languages, audience mix, preview without writes/network, invalid plans/allocations, short query lists, provider/HTTP failures, query caps, cross-query duplicates, entity-gap honesty and synthetic multilingual transfers. Run classification fixtures, setup validation and repository evals. Perform an inline adversarial review of final code and docs and resolve material findings.

## Query-plan contract

- One locale per collection invocation, with explicit `--geo`/`--language` matching the plan. Separate invocations handle separate locales.
- Each row names one supported provider. The requested provider set must exactly match the plan's provider set, preventing omitted candidates or unplanned search routes.
- Each row has a unique query ID; duplicate provider/query pairs are rejected so identical baselines are not scored as independent candidates.
- Query metadata links to existing sampling cells when supplied. Generated phrases remain hypotheses; source-derived seeds retain locators.
- Preview and run artifacts include the exact plan and proposed provider allocations. Runtime ledgers identify what was actually attempted and why anything was skipped.
- Review/refinement notes record substantive judgments. Structural checks do not authenticate reviewer independence or assert native-language skill.

## Plan review

Inline review, not an independent-agent verdict. Scope and authorization are clear; no UI/security-provider integration is involved. Blast radius: collector query construction and four search adapters, their tests, one input schema and the existing skill references. Keep other provider routes unchanged and describe them as outside explicit-plan support.

Resolved design risks before coding:

- **Result starvation:** per-query allowance plus preflight total-allocation validation; no automatic baseline queries in explicit mode.
- **Preview drift:** one shared provider scheduling function.
- **False evidence precision:** retain fetched/unreviewed/failed counts and use the existing semantic source-review contract; no automatic customer-precision score.
- **Scope drift:** exact provider and locale agreement; language fallback remains explicit.
- **Overbuilding:** one query-plan input and existing artifacts; no orchestration engine, judge API or new approval gate.

Acceptance: mechanics demonstrated with synthetic source responses; required repository checks pass or a specific unrelated/environment blocker is disclosed. Live retrieval improvement and cross-host agent behavior remain separate evaluations and must not be claimed from these checks.

## Delivered and verified

- Collector implements validated exact query plans, locale-aware generated queries, mixed audience constraints, shared preview/execution schedules, per-query allocation, duplicate discovery memberships, explicit failures/skips and capture-based entity-gap reporting.
- Added `schemas/pain-query-plan.schema.json` and 65 calibration regression cases in `tests/test_pain_query_calibration.py`; updated two existing tests to assert the intentional anchored/unanchored mix.
- Evidence-scout calibration instructions cover wording and source-location brainstorming, a concrete review checklist, source review, revision with provenance, fresh-query validation and explicit stop reasons. Updated evidence-scout/idea-grill handoffs and command guidance. No new judge service or automatic semantic-quality approval was introduced.
- `bash scripts/validate_setup.sh`: passed with **775 Python tests**, routing/fixture checks and zero errors. Its first sandboxed run had nine subprocess/socket permission failures in unrelated website tests; the unrestricted rerun passed. An existing town-db-curator checklist warning remains.
- Final focused suite after the last reporting adjustment: **111 passed**; classification fixtures: **17 passed**.
- Skill structural validation passed for both edited skills. The pre-existing idea-grill description warning remains. `scripts/run_evals.py` passed structural checks for **167 skill cases** and **31 routing cases**; town-db-curator still has no evals file. These are not LLM behavior evaluations.
- Executed the documented French JSON/CLI example as an offline preview: both exact queries received the declared allowance. Compilation and `git diff --check` passed.

Final inline review corrected plural audience inference, distinguished entity-page capture from searchable-provider preview, removed the irrelevant prose-topic warning for exact plans, and clarified that planned source labels and result counts are not reviewed customer evidence. Existing capture authorization and source-review mechanisms remain the semantic/coverage boundary.

No live VOC benchmark, independent-agent review or cross-host LLM evaluation was claimed. Unrelated concurrent website-review artifacts were left untouched. No commit was created.
