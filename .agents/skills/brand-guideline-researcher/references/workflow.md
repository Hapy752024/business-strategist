# Imported workflow

## Procedure

# Brand Guideline Researcher

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Research before recommending.

Priorities:
- Inspect user-provided assets and local references first.
- Search official brand/design-system/press pages where possible.
- Compare 3-5 category leaders or competitors in the target country/region when available.
- Use `awesome-design/design-md/*/DESIGN.md` for local pattern examples.
- Separate evidence from interpretation.
- End with design implications and recommend the next decision the user should make.

Output:
- Source list.
- Repeated design patterns.
- Category conventions.
- Differentiation opportunities.
- Accessibility and consistency risks.

Use `references/research-method.md` for deeper benchmark structure.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
