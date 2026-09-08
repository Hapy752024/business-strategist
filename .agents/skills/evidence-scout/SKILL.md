---
name: evidence-scout
description: Collect sourced customer pain, workarounds, demand proxies, counter-evidence, and reachable communities. Use after a specific customer and problem hypothesis is researchable.
---

# Evidence Scout

## Success Criteria
- **Quantitative:** triggers on >=90% of validation queries post-idea-grill; completes in <=20 tool calls; zero failed API calls per run where credentials exist; <=15% irrelevant record rate.
- **Qualitative:** users do not redirect mid-collection; provider failures are surfaced before evidence interpretation; evidence, interpretation, counter-evidence, and missing evidence are separated in every output.

## Workflow

1. Read `references/workflow.md` and `references/provider-policy.md`.
2. Initialize or reuse `projects/research/topics/<topic-slug>/`.
3. Run capability lookup and provider doctor when routing matters, then use repository-root scripts.
4. Inspect plans, raw outputs, evidence, irrelevant records, alerts, and gaps.
5. On `insufficient_credits`/`billing_required` for a paid provider, pause and ask the user to top up or continue without the source (protocol: `references/provider-policy.md`). If they topped up, re-validate and rerun the provider before interpreting.
6. Stop on invalid geography, unavailable critical sources, or unsupported claims.

## Output

Return artifact paths, provider status, evidence and counter-evidence, confidence, gaps, and next test. Never treat attention as willingness to pay.
