# Stripe Security Checks

Use only when the selected project uses Stripe. Discover its payment routes, order/pricing model, client integration and fulfillment workers.

- Resolve payable amounts and currency from authoritative server-side records; validate ownership and product eligibility.
- Keep secret keys server-side. Limit client-secret exposure to the intended checkout; exclude secrets and sensitive payloads from URLs, storage, logs and analytics.
- Verify webhook signatures using the unmodified raw request body before trusting events. Use the SDK's documented verification method.
- Deduplicate events durably and make fulfillment safe under retries, concurrent delivery and out-of-order events. Acknowledge only after required work or durable queueing succeeds; match the current provider retry contract.
- Verify payment status server-side before delivering an order or entitlement. A redirect or browser success flag is insufficient.
- Review wrong-owner access, amount tampering, invalid signatures, replay, declines, cancellation and delayed fulfillment. Discover applicable tests rather than assuming filenames or tables.
- Use test mode and synthetic data for payment exercises. Live charges and external account changes require explicit authorization.
