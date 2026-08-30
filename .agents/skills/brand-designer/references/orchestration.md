# Orchestration

## Sequence

1. Run discovery until the brief is clear enough to summarize.
2. Confirm the brief with the user.
3. Create the project workspace folder.
4. Research the industry, competitors, user-provided examples, and relevant design systems.
5. Research candidate fonts and licensing when typography is in scope.
6. Present 2-3 design territories.
7. Ask the user to choose, reject, or combine a territory.
8. Produce deliverables stage-by-stage with user approval after each stage.
9. Run `brand-quality-reviewer`; fix HIGH issues and rerun review.
10. Export CSS branding and agent-readable brand skill/guidelines.
11. Validate consistency, accessibility, file existence, and manifest completeness.

## Required Brief Fields

- Goal.
- Requested deliverables.
- Company/organization name or naming need.
- Industry and offer.
- Target customer segment.
- Primary country/region or market.
- Primary decision-maker, buyer, user, or stakeholder.
- Unique selling proposition or differentiation.
- Values/principles.
- Desired personality.
- Design preferences and constraints.
- Good examples and why they work.
- Required formats/tools/environments.

## Default Output Structure

```text
brand/
  brief.md
  research.md
  strategy.md
  guidelines.md
  tokens/
  logos/source/
  logos/export/
  icons/
  ui/
  marketing/
  manifest.json
```

## Quality Gate

- Each stage starts with exactly 3 visible alternatives unless the user requests otherwise.
- Do not proceed to the next stage until the user approves the current one.
- Every visual decision maps to the brief, research, or approved territory.
- Logo, color, typography, and messaging decisions reinforce the USP/differentiation.
- Every color token has a role.
- Every logo variant has a usage rule.
- UI components include default, hover, active, focus-visible, disabled, and loading/error states when relevant.
- Normal text contrast targets WCAG AA 4.5:1; large text and meaningful UI graphics target 3:1.
- Generated assets are listed in a manifest.
- HIGH review issues are fixed or explicitly accepted by the user.

## Stage Gates

Default order:

1. Logo direction.
2. Logo refinements and variants.
3. Color system.
4. Typography.
5. Imagery/iconography style.
6. UI tokens and components.
7. Frontend app screens, dashboards, and workflows when requested.
8. Marketing assets.
9. Final guidelines, CSS branding, agent skill, and manifest.

For each stage:

1. Generate exactly 3 alternatives the user can visually compare.
2. Ask which numbered option to pursue.
3. Iterate only on the selected option.
4. Before regenerating, move prior iteration files into `old/`.
5. Ask for explicit approval before moving on.
6. Carry approved decisions forward as constraints.
