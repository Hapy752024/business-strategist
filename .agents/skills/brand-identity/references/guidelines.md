# Guidelines mode (route `brand-guidelines-writer`)

Assemble the final source of truth from confirmed strategy, research, assets, tokens and UI outputs.

## Gates

1. Do not write final guidelines until every requested stage has explicit user approval.
2. Do not finalize while review mode has unresolved HIGH findings.
3. For unresolved decisions, list what is missing, recommend what to approve or revise next, and ask for one decision at a time.

## Outline

- **Brand foundation:** purpose, audience, target segment and primary country/region, positioning, USP, values, personality, voice and tone; research summary and sources.
- **Verbal identity:** personality, tone sliders and channel flex, value proposition, message pillars with proof, tagline, vocabulary, do/don't examples (from `voice/`).
- **Visual identity:** logo system and usage (variants, clear space, minimum size, misuse), colour system, typography, iconography, imagery.
- **Corporate design:** layout, spacing, grid, radius, elevation.
- **Motion:** when in scope, pillars, element specs and do's/don'ts sourced verbatim from `motion/motion-guidelines.md`.
- **UI system:** tokens, UI components and states, accessibility, responsive behaviour; when in scope, the component library install path, token wiring and tier breakdown from `components/README.md`.
- **Marketing system:** favicon and app icons, social avatars and banners, presentation/document templates, email and ad templates if requested.
- **Governance:** do's and don'ts, file manifest, known gaps, next review checklist; the CSS branding file and agent-readable brand skill from export mode.

## Writing pattern

Write tokens plus rules, not taste language: token (exact value), role (where used), rationale (why it fits), constraint (where not to use it), example (correct usage). Strong guides, like the `awesome-design` DESIGN.md collection, always cover hierarchy, spacing, typography principles, grid/container, buttons, breakpoints, touch targets, radius, components and do/don't rules; treat these as core sections.
