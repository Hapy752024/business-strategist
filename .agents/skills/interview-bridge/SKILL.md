---
name: interview-bridge
description: Turn reviewed customer experiences and unresolved questions into a screener, non-leading interview guide, and learning tracker. Use when interviews can resolve context, motives, decisions or handoffs.
---

# Interview Bridge

## Success Criteria
- **Research quality:** every probe traces to reviewed evidence or a named hypothesis; material counterexamples and distinct contexts survive selection; no solution pitches or fixed-count validation rules.
- **Qualitative:** screener recruits people who experienced the problem recently, not idea fans; guide asks about past behavior; tracker separates confirmation from refutation.

## Workflow

1. Read `references/workflow.md` and repo-root `references/voc-research-method.md` completely. Choose interviews for the unresolved question, not an aggregate evidence-strength label.
2. Review source meaning and provenance, then run `python3 scripts/evidence_scout/build_interview_kit.py --run-dir <evidence or discovery run dir>`.
3. Supply a digest-bound `source-review.json` per the workflow; unreviewed records cannot generate probes. Research recruitment routes before recruiting.
4. Interview, log results in `interview/interview-tracker.md`, and update the tally.

## Output

Return the kit paths, accepted evidence items, recruitment plan and unresolved decisions. Interviews are hypotheses tests, not validation by volume.

For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
For interview recruitment or strategic acquisition planning, apply repo-root `references/interview-recruitment.md` (shared repository dependency), including a researched zero-network route and a separate learning funnel.
