

# Validation page mode

A single-purpose page for a smoke test designed under `references/smoke-test.md`. Inputs: `smoke-test-plan.md`, `message-variants.json`, approved brand tokens if any, the conversion action, disclosure text and the analytics decision.

Requirements:
- One page per variant or one page with a server-selected variant; no navigation, one CTA, message match to the ad or post that sends traffic.
- Static export or a single static HTML file when no product site exists yet; no server code, auth or CMS.
- Disclosure block after the CTA in the exact plan wording; thank-you route `noindex`; no fabricated testimonials, ratings or scarcity.
- Events: `page_view`, `cta_click`, `lead_submit`, `call_booked` with `variant` and `utm_*`; consent handling per `consent-eu.md` before non-essential scripts. Analytics remains opt-in and owner-activated.
- Performance: mobile LCP under 2.5 s in the lab run; images sized; system or subset fonts.
- Limit form fields to screening needs and include the screener question when responders will be interviewed.
- Hand back preview URL or local build, variant mapping, event names, and plan path. Publishing and traffic buying keep their existing authorization.
