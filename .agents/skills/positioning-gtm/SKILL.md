---
name: positioning-gtm
description: Select business positioning, build stage-gated GTM plans, or derive the operating model and cadence from the selected position. Use for position choices, first customers, launch, channels, partnerships, delivery design or company routines.
compatibility: Requires the business-strategist repository and its shared repo-root `references/strategic-positioning.md` method.
---

# Positioning and GTM

Before positioning, channel, content, website or first-campaign work, read `references/handoffs.md`.

The route ID picks the mode; read only that mode's reference.

| Route ID | Mode | Use when | Read |
|---|---|---|---|
| `business-positioning` | positioning | select or revise the business position and trade-offs | [positioning](references/positioning.md) |
| `gtm-strategy` | gtm | stage-gated GTM: first customers, launch, channels, partnerships, regions | [GTM](references/gtm.md), [evidence base](references/evidence-base.md), applicable sections of [archetypes](references/archetypes.md) and [regions](references/regions.md), [experiments](references/experiments.md) for gates |
| `company-operations` | operations | delivery model from the selected position, or goals, metrics, routines, cash and hiring | [operations](references/operations.md) |

All three routes are pain-gated; GTM and positioning also carry strategy-stage prerequisites; the router enforces them and records any audited override. Position comes first, then GTM or operations; continue only to requested implications.

## Success Criteria
- Links reviewed need to a specific promise, feasible delivery and separately assessed defensibility; preserves scope, uncertainty and stage gates; applies archetype and regional patterns only when they matter.
- Every operating routine has a decision, owner and threshold; no premature hiring or process theater. Infeasible promises return to position selection.

## Rules and output

1. Answer only the requested scope; a focused question needs no full plan or company blueprint. Uncertainty does not authorize execution.
2. Execution-ready GTM plans use relevant sections of `assets/gtm-strategy-template.md`, reuse the active `strategy-plan.json` (KPI owners, formulas, targets, decision rules) and pass `python3 scripts/strategy_review.py validate --plan <strategy-plan.json>` before being called ready.
3. Output is the mode reference's output section.
4. Chosen-idea or strategic continuation work applies repo-root `references/research-coaching.md`; interview recruitment or acquisition planning applies repo-root `references/interview-recruitment.md` (researched zero-network route, separate learning funnel).

Also read as the stage needs: `.agents/skills/precedent-research/references/playbook.md`, repo-root `references/evidence-registry.md`.
