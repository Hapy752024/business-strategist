---
name: interview-bridge
description: Turn weak or medium public evidence into a screener, non-leading interview guide, and confirmation tracker. Use when customer interviews are the next uncertainty-reducing step.
---

# Interview Bridge

## Success Criteria
- **Quantitative:** triggers on >=90% of post-collection weak-evidence situations; completes in <=10 tool calls; every probe traces to a source URL; zero solution pitches in the guide.
- **Qualitative:** screener recruits people who experienced the problem recently, not idea fans; guide asks about past behavior; tracker separates confirmation from refutation.

## Workflow

1. Read `references/workflow.md` completely.
2. Run `python3 scripts/evidence_scout/build_interview_kit.py --run-dir <evidence or discovery run dir>`.
3. Review the screener pools and guide probes against the segment before recruiting.
4. Interview, log results in `interview/interview-tracker.md`, and update the tally.

## Output

Return the kit paths, the traced evidence items, recruitment pools, and one question about which probe to prioritize. Interviews are hypotheses tests, not validation by volume.
