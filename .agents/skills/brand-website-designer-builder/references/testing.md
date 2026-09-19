# Executable website testing

Run on a locally served production build or authorized test deployment. Scripts resolve from this agent repository root; pass the actual Next.js directory (the workspace's source/) and explicit base origin. They do not install dependencies or start services. Install/pin Playwright and Lighthouse as project dev dependencies and a Chromium browser through the project's normal authorized setup. Review target route semantics: even GET navigation must not invoke destructive actions.

## Route audit

Create qa/routes.json from the complete route/CMS/locale inventory. Example shape (replace with real selectors):

```json
[
  {"path":"/", "conversion":true, "cta":"[data-primary-cta]", "stickyCta":"[data-mobile-cta]", "consentReject":"[data-consent-reject]"},
  {"path":"/privacy", "conversion":false, "indexable":false},
  {"path":"/old", "conversion":false, "redirect":{"status":301,"to":"/"}}
]
```

Set `consentReject` on at most one route when the first-visit consent panel
deliberately hides conversion controls. The audit clicks that explicit
reject-optional control in its ephemeral browser context before measuring
routes; consent behavior still requires the separate network/storage matrix.

```bash
node scripts/brand/audit_web_pages.mjs <next-project> <base-origin> <routes.json> > <website>/qa/browser-audit.json
```

Nonzero exit means observed defects or unavailable tooling. Inspect JSON even on failure. The tool checks rendered metadata/duplicates, basic canonical/OG presence, image alt/breakage, overflow at five widths, explicit CTA placement, inventoried same-origin links, OG MIME, robots/sitemap basic structure and unknown URL status. It follows only query-free links whose path is explicitly listed in the route inventory; it reports query-bearing or uninventoried links without requesting them and redacts query values from its report. It does not submit forms. Third-party OG images require separate verification. It cannot discover omitted dynamic routes, judge copy/alt meaning, certify XML/robots policy or prove cookie consent. Inspect every manual_checks entry; never translate this report into automatic launch passes.

Add project Playwright tests for navigation/menu, all loading/validation/network/success states and consent-eu.md's full network/storage matrix. Stub remote form/analytics destinations unless real test traffic is authorized. Use accessible role/label selectors, deterministic response/element waits rather than fixed sleeps, and redacted traces/screenshots. Run axe, keyboard focus, 200% zoom, reduced motion, touch targets and mobile CTA/banner/keyboard obstruction review. Avoid a blanket networkidle wait on sites with persistent traffic.

## Lighthouse and CI

Run the project's pinned binary against its production build; use mobile defaults consistently and save tool/device/network settings. Example from the site directory:

```bash
./node_modules/.bin/lighthouse <page-url> --output=json --output-path=qa/lighthouse.json --chrome-flags=--headless
python3 <agent-repository>/scripts/brand/check_lighthouse.py qa/lighthouse.json
```

The Python checker enforces default per-run LCP/CLS/TBT/performance/SEO budgets and fails on missing values. Capture three runs per representative route, review median and regression deltas as defined in seo-performance.md. It does not prove report origin, field INP, every-page coverage or legal/SEO completeness. If project budgets differ, encode/review those in project CI; do not call the default checker a pass on missing metrics.

Project CI: locked install, lint, typecheck, unit/state tests, production build, Playwright/axe, route audit, Lighthouse budget checks. Retain reports on failure and propagate nonzero statuses (never hide failures behind a final successful command or `|| true`). Secrets stay in environment; no production analytics by default in CI. Record tested commit, URL/config, route scope and manual outcomes in the launch assessment. Missing browser/Chrome/Lighthouse tooling means pending testing, not pass.
