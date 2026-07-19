---
name: startup-challenge-panel
description: Challenge a startup thesis with bounded specialist roles, independent evidence memos, red-team cross-examination, and an arbiter decision. Use for high-stakes idea reviews, segment choices, launch plans, business models, or scale decisions where multiple independent perspectives justify the cost.
---

# Startup Challenge Panel

## Success Criteria
- **Quantitative:** triggers on >=90% of challenge/review queries; completes in <=25 tool calls; runs >=3 independent bounded reviews; produces a disagreement matrix and arbiter verdict; zero decisions by vote.
- **Qualitative:** each role has a bounded objective and evidence contract; independent reviews complete before cross-examination; unsupported claims are surfaced; the arbiter verdict is reasoned, not averaged.

## Workflow

1. Read `references/workflow.md` completely.
2. Load the active topic manifest and only thesis-relevant artifacts.
3. Calibrate roles from comparable operators before assigning analysis.
4. Run independent bounded reviews, then one cross-examination round.
5. Use an arbiter and optional `review-with` gate; never decide by vote.

## Output

Write role memos, disagreement matrix, unsupported claims, decisive tests, arbiter verdict, confidence, and manifest next action under `reviews/`.
