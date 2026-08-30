# Asset Rules

## Logo Rules

- Start with 3 distinct logo alternatives.
- Do not produce full logo variant/export sets until one logo direction is approved.
- Iterate on only the selected numbered logo option.
- Keep the mark legible at 16px and 32px if used as favicon.
- Avoid raster-only master logos.
- Avoid unlicensed proprietary type outlines.
- Avoid resembling known competitors or protected marks.
- Define clear-space and minimum-size rules.
- Provide misuse examples in guidelines.

## Export Rules

Recommended source:

- SVG for logos, marks, favicons, and icons.

Recommended exports:

- PNG: 16, 32, 48, 64, 128, 256, 512, 1024.
- ICO: favicon bundle.
- EPS/PDF: print/vector handoff if tooling exists.

Canonical final logo package:

- `logos/source/`: approved SVG masters.
- `logos/export/small/`: favicon and square-mark PNG/ICO exports.
- `logos/export/wordmark/`: wordmark PNG exports.
- `logos/export/pdf/`: PDF exports for every approved SVG master.
- `logos/export/eps/`: EPS exports for every approved SVG master when Inkscape is available.
- Each export folder must include `export-manifest.json`.
- If the approved SVG geometry changes, regenerate all affected exports before final handoff.

Preferred local exporter:

- Inkscape CLI for SVG to PNG/PDF/EPS when installed.
- Pillow for ICO assembly from exported PNGs.
- CairoSVG only as a fallback when Inkscape is unavailable.
- For final packages, prefer `scripts/export-logo-package.py <logos/source> <logos/export>`.

Runtime installation:

- Do not install dependencies silently.
- If exports are requested and tools are missing, ask before installing.
- Prefer temporary `.brand-tools/venv` install for Pillow/CairoSVG.
- Ask separately before installing system tools such as Inkscape/ImageMagick.
- Continue with SVG masters even if export tools are unavailable.

## AI Image Alternatives

Use OpenRouter when the user wants multiple image/model alternatives:

- Configure `OPENROUTER_IMAGE_MODELS` as comma-separated model ids.
- Configure `OPENROUTER_IMAGE_ALTERNATIVES` as the count per prompt/model.
- Default to 3 alternatives for user comparison.
- Use generated raster images for exploration, moodboards, illustrations, and marketing assets.
- Do not treat raster image generations as final logo masters. Convert approved directions into SVG.

Use Recraft directly only when OpenRouter does not expose the needed vector/SVG feature.

## Manifest

For every exported file, record:

- Source file.
- Output file.
- Format.
- Size/dimensions.
- Intended usage.
- Notes or tool warnings.

Before delivery, verify each manifest entry points to an existing file.
