# Independent judge — Round 2

Date: 2026-09-13. Review scope: revised A/B proposals, C's adversarial cross-review, Round 1 findings, common external packet and the initial sections of `REPORT.md`. No research files, gates or implementation were changed; no human usability test or migration rehearsal was performed.

**Verdict: stop after Round 2. Exactly two materially different options meet the design-review threshold: A 84/100 and B 87/100. No unresolved design blocker remains.** This approves the designs for comparison, not implementation, migration, current software safety or research validity. Round 3 is unnecessary.

## Scores and changes

These are design judgments, not measured performance. Weighted total = sum(score × weight / 5).

| Criterion | Weight | A, R1 → R2 | B, R1 → R2 |
|---|---:|---:|---:|
| Find and compare alternatives | 25 | 5 → 5 | 5 → 5 |
| Honest overlap and taxonomy | 15 | 5 → 5 | 4 → 5 |
| Evidence reuse and correction propagation | 15 | 3 → 4 | 4 → 4 |
| Current conclusions, history and scoped readiness | 20 | 3 → 4 | 4 → 5 |
| Compatibility, migration safety, reversibility | 15 | 4 → 4 | 3 → 3 |
| Maintenance and complexity | 10 | 3 → 2 | 3 → 3 |
| **Weighted total / 100** | **100** | **79 → 84 (+5)** | **80 → 87 (+7)** |

C is a cross-review of these two options, not a third finalist to score. I checked the proposals rather than treating C's favorable conclusion as independent proof of completion.

**A improves evidence/state correctness but becomes materially more complex.** A single candidate assessment now owns current content and state; projections carry revisions; corrections invalidate dependent uses; a scoped writer preserves unrelated candidate entries. Explicit denial of unsupported full progression is an honest boundary that satisfies narrow research continuation. However, authored Markdown inside JSON, an update interface, renderers, locking, correction scanning and admission changes constitute a small application. Maintenance falls to 2/5. Preserved paths reduce relocation disruption; they do not establish low total engineering cost.

**B earns stronger taxonomy and readiness scores.** It preserves broad personal-cover scope and names previously hidden investigations. Physical case storage, case stage authority, shared evidence references and a resolver spanning collection through handoffs provide a complete model for future independent research. More manifests and multi-file writes remain real overhead. Compatibility stays 3/5 because existing root-only path and stage assumptions need broader changes; calling that work “moderate” is an estimate, not a measured implementation effort.

Neither earns 5/5 for evidence reuse: correction handling depends on declared bindings, reviewed applicability and conservative invalidation where claim-level scope is unknown. It does not discover every semantic dependency automatically.

## Eight required scenarios

“Design pass” means the proposed contract specifies a coherent result. It does not mean today's tools implement it.

| Required scenario | A contract | B contract | Finding |
|---|---|---|---|
| 1. Chinese, English and motor within two navigation steps | Root rows link directly to `ideas/personal-insurance-decisions/{chinese,english}-speaking-residents.md` and `ideas/discounted-motor-cover/brief.md`; evidence is the next link. | Root rows link directly to `cases/personal-cover-{chinese,english}/README.md` and `cases/discounted-motor-mga/README.md`. | Design pass for both. Full file-browser self-containment is not promised by A. |
| 2. Arabic doctors without duplicated evidence | One `arabic-speaking-doctors.md` dossier, language/profession cross-links and shared source bindings. | One `arabic-employed-doctors` case with overlapping facets and references to common sources. | Design pass. Scoped interpretation can differ; source observations cannot be double-counted. |
| 3. One shared correction reaches affected ideas | Append correction; scan direct/declared derived consumers; stale affected candidate assessments and generated views; recheck correction revisions on admission. | Shared correction register; direct/declared derived consumer lookup; stale-read/admission checks before propagation completes; separately reassess affected case states and prose. | Design pass for both after checking B's final safeguard. Frozen original bytes remain intact. |
| 4. Parked idea remains discoverable | Persistent root row and motor dossier with dated rationale and reopening conditions. | Persistent registered motor case/root row, minimal dormant case scaffold. | Design pass. The disposition applies to the investigated MGA hypothesis, not all discount motor cover. |
| 5. Cyber cannot inherit personal-insurance validation | Missing/stale cyber assessment denies admission; even reviewed readiness cannot enable unsupported full transitions. | Cyber's own manifest and applicable segment/journey/pain bindings are required by routing and stage updates. | Design pass. No historical project pass is copied during migration. |
| 6. Old English-first advice cannot appear as current winner | Snapshot originals, change direct-entry historical banners/links, generate current scoped dossier and reconcile root narrative. | Same direct-entry treatment; current case state plus reviewed synthesis replaces apparent authority of the old memo. | Design pass. Contradictions remain `needs_reconciliation` until adjudicated; migration does not invent a winner. |
| 7. Resume Chinese without touching motor state | Allocate Chinese run in existing stage storage; revision-check and merge its assessment only; preserve motor entry/run bytes and umbrella stage fields. | Write Chinese case run/state under its own lock; preserve motor files; derive umbrella comparison afterward. | Design pass. A supports bounded desk research/review/recruitment planning; B supports independent full research stages after implementation. |
| 8. Separate project versus language variant | Separate venture requires an explicit independently operated lifecycle/ownership decision. | Independent research cases remain inside one venture; operating ownership/budget/lifecycle justify later project promotion. | Design pass. Separate evidence assessment alone is insufficient. |

## Blocker disposition

The three Round 1 blockers are resolved at design level: both specify correction propagation, a single scoped state/write authority and concrete existing-file treatments with explicit migration exceptions. A's limited continuation is supported deliberately and does not masquerade as independent full progression. B supports full progression through a larger proposed scope contract.

I reread B after its final bounded addition: admission-relevant derived claims must declare underlying dependencies; incomplete dependency scope conservatively stales report consumers. Authored prose carries reviewed assessment/evidence revisions that generated status updates cannot advance. Entry and summary generation flag mismatches and deny use as current guidance/handoffs. This resolves C's final interruption/dependency challenge. A already carries declared dependencies, revisioned projections and admission-time correction checks.

Remaining work below is implementation acceptance, not a missing architecture choice. Exact migration exceptions should be resolved during the later approved inventory; this design review does not authorize guessing their ownership.

## Implementation prerequisites, not completed checks

Both options require schema/identity rules, safe scope resolution, scoped collection/state writes, explicit admission denial, correction processing, current/history handling, a complete migration classification and an update workflow for human synthesis. All relevant direct stage/path callers must be audited; adding an argument to one router is insufficient. Arbitrary shell/file edits remain outside these enforcement boundaries.

Before use, demonstrate unknown/missing/escaped scope rejection, no cyber inheritance, concurrent Chinese/motor updates, unchanged unrelated state, correction between assessment and commit, interrupted projection updates, stale handoff rejection where supported, and direct entry into historical guidance. A must demonstrate that collectors suppress umbrella stage transitions and unsupported progression fails. B must demonstrate case discovery, locks, overrides and downstream reference scoping.

Before migration, produce the exact per-file retained/moved/generated map and exceptions; back up gitignored mutable files outside active paths; rehearse restore; verify protected evidence hashes. Repair the nine sampled missing relative targets and perform a fuller target/anchor audit. Sampled path checks are not proof of corpus-wide link correctness. Broad narrative consistency still requires substantive review.

## Fit and report guidance

There is **no default preference for A**. Choose it when retaining existing source locations and a single research lifecycle matters, the immediate objective is comprehension plus bounded follow-ups, and structured narrative editing is acceptable. Its later upgrade cost could exceed adopting B directly if independently advancing cases is already expected.

Choose B when the intended improvement is sustained idea-specific research with physically grouped future outputs and separately resumed stages. Its stronger ownership model fits that requirement better, provided the user accepts wider infrastructure work and per-case maintenance. Avoid expanding dormant cases into complete venture scaffolds.

The inspected opening and subsequently added option sections of `REPORT.md` distinguish organization findings from market validation and expose A's lifecycle restriction and JSON-authoring cost. I flagged one wording inconsistency for root to fix: A's assessment JSON owns its interpretation and renders a brief, whereas B's case README owns its authored interpretation. Saying both briefs own that content is imprecise. This is a report correction, not a finalist design blocker.

Spec Kit, BMad and GPT Researcher supply partial analogies, not proof of these correction systems or measured usability. The common packet was retrieved on 2026-09-13; no fresh external retrieval occurred in this round. The final two options differ materially in future output storage and lifecycle authority, satisfying the stop rule without forcing two similar navigation libraries to pass.
