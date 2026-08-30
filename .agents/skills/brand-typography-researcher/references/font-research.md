# Font Research

## Source Priority

1. Existing brand assets, website CSS, Figma file, or user-provided examples.
2. Google Fonts for open-source web fonts.
3. Fontsource for npm/self-hosted open-source fonts.
4. Foundry websites for premium fonts and licensing.
5. Adobe Fonts when the user has access.
6. System font stacks when performance or licensing simplicity matters.

## Identification Methods

- Inspect website CSS for `font-family`, `@font-face`, and loaded font files.
- Search exact font names found in CSS.
- Use screenshots only as a clue; visual font identification is probabilistic.
- For Figma files, use Figma MCP/API only when available and authorized.

## Recommendation Output

Always provide 3 numbered options:

1. Option name: heading font + body font.
2. Option name: heading font + body font.
3. Option name: heading font + body font.

For each option include:

- Why it fits the brand brief.
- License/availability.
- Weights needed.
- Language/subset coverage.
- CSS or npm implementation.
- Risks: loading performance, licensing, similarity to competitors, readability.

## Validation

Render sample text when possible:

- Brand name.
- One headline.
- One paragraph.
- Button labels.
- Target-language characters, for example accents, umlauts, or non-Latin scripts.

Check for clipping, awkward metrics, poor legibility, and mismatched personality.
