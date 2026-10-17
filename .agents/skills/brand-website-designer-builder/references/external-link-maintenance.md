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

Default proposal, adapted to risk: discovery at each build, manual transport check before release, weekly link checks, monthly critical-resource editorial review (faster for time-sensitive claims). These are engineering defaults, not universal standards. Prepare optional config without activating it until authorized. Keep external network checks separate from deterministic PR tests; a third-party outage should receive an explicit risk disposition, not automatically break every unrelated build.

An activated monitor needs owner, cadence/timezone, request budget, approved targets/exceptions, retained reports, last-success timestamp, missed-run detection and explicitly authorized notification destination. GitHub schedules may be delayed/dropped; configuration does not prove execution. Do not implicitly create schedules, subscriptions, account connections, issues or messages. Return a local review queue grouped by source page/severity, checked/skipped/unknown counts, next review, and whether a monitor actually runs.

Research basis: repo-root `evals/website-maintenance/2026-10-17-external-resource-maintenance.md`.
