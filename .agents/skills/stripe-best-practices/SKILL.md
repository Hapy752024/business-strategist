---
name: stripe-best-practices
description: Design or review Stripe payments, checkout, subscriptions and marketplace integrations. Use when the selected application needs Stripe integration or changes to existing Stripe behavior.

---

Discover the target application and its pinned Stripe API/SDK versions. Verify current official Stripe documentation before implementation decisions; bundled references are starting guidance and may age. Do not silently upgrade existing integrations.

Use test mode and synthetic data. Live charges, deployment, account connections and dashboard changes require explicit authorization. Preserve applicable project gates; this skill does not authorize a Business launch.

Read only the directly linked reference relevant to the task: [payments](references/payments.md), [billing](references/billing.md), [Connect](references/connect.md), or [Treasury](references/treasury.md). For code changes, pair integration guidance with `security-review` and appropriate browser/regression checks. Report design choices, implementation or review evidence, open gaps and release state.

## Integration routing

| Building…                             | Recommended API                     | Details                  |
| ------------------------------------- | ----------------------------------- | ------------------------ |
| One-time payments                     | Checkout Sessions                   | <references/payments.md> |
| Custom payment form with embedded UI  | Checkout Sessions + Payment Element | <references/payments.md> |
| Saving a payment method for later     | Setup Intents                       | <references/payments.md> |
| Connect platform or marketplace       | Accounts v2 (`/v2/core/accounts`)   | <references/connect.md>  |
| Subscriptions or recurring billing    | Billing APIs + Checkout Sessions    | <references/billing.md>  |
| Embedded financial accounts / banking | v2 Financial Accounts               | <references/treasury.md> |

Read the relevant reference file before answering any integration question or writing code.

## Key documentation

When the user’s request does not clearly fit a single domain above, consult:

- [Integration Options](https://docs.stripe.com/payments/payment-methods/integration-options.md) — Start here when designing any integration.
- [API Tour](https://docs.stripe.com/payments-api/tour.md) — Overview of Stripe’s API surface.
- [Go Live Checklist](https://docs.stripe.com/get-started/checklist/go-live.md) — Review before launching.
