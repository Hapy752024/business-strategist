# UI System Rules

## Core Components

- Buttons: primary, secondary, tertiary/ghost, destructive, icon.
- Links.
- Inputs, textareas, selects.
- Checkbox, radio, toggle.
- Cards and containers.
- Badges/tags/chips.
- Alerts/toasts.
- Navigation/tabs.
- Tables when data-heavy products are in scope.

## Accessibility

- Normal text contrast target: WCAG AA 4.5:1.
- Large text and meaningful non-text UI indicators target: 3:1.
- Focus indicators must be visible and not color-only.
- Error/success/warning states need text or icon support, not color alone.
- Touch targets should generally be at least 44px on mobile.

## Output Files

```text
tokens/colors.json
tokens/typography.json
tokens/spacing.json
tokens/css-variables.css
tokens/branding.css
ui/components.css
ui/button-spec.md
```

Adapt to Tailwind, React, shadcn/ui, or another stack only when requested.

## Stage Gates

1. Color alternatives: show 3 palettes with role names and key contrast pairs.
2. Typography alternatives: show 3 pairings/scales with rationale.
3. Component alternatives: show 3 button/card/input style directions.
4. Generate full token/component files only after approval.

Carry approved logo/color/type decisions into every later UI choice.

For typography choices, use `brand-typography-researcher` first when font availability, licensing, multilingual coverage, or visual identification matters.

## Leveraging Frontend-Design

Use a frontend-design skill as a downstream renderer:

1. Feed it approved brand tokens, typography, radius, elevation, and component-state rules.
2. Ask it to produce screens, component galleries, and responsive UI examples.
3. Review output against the brand guidelines and accessibility checks.

Do not use it as the source of truth for brand strategy, logo design, or corporate identity rules.
