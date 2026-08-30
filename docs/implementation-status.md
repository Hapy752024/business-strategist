# Business strategist / branding implementation status

Implemented in this repository:

- Imported all 15 source branding skills plus `setup-multiharness-project`; compact `SKILL.md` routers keep entries within the 30-line context budget while complete procedures remain in `references/workflow.md`.
- Added deterministic route selection (`scripts/route_workflow.py`) and a 37-skill catalog with collision evals.
- Added project control plane with atomic, revision-checked manifests (`scripts/project_workspace.py`), full brand stages, and resumable website manifests.
- Added explicit business-to-brand snapshot/validation with provenance and coverage gaps; no automatic transition from validation to branding.
- Added the standalone `brand-website-designer-builder` skill: preference profile, creative territories, anti-template review, responsive/accessibility/performance gates, Next.js stable resolver, GitHub/Vercel release rules, and optional one-variable A/B mode.
- Added approval-gated, server/build-time FAL adapter with budget, dimensions, seed, retention, redaction, and no-client-secret checks.
- Added migration inventory/checksums under `docs/migrations/`, templates, schemas, and offline integration tests.

Requires explicit user authorization at execution time:

- Installing dependencies or creating a real Next.js site in a selected target repository.
- Connecting GitHub to Vercel, creating Preview/Production deployments, enabling analytics/flags, or changing production traffic.
- Any paid FAL generation; default behavior is a dry run.
