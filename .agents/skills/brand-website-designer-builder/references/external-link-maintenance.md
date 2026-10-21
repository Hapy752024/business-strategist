# External resource maintenance

Apply when building resource pages or maintaining outbound links. Keep discovery, network observations, editorial review and scheduled activation separate. Do not remove resources automatically from a status-code report.

## Discover automatically

Use the complete route/CMS/locale inventory to collect built HTML or rendered DOM captures of in-scope public pages. Extract external anchors afresh each run; a hard-coded URL list alone misses changes. Source/Markdown extraction supplements rendered coverage. Record omitted routes, states, locales and client-only links. Do not recursively crawl external sites.

```bash
python3 scripts/brand/discover_external_links.py <website>/qa/captures.json > <website>/qa/external-inventory.json
```

`captures.json` is a nonempty array such as `[{"url":"https://site.example/guide","file":"captures/guide.html"}]`; file paths are relative to that JSON. Supply sanitized public captures. This offline standard-library helper deduplicates destinations, keeps referring page/file/line and fragment presence, resolves the first non-template HTML base, and omits query/credential values from skipped records. It does not execute JS, discover routes, validate fragments or fetch URLs. Empty inventory does not prove coverage. Resource images/CSS assets need separate asset tests.

Review candidates before network execution, including action/unsubscribe/logout URLs, signed paths, private destinations and tracking. Resolve destinations and redirects only in an isolated network environment that cannot reach internal/metadata services; the inventory helper is not a destination-safety validator. Query links require a separately reviewed sanitized public equivalent or manual check; never silently strip a meaningful query and test a different resource. Keep confidential URLs out of artifacts.

Keep a small curated registry for critical-resource meaning: URL, referring pages, intended subject/jurisdiction/audience, owner, last editorial review, review interval and expected redirect/fragment. Exceptions require URL pattern, evidence, reason, owner and expiry; expired exceptions reopen review. Show skipped/unmeasured counts.

## Check and classify

Reuse a pinned checker such as Lychee instead of building a networking stack. Prefer GET for final checks; HEAD can produce false failures and cannot inspect content. Record checker version and bounded timeout/redirect/concurrency settings. Start with serial requests and zero automatic retries. After creating a reviewed one-URL-per-line `approved-links.txt`:

```bash
lychee --method GET --max-concurrency 1 --max-retries 0 --timeout 20 --max-redirects 5 --format json approved-links.txt > external-check.json
```

This is a manual pattern for an already installed pinned version, not an installed monitor. Retain output and nonzero status. These flags do not establish per-host cooldown or internal-network isolation. Use host-grouped bounded batches and pause a host when rate limited; do not bypass bot protection or site access policies.

| Observation | Disposition |
| --- | --- |
| 2xx | Reachable now; relevance/freshness unverified. |
| 301/308 | Record chain/final URL; verify equivalent content before updating. |
| 302/303/307 | Temporary destination; no automatic source rewrite. |
| 404/410 | Broken candidate; independently confirm important resources before removal. |
| 401/403, challenge, geoblock | Restricted/unverified, not confirmed broken. |
| 429 | Rate limited; pause host, respect Retry-After date/seconds; never count healthy. |
| 5xx, DNS, TLS, timeout | Infrastructure/transient/security failure awaiting confirmation; do not disable TLS validation. |
| Loop, excess hops, downgrade, unrelated destination | Redirect review even if a destination eventually returns 200. |

Use capped delayed retries with jitter only for transient failures within the run budget; defer if Retry-After exceeds that budget. Retain attempts and consecutive-run history. Do not globally accept 403/429/timeouts to turn CI green. Manually verify ambiguous/critical cases with dated browser evidence and an explicit reviewer disposition; unresolved critical checks remain pending. Validate fragments separately against rendered IDs where practical.

## Review meaning and operate

Critical resources need title, organization, subject, locale, jurisdiction and key-fact review after HTTP success. Soft 404s, parked domains and login pages can return 200. Compare relevant excerpts or structured fields rather than whole-page hashes: navigation and timestamp changes create noise. ETag, Last-Modified and hashes indicate representation changes, not factual freshness. Require editorial verification before changing claims or replacement sources.

Default delivery, adapted to risk: discovery at each build, transport check before release, weekly scheduled CI link checks, monthly critical-resource editorial review (faster for time-sensitive claims). These are engineering defaults, not universal standards. Keep external network checks separate from deterministic PR tests; a third-party outage should receive an explicit risk disposition, not automatically break every unrelated build.

## Required CI delivery

When implementing link QA, automatically create or update the site's `.github/workflows/external-links.yml` and the commands it invokes. Reuse an equivalent existing workflow rather than creating duplicates. Do not stop at a local checker, recommendation or owner setup instructions. If the selected repository already uses another CI provider, implement the equivalent there; do not introduce GitHub hosting solely for this check. Preserve an explicit user decision to disable or defer monitoring.

- Include both `workflow_dispatch` and a weekly `schedule`, using a documented UTC cron at a non-zero minute. Adapt the day/time to a stated preference. The schedule must work after publication to the default branch without a separate opt-in variable by default; honor existing explicit activation choices.
- Use the actual repository root or monorepo working directory, locked dependencies, required browser/tool setup, production build or other supported page capture, fresh discovery, approved destination checks and a readable report with referring pages. Pin checker versions and action revisions. No application database, email or analytics credentials should be needed for public link QA.
- Use read-only repository permissions, bounded runtime/concurrency/request budgets and sanitized artifacts uploaded even when checking fails. Propagate errors and unresolved coverage as described above; do not hide failures with `continue-on-error`, `|| true` or broad accepted-status exceptions. Keep third-party network checks in a separate job/workflow from deterministic PR checks; do not use `pull_request_target` to execute untrusted changes with privileges.
- Include offline tests/discovery in existing PR CI where applicable. A weekly job must regenerate its inventory, not repeatedly check a stale committed list. Result-only links and omitted interactive states need explicit supplementary coverage or a visible gap.
- Validate commands and workflow structure locally. When repository access and publishing are already authorized, publish through the project's normal GitHub delivery process, enable the workflow if necessary, dispatch an initial run, inspect its result and retained artifact, and record the run URL/revision. Do not ask again for authorization already provided. If publication/access is unavailable, still deliver the complete workflow file and state the exact remaining step; do not claim monitoring is active.

Creating workflow files is part of link-QA implementation and needs no separate scheduling approval. Publishing follows the existing GitHub delivery authorization; generating this workflow does not authorize a production deployment, a new account, paid subscription or messages to new recipients. Document the platform's failure-notification settings; do not silently connect email, Slack, issue creation or other destinations.

An activated monitor needs owner, cadence/timezone, request budget, approved targets/exceptions, retained reports, last-success timestamp and a missed-run check. GitHub schedules may be delayed/dropped; configuration does not prove execution. Implement missed-run detection when selected, otherwise explicitly assign an owner to check last-success history and identify the absence of an independent alarm. Return a review queue grouped by source page/severity, checked/skipped/unknown counts, next review, workflow path, activation state and initial-run evidence. A manually dispatched success does not prove a future calendar-triggered run or notification delivery.

Research basis: repo-root `evals/website-maintenance/2026-10-17-external-resource-maintenance.md`.
