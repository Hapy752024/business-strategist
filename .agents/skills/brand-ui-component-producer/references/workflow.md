# Imported workflow

## Procedure

# Brand UI Component Producer

## Success Criteria
- Quantitative: >=90% trigger on branded component requests; 100% of shipped components have passing tests; zero unbranded components at Stop.
- Qualitative: drop-in for a Next.js App Router app; developer installs and uses on first read of README.md; library covers all selected taxonomy items.

## Workflow
1. Read `references/component-taxonomy.md`; present tiered menu; user picks in-scope set + priority.
2. For each component, run `references/tdd-workflow.md`: failing test first, then component, then stories.
3. Use `scripts/scaffold-component.py` to scaffold folders; `scripts/apply-brand-tokens.py` to apply tokens.
4. Run `scripts/validate-component.py` across the tree before Stop.

## Rules
- Always test first; the PreToolUse Write hook blocks `Component.tsx` without matching `Component.test.tsx`.
- Components reference `tokens.css` and `motion-tokens.ts` by import.
- Outputs live under `brand-projects/<name>/components/` (canonical) and `stages/components/iterations/` (working).
- shadcn/ui is the base primitive library; never hand-roll a component that shadcn already provides.
- Dispatch fresh subagents per `references/subagent-dispatch.md` whenever component work parallelizes.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
