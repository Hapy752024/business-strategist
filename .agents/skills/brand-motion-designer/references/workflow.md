# Imported workflow

## Procedure

# Brand Motion Designer

## Success Criteria
- Quantitative: >=90% trigger on motion/transition requests; <=3 iteration rounds per pillar; zero invalid token files at Stop.
- Qualitative: user does not redirect mid-loop; motion feels coherent across elements; developer implements reference impls on first read.

## Workflow
1. Read `references/pillars.md` and present the pillar menu.
2. For each chosen pillar, run `references/iteration-loop.md` to tune tokens.
3. Read `references/element-taxonomy.md`; iterate element motion specs per selected categories.
4. Run `references/coherence-review.md`; produce `coherence-review.md`.
5. Promote approved specs to `motion/` via `scripts/promote-motion-iteration.py`.
6. Generate final reference implementations; validate with `scripts/validate-motion-tokens.py`.

## Rules
- Top-down tokens: element specs reference pillars by name.
- Exploration demos are HTML+CSS; final reference impls are Next.js + Framer Motion (or CSS keyframes / View Transitions API for page-level).
- Cite at least one benchmark per pillar from `references/benchmarks.md`.
- Outputs live under `brand-projects/<name>/motion/` (canonical) and `stages/motion/` (working).
- Dispatch fresh subagents per `references/subagent-dispatch.md` whenever work parallelizes.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
