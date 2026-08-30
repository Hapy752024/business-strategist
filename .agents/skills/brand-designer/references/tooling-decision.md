# Tooling Decision

## No Extra Access Needed

Use local files and built-in agent tools when the user only needs:

- Brand brief.
- Research synthesis.
- Guidelines markdown.
- SVG logo masters.
- CSS/JSON design tokens.
- Basic UI component templates.

## CLI Tools Worth Having

Ask for installation/access only when exports are required:

- Inkscape CLI: SVG to PNG/PDF/EPS.
- ImageMagick: ICO files and raster resizing.
- CairoSVG: Python fallback for SVG to PNG/PDF/PS.
- Sharp: Node fallback for SVG/PNG/WebP pipelines.

Temporary install policy:

- Use `.brand-tools/venv` for temporary Python dependencies: Pillow and CairoSVG.
- Do not silently install anything.
- Inkscape and ImageMagick are system tools; ask before installing via apt, brew, choco, or winget.
- Linux/WSL: apt commands are generated.
- macOS: Homebrew commands are generated.
- Windows: winget commands are generated.
- If the user declines system tools, continue with SVG masters and Python fallback exports where possible.

## MCP/API Worth Having

Ask for access only when the deliverable depends on it:

- Web search/scrape MCP/API: competitor research, inspiration capture, official asset lookup.
- OpenRouter API: preferred router for configurable image-generation alternatives across multiple models.
- Recraft API: preferred direct provider when editable vector/SVG generation is required and router support is insufficient.
- Figma MCP/API: collaborative design files, token import, designer handoff.
- Image generation API/MCP: moodboards, illustration systems, campaign imagery, social graphics.
- Font/provider APIs: checking font availability and licensing.
- Brand asset/press-kit sources: official logos and product imagery for existing brands.

## Recommendation

For a new CI/CD generator, start with local markdown + SVG + Inkscape export CLI. Use OpenRouter for model comparison and multiple visual alternatives. Add direct Recraft only for vector/SVG generation gaps, and add Figma MCP only for design handoff.

## Recraft Vs Generic SVG Makers

Recraft is an AI design/image model provider. It can generate polished raster and vector-style design outputs from prompts and is useful for concept exploration, illustration systems, and sometimes editable vector directions.

SVG makers are deterministic tools or libraries that create, edit, optimize, or convert SVG files. They do not understand brand strategy by themselves; they preserve and export geometry.

Use them together:

1. Generate alternatives with OpenRouter/Recraft.
2. Select a direction.
3. Rebuild the final mark as clean SVG geometry.
4. Export with Inkscape.

## Anthropic Frontend-Design Usage

Use `frontend-design` only after the brand territory and tokens exist. It should consume the brand guidelines to produce polished screens, component demos, and UI refinements. Do not let it decide the core brand strategy, logo system, or legal/asset governance.
