# Website launch contract

Apply to every new site. Maintenance audits affected routes; every production recording requires the full contract. Legacy manifests remain readable but need `launch` initialized using repository `scripts.brand.website_launch.pending()` before a new production success can be recorded. Manifests initialized before the `https_enforcement`/`spam_protection`/`broken_links` revision must add these checks as `pending` first. Preserve historical releases.

Inventory every public route, locale and dynamic/CMS URL in `qa/routes.json` and manifest `pages`; include redirects, noindex routes and conversion roles. Compare source-generated inventory with build output and sitemap. Sampling cannot prove every-page coverage. Inspect rendered output and HTTP, not filenames. Protect private routes; robots is not access control.

## Mandatory checks

Canonical IDs: repository `scripts/brand/website_launch.py`. No silent N/A. Analytics alone may use `not_requested` with evidence of the user decision and verification that no analytics is active. Unresolved analytics preference stays pending. Missing inputs stay pending; an explicit owner scope change requires an explicit contract revision, never a fabricated pass.

| ID | Required acceptance evidence |
| --- | --- |
| custom_404 | Branded recovery/navigation, actual unknown-URL HTTP 404; inspect Next.js streaming behavior and prevent soft-404 indexing. |
| meta_title | Meaningful nonempty title on every route/locale including utility pages; distinct indexable-page titles. |
| meta_description | Nonempty route-specific description on every page; check inherited/dynamic metadata and accidental duplicates. |
| above_fold_cta | Primary action usable before scrolling on conversion pages at mobile/desktop sizes; legal pages need no sales CTA. |
| favicon_integration | Branding-approved set with source/digests; verify served URLs, MIME and browser rendering. Website never designs/exports the set. |
| robots | Working /robots.txt, reviewed search/training bot policy, correct environment and sitemap URL; no accidental production block-all. |
| https_enforcement | Production serves HTTPS with valid TLS; HTTP permanently redirects to HTTPS without chains, HSTS enabled, no mixed content on any route. Verify with production HTTP requests and rendered pages, not platform defaults. |
| sitemap | Valid /sitemap.xml with canonical production URLs/locales and genuine modified dates; exclude redirects, errors, noindex, private and thank-you routes; compare full inventory. |
| open_graph | Resolved title/description/url and reachable correctly sized OG image, absolute production URLs and social-preview review. |
| image_alt | Every img has alt; meaningful for informative images, empty for decorative ones; image links have accessible action names. Review meaning manually. |
| mobile_breakpoints | 320/375/390/768/1440 widths, no overflow, usable navigation/focus; zoom/reflow and landscape review. |
| sticky_mobile_cta | Conversion CTA remains usable on scroll; safe-area padding, no obstruction of content, cookie controls, footer, focused fields or virtual keyboard. |
| loading_states | Slow navigation/data/submission has stable meaningful accessible status, prevents duplicate submission; static pages can prove immediate usable content without fake spinners. |
| form_errors | Client/server validation, network/server errors, field associations, safe input preservation and retry; no false success. Test sandbox endpoints, not unsolicited real submissions. |
| spam_protection | Every public form has abuse protection (honeypot, rate limiting or challenge) proven by test submission; protection must not block legitimate users, break validation states or leak data. A site with no public forms passes only with a route-inventory evidence statement. |
| thank_you | Dedicated route only counts conversion after confirmed success; useful next step, no PII in URL, noindex and absent from sitemap. Direct visits never count as conversions. |
| privacy_policy | Actual controller, purposes/bases, recipients, retention, rights/contact and transfers match processing; owner/legal review, no invented facts. |
| terms | Accessible site-specific owner-reviewed terms and actual service/governing details; placeholders block launch. |
| cookie_consent | consent-eu.md behavior, network/storage evidence for all states, reviewed vendor inventory/jurisdiction. Banner visibility alone cannot pass. |
| analytics | Optional by user choice. If declined, record not_requested with user decision and absence of tracking evidence. If selected: provider installed, owner-authorized activation, minimal event plan, deduplicated SPA views and confirmed-success events; observed delivery after consent and absence after refusal. Stub is not production analytics. |
| contact_address | Owner confirms real publishable business/postal address and contact channel; consistent footer/contact/legal details. Never fabricate or publish an inferred private address. |
| compressed_images | Optimized served variants, dimensions/sizes/srcset and byte budgets; preserve quality, avoid lazy LCP images and layout shifts. next/image presence is insufficient. |
| seo_geo | seo-performance.md: canonical/indexability, crawlable useful content/links, accurate structured data; no invented claims or AI citation guarantees. |
| broken_links | Crawl the full route inventory on the production build: no internal link, asset or outbound link returns 4xx/5xx; redirect chains resolved at the source. Evidence is a crawl report covering every route in `qa/routes.json`; sampling is insufficient. |
| performance | Production-build mobile lab measurements, artifacts/tool/device/version and budgets; field CWV separately reported as unknown until available. |
| browser_tests | Runnable route auditor plus project consent/state tests, screenshots, axe and keyboard review; full inventory coverage and manual results. |

## Evidence and production recording

`website-manifest.json.launch`: version 1, full 40-character `commit`, exact tested production `url`, `deployment_id` (immutable deployment plus configuration revision), and `checks` keyed above. Each has `status: pending|pass|fail (analytics also permits not_requested)` and `evidence`: artifact locator, observed result, scope, reviewer and date. Keep redacted reports under `qa/`. The gate checks completeness and release binding, not artifact truth; the reviewer must inspect evidence. A string/schema pass cannot prove site quality.

Preview supports preparation. After authorized deployment, repeat production HTTP/robots/canonical/consent/analytics checks before recording success. Code/content/vendor/config changes invalidate evidence even if commit stays unchanged. Do not mutate deployments during inspection.

From repository root:

```bash
python3 scripts/brand/website_launch.py <website-manifest> --commit <full-sha> --url <production-url> --deployment-id <deployment-and-config-id>
python3 scripts/brand/release_manifest.py <website-manifest> --status production --commit <full-sha> --url <production-url> --deployment-id <deployment-and-config-id> --github-repo <owner/repo> --github-branch <branch> --vercel-project <project> --confirm-production
```

Commands record state only; deployment and analytics activation retain owner authorization. Missing legal/content/vendor inputs block launch, not local development. Preserve managed-subproject publication through existing helpers.
