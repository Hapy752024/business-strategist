# Export Format

## CSS Branding

Create `tokens/branding.css` with CSS custom properties:

```css
:root {
  --brand-color-primary: #233233;
  --brand-color-primary-hover: #1c2929;
  --brand-color-secondary: #7a8c8d;
  --brand-color-accent: #d97757;
  --brand-color-success: #16803c;
  --brand-color-warning: #b7791f;
  --brand-color-error: #c53030;
  --brand-color-info: #2563eb;
  --brand-color-background: #ffffff;
  --brand-color-surface: #f7f7f4;
  --brand-color-text: #141413;
  --brand-color-text-muted: #64645f;
  --brand-color-border: #deded8;
  --brand-color-focus: #2563eb;
  --brand-font-heading: "Inter", system-ui, sans-serif;
  --brand-font-body: "Inter", system-ui, sans-serif;
  --brand-radius-sm: 4px;
  --brand-radius-md: 8px;
  --brand-radius-lg: 12px;
  --brand-spacing-unit: 8px;
}
```

Also provide common aliases when useful:

```css
:root {
  --color-primary: var(--brand-color-primary);
  --color-background: var(--brand-color-background);
  --font-heading: var(--brand-font-heading);
}
```

## Agent Brand Skill

The generated agent skill should be installable/copyable as a normal skill folder:

```text
agent-skill/<brand-slug>/
  SKILL.md
  references/
    DESIGN.md
    branding.css
    brand-tokens.json
```

`SKILL.md` should be compact, similar in spirit to Anthropic's brand-guidelines skill, but brand-specific:

- Frontmatter name and description.
- Overview.
- When to use.
- Required behavior.
- Link to `references/DESIGN.md`.
- Link to CSS/tokens.

`DESIGN.md` should follow the richer local `awesome-design` style:

- Visual theme and atmosphere.
- Color palette and roles.
- Typography rules.
- Layout principles.
- Elevation and depth.
- Shapes and image geometry.
- Components and states.
- Do's and don'ts.
- Responsive behavior.
- Agent prompt guide.

## Naming

Use stable, lowercase kebab-case names:

- CSS variables: `--brand-color-primary`.
- JSON tokens: `color.primary`.
- Component tokens: `component.button.primary`.

Avoid ambiguous names like `--blue` or `--nice-gray`.
