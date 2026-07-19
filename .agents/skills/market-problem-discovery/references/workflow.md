---
name: market-problem-discovery
description: Research a rough market before a founder has chosen a customer problem or segment, then present evidence-grounded candidate pockets and let the founder choose what to validate.
---

# Market Problem Discovery Workflow

## Purpose and Boundary

Use this workflow for the **Discover** part of customer research: understand the market's users, jobs, frustrations, workarounds, alternatives, and visible gaps before narrowing to one thesis. It is not a lightweight version of `idea-grill`, and it does not validate a business, declare a segment underserved, or recommend building a product.

Use `idea-grill` only after the user chooses a candidate problem-segment pocket. Use `evidence-scout` afterward to test that selected candidate with targeted terms and a clear hypothesis.

## Mode Selection

Choose market discovery without asking when the user explicitly asks to explore a market, find customer problems, identify overlooked segments, analyse recurring complaints, or investigate a rough domain.

Choose idea validation when the user supplies a candidate problem/segment and asks whether it is worth pursuing, wants to test a solution, or asks for a business/MVP plan.

When intent is genuinely ambiguous, ask exactly one question and wait:

`Do you want market discovery—find evidence-backed customer problems and segments from this area—or idea validation—pressure-test a specific customer/problem hypothesis?`

Do not ask intake questions such as buyer, willingness to pay, or current workaround before an explicit discovery run. Ask one narrow scope question only if geography, language, or the market definition would materially change the sources; otherwise state and label the initial scope assumption.

## Procedure

1. Restate the market/domain, any rough hunch, and the source scope. Treat the hunch as a search seed, not a claim.
2. Initialize a discovery run. Use the repository-root command:

   ```bash
   python3 scripts/evidence_scout/discover_market_problems.py --topic "<market or domain>" --focus "<optional hunch>" --geo <AUTO|country> --language <AUTO|language> --collect
   ```

3. Before substantial collection, run the required routing and runtime checks:

   ```bash
   python3 scripts/capability_lookup.py --question "discover recurring customer problems and segments in <market>" --compact
   python3 scripts/validate_apis/run_all.py
   python3 scripts/evidence_scout/provider_doctor.py --json
   ```

   Use default sources first. Ask before paid social, app-store, login-backed, or other paid enrichment exactly as required by the provider policy. Never silently substitute a paid source.

4. Inspect `<run>/evidence/research_plan.md`, `summary.json`, `report.md`, `evidence.jsonl`, `irrelevant.jsonl`, and provider alerts. Exclude irrelevant records before clustering.
5. Synthesize the sources into `<run>/market-discovery-report.md`. Replace every template placeholder. Cite the evidence IDs or source URLs for material claims.
6. Build 3–7 candidates only when the evidence supports them. A candidate needs a plausible segment, trigger/job, recurring pain or decision uncertainty, current workaround or alternative, and a named uncertainty. If evidence is thin, report fewer candidates or none.
7. For each candidate, separate:

   - observed evidence;
   - interpretation;
   - counter-evidence or saturation signal;
   - missing sources or weak coverage;
   - the cheapest next investigation.

8. Close the artifact after synthesis:

   ```bash
   python3 scripts/evidence_scout/discover_market_problems.py --finalize --run-dir "<run path>" --candidate-count <0-7>
   ```

9. Ask exactly one decision question: `Which path should we take next: validate Candidate [X], broaden/narrow the market scope, extend a named source gap, or stop?`

## Analysis Rules

- Public posts, reviews, search signals, and comments are discovery signals, not proof of demand or willingness to pay.
- Treat repeated independent pain plus a workaround, spend, risk, or lost time as stronger than engagement, views, or one dramatic complaint.
- Treat competitor, provider, and editorial content as context about alternatives; do not treat it as customer demand.
- Call an area a **candidate** opportunity by default. Use “potentially underserved” only when the report shows a recurring job, a consequential workaround or dissatisfaction pattern, and a concrete gap in current alternatives. State the uncertainty beside the claim.
- Do not use demographic stereotypes to invent segments. Segment by trigger, job, consequence of failure, decision role, current workaround, and reachable community.
- Surface negative findings. “No credible pocket found within this scope” is a useful result.
- Do not ask the founder to choose a solution, price, or business model until they choose a candidate.

## Report Contract

The final `market-discovery-report.md` must include these headings:

1. `Executive Summary`
2. `Scope and Source Coverage`
3. `Candidate Problem-Segment Pockets`
4. `Detailed Findings`
5. `Cross-Cutting Patterns`
6. `Counter-Evidence and Coverage Gaps`
7. `Questions for Your Decision`
8. `Recommended Next Investigations`
9. `Handoff`

The final response should lead with the report path and the evidence truth, then ask one choice question. Do not bury failed providers or source gaps.

## Quality Checklist

- The report names the scope, geography/language, sources searched, and source failures.
- Every candidate includes a segment, trigger/job, workaround/alternative, source-backed observation, counter-evidence, and a named unknown.
- Evidence, interpretation, and simulated possibilities are not blended.
- Candidate rankings do not use attention as proof of demand.
- The report offers a user-controlled choice, not an automatic handoff to product building.
- The selected next step reduces uncertainty rather than merely producing more content.
