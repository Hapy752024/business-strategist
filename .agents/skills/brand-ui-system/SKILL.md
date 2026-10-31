---
name: brand-ui-system
description: Branded UI system work - UI kit tokens, motion system, React/Next.js component libraries and product app screens. Use for design tokens, motion, branded components, dashboards or app UI, not marketing websites.
---

# Brand UI System

One skill, one mode per former UI specialist. The route ID picks the mode; read only that mode's reference.

| Route ID | Mode | Read |
|---|---|---|
| `brand-ui-kit-producer` | kit | [kit](references/kit.md) |
| `brand-motion-designer` | motion | [motion](references/motion.md), then as the step needs: [motion concept](references/motion-concept.md), [pillars](references/pillars.md), [iteration loop](references/iteration-loop.md), [element taxonomy](references/element-taxonomy.md), [benchmarks](references/benchmarks.md), [coherence review](references/coherence-review.md), [token mapping](references/token-mapping.md), [motion output contract](references/motion-output-contract.md) |
| `brand-ui-component-producer` | components | [components](references/components.md), then [component taxonomy](references/component-taxonomy.md), [TDD workflow](references/tdd-workflow.md), [shadcn mapping](references/shadcn-mapping.md), [token application](references/token-application.md), [component output contract](references/component-output-contract.md) |
| `app-ui` | app | [app](references/app.md), [trusted MCPs](references/trusted-mcps.md) |

Pipeline position (set by `brand-identity` orchestration): motion concept after typography and before imagery; then UI tokens (kit) -> motion tokens and reference implementations (motion) -> component library (components) -> app screens (app). Each mode needs an approved brand direction; motion, components and app need approved tokens.

## Standing rules

- Show 3 alternatives per stage, recommend one, and wait for explicit approval before generating the full set or moving on.
- Tokens are the source of truth: no hardcoded colours or durations; overrides carry a recorded justification.
- Accessibility is built in: WCAG AA contrast, visible focus, no colour-only state, 44px touch targets, reduced-motion fallbacks.
- Ask before installing or connecting any MCP; use only the trusted ones.
- Promote only locked/approved iterations (`scripts/promote-motion-iteration.py`, repo-root `scripts/brand/promote_artifact.py --confirm`).
- Never parallelize subagents that write the same file.
- Brand identity decisions (strategy, logo, guidelines) belong to `brand-identity`; marketing sites to `brand-website-designer-builder`; imagery and paid generation to `brand-asset-producer`.

## Output

Return the requested artifacts with provenance, approval status, validator results (`scripts/validate-motion-tokens.py`, `scripts/validate-component.py`), unresolved gaps and one recommended next action. Run `brand-identity` review mode before final handoff.
