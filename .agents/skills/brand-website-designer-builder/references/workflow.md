# Website workflow

1. Inspect an explicit brand manifest or start a standalone brief. Do not trigger business research automatically.
2. Load/create `website-preferences.json`; separate brand-locked, user-stated, user-selected, and agent-inferred choices.
3. Resolve the current stable Next.js version with `scripts/resolve-next-stable.mjs`; pin it and the lockfile.
4. Produce two or three lightweight territories (tokens, layout sketch, type, imagery, motion, signature device). Use screenshots or small proofs, not three production builds.
5. Ask for selection unless the user delegated it. Record the decision and rationale in `website-manifest.json`.
6. Build the hero/navigation/primary CTA vertical slice, capture 375px and desktop screenshots, and fix concrete issues.
7. Complete pages, content states, localization, metadata, assets, reduced motion, and performance budgets.
8. Run `scripts/validate-site.mjs`, Playwright/axe, visual review, and the independent `brand-quality-reviewer`.
9. If requested, run experiment mode from `references/experimentation.md`.
10. Prepare a GitHub PR and Vercel Preview. Do not connect, merge, deploy production, enable analytics, or split traffic without approval.

## Output

Return the manifest path, selected direction/signature device, stack versions, asset provenance, QA status, Preview URL (if authorized), experiment status, open gaps, and next action.
