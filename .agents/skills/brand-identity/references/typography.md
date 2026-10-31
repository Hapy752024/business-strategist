# Typography mode (route `brand-typography-researcher`)

Use when typography is in scope or the user supplies font examples, images or sites.

## Procedure

1. Source priority: existing brand assets, website CSS, Figma or user examples -> Google Fonts -> Fontsource (npm/self-hosted) -> foundry sites for premium fonts and licensing -> Adobe Fonts when the user has access -> system stacks when performance or licensing simplicity matters.
2. Identify fonts from CSS (`font-family`, `@font-face`, loaded files) and search exact names. Screenshots are only a clue; visual identification is probabilistic. Use Figma MCP/API only when available and authorized.
3. Check licence/availability and language coverage for the target country/region before recommending.
4. Propose exactly 3 numbered options (heading + body font). For each: fit with the brief, licence/availability, weights, language/subset coverage, implementation (CSS import, npm package, system stack or licensed file), and risks (loading, licensing, similarity to competitors, readability).
5. Render samples where possible: brand name, a headline, a paragraph, button labels and target-language characters (accents, umlauts, non-Latin scripts). Check clipping, awkward metrics, legibility and personality fit.
6. Recommend one option and tell the user what to approve or compare next.
