---
name: opportunity-risk-designer
description: Convert customer, workaround, demand, and competitor evidence into ranked assumptions, low-cost tests, and decision gates. Use when deciding what to validate next.
---

# Opportunity Risk Designer

**Case appraisal and v2 publication contract.**
For researched case appraisal, route and publisher require the same eligible reviewed case run and a bound claim ledger;
authored segment/journey/pain summaries alone do not qualify.
Use the v2 publication contract in repo-root `references/case-assessment.md` and `references/case-insights.md` for direct reviewed-source citations, nine decision sections, progressive publication and separate final review.
A legacy output remains readable but cannot close v2 research delivery.
Integrate substantive deep-dive answers into current insights, then refresh affected appraisal/economics, per-case business plan and selected plan.
A new deep dive makes downstream plan use pending until the selected insights are current again.

**Case insights.**
For a registered Business case, maintain `cases/<id>/case_insights.md` as its one current reader-facing assessment.
Publish coherent reviewed findings progressively, then consolidate material findings across research runs, deep dives and answered founder questions.
Check source coverage, numeric context, freshness and conflicting conclusions before each publication; distinguish a current progress snapshot from final delivery.
New cases have no case-level README; project-level READMEs remain navigation and comparison.
Apply repo-root `references/case-insights.md` throughout substantive case research;
existing legacy case narratives require reviewed conversion, not automatic migration.

**Competitive decision.**
The competitive decision is whether this entrant can succeed at the founder's intended scale.
Existing supply is not saturation; an empty niche is not demand.
Apply the served-versus-entrant-feasibility assessment and recommendation-change check in repo-root `references/strategic-positioning.md`.
Claim completion only for requested coverage actually audited and delivered.

**VC signals.**
For idea assessments where the founder intends venture-scale growth, seeks VC, explicitly requests investor activity, or this input could change financing assumptions, inspect capital-market activity separately from customer evidence.
Use repo-root `references/vc-investment-signals.md`; when available, run the Parsers VC topic scan, compare equal-length current and prior periods, and verify material rounds from primary sources.
Do not use investor attention as demand, success, market-size, or fundraising-fit proof.
State when VC fit is immaterial for a smaller business.

## Success Criteria
- **Quantitative:** triggers on >=90% of risk/opportunity queries; completes in <=12 tool calls; covers decision-changing risks and proportionate low-cost tests; zero risks stated without a testable assumption.
- **Qualitative:** observations, interpretations, assumptions, and unknowns are separated; each risk has a test with pass/fail criteria; the riskiest assumption is surfaced first.

## Workflow

For the checked `case-appraisal` route, read repo-root `references/case-assessment.md` and use its bounded appraisal/publication mode. Under the contract above, cover all nine decision sections, direct reviewed-source links, conditional economics and missing inputs. Prepare the exact bundle and obtain separate review before final v2 publication. Progress may publish while research continues. A passed pain gate or selection is not required; do not advance commitment stages.
For the checked `case-insights` route, consolidate the registered case's reviewed findings, deep dives and answered questions into `case_insights.md` (see top). Use the full inventory, numeric and freshness checks, then record a semantic contradiction review before publishing. This mode does not run the full risk workflow or change stage gates.

1. Read `references/workflow.md` completely.
2. Load the active topic manifest and evidence artifacts.
3. Separate observations, interpretations, assumptions, and unknowns.
4. Rank risks by importance, uncertainty, and test cost.
5. Define explicit pass, pivot, repeat, and stop thresholds.

## Output

Open every output with a `## Strongest reason this fails` section tied to a cited claim, an `{{assumption.<id>}}` or a named unknown with its test; never open with what is promising, and hold correct findings under pushback (repo-root `references/research-coaching.md`, truthful stance). In full mode produce opportunity areas, risk register, assumption map, test cards, evidence gaps, decision gates, and next actions. Contribute execution drafts to the startup builder's selected root `strategy-plan.json` authority and run `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>`. Appraisal mode owns only its designated case outputs.

For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
For interview recruitment or strategic acquisition planning, apply repo-root `references/interview-recruitment.md` (shared repository dependency), including a researched zero-network route and a separate learning funnel.

For the checked `smoke-test-design` route, read repo-root `references/smoke-test.md`. Take the assumption ids from the case `assumptions.json` riskiest list, generate the draft with `python3 scripts/evidence_scout/build_smoke_test_kit.py --run-dir <evidence-run> --experiment-id E-<slug> --assumption-id <A-id> --offer ... --segment ... --out-dir <run>/experiments/<slug>`, then commit it with `case_workspace.py experiment-plan --input <out>/experiment-card.json`. Use this as the default next test when the riskiest assumption is demand or message and the founder has no customer panel; interviews recruit from responders. Ad spend needs the recorded approval before `experiment-approve`.

Also read when the stage needs it:
- `references/evidence-registry.md`
