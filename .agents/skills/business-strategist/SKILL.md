---
name: business-strategist
description: Route business, brand, website, and experiment requests to the smallest useful workflow. Use when a request spans specialties or the correct specialist is unclear.
---

# Business Strategist

**Pain-first rule for Business.**
For venture investigation, first establish customer segments, journeys and pain points with web evidence, even when the user arrives with a solution.
Paths are relative to the Business or investigated-case root: `market_research/customer_segments/`, `market_research/customer_journey/`, and `market_research/pain_points/` (runs under `pain_points/runs/`).
Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded.
Branding, standalone Marketing and other Digital Assets can start from their own brief; only explicitly business-linked consumption inherits Business checks.
Marketing inside a project that also contains Business defaults to business-linked.
An independent Marketing route inside that project must include an established-business brief; a routing flag alone does not bypass the gate.

**Subprojects.**
Business, Branding, Marketing, Website and other Digital Assets are independently startable subprojects; follow repo-root `references/subprojects.md`.
Brand and Website commands default to standalone entry and require no prior research, even inside a project that also has a Business subproject.
After a user explicitly selects a validated business handoff, branding may reuse its segment and positioning snapshot.
A completed business validation may offer a brand handoff but never starts branding automatically.
GTM, business positioning and explicitly business-linked marketing/brand/website work route with `scripts/route_workflow.py --project <slug>`:
the pain-first gate returns `gate_blocked` with `first_skill: idea-grill` until the required `problem_validation` receipt is current (or the user records an explicit `--override-gate`).

**Scope and selection.**
Keep simple requests simple: apply repo-root `references/task-scope.md` before dispatch.
Explicit user intent and exclusions override phrase matching and unrelated workspace state.
Focused answers and execution do not automatically initiate research workspaces or full strategy outputs.
Verify new market/platform claims when needed; rewriting supplied copy and synthetic code tests do not require market research.
Select situational capabilities from the installed skill descriptions and `config/workflow-routes.json`; use `references/routing.md` only when ownership is unclear.
Load the selected specialist, not the entire catalog of workflows.
`config/skill-catalog.json` lists prerequisites, outputs and side-effect boundaries.
Brand, website, marketing, operations and monitoring requests retain their own scope; they do not automatically start business validation.
Route-ID, alias, status and validation rules: repo-root `references/runtime-routing.md`.

Use `scripts/route_workflow.py` to make an explicit route decision before loading long references. Check dispatch with `--check-skill <selected-skill>` and stop on a nonzero exit; pass `--project <slug>` for a venture with a business track.
For substantive work on a registered Business case, check the current `case_insights.md` state and route final consolidation through `case-insights`. Use repo-root `references/case-insights.md`. The case document is the user-facing conclusion; supporting research remains with its specialist.
Preserve whether the request is a focused answer, deep dive or full rerun. For the latter, require the collection, reviewed-research and exact-run delivery checks in repo-root `references/research-execution.md`; never treat a current unrelated brief or three prose summaries as completed research. Route appraisals and selected plans through repo-root `references/case-assessment.md`, including original-source links and final separate review.
For a multi-case Business rerun, work the `build_case_closeout.py` queue for each case through an explicit provisional-plan, targeted-research or reviewed-insufficient-evidence outcome. Report `closure_status` separately: an interim published plan is not closed research. `--require-terminal` must pass before claiming closure; otherwise report the first blocking item.
Rules:

- Keep research, brand, website, and experiment state in their authoritative manifests.
- Ask at most one question when ambiguity would materially change the workflow.
- Paid customer-evidence API spend is pre-authorized (see AGENTS.md spend policy). Require explicit approval before advertising or recruitment spend, paid asset generation, external connections, analytics activation, live experiments, commits to another repository, or deployment.
- Return the selected skill, mode, prerequisites, expected artifacts, cost class, and next action before dispatch.

## Procedure

Read `references/workflow.md` and dispatch only the selected specialist.

## Output

Return the route packet and next action.

## Quality Checklist

No unrelated skill or research workflow was loaded; approvals and state ownership are explicit. For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
