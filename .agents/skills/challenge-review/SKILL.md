---
name: challenge-review
description: Challenge a startup thesis, strategy or consumer service - red-team panel with an arbiter, generate-and-judge draft tournament, or evidence-grounded customer-perspective review. Use when a consequential choice needs adversarial review.
---

# Challenge Review

One skill, three separate protocols. The route ID picks the mode; read only that mode's reference and never mix protocols.

| Route ID | Mode | Use when | Read |
|---|---|---|---|
| `startup-challenge-panel` | panel | an existing thesis or plan needs independent role memos, cross-examination and an arbiter verdict | [panel](references/panel.md) |
| `strategy-draft-tournament` | tournament | a consequential decision has a wide answer space and no plan exists yet; drafts are generated and judged | [tournament](references/tournament.md), [judge lenses](references/judge-lenses.md) |
| `service-customer-perspective-challenger` | customer-perspective | a consumer service's idea, package, trust design or message needs buyer-context challenge | [customer perspective](references/customer-perspective.md), [regional lenses](references/regional-lenses.md), [decision lenses](references/decision-lenses.md) |

Tournament mode needs its strategy prerequisites; the router enforces them and records any audited override.

## Standing rules

- Challenge by default; never approve because a plan sounds good. Say "I don't know" when evidence does not settle a point.
- Every critique or score cites evidence, a registry lens or a named assumption; claims without support are listed as unsupported.
- Decide on evidence weight: no averaging, no majority vote.
- Simulated customer voice and role memos are hypotheses, never evidence records; send evidence gaps to `evidence-scout` or `interview-bridge`.
- Never infer personality from nationality; segment by trigger, job, stakes and decision role.
- Multi-agent effort stays proportional to decision value; for a simple question use one critic.
- Save substantial outputs under the topic workspace `reviews/<timestamp>-<decision>/` and record the event in the topic manifest.
- Use repo-root `references/evidence-registry.md` for sequencing, weak-evidence and trust lenses.

## Output

Panel: role memos, disagreement matrix, unsupported claims, decisive tests and arbiter verdict. Tournament: decision frame, draft mechanisms, judge scorecard, selected or synthesized pick and the cheapest falsifying test. Customer perspective: the review template in `assets/customer-perspective-review-template.md` with evidence ledger, decision contexts, labeled simulated reactions, package and message changes and behavioral tests.
