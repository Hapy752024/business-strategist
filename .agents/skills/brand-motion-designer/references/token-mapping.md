# Motion Token Mapping

## Purpose
Define the exact shape of `motion-tokens.css` and `motion-tokens.ts` so that `scripts/validate-motion-tokens.py` can mechanically validate them and downstream consumers (component producer, frontend app designer) know what to import.

## Pillar Token Schema

Each pillar contributes durations, easings, and (optionally) springs. Variants are named per pillar (e.g., `fast`, `default`, `slow` for durations; `standard`, `emphasized` for easings).

### `motion-tokens.css`

```css
:root {
  /* Per pillar, per variant */
  --motion-duration-<pillar>-<variant>: <ms>ms;
  --motion-ease-<pillar>-<variant>: <cubic-bezier or named-ease>;
  --motion-spring-<pillar>-<variant>-stiffness: <number>;
  --motion-spring-<pillar>-<variant>-damping: <number>;
}
```

Example:
```css
:root {
  --motion-duration-responsive-fast: 100ms;
  --motion-duration-responsive-default: 150ms;
  --motion-ease-responsive-standard: cubic-bezier(0.25, 1, 0.5, 1);
  --motion-spring-expressive-default-stiffness: 300;
  --motion-spring-expressive-default-damping: 30;
}
```

### `motion-tokens.ts`

```typescript
export const motionPillars = {
  <pillar>: {
    durations: { <variant>: <ms> },
    easings: { <variant>: <number[]> | <string> },
    springs: { <variant>: { stiffness: <number>, damping: <number> } }
  }
} as const;
```

Example:
```typescript
export const motionPillars = {
  responsive: {
    durations: { fast: 100, default: 150 },
    easings: { standard: [0.25, 1, 0.5, 1] },
    springs: {}
  },
  expressive: {
    durations: {},
    easings: {},
    springs: { default: { stiffness: 300, damping: 30 } }
  }
} as const;
```

## Validation Rules (enforced by `scripts/validate-motion-tokens.py`)

1. `motion-tokens.css` must parse as CSS (no unbalanced braces, no missing semicolons).
2. Every `--motion-duration-*` value must end in `ms` and be a positive integer.
3. Every `--motion-ease-*` value must be either a named easing (`ease-out`, `ease-in-out`, `linear`, etc.) or a `cubic-bezier(a, b, c, d)` with four numeric values.
4. Every `--motion-spring-*` value must be a positive number.
5. For every `--motion-spring-<pillar>-<variant>-stiffness` there must be a matching `-damping` and vice versa.
6. `motion-tokens.ts` must contain a top-level `export const motionPillars` declaration.
7. Every pillar named in the CSS custom properties must also appear as a key in `motionPillars` in the TS file, and vice versa.
8. The TS file must parse as TypeScript (no unbalanced braces; regex check is acceptable, a full TS parser is not required).

## Exit Codes (from `validate-motion-tokens.py`)
- 0: both files valid.
- 1: one or more validation rules failed (message printed to stderr).
- 2: usage error (missing file, wrong arguments).
