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

When the request also asks which opportunity the founder should pursue, apply repo-root `references/strategic-positioning.md` before prioritisation. Reuse supplied founder preferences and constraints; ask only a missing decision-changing input. Broad problem discovery can proceed without requiring the founder to invent a pain in advance. Give viable candidates comparable initial coverage and distinguish public-evidence salience from business attractiveness.

## Procedure

1. Restate the user’s requested outcome, market/domain, any rough hunch, and source scope. Treat the hunch as a search seed, not a claim. A pain-point study may finish with customer findings, counter-evidence and unknowns; it need not produce an idea. If the user supplied a specific idea to validate, use idea-grill. Similar companies at home or abroad are optional comparables, not an idea-import objective.
2. Brainstorm local job/trigger vocabulary, alternative explanations and source locations; review candidate queries using repo-root `references/research-query-calibration.md`. Select complementary approaches from repo-root `references/opportunity-research-approaches.md` only where they investigate a different explanation or evidence frame. Preview `--query-plan` with explicit locale/providers and result allocations before broad collection. Then initialize a discovery run with the reviewed plan. Use the repository-root command:

   ```bash
   python3 scripts/evidence_scout/discover_market_problems.py --topic "<market or domain>" --focus "<optional hunch>" --geo <AUTO|country> --language <language> --topic-keywords "<short local phrase>" --query-plan "<reviewed plan.json>" --providers "<plan providers>" --limit <allocated total> --results-per-query <depth> --collect
   ```

3. Before substantial collection, run the required routing and runtime checks:

   ```bash
   python3 scripts/capability_lookup.py --question "discover recurring customer problems and segments in <market>" --compact
   python3 scripts/validate_apis/run_all.py
   python3 scripts/evidence_scout/provider_doctor.py --json
   ```

   Use suitable default and paid sources; customer-evidence API spending is standing-authorized without a monetary cap. Disclose credit/access gaps and use valid fallbacks. This does not authorize deceptive/private access, recruitment or advertising.

4. Inspect `<run>/evidence/research_plan.md`, `summary.json`, `report.md`, `evidence.jsonl`, `irrelevant.jsonl`, and provider alerts. Apply repo-root `references/customer-voice.md` and `references/voc-research-method.md`: review source-linked experiences, always cover topic-led discovery, and add entity feedback as verified alternatives emerge. Unknown segments remain explicit hypotheses.
5. Inspect original speakers and rejected leads. Refine vocabulary/source choices with located evidence, preserve the initial run and parent plan digest, and count fresh useful sources separately from rediscoveries. Synthesize the sources into `<run>/market-discovery-report.md`. Replace every template placeholder. Cite the evidence IDs or source URLs for material claims.
6. Build 3–7 candidates only when the evidence supports them. A candidate needs a plausible segment, trigger/job, recurring pain or decision uncertainty, current workaround or alternative, and a named uncertainty. If evidence is thin, report fewer candidates or none.
   For each candidate, outline the journey in which the need arises using the customer-journey contract in `evidence-scout/references/workflow.md` (sibling skill). Existing providers do not exclude a candidate: assess potential customer choice and access, with unknowns, before calling a segment saturated.
7. For each candidate, separate:

   - observed evidence;
   - interpretation;
   - counter-evidence or saturation signal;
   - missing sources or weak coverage;
   - the cheapest next investigation.

8. Build the VOC source plan using the active discovery identity from `<run>/summary.json`; the design digest is the SHA-256 of `<run>/research_plan.md`. Select only the relevant complementary approaches; the customer-workflow approach is the default. Store the source plan and isolated approach packets under `<run>/customer-feedback/`:

   ```bash
   python3 scripts/evidence_scout/plan_customer_feedback.py --topic "<topic>" --customer-segment "<segment>" --intent customer_problem --study-id "<study_id>" --research-design-digest "<research_design_digest>" --approach customer_workflow --approach switching_and_changes --out-dir "<run>/customer-feedback"
   ```

   Add `alternatives_and_cases` or `ecosystem_and_implementation` only when relevant to the research question. Keep each packet’s sources, coverage and open questions separate; the coordinator deduplicates overlapping source observations and reconciles disagreement. A selected country comparison remains evidence about the user’s question, not a recommendation to copy the company.

   Close the artifact after synthesis:

   ```bash
   python3 scripts/evidence_scout/discover_market_problems.py --finalize --run-dir "<run path>" --candidate-count <0-7>
   ```

   Before finalization, provide the version-2 research pack under `<run>/customer-feedback/`: `evidence.jsonl`, `source-review.json`, `customer-feedback-coverage.json`, and `customer-voc-synthesis.json`. Pass `--voc-pack <path>` for another directory. Finalization validates these artifacts, not report headings alone. Choose the next method from the unanswered question; use interviews for missing context/motives/decisions, discovery for missing coverage, and authorized behavioral tests for payment questions.

9. Ask exactly one decision question: `Which path should we take next: validate Candidate [X], broaden/narrow the market scope, extend a named source gap, or stop?`

## Candidate Ranking Rubric

Prioritize learning from reviewed evidence using consequence, observed unmetness, decision relevance and uncertainty. Record a short comparison with evidence IDs, contrary cases and missing comparisons; do not use an opaque total score.

This rubric ranks observed evidence within this run only. It does not estimate market prevalence, willingness to pay, or the best opportunity for the founder. Unequal source coverage and missing independence limit comparison; apply the shared positioning contract before an opportunity recommendation.

Counts describe the sample, not importance or prevalence. Preserve rare high-consequence needs and explain where alternatives already work. Distinguish independent people from records; unknown independence is not corroboration. Supplier/editorial material remains alternatives context, not customer evidence.

## Analysis Rules

- Public posts, reviews, search signals, and comments are discovery signals, not proof of demand or willingness to pay.
- Treat repeated independent pain plus a workaround, spend, risk, or lost time as stronger than engagement, views, or one dramatic complaint.
- Treat competitor, provider, and editorial content as context about alternatives; do not treat it as customer demand.
- Call an area a **candidate** opportunity by default. Use “potentially underserved” only when the report shows a recurring job, a consequential workaround or dissatisfaction pattern, and a concrete gap in current alternatives. State the uncertainty beside the claim.
- Do not use demographic stereotypes to invent segments. Segment by trigger, job, consequence of failure, decision role, current workaround, and reachable community.
- Apply the latent-outcome comparison in repo-root `references/voc-research-method.md` within existing candidate findings: shortfall, consequence, competing explanation and disconfirming test. Distinguish adequate service from insufficient evidence; neither requires a manufactured opportunity.
- Do not ask the founder to choose a solution, price, or business model until they choose a candidate.

## Report Contract

The final `market-discovery-report.md` must include these headings:

1. `Executive Summary`
2. `Scope and Source Coverage` — including the standing line-item `Reachability bias:` (which segment demographics the used sources cannot see, blind spots rated high/medium/low; low public signal for such segments is a coverage question, not absence of pain)
3. `Candidate Problem-Segment Pockets`
4. `Detailed Findings`
5. `Cross-Cutting Patterns`
6. `Counter-Evidence and Coverage Gaps`
7. `Questions for Your Decision`
8. `Recommended Next Investigations`
9. `Handoff`

The `--finalize` gate rejects reports missing any heading or the `Reachability bias:` line-item.

The final response should lead with the report path and the evidence truth, then ask one choice question. Do not bury failed providers or source gaps.

Closing-question rule: end the response with exactly one question — the first unresolved item from the run's `evidence/assumptions.md` verification sequence when one exists, otherwise the candidate choice question — and wait for the answer before asking anything else. Never stack questions.

## Quality Checklist

- The report names the scope, geography/language, sources searched, and source failures.
- Every candidate includes a segment, trigger/job, workaround/alternative, source-backed observation, counter-evidence, and a named unknown.
- Evidence, interpretation, and simulated possibilities are not blended.
- Learning priorities show consequence, unmetness, decision relevance and uncertainty with auditable evidence and contrasts, not attention or raw mention volume.
- The report offers a user-controlled choice, not an automatic handoff to product building.
- The selected next step reduces uncertainty rather than merely producing more content.
