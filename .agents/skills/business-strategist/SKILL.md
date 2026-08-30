---
name: business-strategist
description: Routes business research, validation, branding, distinctive website, and experiment requests to the smallest useful specialist workflow. Use whenever a request spans business strategy and brand execution, or when the correct specialist is unclear.
user_invocable: true
---

# Business Strategist

Use `scripts/route_workflow.py` to make an explicit route decision before loading long references.

Rules:

- Preserve standalone branding: never require business research for a brand or website request.
- A validated business may offer a brand handoff, but never start branding automatically.
- Keep research, brand, website, and experiment state in their authoritative manifests.
- Ask at most one question when ambiguity would materially change the workflow.
- Require explicit approval before paid providers, external connections, analytics, experiments, commits to another repository, or deployment.
- Return the selected skill, mode, prerequisites, expected artifacts, and next action before dispatch.

## Procedure

Read `references/workflow.md` and dispatch only the selected specialist.

## Output

Return the route packet and next action.

## Quality Checklist

No unrelated skill or research workflow was loaded; approvals and state ownership are explicit.
