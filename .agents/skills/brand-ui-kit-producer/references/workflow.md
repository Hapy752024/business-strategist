# Brand Ui Kit Producer Workflow


Generate tokens before components.

Work stage-by-stage: show exactly 3 visual/token alternatives for colors, typography, and component style before generating the full UI kit.
For every stage, explain the tradeoff, recommend one option, and ask the user to choose a number or approve.

Required token groups:
- Color primitives and semantic roles.
- Typography.
- Spacing.
- Radius.
- Elevation.
- Motion/focus.

Required component states:
- Default, hover, active, focus-visible, disabled.
- Loading, selected, invalid/error where relevant.

Use `references/ui-system-rules.md` for component details.
When Anthropic `frontend-design` is available, use it after tokens exist to refine screens and component demos.


## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
