# Imported workflow

## Procedure

# Brand UI Kit Producer

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

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


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
