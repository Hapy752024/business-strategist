# Implementation and skill-scope review

Date: 23 September 2026. Scope: the current working tree, including the uncommitted implementation of the [analysis-quality plan](../agent-improvements/2026-09-23-analysis-quality-implementation-plan.md). Existing venture research was not audited or changed.

## Conclusion

The plan is partially implemented. There are useful capture, schema, template and routing changes, but the implementation does not yet enforce several of its central evidence-quality promises. Improving analysis has not been demonstrated by comparative outputs. Fix the acceptance boundaries before adding more research throughput.

The [implementation record](../agent-improvements/analysis-quality-implementation-record.md) acknowledges many unfinished items. However, its statement that candidate-bearing finalization is bound to the study is stronger than the code supports. Its description of the evaluation scaffold as making no quality claim also conflicts with the summarizer's `overall_quality_pass` output.

## Evidence and boundaries

- Inspected the plan, implementation record, relevant producers, consumers, validators, schemas, router, module references, skill metadata and project-bound references.
- Inventoried 39 installed skills. Only `town-db-curator` lacks an `evals.json`; presence of such a file does not establish a measured quality evaluation.
- Ran [offline adversarial reproductions](fixtures/analysis-quality-20260923/reproduce.py); [results and inspected-code hashes](fixtures/analysis-quality-20260923/results.json) are preserved. These exercise two receipt functions, the real claim-validator CLI, and the evaluation summarizer. They do not constitute a full discovery-to-business-stage replay.
- Did not rerun the full suite. The implementation record's 842 passing tests are a prior result, not a new result of this audit. The current reproductions demonstrate cases that green structural tests did not exclude.
- No production code, skill, project data or workflow state was modified by this review. New audit documents and the reproducer are the deliverables.

## Findings in priority order

### 1. High: ordinary problem validation accepts documents without customer evidence

Location: `scripts/evidence_scout/workspace.py:66` (`_problem_validation_receipt`) and `:103` (`_receipt_current`).

The producer requires three nonempty files under the segment, journey and pain directories, rejects a few unfinished-marker words, and looks for a URL and date. It does not require reviewed findings, resolve source locators, or inspect evidence disposition. The consumer checks case/revision and file hashes.

**Reproduced:** three files containing `No customer observations exist. https://example.invalid/source 2026-09-23` produce a `valid` receipt which is accepted as current. This proves a failure in the receipt acceptance boundary; the reproducer does not replay every downstream route.

**Consequence:** file presence and stable bytes can be mistaken for a validated customer problem.

**Required repair:** ordinary closure must consume an explicitly reviewed, current problem assessment linked to the relevant segment, journey, findings and evidence. Bind actual scope and decision disposition. An insufficient-evidence investigation can complete honestly while remaining ineligible for a business commitment. Preserve explicit authorized overrides as a separate, scoped path. Do not make an arbitrary interview count or every possible source a prerequisite.

### 2. High: discovery finalization does not bind the pack to the active study

Location: `scripts/evidence_scout/discover_market_problems.py:228–335`; `scripts/evidence_scout/validate_customer_voc_synthesis.py`.

The finalizer accepts an external `--voc-pack`, requires version 3 for new candidate-bearing outputs, checks its report hash, and validates IDs. It supplies the source review's own target segment to the validators. It never compares `study_id` or `research_design_digest` to an authoritative active run, case, scope or question plan.

**Code-inspection finding:** a pack's internal consistency and its self-supplied report hash do not establish that it belongs to this investigation. This audit did not construct a full schema-valid cross-study finalization fixture.

**Required repair:** resolve expected identity from the current run, compare study/case/scope/design revision, and resolve question and candidate associations against that identity. Legitimate shared or external evidence needs an explicit source snapshot and applicability binding. Changing only the report hash must not make an unrelated study current.

### 3. High: finding/claim links do not establish that the finding is supported

Location: `scripts/evidence_scout/validate_synthesis.py:36–58`, `:77–92`, `:149–189`; discovery candidate checks at `discover_market_problems.py:299–311`.

The implementation checks reciprocal IDs and the presence of a verification object. It binds verification to the claim text and evidence/review bytes, but does not bind it to the published finding text. Passage locators are not resolved by this verifier. Unsupported, unresolved and contradicted assessments are permitted without checking how a linked positive finding uses them. The report's claim IDs need only be a subset of known IDs; coverage of material report assertions is not established.

**Reproduced through the actual claim-validator CLI:** an unsupported claim saying no payment observation exists, backed by an empty evidence file, can link to a positive payment finding and return `pass`. This uses a deliberately minimal synthesis, so it proves the claim-validator boundary, not acceptance of a complete version-3 VoC pack by every validator.

**Required repair:** bind the reviewed relationship to exact current claim and finding text, and resolve supporting/contrary passages to captured content. Preserve contradictory or unresolved records for analysis, but prevent their promotion into supported assertions. Reports need material-assertion coverage and an explicit disposition for hypotheses. Source hashes are an integrity check; semantic support still requires an actual review of the passages.

### 4. High: the evaluation importer can report success without an evaluation

Location: `scripts/validate_analysis_eval.py:25–64`; `evals/voc/analysis-eval-manifest.json`.

**Reproduced:** empty ratings return `valid: true` and `overall_quality_pass: true`. An unknown task with one A/B pair also passes. A version with source fidelity and uncertainty rated 1/4 can win by summing higher ratings on other dimensions. The manifest remains explicitly design-only.

**Required repair:** distinguish valid input, complete comparison and adoption decision. Reject unknown tasks, missing required pairs and unfrozen evaluation inputs. Require actual packet/output identities, reviewer calibration and the declared comparison panel before emitting any quality decision. Preserve noncompensatory fidelity and uncertainty requirements; report dimensions separately. An explicit exploratory subset can be summarized without becoming an adoption pass.

This is additional to the already acknowledged absence of frozen packets, a pre-change analytical baseline, blind ratings and module-specific comparisons.

### 5. Medium: resumption preserves completed provider batches, including unsuccessful ones

Location: `scripts/evidence_scout/collect.py:4793–4817`, `:4829–4866`.

Every returned provider summary is put in `providers_completed`, irrespective of success, partial failure or credential failure. Resume loads and skips those entries. Recovery is at provider boundaries; a crash after raw capture but before the completion marker does not replay the captured payload into normalized records.

**Code-inspection finding:** retrying after a repaired provider can retain its previous failure. Retrying an interrupted batch can repeat remote work. Appending normalized records and saving the marker are separate operations, creating another interruption boundary to exercise.

**Required repair:** distinguish successful work, retryable failures and terminal unsupported routes; persist operation identity and recover captured responses before retrieval. Keep budget accounting and raw provenance. Test interruption before/after raw persistence, normalization and checkpoint publication. Exactly-once remote billing is not promised.

### 6. Medium: module ownership is exposed but downstream lifecycle enforcement remains incomplete

Locations: `scripts/route_workflow.py:314–317`; `scripts/subprojects.py:59–81`; `references/modules/`; `.claude/hooks/precompact.py` and `postcompact.py`.

The router emits a separate `module_reference`; it is not included in `required_references`, the field the caller is instructed to load. The module map covers only some specialists. Marketing's workstream is initialized but no ongoing publication/validation consumer was found. Initialization can mark an empty default brief as `briefed`. `start()` resolves a registered target but writes through the default `PATHS[name]`, so registered custom destinations need a regression check.

The existing compaction hooks do not deliver the planned session-specific modern-layout restore. These limitations are mostly acknowledged in the implementation record.

**Required repair:** complete the existing four ownership contracts and their consumers. Make applicable module guidance part of the required reference packet; validate imported decisions when consumed; keep current workstream state through publication; honor registered paths and session identity. Avoid introducing another router.

### 7. Medium: research design and provider authorization remain inconsistent across entry points

Locations: `scripts/evidence_scout/plan_customer_feedback.py`; associated research-design schema; `.agents/skills/evidence-scout/references/workflow.md:270,298`.

Decision-question fields exist but are optional, so legacy-style plans can still omit the intended design for substantive new research. Some workflow instructions still condition paid enrichment on fresh approval despite standing authorization elsewhere.

**Required repair:** require or explicitly reuse an applicable question design for substantive research, while retaining focused-lookup and historical-read compatibility. Remove conflicting approval prompts for authorized customer-evidence collection. Preserve separate authorization for advertising and outreach.

## Phase status against the approved plan

| Phase | Current assessment | Outstanding completion evidence |
| --- | --- | --- |
| P0 evaluation baseline | Scaffold only | Frozen reviewed packets, defensible baseline, calibrated reviewers, adoption rule |
| P1 capture/resume | Useful partial delivery | Operation-level recovery, retry dispositions, fault-injected integrity |
| P2 decision questions | Fields and propagation added | Consistent substantive entry-point use and meaningful question quality |
| P3 episodes/findings | Structural support added | Comparative episode interpretation; observed-versus-inferred chronology; contradictory/multilingual examples |
| P4 verification/closure | Material acceptance gaps | Findings 1–3 repaired and tested through full workflows |
| P5 report quality | Template improved | Semantic support and completeness of the actual final report |
| P6 modules | Partial routing/scaffolding | Required guidance, workstream consumers, current handoffs, compaction recovery |
| P7 comparative quality | Not delivered | Saved outputs and independent assessments, including Branding/Marketing/Website |
| P8 provider extraction | Deferred appropriately | Extract only where a concrete maintenance benefit warrants it |

## Project-specific skills

### Move `town-db-curator` to its owning project

This skill is specifically about the Italian-town database. Its description names `projects/italy-town-db/`, which is absent in this checkout. The actual scripts resolve data under **`projects/us-retirees-italy/digital-assets/town-db/`** (`scripts/town_db/db_common.py:18`), which exists. It is therefore tied to the US-retirees-in-Italy project.

Current global exposure: `.agents/skills/town-db-curator/`, `scripts/town_db/`, `config/skill-catalog.json`, `config/workflow-routes.json`, and the town route expectation in `tests/test_skill_route_coverage.py`.

Recommended destination:

```text
projects/us-retirees-italy/
  AGENTS.md                           # Project entry and local skill pointer
  .agents/skills/town-db-curator/      # Instructions, references, local evals
  scripts/town_db/                    # Project-owned commands and seed/schema
  digital-assets/town-db/             # Existing data stays here
```

**Migration requirements:**

1. Establish versioned ownership first. `.gitignore:44` excludes `projects/`; moving tracked code there without a project repository or a narrow tracking arrangement would remove it from maintained distribution.
2. Rehearse on a copy. Rebase script root discovery, command references and the stale skill path. Preserve DB contents and source provenance; do not reinitialize the live database.
3. Ensure project-local loading works for each configured harness and when entering the project from the parent workspace. Explicit project instruction loading is an acceptable mechanism; do not assume every harness discovers nested skills the same way.
4. Remove its global route/catalog entry and adjust parity tests only after local discoverability and commands work. Do not preserve a globally advertised alias that silently writes into one project.
5. Put fixture-based curation evals with the project: dated source writes, stale-field reporting, export/shortlist correctness and no cross-project writes. A missing global eval is not a reason to keep a project-specific skill global.

### Keep the remaining reusable skills shared

The scan found no other entire skill whose purpose clearly belongs to one concrete project. Domain specialization alone is not project specificity: `saas-fintech-pilot-designer` and `service-customer-perspective-challenger` can serve multiple ventures.

Three shared references cite named project research:

| Shared skill | Project-bound reference | Adjustment |
| --- | --- | --- |
| `archetype-gtm-strategist` | `references/evidence-base.md` cites `projects/founder-gtm-playbooks/` | Retain shared sourced distillation; mark extended project research as optional provenance |
| `social-digital-marketing-planner` | `references/social-digital-marketing-research.md` cites the same playbook project | Ensure the maintained shared reference contains all required guidance |
| `service-customer-perspective-challenger` | `references/evidence-base.md` cites `projects/european-german-us-service-customer-psychology/` | Keep reusable lessons and direct sources available independently of the ignored project |

Historical examples may remain clearly labelled. A clean checkout must not need an unrelated local venture folder to perform a shared skill. This is a scope/dependency review, not a live portability certification of every command in all 39 skills.

## Recommended order

1. Correct the acceptance boundaries and evaluation false passes, then update completion claims.
2. Finish authorized recovery, module and evaluation work from the existing plan.
3. Relocate town curation with explicit versioned project ownership.
4. Add the selected SaaS discovery approaches using the [extension plan](../agent-improvements/2026-09-23-saas-discovery-approaches-plan.md), reusing existing owners and evidence contracts.
