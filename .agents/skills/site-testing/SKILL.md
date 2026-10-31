---
name: site-testing
description: Test a selected web app in a real browser with Playwright, or run release regression checks. Use for focused frontend checks, screenshots, browser-error diagnosis, or, only on explicit request, pre-release regression.
license: Browser mode and scripts/with_server.py derive from Anthropic's webapp-testing skill; Apache-2.0 terms in LICENSE.txt.
---

# Site Testing

Pick the mode from the checked route; plain text infers it from the request. This skill tests and reports; page fixes and changes go to route `website-build`.

| Route | Mode | Use for | Reference |
| --- | --- | --- | --- |
| `webapp-testing` | browser | focused local browser checks, screenshots, console errors, debugging | [browser](references/browser.md) |
| `pre-release-regression` | regression | release scope, changed journeys and shared dependencies, run only on explicit request | [regression](references/regression.md) |

## Shared rules

- Discover the selected application's instructions, commands, URL and existing test framework; reuse its browser
  tests. Playwright and its browser binaries must already be installed.
- Use synthetic data, sanitize artifacts and stop before unauthorized live transactions, payments outside test mode
  or external messages.
- Report environment, commands, expected versus observed behavior, evidence paths and untested coverage.
  Browser checks are not unit tests, and a local or preview pass does not establish production readiness or
  authorize deployment.

## Modes

- **browser:** follow [browser workflow](references/browser.md). For optional Python server orchestration, run
  `scripts/with_server.py --help` first.
- **regression:** runs only on explicit request (the former user-only pre-release check). Follow
  [release workflow](references/regression.md); it uses the browser workflow for execution and reports pass, fail,
  skipped and blocked separately. Ordinary browser debugging stays in browser mode.
