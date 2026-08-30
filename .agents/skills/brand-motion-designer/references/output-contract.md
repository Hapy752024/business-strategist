# Output Contract

## Purpose
Define the exact file shapes the motion skill must produce before its Stop hook will allow the skill to declare done.

## Canonical Delivery: `brand-projects/<name>/motion/`

```
motion/
├── motion-guidelines.md
├── motion-tokens.css
├── motion-tokens.ts
└── reference-implementations/
    ├── press-feedback/
    ├── page-transitions/
    ├── data-reveal/
    ├── morph-grow/
    ├── drag-reorder/
    ├── loading-states/
    ├── notifications/
    └── scroll-driven/
```

### `motion-guidelines.md` (required sections)
1. **Pillars** — for each chosen pillar: name, feel description, default tokens, benchmark cited (format: `Benchmark: <pattern name> from references/benchmarks.md`).
2. **Element Motion Specs** — for each in-scope element: category, element, pillar reference, CSS properties, overrides with justification.
3. **Coherence Verdict** — copy of the verdict from `stages/motion/coherence-review.md`.
4. **Implementation Notes** — which reference implementation file implements each element spec.

### `motion-tokens.css`
- Must conform to `references/token-mapping.md` schema.
- Must pass `scripts/validate-motion-tokens.py --css motion-tokens.css --ts motion-tokens.ts`.

### `motion-tokens.ts`
- Must conform to `references/token-mapping.md` schema.
- Must pass the same validator.

### `reference-implementations/<category>/<element>.tsx`
- Next.js client component ("use client" directive) using Framer Motion by default.
- For page-level transitions: CSS keyframes or View Transitions API may be used instead.
- Each file imports from `../../motion-tokens.ts` (or its CSS equivalent) and references pillar tokens by name.
- Each file's header comment names the source spec it implements: `// Implements: stages/motion/elements/<category>/<element>/spec.json`.

## Working History: `brand-projects/<name>/stages/motion/`

```
stages/motion/
├── pillars/
│   └── <pillar-name>/
│       ├── option-1.html
│       ├── option-2.html
│       ├── option-3.html
│       ├── tokens.json
│       └── benchmark-citation.md
├── elements/
│   └── <category>/<element>/
│       ├── option-1.html
│       ├── option-2.html
│       ├── option-3.html
│       └── spec.json
├── coherence-review.md
├── iteration-state.json
└── iteration-manifest.json
```

### `iteration-manifest.json` (append-only log)
Each PostToolUse hook appends a record:
```json
{"timestamp": "<iso>", "phase": "pillar|element", "target": "<name>", "round": <int>, "artifact": "<path>", "feedback": "<text or null>", "action": "generate|refine|lock"}
```

## Stop Hook Requirements
The Stop hook (see `.claude/settings.json`) refuses to mark the skill done unless:
1. `motion/motion-guidelines.md` exists and contains all 4 required sections.
2. `motion/motion-tokens.css` and `motion/motion-tokens.ts` pass `scripts/validate-motion-tokens.py`.
3. `motion/coherence-review.md` exists (a copy of `stages/motion/coherence-review.md`) and its Overall Verdict is not `needs-rework`.
4. At least one `Benchmark: <pattern name> from references/benchmarks.md` citation appears per chosen pillar in `motion-guidelines.md`.
