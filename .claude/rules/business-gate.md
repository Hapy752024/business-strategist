---
paths: ["projects/**/business/**", "projects/**/business-analysis/**"]
---

# Business pain-first gate

For venture investigation, first establish customer segments, journeys and pain points with web evidence, even when the user arrives with a solution.
Paths are relative to the Business or investigated-case root: `market_research/customer_segments/`, `market_research/customer_journey/`, and `market_research/pain_points/` (runs under `pain_points/runs/`).
Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded.
`scripts/route_workflow.py --project <slug>` returns `gate_blocked` with `first_skill: idea-grill` until the required `problem_validation` receipt is current, or the user records an explicit `--override-gate`.
Interview recruitment planning is allowed before the gate; launches remain gated.
Inside a project, brand, website and marketing builds are business-linked by default and inherit Business checks; work starts from its own brief only when the user asks for it independent of the business case (or outside a project); the route envelope then carries `standalone_reason` quoting those words. Brand research and discovery stay ungated.
Marketing inside a project that also contains Business defaults to business-linked; an independent Marketing route there must include an established-business brief, and a routing flag alone does not bypass the gate.
Full routing rules: `.agents/skills/business-strategist/SKILL.md`.
