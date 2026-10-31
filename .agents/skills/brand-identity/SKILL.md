---
name: brand-identity
description: Brand identity work from brief to package - discovery, workspace, research, typography, strategy, voice, naming, review, guidelines and export. Use for logos, brand identity, guidelines, brand QA, or orchestrating a brand.
---

# Brand Identity

One skill, one mode per former brand specialist. The route ID picks the mode; read only that mode's reference.

| Route ID | Mode | Read |
|---|---|---|
| `standalone-brand` | orchestration | [orchestration](references/orchestration.md) |
| `brand-discovery-interviewer` | discovery | [discovery](references/discovery.md), [question bank](references/question-bank.md) |
| `brand-workspace-manager` | workspace | [workspace](references/workspace.md) |
| `brand-research` | research | [research](references/research.md) |
| `brand-typography-researcher` | typography | [typography](references/typography.md) |
| `brand-strategy-director` | strategy | [strategy](references/strategy.md), [verbal identity](references/verbal-identity.md), [naming and checks](references/naming-and-checks.md) |
| `brand-guidelines-writer` | guidelines | [guidelines](references/guidelines.md) |
| `brand-exporter` | export | [export](references/export.md) |
| `brand-quality-reviewer` | review | [review](references/review.md), [best-practices guidelines](references/best-practices-guidelines.md) |

Packaging and the final gate: [package structure](references/package-structure.md), [finalization gate](references/finalization-gate.md).

Sibling skills: `brand-asset-producer` owns logos, favicons, imagery and every paid generation; `brand-ui-system` owns UI tokens, motion, components and app screens; `brand-website-designer-builder` owns marketing websites.

## Standing rules

- Branding starts from its own brief; business research is optional unless the user imports a Business handoff (repo-root `references/subprojects.md`).
- One question at a time; numbered options the user can answer with a number.
- Search the web before strategy or design recommendations; record sources with dates; separate evidence from interpretation.
- Stage gates hold: discovery before strategy, an approved territory before final assets, one approved stage before the next, review before finalization, the finalization gate before "done" (numbered list in orchestration mode).
- Paid asset generation needs the user's explicit approval and runs only through `brand-asset-producer`.
- Never promote an unapproved artifact: `scripts/brand/promote_artifact.py` and `workspace_cli.py promote` stay dry runs until `--confirm` after approval; a conflicting destination needs separate replacement approval.
- Never delete old iterations; archive them to `old/<stage>/<timestamp>/`.
- Export and workspace modes write files: run them only on explicit request or as an orchestration step.
- Review mode dispatches the independent `brand-critic` agent (`.claude/agents/brand-critic.md`) without the creator's rationale.

## Output

Return the requested artifacts with provenance, approval status, unresolved gaps and one recommended next action. Run the mode's validators before delivery; do not claim completion with unresolved HIGH findings.
