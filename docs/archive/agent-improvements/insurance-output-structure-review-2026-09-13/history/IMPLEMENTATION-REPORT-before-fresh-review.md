# Case workflow implementation

Implemented 13 September 2026. New research projects now support multiple investigated cases, bounded feasibility and economics for each, and one explicitly selected execution target. The live German insurance project remains unchanged; migration was exercised on a disposable copy.

The [approved Revision 2 plan](history/IMPROVEMENT-PLAN-approved-revision-2.md) is preserved. [Machine-readable verification](implementation-verification.json) records checks and limits.

## Reader-facing behavior

- Root `README.md` lists cases and links their current findings, feasibility and business case. Supporting documents appear when assessed.
- Each `cases/<id>/` owns its research manifest and current narratives. IDs survive display-title changes. Selection is separate from research focus and validation.
- The startup builder owns the selected business's root `strategy/business-plan.md` and existing structured strategy plan. Sections explicitly distinguish supported, provisional, missing and not-applicable coverage.
- One project timeline links canonical decisions and actual prior versions. Current narratives carry current conclusions; a correction or selection change visibly marks affected plans for review.

The [shared contract and commands](../../../references/case-assessment.md) describe initialization, case registration, appraisal, explicit selection, publication and recovery. Existing projects continue ordinary research on their old paths; new case work and execution routes require explicit migration. No live migration was performed or inferred from this implementation request.

## Agent and calculation changes

One new route, `case-appraisal`, reuses opportunity-risk-designer. Its declared inputs include the case context, current concept, source-use bindings and reviewed revisions. Initial segment/journey/pain research is required; a passed pain gate or execution choice is not. Appraisal cannot publish root strategy, brand or campaign outputs or advance commitment stages.

The shared research instructions cover actual buying behavior versus complaints or attention, user/buyer/payer, workarounds, acquisition effort, appropriate repeat-value windows, delivery capacity, dependencies, counter-evidence and proportionate next tests. Existing local specialists retain ownership; no external agent repository, standing panel, provider, new skill or evaluation platform was imported.

The economics helper supports transactional and recurring cases using one bounded monthly cash schedule. It distinguishes venture receipts from pass-through spend, lead versus customer acquisition costs, service/refund/partner costs, owner cash, capacity and payment timing. Unknowns remain unresolved. Decimal calculations prevent spurious extra sales at the break-even boundary. Downside/upside inputs are optional conditional scenarios, without invented probabilities or lifetime-value forecasts.

## Publication and writer coverage

A project lock, checked revisions, before/after digests and one pending journal coordinate current documents, case manifests, decisions, timeline and the final project commit marker. Recovery completes a committed publication or restores exact before-images; outside edits stop recovery. Cosmetic drafts use a separate write revision; overlapping root-plan drafts use the prior document digest. Old research runs cannot close a corrected case revision.

| Existing surface | Case-aware behavior |
|---|---|
| Topic initialization and discovery | Lazy versioned topics; registered-case discovery without requiring a root research manifest |
| Evidence, market discovery, competitor discovery, competitor marketing and ads collectors | Explicit case resolution, unique research runs and captured assessment revision |
| Founder/operator research | Case-local research runs; legacy research paths preserved |
| Entity/landscape builders | Destination validation before writes; fresh run outputs and scoped checkpoint closure |
| Interview kit and whitespace matrix | Case-derived destinations; immutable new outputs; no topic-label fallback outside the source case |
| Router, checked host envelope and catalog validator | Mode ownership, case identity, selection, prerequisites and revision-scoped evidence overrides |
| Strategy publisher/reviewer and business-to-brand builder/validator | Current selection, assessment, economics and source dependencies; stale handoffs rejected after A→B→A |
| Project controller and migration | Shared publication for versioned links; explicit recoverable migration without inherited case passes |

These checks enforce the CLI, checked host dispatch and publisher contracts. They do not sandbox arbitrary shell/file access or discover undeclared semantic dependencies.

## Verification and independent review

The final setup check, complete 350-test Python suite, route/catalog validation and all 143 structural evaluation cases passed. Exact counts and logs are in [verification](implementation-verification.json) and [setup output](implementation-evidence/setup-check.txt). Existing town-db-curator checklist/evaluation coverage warnings remain.

An actual fresh-context agent assessed fixed synthetic evidence. A separate reviewer passed [all ten saved-artifact assertions](implementation-evidence/semantic/run/independent-review.md), covering evidence overclaiming, unknown economics, transfer limits, conflicting advice, material corrections, archives, immaterial spelling changes and no implicit selection. The [final publication-contract replay](implementation-evidence/semantic/contract-replay/run/verification.json) preserved all six agent-authored current documents byte-for-byte while exercising the added write-revision checks.

The semantic result is bounded: exact runtime model identification was unavailable, follow-ups were disclosed in advance, and the final replay reused saved authored text. It does not establish live market research quality, unforeseen-conversation behavior or customer validation. Numerical correctness and selected-plan/handoff invalidation have separate implementation regressions.

Independent code review identified and closed: stale stage completion, unknown startup cash treated as zero, deferred billing suppressing service cost, rounded negative cash passing, missing legacy migration routing, incorrect attribution of an old plan's source to the newly selected case, retained economics dropping its source bindings, overlapping cosmetic drafts and floating-point break-even errors. Relevant regression tests were added; the final two findings received a separate bounded reread and arithmetic reproduction confirming closure. Later relative-path and direct-builder fixes passed the full suite but did not receive another independent rereview.

The [insurance copy rehearsal](implementation-evidence/migration-report.json) exercised interruption, exact rollback, retry, selection switching, unrelated-case correction and rejection of an old binding after switching back. Raw/research paths and source hashes were retained. Existing root metadata and the old structured strategy were archived when superseded. **All 376 live insurance files are byte-identical to the pre-work inventory.**

Historical snapshots preserve original bytes. Their embedded relative links retain their original document base; the decision records identify that original path. No historical Markdown was rewritten to make it appear newly authored.
