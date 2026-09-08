---
name: brand-quality-reviewer
description: Review brand outputs for consistency, accessibility, visual quality, compliance, completeness, and UI defects. Use before delivery and after major revisions.
---

# Brand Quality Reviewer

Read `references/workflow.md` for the complete procedure. Load only the additional references needed for the requested stage.

## Procedure

Use the imported workflow and keep state in the active manifest.
Check motion coherence (`motion-guidelines.md`) and component coverage (`scope.json`) with `validate-motion-tokens.py` and `validate-component.py` where present.

## Output

Return the requested artifacts, provenance, unresolved gaps, and next action.

## Quality Checklist

Run the relevant validators before delivery; never promote unapproved artifacts.
