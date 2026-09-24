# Analysis-quality implementation record

Date: 24 September 2026

## Delivered

- **P1, capture integrity:** transcript payloads and provenance persist; social platform allowances are allocated explicitly; normalized provider batches and run settings are checkpointed; collection can resume only against the same plan/settings; request/enrichment allowances survive resumption; JSON state writes use atomic replacement.
- **P2, question design:** customer-feedback plans can record decisions, stable question IDs, known facts, hypotheses, alternatives and distinguishing observations. Query rows and evidence memberships retain question associations. No extra paid-evidence approval prompt was added.
- **P3, episodes and findings:** experience ledgers retain chronology and resolution metadata and can emit comparison views. VOC synthesis v3 adds study/question linkage, candidate support and review fields while historical v1/v2 remain readable.
- **P4, claim checks and gate integrity:** claim verification is digest-bound to claim/evidence/review inputs; finding-to-claim links are validated. Ordinary problem-validation closure now requires current workspace-local, dated, sourced artifacts for customer segments, journey and pain points; the route checks the receipt. The report/claim finalizer binds new candidate-bearing completion to the study and report bytes.
- **P5, output guidance:** the discovery report template removes unsupported severity-times-frequency scoring and requests bounded findings with consequences, alternatives, counterevidence and scope.
- **P6, modular ownership:** Marketing has an explicit `marketing/` destination in new layout-3 projects, a versioned brief-bound workstream file, a module reference and router ownership. Independent Marketing inside a project requires a supplied standalone brief. Four short module references describe Research, Branding, Marketing and Website ownership. Research entry points preserve idea-validation versus segment-pain intent, explain when to use distinct evidence packets, and keep foreign companies optional comparables rather than a default idea-import objective.
- **P6, compaction recovery:** replaced the shared all-workspace resume file with atomic per-session snapshots, persisting the checked project/module/case/run selection when the route dispatches. The resolver prefers case state, respects registered module destinations, and avoids inferring a case from repo-root cwd. PostCompact stores the compact summary; SessionStart injects only that session's checkpoint, including open question and accepted decisions. Local contract coverage does not establish live host behavior.
- **Project-specific skill ownership:** moved `town-db-curator` and `scripts/town_db/` into `projects/us-retirees-italy/`, corrected the database root path, added local instructions and evals, exposed the local skill to Claude Code by scoped symlink, and removed its global catalog and route entries. The town database remains ignored and local.
- **P0/P7, evaluation scaffolds:** added synthetic-only source packets for the 12 grouped Research tasks and two packets each for Branding, Marketing and Website, with tailored dimensions/critical errors and configurable split counts. Packets now include generation inputs, isolated reviewer keys, and clearly illustrative paired outputs. The offline validator checks selected manifests, packet assets, output/trace hashes and blinded reviewer records. All remain `design_only_packets_and_scores_pending`; illustrative outputs are not actual agent outputs, customer evidence, or independently reviewed gold labels.
- **P0 eval false-pass repair:** empty ratings, unknown task IDs and incomplete panels no longer produce a quality pass. Comparison uses per-dimension Pareto outcomes so a gain cannot hide a regression in another dimension. `--allow-subset` is explicitly exploratory and cannot make the evaluation decision-ready.
- **Problem assessment workflow:** added a builder for a reviewed, hash-bound assessment tied to current segment/journey/pain artifacts, study identity, VoC pack, finding IDs and linked claims. The commitment gate verifies this contract and its underlying VOC/claim validators; only a reviewed `supported` assessment passes the ordinary Business commitment gate. An insufficient-evidence discovery can still close as research without authorizing a Business commitment.
- **Intent-preserving research approaches:** customer-feedback plans record whether the task is idea validation or customer-problem understanding and create isolated packets for selected complementary approaches. The required workflow starts from the user's idea/topic; domestic or foreign companies are optional comparative evidence, not a default idea-import objective. A shared reference documents switching, decision-participant, actual-alternative and ecosystem lenses.
- **Marketing workstream lifecycle:** registered Marketing destinations are honored; workstream briefs, imported decisions and outputs are hash-bound and path-contained. Stale input blocks routing until an explicit reviewed refresh; publication updates outputs and workstream revision together. Applicability and approval scope are surfaced to the specialist for review rather than guessed automatically.
- **Competitor-change analysis:** added an offline, versioned change-to-customer-hypothesis contract requiring dated before/after snapshots, comparable fields and hashes. It distinguishes supplier announcements from customer evidence and emits the next customer verification step; it does not infer demand from product/hiring changes or schedule monitoring.
- **Founder playbook intent:** foreign-company cases support validation of the user's selected idea or investigation of a segment's pain; importing an idea is only in scope when explicitly requested.

## Validation

- Focused evidence, gate, routing, synthesis, monitoring, compaction and evaluation regressions: **112 passed**.
- Full Python suite after integration: **866 passed** outside the sandbox.
- `scripts/validate_skill_routes.py`: passed.
- `scripts/validate_analysis_eval.py`: passed for Research (12 tasks) and Branding, Marketing and Website (2 tasks each), all in design-only state.
- `scripts/run_evals.py`: structural checks passed for **173 eval cases across 38/38 global skills**; the project-local town curator has two scoped eval examples.
- Skill-creator quick validation passed for the updated founder-playbook skill.
- `git diff --check`: passed after removing trailing whitespace.
- Python compilation for the changed collector, gate, query, ledger, validator, router and evaluation modules: passed.
- Marketing workstream initializer and manifest schema: valid; its subproject, router and runtime regressions passed (20 tests in the final focused group).
- No live provider or model calls were made. No research workspace or prior study was migrated or rewritten; only the curator code and agent instructions moved.

## Still open

- **P0/P7:** illustrative packets now support a prospective comparison, but old/revised actual agent outputs, independent blind ratings, reviewer calibration and a frozen adoption threshold are absent. The pre-change analytical baseline was not captured; retrospective comparison is impossible. Analytical benefit remains unproven; no model calls were made.
- **P1:** provider-batch recovery merges prior partial records and records interrupted attempts, but recovery has not been fault-injected at every individual query/raw-capture boundary. Some providers use SDK/subprocess paths outside the shared HTTP counter, as documented in the plan. Exactly-once remote billing is not claimed.
- **P2/P3:** research-question design and claim links have structural support, but the complete workflow has not yet been exercised on independently labelled multilingual and contradictory source packets. Evaluation is required before claiming better synthesis.
- **P4/P6:** Marketing handoffs now have freshness and explicit review bindings. Other arbitrary handoff consumers do not yet share this full protocol; scope compatibility is human-reviewed from the dispatch packet, not semantically matched by code. Historical override events remain non-reusable.
- **P6:** compaction selection, current case/module resolution and session isolation have local regression coverage. Live Claude host behavior remains unverified.
- The town-curator move has structural evals but no live model evaluation.
- **P7b:** Branding, Marketing and Website now have synthetic evaluation packets, but paired outputs and independent comparisons have not been run.
- **P8:** provider extraction remains deferred because this implementation did not establish a concrete maintenance benefit that justifies the migration surface.

Remaining limitations are substantive quality/evidence work, so the implementation is locally complete but analytical benefit is still unmeasured. Structural test success does not establish better interpretation, customer demand, live provider behavior or deployment behavior.
