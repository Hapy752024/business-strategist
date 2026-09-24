# Brand Frontend App Designer Workflow


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


## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
