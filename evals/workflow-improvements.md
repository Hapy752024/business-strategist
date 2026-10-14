# Agentic workflow improvement log

Single shared record for failures, problems and improvement candidates across this repository. Instructions in `AGENTS.md` require agents to maintain this file. Existing evaluation suites remain the executable evidence; this file tracks what to review and improve.

## How to use

- Search by symptom and component before adding an entry. Repeated incidents update the same ID and history.
- Use the next `WF-NNN` ID. Priorities: P1 incorrect completion, evidence integrity or data exposure; P2 workflow reliability/correctness; P3 improvement opportunity. State the impact rather than relying only on priority.
- Status: `open`, `in_progress`, `blocked`, `deferred`, `resolved`. A blocked/deferred entry needs the condition for resuming. An implemented change remains in progress until its relevant verification passes.
- Separate observed behavior from suspected causes. Include a minimal reproduction or evidence link, expected behavior, affected scope, owner/next action and dated closure evidence. Unknowns remain unknown.
- Retain resolved entries and their history. Reopen on recurrence. Preserve other agents' edits; reread the affected section before updating it. Never retain secrets or private customer data.
- During a workflow review, prioritize open/blocked items by impact and recurrence; validate older evidence before choosing work. Logging does not itself authorize implementation or external actions.

## Review queue

| ID | Priority | Status | Area | Issue |
| --- | --- | --- | --- | --- |
| WF-001 | P1 | resolved | Placement evidence | Inert template anchor incorrectly completes a placement |
| WF-002 | P1 | resolved | Capture privacy | Rejected sensitive URL retained in failure record |
| WF-003 | P2 | resolved | SEO comparison | Aborted audit incorrectly resolves earlier defects |
| WF-004 | P2 | resolved | Marketing provenance | Opportunity stays current after its source changes |
| WF-005 | P2 | resolved | Public fetching | Trickled headers bypass total deadline |
| WF-006 | P2 | resolved | Evidence recovery | Original capture/observation cannot be restored transactionally |
| WF-007 | P2 | open | Research tests | Competitor-query warning expectation fails |
| WF-008 | P3 | open | Skill maintenance | Three existing skill entries exceed line budget |
| WF-009 | P3 | open | Review tooling | Provider/model identity diagnostic needs verification |
| WF-010 | P1 | resolved | Non-video contracts | Retry, preservation and audience gaps fixed |
| WF-011 | P3 | open | Model evaluation | Expired OAuth prevents live trials |

## Entries

### WF-001 — Inert template anchor completes placement

- First/last observed: 2026-10-11. Owner: Marketing evidence maintainer.
- Observed: `scope_complete=True` for a link inside `<template>`; Chromium found zero live anchors. Impact: false completed backlink.
- Expected/change: ignore template descendants, including nested templates and base elements, while retaining real anchors.
- Evidence: `tests/test_seo_review_fixes.py::test_inert_templates_cannot_complete_and_cannot_override_base`; `scripts/marketing/link_observations.py`.
- Next action/closure: resolved 2026-10-11; inert/nested/self-closing template regression and Marketing publication tests pass. This establishes parser behavior, not live SEO impact.

### WF-002 — Sensitive URLs retained after rejection

- First/last observed: 2026-10-11. Owner: Public-capture maintainer.
- Observed: a synthetic `?token=` value remained in failure observation source/final URLs despite fetch rejection. Impact: secrets could be written to disk.
- Expected/change: reject source and target before creating a record or output directory; sanitized CLI error.
- Evidence: `tests/test_seo_review_fixes.py::test_sensitive_url_is_rejected_without_artifacts_or_diagnostics`; `scripts/marketing/verify_links.py`.
- Next action/closure: resolved 2026-10-11; both source/target CLI regressions pass, with no output directory or synthetic secret in diagnostics.

### WF-003 — Aborted audit reports resolved defects

- First/last observed: 2026-10-11. Owner: Website audit maintainer.
- Observed: browser-launch failure with no measured pages marked a prior canonical defect resolved. Impact: false technical improvement report.
- Expected/change: record complete audit coverage and compared routes; incomplete/legacy coverage is non-comparable.
- Evidence: `tests/test_seo_review_fixes.py::test_failed_or_unknown_audit_coverage_cannot_resolve_defects`; `scripts/brand/compare_seo_audits.py`.
- Next action/closure: resolved 2026-10-11; comparison regressions and Chromium audit tests pass. Unknown/aborted coverage remains non-comparable.

### WF-004 — Opportunity provenance not validated on resume

- First/last observed: 2026-10-11. Owner: Marketing publication maintainer.
- Observed: source replacement kept workstream `valid_for_use=True`, while the opportunity validator rejected its digest. Impact: stale qualification can appear current.
- Expected/change: shared artifact validation covers singular/plural opportunity records at publication, source-only updates and resume.
- Evidence: `tests/test_seo_review_fixes.py::test_opportunity_provenance_checked_on_publication_source_change_and_resume`; `scripts/subprojects.py`.
- Next action/closure: resolved 2026-10-11; source-update rejection, unchanged manifest revision, stale resume detection and exact source restoration pass.

### WF-005 — Header trickling exceeds fetch deadline

- First/last observed: 2026-10-11. Owner: Public-fetch maintainer.
- Observed: a 0.1-second fixture took 0.322 seconds because each arriving header reset the inactivity timeout. Impact: untrusted endpoints can stall work beyond the declared deadline.
- Expected/change: every underlying header/body read uses remaining total transport time. OS DNS resolution remains an explicitly separate limitation.
- Evidence: `tests/test_seo_review_fixes.py::test_trickled_headers_obey_total_deadline`; `scripts/marketing/public_fetch.py`.
- Next action/closure: resolved 2026-10-11; trickled-header deadline and normal/redirected HTTP capture tests pass. OS resolver timeout remains a limitation.

### WF-006 — Original evidence restoration rejected

- First/last observed: 2026-10-11. Owner: Marketing publication maintainer.
- Observed: replacing corrupted bytes with the original digest-matching capture was rejected as an immutable rewrite; damaged observation failed before staged bytes were considered. Impact: normal transaction cannot recover valid historical evidence.
- Expected/change: compare staged restoration to historical digests, not damaged disk bytes; continue rejecting rewritten history.
- Evidence: `tests/test_seo_review_fixes.py::test_restore_original_evidence_without_rewriting_history`; `scripts/subprojects.py`.
- Next action/closure: resolved 2026-10-11; all four missing/corrupted capture/observation cases restore transactionally; alternate historical bytes are rejected.

### WF-007 — Competitor-query warning test failure

- First/last observed: 2026-10-11 during implementation validation. Owner: Research collector maintainer.
- Observed: `tests/test_research_query_expansion.py::test_competitor_plan_preserves_input_and_does_not_inject_english` expected warnings but received an empty list. Latest broad rerun after the review fixes: 1146 passed, 1 failed (2026-10-11). Cause not yet assessed; unrelated to SEO changes.
- Impact/next action: full validation is not green; reproduce on current code and reconcile intended locale/query behavior with the assertion. Do not remove the assertion merely to pass.
- Evidence: `docs/agent-improvements/2026-10-11-seo-and-earned-media-implementation.md`. Closure: pending.
- Recurrence 2026-10-11, shared-post agent review: unrestricted setup rerun produced 1147 passed, 1 failed, the same competitor-query warning assertion. Sandbox-only subprocess/browser/network failures cleared outside the sandbox. Evidence: `docs/agent-improvements/2026-10-11-shared-posts-review.md`. No fix attempted in this review.

### WF-008 — Existing skill entry line budgets

- First/last observed: 2026-10-11 during setup validation. Owner: Skill maintenance.
- Observed: evidence-scout 32 lines, idea-grill 31, market-problem-discovery 31 versus the 30-line entry budget. Reconfirmed by setup validation after the review fixes on 2026-10-11.
- Impact/next action: setup validation fails; compact or move detail to direct references without losing required guidance, then rerun the entry checks.
- Evidence: `docs/agent-improvements/2026-10-11-seo-and-earned-media-implementation.md`. Closure: pending.
- Recurrence 2026-10-11, shared-post agent review: setup again detected evidence-scout 32 lines, idea-grill 31 and market-problem-discovery 31 against the 30-line budget. Evidence: `docs/agent-improvements/2026-10-11-shared-posts-review.md`. No skill changes made.

### WF-009 — Independent review provider produced no findings

- First/last observed: 2026-10-11. Owner: Review tooling maintainer.
- Observed: review-with selected DeepSeek; sandbox and unrestricted attempts produced only an unrecognized-model diagnostic and no usable review before being stopped. Root cause unknown.
- Impact/next action: independent review evidence unavailable; reproduce provider/model resolution with sanitized diagnostics, then verify a bounded read-only review completes. Local inspection/reproductions must remain separately attributed.
- Evidence: the implementation review in this conversation; transient provider outputs under `.agent-review/deepseek/`. Closure: pending; no successful provider review is claimed.

### WF-010 — Non-video correction and evidence contract gaps

- Priority/status: P1/resolved. First/last observed: 2026-10-11. Owner: shared packet/Marketing/website maintainers.
- Observed: independent local reviewer reproduced exhausted rejected work becoming eligible by resetting state to pending, preservation silently skipped on redirect routes, and oversized-count ratio overflow. Cross-provider review found briefs could consume questions from a different reviewed audience.
- Impact: bounded corrections and evidence applicability could be bypassed; page audit could omit declared value checks.
- Fix/closure: exhausted pending/rejected units remain blocked, redirect preservation is rejected, overflow stays undefined, brief audience matches reviewed question segment. Synthetic regressions in `tests/test_source_work_packets.py`, `tests/test_website_browser_audit.py`, `tests/test_creative_evidence.py`, `tests/test_customer_questions.py`. Deterministic behavior only, not live research quality. Receipt: `docs/agent-improvements/2026-10-11-non-video-implementation-receipt.md`.

### WF-011 — Live workflow evaluation authentication failure

- Priority/status: P3/open. First/last observed: 2026-10-11. Owner: local Claude runtime maintainer.
- Observed: five development current-arm trials exited before inference with expired OAuth session that could not refresh; zero output tokens. No quality score produced. Cause: reported authentication failure; no provider diagnosis attempted.
- Impact/next action: authenticate the selected runtime and rerun both arms, then inspect outputs/traces; keep held-out work separate and run operator usability independently.
- Evidence: `evals/non-video/README.md`, implementation receipt. Closure pending successful inference and output review.

## Latest verification receipt

- WF-007/WF-008 recurrence 2026-10-11 non-video implementation: unrestricted setup reported 1171 passed/1 failed, plus the same three line budgets; no unrelated fixes. Receipt below.
- WF-009 follow-up 2026-10-11: review-with DeepSeek returned a usable read-only review with concrete findings, despite an unrecognized-model diagnostic. Findings assessed and audience gap corrected; exact served model identity remains unverified. Do not equate this review with workflow-quality evaluation.



2026-10-11: `tests/test_seo_review_fixes.py` and `tests/test_verify_links.py`: 22 passed. Final browser/coverage and review regressions: 28 passed; the final unmeasured-coverage comparison check: 10 passed. Full Python suite: 1146 passed, the known WF-007 test failed. Setup also reconfirmed WF-008. These checks establish deterministic behavior and local browser/HTTP handling; they do not establish live agent quality or SEO uplift. Detailed transient log: `/tmp/seo-review-fix-validation.log`.

## New entry template

### WF-NNN — Short symptom

- Priority/status: P1/P2/P3; open/in_progress/blocked/deferred/resolved. Add/update the queue row too.
- First/last observed: YYYY-MM-DD. Owner: component or role.
- Observed behavior and reproduction/evidence: sanitized repository-relative links; identify synthetic, live or unverified evidence.
- Expected behavior and impact: affected workflow and consequence.
- Cause: confirmed facts versus hypothesis.
- Next action: bounded improvement; dependency or resume condition if blocked/deferred.
- Resolution/history: dated change, command/result or evaluation receipt, remaining limits. Preserve past incidents.

### WF-013 — Repository-local evaluation ownership

- Priority/status: P2/resolved for local entrypoint and result-contract implementation; live quality remains WF-011.
- First/last observed: 2026-10-13. Owner: Agent evaluation maintainer.
- Observation/impact: local evaluation tools existed without one independently runnable check/trial/review/report path; central broker runs were not full domain quality evaluation.
- Change: scripts/evaluate.py delegates existing checks, records local immutable results and bounded selected-skill native trials, supports blind independent review, and exports summaries only by explicit request. No central runtime dependency.
- Verification/evidence: evals/test_local_evaluation.py (32 tests), real Bubblewrap network/key/home exclusion probes, and evals/local-implementation-report.md. Native pilot hit expired OAuth before inference; no quality improvement or baseline acceptance is claimed.
- WF-011 recurrence 2026-10-13: bounded native pilot returned “OAuth session expired and could not be refreshed”; append-only classification records INFRASTRUCTURE_ERROR. Existing authentication blocker remains open. After reauthentication, obtain observed native responses and independent grades; do not rotate credentials or silently substitute a paid provider.
