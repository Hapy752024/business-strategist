# Strategy mode (route `brand-strategy-director`)

Create brand strategy and visual territories from a confirmed brief and research. No final assets until a territory is approved.

## Business-linked input

Use the selected snapshot and repo-root `references/strategic-positioning.md` to check alignment. Run `python3 scripts/brand/validate_business_to_brand_handoff.py <snapshot.json> --check-sources` before generation. A changed or unavailable source needs a fresh handoff or explicitly provisional work; preserve archived snapshots and uncertainty. Territories express one business position; a different buyer, promise or relative price is an explicit business-strategy revision. Standalone brand discovery stays independent.

## Territories

Create exactly 3 distinct territories unless the user asks for a different count, as numbered options. Template per territory:

- Name and core idea.
- Business-linked work: source snapshot/revision and how it expresses the selected position, plus any material conflict (standalone: a provisional brand-positioning idea).
- USP/differentiation expressed; best for; audience signal; values and personality keywords.
- Logo concept; colour logic; typography logic; imagery/iconography.
- UI and marketing-asset implications; messaging hierarchy.
- Accessibility watch-outs; what it avoids.

Recommend the strongest territory in one sentence, then ask: which numbered territory becomes the source of truth: 1, 2, 3, a combination, or reject all 3?

## After approval

- Voice stage: [verbal identity](verbal-identity.md), after strategy and before logo production.
- Naming and preliminary legal checks: [naming and checks](naming-and-checks.md), when a name is needed or before logo/tagline approval.
