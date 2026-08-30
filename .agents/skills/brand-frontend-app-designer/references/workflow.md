# Imported workflow

## Procedure

# Brand Frontend App Designer

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Use when the user asks for app/web UI, dashboards, workflows, forms, screens, prototypes, or frontend implementation.

Priority:
1. If Figma MCP is available, use Figma for interactive canvas review and user feedback.
2. If Storybook MCP is available, use real coded components and documented props.
3. If both exist, use Figma for design feedback and Storybook for implementation truth.
4. If neither exists, use `frontend-design`, local previews, Playwright screenshots, and `brand-quality-reviewer`.

Rules:
- Ask before installing or connecting MCPs.
- Use only trusted/default MCPs listed in `references/trusted-mcps.md`.
- Do not recommend third-party Figma MCP packages unless explicitly requested and reviewed.
- Build stage-by-stage with 3 visual alternatives and user approval.
- Guide feedback loops: tell the user what to review in Figma/preview, how to give feedback, and the recommended next iteration.

Use `references/frontend-workflow.md` and `references/trusted-mcps.md`.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
