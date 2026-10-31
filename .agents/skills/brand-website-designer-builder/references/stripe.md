# Stripe mode (route `stripe-best-practices`)

Reference for designing or reviewing Stripe payments, checkout, subscriptions and marketplace integrations in the
selected application. Website builds that add payments read it too.

## Stage checklist

1. Discover the target application and its pinned Stripe API/SDK versions. Do not silently upgrade existing integrations.
2. Verify current official Stripe documentation before implementation decisions; these references are starting guidance and may age.
3. Read only the reference for the task (table below) before answering an integration question or writing code.
4. Use test mode and synthetic data. Live charges, deployment, account connections and dashboard changes need explicit authorization; this mode does not authorize a Business launch or bypass project gates.
5. For code changes, pair with `security-review` (its Stripe checks) and `site-testing` browser or regression checks (routes `webapp-testing`, `pre-release-regression`).
6. Report design choices, implementation or review evidence, open gaps and release state.

## Integration routing

| Building | Recommended API | Details |
| --- | --- | --- |
| One-time payments | Checkout Sessions | references/stripe-payments.md |
| Custom payment form with embedded UI | Checkout Sessions + Payment Element | references/stripe-payments.md |
| Saving a payment method for later | Setup Intents | references/stripe-payments.md |
| Connect platform or marketplace | Accounts v2 (`/v2/core/accounts`) | references/stripe-connect.md |
| Subscriptions or recurring billing | Billing APIs + Checkout Sessions | references/stripe-billing.md |
| Embedded financial accounts / banking | v2 Financial Accounts | references/stripe-treasury.md |

When the request fits none of these, start from [Integration Options](https://docs.stripe.com/payments/payment-methods/integration-options.md),
the [API Tour](https://docs.stripe.com/payments-api/tour.md) and, before launch, the
[Go Live Checklist](https://docs.stripe.com/get-started/checklist/go-live.md).
