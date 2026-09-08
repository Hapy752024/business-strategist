---
name: competitive-landscape-builder
description: Build a three-lane competitive landscape of market competitors, cross-market analogs, and capability references. Use when broad competitor, pricing, social, positioning, or USP analysis is needed.
---

# Competitive Landscape Builder

Coordinate the existing `competitor-scout` and `competitor-marketing-analyzer` workers. Do not treat all similar-looking entities as competitors.

## Workflow

Read [references/workflow.md](references/workflow.md), create a compact landscape brief, then run the three lanes independently:

- `competitive_market`: same customer job, buyer/segment and market; informs threats, table stakes and positioning.
- `similar_company`: same or similar service/model with a documented segment, demographic or geography mismatch; informs inspiration only.
- `capability_reference`: narrow website, brand, offer, social, YouTube, onboarding or trust reference; informs a named learning purpose only.

Treat discovery lane observations as provenance, not classification. Verify official service evidence before invoking the canonical classifier. Preserve source dates, unknowns and exclusions. Analyze observed services, price points, proof, CTAs, website and checked public social usage. Produce competitive conclusions only from verified first-lane entities. Stop synthesis when `quality-gate.json` fails; report the missing evidence instead of filling templates. Branding and website handoffs are optional and never make research a prerequisite.

## Output

Return the route packet, lane-aware entity landscape, service/price matrix, social-presence table, positioning hypotheses, inspiration library, coverage gaps and next validation test.
