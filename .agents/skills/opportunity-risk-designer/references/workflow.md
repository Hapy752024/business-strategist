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
- `competitors.json` and `marketing_analysis.json` from `competitor-scout` / `competitor-marketing-analyzer`, when they exist

Reuse relevant founder decision context from the active thesis or strategy record: objective, desired role, means/access, affordable downside, time horizon, and acquisition/operating constraints. If a missing item changes the ranking or test design, ask one focused question and label the result as constraint, preference, assumption, or unresolved input.

If the user does not provide paths, read the active topic `manifest.json` and use its latest evidence artifacts. Do not select a run from another topic by timestamp alone.

Before ranking opportunity risk, inspect `summary.json.needs_user_attention`. If provider failures, missing credits, permission errors, or missing keys affected collection, state that the evidence base is incomplete and include the failed providers in the risk assessment.

## Procedure

1. Locate the relevant `summary.json`, `evidence.jsonl`, `report.md`, and original hypothesis.
2. Inspect provider alerts, missing evidence, and `summary.json.needs_user_attention` before interpreting the opportunity.
3. Separate direct evidence, interpretation, counter-evidence, and missing evidence.
4. Rank problem, segment, urgency, willingness-to-pay, solution, entry/customer-choice, channel/relationship, delivery/economics, timing, and evidence-coverage risks.
5. Identify the narrowest opportunity area supported by the evidence.
6. Use a coverage matrix only when a claimed competitor gap is material to the decision. It is an instrument for checking that claim, not a mandatory prerequisite or a proof of entry feasibility:

   ```bash
   python3 scripts/evidence_scout/build_whitespace_matrix.py --topic "<topic>" --evidence-jsonl "<evidence.jsonl>" --competitors-json "<competitors.json>"
   ```

   Fill each cell from citable evidence only; `unknown` means unscored, not unserved. A candidate gap stays a hypothesis until tested. If direct competitors address the pain, assess instead why a suitable customer would notice, trust and choose this entrant at acceptable acquisition and delivery cost.
7. Design low-cost tests that reduce the highest-ranked risks before recommending product buildout.
8. Give each test a target segment, action, success threshold, stop/pivot condition, cost, and time budget.
9. Choose a decision gate: insufficient_evidence, persevere, narrow segment, pivot problem, or stop. Persevere means continue the bounded test; it does not authorize investment or scale.

## Risk Ranking

Apply the entrant-success contract in repo-root `references/strategic-positioning.md`. Assess the founder's required scale and 12–24-month horizon (or stated override), using customer-journey evidence and the competitor's visibility, sales, service and retention strengths/weaknesses. Existing supply is not saturation; absent social activity is not a proven opening. Review changes to a recommendation against changed facts, constraints or corrected reasoning. If acquisition/capacity/economics are unverified, use investigate/insufficient evidence rather than a forced winner or stop.

Rank these risks:

- Problem risk: users do not care enough.
- Segment risk: the chosen segment is too broad, unreachable, or not the buyer.
- Urgency risk: the pain exists but can wait.
- Willingness-to-pay risk: users complain but will not pay.
- Solution risk: proposed solution does not beat workarounds.
- Entry/customer-choice risk: no plausible reason for a suitable customer to notice, trust or choose the entrant over doing nothing or available alternatives. Several modest advantages may jointly be enough; novelty is not required.
- Channel/relationship risk: early adopters cannot be reached ethically or cheaply, or the category needs trust/ongoing engagement that the proposed route cannot plausibly earn.
- Delivery/economics risk: the offer cannot be delivered within founder capacity, cash, compliance/dependency limits, or a plausible contribution range.
- Timing risk: interest is declining, seasonal, or driven by temporary news.
- Evidence coverage risk: key sources failed, lacked credits, lacked permissions, or were not run.
- Sequencing risk: the plan amplifies before proof. Check against the sequencing rule and canonical failure modes in `references/evidence-registry.md`: paid or discount-driven acquisition before retained-value proof (Homejoy scaled Groupon cohorts with inconsistent delivery and negative contribution margin), loops before single-user value, waitlists or press treated as PMF (Robinhood's earlier products; Socialcam). When the test plan or roadmap skips manual learning → proof → one repeatable motion, name the skip as a ranked risk and make the skipped stage the next test.
- Trust-pattern risk: the model or plan depends on tactics the registry classifies as dark patterns or compliance violations — incentivized/fake reviews, hidden fees, obstructed cancellation, pressure selling. For consumer services, also rank the absence of uncertainty reducers (scope, total price, credentials, human access, redress) relative to the service's risk level.
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

  Judge durability relative to founder ambition, required margin, operating horizon and credible competitor response. A weak moat is a risk to examine, not a universal rejection of a small profitable service. Require a durability test only when it could change the next decision.

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
- Coverage matrix only when a claimed gap matters, with its cheapest confirmation test.
- Top 5 risks.
- Test plan for the next 7 days.
- Decision gate: insufficient_evidence, persevere, narrow segment, pivot problem, or stop.

Decision gates:

- `persevere`: strong pain, reachable segment, and evidence of workaround/spend.
- `narrow segment`: pain exists but the segment is too broad or mixed.
- `pivot problem`: the segment is reachable but cares about a different pain.
- `insufficient_evidence`: coverage or relevant behaviour is inadequate to judge; name the next investigation.
- `stop`: demonstrated rejection or economic/operating incompatibility makes the opportunity unsuitable under the founder's constraints. Weak evidence or existing solutions alone do not justify stop.

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
- Competitive durability risk is assessed and ranked alongside the other risks.
- Sequencing risk (amplification before proof) and trust-pattern risk (dark patterns, missing uncertainty reducers) are ranked when the plan touches channels, loops, or consumer-service offers.
- If no moat source scores above "weak" on evidence and durability, this is explicitly called out.
- The test plan challenges competitive durability when it is material to the next decision.
- The decision gate factors in competitive durability, not just demand evidence.
- When a claimed competitor gap matters, a coverage matrix was scaffolded and its cells rated from citable evidence; otherwise entry/customer-choice evidence was assessed directly.
