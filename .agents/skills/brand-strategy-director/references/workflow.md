# Imported workflow

## Procedure

# Brand Strategy Director

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Do not create final assets until a territory is approved.

Create exactly 3 distinct territories unless the user requests a different count:
- Positioning idea.
- USP/differentiation expression.
- Personality keywords.
- Logo direction.
- Color direction.
- Typography direction.
- UI and marketing implications.
- Accessibility risks.
- What it avoids.

Ask the user to choose, reject, or combine one direction.
Present territories as numbered options so the user can reply with the number.
Recommend the strongest territory and explain the reason in one sentence.
End by instructing the user to choose a number, combine options, or reject all 3.

Use `references/territory-template.md` when writing the options.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
