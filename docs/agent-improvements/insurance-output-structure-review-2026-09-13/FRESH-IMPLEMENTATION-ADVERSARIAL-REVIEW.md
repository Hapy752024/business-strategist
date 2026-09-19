# Fresh implementation adversarial review

13 September 2026. **Verdict: BLOCK for full-plan acceptance and default rollout.** The central case publisher is useful and its existing regressions pass, but normal repository CLIs still escape the promised output/publication boundary, generated assessments lose explicit source dependencies, and numerical narratives can be published with contradictory current conclusions. These are implementation failures, not reasons to redesign the plan or add a framework.

I read `AGENTS.md` and the preserved approved Revision 2 plan first, independently derived the checklist below, and inspected code before reading `IMPLEMENTATION-REPORT.md` or the saved semantic review. I did not use earlier code-review findings as my checklist. This is an implementation conformance review. No implementation, live project, credential, network, paid-provider, commit or subagent actions were performed. Only this report and disposable `/tmp` reproductions were written.

## Independent requirement coverage

“Partial” means some positive implementation evidence exists, but the approved acceptance condition is not closed.

| Approved requirement | Coverage | Evidence / remaining gap |
|---|---|---|
| Identity-only registry, stable case IDs, lazy folders, nullable single selection | Substantially implemented | Version-2 initialization, explicit registration/rename/clear and generation-bound selection exist; case tests pass. Registry does not duplicate case stage state. |
| A→B→A, unrelated B updates, stale handoffs, revision-scoped overrides | Implemented in central paths | Case, route, selected-plan and handoff regressions pass; selection is checked before overriding evidence prerequisites. This does not establish coverage of all downstream writers: F1. |
| Case-local checkpoints and explicit shared/source applicability | Partial | Local artifact containment and digests exist; normal landscape inputs never enter checkpoint source-use bindings: F3. |
| All output conflicts and symlink escapes rejected before writing | Failed | Two normal CLI reproductions violate this: F2. |
| One locked publication protocol, pending refusal, snapshots and recovery | Partial | Central publication/recovery tests pass, including rollback preservation and committed recovery. Official brand/website and strategy-freeze writers remain outside the protocol: F1/F5. |
| Shared-source interpretation corrections invalidate every consuming case | Failed end to end | Explicitly bound cases invalidate; a normal derived landscape consumer is missed: F3. |
| Exactly one bounded appraisal mode and narrative owner | Mostly implemented | Explicit route and ambiguous old skill alias are enforced; shared reference/templates exist. Packet supplies a case output root and contract descriptions, but not concrete requested-section data or an allowlist of resolved destination paths. |
| Customer choice, spend, reach/repeat value, delivery, disconfirmation | Implemented as guidance; bounded semantic evidence | Shared assessment reference covers these dimensions. Saved synthetic narratives demonstrate restraint on several false-positive evidence types. No broad research-quality claim follows. |
| Comparable current case overview and usable history | Partial | Current-case links and snapshots exist. Root overview is a navigation table without comparison conclusions; see F7. Snapshot-relative source links are preserved as bytes but are not automatically usable from their new location. |
| Transactional and recurring economics, null unknowns, cash timing and digest validation | Partial | Main arithmetic fixtures pass; narrative refresh is not enforced (F4), and several approved economic dimensions remain absent (F6). |
| Selected root business plan, structured strategy authority and source bindings | Mostly implemented in publisher | Nine coverage sections, prior-plan digest conflict check and execution binding exist. Selected-plan consumers are incompletely adapted: F1/F5. |
| Evidence-based MVP/pilot scope-amendment rule | Missing | Existing pilot procedure/output contract has not gained the approved amendment requirement: F8. |
| Legacy continuation, explicit copy migration and no inherited umbrella passes | Substantially implemented in case/router paths | Migration and legacy continuation tests pass; saved insurance rehearsal preserves source/run hashes and does not transfer passes. Downstream legacy writer coverage is not complete: F1. |
| Full producer audit before default enablement | Failed | Version 2 is already the default despite F1–F3/F5. The implementation report’s producer table omits concrete skill-local writers. |
| Real semantic responses, saved assertions, corrections and fresh input handoff | Bounded partial acceptance | Actual saved agent-authored responses and separate review exist. Final-contract replay reused text; model version was unknown; numeric stale-prose case and actual downstream consumers were not covered. |

## Confirmed findings

### F1 — High: official downstream writers ignore enclosing case authority and pending publication

**Locations:** `.agents/skills/brand-workspace-manager/scripts/workspace_cli.py:113`, `:121`, `:131`, `:133`; `.agents/skills/brand-workspace-manager/scripts/manage-brand-workspace.py:23`, `:45`; `.agents/skills/brand-website-designer-builder/scripts/scaffold-site.mjs:6`, `:11`, `:13`, `:25`.

The approved plan explicitly includes downstream brand/website writers and requires pending refusal, current execution selection/bindings and shared publication. These official writers have not been adapted. `workspace_cli.py create` treats `--base-dir` as standalone without checking whether its destination is inside a versioned business project. Even its `--project` branch creates directories, copies a snapshot and writes the brand manifest **before** calling the project link checker. The business-linked branch checks that a supplied handoff is a file, rather than validating its selection/source binding. The website scaffolder has no enclosing case/pending check.

**Reproduction:** `/tmp/fresh-case-adversary.py` created a versioned project with selection null and intentionally left a real pending publication through the publisher’s fault hook. Both commands exited 0:

```bash
python3 .agents/skills/brand-workspace-manager/scripts/workspace_cli.py create --name branding --base-dir /tmp/fresh-case-adversary/downstream/topic
node .agents/skills/brand-website-designer-builder/scripts/scaffold-site.mjs /tmp/fresh-case-adversary/downstream/topic/web-site
```

The first wrote `branding/brand-manifest.json`; the second wrote `web-site/scaffold-command.txt` and support folders. The pending operation remained unresolved. No package installation was requested or run.

**Expected:** discover the containing authority from the destination as well as caller metadata; reject pending/no-selection/stale-input case work before any write. Preserve genuine standalone behavior outside business projects. Carry the current binding through subsequent brand mutation/promotion paths and use the project publication contract for versioned current state. These are ordinary supported repository CLIs, not an attempt to prohibit arbitrary filesystem access.

### F2 — High: output preflight can be bypassed by a legacy workspace, and default run paths write through symlinks

**Locations:** `scripts/evidence_scout/workspace.py:623`–`:627`, `:694`–`:703`; `scripts/evidence_scout/build_landscape_artifacts.py:132`, `:156`; `scripts/evidence_scout/discover_market_problems.py:149`–`:165`.

There are two confirmed failures of the same required before-write boundary:

1. `prepare_research_output()` locates either the explicit workspace or the output, not both. If `--workspace` is legacy, it returns before inspecting a versioned destination. A normal landscape CLI with a legacy `--workspace` and an already populated case `--out-dir` exited 0 and replaced the original case-run matrix. It also treated the new outputs as legacy stage evidence. The existing immutable-run guard was never reached.
2. `resolve_run_dir()` calls `cases.safe()` only for explicit `--out-dir`. Its default branch creates the run directory and writes `.case-context.json` through any symlink inside the research path. Discovery writes its reports before stage validation finally detects the symlink.

**Reproduction evidence:** `/tmp/fresh-case-adversary/results.json`, key `builder_conflicting_workspace`, reports `returncode: 0` and `original_run_preserved: false`. The actual command used the checked fixture source from F3, a disposable legacy workspace, and the existing versioned run at `dependency/topic/cases/a/market_research/solution_alternatives/runs/derived`.

`/tmp/fresh-case-adversary-symlink.py` made case A’s `market_research/market_discovery` a symlink to a sibling `/tmp` directory and ran:

```bash
python3 scripts/evidence_scout/discover_market_problems.py --topic 'Synthetic topic' --workspace /tmp/fresh-case-adversary/symlink/topic --case a
```

It exited 2 with `Project paths must not be symlinks`, **after** creating `.case-context.json`, `market-discovery-report.md` and `research_plan.md` outside the project. See `/tmp/fresh-case-adversary/symlink/results.json`.

**Expected:** resolve and reconcile every explicit workspace/output authority; validate the final default or explicit destination, including all symlink components, before creating anything. Add normal-CLI no-write regression assertions, not only helper exception checks.

### F3 — High: normal shared-input builders lose the dependency needed for corrections

**Locations:** `scripts/evidence_scout/build_landscape_artifacts.py:135`, `:138`, `:183`–`:189`; `scripts/evidence_scout/workspace.py:396`–`:399`; `scripts/case_workspace.py:633`–`:639`.

The landscape builder reads an explicit `--entities-json` and optional `--marketing-json`, but its checkpoint binds only its generated output files. It neither requires an applicability declaration for shared/cross-case inputs nor records their checked digests. `correct --source` searches only stored case/stage/plan bindings, so the known input dependency disappears. A same-byte interpretation correction becomes a committed decision with no affected case.

**Reproduction:** the offline landscape fixture at `/tmp/fresh-case-adversary/dependency/topic/market_research/shared-entities.json` was supplied to the ordinary builder with `--workspace <topic> --case a`. It exited 0 and passed `competitive_landscape`. All eight stored bindings point to generated case outputs; none points to the shared input. Calling `correct(..., source_path='market_research/shared-entities.json')` then left A’s assessment revision **1 → 1** and its stage **passed → passed**. Exact commands/setup and captured bindings are in `/tmp/fresh-case-adversary.py` and `/tmp/fresh-case-adversary/results.json` (`shared_builder`).

**Expected:** normal writers must bind their declared source inputs, including applicability and input revisions/digests, before allowing derived assessments to pass. Corrections must follow those dependencies. This is not asking the system to discover an undeclared semantic relationship: the missing input was explicitly provided to its own CLI. Apply the same audit to entity, whitespace and interview-derived outputs.

### F4 — High: fresh economics are stamped onto stale numerical narratives without rejecting the contradiction

**Locations:** `scripts/case_workspace.py:498`–`:506`, `:521`–`:525`; selected-plan rendering at `:570`–`:587`.

Recalculating `economics.json` is correctly automatic, but there is no authored narrative input-digest binding or refresh acceptance check. The publisher blindly appends the **new** digest and calculated summary to whatever prose it receives. The appendix does not make the original claim current.

**Reproduction:** two normal `case_workspace.py appraise` invocations succeeded. First, the synthetic 100 revenue / 50 contribution model accompanied prose stating “Contribution is EUR 50 per completed sale; 80 completed sales are required per month.” Second, revenue changed to 150 while that authored prose was resubmitted unchanged. Current `business-case.md` now says both:

> Contribution is EUR 50 per completed sale; 80 completed sales are required per month.

and:

> Calculated contribution per unit: 100.0. Required monthly sales: 40. Capacity meets target: True.

It is stamped with the new economics digest. Both CLI exit codes were 0. See `/tmp/fresh-case-adversary-more.py` and `/tmp/fresh-case-adversary/more/results.json`.

**Expected:** the approved plan requires recalculation **and affected narrative refresh**, with current narratives bound to the same inputs/results. Use explicit numerical/section bindings or a bounded acceptance check; leave the affected narrative review-required until refreshed. Do not rely on appending conflicting numbers. Add this case to the actual semantic acceptance fixture as well as publication regressions. The same vulnerability exists when arbitrary selected-plan section text is rendered beside the calculated economics appendix.

### F5 — Medium: strategy freeze remains an unrestricted cross-case writer outside publication

**Locations:** `scripts/strategy_review.py:79`–`:85`, `:101`–`:115`.

The CLI checks the source plan under the project lock, releases the lock, then writes any requested destination with `open('x')`. It does not resolve the destination’s authority/purpose, bind the baseline to publication metadata, or protect the check-to-write interval. Source validation is not destination authorization.

**Reproduction:** a current selected A plan was frozen into B with exit 0:

```bash
python3 scripts/strategy_review.py freeze --plan /tmp/fresh-case-adversary/publication/topic/strategy/strategy-plan.json --output /tmp/fresh-case-adversary/publication/topic/cases/b/new-baseline.md
```

B received A’s executable plan data; the project manifest stayed at revision 11 and no publication/decision recorded this write. See `freeze_cross_case` in `/tmp/fresh-case-adversary/results.json`. The path did not previously exist, so no overwrite was necessary to demonstrate the scope violation.

**Expected:** maintain standalone exports where allowed, but enforce case-purpose containment for outputs within a versioned project and publish tracked baselines under the same authority. Recheck inside the write/publication lock. An input outside a case project must likewise not bypass validation of an output inside one.

### F6 — Medium: the approved economic contract is narrower than claimed

**Locations:** `scripts/case_economics.py:50`–`:62`, `:130`–`:145`, `:155`–`:170`; `references/case-assessment.md:31`.

These are confirmed missing contract dimensions, not alleged arithmetic mistakes in the existing 50-contribution fixture:

- The only double-count check is acquisition-in-service cost. There is no supported input/status distinction for imputed founder labor versus owner compensation, nor a check for owner labor already included in service expense. A prose warning cannot provide the approved executable double-count regression.
- Recurring monthly rows expose recognized revenue, receipts/payments, cash and workload, but no monthly contribution calculation. Cash payments mix fixed/owner/startup payments with timing-shifted variable costs, so they cannot substitute for monthly contribution.
- Base-only input is accepted with no downside/sensitivity record or explicit reason for missing scenarios. The approved plan asked for base/downside and decision-changing sensitivities; the implemented contract describes downside as optional.

The helper also accepts arbitrary unused input keys. An exploratory probe with extra founder-labor fields was retained in the input digest but had no effect on results; those invented field names are **not** claimed to be a supported interface. The finding is the absence of the approved supported representation and checks.

**Expected:** add only the missing bounded definitions/calculations or explicitly mark unsupported dimensions unresolved. Reject unknown inputs that appear to be modeled. Cover owner-labor accounting and recurring monthly contribution with meaningful fixtures; do not expand into a finance framework.

### F7 — Medium: the generated root overview cannot preserve the required current comparison

**Locations:** `scripts/case_workspace.py:151`–`:166`, `:218`; `templates/project/case-README.md:7`.

`overview()` renders titles, selection and links based on file existence. It never consumes current findings, decision summaries, readiness, principal uncertainty or comparative conclusions. Every publication replaces root `README.md` with this fixed table, so an agent-authored comparison placed there is lost. The saved semantic exercise instead has a separate `run/final-comparison.md`; that does not implement the project’s canonical current comparison.

**Observed:** the reproduced root overview lists `[Read]` and `Not assessed` but no case comparison; it displays the same links when an assessment has become a review-required placeholder. See `/tmp/fresh-case-adversary/more/results.json`, `root_readme`.

**Expected:** retain a concise current comparison at the canonical root overview, derived from current case-owned assessment data without duplicating stage authority or choosing a winner automatically. Keep the detailed prose in case assessments. Expose review-required status in the overview so link existence does not look like completed assessment coverage.

### F8 — Medium: the MVP/pilot amendment requirement was not added

**Location:** `.agents/skills/saas-fintech-pilot-designer/references/workflow.md:94`–`:105`, `:124`–`:138`.

The approved package 4 requires a new feature to show that it enables the chosen outcome or required trust, together with cost/capacity consequences. The current pilot procedure asks for scope/non-goals, metrics and agreements, but contains no feature-amendment criterion, evidence requirement or associated cost/capacity decision. Searches of the pilot skill and its references found no implementation of that rule. This is a missing planned workflow improvement, independent of the case infrastructure findings.

**Expected:** put the compact amendment contract into the existing pilot output/procedure and verify a proposed feature expansion against it. No new skill or stage is needed.

## Verification, semantic evidence and limits

I ran the five new case suites directly: **32 passed**. I then independently ran `python3 scripts/validate_skill_routes.py`, `bash scripts/validate_setup.sh` and `python3 scripts/run_evals.py` with bytecode disabled. All completed successfully. Setup ran the full Python suite: **350 passed**. Structural evaluation reported **143 cases, zero structural errors**. The existing town-db-curator checklist/evaluation coverage warnings remain. Passing these checks does not cover the failures above.

Reproduction setup and captured outputs remain in `/tmp/fresh-case-adversary.py`, `/tmp/fresh-case-adversary-more.py`, `/tmp/fresh-case-adversary-symlink.py` and `/tmp/fresh-case-adversary/`. They import existing synthetic fixtures and run normal CLIs; use a fresh disposable base path for another run. No provider calls occurred.

I inspected the saved semantic task prompt, host metadata, actual responses/publication inputs and separate assertion review. The evaluation is real but limited: exact runtime model/version was unavailable, corrections were disclosed in the initial prompt, and the final publication-contract replay reused saved text. Its ten assertions support cautious interpretation of fixed synthetic evidence and no implicit selection. They do not cover numerical narrative refresh (F4), a fresh downstream specialist executing solely from the checked packet, or the omitted writer paths. I do not treat the saved reviewer’s PASS as full implementation acceptance.

The central recovery implementation and passing tests are positive evidence. I did not independently inject a crash during rollback, and the inspected new tests exercise `pending`, first `replace` and `commit`, not every specifically requested interruption point. The insurance copy rehearsal records interruption/rollback/retry, source hash preservation and selection switching; it is structural migration evidence, not reassessment of case findings. I did not rerun a live migration or refresh any market claim.

Additional static concern, not needed for the BLOCK verdict: checked route packets generally return `output_root=cases/<id>` even for root-output specialists, and appraisal input metadata names “requested sections” without supplying structured section values or resolved destination allowlists (`scripts/route_workflow.py:321`). The saved appraisal exercise does not establish that a fresh root-plan/website specialist resolves those competing destination cues correctly. A focused handoff test should settle this instead of assuming the packet is sufficient.

## Acceptance decision

Fix F1–F5 and rerun their normal-CLI no-write/dependency/narrative cases before treating the case path as complete or default-ready. Close F6–F8 as approved scope, or obtain an explicit scope change and accurately mark what remains unavailable. Preserve the existing positive implementation and migration evidence, but keep structural, semantic and producer-boundary acceptance separate. The current default at `scripts/evidence_scout/workspace.py:142` is premature under the approved rule that a partial implementation stays experimental.

Durable copies of reproduction scripts and captured results: [review evidence](implementation-evidence/fresh-adversarial-review/). Original temporary paths in captured output are retained as provenance.
