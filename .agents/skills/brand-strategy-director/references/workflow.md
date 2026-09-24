# Brand Strategy Director Workflow


Do not create final assets until a territory is approved.

For business-linked branding, use the selected snapshot and repo-root `references/strategic-positioning.md` to check alignment. Run `python3 scripts/brand/validate_business_to_brand_handoff.py <snapshot.json> --check-sources` before generation. A changed/unavailable source requires a fresh handoff or explicitly provisional work; preserve archived snapshots and uncertainty. Territories express one business position; a different buyer, promise, or relative price is an explicit business-strategy revision. Standalone brand discovery remains independent.

Create exactly 3 distinct territories unless the user requests a different count:
- Expression of the selected business position (or a provisional brand-positioning idea for standalone discovery).
- USP/differentiation expression.
- Personality keywords.
- Logo direction.
- Color direction.
- Typography direction.
- UI and marketing implications.
- Accessibility risks.
- What it avoids.

Ask the user to choose, reject, or combine one direction.
Present territories as numbered options so the user can reply with the number.
Recommend the strongest territory and explain the reason in one sentence.
End by instructing the user to choose a number, combine options, or reject all 3.

Use `references/territory-template.md` when writing the options.


## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
