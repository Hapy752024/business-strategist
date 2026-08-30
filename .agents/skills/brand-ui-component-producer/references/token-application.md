# Token Application

## Purpose
Define how brand design tokens (from `brand-ui-kit-producer`) and motion tokens (from `brand-motion-designer`) are applied to a shadcn base component.

## Inputs Required
- `brand-projects/<name>/tokens.css` — CSS custom properties for color, typography, spacing, radii, shadows.
- `brand-projects/<name>/motion/motion-tokens.css` — CSS custom properties for durations and easings.
- `brand-projects/<name>/motion/motion-tokens.ts` — TS exports for Framer Motion configs.
- The shadcn base component file (e.g., `input.tsx` from the shadcn registry).

## Application Procedure
1. **Read the shadcn base file** and identify every hardcoded color, radius, shadow, duration, and easing.
2. **Map each hardcoded value to a brand token**:
   - `bg-primary`, `text-primary`, `border-input`, `ring-ring` etc. → already reference shadcn's semantic CSS variables; remap those variables in `tokens.css` to the brand's tokens (`--color-primary`, `--color-primary-foreground`, `--color-ring`, etc.).
   - `rounded-md`, `rounded-lg` → swap for `var(--radius-*)` tokens from `tokens.css`.
   - `transition-colors`, `transition-all` with default duration → swap for `transition: var(--motion-duration-<pillar>-<variant>) var(--motion-ease-<pillar>-<variant>)`.
3. **For Framer Motion usage** (in components with significant motion like drawer, modal, accordion): import `motionPillars` from `motion-tokens.ts` and use `motionPillars.<pillar>.durations.<variant>` and `motionPillars.<pillar>.springs.<variant>` in `transition={{ duration: ..., ease: ... }}` or `transition={{ type: 'spring', stiffness: ..., damping: ... }}`.
4. **Preserve accessibility**: do not remove `aria-*`, `role`, `tabIndex`, focus handlers, or keyboard event handlers from the shadcn base.
5. **Write the customized component** to `components/<tier>/<component-name>/<ComponentName>.tsx`.

## Token Reference Convention
Components must import tokens at the top of the file:
```typescript
import "@/styles/tokens.css";        // brand design tokens (color, type, spacing)
import "@/styles/motion-tokens.css"; // motion tokens (durations, easings)
import { motionPillars } from "@/styles/motion-tokens";  // Framer Motion configs
```

(Exact import paths depend on the consuming app's structure; the `components/README.md` documents how to wire these.)

## Validation
After application, `scripts/validate-component.py` checks:
- The component file does not contain hardcoded hex colors (regex: `#[0-9a-fA-F]{3,8}`).
- The component file references at least one `var(--color-*)` or `var(--motion-*)` token.
- The component file's `.test.tsx` exists and passes.

## Example: Branded `input`
Given shadcn's `input.tsx`:
```typescript
className = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
```

After token application:
```typescript
className = "flex h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-base text-[var(--color-foreground)] ring-offset-[var(--color-background)] transition-[border-color, box-shadow] duration-[var(--motion-duration-responsive-default)] ease-[var(--motion-ease-responsive-standard)] placeholder:text-[var(--color-muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
```
