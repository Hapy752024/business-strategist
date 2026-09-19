# EU consent implementation and tests

Engineering baseline for GDPR consent and national ePrivacy rules, not certification. Establish controller/target jurisdictions, vendors and current applicable regulator guidance before production. Europe is not one cookie jurisdiction. Record owner/legal review and actual processing inventory.

First layer: equally accessible Accept all, Reject non-essential and Customize. Optional purposes off by default; no preselected boxes, implied/scroll consent, coercive wall or deceptive styling. Explain purposes, link policy/vendor information, provide granular category choices. Document essential storage necessity; analytics is not essential merely by label. No bundled marketing consent for contact forms.

Before consent and after refusal, block nonessential scripts, requests, pixels, embeds, storage, identifiers and server-side event forwarding. Denied consent-mode pings remain processing; cookieless does not mean exempt. Default to no optional requests; any exemption requires site-specific legal assessment and explicit owner change to that default. Geolocation/CMP/vendor failure must never default to consent.

Persist both acceptance and rejection using a reviewed expiry and policy/vendor version. Minimize consent records; re-request on material purpose changes. Permanent Cookie settings access enables withdrawal as easily as grant. Stop future events immediately and remove accessible nonessential cookies/storage with reviewed vendor cleanup; do not claim deletion of data already transmitted. Missing/expired/corrupt/unavailable storage defaults to denial. Core content must work without optional processing.

Maintain a dated purpose/vendor/storage/retention/recipient/transfer inventory and proportionate consent evidence. Policy, CMP config and actual behavior must agree. Configure analytics locally until activation is authorized; production acceptance needs observed post-consent delivery. No form contents, personal query strings or contact details in analytics payloads.

## Project-specific Playwright tests

Capture requests/cookies/storage before scripts execute; include same-origin proxy endpoints. Define essential allowlist and optional processing from actual inventory. Isolated contexts must test:

1. No action: only essential behavior; accessible keyboard/screen-reader controls.
2. Reject: no optional traffic/storage during navigation/reload; refusal persists.
3. Analytics-only: analytics works, marketing/embeds remain blocked.
4. Accept all: only disclosed purposes start, views and confirmed-success conversions fire once.
5. Withdraw: future events stop, accessible storage removed, reload stays denied.
6. Expiry/version change, corrupt/unavailable storage and CMP failure: denied fallback and appropriate renewed choice.
7. Mobile CTA, banner/settings, keyboard/zoom and slow networks coexist without obstruction.

Use sandbox forms/analytics when possible; production test traffic requires applicable authorization. Archive redacted network evidence, not just banner screenshots.

Sources checked 2026-09-14: [EDPB report adopted 2023-01-17](https://www.edpb.europa.eu/system/files/2023-01/edpb_20230118_report_cookie_banner_taskforce_en.pdf), [CNIL dark patterns](https://cnil.fr/en/dark-patterns-cookie-banners-cnil-issues-formal-notice-website-publishers). Refresh before legal decisions.
