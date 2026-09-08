---
name: archetype-gtm-strategist
description: Select business positioning and derive strategic trade-offs, or build stage-gated GTM plans. Use for business-position choices, first customers, channel tests, partnerships, or launch decisions; load archetype playbooks only where applicable.
---

# Archetype GTM Strategist

## Success Criteria
- **Quantitative:** triggers on >=90% of GTM strategy queries; completes in <=20 tool calls; selects the correct archetype (SaaS/fintech/service) before producing output; zero stage gates skipped.
- **Qualitative:** recommendations are grounded in the founder's evidence and constraints; archetype-specific patterns are applied; regional adaptations are explicit when geography differs.

## Workflow

1. Read `references/workflow.md`; for position selection/revision use repo-root `references/strategic-positioning.md` and answer only the requested scope.
2. For a GTM plan, read `references/evidence-base.md` and only applicable sections of `references/archetypes.md` and `references/regions.md`.
3. Use `references/experiments.md` for stage gates and test design.
4. Ground recommendations in the founder's evidence, constraints, and current stage.
5. Use relevant sections of `assets/gtm-strategy-template.md`; for execution-ready plans, reuse the active `strategy-plan.json` with accountable KPI owners, formulas, targets, and decision rules. A focused advisory answer needs no full plan.
6. Validate it with `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>` before calling a GTM plan ready to execute.

## Output

For focused positioning, return the decision and requested implications. For a full GTM plan, produce segment, positioning/offer, launch and first-customer motion, channels/partners, relevant regional adaptations, economics, KPIs, gates, and accountable actions.
