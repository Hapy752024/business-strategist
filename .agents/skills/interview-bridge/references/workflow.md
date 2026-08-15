---
name: interview-bridge
description: Convert collected weak/medium public evidence into an interview screener, non-leading interview guide, and confirmation tracker. Use after an evidence-scout or market-problem-discovery run when evidence is mostly weak or medium and the next uncertainty-reducing step is talking to real customers, not more desk research.
---

# Interview Bridge Workflow

## Purpose and Boundary

Public evidence is mostly weak. Its best use is recruiting real customers and grounding interviews — not deciding whether an idea is good. This skill turns an evidence run into three artifacts:

- `interview-screener.md` — who to recruit, from where, and who to disqualify
- `interview-guide.md` — non-leading probes, each traced to a specific public evidence item
- `interview-tracker.md` — a confirmation/refutation log so interview outcomes update the evidence, not just the founder's mood

Do not use this skill before any evidence run exists. Do not use interviews to validate the solution; use them to verify whether the publicly observed pain, workaround, and segment are real.

## When To Use

- After `evidence-scout` when `user_review_plan.md` shows mostly weak/medium items.
- After `market-problem-discovery` when the user selects a candidate and public evidence needs primary confirmation before `idea-grill` closes remaining hypothesis gaps.
- When the founder says "the evidence looks thin" — thin evidence is an interview trigger, not a conclusion.

## Command

```bash
python3 scripts/evidence_scout/build_interview_kit.py --run-dir "<run path>" --limit 8
```

Pass an evidence run directory (`research/topics/<topic>/evidence/runs/<run>`) or a market-discovery run root (`research/topics/<topic>/market-discovery/runs/<run>`); the script finds `evidence.jsonl` in either layout. `--topic` and `--segment` override labels from `summary.json`.

## Procedure

1. Confirm the run directory contains evidence and that weak/medium items dominate — otherwise more desk research or a narrower rerun is the right move, not interviews.
2. Run the generator and inspect all three artifacts.
3. Review the screener against the segment hypothesis: are the recruitment pools reachable by this team? Are the disqualifiers consistent with the buyer? Adjust pools/questions by editing the artifact.
4. Review every probe in the guide: rephrase into the segment's own language where the public phrasing is insider jargon, and keep the evidence trace (E1, E2, …) intact.
5. Recruit 5–8 interviews per segment pocket. Log every interview in the tracker, including refutations.
6. Update the tally after each batch. A signal with 3+ independent confirmations can be treated as more than a lead; one clear refutation demotes it below the public post that produced it.
7. Feed confirmed/refuted results back into the topic workspace before running `idea-grill` refinement or `opportunity-risk-designer`.

## Interview Rules

- Ask about past behavior, not future intentions. `Tell me about the last time…` beats `Would you use…`.
- Never pitch the solution. The moment you describe the idea, the answer stops being evidence.
- Capture verbatim phrases; they feed positioning later.
- Interview count is not validation. Five interviews that all confirm a workaround exists is strong signal for pain; it still proves nothing about willingness to pay for your fix.

## Analysis Rules

- Separate confirmed facts (participant experienced the pain, used the workaround, spent money/time) from opinions (they like the idea).
- Separate segment-fit interviews from out-of-segment interviews in the tracker; only in-segment results count toward the tally.
- If interviews consistently refute the public signal, treat the public source as misleading for this segment and record that in the workspace gaps — this is a success outcome, not a failed interview round.
- Watch reachability bias: if you cannot recruit a demographic visible in the public evidence (or invisible in it), say so instead of generalizing from the reachable subset.

## Quality Checklist

- Every guide probe traces to a source URL and is phrased non-leading.
- The screener disqualifies never-experienced and no-workaround participants.
- The tracker logs refutations with the same weight as confirmations.
- Interview results were written back into the workspace (manifest gaps, assumptions, or candidate notes) before the next skill runs.
- The final response asks exactly one question — which probe or pool to prioritize first.
