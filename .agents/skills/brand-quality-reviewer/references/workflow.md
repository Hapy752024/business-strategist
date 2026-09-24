# Brand Quality Reviewer Workflow


Review as an independent critic, not as the creator.

Check:
- Brief and approved territory alignment.
- For business-linked work, run `python3 scripts/brand/validate_business_to_brand_handoff.py <snapshot.json> --check-sources`; compare service claims, tone, visuals, proof, and CTAs against that position and its exclusions. Load repo-root `references/strategic-positioning.md` for material conflicts. Preserve uncertainty and report changed/unavailable sources and affected outputs; stylistic differences alone are not strategy drift. Standalone brand work needs no business snapshot.
- Human-centered brand fit: audience, country/culture, USP, trust cues, emotion.
- Best-practice compliance from `references/best-practices-guidelines.md`.
- Guideline completeness.
- Logo and asset consistency.
- Color/contrast/accessibility.
- UI component states and responsive behavior.
- Motion coherence: every element spec in `motion/motion-guidelines.md` references a pillar defined in `motion/motion-tokens.ts`; run `brand-motion-designer/scripts/validate-motion-tokens.py` and flag any drift.
- Component coverage: every entry in `stages/components/scope.json` has a matching `components/<tier>/<Component>/` triplet (`Component.tsx`, `Component.test.tsx`, `Component.stories.tsx`); run `brand-ui-component-producer/scripts/validate-component.py --components-dir components/ --scope stages/components/scope.json`.
- Component token wiring: no hardcoded hex colors in `components/`; all interactive components reference at least one `var(--motion-*)` or `var(--color-*)` token.
- Visual polish: spacing, alignment, hierarchy, overlaps, legibility.
- File/export manifest completeness.
- Canonical package structure: root delivery folders are active handoff; `stages/` and `old/` are history.
- Active documentation must not point to stale stage/archive paths unless explicitly discussing history.

Return findings first, ordered HIGH, MEDIUM, LOW.
End with a clear recommendation: fix, approve, request revision, or accept residual risk.

If subagents are available, ask one critic subagent to review without seeing the creator's rationale.

Fix HIGH issues, rerun review, then deliver.

Use:
- `references/review-checklist.md` for severity and output format.
- `references/best-practices-guidelines.md` for brand, color, UX, and UI standards.
- `references/visual-review.md` for screenshot/image inspection.
- `scripts/audit-brand-package.py <project-dir>` for final package checks: required folders, export manifests, local HTML references, and stale path/tooling statements.


## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
