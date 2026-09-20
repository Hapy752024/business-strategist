# Decision-engine (agent) readiness — conditional

Apply only for businesses with commerce or comparable offers, after the marketing bottleneck diagnosis justifies it. DEO is an emergent label (coined 2026-09); the mechanics (product feeds, agentic commerce protocols) are real but recommendation→transaction conversion has almost no public data. Present as conditional infrastructure, never a promised channel.

Machine-comparable attributes: pricing in crawlable plain HTML (never JS-only or "contact sales" for eligible tiers), Product/Offer markup with identifiers (GTIN/MPN/SKU/brand), price, availability and aggregateRating encoded only from owner-confirmed facts. Policy markup must match the visible policy text exactly and sit at the correct scope: organization-level return policy is `Organization.hasMerchantReturnPolicy` → `MerchantReturnPolicy`, and organization-level shipping is `Organization.hasShippingService` → `ShippingService` ([return policy](https://developers.google.com/search/docs/appearance/structured-data/return-policy), [shipping policy](https://developers.google.com/search/docs/appearance/structured-data/shipping-policy)); the offer-level overrides are `Offer.hasMerchantReturnPolicy` → `MerchantReturnPolicy` and `Offer.shippingDetails` → `OfferShippingDetails` — `OfferShippingDetails` is an offer-level type, never organization-level. Offer-level markup outranks organization-level markup and supports a narrower property set. Inaccurate markup is penalized harder than absent markup; the agent encodes, the owner supplies truth.

Owner-gated approvals (identity-bound, cannot be delegated): OpenAI merchant application, Google Merchant Center/UCP onboarding, Google Business Profile verification, review-platform profiles. Record these as owner actions (references/owner-actions.md at repo root).

Feed publication requires the feed contract before any scheduled push: named authoritative inventory/price source with a freshness limit (stale input fails closed); replacement/deletion semantics so removed products are withdrawn, not merely not-updated; delivery reconciliation (acknowledgements, rejections, retries) with operator alerts; acceptance tests covering stale input, removed products, rejected updates and delayed retries.

Reputation: reviews come from real customers on independent platforms (G2, Capterra, Trustpilot, Google). The agent audits presence and drafts owner-approved review requests; fake reviews are fraud and never an option.

Measurement: track decision-stage prompts ("which X with A and B under price P") separately from educational prompts using the `prompt_type` label under the ai_answer_probe measurement contract.

Deferred until a selected integration needs them: MCP commerce servers, `/.well-known` discovery files, llms.txt.

Sources: living documents checked in-session 2026-09-19 — the OpenAI product-feed specification, Google Merchant Center/UCP onboarding guides and OpenAI shopping help. Re-fetch them before implementation; do not quote their details from memory, and add them to the spec §7 register when they inform a binding claim.
