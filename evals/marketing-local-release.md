# Local campaign workflow delivery — 2026-10-17

Scope: approved P0/P1 and minimum P2. Shared campaign operations now support project-specific, secret-free connection definitions, versioned English aggregate CSV presets, a private descriptive packet, interactive structured agent review, atomic Marketing publication, durable owner task decisions, declared claim checks and a website handoff. Existing Marketing/Business ownership and publisher evidence checks remain applicable. Model inference is performed by the current interactive agent, not a new paid/headless service.

Follow-up 2026-10-18: a broader review found five local compatibility/lifecycle defects. All were corrected and covered by nine additional regression cases; 177 distinct targeted tests now pass. See `evals/marketing-local-review-2026-10-18.md` for findings, fixes and the new evaluation receipt. The checks below describe the original delivery.

## Entry points

- Usage and exact supported layouts: `references/marketing-execution.md`.
- Campaign setup/task decisions: `python3 scripts/marketing/campaign.py --help`.
- Prepare/finalize: `python3 scripts/marketing/review_cycle.py --help`.
- Secret-free configuration status: `python3 scripts/marketing/connections.py --project <slug>`.
- Declared claims: `python3 scripts/marketing/claims.py --help`.
- Safe synthetic walkthrough: `python3 scripts/marketing/demo.py --out <new-directory>`.
- Agent routing: checked `marketing-campaign-setup`, `marketing-results-import`, `marketing-campaign-review`, `marketing-connections` modes.

The operator lives at `.agents/skills/marketing-campaign-operator/SKILL.md`; the existing Claude skill-root alias discovers the same source. The website builder reads its campaign-review handoff reference. These are repository-specific shared references, not a standalone packaged marketing bundle.

## Verification

- `python3 -m pytest -q tests/test_marketing_campaign_cycle.py tests/test_marketing_execution.py tests/test_marketing_observations.py tests/test_seo_routes.py tests/test_case_routes.py tests/test_skill_route_coverage.py`: **72 passed**.
- `python3 scripts/validate_skill_routes.py`: passed.
- Skill-creator `quick_validate.py` for the new campaign operator and changed website builder: structurally valid.
- `python3 scripts/evaluate.py check`: deterministic PASS; final receipt: `evals/local-runs/20261017T160705Z-6f4985ee48ed/result.json`.
- `git diff --check`: passed.
- Synthetic CLI demo under `/tmp/marketing-local-demo-20261017-final`: two reviewed occurrences, unchanged-week handling and an accepted/snoozed task carried into the second report. No real business/customer metrics or external actions.

Representative regression cases include: all four exact export layouts; rates/weighted metrics/non-additive users; missing/suppressed/zero; metadata/filter/transform revisions; first/non-comparable windows; stale context/claims/queue; duplicate finalization; restatements; cross-project/account/campaign mixing; path aliases/symlinks; concurrent publisher revision conflicts; decline/snooze/completion; HTML/Markdown escaping; historical report immutability and exact-byte restoration; and preservation of v2 placement/delivery evidence checks under v3.

## Independent review and corrections

A fresh reviewer found three material defects during development: independent unions mixed account and campaign scope, task-ID collisions discarded follow-ups, and the shared publisher permitted replacing report history. They were corrected, given regression coverage and independently rechecked. The reviewer independently ran the 32 campaign-cycle tests and additional alias/traversal/symlink/restoration probes, with no remaining concrete blocker in this local scope. The review is retained locally at `docs/agent-improvements/2026-10-17-marketing-local-implementation-review.md` (ignored by existing Git policy).

Other corrections: report/task freshness now includes campaign facts, context and claims; composite import identity includes metadata, preset and transform; unknown metadata is rejected; declared filters/scope must match for comparisons. Skill validation initially rejected a relative link outside the skill folder; the entry now uses this repository's explicit shared-reference convention and validates.

## Remaining boundaries

No actual Google/Meta account is connected. Connection files contain opaque credential references and remain `unconfigured`; this release neither resolves secrets nor claims authenticated isolation. P3 must add protected enrollment, isolated collectors, transport/auth adapters and observed account-scope checks before real credentials load. P4 adds the selected scheduler/runtime and observed unattended delivery. P5/P6 add separately authorized publishing/advertising executors; no execution route is installed yet. TikTok/OpenAI advertising adapters remain later coverage work.

Real export/account compatibility, private credential renewal, unattended operation, deployed website behavior and commercial outcomes remain unverified. Claims checks verify declared markers/dates/numbers; editorial review of unmarked/semantic claims remains required. Fixtures and code review do not establish better model decisions, host behavior or marketing uplift. No matched baseline/current native model trial or independent output grading was performed. Existing full-suite failures were not re-audited; this receipt covers the named affected checks only.
