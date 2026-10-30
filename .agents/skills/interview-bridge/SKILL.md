---
name: interview-bridge
description: Turn reviewed customer experiences and unresolved questions into a screener, non-leading interview guide, and learning tracker. Use when interviews can resolve context, motives, decisions or handoffs.
---

# Interview Bridge

For a registered Business case, pass reviewed interview learnings and still-open customer questions to the case-insights owner under repo-root `references/case-insights.md`. The interview tracker remains the detailed source.

## Success Criteria
- **Research quality:** every probe traces to reviewed evidence or a named hypothesis; material counterexamples and distinct contexts survive selection; no solution pitches or fixed-count validation rules.
- **Qualitative:** screener recruits people who experienced the problem recently, not idea fans; guide asks about past behavior; tracker separates confirmation from refutation.

## Workflow

1. Read `references/workflow.md` and repo-root `references/voc-research-method.md` completely. Choose interviews for the unresolved question, not an aggregate evidence-strength label.
2. Review source meaning and provenance, then run `python3 scripts/evidence_scout/build_interview_kit.py --run-dir <evidence or discovery run dir>`.
3. Supply a digest-bound `source-review.json` per the workflow; unreviewed records cannot generate probes. Research recruitment routes before recruiting.
4. For smoke-test responders, pass the card's `responders_ref` path as `--responders` together with the evidence `--run-dir`; `scripts/route_workflow.py status` reports this skill runnable once a card has bookings. Screen segment fit and a recent incident before counting an interview.
5. Interview, log results in `interview/interview-tracker.md`, and update the tally.
6. Code each transcript yourself into `{"transcript_id", "items": [{"theme", "interpretation", "verbatim_quote", "speaker", "locator", "evidence_type", "author_voice_status"}]}`, copying quotes exactly. Run `python3 scripts/evidence_scout/ingest_transcript_coding.py --coding <coding.json> --transcript <id>=<path> --out <fresh evidence.jsonl>`; it rejects any quote not found verbatim. Quotes become evidence; themes stay labelled interpretation. Keep transcripts and speaker identities private.

## Output

Return the kit paths, accepted evidence items, recruitment plan and unresolved decisions. Interviews are hypotheses tests, not validation by volume.

For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
For interview recruitment or strategic acquisition planning, apply repo-root `references/interview-recruitment.md` (shared repository dependency), including a researched zero-network route and a separate learning funnel.

Also read as the stage needs: `references/evidence-registry.md`.
