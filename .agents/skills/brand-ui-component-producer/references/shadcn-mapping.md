# shadcn/ui Mapping

## Purpose
Map each component in the taxonomy to its shadcn/ui base primitive. The skill uses this mapping to scaffold from shadcn rather than hand-rolling, then applies brand tokens and motion tokens per `references/token-application.md`.

## Mapping Table

| Component | shadcn primitive | Notes |
|---|---|---|
| input | `input` | apply brand border-radius, focus ring from tokens |
| textarea | `textarea` | same as input |
| radio-group | `radio-group` | apply brand color to checked state |
| checkbox | `checkbox` | apply brand color to checked state |
| toggle | `switch` | apply brand color to on state |
| select | `select` | apply brand colors to trigger and content |
| combobox | `combobox` (popover + command) | apply brand colors |
| card | `card` | apply brand radius, shadow, padding tokens |
| badge | `badge` | map brand semantic variants (default/secondary/destructive/outline) |
| avatar | `avatar` | apply brand radius and fallback styling |
| alert | `alert` | map brand semantic variants |
| tooltip | `tooltip` | apply brand background and text colors |
| progress | `progress` | apply brand color to indicator |
| spinner | custom (SVG + Tailwind animate-spin) | apply brand color |
| skeleton | `skeleton` | apply brand muted color |
| empty-state | custom (composition) | use brand typography and color |
| tabs | `tabs` | apply brand active underline/background |
| breadcrumb | `breadcrumb` | apply brand separator and text colors |
| pagination | `pagination` | apply brand active state |
| menu | `dropdown-menu` | apply brand colors |
| sidebar | `sidebar` | apply brand colors; consume `sidebar` shadcn primitive |
| navbar | custom (flex + container) | use brand spacing, logo slot |
| modal | `dialog` | apply brand radius and shadow |
| drawer | `sheet` | apply brand radius and shadow |
| popover | `popover` | apply brand colors |
| accordion | `accordion` | apply brand colors and motion tokens |
| date-picker | `calendar` + `popover` | apply brand colors |
| time-picker | custom (select + popover) | apply brand colors |
| slider | `slider` | apply brand color to track and thumb |
| file-upload | `dropzone` (custom; shadcn doesn't ship) | use brand colors and motion tokens |
| toast | `sonner` (shadcn recommends Sonner) | apply brand colors |
| snackbar | `sonner` | same as toast with different positioning |
| command-palette | `command` (in dialog) | apply brand colors |
| context-menu | `context-menu` | apply brand colors |
| hover-card | `hover-card` | apply brand colors |
| data-table | `table` + `tanstack/react-table` | apply brand colors; use motion tokens on row hover |
| tree | custom (radix-like) | use brand colors |
| virtualized-list | `list` (virtualized via `tanstack/react-virtual`) | apply brand colors |
| scroll-area | `scroll-area` | apply brand scrollbar colors |
| divider | `separator` | apply brand color |

### Dashboard pack
| Component | shadcn base | Notes |
|---|---|---|
| kpi-card | `card` (composition) | apply brand typography |
| chart-line/bar/pie/area | `recharts` wrapped in `card` | apply brand colors to series; use motion tokens on chart reveal |
| stat-grid | `grid` (composition) | use brand spacing |
| activity-feed | `list` (composition) | use brand colors; motion tokens on new items |
| progress-gauge | custom (SVG + recharts) | apply brand color |

### E-commerce, Auth, Content packs
- Each component in these packs is a composition of Core/Extended primitives. The mapping records the primitive stack used; the skill applies brand tokens at the composition boundary.

## Customization Rules
1. **Never hand-roll a component that shadcn provides.** Always start from the shadcn primitive.
2. **Apply brand tokens via CSS custom properties**, not hardcoded values. Components import `tokens.css` and `motion-tokens.ts` and reference `var(--color-primary)`, `var(--motion-duration-<pillar>-<variant>)`, etc.
3. **Custom variants**: if the brand needs a semantic variant shadcn doesn't ship (e.g., "success" badge), add it as an extension in the component file; do not fork the shadcn primitive.
4. **Accessibility stays intact**: do not remove ARIA roles, keyboard handlers, or focus management from shadcn primitives.
5. **Motion tokens replace shadcn's default transitions**: shadcn uses Tailwind's default transition classes; the skill swaps these for `var(--motion-duration-<pillar>-<variant>)` and `var(--motion-ease-<pillar>-<variant>)` from the motion skill's outputs.

## Adding New Mappings
- When a custom component is named (see `references/component-taxonomy.md`), record its mapping here under a new "Custom" section before implementation. Format: `custom-<name>` → base primitive(s) → notes.
