---
name: opportunity-risk-designer
description: Convert customer, demand and competitor evidence into ranked assumptions, low-cost tests, decision gates and staged SaaS/fintech/insurtech pilots. Use when deciding what to validate next or designing a pilot.
---

# Opportunity Risk Designer

**Case appraisal and insights.**
Researched case appraisal needs the same eligible reviewed case run and a bound claim ledger; authored summaries alone do not qualify.
Before publishing case insights run `scripts/evidence_scout/build_voc_table.py` then `build_decision_memo.py`; the v2 contract and steps are in [workflow](references/workflow.md), with repo-root `references/case-assessment.md` and repo-root `references/case-insights.md`.
No final recommendation without a claim challenge (`claim-falsification` route); without a reviewed ledger, challenge draft claims (`basis: draft`).

**Competitive decision.**
Can this entrant succeed at the founder's intended scale?
Existing supply is not saturation; an empty niche is not demand.
Apply the served-versus-entrant-feasibility assessment and recommendation-change check in repo-root `references/strategic-positioning.md`.

**VC signals.**
For venture-scale intent or investor questions, inspect capital-market activity separately under repo-root `references/vc-investment-signals.md`; it is never demand proof.

## Success Criteria
- Each risk has a test with pass/fail criteria; the riskiest assumption is surfaced first.

## Workflow

For the checked `case-appraisal` route, read repo-root `references/case-assessment.md` and use its bounded appraisal/publication mode with separate review before final v2 publication. A passed pain gate or selection is not required; do not advance commitment stages.
For the checked `claim-falsification` route, follow `references/falsify.md` before final case delivery.
For the checked `case-insights` route, consolidate the case's reviewed findings into `case_insights.md` ([workflow](references/workflow.md)); it does not change stage gates.
For the checked `saas-fintech-pilot-designer` route (pilot mode: prototypes, POCs, MVPs, paid pilots, betas, sandboxes; pain-gated, with strategy-stage prerequisites), follow [pilot](references/pilot.md) instead of the steps below and, for regulated activity or sensitive data, [pilot regulatory guardrails](references/pilot-regulatory.md).

1. Read `references/workflow.md` completely and load the topic manifest and evidence artifacts.
2. Separate observations, interpretations, assumptions and unknowns.
3. Rank risks by importance, uncertainty and test cost; define pass, pivot, repeat and stop thresholds.

## Output

Open every output with a `## Strongest reason this fails` section tied to a cited claim, an `{{assumption.<id>}}` or a named unknown with its test; hold correct findings under pushback (repo-root `references/research-coaching.md`). In full mode produce opportunity areas, risk register, assumption map, test cards, evidence gaps, decision gates and next actions; contribute execution drafts to the selected root `strategy-plan.json` and run `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>`. Appraisal mode owns only its designated case outputs.

Chosen-idea continuation follows the research-coaching reference above; interview recruitment applies repo-root `references/interview-recruitment.md`.

For the checked `smoke-test-design` route, read repo-root `references/smoke-test.md` and the kit steps in [workflow](references/workflow.md). It is the default next test when the riskiest assumption is demand or message and there is no customer panel. Ad spend needs the recorded approval before `experiment-approve`.

Also read as needed: repo-root `references/evidence-registry.md`.
