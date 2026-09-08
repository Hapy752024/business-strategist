---
name: market-problem-discovery
description: Discover sourced customer problems, workarounds, segments, and candidate underserved pockets. Use for broad market exploration before a specific customer and problem hypothesis exists.
---

# Market Problem Discovery

## Success Criteria
- **Quantitative:** triggers on >=90% of exploration/discovery queries; completes discovery in <=25 tool calls; produces 3-7 candidates or a clear "no pocket found" result; zero missed required report headings.
- **Qualitative:** every candidate includes segment, trigger, workaround, source-backed observation, counter-evidence, and named uncertainty; evidence and interpretation are not blended; user controls the next path.

## Workflow

1. Read `references/workflow.md` completely.
2. Infer discovery mode when explicit; otherwise ask the one routing question before collecting.
3. Create a durable discovery run, validate source routes, and collect public evidence before proposing candidates.
4. Write the detailed Markdown report and distinguish evidence, interpretation, counter-evidence, and coverage gaps.
5. Let the user choose the next path; do not automatically convert a discovery candidate into a startup thesis.

## Output

Return the report path, source coverage, 3–7 candidate problem-segment pockets or a clear no-opportunity finding, the strongest counter-evidence, and one user decision question.
