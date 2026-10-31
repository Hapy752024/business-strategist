# Review mode (route `brand-quality-reviewer`)

Review brand or website outputs for consistency, accessibility, visual quality, compliance, completeness and UI defects, before delivery and after major revisions. Review as an independent critic, not as the creator.

## Independent critic

Dispatch the `brand-critic` agent (`.claude/agents/brand-critic.md`) with only the brief, the approved territory, the final artifacts and this file's checklist; never the creator's reasoning or expected answer. The critic reads and reports; it never edits. Without subagents, run the checklist yourself and say the review was not independent.

## Review loop

1. Review against the brief, approved territory and guidelines, then [best-practices guidelines](best-practices-guidelines.md).
2. Inspect visuals (below) whenever artifacts are visual.
3. For final packages, run `python3 .agents/skills/brand-identity/scripts/audit-brand-package.py <project-dir>` (required folders, export manifests, local HTML references, stale paths/tooling statements).
4. List findings HIGH, MEDIUM, LOW; fix HIGH; rerun until no HIGH remains or the user explicitly accepts the risk.
5. End with fix, approve, request revision or accept residual risk.

## What to check

- Brief and territory alignment; human-centred fit (audience, country/culture, USP, trust cues, emotion).
- Business-linked work: run `python3 scripts/brand/validate_business_to_brand_handoff.py <snapshot.json> --check-sources`; compare service claims, tone, visuals, proof and CTAs with the position and its exclusions; load repo-root `references/strategic-positioning.md` for material conflicts. Report changed/unavailable sources and affected outputs; stylistic differences alone are not strategy drift. Standalone work needs no snapshot.
- Motion coherence: every element spec in `motion/motion-guidelines.md` names a pillar defined in `motion/motion-tokens.ts`; run `.agents/skills/brand-ui-system/scripts/validate-motion-tokens.py`.
- Component coverage: every `stages/components/scope.json` entry has a `components/<tier>/<Component>/` triplet (`.tsx`, `.test.tsx`, `.stories.tsx`); run `.agents/skills/brand-ui-system/scripts/validate-component.py --components-dir components/ --scope stages/components/scope.json`. No hardcoded hex colours; interactive components use `var(--motion-*)` or `var(--color-*)` tokens.
- Logo/asset consistency, colour/contrast, UI states, responsive behaviour, guideline completeness, export manifests, canonical package structure, and no active docs pointing to `stages/` or `old/`.
- Websites with personal data: load `.agents/skills/brand-website-designer-builder/references/privacy-design.md` and inspect layered notices, necessary collection, fair choices and actual network/storage/deletion behaviour. External resources: load `.agents/skills/brand-website-designer-builder/references/external-link-maintenance.md`. A policy page or a successful HTTP response alone is insufficient evidence.

## Visual review

Inspect alignment, spacing rhythm, clipping/overlap, control and touch-target sizes, logo legibility at 16/32/64 px and large, colour roles, contrast and focus visibility, asset rendering (missing images, broken SVGs, jagged exports), and whether audience, USP and emotion read without the creator's rationale. Open favicon/app-icon sizes separately. For web/UI, take Playwright screenshots at 390x844, 768x1024, 1440x900 (and 1920x1080 when image-heavy). Run contrast checks on documented pairs, grayscale or colour-vision simulation where tooling exists, non-empty export checks, valid SVG XML, and visibly distinct default/hover/active/focus-visible/disabled/loading/error states. Visual AI review is a filter, not designer or legal review; flag subjective concerns separately from objective failures.

## Severity

HIGH: contradicts the brief, territory, audience, country/culture or buyer needs; fails to express the USP or looks generic without reason; a later stage started without approval of the previous one; full asset sets before direction selection; inconsistent or unusable logo variants; normal text below WCAG AA 4.5:1; meaningful UI graphics, focus indicators or large text below 3:1; colour-only status; missing requested UI states; overlap, clipping, illegible text, broken layout or missing assets; misleading trust cues for regulated or high-stakes industries; missing export formats without explanation; missing canonical folders or package manifest; manifests pointing to missing files; active HTML with missing local assets; no trademark similarity search recorded in `naming/checks.md` for name, tagline and mark (with date and classes); no human vector-edit pass recorded on the approved mark (who, what changed, date) since an AI raster alone is not an approved master; mark not legible at 16px favicon size and in monochrome positive and reversed.

MEDIUM: vague guidelines where rules are needed; incomplete colour roles or weak palette harmony; no font fallback or licensing notes; incomplete or untested type scale; unclear messaging hierarchy; under-specified responsive behaviour; missing safe-area guidance for marketing assets; incomplete component state behaviour; undocumented cultural/localization assumptions; active docs pointing to `stages/` or `old/`; selected and rejected alternatives still side by side.

LOW: naming clarity, minor polish, optional examples or extra do/don't examples.

## Output

```text
Findings
HIGH
1. <artifact path> - <violated criterion> - <concrete fix>
MEDIUM
1. ...
LOW
1. ...
Fix Plan
1. ...
Residual Risk
1. ...
```
