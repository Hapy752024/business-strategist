# Brand Designer Workflow
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
- For explicitly business-linked work, use repo-root `references/strategic-positioning.md` for the existing handoff builder/source-check commands; preserve the selected position and evidence labels across stages. Standalone branding needs no business-positioning exercise.
- Use root-level canonical delivery folders for approved handoff assets; keep `stages/` as working history only.
- After a user approves a direction, log the decision, archive/remove competing active alternatives, and promote approved assets before final delivery.
- Before saying a brand package is done, run the finalization gate.
- Dispatch a fresh subagent per pipeline stage whenever stages can run in parallel (e.g. motion pillars + component taxonomy scoping), and one critic subagent for the finalization gate review. Never parallelize subagents that touch the same brand-project folder.

Routing: see `references/routing.md` for the child-skill dispatch table.
Pipeline order: discovery -> naming (if needed) -> strategy -> voice -> logo -> colors -> typography -> guidelines -> export; imagery-style (`brand-asset-producer`, art-direction mode) -> motion-concept (`brand-motion-designer`, concept mode) -> imagery (`brand-asset-producer`) -> tokens (`brand-ui-kit-producer`) -> motion tokens/impls (`brand-motion-designer`) -> components (`brand-ui-component-producer`) -> screens (`brand-frontend-app-designer`).

Gates:
- `imagery-style` must be approved before any imagery asset production: medium (photo/illustration/hybrid), treatment (grading, overlays), subject mix, crop ratios, licensing, and 2-3 style frames. Template: `brand-asset-producer/references/imagery-art-direction.md`.
- `motion-concept` must be approved before tokenization: motion principles, duration/easing primitives, named signature moments (e.g. hover illustration-to-photo crossfade), and reduced-motion policy. Template: `brand-motion-designer/references/concept.md`. The later `motion` stage consumes the approved concept.

Canonical package workflow:
- Read `references/package-structure.md` when creating or reorganizing a project package.
- Use `scripts/brand/promote_artifact.py <project-dir> --artifact-id <id> --dry-run`, then `--confirm` after approval and hash checks pass.
- Read `references/finalization-gate.md` before final QA, final export, or any "are we done" answer.

Refs: `references/orchestration.md`, `references/guided-user-journey.md`, `references/design-guideline-anatomy.md`, `references/tooling-decision.md`, `references/startup-check.md`.



## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.

Default scope (lean brand sprint): discovery → naming (if needed) → strategy → voice → logo system (primary, secondary, mark, monochrome, favicon) → color → typography → short guidelines → export/brand kit. Imagery style, motion, UI tokens, component libraries and app screens are opt-in stages requested by the founder or triggered by a website/product build; do not propose them by default before product-market fit.
