# Validation and review record — 2026-09-14

Scope: reusable website and Branding capabilities, not project research or a deployed website. Pre-existing dirty changes were preserved; task-local snapshots for existing touched files were captured under /tmp/website-setup-baseline. No commit, deployment, external account connection or tracking activation performed.

## Implemented

Existing website builder now owns creation/maintenance/testing, SEO/LLM-EO, consent and optional measurement guidance. Branding owns favicon creation; its two exporters now include 180/192px outputs and generate multi-resolution ICO files from the largest available raster rather than the smallest. Added launch assessment initialization/schema and production completeness gate, bound to full commit, URL and deployment/config ID. Analytics alone may be not_requested with evidence.

Runnable tools: scripts/brand/audit_web_pages.mjs (project Playwright), check_lighthouse.py (lab report budgets), website_launch.py (evidence completeness). No new orchestration skill or mandatory provider dependency. Extended route vocabulary and fixed Next.js being split at its period. Optional campaign references include verified sources and practical account/event/consent/server delivery setup sequence.

## Checks

- bash scripts/validate_setup.sh: 496 Python tests passed; zero errors; one setup warning for existing town-db-curator Quality Checklist guidance. Its missing eval file is also reported as an accepted coverage warning.
- Targeted website/browser/favicon suite: 59 passed, including actual local Chromium, missing-description rejection, correct/incorrect redirects, all mandatory launch-check omissions, release-binding mismatches, optional analytics and ICO entries.
- Final targeted routing/release/favicon regression run: 87 passed.
- Website skill quick validation, catalog/disk/route reachability, eval structure, Python compilation, Node syntax and git diff --check passed. Branding quick validation passed with its existing description heuristic warning.
- Launch and Lighthouse CLI smoke checks correctly returned failure on pending/missing evidence.

Initial sandbox run could not create HTTP sockets/spawn some child processes; required checks were rerun with approved escalation and passed. The website entry initially exceeded the repo 30-line budget; it was reduced before final full validation.

## Review iterations

- Fresh plan reviewer 1: required explicit production URL/configuration binding, not just Preview/source commit. Plan corrected.
- Fresh plan reviewer 2: PASS on full 20-item/test plan.
- Fresh implementation reviewer 1: valid redirects caused duplicate-metadata false failures. Added explicit redirect status/destination expectations and regressions.
- Fresh implementation reviewer 2: experiment stopping language was misleading. Replaced it with predeclared fixed-horizon or valid sequential stopping.
- Expanded optional tracking plan: separate fresh plan review PASS before final reference/sequence integration.
- Final combined implementation review: PASS, no meaningful remaining findings. Reviewer independently verified all 59 targeted tests (55 in sandbox plus four actual Chromium cases outside sandbox).

## Limits

Launch gate validates attestation completeness and source/URL/config bindings, not artifact truth or live deployment identity. Browser audit reports automated observations and manual gaps; it cannot prove inventory completeness, legal compliance, full SEO or consent semantics. Lighthouse checker reads supplied reports; no real website Lighthouse performance result was produced here. Server delivery/PostHog/GA4/Meta are reusable integration instructions and test contracts, not live integrations tested in this task. Cross-host behavioral quality and analytics uplift have not been measured. Third-party repository review is selective fit/source inspection, not a comprehensive security/license audit or execution benchmark.
