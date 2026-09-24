# Round 2 — C adversarial cross-review

2026-09-13. Reviewed all Round 1 proposals, the judge, common external/local packets and both revised `round-2/proposal-{a,b}.md` files. Scope: the two finalist architectures, not a third proposal. This is a paper contract review; no implementation, migration, market revalidation or founder usability test was performed.

## Judgment and smallest contracts

The valid distinction is **A: one scope-aware research manifest, existing stage storage, generated idea views** versus **B: case-authoritative manifests and physically scoped future research outputs**. Different folder labels would not qualify as two options. Both keep one insurance venture, shared evidence, and no automatic brand/website tree per variant.

A needs an identity-only `ideas/index.json`; `market_research/manifest.json` owns `idea_assessments[ID]`, including disposition, next question, binding revisions and current narrative fields. Generated cards/root comparison have no independent mutable status. Updating Chinese under the root lock changes its entry only, while preserving motor entries and umbrella stage history. This is genuinely smaller than B only if A supports narrow research continuation and explicitly rejects unsupported independent stage progression and handoffs. Keeping evidence paths unchanged does **not** mean existing collectors and gates can remain unchanged: their automatic stage writes must be scoped or suppressed.

The restriction alone would be an arbitrary handicap, not a valuable second design. A earns its place by preserving one authoritative research scope and existing output locations while solving navigation and bounded follow-ups. It avoids nested lifecycle discovery, separate stage locks and per-case downstream handoffs. But authored narrative in JSON, rendering and scoped admission are substantial work; “nearly zero-code” or “inherently lean” would be misleading. If repeated independent case progression is expected soon, A's later upgrade could cost more than implementing B directly. Its benefit is lower relocation/lifecycle disruption, not established lower total engineering cost.

B needs identity-only `cases.json`; `cases/<ID>/market_research/manifest.json` owns that case's state. A centralized scope resolver must cover collection, stage writes, discovery/resume, locks, gate overrides and downstream handoff references. An output directory argument is insufficient. Dormant cases should require only a dossier and minimal manifest; stage directories are created when actual outputs exist. Otherwise a useful folder idea becomes a costly administrative system.

Both need evidence-use bindings: stable artifact ID/path; record or claim selector; candidate applicability; limitations; reviewed correction revision; assessment result; review date. Neither a file digest nor a link alone establishes suitability. Narrative claims and admission assessments must refer to these bindings so affected consumers can be found.

## Eight required scenarios

“Pass” below means the paper contract is adequate. “Conditional” means the stated implementation prerequisite must exist before the workflow is safe. Neither label asserts current working software.

| Scenario | A transition | B transition | Review |
|---|---|---|---|
| Find English, Chinese, motor within two steps | Root links `ideas/personal-insurance-decisions/{english,chinese}-speaking-residents.md` and `ideas/discounted-motor-cover/brief.md`. | Root links `cases/personal-cover-{english,chinese}/README.md` and `cases/discounted-motor-mga/README.md`. | Pass: both revised designs expose direct rows with scoped status. |
| Arabic doctors overlap without copied evidence | A dedicated cross-linked variant points to `strategy/arabic-brokerage-assessment.md`; related language and profession entries point to the same card/evidence. | One Arabic-doctor case has language/profession facets and reviewed references to the shared Arabic assessment and doctor journey. | Pass. It is acceptable to repeat a short scoped interpretation; repeating raw evidence as independent observations is not. |
| Shared correction reaches affected ideas | Append a correction; scan bindings; mark affected `idea_assessments[ID]` stale under root lock; regenerate their views. | Append correction; scan case bindings; stale affected case assessments under case locks; rebuild umbrella view. | Conditional on correction lookup at admission and resume, not just a successful background refresh. |
| Parked idea remains visible | Motor retains a root row/card with parked rationale and reopening condition. | Motor case remains in the root comparison and on disk. | Pass. Park the investigated MGA mechanism under its stated constraints; do not label every discount-car model disproven. |
| Cyber cannot inherit personal gate | Missing/stale cyber assessment denies admission; global conditional pass is irrelevant. | Router selects cyber manifest and local applicability assessment; umbrella personal pass cannot qualify it. | Conditional on every stage-writing entry point using the scoped check. A may safely deny unsupported commitment altogether. |
| Superseded English guidance cannot look current | Back up originals; historical entry documents receive prominent dated supersession banners and a link to current EN card/root decision. | Same direct-entry treatment, linking to EN case. | Pass only with changes to the old current-looking files themselves; root history links alone fail this scenario. |
| Chinese-only research continuation | Read `idea_assessments[personal-chinese]`; write `market_research/pain_points/runs/<timestamp>-personal-chinese/` plus that entry; motor entry unchanged. | Read Chinese case manifest; write `cases/personal-cover-chinese/market_research/pain_points/runs/<run>/` plus that manifest; motor files unchanged. | Conditional on scope isolation, revision checks and restart-safe writes. In A this is narrow desk research, not an independent full lifecycle. |
| Separate venture versus language variant | Promote to a separate project only after an explicit independently operated venture decision. | Research case stays inside umbrella despite separate evidence assessments; promote only for independent operating ownership/lifecycle. | Pass. Independent evidence alone does not imply a separate business. |

## Hardest trace: correcting evidence whose bytes never changed

Example: an interpretation in `market_research/customer_segments/surelius-and-language-segments.md` was used to support language-demand claims. Later review finds that it measured a population proxy and cannot support that customer-demand inference. Do not edit frozen evidence or manufacture a new observation.

1. Append correction `COR-001` identifying artifact and affected claim/section, reason, replacement interpretation and affected-use category. A fetched replacement source is a new dated artifact if needed.
2. Resolve bindings using the old claim, including indirect derived claims declared as dependencies. English and Chinese may need review; motor need not if it has no dependency.
3. Mark affected interpretations and readiness stale; preserve their prior assessment as history. Root/card conclusions show the stale state rather than silently retaining an unqualified winner.
4. Admission checks the correction revision against each reviewed binding. If propagation stopped halfway, an outdated reviewed revision still denies admission. Avoid granting action while a background job catches up.
5. Assigned scoped reviewer reassesses applicability and dependent conclusions, records retained/revised/withdrawn result, refreshes relevant views and only then clears that binding's stale state. Reopening a passed assessment is scoped; it does not erase history or automatically reopen unrelated ideas.

A has one lock/transaction but potentially a larger manifest. B has several independent writes and must be interruption-safe. Neither should promise to detect an undeclared semantic dependency automatically: the guarantee covers registered bindings, with a conservative document-level review when finer scope is unknown.

## Cross-pollination decisions

| Source idea | Borrowed into review | Rejected or limited |
|---|---|---|
| A: visible reader library | Direct variant rows, clear dossiers, old-document supersession. | A mere index of links without self-contained conclusions does not solve the founder's comprehension problem. |
| B: identity-only registry | One authoritative mutable state location; registry stores identity/paths. | Duplicate stages, blockers and next actions in registry and brief frontmatter. |
| B: explicit scope resolver | Scope all writing/admission boundaries, reject unknown destination. | Treating `--out-dir` or nested folder existence as independent execution authority. |
| C: idea/facet/variant/experiment distinction | Preserve overlaps and do not create every combination. | Independent evidence assessment as sufficient reason for a separate venture. |
| C: existing-path compatibility | Preserve frozen runs and map new reader entry points to existing evidence. | Claiming no tooling work is needed for Chinese-only state progression. |
| Judge: correction propagation | Correction record, consumer lookup, stale state, admission denial, scoped review/reopening. | Digests alone or a blanket “sources are shared” claim. |

## Coverage traps and maintenance costs

The first physical-case tree narrowed EN/ZH to health although original personal insurance includes BU and sickness-income decisions. Both final designs must preserve that parent scope and explicitly identify the currently researched health wedge. Japanese/Korean comparisons, Arabic doctors, broker succession/acquisition and 55+ retirement are documented investigations that can disappear behind a convenient six-folder summary. Each needs a named card, case or linked investigation entry with honest unequal coverage; not necessarily a full independent lifecycle.

Surelius and the GKV/PKV simulator may be shared capabilities or commercial hypotheses. Classification should be recorded, not inferred from a product name. Register mail belongs under acquisition/access investigations and relates to relevant candidates; a corrected channel claim must not become a new venture recommendation.

A's maintenance cost is structured narrative editing in a shared manifest, root-lock contention and generated-view discipline. B's cost is more manifests, explicit shared/case output decisions, cross-case correction handling and broader scope integration. B should not copy the complete existing project scaffold into every case. Both must repair the nine sampled broken links and then run a fuller local-link/anchor audit during a later migration; preserving paths does not fix pre-existing defects.

## External grounding and limits

The supplied September 13 packet supports decomposition with restraint: [Spec Kit umbrella/child cycles](https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md) inform B while warning about overhead; [explicit scope selection](https://github.com/github/spec-kit/blob/main/docs/guides/monorepo.md) supports rejection of ambiguous destinations. [BMad planning paths](https://docs.bmad-method.org/cs/plan/choose-a-planning-path/) support proportionate artifacts. [GPT Researcher](https://github.com/assafelovic/gpt-researcher/blob/main/README.md) supports preserving dated report runs. These analogies do not prove either folder system works for this founder, solve semantic evidence dependencies, or validate insurance findings.

## Remaining implementation acceptance work

The final revisions resolve the Round 1 coverage omissions and define all eight scenarios. Neither has an unresolved folder/taxonomy blocker. I sent two narrow hardening requests back to both authors: explicitly declare source dependencies of derived reports, and display generation/prose revision mismatches as stale. These are correctness details of the proposed binding/freshness contracts, not reasons to manufacture a third architecture. If omitted during implementation, both designs can still show stale conclusions.

Both designs still require development and a migration rehearsal before use: unknown/escaped scope rejection, two simultaneous different-scope updates, correction interruption, unchanged unrelated state, no inherited gates, old-document direct entry, local-only backup/restore and protected-evidence hash checks. Migration must not invent a fresh winner to reconcile inconsistent source text. Record `needs_reconciliation` until the inconsistency is actually adjudicated.
