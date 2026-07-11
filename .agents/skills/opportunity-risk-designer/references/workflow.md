---
name: opportunity-risk-designer
description: Turn collected evidence about user pain, workarounds, search demand, and counter-evidence into opportunity areas, risk-ranked assumptions, and low-cost validation tests.
---

# Opportunity Risk Designer Workflow

Use this skill after evidence has been collected.

## Stance

Be skeptical. The goal is not to prove the founder right. The goal is to reduce risk with the least time and money.

## Ambiguity and Unknowns

If ambiguity materially changes the risk ranking or test design, ask one focused clarification question before recommending tests. If the evidence does not answer a question, say "I don't know" and convert it into an explicit risk or testable assumption. Do not treat missing evidence as negative evidence, and do not treat weak evidence as validation.

## Inputs

Use:

- `summary.json`
- `evidence.jsonl`
- `report.md`
- The user hypothesis from `idea-grill`

If the user does not provide paths, read the active topic `manifest.json` and use its latest evidence artifacts. Do not select a run from another topic by timestamp alone.

Before ranking opportunity risk, inspect `summary.json.needs_user_attention`. If provider failures, missing credits, permission errors, or missing keys affected collection, state that the evidence base is incomplete and include the failed providers in the risk assessment.

## Procedure

1. Locate the relevant `summary.json`, `evidence.jsonl`, `report.md`, and original hypothesis.
2. Inspect provider alerts, missing evidence, and `summary.json.needs_user_attention` before interpreting the opportunity.
3. Separate direct evidence, interpretation, counter-evidence, and missing evidence.
4. Rank problem, segment, urgency, willingness-to-pay, solution, channel, timing, and evidence-coverage risks.
5. Identify the narrowest opportunity area supported by the evidence.
6. Design low-cost tests that reduce the highest-ranked risks before recommending product buildout.
7. Give each test a target segment, action, success threshold, stop/pivot condition, cost, and time budget.
8. Choose a decision gate: persevere, narrow segment, pivot problem, or stop.

## Risk Ranking

Rank these risks:

- Problem risk: users do not care enough.
- Segment risk: the chosen segment is too broad, unreachable, or not the buyer.
- Urgency risk: the pain exists but can wait.
- Willingness-to-pay risk: users complain but will not pay.
- Solution risk: proposed solution does not beat workarounds.
- Channel risk: early adopters cannot be reached ethically or cheaply.
- Timing risk: interest is declining, seasonal, or driven by temporary news.
- Evidence coverage risk: key sources failed, lacked credits, lacked permissions, or were not run.
- Competitive durability risk: the business cannot defend its position after initial traction. Moats are structural advantages that protect value against competitors. A business can validate demand, find customers, and still fail if the first well-funded competitor that copies it destroys margins.

  For competitive durability, sub-rank these moat sources by relevance to the specific business:

  - Switching costs (high for B2B enterprise, low for B2C unless significant learning curve or artifact migration)
  - Network effects (each additional user makes the product more valuable for all users; note: fads are not network effects)
  - Brand/status (only relevant for visible consumer products; aspirational brands are strongest)
  - Share of mind / habit (relevant for frequently consumed, low-cost products)
  - Trust / asymmetric downside (relevant when the cost of being wrong exceeds the cost of the product)
  - Cost advantage (structural only, not passing through cheap inputs; weaker for visible consumer products)
  - Efficient scale (market only supports one or two profitable players)
  - Regulatory / contractual barriers
  - Data / learning advantage (can be copied over time, so medium-low durability)
  - Distribution / entrenchment (channel control)
  - Physical asset (irreplaceable location or access)
  - Product superiority (gets replicated over time unless structural bottleneck)

  For each relevant moat source, assess: (a) does the business have this moat? (b) does it map to a top customer priority? (c) can a well-funded competitor replicate it, and if so, on what timeline? (d) would a rational competitor choose not to copy it (incentive barrier, e.g., copying would cannibalize their own cash cow)?

  If no moat source scores above "weak" on both evidence and durability, competitive durability risk is high regardless of demand validation results.

## Tests

Design tests that minimize investment:

- 5-10 customer interviews in named communities.
- Concierge/manual workflow before building software.
- Landing-page smoke test with specific pain copy.
- Paid-search or community-post test for problem language.
- Competitor review mining for unmet needs.
- Preorder, waitlist, or paid pilot only when the segment and pain are specific enough.
- Competitor moat audit: for the top 2-3 direct competitors, identify their moat sources and map them to customer decision priorities. If competitors have strong moats, the startup needs a wedge where those moats do not apply.
- Switching-cost interview: interview 5 customers of a competitor and ask what it would take to switch. If the answer is "nothing, I'd switch for a 10% better price," switching costs are low.
- Incumbent-response simulation: assume the top incumbent copies the startup's core feature within 12 months. What does the startup have that the incumbent cannot copy at reasonable cost? If the answer is "nothing," competitive durability risk is high.
- Customer decision hierarchy interview: ask 5 target customers to rank what matters most when choosing a solution (price, function, reliability, convenience, trust, brand, etc.). If the startup's moat source does not appear in the top 3 priorities, the moat is decorative.

Every test must specify:

- Hypothesis being tested.
- Target segment and where to find them.
- Action to run.
- Success threshold.
- Stop/pivot condition.
- Cost and time budget.

Do not recommend building product features until a cheaper test would no longer reduce the main risk.

## Output

Produce:

- Opportunity thesis.
- Evidence confidence level.
- Top 5 risks.
- Test plan for the next 7 days.
- Decision gate: persevere, narrow segment, pivot problem, or stop.

Decision gates:

- `persevere`: strong pain, reachable segment, and evidence of workaround/spend.
- `narrow segment`: pain exists but the segment is too broad or mixed.
- `pivot problem`: the segment is reachable but cares about a different pain.
- `stop`: evidence is weak, generic, solved, or not worth paying for.

## Quality Checklist

Before finalizing, check:

- Provider gaps and missing evidence are included in the risk ranking.
- Weak evidence is not treated as validation.
- Missing evidence is framed as uncertainty, not proof of no demand.
- Risks are ranked by likelihood and impact on the next decision.
- Each recommended test has a hypothesis, target segment, action, threshold, stop condition, budget, and timeline.
- Tests are cheaper than building product features.
- The decision gate follows from the evidence strength, not founder optimism.
- The next 7 days are concrete and executable.
- Competitive durability risk is assessed and ranked alongside the other 8 risks.
- If no moat source scores above "weak" on evidence and durability, this is explicitly called out.
- The test plan includes at least one test that challenges competitive durability, not just demand.
- The decision gate factors in competitive durability, not just demand evidence.
