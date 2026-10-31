# Orchestration mode (route `standalone-brand`)

Run the whole brand pipeline: keep state in the brand manifest, run each stage through its `brand-identity` mode or sibling skill, and stop at every gate below.

## Startup

1. Run `python3 .agents/skills/brand-identity/scripts/check-brand-tooling.py`. When export tooling is missing, offer: 1. continue discovery/strategy and install later; 2. temporary Python install (`python3 .agents/skills/brand-identity/scripts/install-brand-tooling.py --mode temp`, into `.brand-tools/venv`); 3. system tools (`... install-brand-tooling.py --mode system --print-only` prints apt/brew/winget commands). Install nothing until the user picks an option.
2. Create or resume the workspace in workspace mode ([workspace](workspace.md)).
3. Local files, SVG masters and CSS/JSON tokens need no extra access. Ask for Inkscape/ImageMagick/CairoSVG only when exports are requested; ask for web search, Figma, font or image-generation access only when a deliverable depends on it. OpenRouter/Recraft alternatives are concepts: rebuild the chosen mark as clean SVG geometry and export it with Inkscape. `frontend-design` renders screens only after territory and tokens exist; it never decides strategy, logo or governance.

## Stage gates (numbered checklist; do not skip or reorder)

1. **Discovery before anything else.** Run discovery mode until the brief has every required field; summarize it and get explicit confirmation.
2. **Workspace before assets.** One project folder exists before any asset work; prior iterations move to `old/<stage>/<timestamp>/` before regeneration.
3. **Research before recommendations.** Research mode (and typography mode when fonts are in scope) runs before strategy or design advice.
4. **Naming if needed.** Naming checks ([naming-and-checks](naming-and-checks.md)) run before logo or tagline approval.
5. **Strategy approval before final assets.** Present 2-3 design territories; the user chooses, combines or rejects them. No final logo, colour, type, UI kit or guideline work before an approved territory.
6. **Voice after strategy, before logo** ([verbal identity](verbal-identity.md)).
7. **One stage at a time.** Default order: logo direction -> logo refinements and variants -> colour -> typography -> (opt-in) imagery style -> motion concept -> imagery -> UI tokens -> motion tokens -> components -> app screens -> marketing assets -> guidelines -> export. Each stage: 3 visible alternatives, user picks a number, iterate only the selected option, archive prior files to `old/`, explicit approval before the next stage; carry approved decisions forward as constraints.
8. **Imagery-style gate** before any new imagery system: medium, treatment, subject mix, crops, licensing and 2-3 style frames (`.agents/skills/brand-asset-producer/references/imagery-art-direction.md`). Supplied photos or an approved style go straight to scoped placement, edit or generation under `../../brand-asset-producer/references/image-sourcing.md`; do not restart branding for them.
9. **Motion-concept gate** before tokenization: principles, duration/easing primitives, signature moments, reduced-motion policy (`brand-ui-system` motion mode, `.agents/skills/brand-ui-system/references/motion-concept.md`).
10. **Paid generation needs approval.** Asset generation that costs money runs only through `brand-asset-producer` after the user approves the spend.
11. **Promote only approved artifacts.** Log the decision, archive competing alternatives, then `scripts/brand/promote_artifact.py <project-dir> --artifact-id <id> --dry-run`, and `--confirm` only after approval and hash checks pass.
12. **Review before finalization.** Run review mode; fix HIGH findings and rerun until none remain or the user explicitly accepts the risk.
13. **Finalization gate before "done".** Run [finalization gate](finalization-gate.md) before final QA, export or any "are we done" answer; then guidelines and export modes.

Default scope is a lean brand sprint: discovery -> naming (if needed) -> strategy -> voice -> logo system (primary, secondary, mark, monochrome, favicon) -> colour -> typography -> short guidelines -> export. Imagery style, motion, UI tokens, components and app screens are opt-in (founder request or a website/product build); do not propose them before product-market fit.

## Stage owners

| Stage | Owner |
|---|---|
| Workspace, discovery, research, typography, strategy/voice/naming, review, guidelines, export | `brand-identity` modes |
| Logo, favicon, exports, imagery art direction, imagery | `brand-asset-producer` |
| UI tokens, motion concept and tokens, components, app screens | `brand-ui-system` modes `kit`, `motion`, `components`, `app` |

Dispatch a fresh subagent per stage when stages can run in parallel (e.g. motion pillars and component scoping) and one critic for the finalization review; never parallelize subagents that write the same brand-project folder.

## Required brief fields

Goal; deliverables; name or naming need; industry and offer; target segment and primary country/region; decision-maker/buyer/user; USP; values; personality; design preferences and constraints; good examples and why; required formats/tools.

## Quality rules

- Every visual decision maps to the brief, research or approved territory and reinforces the USP.
- Every colour token has a role; every logo variant a usage rule; UI components cover default, hover, active, focus-visible, disabled, loading/error.
- Normal text meets WCAG AA 4.5:1; large text and meaningful UI graphics 3:1.
- SVG/vector masters are the source of truth; generated assets are listed in a manifest.
- Separate evidence, interpretation and recommendation. Business-linked work uses repo-root `references/strategic-positioning.md` and preserves the selected position and evidence labels; standalone branding needs no positioning exercise.
- Root-level delivery folders are canonical ([package structure](package-structure.md)); `stages/` is working history.

## Guiding the user

- One discovery question at a time; numbered choices (`1.`, `2.`, `3.`) the user can answer with a number.
- Vague feedback: one focused clarification. Clear feedback: revise, then ask for approval of that stage. Never ask for approval of a later stage first.
- End each response with one user action and one recommended next step.
- Stage guidance: workspace (say where the folder is and what gets archived); research (summarize evidence, recommend the next decision); strategy (choose, reject or combine one of 3 territories); assets, colours, typography, UI (3 alternatives, trade-off, recommendation, wait); Motion (3 pillar/element demos such as Snappy/Smooth/Bouncy, wait before promoting); Components (3 variants per scope item, wait before token wiring); review (findings first, then approve/fix/revise/accept risk); export (which files were created and how to use them).
