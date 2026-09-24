# Brand Asset Producer Workflow


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

For FAL generation, first run `python3 scripts/fal_assets.py ...` in dry-run mode and show model, dimensions, variants, estimated cost, maximum cost, and approval ID. A paid request requires both `--execute` and `--confirm`. When the completed provider JSON is available, immediately run `python3 scripts/brand/finalize_fal_assets.py --response <result.json> --output-dir <local-assets> --record <asset-record.json> --expected-width <px> --expected-height <px>`. The finalizer accepts validated PNG/JPEG outputs from trusted FAL hosts, enforces size/MIME/dimensions, hashes local files, and persists no temporary URL. Record finalized files as candidate artifacts before approval/promotion.


## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
