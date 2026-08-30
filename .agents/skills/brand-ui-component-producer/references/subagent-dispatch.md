# Subagent Dispatch

Dispatch a fresh subagent (Agent tool) for any of these:

- **Per-component scaffold + TDD.** One subagent per component in the user's in-scope set. Each subagent owns `components/<tier>/<Component>/` (disjoint folders — safe to parallelize). Pass the subagent: the component name, the tier, the brand token paths (`tokens.css`, `motion-tokens.ts`), and the shadcn mapping reference. The subagent runs the full TDD loop (failing test → component → stories → validate) and reports the three file paths it created.
- **Three variants per component.** When the user wants visual options for a flagship component, dispatch three subagents — one per variant — each writing to `stages/components/iterations/<Component>/option-N/`. Disjoint paths; parallelize. The controller presents the three variants to the user.
- **Domain-pack parallelization.** When the user has approved 2+ domain packs (e.g. dashboard + ecommerce), dispatch one subagent per pack. Each owns `components/domains/<pack>/` — disjoint.
- **Cross-component token audit.** After all components are scaffolded, dispatch one critic subagent to read every `Component.tsx` and report any hardcoded color, missing `var(--color-*)` / `var(--motion-*)` reference, or missing `.test.tsx` / `.stories.tsx`. The subagent reviews cold, without this skill's reasoning.
- **shadcn mapping research.** When a component is not in `references/shadcn-mapping.md`, dispatch a research subagent (Context7 / WebFetch) to find the shadcn/ui primitive and append a mapping entry.

Never parallelize subagents that touch the same file. Never dispatch a subagent for a single-component task — do that inline. Always pass the subagent the exact paths, component name, tier, and token filenames; do not paste this skill's conversation history.
