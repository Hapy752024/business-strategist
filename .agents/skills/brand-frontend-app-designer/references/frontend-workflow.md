# Frontend Workflow

## When To Use

Use for:

- Dashboards.
- Admin tools.
- SaaS workflows.
- Forms and onboarding.
- Settings screens.
- Data tables.
- Mobile/web app screens.
- Clickable prototypes.

## Workflow

1. Confirm product task and target user workflow.
2. Check whether Figma MCP and/or Storybook MCP is available.
3. If not available and interactive design is desired, ask the user to install trusted MCPs.
4. Generate exactly 3 layout/workflow alternatives.
5. Let the user pick one numbered option.
6. Iterate in Figma or local preview.
7. Validate visually with screenshots and/or Storybook previews.
8. Run quality review before final handoff.

## Figma Role

Use Figma for:

- Interactive user feedback.
- Visual editing on canvas.
- Frame/flow selection.
- Design token/variable inspection.
- Sending live UI back to Figma when supported.

## Storybook Role

Use Storybook for:

- Real component discovery.
- Props and usage rules.
- Existing design system behavior.
- Story previews.
- Interaction and accessibility tests when configured.

## Fallback

Without MCPs:

- Use approved brand tokens.
- Use `frontend-design` if available.
- Create local HTML/React previews.
- Run Playwright screenshots at mobile/tablet/desktop.
- Review with `brand-quality-reviewer`.
