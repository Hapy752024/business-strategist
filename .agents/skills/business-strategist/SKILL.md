---
name: business-strategist
description: Route business, brand, website, and experiment requests to the smallest useful workflow. Use when a request spans specialties or the correct specialist is unclear.
---

# Business Strategist

**Pain-first rule for Business.**
For venture investigation, first establish customer segments, journeys and pain points with web evidence, even when the user arrives with a solution.
Paths are relative to the Business or investigated-case root: `market_research/customer_segments/`, `market_research/customer_journey/`, and `market_research/pain_points/` (runs under `pain_points/runs/`).
Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded.
Inside a project, brand, website and marketing builds are business-linked by default and inherit Business checks; work starts from its own brief only when the user asks for it independent of the business case (or outside a project). Brand research and discovery stay ungated.
Marketing inside a project that also contains Business defaults to business-linked.
An independent Marketing route inside that project must include an established-business brief; a routing flag alone does not bypass the gate.

**Subprojects and scope.**
Business, Branding, Marketing, Website and other Digital Assets are independently startable (repo-root `references/subprojects.md`); inside a project, Brand and Website default to business-linked (gated); independent design work needs an explicit standalone request.
Business-linked work (GTM, positioning, explicitly business-linked marketing/brand/website) routes with `scripts/route_workflow.py --project <slug>`; the gate returns `gate_blocked` with `first_skill: idea-grill` until the `problem_validation` receipt is current or the user records `--override-gate`.
Keep simple requests simple: apply repo-root `references/task-scope.md` before dispatch; explicit user intent and exclusions override phrase matching.
Select situational capabilities from the installed skill descriptions and `config/workflow-routes.json`; load the selected specialist, not the catalog.
Check dispatch with `--check-skill <selected-skill>` and stop on a nonzero exit.
Case-insights routing, rerun checks and multi-case closure: [workflow](references/workflow.md), under repo-root `references/case-insights.md`, repo-root `references/case-assessment.md` and repo-root `references/research-execution.md`.

Rules:

- Keep research, brand, website, and experiment state in their authoritative manifests.
- Ask at most one question when ambiguity would materially change the workflow.
- Paid customer-evidence API spend is pre-authorized (see AGENTS.md spend policy). Require explicit approval before advertising or recruitment spend, paid asset generation, external connections, analytics activation, live experiments, commits to another repository, or deployment.
- Return the selected skill, mode, prerequisites, expected artifacts, cost class, and next action before dispatch.

## Procedure

Follow the Router procedure in repo-root `references/runtime-routing.md` and dispatch only the selected specialist.

## Output

Return the route packet and next action.

## Quality Checklist

No unrelated skill or research workflow was loaded; approvals and state ownership are explicit. For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
