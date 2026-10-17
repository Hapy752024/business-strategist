---
name: security-review
description: Review website or application code, plans and diffs for exploitable security risks. Use for auth, payments, webhooks, sensitive data, uploads and deployment security reviews.
---

# Security Review

1. Identify the target application, review mode (plan, diff or bounded baseline), assets and trust boundaries. This repository hosts multiple projects; discover the selected project's stack and rules rather than assuming a shared backend.
2. Read [core checklist](references/core-checklist.md) for every review and [project discovery](references/project-context.md) to establish context. For Stripe changes, also read [Stripe checks](references/libraries/stripe.md) and use `stripe-best-practices` for integration decisions.
3. Trace relevant attacker inputs through authorization, validation, storage, external services and side effects. Cite concrete code paths; distinguish verified findings from questions.
4. Inspect existing tests and scans. Run proportionate authorized verification; use synthetic data and avoid exposing credentials or customer information to tools.
5. Report severity, file/line or plan section, exploit path, impact, proposed fix and verification for each finding. State inspected scope, missing evidence and residual risk even when no findings are found.

Remain read-only during the review. Findings do not authorize fixes, deployments, secret rotation, migrations or external account changes. Use available independent review when requested; no specific agent host or graph service is required. This review does not certify legal or regulatory compliance.
