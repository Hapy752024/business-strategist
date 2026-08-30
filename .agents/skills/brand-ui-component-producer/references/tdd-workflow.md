# TDD Workflow for Components

## Purpose
Define the red-green-refactor loop the skill follows for every component. The PreToolUse Write hook (Task B8) blocks `Component.tsx` from being written before `Component.test.tsx` exists; this reference defines what the test must cover.

## Per-Component Loop

### Step 1: Identify shadcn base
- Look up the component in `references/shadcn-mapping.md`.
- If a base exists, fetch it from the shadcn registry (or local shadcn install if the consuming project has one).
- If no base exists (custom component), note it; the implementation will be a composition.

### Step 2: Write the failing test
- Path: `components/<tier>/<component-name>/<ComponentName>.test.tsx`
- Use Vitest + React Testing Library + jest-axe (for a11y).
- Tests must cover:
  1. **Rendering**: component renders without crashing for each variant/prop combination.
  2. **Behavior**: key user interactions (click, focus, type, etc.) produce expected outcomes.
  3. **Accessibility**: axe accessibility scan passes (no critical violations); keyboard navigation works as expected (Tab, Enter, Escape, Arrow keys where applicable).
  4. **Token usage**: component references at least one `var(--color-*)` or `var(--motion-*)` token in its className (verified by reading the component file from the test, or via a snapshot of className strings).
- Run the test; it must FAIL (component doesn't exist yet).

### Step 3: Write the component
- Path: `components/<tier>/<component-name>/<ComponentName>.tsx`
- Start from the shadcn base; apply brand tokens per `references/token-application.md`.
- Add `"use client"` directive if the component uses state, effects, or Framer Motion.
- Run the test; it must PASS.

### Step 4: Write the stories
- Path: `components/<tier>/<component-name>/<ComponentName>.stories.tsx`
- Use Storybook CSF format.
- Cover each variant and each interactive state (default, hover, focus, active, disabled, error).
- Stories don't need to be tested; they exist as a browsable gallery.

### Step 5: Refactor
- Tidy imports, extract repeated className strings into a `cn()` helper (clsx + tailwind-merge, standard shadcn pattern).
- Run the test again; it must still PASS.

### Step 6: Move to next component
- Log the completion to `stages/components/iteration-manifest.json`:
  ```json
  {"timestamp": "<iso>", "component": "<name>", "tier": "<tier>", "shadcn_base": "<primitive>", "test_status": "pass", "stories_count": <int>}
  ```
- Ask the user whether to proceed to the next component or pause for review.

## TDD Discipline
- The PreToolUse Write hook blocks writing `Component.tsx` if `Component.test.tsx` does not exist in the same folder. This is mechanical enforcement; do not try to bypass it.
- The SubagentStop hook (Task B8) validates each component produced by a subagent has all three files + passing tests.

## Failure Modes to Avoid
- Writing the component first and backfilling tests. The hook blocks this.
- Tests that only check "renders without crashing" without behavioral assertions. The test template in Step 2 requires behavioral + a11y + token-usage coverage.
- Hardcoded colors in the component. `validate-component.py` flags this.
