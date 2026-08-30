# Imported workflow

## Procedure

# Brand Typography Researcher

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Use when typography is in scope or when the user provides font examples/images/sites.

Tasks:
- Search web font sources and foundries.
- Identify likely fonts from websites, screenshots, or CSS when possible.
- Check license/availability before recommending.
- Check language coverage for target country/region.
- Propose exactly 3 typography alternatives.
- Include implementation method: CSS import, npm package, system stack, or licensed file.
- Recommend one option and tell the user what to approve or compare next.

Use `references/font-research.md` for source priority and output format.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
