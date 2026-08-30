# Component Taxonomy

## Purpose
Define the tiered menu of components the skill can produce. The user picks Core (always shipped) + Extended items on demand + Domain packs on demand + custom components.

## Core (always shipped)

### Form inputs
- `input` — text input
- `textarea` — multiline text input
- `radio-group` — radio button group
- `checkbox` — checkbox
- `toggle` — toggle switch
- `select` — native-style select
- `combobox` — autocomplete combobox

### Display
- `card` — content card
- `badge` — small status badge
- `avatar` — user avatar
- `alert` — inline alert
- `tooltip` — hover tooltip
- `progress` — determinate progress bar
- `spinner` — indeterminate spinner
- `skeleton` — loading skeleton
- `empty-state` — empty state placeholder

### Navigation
- `tabs` — tab navigation
- `breadcrumb` — breadcrumb trail
- `pagination` — page navigation
- `menu` — dropdown menu
- `sidebar` — sidebar navigation
- `navbar` — top navigation bar

### Overlays
- `modal` — modal dialog
- `drawer` — side drawer / sheet
- `popover` — popover
- `accordion` — collapsible accordion

## Extended (shipped on demand)

- `date-picker`, `time-picker` — date and time inputs
- `slider` — range slider
- `file-upload`, `dropzone` — file upload with drag-drop
- `toast`, `snackbar` — ephemeral notifications
- `command-palette` — Cmd+K palette
- `context-menu` — right-click menu
- `hover-card` — hover-revealed card
- `data-table` — sortable/filterable table
- `tree` — tree view
- `virtualized-list` — virtualized list
- `scroll-area` — custom scroll area
- `divider` — visual separator

## Domain Packs (on demand)

### Dashboard pack
- `kpi-card` — KPI metric card
- `chart-line`, `chart-bar`, `chart-pie`, `chart-area` — chart wrappers (via Recharts)
- `stat-grid` — responsive stat grid
- `activity-feed` — activity stream
- `progress-gauge` — radial progress gauge

### E-commerce pack
- `product-card` — product listing card
- `price-tag` — price display
- `cart-item` — cart line item
- `checkout-stepper` — multi-step checkout

### Auth pack
- `signin-form`, `signup-form` — auth forms
- `mfa-input` — MFA code input
- `password-strength` — password strength meter

### Content pack
- `article` — article layout
- `media-gallery` — image/media gallery
- `comment-thread` — comment list

## Custom Components
- The user may name a custom component. The skill captures: name, parent tier (Core/Extended/Domain/<domain>), shadcn base if any, required props, behavior tests needed, then iterates via the same TDD loop.

## Scope Selection Procedure
1. Present the taxonomy above as a numbered list.
2. Ask the user: "Which Extended items do you need? Which Domain packs? Any custom components?"
3. Record the in-scope set to `stages/components/scope.json`:
   ```json
   {
     "core": true,
     "extended": ["date-picker", "slider", "toast"],
     "domains": ["dashboard"],
     "custom": []
   }
   ```
4. Ask the user for priority order (or accept default: Core first, then Extended in listed order, then Domains).
5. Proceed to per-component TDD loop (see `references/tdd-workflow.md`).
