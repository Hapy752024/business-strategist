# Search visibility: goal review and corrective plan

**Verdict: retain the useful skill changes; do not approve the probe for operational use. The original goal is only partly delivered.** The work improved instructions and evidence discipline, but concentrated on an offline comparator before demonstrating a useful website-improvement workflow. Current code still loses files and can report misleading comparisons. More review rounds against the same implementation plan will not close the product gap.

Reviewed on **2026-09-21**, HEAD `c5fd16547eb189459eb7a8d581768ada9d322eff`. The local branch is **30 commits ahead of the local `origin/main` reference**, not 29; no remote refresh was performed. The handoff itself is the last commit. Unrelated query-calibration work changed during this review. No source code, skills, project data, accounts, production sites, or existing plans were changed by this review; only this report and its evidence bundle were added.

Evidence: [reproduction program](audits/search-visibility-2026-09-21/reproduce.py), [observed results including rendered reports](audits/search-visibility-2026-09-21/results.json), and [reviewed file hashes / verification record](audits/search-visibility-2026-09-21/verification.json). The program creates fresh temporary fixtures; never test the current probe against a real workspace with `--out .`.

**What success should mean**

Given a selected website/brand and a scoped brief, the agent should establish the relevant bottleneck, produce a short evidence-backed improvement queue, prepare the useful changes, expose specific owner dependencies, and define how results will change the next decision. A focused technical audit can do this without starting business validation or a full channel strategy. Strategic business commitments retain their existing gates.

The six labels are a coverage checklist, not six mandatory programs. The deliverable is a usable decision and implementation handoff. It does not require a custom multi-engine monitoring service.

| Original requirement | Current assessment |
|---|---|
| A sound optimization approach | Substantially improved: bottleneck selection, attribution limits, conditional commerce work, no citation promises. Some live-platform guidance needs updating. |
| Existing skills can perform the work | Entry points and routes are connected. A representative complete output has not been demonstrated in the reviewed work. |
| Owner work is explicit | Useful states and proposed cadence exist. Ownership of persistence and resume behavior remains underspecified. |
| Measurement supports decisions | Offline processing exists; collection, trustworthy comparison, report consumption and business follow-up are incomplete. |
| Ready to ship/use | No: current file-loss reproductions and misleading measurement behavior remain. |

**Material findings and how to address them**

**F1 — Critical, reproduced: replacing `--out` deletes pre-existing user files; failed replacement also destroys the previous evidence.**

In [the probe](../scripts/monitoring/ai_answer_probe.py), `_publish` at line 451 moves the entire existing output into the temporary outgoing holder. The `finally` at line 541 recursively deletes that holder even when publication fails. Creating the holder does not establish ownership of everything subsequently moved into it.

Two ordinary CLI fixtures, an existing output directory and `--out .`, each contained `valuable-user-notes.txt`. Both returned **exit 0 / status pass**, and both deleted the file. A third fixture injected failure on the second rename: **exit 1**, with the previous evidence absent everywhere under the fixture. The claim that the old state is recoverable is therefore false for that exception path. No races, hostile symlink changes or real user data were needed.

The existing dot-output test at [test line 951](../tests/test_ai_answer_probe.py) starts with an empty directory. The interruption tests require that no old pass summary remain reachable, but do not require preservation of the old evidence. Those acceptance criteria helped lock in this behavior.

**Correction:** adopt immutable, unique run destinations, consistent with the existing workspace lifecycle. Refuse an already-existing output destination before mutation; in particular, reject `.` and `..`. Keep older runs intact. Write only within a directory exclusively allocated for the current run, and publish a completion marker/summary after its artifacts are complete. Consumers must require completion for that run; a failed new run must not invalidate or delete a valid historical run. Define concurrent same-destination behavior explicitly. This removes the need to rotate and recursively discard arbitrary previous outputs.

**Acceptance:** existing directory/file/symlink/cwd fixtures are rejected unchanged; failed and interrupted new runs preserve all previous bytes; a consumer cannot confuse incomplete work with a completed run. Do not fix this by adding another layer of backup cleanup.

**F2 — High, reproduced: the selected panel governs coverage but does not govern the comparisons.**

`_panel_coverage` filters rows, but `build_summary` passes the original unfiltered current/prior lists to `diff_observations` at lines 303–306. The fixture contains one selected prompt with no change and one excluded prompt whose mention changes from false to true. The report says **1/1 covered**, identifies the excluded row, then reports **two compared targets** and a `0.00 -> 1.00` trend for the excluded prompt. Exit/status are successful.

**Correction:** resolve the eligible observation set once and use it for both coverage and comparison. Excluded rows may remain in diagnostic/raw artifacts, but must not contribute selected-panel trends. Apply the same rule to undeclared engines and both windows.

**Acceptance:** adding or reordering excluded rows cannot change any selected-panel rate, delta or comparison denominator.

**F3 — High, reproduced: comparability and coverage do not enforce the stated measurement contract.**

The evidence bundle demonstrates four cases:

| Input | Actual result | Required correction |
|---|---|---|
| Prior supplied without its panel/version | `compatible: null`, yet status pass and a positive trend | Unknown compatibility must prevent an eligible trend; preserve observations and explain what is missing. |
| Current window precedes the supplied prior window | Positive trend, pass, no chronology warning | Validate direction before reporting temporal movement. |
| Prompt text changes while panel/prompt version labels remain unchanged | Compatible, pass, reported trend | Bind comparison to canonical prompt content/configuration, not only caller-maintained labels; reject conflicting content under the same identity. |
| Two repetitions requested; one API row and one consumer row with distinct repetition indices | 1/1 fully covered, zero gaps | Declare expected surface/model/config/locale targets and count repetitions within those targets. |

Locations: `load_panel`, `_panel_coverage` lines 265–285, `diff_observations` lines 183–235, and the status branches at lines 310–315. The last case establishes pooled **coverage**, not pooled trend rates: the comparison key already separates surfaces. Keep that distinction in the fix description.

Additional context is lost on output: trends omit model/config/locale/surface from their identity, and the Markdown omits prompt type. Distinct comparisons can have indistinguishable labels.

**Correction:** define operational completion separately from measurement eligibility. A completed baseline, partial observation, incomparable pair and eligible descriptive comparison are different results. A successful process must not imply a valid trend. Preserve all relevant target dimensions in machine and human outputs. Repetition indices are sample identifiers, not evidence that stochastic responses are paired experimental subjects; aggregate rates and sample counts should remain the primary descriptive result. Do not infer significant improvement or causal impact from a small rate change.

**Acceptance:** the cases above yield the specified unknown/ineligible/partial states across all artifacts, with no eligible trend. Overlapping windows must also be ineligible for temporal movement, rather than merely warning alongside an apparently usable delta.

**F4 — High, inspected and partly reproduced: there is no complete observation-to-action contract.**

The original plan explicitly deferred live collection. That deferral is legitimate, but it means the normalizer is not yet a live pilot. `ai_answer_engines` points at an offline script while advertising four API credentials; `brand_mention_listening` has `collector_provider: pending_pilot`. The monitoring workflow nevertheless says to collect with the probe under both capabilities. This blurs implemented processing, planned collection and mention listening.

The normalizer retains booleans and answer text, but has no declared brand/domain identity or annotation protocol. The fixture supplied `target_brand`, `target_url` and `citation_urls`; all were dropped by normalization. Provider error detail is also outside the retained field set. A full answer is useful, but it does not reliably preserve structured citation annotations, establish which entity a flag refers to, or explain a billing failure.

There are instruction-level consumers—the website and monitoring references explicitly point at the probe. The handoff's “no consumer” should mean **no demonstrated end-to-end consumer or decision outcome**, not literally no references. Likewise, “zero blast radius” is wrong: a manually invoked CLI already has a destructive filesystem effect.

**Correction:** first document one minimal recorded-run example: actual prompt text and selection evidence, target entity/domain, exact surface/configuration, recording source, citation URLs/annotations, extraction method or reviewer, and failure reason. Preserve raw recordings or a stable source reference. Label capability availability honestly: offline processing ready only after F1–F3; live collection unimplemented; listening pending. Do not require API keys for offline work.

Define the consumer output before expanding collection. For each material observation it must identify the affected URL/claim, supporting evidence, proposed change, expected customer benefit, owner dependency, verification and next decision. It must be allowed to conclude **no action warranted**. An API client or scheduling service is justified only after a manual/read-only pilot produces useful decisions.

**F5 — High for the intended outcome: current first-party measurements and controls are missing from the procedure.**

The AEO/GEO reference calls Bing the only first-party AI citation feed and moves directly to the custom probe. Current Google documentation also describes a **Generative AI performance report** for AI Overviews and AI Mode, and a separate **Search generative AI inclusion control**, with worldwide rollout notes dated August 31, 2026. This is directly relevant to baseline selection and visibility diagnosis. The Google report measures link impressions; do not relabel those as Bing-style citation counts. [Google report](https://support.google.com/webmasters/answer/16984139), [Google inclusion control](https://support.google.com/webmasters/answer/16908024), checked 2026-09-21.

**Correction:** use available authorized first-party reports early; check the actual property's access/settings and preserve unknowns. Distinguish Google impressions, Bing citation activity, actual referred visits/conversions and configured API observations. Do not combine them into one score. Do not assume a programmatic API exists merely because a dashboard/export exists. Google's report documentation says unavailable display values can become zeros in exports, so preserve availability context when importing them.

The older Google AI-features page still describes aggregate Web reporting, while the newer optimization guide links the dedicated report. Record this documentation difference and use the specific current report documentation for the procedure. A source check must follow relevant newer links, not merely confirm that an old bookmarked page still exists.

Google's newer guide also explicitly discourages AI-specific rewriting and mandatory content chunking. Keep the useful clarity/answer-structure experiment, but remove any default capsule length or arbitrary content-refresh cadence. Review content when facts, offers, questions or performance warrant it. Prioritize useful firsthand substance and reader comprehension. [Google optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide), checked 2026-09-21.

Other instruction corrections: in the conditional DEO procedure, preserve a legitimate quote-based sales model instead of categorically forbidding “contact sales”; select Product/Offer markup only for applicable offers and documented consumers. The phrase “inaccurate markup is penalized harder than absent markup” is an unsupported comparative claim; replace it with the concrete requirement that markup match supported visible facts.

**F6 — Medium, instruction gap: the owner handoff needs a complete resume contract.**

[The owner-action reference](../references/owner-actions.md) correctly distinguishes proposed from accepted work and reserves blockers for dependencies. But it asks for full rows in `owner-actions.md` while declaring a concise `next_action` string authoritative. It does not specify which subproject manifest owns the action, how unrelated next steps survive updates, or how the resumer loads details and records completed/deferred recurring work. This is an underspecified workflow, not a reproduced claim that actions were lost in a live project.

**Correction:** name the active track's manifest; keep accepted task identity, cadence/next review and status in its next-action representation, with a link to the detailed row. Merge rather than replace unrelated next steps. Require resume to load that row and reconcile accepted/completed/deferred state before proposing work. Keep history/proposals distinct from active commitments. This can start as a precise documented convention with the current fields; no new task platform or schema migration is needed.

Every actionable owner row should state the concrete input/decision, why the agent cannot supply it, rough effort, needed-by/review point and definition of completion. Recurring activity also needs the customer outcome and a stop/change criterion. “Write weekly posts” alone does not satisfy the original requirement.

**Why the review process kept missing this**

The artifact consistency layer is useful. However, `_expected_report_lines(summary)` in the tests reconstructs output from the implementation's summary. That proves consistent rendering of a summary; it does not independently prove the summary represents the right panel, populations or decision. Four agreeing outputs can be consistently wrong. The current reproductions show exactly that.

The plans also prescribed implementations and success criteria that damaged the goal: preserving `--out .` and making the old pass summary disappear became more important than preserving existing files. A failed new run and a valid historical run can coexist safely when run identity is explicit. Deleting historical evidence is not a necessary consequence of fail-closed reporting.

Use each finding in this form: **reviewed revision → realistic input → observed artifact/effect → user consequence → smallest correction → acceptance example**. Label proposed mutations and unresolved hypotheses separately. Mutation survival is not automatically a material production defect; exact line order and diagnostic wording should not drive repeated redesigns unless a real consumer depends on them.

Do not use old plan code blocks as the implementation authority. Keep history, mark executed plans as historical at the top, and maintain one short current contract/finding table. Bind review outcomes to the source hash. No persisted Round 5 verdict was found in the reviewed repository documents; the separate review's result remains unknown. This review is independent of that missing result.

**Recommended implementation sequence**

| Order | Work and responsible capability | Done when |
|---|---|---|
| 1 | Contain probe risk; fix immutable output ownership (coding) | F1 preservation fixtures pass; existing outputs cannot be replaced or deleted. |
| 2 | Correct selected-panel and comparability semantics (coding) | F2–F3 input-derived expectations pass across all output surfaces. |
| 3 | Clarify capability availability and recording contract (monitoring/provider instructions) | An agent can process one supplied recording without inventing a collector, credential dependency, entity or citation. |
| 4 | Update website/marketing guidance and owner resume rules | The same bounded task reaches the right reference, produces relevant owner actions and resumes without reviving proposals. |
| 5 | Exercise representative skill tasks with fixed inputs | Usable outputs meet the behavioral criteria below; structural checks alone do not close this step. |
| 6 | Run one selected-site pilot and make one concrete change | Evidence supports a prioritized change or a justified no-action decision; authorized implementation has QA and an outcome follow-up. |
| 7 | Automate only the repeat work shown useful by the pilot | Time saved and decisions improved justify ongoing collection/cadence. |

Do not begin another unbounded cleanup-review cycle or a broad monitoring build. The requested review does not identify a website to operate on, so this report defines the pilot without selecting a project or connecting accounts on the user's behalf.

**The output contract the skills should actually deliver**

Use a compact improvement queue in the existing audit/strategy deliverable. Each row needs: **page/customer task → dated observation and uncertainty → proposed change → expected outcome → agent work → owner-only input/decision → effort/priority → acceptance check → review/stop rule**. Prioritize material blockers and the few highest-confidence changes; explicitly defer irrelevant layers. Attach the baseline and source records. A separate universal score or new orchestration layer is unnecessary.

Illustrative owner handoff: “Confirm the actual cancellation window for `/pricing`; 10 minutes; needed before publication; agent drafts from the existing approved terms; completed when the owner confirms or corrects the exact statement.” A proposed posting program would additionally need audience/channel evidence, a feasible cadence and a review criterion before acceptance. These are examples, not required tasks for every site.

Behavioral acceptance tasks, to be run as tasks rather than only schema-checked eval records:

| Task | Required observable result |
|---|---|
| Existing local-service site, no analytics, two hours/week owner capacity | Scoped technical/content queue and an explicit measurement gap/fallback; no silent analytics activation or automatic six-layer program. |
| E-commerce site with conflicting visible/feed prices and stale inventory | Truth-source reconciliation before feed/markup work; owner facts isolated; no unjustified publishing. |
| Quote-based B2B service seeking an AI-visibility audit | Preserve its sales model; applicable page/readiness recommendations; no blanket requirement for product feeds or public fixed prices. |
| Recorded panel containing failed, mixed-surface and excluded rows | Correct unknowns/coverage; excluded rows do not produce trends; no demand or causal claims. |
| Rewrite two supplied headings | Two scoped rewrites; no research workspace, posting cadence or new measurement program. |
| Resume after accepting one task, deferring another and completing a third | Correct active task and owner effort; deferred/completed tasks do not become blockers or recur as newly accepted work. |

Start with supplied/synthetic cases, then one selected site. These task cases are recommended acceptance criteria; they were **not executed as independent LLM evaluations in this review**. Real search or conversion uplift requires subsequent live observation and cannot be proved by local tests.

**Verification and retained improvements**

- Targeted probe/website-launch/route suite: **149 passed**. Router/catalog validation: passed. Eval checker: **167 structurally valid cases**, zero structural errors; its own docstring states it does not execute LLM evals.
- Setup in the sandbox: **11 failed, 699 passed**; nine failures involved blocked subprocess/socket operations. Re-run outside the sandbox: **2 failed, 708 passed**, setup reported one error and the existing warning.
- Both remaining failures were query-plan assertions against the concurrently modified `collect.py`. The same assertion sets passed when executing committed HEAD's `collect.py` with current dependencies. The other workstream subsequently modified those tests too. This is not evidence of a search-visibility regression, and this changing working tree cannot support a clean whole-branch pass claim.
- The reproduction program produced nine review scenarios, with the current source hash recorded. Its data-loss fixtures used only files created for the review. No live API probe, account connection, advertising, posting, customer research or deployment was performed.
- Retain the corrected repetition handling, success-context validation, error-as-unknown rule, real maintenance entry point, bottleneck-driven marketing handoffs, markup scope corrections, and proposed-versus-accepted distinction. They solve real earlier problems.
- Use an isolated checkout/worktree for subsequent implementation, with a recorded starting revision and explicit file ownership. Do not absorb the unrelated query-calibration changes, reset the shared checkout, or push the branch as part of this review. Reflog events alone do not identify who made past changes.

**Sources and evidence dates**

- Repository specification, both implementation/fix plans, prior adversarial/implementation reviews, handoff, affected skills/configuration, lifecycle/owner contracts, probe, tests and validation scripts: inspected **2026-09-21**. Exact reviewed hashes and observed outputs are in the linked evidence bundle. Historical source statistics in the earlier plan were not all re-researched and are not used as new performance claims here.
- [Google: Generative AI performance report](https://support.google.com/webmasters/answer/16984139) — living official documentation, rollout note **2026-08-31**, retrieved **2026-09-21**; supports the report, dimensions and export caveat.
- [Google: Search generative AI control](https://support.google.com/webmasters/answer/16908024) — living official documentation, rollout note **2026-08-31**, retrieved **2026-09-21**; supports inclusion/exclusion and inheritance, separate from training controls.
- [Google: optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) — living official documentation, retrieved **2026-09-21**; supports reader-focused content, no mandatory chunking, and links to current first-party controls/reporting.
- [Google: AI features and websites](https://developers.google.com/search/docs/appearance/ai-features) — page marked updated **2025-12-10**, retrieved **2026-09-21**; older aggregate-reporting description distinguished above.
- [Google: documentation updates](https://developers.google.com/search/updates) — living official changelog, retrieved **2026-09-21**; confirms FAQ rich-result retirement effective **2026-05-07**. The existing correction remains valid.
- [Bing: AI Performance public preview](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview) — **February 2026**, retrieved **2026-09-21**; citation activity across supported surfaces and sampled grounding queries, not buyer demand or conversion attribution.
