# App mode (route `app-ui`)

Design branded product interfaces: dashboards, admin tools, SaaS workflows, forms and onboarding, settings, data tables, mobile/web app screens and clickable prototypes. Marketing websites belong to `brand-website-designer-builder`.

## Procedure

1. Confirm the product task and the target user workflow.
2. Check whether Figma MCP and/or Storybook MCP is available. Figma: interactive canvas review, visual editing, frame/flow selection, token/variable inspection. Storybook: real components, props and usage rules, story previews, interaction and accessibility tests. With both, Figma is design feedback and Storybook is implementation truth.
3. If neither is available and interactive design is wanted, ask before installing or connecting trusted MCPs ([trusted MCPs](trusted-mcps.md)); never recommend third-party Figma MCP packages unless the user asks and the source, maintenance, permissions and advisories are reviewed.
4. Generate exactly 3 layout/workflow alternatives; the user picks one numbered option.
5. Iterate in Figma or a local preview; tell the user what to review, how to give feedback and the recommended next iteration.
6. Validate visually with screenshots and/or Storybook previews; without MCPs use approved tokens, `frontend-design` if available, local HTML/React previews and Playwright screenshots at mobile/tablet/desktop.
7. Run `brand-identity` review mode before final handoff.
