# Imported workflow

## Procedure

# Brand Asset Producer

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Use SVG/vector masters first.

Produce only assets that map to the approved brief and territory.

Work in stage gates: show exactly 3 visible alternatives, ask the user which numbered option to pursue, iterate on that option, and wait for approval before producing variants/exports.
For every asset response, tell the user what to inspect and recommend the next action: choose, revise, approve, or export.

Required variants when logo work is requested:
- Primary.
- Secondary or horizontal.
- Icon/mark.
- Square avatar.
- Monochrome dark/light.
- Reversed.
- Favicon-safe.

After a logo direction is approved:
- Keep approved SVG masters in `logos/source/`.
- Generate exports under `logos/export/small/`, `logos/export/wordmark/`, `logos/export/pdf/`, and `logos/export/eps/` when tooling is available.
- Generate manifests for every export folder.
- Regenerate exports whenever approved SVG logo geometry changes.
- Do not leave partial export status ambiguous; document missing formats only when tooling is unavailable or the user accepts the gap.

Use `references/asset-rules.md` before designing.
Use `scripts/export-brand-assets.py` for SVG exports when local tools exist.
Prefer `scripts/export-logo-package.py <logos/source> <logos/export>` for final approved logo packages.
Use `assets/.env.example` and `scripts/generate-openrouter-images.py` for optional image-model alternatives.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
