# Branding, Human-Centered Design, Color, UX, and UI Review Guidelines

Use this file as the reviewer standard for brand identity, corporate design, UI kits, marketing assets, and frontend app designs. Judge the produced work against the user's brief, approved direction, target segment, country/region, and USP first; then apply these best-practice checks.

## Evidence Base

This rubric combines:

- Common structure found in `awesome-design/design-md/*/DESIGN.md`: overview, color roles, typography, spacing, grid, elevation, shapes, components, do/don't rules, responsive behavior, iteration guidance, and known gaps.
- WCAG AA color contrast norms: 4.5:1 for normal text, 3:1 for large text and UI graphics, stronger ratios for critical/older-audience use cases.
- Material Design color/accessibility principles: role-based color, primary/secondary variants, semantic color, state clarity, and multiple cues beyond color.
- Nielsen Norman Group UX principles: visual hierarchy, scale, balance, contrast, Gestalt grouping, consistency, system feedback, real-world language, error prevention, and minimalist focus.
- Mature public brand systems such as Webflow: logo clearspace, scalable mark variants, explicit misuse rules, typography scales, restrained color use, and component-level usage guidance.

## 1. Brand Strategy Fit

Good branding is not only attractive; it makes a specific promise memorable to a specific audience.

Review:

- The identity expresses the approved USP, not a generic category mood.
- The first remembered idea is clear: who it helps, what it protects/improves, why it is different.
- The tone fits the target buyer/user and country/region. Consider formality, trust cues, local color symbolism, language length, reading direction, cultural sensitivity, and regulatory expectations.
- Category signals are intentionally chosen: either conform enough to be trusted or contrast deliberately enough to be distinctive.
- The brand has a durable personality with 3-5 stable attributes, not a list of vague adjectives.
- Messaging hierarchy is visible in logo, colors, typography, components, and sample assets.

Flag HIGH if the output contradicts the audience, country, industry, values, or USP. Flag MEDIUM if it looks polished but interchangeable.

## 2. Logo and Mark System

A logo system must survive real usage, not only one hero mockup.

Review:

- Primary logo, secondary layout, icon/favicon, monochrome, reversed, and small-size variants share the same concept.
- The mark is recognizable at 16, 32, 64, and 128 px without tiny details becoming noise.
- Geometry is intentional: optical alignment, consistent stroke behavior, balanced whitespace, no accidental tangents, awkward intersections, clipping, or near-misses.
- Clearspace and minimum-size rules exist. Clearspace should be based on an internal unit such as cap height, x-height, or mark width.
- The logo works on light, dark, and single-color contexts.
- The logo is not dependent on gradients, shadows, fine lines, or a complex background.
- Misuse rules cover stretching, recoloring, effects, low contrast, crowding, wrong lockups, and unsafe backgrounds.

Flag HIGH for unreadable small marks, inconsistent variants, missing core variants, or accidental intersections. Flag MEDIUM for missing clearspace/min-size guidance.

## 3. Color System and Harmony

The color system must balance emotion, recognition, accessibility, and operational roles.

Review:

- Palette roles are explicit: primary, secondary/accent, neutrals, surfaces, borders/hairlines, text, overlays, semantic colors, focus, disabled, hover, active.
- Neutrals are complete enough for real UI: at least canvas, surface, surface-raised, border, text, muted text, disabled text.
- Harmony is intentional:
  - Monochromatic: calm, focused, easier to make accessible.
  - Analogous: approachable, natural continuity.
  - Complementary/split-complementary: higher energy and differentiation.
  - Triadic/tetradic: expressive but risky; use with strict role limits.
- Saturation and lightness are controlled. Avoid using multiple equally saturated colors at the same hierarchy level unless the brand intentionally needs a playful/color-blocked system.
- Primary color is not overused. It should identify the brand and guide action, not flood every surface.
- Semantic colors are not just brand accents renamed. Error, warning, success, and info must be legible and culturally reasonable.
- Color meaning is never color-only. Error also needs text/icon/border. Success needs label/icon/shape. Focus needs a visible outline.
- Critical color pairs are documented and pass contrast: text/background, button text/fill, input border/fill, focus ring/background, disabled state, charts/badges.
- Pure black and pure white are used deliberately. For many brands, near-black/off-white reduce glare and feel more owned.

Flag HIGH for WCAG AA text contrast failures, color-only meaning, or missing semantic roles in UI work. Flag MEDIUM for incomplete neutral scales or overdecorative palettes.

## 4. Typography and Readability

Type must express personality while staying readable in real content.

Review:

- Font choices support the brand personality: premium/editorial, utilitarian/technical, friendly/human, bold/disruptive, or another explicit direction.
- Licensing and availability are clear. Include web-safe/system fallbacks and open-source substitutes when proprietary fonts are referenced.
- The type scale is defined with sizes, weights, line heights, letter spacing, and usage roles.
- Hierarchy uses 2-3 dominant sizes per composition, not many competing scales.
- Body copy is readable: generally 16 px or larger for digital body text, line-height around 1.45-1.7, comfortable measure, and enough paragraph spacing.
- Display type is tested with real brand/company/product names, long German/French/English strings where relevant, and mobile widths.
- Letter spacing is conservative. Do not use negative tracking for body text. Use all caps sparingly and with positive tracking.
- Numeric, currency, and tabular data needs suitable glyph support when the brand will have dashboards or finance/insurance content.

Flag HIGH for clipped/overflowing text, unreadable body copy, or missing fallback/licensing in a deliverable. Flag MEDIUM for an incomplete scale or untested long-string behavior.

## 5. Layout, Composition, and Visual Hierarchy

Strong layouts guide attention without explanation.

Review:

- One primary focal point exists per screen/asset.
- Scale, contrast, spacing, and position create the intended hierarchy.
- Spacing follows a tokenized rhythm, typically a 4 px or 8 px base, with consistent section, card, and component padding.
- Grids and containers are defined: max widths, gutters, columns, breakpoints, and collapse behavior.
- Balance is optically correct. Heavy marks, imagery, or dark blocks are counterweighted by whitespace or supporting content.
- Related elements are visually grouped by proximity, alignment, similarity, and common region.
- The design avoids nested card-on-card structures unless there is a clear product reason.
- Dense operational tools favor scanability, predictable navigation, and restrained decoration. Marketing surfaces may be more expressive but still need clear hierarchy.

Flag HIGH for overlaps, clipped content, broken responsive layouts, or hierarchy that hides the main action/message. Flag MEDIUM for inconsistent spacing or weak grouping.

## 6. UI Components and Interaction States

A brand system is incomplete if it cannot be used in product UI.

Review:

- Core components are defined at least for buttons, links, inputs, selects/menus, checkboxes/toggles, tabs, cards, badges/status, alerts/toasts, modals, navigation, and tables if needed.
- Every interactive component has default, hover, active/pressed, focus-visible, disabled, loading, and error states where applicable.
- Focus-visible is clearly visible and not just a subtle color shift.
- Disabled state changes more than color when necessary: opacity, cursor, label, icon, or affordance.
- Touch targets are large enough: generally 44x44 px minimum, 48x48 px preferred for primary mobile actions.
- Buttons use clear roles: one primary action per region, secondary for alternatives, tertiary/text for low emphasis.
- Error states use plain language, identify the problem, and suggest recovery.
- Motion is purposeful, short, and respectful of reduced-motion preferences.

Flag HIGH for missing focus states, missing requested states, inaccessible targets, or ambiguous primary actions. Flag MEDIUM for incomplete component documentation.

## 7. Imagery, Iconography, Illustration, and Marketing Assets

Visual assets should amplify the brand promise, not add generic decoration.

Review:

- Imagery style is defined: photography vs illustration vs product screenshots vs abstract graphics.
- Subject matter reflects the target customer and country/market without stereotypes.
- Icon style is consistent: stroke width, corner radius, fill behavior, size grid, and optical alignment.
- Favicon, social avatar, app icon, email header, presentation cover, and social post templates keep the same recognition system.
- Safe areas, crop rules, backgrounds, and minimum sizes are documented.
- Generated images are checked for artifacts, brand mismatch, illegible text, distorted marks, and inappropriate cultural signals.

Flag HIGH for brand-inconsistent assets or generated artifacts in final assets. Flag MEDIUM for missing safe-area or crop rules.

## 8. Accessibility, Inclusion, and Human Psychology

Human-centered design reduces cognitive effort and emotional friction.

Review:

- The design supports recognition over recall: visible choices, clear labels, familiar patterns.
- It speaks the user's language and avoids internal jargon.
- Feedback is timely: selected, loading, success, warning, and error states are visible.
- The system prevents mistakes where possible and helps recovery when mistakes happen.
- The emotional tone fits the stakes. Finance, insurance, health, legal, and safety brands usually need calm, clarity, credibility, and restraint before novelty.
- The design does not rely on decorative complexity to feel premium. Premium often comes from spacing, typography, proportion, material quality, and restraint.
- Accessibility is built into tokens and components, not treated as a final polish step.

Flag HIGH for exclusionary assumptions, inaccessible critical flows, or misleading trust cues. Flag MEDIUM for jargon, weak feedback, or high cognitive load.

## 9. Design Guideline Completeness

A finished brand guide should let another agent or designer reproduce the system.

Minimum expected sections:

- Brand overview: purpose, audience, country/region, USP, values, personality, messaging hierarchy.
- Logo system: variants, clearspace, minimum sizes, color usage, misuse rules.
- Color tokens: brand, neutral, semantic, surface, text, border, state, contrast table.
- Typography: families, fallbacks, scale, hierarchy, usage rules, licensing.
- Layout: spacing scale, grid/container, breakpoints, responsive rules.
- Shape/elevation/motion: radius scale, shadows/surfaces, transitions.
- Components: tokens and state rules for key UI elements.
- Imagery/iconography: style, crop, safe area, examples.
- Marketing assets: favicon/app icon/social/email/presentation templates where requested.
- Do/don't rules and implementation files: CSS variables/tokens, agent-facing `DESIGN.md` or brand skill, export manifest, known gaps.

Flag HIGH if required requested deliverables are missing. Flag MEDIUM if a guide is too vague for implementation.

## 10. Reviewer Decision Rules

Use these rules to avoid subjective taste-only critique:

- Objective failures beat taste: contrast, missing states, missing formats, invalid files, overlap, clipping, inconsistent variants.
- Strategy failures beat polish: a beautiful output that misses the USP/audience is not acceptable.
- Stage discipline matters: do not approve mass asset generation before direction approval.
- Distinctiveness must be purposeful: either it improves memory/trust/usability or it is decoration.
- Every recommendation should name the affected artifact and the design principle it violates.
