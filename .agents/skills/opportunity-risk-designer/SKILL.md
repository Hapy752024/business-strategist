---
name: opportunity-risk-designer
description: Convert customer, workaround, demand, and competitor evidence into ranked assumptions, low-cost tests, and decision gates. Use when deciding what to validate next.
---

# Opportunity Risk Designer

## Success Criteria
- **Quantitative:** triggers on >=90% of risk/opportunity queries; completes in <=12 tool calls; ranks >=5 risks; designs >=3 low-cost tests; zero risks stated without a testable assumption.
- **Qualitative:** observations, interpretations, assumptions, and unknowns are separated; each risk has a test with pass/fail criteria; the riskiest assumption is surfaced first.

## Workflow

1. Read `references/workflow.md` completely.
2. Load the active topic manifest and evidence artifacts.
3. Separate observations, interpretations, assumptions, and unknowns.
4. Rank risks by importance, uncertainty, and test cost.
5. Define explicit pass, pivot, repeat, and stop thresholds.

## Output

Produce opportunity areas, risk register, assumption map, test cards, evidence gaps, decision gates, and next actions. When the result becomes an execution plan, record it as `strategy-plan.json` and run `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>`.
