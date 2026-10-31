# Kit mode (route `brand-ui-kit-producer`)

Produce brand-aligned UI tokens and component templates from an approved brand direction. Tokens come before components.

## Stage gates

1. Colour alternatives: 3 palettes with role names and key contrast pairs.
2. Typography alternatives: 3 pairings/scales with rationale; use `brand-identity` typography mode first when availability, licensing, multilingual coverage or visual identification matters.
3. Component alternatives: 3 button/card/input style directions.
4. Generate the full token and component files only after approval.

For each stage explain the trade-off, recommend one option and ask the user to choose a number or approve. Carry approved logo, colour and type decisions into every later UI choice.

## Required content

- Token groups: colour primitives and semantic roles, typography, spacing, radius, elevation, motion/focus.
- Core components: buttons (primary, secondary, tertiary/ghost, destructive, icon), links, inputs/textareas/selects, checkbox/radio/toggle, cards and containers, badges/tags/chips, alerts/toasts, navigation/tabs, tables when the product is data-heavy.
- States: default, hover, active, focus-visible, disabled; loading, selected, invalid/error where relevant.
- Accessibility: normal text WCAG AA 4.5:1; large text and meaningful non-text indicators 3:1; visible, not colour-only focus; error/success/warning carry text or icon; touch targets at least 44px on mobile.

## Output files

```text
tokens/colors.json  tokens/typography.json  tokens/spacing.json
tokens/css-variables.css  tokens/branding.css
ui/components.css  ui/button-spec.md
```

Adapt to Tailwind, React, shadcn/ui or another stack only when requested. When `frontend-design` is available, use it after tokens exist as a downstream renderer: feed it approved tokens, typography, radius, elevation and state rules; review its screens and galleries against the guidelines and accessibility checks. It is never the source of truth for strategy, logo or identity rules.
