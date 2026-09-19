---
name: opportunity-risk-designer
description: Convert customer, workaround, demand, and competitor evidence into ranked assumptions, low-cost tests, and decision gates. Use when deciding what to validate next.
---

# Opportunity Risk Designer

## Success Criteria
- **Quantitative:** triggers on >=90% of risk/opportunity queries; completes in <=12 tool calls; covers decision-changing risks and proportionate low-cost tests; zero risks stated without a testable assumption.
- **Qualitative:** observations, interpretations, assumptions, and unknowns are separated; each risk has a test with pass/fail criteria; the riskiest assumption is surfaced first.

## Workflow

For the checked `case-appraisal` route, read repo-root `references/case-assessment.md` and use its bounded appraisal/publication mode. It replaces the full risk workflow for that invocation: initial research is required, but a passed pain gate and execution selection are not. Do not invoke full strategy/pilot workflows or advance commitment stages. Own the assembled case narratives; use the calculation helper for economic results.

1. Read `references/workflow.md` completely.
2. Load the active topic manifest and evidence artifacts.
3. Separate observations, interpretations, assumptions, and unknowns.
4. Rank risks by importance, uncertainty, and test cost.
5. Define explicit pass, pivot, repeat, and stop thresholds.

## Output

In full mode produce opportunity areas, risk register, assumption map, test cards, evidence gaps, decision gates, and next actions. Contribute execution drafts to the startup builder's selected root `strategy-plan.json` authority and run `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>`. Appraisal mode owns only its designated case outputs.

For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
For interview recruitment or strategic acquisition planning, apply repo-root `references/interview-recruitment.md` (shared repository dependency), including a researched zero-network route and a separate learning funnel.
