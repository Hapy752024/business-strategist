# Components mode (route `brand-ui-component-producer`)

Produce a branded React/Next.js App Router component library from approved brand and motion tokens. shadcn/ui is the base primitive library; never hand-roll a component shadcn already provides.

## Procedure

1. Present the [component taxonomy](component-taxonomy.md) (Core always; Extended, Domain packs and custom on demand); record the in-scope set and priority in `stages/components/scope.json`.
2. Per component, run the [TDD workflow](tdd-workflow.md): failing test first, then the component from its [shadcn mapping](shadcn-mapping.md) with [token application](token-application.md), then stories. For visual options on a flagship component, show 3 variants and wait for the user's choice before token wiring.
3. Scaffold with `scripts/scaffold-component.py`; apply tokens with `scripts/apply-brand-tokens.py`.
4. Validate the tree with `scripts/validate-component.py --components-dir components/ --scope stages/components/scope.json` before declaring done; the [output contract](component-output-contract.md) lists the completion requirements.

Script paths are relative to `.agents/skills/brand-ui-system/`.

## Rules

- Test first: never write `Component.tsx` before its `Component.test.tsx`.
- Components import `tokens.css` and `motion-tokens.ts`; no hardcoded hex colours.
- Outputs: `projects/<name>/branding/components/` (canonical) and `stages/components/iterations/` (working).

## Subagents

Dispatch a fresh subagent when work parallelizes, passing exact paths, component name, tier and token filenames, never this conversation:

- One per in-scope component, each owning `components/<tier>/<Component>/`, running the full TDD loop and reporting its three files.
- One per variant when the user wants visual options, writing `stages/components/iterations/<Component>/option-N/`.
- One per approved domain pack, owning `components/domains/<pack>/`.
- One cold critic after scaffolding to report hardcoded colours, missing `var(--color-*)`/`var(--motion-*)` references or missing tests/stories.
- One research subagent when a component is missing from the shadcn mapping, to append its entry.

Never parallelize subagents that touch the same file; do single-component work inline.
