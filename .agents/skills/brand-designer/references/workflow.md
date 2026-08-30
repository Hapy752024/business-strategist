# Imported workflow

## Procedure

# Brand Designer
## Success Criteria
- Quantitative: >=90% trigger on brand identity / corporate design / design-system work; <=25 tool calls per run; zero failed child-skill dispatches.
- Qualitative: no mid-workflow redirects; discovery stays one question at a time; a new user completes a brand identity project on the first try.

Rules:
- On start, run `scripts/check-brand-tooling.py` if available; otherwise read `references/startup-check.md`.
- Use `brand-workspace-manager` to create/manage the project folder.
- Ask exactly one discovery question at a time; if unclear, ask one focused follow-up.
- Enumerate suggestions/choices as `1.`, `2.`, `3.` so the user can answer with a number.
- Search the web before strategy or design recommendations.
- Work stage-by-stage; do not create the next asset group until the current one is approved.
- Guide the user at every stage: state what to do now and recommend the next step.
- Keep SVG/vector masters as the source of truth for logos and icons.
- Separate evidence, interpretation, and recommendations.
- Use root-level canonical delivery folders for approved handoff assets; keep `stages/` as working history only.
- After a user approves a direction, log the decision, archive/remove competing active alternatives, and promote approved assets before final delivery.
- Before saying a brand package is done, run the finalization gate.
- Dispatch a fresh subagent per pipeline stage whenever stages can run in parallel (e.g. motion pillars + component taxonomy scoping), and one critic subagent for the finalization gate review. Never parallelize subagents that touch the same brand-project folder.

Routing: see `references/routing.md` for the child-skill dispatch table.
Pipeline order: tokens (`brand-ui-kit-producer`) -> motion (`brand-motion-designer`) -> components (`brand-ui-component-producer`) -> screens (`brand-frontend-app-designer`).

Canonical package workflow:
- Read `references/package-structure.md` when creating or reorganizing a project package.
- Use `scripts/promote-approved-assets.py <project-dir>` after stage artifacts are approved and need handoff placement.
- Read `references/finalization-gate.md` before final QA, final export, or any "are we done" answer.

Refs: `references/orchestration.md`, `references/guided-user-journey.md`, `references/design-guideline-anatomy.md`, `references/tooling-decision.md`, `references/startup-check.md`.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
