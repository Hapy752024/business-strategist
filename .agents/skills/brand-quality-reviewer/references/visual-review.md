# Visual Review

Use visual review whenever outputs include logos, icons, favicons, UI screens, HTML previews, marketing templates, or generated imagery.

## What To Inspect

- Alignment and spacing rhythm.
- Text clipping, overflow, or overlap.
- Button/card/control dimensions.
- Touch target size.
- Logo legibility at 16px, 32px, 64px, and large sizes.
- Color harmony and role clarity.
- Contrast and focus visibility.
- Responsive behavior at mobile, tablet, desktop, and wide desktop.
- Asset rendering: no missing images, broken SVGs, unexpected transparency, or jagged exports.
- Strategic fit visible in the artifact: audience, USP, country/culture, and desired emotion should be recognizable without reading the creator's rationale.
- Human factors: cognitive load, scan path, hierarchy, trust cues, and whether the main action/message is immediately clear.

## Recommended Methods

For local images:

- Open PNG/SVG/PDF previews with the agent's image-view capability when available.
- Inspect favicon/app-icon sizes separately, not only the large master.

For web/UI outputs:

- Start the local preview/dev server if needed.
- Use Playwright screenshots at representative viewports:
  - 390x844 mobile.
  - 768x1024 tablet.
  - 1440x900 desktop.
  - 1920x1080 wide desktop when layout is image-heavy.
- Check screenshots visually for overlap, clipping, blank regions, unreadable text, and asset failures.

For automated checks:

- Run contrast checks for documented color pairs.
- Check color-only state communication by reviewing grayscale or color-vision-simulation output when tooling exists.
- Check exported files exist and are non-empty.
- Confirm SVG masters open as valid XML/SVG.
- For UI assets, check that default, hover, active, focus-visible, disabled, loading, and error states are visually distinct.

## Limits

Visual AI review is a quality filter, not a substitute for designer/legal review. Flag subjective concerns separately from objective failures.
