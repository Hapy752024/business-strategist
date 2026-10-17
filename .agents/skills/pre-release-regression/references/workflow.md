# Release Regression Workflow

1. Resolve the selected application and release scope. Use an explicit base commit/tag where supplied; otherwise inspect history and release metadata. If no defensible base exists, report that gap and use a declared bounded scope rather than inventing a tag or commit range.
2. Discover existing test suites, fixtures, supported languages, responsive targets and product journeys. Map changes and shared dependencies to affected behavior.
3. Prioritize critical journeys, authorization boundaries, validation, navigation/reload behavior and integration failure states. For payment changes, include affected payment journeys, decline/cancel/retry cases and durable fulfillment. Choose languages and devices from actual support requirements.
4. Reuse existing tests first. Add lasting regression cases when they protect changed behavior and the task authorizes implementation. Do not manufacture a permanent generated suite for every release.
5. Execute against the verified local or explicitly authorized test environment using the project's browser runner or available Playwright tooling. Never infer a URL from a host naming pattern or API environment variable. Confirm test credentials and payment test mode before transactions. Stop before live charges, customer messaging or other unauthorized side effects.
6. Save sanitized screenshots, traces and logs where needed in the target project's established evidence directory. State commands, base/head, target environment, cases, expected/observed outcomes and artifact paths.
7. Report failures, skipped/blocked coverage and remaining release requirements. A tested preview is evidence for that preview; production verification and deployment require their own authority.
