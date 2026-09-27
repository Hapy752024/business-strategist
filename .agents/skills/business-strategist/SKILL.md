---
name: business-strategist
description: Route business, brand, website, and experiment requests to the smallest useful workflow. Use when a request spans specialties or the correct specialist is unclear.
---

# Business Strategist
Use `scripts/route_workflow.py` to make an explicit route decision before loading long references. Check dispatch with `--check-skill <selected-skill>` and stop on a nonzero exit; pass `--project <slug>` for a venture with a business track.
For substantive work on a registered Business case, check the current `case_insights.md` state and route final consolidation through `case-insights`. Use repo-root `references/case-insights.md`. The case document is the user-facing conclusion; supporting research remains with its specialist.
Preserve whether the request is a focused answer, deep dive or full rerun. For the latter, require the collection, reviewed-research and exact-run delivery checks in repo-root `references/research-execution.md`; never treat a current unrelated brief or three prose summaries as completed research. Route appraisals and selected plans through repo-root `references/case-assessment.md`, including original-source links and final separate review.
For a multi-case Business rerun, work the `build_case_closeout.py` queue for each case through an explicit provisional-plan, targeted-research or reviewed-insufficient-evidence outcome. Report `closure_status` separately: an interim published plan is not closed research. `--require-terminal` must pass before claiming closure; otherwise report the first blocking item.
Rules:

- Follow `references/subprojects.md`: Business, Branding, Website and other Digital Assets start independently or connect through explicit handoffs. Brand/Website routing defaults to standalone, including inside existing projects; only explicit business-linked consumption inherits Business evidence/selection checks.
- A validated business may offer a brand handoff, but never start branding automatically.
- Keep research, brand, website, and experiment state in their authoritative manifests.
- Ask at most one question when ambiguity would materially change the workflow.
- Paid customer-evidence API spend is pre-authorized (see AGENTS.md Provider Policy). Require explicit approval before advertising or recruitment spend, paid asset generation, external connections, analytics activation, live experiments, commits to another repository, or deployment.
- Return the selected skill, mode, prerequisites, expected artifacts, cost class, and next action before dispatch.

## Procedure

Read `references/workflow.md` and dispatch only the selected specialist.

## Output

Return the route packet and next action.

## Quality Checklist

No unrelated skill or research workflow was loaded; approvals and state ownership are explicit. For chosen-idea or strategic continuation work, apply repo-root `references/research-coaching.md` (shared repository dependency).
