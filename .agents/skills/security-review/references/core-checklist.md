# Core Security Checklist

Use this for every security review, regardless of libraries.

## Trust Boundaries

- Identify every boundary crossed: browser to API, API to DB, API to external service, webhook to API, background task to DB/storage/email, admin UI to admin API.
- Treat all client data, URL params, headers, cookies, uploaded files, webhook payloads before verification, and background task inputs as untrusted.
- Confirm object-level authorization/ownership checks happen server-side for every state-changing or sensitive read.

## Data Protection

- Classify data: the selected application's personal data, payment identifiers, credentials, session material, documents and logs.
- Avoid client persistence of secrets or sensitive data. If short-lived client values are required, keep them memory-only where feasible and never log them.
- Encrypt or provider-store sensitive data according to existing project patterns.
- Do not add sensitive values to URLs, analytics, monitoring context, browser storage, logs, or email templates unless explicitly required and sanitized.
- Confirm deletion/retention behavior for new PII or documents.

## Input Validation And Injection

- Validate all request bodies and query/path params with typed schemas at API boundaries.
- Use server-side allowlists for supported products, tenants, modes, statuses, document types and callback event types.
- Do not build SQL, filesystem paths, storage keys, URLs, HTML, email templates, or shell commands by concatenating untrusted input.
- For rendered HTML/PDF/email content, check contextual escaping and template boundaries.

## Authentication And Authorization

- Admin endpoints require authenticated admin identity and role/function authorization.
- Public resource endpoints need ownership or equivalent capability checks for reads and writes.
- Token/session verification must include expiry, signature, revocation/rotation behavior where applicable, and environment-specific secrets.
- CSRF protection is required for cookie-authenticated unsafe methods.

## Business Logic Abuse

- Payment amounts, currencies, product eligibility, order fulfillment, and submission state transitions must be decided server-side.
- Check idempotency for submissions, payment processing, document generation, email sending, and webhook/background task retries.
- Add rate limiting to endpoints that create resources, trigger email/documents, validate tokens, or reveal state.
- Ensure race conditions cannot issue duplicate orders, emails, documents, or payment records.

## Secrets And Configuration

- Secrets come from environment/secrets management only. Never place them in source, tests with realistic live-looking values, CLI args, URLs, or public env vars.
- Production defaults should fail closed for security-sensitive features.
- CORS must use explicit origins, not wildcards with credentials.
- Security headers/CSP should be preserved when changing frontend or proxy behavior.

## Logging, Errors, And Monitoring

- Logs should include correlation IDs and operational context without PII, health data, credentials, payment secrets, webhook signatures, or document contents.
- User-facing errors should be generic enough to avoid enumeration and implementation leakage.
- monitoring context should be scrubbed for sensitive data.
- Security-sensitive changes need observability: audit logs, structured warnings, metrics, or monitoring events as appropriate.

## Testing And Scans

Match verification to risk:

- Backend: targeted tests for auth/ownership, validation, idempotency, webhooks, PII encryption, logging sanitization, migrations.
- Frontend: unit tests for API clients, persistence boundaries, public env handling, and error handling.
- Scans: Bandit, Semgrep, pip-audit/safety, npm audit, gitleaks, Trivy, Checkov when relevant.
- Regression: run the smallest reliable test set first, then broader checks when payment/PII/admin behavior changes.
