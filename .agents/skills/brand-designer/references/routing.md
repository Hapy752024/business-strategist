# Routing

The orchestrator dispatches to these child skills by name, in pipeline order:

- Workspace: use `brand-workspace-manager`.
- Discovery: use `brand-discovery-interviewer`.
- Research and benchmarks: use `brand-guideline-researcher`.
- Strategy and design territories: use `brand-strategy-director`.
- Font search/ID: use `brand-typography-researcher`.
- Logo, favicon, and exports: use `brand-asset-producer`.
- UI tokens: use `brand-ui-kit-producer`.
- Motion concept and tokens: use `brand-motion-designer` (after tokens, before components).
- UI component library: use `brand-ui-component-producer` (after motion, before screens).
- Frontend apps/flows: use `brand-frontend-app-designer`.
- Quality review: use `brand-quality-reviewer`.
- Final exports/guidelines: use `brand-exporter` and `brand-guidelines-writer`.
