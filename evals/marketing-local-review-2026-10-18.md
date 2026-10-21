# Local marketing implementation review — 2026-10-18

Original disposition: changes requested before relying on the recurring local workflow. The review found five reproducible P2 defects and made no implementation changes or account operations. The subsequently authorized corrections are recorded below; all five findings are now closed for the local implementation.

Scope: P0/P1/minimum P2 campaign configuration, export transforms, report preparation/finalization, shared Marketing publication, task continuity, routing and declared claims. Existing unrelated website changes were excluded. Live credentials, account permissions, scheduling and external execution are unimplemented and were not evaluated. No model-quality or marketing-outcome conclusion follows from these checks.

## Findings

### MR-01 — P2: Campaign validation intercepts unrelated review files

Location: `scripts/subprojects.py:91` and `scripts/marketing/artifacts.py:21`.

The artifact dispatcher selects the campaign validator by basename alone. Existing customer-question source evidence uses `sources/review.json`; the new validator rejects it because its path does not begin with `campaigns/<id>/`. This prevents publication and restoration of valid existing Marketing evidence and marks an already published workstream invalid during resume.

Reproduction: `python3 -m pytest -q tests/test_customer_questions.py::test_publication_staged_sources_refresh_and_resume` fails at the first publication with `campaign artifact has an invalid location`. Replacing only `subprojects.marketing_artifact_errors` in memory with the function from `HEAD:scripts/subprojects.py` makes the same test pass. No source file was changed for that control.

Fix: dispatch on the canonical campaign namespace and exact artifact locations; handle root `connections.json` explicitly. Preserve existing source-review validation. Regression should cover initial publication, resume and exact-byte restoration of customer-question evidence.

### MR-02 — P2: Late corrections supersede the wrong report

Location: `scripts/marketing/review_cycle.py:210`–`218`.

Restatement detection compares only with the last published period, and `supersedes` always points to that last report. Publish January 8–14, then January 15–21, then a later export for January 8–14. The resulting pointer reports `restatement: false`, supersedes January 15–21 and moves the current period backwards to January 8–14. The rendered report contains no restatement label. A genuine correction to earlier conversions can therefore be presented as a new weekly result; subsequent comparisons are not marked for reconciliation.

Fix: find prior revisions by reporting period/source identity, link the correction to the matching occurrence, distinguish the latest reporting period from the most recently processed revision, and render correction status. Recompute affected comparisons or explicitly mark them pending. Test out-of-order corrections after at least two published weeks, including unchanged latest-period behavior and visible revised conclusions.

### MR-03 — P2: Fresh review silently carries an unusable stale task

Location: `scripts/marketing/review_cycle.py:151`–`158`; acceptance enforcement: `scripts/marketing/campaign.py:162`–`163`.

Publish a proposed task, update the campaign offer through the publisher, then prepare/finalize a fresh review containing the identical task proposal. Finalization succeeds and the report lists the task as due, but acceptance fails with `task context changed; review a new follow-up task before accepting or completing it`. The carry branch compares proposal fields without checking the stored context hash, and retains that stale hash.

Fix: reject stale carried proposals with actionable recovery, or explicitly create a reviewed replacement and retire/supersede the stale task. Preserve the requirement for renewed owner acceptance; do not silently restore authority. Reports must not list unusable stale tasks as ordinary due work. Test offer and claim-registry changes followed by fresh review and task acceptance.

### MR-04 — P2: Campaign finalization removes existing owner instructions

Location: `scripts/marketing/review_cycle.py:208`–`218` and `224`–`234`.

Finalization discards the owner output from `execution.render()` and overwrites the shared `owner-actions.md` using a reduced renderer. Existing tasks lose their dependency blockers, exact `user_step`, destination and prepared-material links. Reproduced with a valid v2 `submit_listing` task awaiting owner action and an incomplete prerequisite: after a campaign review with no new tasks, the workstream still validates, but all four pieces of guidance disappear from its owner summary. The underlying execution JSON retains them.

Fix: reuse the existing owner packet rendering contract or preserve all its fields and dependency checks in a shared renderer. Test a mixed queue containing both preexisting delivery tasks and recurring campaign work.

### MR-05 — P2: Snoozed tasks hide due work in the owner summary

Location: `scripts/marketing/review_cycle.py:227`–`234`.

`owner_actions()` takes the first three unfinished tasks in insertion order before considering snooze dates. With three tasks snoozed into the future and a fourth due now, the owner summary shows only the snoozed tasks and a generic extra-task count. The weekly report uses a different due-task filter, so the two owner views disagree.

Fix: select actionable due tasks before applying the three-task display limit, summarize deferred work separately, and share selection logic with the weekly report. Test future and expired snoozes plus more than three outstanding tasks.

## Verification

- Original affected suite: **72 passed** (`test_marketing_campaign_cycle`, `test_marketing_execution`, `test_marketing_observations`, `test_seo_routes`, `test_case_routes`, `test_skill_route_coverage`).
- Additional shared-publication suite: **95 passed, 1 failed** (`test_creative_evidence`, `test_customer_questions`, `test_gap_closure`, `test_link_observations`, `test_seo_earned_media_flow`, `test_seo_review_fixes`). The failure is MR-01, not an unrelated baseline failure; the in-memory previous-dispatcher control passed.
- `python3 scripts/validate_skill_routes.py`: passed.
- `git diff --check`: passed before review-record edits; rechecked after recording findings.
- Temporary synthetic probes reproduced MR-02 through MR-05. MR-04 was additionally reproduced end to end through validated publication and finalization with a valid v2 source queue. No private project data was used.

The existing tests establish useful local invariants but do not cover these lifecycle and compatibility cases. The 2026-10-17 delivery receipt remains a historical record of its narrower checks; it does not establish current review acceptance.

## Correction verification — 2026-10-18

The user subsequently requested correction of all five findings. Implementation and regression coverage now establish:

- MR-01: campaign validation dispatches only in its namespace, with root connection configuration handled explicitly. Exact artifact locations are checked. Existing source `review.json` publication, resume and restoration pass.
- MR-02: ordered bound review history resolves revisions by source/account/reporting period. Corrections supersede the matching period, render their status, preserve the latest reporting period and flag affected comparisons until a new review uses the revised baseline. Tests also cover backfill, migration from pre-index reports, repairing an older incorrect latest pointer, foreign history rejection and immutable original reports.
- MR-03: re-proposing a stale task is rejected with explicit replacement instructions. Both owner views label stale tasks for context review and exclude them from due work. Tests cover offer and claim changes, explicit decline, replacement proposal and renewed acceptance.
- MR-04: a common owner renderer preserves precise steps, destinations, material paths/hashes and blockers through finalization and later task events. Valid preexisting v2 delivery tasks retain their instructions. Submitted work is marked for outcome review rather than repeated.
- MR-05: common selection logic chooses due tasks before the three-task limit, with separate deferred/blocked/context-review sections. Future and expired snoozes are covered in both views.

Verification: the combined 12-file Marketing/publication/router suite passed **175 tests**; two additional focused regressions for legacy-pointer repair/history scope and submitted-task rendering passed separately (**177 distinct tests total**, including nine newly added cases). `scripts/validate_skill_routes.py` passed. `scripts/evaluate.py check` returned deterministic PASS at `evals/local-runs/20261018T084645Z-56166f081de2/result.json`. `git diff --check` passed after the corrections and documentation update. No live accounts, scheduling, external publication/spend or independent model-quality trial were exercised. These fixes were checked locally; a new independent agent review was not performed.
