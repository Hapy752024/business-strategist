# Router detail (moved from SKILL.md)

**Subprojects.**
Business, Branding, Marketing, Website and other Digital Assets are independently startable subprojects; follow repo-root `references/subprojects.md`.
Inside a project, Brand and Website commands default to business-linked entry and are gated by the selected Business plan; standalone entry (no prior research) is used only when the user explicitly asks for work independent of the business case, or outside a project.
After a user explicitly selects a validated business handoff, branding may reuse its segment and positioning snapshot.
A completed business validation may offer a brand handoff but never starts branding automatically.
GTM, business positioning and explicitly business-linked marketing/brand/website work route with `scripts/route_workflow.py --project <slug>`:
the pain-first gate returns `gate_blocked` with `first_skill: idea-grill` until the required `problem_validation` receipt is current (or the user records an explicit `--override-gate`).

**Scope and selection.**
Keep simple requests simple: apply repo-root `references/task-scope.md` before dispatch.
Explicit user intent and exclusions override phrase matching and unrelated workspace state.
Focused answers and execution do not automatically initiate research workspaces or full strategy outputs.
Verify new market/platform claims when needed; rewriting supplied copy and synthetic code tests do not require market research.
Select situational capabilities from the installed skill descriptions and `config/workflow-routes.json`; use the Routing boundaries section of repo-root `references/runtime-routing.md` only when ownership is unclear.
Load the selected specialist, not the entire catalog of workflows.
`config/skill-catalog.json` lists prerequisites, outputs and side-effect boundaries.
Brand, website, marketing, operations and monitoring requests retain their own scope; they do not automatically start business validation.
Route-ID, alias, status and validation rules: repo-root `references/runtime-routing.md`.

Use `scripts/route_workflow.py` to make an explicit route decision before loading long references. Check dispatch with `--check-skill <selected-skill>` and stop on a nonzero exit; pass `--project <slug>` for a venture with a business track.
For substantive work on a registered Business case, check the current `case_insights.md` state and route final consolidation through `case-insights`. Use repo-root `references/case-insights.md`. The case document is the user-facing conclusion; supporting research remains with its specialist.
Preserve whether the request is a focused answer, deep dive or full rerun. For the latter, require the collection, reviewed-research and exact-run delivery checks in repo-root `references/research-execution.md`; never treat a current unrelated brief or three prose summaries as completed research. Route appraisals and selected plans through repo-root `references/case-assessment.md`, including original-source links and final separate review.
For a multi-case Business rerun, work the `build_case_closeout.py` queue for each case through an explicit provisional-plan, targeted-research or reviewed-insufficient-evidence outcome. Report `closure_status` separately: an interim published plan is not closed research. `--require-terminal` must pass before claiming closure; otherwise report the first blocking item.
