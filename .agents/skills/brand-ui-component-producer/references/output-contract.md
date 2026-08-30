# Output Contract

## Purpose
Define the exact file shapes the component producer must produce before its Stop hook will allow the skill to declare done.

## Canonical Delivery: `brand-projects/<name>/components/`

```
components/
├── README.md
├── tokens.css                              # symlink or copy from brand-projects/<name>/tokens.css
├── motion-tokens.css                       # symlink or copy from motion/motion-tokens.css
├── motion-tokens.ts                        # symlink or copy from motion/motion-tokens.ts
├── core/
│   ├── input/{Input.tsx, Input.stories.tsx, Input.test.tsx}
│   ├── radio-group/{RadioGroup.tsx, ...}
│   └── ...
├── extended/                               # only selected Extended items
│   └── ...
└── domains/
    ├── dashboard/                          # only selected domain packs
    ├── ecommerce/
    ├── auth/
    └── content/
```

### `README.md` (required sections)
1. **Install** — how to copy `components/` into a Next.js App Router app.
2. **Token Wiring** — how `tokens.css`, `motion-tokens.css`, and `motion-tokens.ts` connect to the app's global styles.
3. **Import Convention** — how to import a component (`import { Input } from "@/components/core/input/Input"`).
4. **Customization** — how to override a component for app-specific needs without forking.
5. **Storybook** — how to run the stories locally (`npx storybook` or Ladle equivalent).

### Per-component folder shape
For each component `<PascalName>`:
- `<PascalName>.tsx` — the component implementation (Next.js client component if interactive).
- `<PascalName>.test.tsx` — Vitest + React Testing Library + jest-axe tests.
- `<PascalName>.stories.tsx` — Storybook CSF stories.

### `validate-component.py` requirements (per component)
- All three files exist.
- Test passes (`vitest run <PascalName>.test.tsx` returns 0; if vitest isn't installed, fall back to a static analysis check that the test file imports the component and has at least one `it()` or `test()` block).
- Component file references at least one `var(--color-*)` or `var(--motion-*)` token.
- Component file contains no hardcoded hex colors (regex `#[0-9a-fA-F]{3,8}`).

## Working History: `brand-projects/<name>/stages/components/`

```
stages/components/
├── scope.json                              # selected taxonomy items
├── iterations/                             # earlier drafts during review
├── iteration-state.json                    # current component, test status, pending feedback
└── iteration-manifest.json                 # append-only log of completed components
```

### `scope.json` shape
```json
{
  "core": true,
  "extended": ["date-picker", "slider"],
  "domains": ["dashboard", "auth"],
  "custom": []
}
```

### `iteration-state.json` shape
```json
{
  "current_component": "input",
  "current_tier": "core",
  "test_status": "pass",
  "pending_user_feedback": null
}
```

## Stop Hook Requirements
The Stop hook (Task B8) refuses to mark the skill done unless:
1. `components/README.md` exists and contains all 5 required sections.
2. Every component listed in `stages/components/scope.json` has a folder under `components/<tier>/<component-name>/` with all three files (`<PascalName>.tsx`, `.test.tsx`, `.stories.tsx`).
3. `scripts/validate-component.py --components-dir components/ --scope stages/components/scope.json` returns 0 (all components pass validation).
4. `stages/components/iteration-manifest.json` lists every shipped component with `test_status: "pass"`.
