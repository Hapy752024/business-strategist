# Startup Challenge Panel Workflow

## Procedure

Use an orchestrator-worker pattern only when workstreams are separable and the decision value justifies extra cost. For simple questions, use one critic.

### Role calibration

Before analysis, give each role a short evidence-backed briefing from comparable businesses. A role is an objective and evidence contract, not a theatrical persona.

| Role | Objective | Required evidence | Stop condition |
|---|---|---|---|
| Customer Evidence Prosecutor | Disprove pain, urgency, workaround, and payment claims | Interviews, behavior, spend, evidence records | Every thesis-critical customer claim is supported or marked unsupported |
| Segment Strategist | Compare reachable early segments | Trigger, pain, buyer, reachability, economics | One beachhead is recommended with explicit tradeoffs |
| Distribution Operator | Challenge first-ten-customer and low-cost channels | Channel behavior, access, conversion assumptions | Each channel has a manual test and threshold |
| Business Model Economist | Challenge pricing, margin, sales effort, retention | Price, cost-to-serve, cycle, churn assumptions | Unit-economics gaps and scale blockers are explicit |
| Regulatory Skeptic | Identify licensing, advice, data, and consumer-risk gates | Current authoritative sources | Enabled only for regulated or sensitive models |
| Decision Arbiter | Resolve disagreements against evidence and gates | Role memos and topic artifacts only | Verdict names decisive evidence and next test |

### Orchestration

1. The lead writes one shared decision question, scope, artifact list, source rules, output schema, and effort budget.
2. Assign independent roles with non-overlapping objectives. Each returns claims, evidence IDs, counter-evidence, unknowns, and recommended tests.
3. Run one cross-examination round in which each role challenges a different memo's weakest material claim.
4. The arbiter scores evidence quality, impact, reversibility, and disagreement. Do not average opinions or decide by majority vote.
5. For high-stakes gates, invoke `review-with` if available for an independent provider review of the arbiter memo.
6. Save outputs under `reviews/<timestamp>-<decision>/` and update the manifest.

## Output

- Role-calibration source notes.
- Independent role memos.
- Claim/evidence/disagreement matrix.
- Arbiter verdict: proceed, conditional proceed, pivot, repeat test, or stop.
- Confidence, blockers, decisive next test, owner, cost, and deadline.

## Quality Checklist

- Roles have distinct objectives and bounded tools/sources.
- Every critique names evidence or a concrete missing-evidence test.
- The panel includes counter-evidence and failure cases.
- The arbiter does not introduce uncited new facts.
- Multi-agent effort is proportional to decision value.
