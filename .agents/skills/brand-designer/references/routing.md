# Routing

The orchestrator dispatches to these child skills by name, in pipeline order:

- Workspace: use `brand-workspace-manager`.
- Discovery: use `brand-discovery-interviewer`.
- Research and benchmarks: use `brand-guideline-researcher`.
- Strategy and design territories: use `brand-strategy-director`.
- Font search/ID: use `brand-typography-researcher`.
- Logo, favicon, and exports: use `brand-asset-producer`.
- Imagery art direction (style gate, before any imagery production): use `brand-asset-producer` in art-direction mode per `brand-asset-producer/references/imagery-art-direction.md`.
- Motion concept (principles, signature moments; after typography, before imagery): use `brand-motion-designer` in concept mode per `brand-motion-designer/references/concept.md`.
- Imagery assets (moodboards, hero images, illustration sets): use `brand-asset-producer` (only after the imagery-style gate is approved).
- UI tokens: use `brand-ui-kit-producer`.
- Motion tokens and reference implementations: use `brand-motion-designer` (after tokens, before components; consumes the approved motion concept).
- UI component library: use `brand-ui-component-producer` (after motion, before screens).
- Frontend apps/flows: use `brand-frontend-app-designer`.
- Quality review: use `brand-quality-reviewer`.
- Final exports/guidelines: use `brand-exporter` and `brand-guidelines-writer`.
