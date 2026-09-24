# Pipeline Change: Imagery-Style Gate + Motion-Concept Stage

Date: 2026-09-04. Requested by founder before the imagery stage of `italy-retiree-move`.

## Problem

1. The pipeline jumps from typography straight to `imagery` asset production with no art-direction gate. Nothing decides *medium* (photo / illustration / mosaic / hybrid), *treatment* (grading, dark overlay, duotone), *subject mix* (landscape vs human faces vs detail), or crop rules before assets get made.
2. Motion exists only as `motion` (tokens + reference implementations) **after tokens** — a late, technical stage. Nothing defines the *animation concept* (principles, signature moments like hover drawn→realistic image transitions) early enough to steer imagery and component choices.
3. No skill owns "imagery" in `brand-designer/references/routing.md` at all — the stage is in the workspace enum but unrouted.

## Best-practice findings (web research, 2026-09-04)

- **Art direction before shot lists.** Professional practice is a visual-strategy document (often "moodboard" or "art-direction brief") covering: medium/style, color story, lighting, 3–5 mood words, shot ratio (e.g. 70% candid / 30% directed), subject mix, then *style frames* — a few fully-realized example images that lock the style before batch production.
- **Retouch/grading briefs** are separate from capture: overlay, duotone, grain, warmth, contrast targets are decided once and applied to every asset.
- **Crop ratios and safe zones** are defined per channel (hero, card, social, avatar) so assets are reusable.
- **Motion language is defined early, as "brand voice in motion"**: principles + primitives (durations 200–500 ms for UI, easing curves tied to the brand concept, e.g. VW "Rhythm of the Road", Greenhouse motion language, Google Material). Tokenization comes later.
- **Signature moments** (one or two memorable interactions, e.g. hover crossfade from illustration to photograph) are named explicitly in the concept so designers and developers build toward them.
- **Reduced-motion and accessibility** (prefers-reduced-motion fallback, no vestibular triggers) belong in the concept, not as a retrofit.

## Proposed pipeline

```text
... typography -> imagery-style -> motion-concept -> imagery -> tokens -> motion -> components -> screens ...
```

Two new gates, no new skills:

1. **`imagery-style`** (new stage, owner: `brand-asset-producer` in art-direction mode)
   Deliverable: `stages/imagery-style/art-direction.md` + moodboard/style frames. Required decisions:
   - Medium: realistic photography / illustration / hybrid (e.g. photo + line-art overlay) / mosaic-texture accents.
   - Treatment: grading target, overlay policy (e.g. warm dark overlay at 40% for text-bearing heroes), duotone or full-color.
   - Subject mix: ratio of place/nature vs human faces vs detail shots; candid-vs-directed ratio; age representation rule for a 50+ audience.
   - Crop ratios + safe zones per channel; licensing policy (stock vs generated vs commissioned).
   - 2–3 style frames rendered for approval before any batch production.

2. **`motion-concept`** (new stage, owner: `brand-motion-designer` in concept mode, new `references/concept.md`)
   Deliverable: `stages/motion-concept/motion-concept.md`. Required decisions:
   - 3 motion principles (voice in motion, tied to brand territories).
   - Primitive ranges: duration bands, easing curve(s) named after the brand concept.
   - Signature moments: e.g. hero hover crossfade illustration→photograph; scroll reveal policy; page transition style.
   - Reduced-motion fallback policy.
   The existing `motion` stage (after tokens) stays, but consumes the approved concept instead of starting from a pillar menu cold.

## Files to change

| File | Change |
|---|---|
| `.claude/skills/brand-workspace-manager/scripts/manage-brand-workspace.py` | STAGES: insert `imagery-style`, `motion-concept` after `typography`, before `imagery` |
| `.claude/skills/brand-workspace-manager/scripts/workspace_cli.py` | same STAGES tuple |
| `.claude/skills/brand-designer/references/workflow.md` | pipeline-order line + gate descriptions |
| `.claude/skills/brand-designer/references/routing.md` | route imagery-style → brand-asset-producer (art-direction mode); motion-concept + imagery ownership lines |
| `.claude/skills/brand-asset-producer/references/imagery-art-direction.md` | NEW: brief template (medium, treatment, subject mix, crops, licensing, style frames) |
| `.claude/skills/brand-motion-designer/references/concept.md` | NEW: concept template (principles, primitives, signature moments, reduced motion) |
| `.claude/skills/brand-motion-designer/references/workflow.md` | step 0: run/confirm approved motion-concept before pillars |
| `.claude/skills/brand-designer/references/package-structure.md` | note `imagery-style/` and `motion/` canonical folders |
| `config/skill-catalog.json` | update brand-asset-producer + brand-motion-designer intent/artifacts/prerequisites |
| `config/routing-evals.json` | +2 evals: imagery-style routing, motion-concept routing |

Then run `scripts/validate_setup.sh` and `scripts/run_evals.py` to keep CI green.
