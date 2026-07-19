---
name: competitor-scout
description: Discover direct, indirect, substitute, and future competitors for a business idea, then exclude blogs, directories, affiliates, agencies, and false positives. Use whenever alternatives or market structure matter.
---

# Competitor Scout

## Success Criteria
- **Quantitative:** triggers on >=90% of competitor discovery queries; completes in <=15 tool calls; classifies >=80% of discovered competitors as direct/indirect/substitute; zero false positives in final output.
- **Qualitative:** blogs, directories, affiliates, and agencies are excluded; each competitor has a classification reason; known competitors are preserved and enriched.

## Workflow

1. Read `references/workflow.md` completely.
2. Use the canonical repository discovery command documented in the workflow.
3. Preserve supplied competitors and use the active topic workspace.
4. Classify entity and source-page type separately.
5. Rate evidence quality before competitive strength.

## Output

Produce competitor arrays, exclusions, source URLs, success factors, uncertainties, and marketing-analysis candidates.
