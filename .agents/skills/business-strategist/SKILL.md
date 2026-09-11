---
name: business-strategist
description: Route business, brand, website, and experiment requests to the smallest useful workflow. Use when a request spans specialties or the correct specialist is unclear.
---

# Business Strategist

Use `scripts/route_workflow.py` to make an explicit route decision before loading long references. Check dispatch with `--check-skill <selected-skill>` and stop on a nonzero exit; pass `--project <slug>` for a venture with a business track.

Rules:

- Preserve standalone branding: independent brand or website requests need no business research; venture-linked commitment work must pass the pain-first gate or carry an explicit audited user override.
- A validated business may offer a brand handoff, but never start branding automatically.
- Keep research, brand, website, and experiment state in their authoritative manifests.
- Ask at most one question when ambiguity would materially change the workflow.
- Require explicit approval before paid providers, external connections, analytics, experiments, commits to another repository, or deployment.
- Return the selected skill, mode, prerequisites, expected artifacts, cost class, and next action before dispatch.

## Procedure

Read `references/workflow.md` and dispatch only the selected specialist.

## Output

Return the route packet and next action.

## Quality Checklist

No unrelated skill or research workflow was loaded; approvals and state ownership are explicit.
