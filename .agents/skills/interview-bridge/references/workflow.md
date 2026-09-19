---
name: interview-bridge
description: Convert reviewed experiences and unanswered customer questions into a non-leading interview kit when conversations or observation can resolve the uncertainty.
---

# Interview Bridge Workflow

## Purpose and Boundary

Public evidence is mostly weak. Its best use is recruiting real customers and grounding interviews — not deciding whether an idea is good. This skill turns an evidence run into three artifacts:

- `interview-screener.md` — who to recruit, from where, and who to disqualify
- `interview-guide.md` — non-leading probes, each traced to a specific public evidence item
- `interview-tracker.md` — a confirmation/refutation log so interview outcomes update the evidence, not just the founder's mood

Do not use this skill before any evidence run exists. Do not use interviews to validate the solution; use them to verify whether the publicly observed pain, workaround, and segment are real.

## When To Use

- After `evidence-scout` when the unresolved question concerns motives, decisions, context or handoffs that interviews can illuminate, even with strong public evidence.
- After `market-problem-discovery` when the user selects a candidate and public evidence needs primary confirmation before `idea-grill` closes remaining hypothesis gaps.
- When evidence is thin, first diagnose why: missing source coverage calls for discovery; missing experience/context may call for interviews.

## Command

```bash
python3 scripts/evidence_scout/build_interview_kit.py --run-dir "<run path>" --limit 8
```

Pass an evidence run directory (`projects/<topic>/market_research/pain_points/runs/<run>`) or a market-discovery run root (`projects/<topic>/market_research/market_discovery/runs/<run>`); the script finds `evidence.jsonl` in either layout. `--topic` and `--segment` override labels from `summary.json`.

## Procedure

1. Name the unresolved question and explain why interviews can answer it. Source-coverage gaps may instead need local discovery; solution-use uncertainty may need observation/usability testing; payment claims need a separately authorized behavioral test.
2. Run the generator and inspect all three artifacts.
3. Review the screener against the segment hypothesis: are the recruitment pools reachable by this team? Are the disqualifiers consistent with the buyer? Adjust pools/questions by editing the artifact.
4. Review every probe in the guide: rephrase into the segment's own language where the public phrasing is insider jargon, and keep the evidence trace (E1, E2, …) intact.
5. Choose an initial learning batch for the question and contrasting contexts; include successful alternatives and non-adopters, not only painful cases. Log every interview, including refutations.
6. Update the interpretation after each batch against hypothesis-specific criteria set beforehand. No fixed confirmation count validates a claim. A contrary case may reveal a context or segment boundary rather than erase other experiences. Inspect interview-selection.json for omitted perspectives and expand the guide when needed.
7. Feed confirmed/refuted results back into the topic workspace before running `idea-grill` refinement or `opportunity-risk-designer`.

## Hypothesis Probes From The Evidence Registry

Public evidence tests pain and workaround; it rarely tests the offer. When the workspace carries offer, pricing, packaging, channel, or loop hypotheses, add probes derived from the untested hypotheses in `references/evidence-registry.md`, phrased as past-behavior questions rather than pitches:

- **Uncertainty reducers:** for consequential, data-sensitive, or hard-to-reverse services, ask how the participant evaluated the last comparable purchase — what they needed to see (scope, credentials, total price, human contact, redress) before committing, and what made them walk away.
- **Staged commitment:** ask whether they previously bought a diagnostic, trial, or fixed-scope first step before a large commitment in this category, and what happened — instead of asking whether they *would* prefer one.
- **Reviews and proof:** ask which reviews or proof they actually used last time, how they judged authenticity, and whether a provider's response to a failure ever changed a decision.
- **Exit clarity:** ask whether cancellation, refund, or contract terms ever stopped or delayed a purchase in this category.
- **Referral and loop hypotheses:** if a referral or recipient-exposure loop is planned, ask about the last time they recommended or were recommended a comparable service — the trigger, the wording, and whether the recipient acted.

Each registry-derived probe is a hypothesis probe, not an evidence probe: tag it `H` in the guide (vs. `E1, E2, …` for evidence-traced probes) and log confirmations/refutations against the hypothesis in the tracker. Never read the offer to the participant to "test" it — these probes exist to learn how the segment decides, not to pitch.

## Interview Rules

- Ask about past behavior, not future intentions. `Tell me about the last time…` beats `Would you use…`.
- Never pitch the solution. The moment you describe the idea, the answer stops being evidence.
- Capture verbatim phrases; they feed positioning later.
- Interview count is not validation. A workaround's existence does not itself establish painful unmetness or willingness to pay for a different solution.

## Analysis Rules

- Separate confirmed facts (participant experienced the pain, used the workaround, spent money/time) from opinions (they like the idea).
- Separate segment-fit interviews from out-of-segment interviews in the tracker; only in-segment results count toward the tally.
- If interviews consistently refute the public signal, treat the public source as misleading for this segment and record that in the workspace gaps — this is a success outcome, not a failed interview round.
- Watch reachability bias: if you cannot recruit a demographic visible in the public evidence (or invisible in it), say so instead of generalizing from the reachable subset.

## Quality Checklist

- Every guide probe traces to a source URL (`E`) or a named registry hypothesis (`H`) and is phrased non-leading, past-behavior first.
- The screener establishes a relevant recent incident; absence of a workaround needs investigation, not automatic exclusion.
- The tracker logs refutations with the same weight as confirmations.
- Interview results were written back into the workspace (manifest gaps, assumptions, or candidate notes) before the next skill runs.
- Ask one decision-changing question early only when an unresolved choice matters; do not tack on a ceremonial closing question.

## Source acceptance before generated probes

Read the actual source and decide whether its segment, incident/journey and voice support the intended probe. Keyword matches and automatic relevance labels are discovery aids, not acceptance. Preserve the raw run; write `<run>/source-review.json` (or pass `--source-review`) with `evidence_sha256` for exact evidence.jsonl bytes, `target_segment`, and `reviews`. Each review records `evidence_id`, `source_url`, `status` (accepted/rejected/unresolved), `reviewed_segment`, `journey_stage`, `relevance_rationale`, `voice` (customer/operator/context), `segment_relation` (target/adjacent/unresolved), and boolean `firsthand`. Accepted reviews must match the target segment. Explain rejection or unresolved meaning.

Only accepted firsthand customer records with segment_relation=target can produce E probes. Adjacent and unresolved segment sources are comparator/discovery context, not target pain. Operator claims, creator transcripts, aggregate context and unreviewed stories cannot become customer voice. Missing/stale review or no eligible customer evidence stops generation before writes. In that case write a manually curated H hypothesis guide from the named customer/job hypothesis, clearly marked as hypotheses; do not fabricate an acceptance record to satisfy the generator. Discovery destinations remain unverified recruitment access until checked under the shared recruitment contract.
