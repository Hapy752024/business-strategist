# Motion mode (route `brand-motion-designer`)

Design the brand motion system: concept, pillar tokens, element specs and reference implementations.

## Procedure

0. Concept gate: when the pipeline is at `motion-concept` or no approved concept exists, run [motion concept](motion-concept.md) and get `stages/motion-concept/motion-concept.md` approved. Otherwise treat the approved concept as fixed input; do not reopen it.
1. Present the [pillar](pillars.md) menu and propose 2-4 pillars from the brand personality.
2. Tune each chosen pillar with the [iteration loop](iteration-loop.md) (2-3 HTML demos such as Snappy/Smooth/Bouncy, user picks, max 3 rounds).
3. Iterate element specs per selected [element taxonomy](element-taxonomy.md) categories.
4. Run the [coherence review](coherence-review.md); `needs-rework` blocks final implementations.
5. Promote approved specs to `motion/` with `scripts/promote-motion-iteration.py` only after the user locks them.
6. Write final reference implementations; validate tokens with `scripts/validate-motion-tokens.py --css motion-tokens.css --ts motion-tokens.ts` ([token mapping](token-mapping.md), [output contract](motion-output-contract.md)).

Script paths are relative to `.agents/skills/brand-ui-system/`; `scripts/generate-demo.py` scaffolds demos.

## Rules

- Top-down tokens: element specs reference pillars by name; overrides need a recorded justification.
- Exploration demos are standalone HTML+CSS; final implementations are Next.js + Framer Motion (CSS keyframes or View Transitions API for page-level motion).
- Cite at least one [benchmark](benchmarks.md) per pillar.
- Outputs: `projects/<name>/branding/motion/` (canonical) and `stages/motion/` (working).

## Subagents

Pass exact paths, pillar names and token filenames, never this conversation:

- Three demo variants in parallel, one `option-N.html` each.
- One per pillar when two pillars are tuned in the same round (`stages/motion/pillars/<pillar>/`).
- One per category when 4+ element categories are approved.
- One cold critic for coherence: every pillar named by an element spec exists in `motion/motion-tokens.ts`.
- One research subagent when the user names a new reference product, to append 2-3 patterns to the benchmarks.

Never parallelize subagents that touch the same file; do single-variant work inline.

## Success criteria

- Quantitative: at least 90% trigger on motion and transition requests; at most 3 iteration rounds per pillar; zero invalid token files at completion.
- Qualitative: the user does not redirect mid-loop; motion feels coherent across elements; a developer can implement the reference implementations from one read.
