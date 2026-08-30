# Brand Finalization Gate

Run this gate before saying a brand package is done or ready for handoff.

Required checks:

1. `PACKAGE-MANIFEST.md` exists and describes canonical delivery folders.
2. Approved artifacts are promoted from `stages/` into root-level delivery folders.
3. Active docs point to canonical root folders, not stage/old paths.
4. `logos/source/` contains approved SVG masters.
5. `logos/export/` contains required PNG/ICO/PDF/EPS exports where tooling is available.
6. Export manifests exist and have zero missing files.
7. Root-level HTML files have zero missing local `src`, `href`, or `poster` references.
8. UI previews parse and have been visually checked at desktop and mobile sizes after major UI changes.
9. `motion/motion-guidelines.md` exists and references approved pillars; `motion/motion-tokens.css` and `motion/motion-tokens.ts` validate via `brand-motion-designer/scripts/validate-motion-tokens.py`.
10. `components/README.md` exists with `## Install` and `## Token Wiring` sections; `components/` validates via `brand-ui-component-producer/scripts/validate-component.py` against `stages/components/scope.json`.
11. Motion pillars referenced by element specs all exist in `motion/motion-tokens.ts` (coherence check).
12. Approved option decisions are logged and rejected alternatives are removed from active docs/previews.
13. QA report lists residual risks, not outdated resolved gaps.

Recommended scripts:

- `brand-designer/scripts/promote-approved-assets.py` to copy approved stage files into canonical folders.
- `brand-quality-reviewer/scripts/audit-brand-package.py` to verify manifests, HTML refs, stale paths, and required files.
- `brand-asset-producer/scripts/export-logo-package.py` to regenerate logo exports from SVG masters.

Stop and fix any HIGH issue before final delivery. If a MEDIUM issue remains, document the residual risk explicitly.
