# Motion Pillars

## Purpose
Define the foundational motion archetypes for a brand. Each pillar carries its own token set; element motion references pillars by name.

## Fixed Archetype Menu

### Natural
- Feel: physics-based, organic deceleration.
- Default tokens: durations 200–400ms; easings `ease-out`, `ease-in-out`.
- Use for: card hovers, list item reordering, sheet opens.

### Responsive
- Feel: immediate feedback, no perceived lag.
- Default tokens: durations 100–200ms; easings `ease-out-quart`, `cubic-bezier(0.25, 1, 0.5, 1)`.
- Use for: button presses, toggles, tap feedback.

### Expressive
- Feel: personality, delight, spring physics.
- Default tokens: `spring(stiffness=300, damping=30)`, custom curves.
- Use for: hero animations, success states, micro-interactions.

### Directional
- Feel: consistent spatial model; elements enter/exit from predictable origins.
- Default tokens: `translateX/Y` from origin; durations 200–300ms; `ease-out`.
- Use for: page transitions, drawer slides, popover entry.

### Continuous
- Feel: elements morph, never teleport.
- Default tokens: `clip-path`, `scale`, `opacity` chains; durations 300–500ms; `ease-in-out`.
- Use for: shared element transitions, image zoom, expand-to-detail.

## Custom Pillars
- The user may name a custom pillar. The skill helps define its feel, default tokens, and use cases before tuning begins.

## Per-Pillar Tuning Procedure
1. Ask the user what feel they want for this pillar; collect a benchmark reference if they named one ("make it feel like Airbnb's card hover").
2. Use `scripts/generate-demo.py --pillar <name> --tokens <json>` to scaffold 2–3 distinct HTML+CSS demo options under `stages/motion/pillars/<pillar-name>/option-N.html`.
3. Tell the user to open each demo in a browser and report which option feels closest.
4. Iterate on the chosen option (refine tokens, regenerate) until the user approves.
5. Lock the pillar's token set; write it to `stages/motion/pillars/<pillar-name>/tokens.json` with fields: `durations` (list of {variant, ms}), `easings` (list of {variant, cssBezier, framerEasing}), `springs` (list of {variant, stiffness, damping}).
6. Record the benchmark pattern cited (from `references/benchmarks.md`) in `stages/motion/pillars/<pillar-name>/benchmark-citation.md`.

## Pillar Selection Heuristic
- Read `brand-strategy-director` outputs (brand personality, audience, tone) from `brand-projects/<name>/strategy/`.
- Map brand personality traits to pillar archetypes:
  - "Trustworthy, professional" → Natural + Responsive
  - "Playful, energetic" → Expressive + Continuous
  - "Premium, refined" → Natural + Directional
  - "Data-dense, analytical" → Responsive + Directional
- Propose 2–4 pillars; let the user adjust before tuning begins.
