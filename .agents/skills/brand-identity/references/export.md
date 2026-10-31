# Export mode (route `brand-exporter`)

Export approved brand decisions as CSS variables and an agent-readable design package. This mode writes delivery files: run it only on explicit request.

## Gates

1. Run only after all requested stages are approved and HIGH review findings are resolved; if finalization approval is not explicit, ask the user to confirm first.
2. The [finalization gate](finalization-gate.md) has passed, or list the residual risks.
3. Export only approved artifacts; never unapproved options.

## Create

- `tokens/branding.css`: CSS custom properties with stable kebab-case names, e.g. `--brand-color-primary`, `--brand-color-primary-hover`, secondary, accent, success, warning, error, info, background, surface, text, text-muted, border, focus, `--brand-font-heading`, `--brand-font-body`, `--brand-radius-sm|md|lg`, `--brand-spacing-unit`; add aliases such as `--color-primary: var(--brand-color-primary)` when useful. No ambiguous names like `--blue`.
- `tokens/brand-tokens.json`: structured values (`color.primary`, `component.button.primary`).
- `PACKAGE-MANIFEST.md` if missing.
- `agent-skill/<brand-slug>/SKILL.md` (frontmatter name and description, overview, when to use, required behaviour, link to CSS/tokens; note that `DESIGN.md` lives in the brand workspace export, not the repo) plus `agent-skill/<brand-slug>/references/DESIGN.md`, `branding.css` and `brand-tokens.json` beside it. `DESIGN.md` covers visual theme, colour roles, typography, layout, elevation, shapes and image geometry, components and states, do's and don'ts, responsive behaviour and an agent prompt guide.
- Verbal identity: `voice/voice.json` and `voice/voice.md` for marketing and website copy.
- Motion, when approved: copy `motion/motion-tokens.css`, `motion/motion-tokens.ts` and `motion/motion-guidelines.md` into the package under `motion/`.
- Components, when approved: copy the `components/` library including `components/README.md` under `components/`.
- Update `PACKAGE-MANIFEST.md` with `## Motion` (token files and guidelines) and `## Components` (library path and install instructions) sections.

Scaffold with `python3 .agents/skills/brand-identity/scripts/create-brand-agent-skill.py`. After export, tell the user which files to use next for CSS, agents and documentation.
