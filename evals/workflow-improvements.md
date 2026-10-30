# Agentic workflow improvement log

Single shared record for failures, problems and improvement candidates across this repository. Instructions in `AGENTS.md` require agents to maintain this file. Existing evaluation suites remain the executable evidence; this file tracks what to review and improve.

## How to use

- Search by symptom and component before adding an entry. Repeated incidents update the same ID and history.
- Use the next `WF-NNN` ID. Priorities: P1 incorrect completion, evidence integrity or data exposure; P2 workflow reliability/correctness; P3 improvement opportunity. State the impact rather than relying only on priority.
- Status: `open`, `in_progress`, `blocked`, `deferred`, `resolved`. A blocked/deferred entry needs the condition for resuming. An implemented change remains in progress until its relevant verification passes.
- Separate observed behavior from suspected causes. Include a minimal reproduction or evidence link, expected behavior, affected scope, owner/next action and dated closure evidence. Unknowns remain unknown.
- Retain resolved entries and their history. Reopen on recurrence. Preserve other agents' edits; reread the affected section before updating it. Never retain secrets or private customer data.
- During a workflow review, prioritize open/blocked items by impact and recurrence; validate older evidence before choosing work. Logging does not itself authorize implementation or external actions.

## Review queue

### WF-027 — Website SEO launch misses production host canonicals and owner indexing handoff

- Priority/status: P2/resolved for deterministic implementation; live agent behavior unverified. First/last observed: 2026-10-30. Owner: Website skill maintenance (`brand-website-designer-builder`).
- Observed (live): the deployed Italy site declared canonicals, `og:url`, sitemap entries and the robots sitemap on `https://italyforretirees.com` while that host returned 308 to `https://www.italyforretirees.com`. Local launch tests passed because `tests/launch.spec.ts` asserted the same hard-coded origin. A `site:` search returned no indexed pages; no Search Console property, sitemap submission or indexing request was recorded or prompted. Guides had no visible byline/update date, titles reached 81 characters, thin utility pages (questionnaire, legal, credits) were in the sitemap, and the secondary domain `italymoveguide.com` did not respond. Evidence: live audit in this session; fixes in `projects/us-retirees-italy/web-site/app/metadata.ts`, `app/sitemap.ts`, `app/robots.ts`, `app/guide/guide-meta.tsx`, `qa/routes.json`, `owner-actions.md`.
- Expected/impact: the launch contract should prove that every canonical/sitemap URL answers 200 on the production host without a redirect, and hand the owner a step-by-step Search Console/Bing onboarding task. Otherwise a site can pass all checks yet send conflicting signals and stay unindexed with nobody assigned to notice.
- Cause: confirmed that `references/launch-contract.md` and `references/seo-performance.md` say to repeat canonical checks after deployment and that `references/maintenance.md` mentions indexing ownership, but neither defines a production-host redirect probe, a domain/secondary-domain policy, a Search Console onboarding owner action, or title-length/thin-page/byline checks; `scripts/brand/seo_checks.py` has no title-length check. Hypothesis: the same-origin test fixture masks host mismatches in other projects.
- Next action: (1) add a post-deploy check that fetches each canonical and sitemap URL on the production host and fails on any 3xx, and derive test origins from the site constant instead of hard-coding; (2) add a `search_console` owner handoff (domain-property DNS verification, sitemap submit, URL inspection for key pages, Bing import, 1–2 week coverage review) to the launch contract and maintenance handoff, written into the project's owner actions; (3) record every registered domain with an explicit redirect/lapse decision; (4) add warnings for titles over about 60 characters, thin indexable utility pages, and guide pages without a visible byline/updated date/sources. Verify with `python3 scripts/evaluate.py check` plus a fixture whose canonical host redirects.
- Resolution/history: 2026-10-30 Italy site corrected locally and deployed by the owner (live canonicals and robots now on www). Same day: added `scripts/brand/production_seo_probe.py` (no-redirect production probe of robots, sitemap, canonical and og:url hosts; secondary-domain `redirect`/`lapse` decisions; warnings for titles over 60 characters, thin indexable pages and articles without date/sources/Article data; Search Console owner-actions row generator); title warnings in `scripts/brand/seo_checks.py`, surfaced as `seo_warnings` by `audit_web_pages.mjs`; launch checks `production_host` and `search_console` (`owner_handoff` allowed with evidence) in `scripts/brand/website_launch.py` and `schemas/website-manifest.schema.json`; launch-contract, testing, seo-performance, maintenance and SKILL.md instructions; eval `website-post-deploy-production-host-and-search-console`. Italy manifest records `production_host: fail` (only `italymoveguide.com` unreachable) and `search_console: owner_handoff`.
- Closure evidence: `tests/test_production_seo_probe.py` (16, including the redirecting-canonical regression) plus launch/SEO suites: 105 passed; `python3 scripts/evaluate.py check` PASS (`evals/local-runs/20261030T161646Z-eacd97255949`); `scripts/validate_skill_routes.py` no errors; full `pytest tests`: 1301 passed, 1 unrelated pre-existing failure in `tests/test_skill_hygiene.py::test_paid_campaign_reference_exists_and_is_linked`. Live probe against the Italy site ran and reported the expected domain error. Remaining limit: no native model trial yet shows the agent runs the probe and writes the owner handoff unprompted.

### WF-026 — Website references and supplied-photo modes lacked a shared workflow

- Priority/status: P2/resolved for instruction, routing and storage contracts; live image quality unverified. First/last observed: 2026-10-23. Owner: Website and asset skill maintenance.
- Observed/cause: website reference intake was optional, asset guidance centered on FAL/OpenRouter, and no shared procedure covered mixed supplied-photo uses, stock acquisition or licensed-stock AI-reference permissions. Universal imagery approval wording also restarted branding for scoped image work.
- Impact: supplied references could be missed or reused without the intended usage distinction; native generation and rights provenance were underspecified.
- Change: added ask-once reference inspection and saved preferences, shared image sourcing with as-supplied/edit/AI-guidance/brief-only modes, stock rights checks, native imagegen handoff and per-output reference lineage. Reused scoped briefs instead of universal logo/imagery gates; registered focused routing phrases and authored behavioral scenarios.
- Closure evidence: `tests/test_website_image_workflow.py` and existing website/favicon/orchestrator tests: 75 passed; route validation and both edited skill entrypoint validations passed; `python3 scripts/evaluate.py check` deterministic PASS (`evals/local-runs/20261023T162050Z-0e3b201fe514`). Mixed-workflow requests retain the existing explicit-intent routing contract.
- Remaining boundary/next action: authored photo/reference scenarios have not been run as native model trials. Review actual source handling, license decisions, generated imagery and independent quality grades during a real authorized asset task; no generated-image quality improvement or production effect is claimed.

### WF-025 — Analytics stubs miss real-provider consent and automatic-event behavior

- Date: 2026-10-23. Area: website analytics/consent verification. Priority: P1. Status: open.
- Observed: mocked browser consent tests passed while a real Google tag emitted an additional delayed pageview for an already consented route after withdrawal. No new refused-route path was observed; fresh post-refusal collection versus previously queued delivery must remain distinguished. Separately, real PostHog bot filtering excludes automated browsers unless the test browser simulates normal navigation, so a consented event can be missing without an integration failure.
- Expected: initial refusal produces no vendor requests; consented views are sanitized and counted once; withdrawal suppresses both future captures and pending traffic under the selected acceptance criterion.
- Impact: fake-provider tests alone cannot prove account connection, automatic-event settings, or real SDK withdrawal behavior. Declaring production readiness from those tests would be incorrect.
- Evidence: `projects/us-retirees-italy/web-site/qa/analytics-2026-10-23/review.md`; `projects/us-retirees-italy/web-site/tests/analytics.spec.ts`. No tokens or visitor data retained in this log.
- Next action: review/disable the GA stream's automatic history measurement and unnecessary enhanced events, then rerun real-provider duplication and withdrawal checks. Keep release pending until that result is verified. No workflow/skill changes or unrelated account operations are authorized by this entry.
- 2026-10-23 implementation update: Google now defaults off behind a deployment flag until the account-side history/automatic-event setting and a real-provider retest are complete. A prior analytics grant is cleared/blocked if saving withdrawal fails; its browser regression passes. Server totals use committed pending snapshots before network delivery, since changing totals after an uncertain response otherwise changes retry identity and risks overlapping counts. PostgreSQL replay/concurrency/retention/role tests pass, and the real EU batch endpoint accepted a labelled synthetic aggregate with `{status: "Ok"}` (numeric-only acknowledgement fixtures would have incorrectly rejected it). Production migration/deployment remains pending; this entry stays open for the Google real-provider gap.
- 2026-10-24 owner-authorized replay update: added masked, consent-gated replay outside check/questionnaire/payment routes with DOM blocking during transitions and URL-parameter exclusions. Retained prior refusals; prior pageview-only grants need a fresh choice. Real SDK browser checks exposed the recorder requirement for a post-start user interaction before upload, so synthetic DOM mutation alone was insufficient evidence. Local mocked ingestion verifies masked snapshots, wizard exclusion, resume and withdrawal; project replay enablement, retention and production ingestion remain unverified. Evidence: `projects/us-retirees-italy/web-site/tests/replay.spec.ts`, `scripts/tests/replay-policy.test.ts` inside that website. Existing Google gap remains open.



### WF-023 — Visa-check email is raw JSON and success leaves the request form visible

- Date: 2026-10-21. Area: website visa-check result delivery. Priority: P2. Status: in_progress.
- Observed: owner completed the visa check, requested the result by email, received the full payload as JSON, and expected the email field to be replaced by a prominent success confirmation. Current source confirms the email HTML rendered the serialized payload inside `<pre>`, while the page only set a plain status message and left the form mounted.
- Impact: requested result is harder to scan, and successful delivery is not clearly distinguished from an unfinished request. Fix implemented: render a branded HTML result email with verdict, reasons, caveats, route, documents, wait estimate, source and a plain-text alternative; replace the form after a successful send with an accessible green confirmation and check mark. A new result resets the prior email-success state.
- Closure: pending focused email-rendering and browser-flow verification. No test suite was run in this change.
- Evidence: `projects/us-retirees-italy/web-site/app/lib/wizard-events.ts`, `projects/us-retirees-italy/web-site/app/check/checker.tsx`, `projects/us-retirees-italy/web-site/app/globals.css`.

### WF-022 — Real contact-form browser checks caught locale hydration and invisible-validation defects

- Follow-up 2026-10-19: owner supplied a trace referring to the superseded `names.of` country picker and a historical contact 503. Current source uses the shared fixed list. Fresh development browser submission/retry checks passed with no hydration errors after Fast Refresh settled. A proof from the running server passed through the current handler with Railway and Brevo sandbox: HTTP 200, provider 201, receipt accepted and synthetic receipt removed; no real email sent. Original 503 was not reproduced. Added sanitized server-side 5xx category/database-code diagnostics for future investigation. Evidence: `projects/us-retirees-italy/web-site/qa/contact-form-2026-10-19.json`.

- Date: 2026-10-18. Area: website contact form. Priority: P2. Status: resolved.
- Observed: server and browser `Intl.DisplayNames` country labels differed, causing a real hydration warning. Separately, native validation of the invisible CAPTCHA checkbox could swallow submission before the React handler ran. Backend-only proof and sending tests did not expose either issue.
- Impact: contact submission could fail despite valid user input and a correct backend. Fix: use one fixed English phone-country list for SSR/client rendering (also applied to the questionnaire); disable form-wide native validation and explicitly validate visible required fields before running invisible verification on submit.
- Closure: all 7 development browser checks passed, followed by all 6 contact browser checks against the optimized preview build, including no console/page errors or offsite requests, real proof computation, failure/retry with preserved input, mobile/desktop axe and contact-link migration. Seven local PostgreSQL/API checks passed for proof tampering/expiry, replay, rate limits, idempotency, origin/body validation and HTML escaping. Brevo sandbox returned 201 without real delivery. Build, TypeScript and lint passed.
- Evidence: `projects/us-retirees-italy/web-site/tests/contact.spec.ts`, `projects/us-retirees-italy/web-site/scripts/tests/contact.test.ts`, `projects/us-retirees-italy/web-site/qa/contact-form-2026-10-18.json`.

### WF-021 — A new follow-up category conflicted with the wizard-name constraint

- Date: 2026-10-18. Area: website regional availability. Priority: P2. Status: resolved.
- Observed: first synthetic local API probe returned 503 because a proposed new wizard name was outside the existing database CHECK constraint. The schema allowed only the visa checker and moving questionnaire.
- Impact: a region-specific follow-up could not be recorded. Fix: keep `moving-questionnaire` and store `requestType: regional-review-waitlist` plus the follow-up status in the existing JSON inputs. No migration or constraint weakening needed.
- Closure: two real local API requests with the same synthetic event returned 200 and the availability URL; independent DB readback found exactly one follow-up record and zero payment orders. The synthetic row was removed. Gateway unit checks verified unavailable-only requests never reach database/payment session creation in the payment service; browser checks covered the notice, no Stripe navigation and mobile/desktop accessibility. TypeScript and lint passed.
- Evidence: `projects/us-retirees-italy/web-site/app/api/checkout/route.ts`, `projects/us-retirees-italy/web-site/db/wizard-events.sql`, `projects/us-retirees-italy/web-site/tests/regional-availability.spec.ts`.

### WF-020 — Mocked checkout checks missed a Stripe API enum change

- Date: 2026-10-18. Area: Stripe checkout. Priority: P2. Status: resolved.
- Observed: real test-mode checkout returned 503 because Stripe rejected `ui_mode: hosted`, requiring `hosted_page`. Mock gateway and browser checks had not exercised the real session-creation request.
- Impact: questionnaire payment could not open despite valid credentials and reachable database. Fix: use `hosted_page` in `projects/us-retirees-italy/web-site/app/lib/review-payment-server.ts`, matching current official Checkout Session API documentation.
- Closure: read-only schema and test-key authentication probes passed; real local POST `/api/checkout` returned 200 with a Stripe Checkout URL after the fix. Synthetic unpaid test session was expired afterward; no charge was made. TypeScript check passed. No production deployment or completed-payment/webhook verification claimed.
- Next action: retain real Stripe test-mode session creation as a release check when credentials are available; mocked tests alone do not establish provider compatibility.

### WF-024 — Modules shared no checked state; experiments and truthfulness were unenforced

- Dates: observed 2026-10-21, resolved 2026-10-21. Area: Business research and strategy modules. Priority: P2. Status: resolved (structural); live-quality gap open.
- Observed: assumptions lived in prose, only the smoke test was a first-class experiment, results never flowed back into case insights, the router could not report runnability, and the truthful stance in AGENTS.md had no check. The smoke-test kit emitted placeholder thresholds.
- Change: per-case `assumptions.json` register and `experiments/E-*.json` cards with publisher-only writes (`case_workspace.py assumptions|experiment-plan|experiment-approve|experiment-start|experiment-close`); `config/experiment-library.json`; rewritten smoke kit with computed sample plan; `import_responders.py`; insights contract v3 with `{{assumption.<id>}}`, change-trigger and could-not-check sections and a paragraph-level evidence/status rule; typed catalog `consumes`/`produces` and `route_workflow.py status`; transcript-coding ingester; decision KPIs; challenge-first skill outputs; `founder-pushback` and `premature-validation` eval cases. Design and plan: `docs/superpowers/specs/2026-10-21-agentic-validation-loop-design.md`, `docs/superpowers/plans/2026-10-21-agentic-validation-loop.md` (gitignored).
- Closure evidence: branch `feature/validation-loop`; tests `test_case_artifacts_schema.py`, `test_assumption_register.py`, `test_experiment_cards.py`, `test_case_insights.py` (v3 and truthfulness cases), `test_smoke_test_kit.py`, `test_import_responders.py`, `test_catalog_contracts.py`, `test_case_status.py`, `test_truthfulness_structure.py`, `test_ingest_transcript_coding.py`, `test_capability_registrations.py`; full suite 1253 passed with only the WF-007 failure; `evaluate.py check` PASS.
- Final review 2026-10-21 (fresh reviewer): fixed approval dead end, rate-blind pass, CWD-relative importer ledger, per-event counting, unsalted pseudonyms, variant-0 parsing and opt-in v3 rules; suite 1260 passed (WF-007 only). Five minors deferred in the branch ledger.
- Still open: the two new eval cases have not been run as native trials or graded (WF-011 OAuth); GrowthBook/PostHog import presets are unverified against real exports; Dialog Reddit MCP is registered but not validated by the provider doctor. Structural checks do not prove agents are less agreeable in practice.
- Follow-up 2026-10-21: Dialog Reddit MCP registered at local scope as subreddit discovery only, with `subreddit_query_rows.py` handing communities to the Reddit API collector; first use needs the founder's own OAuth sign-in through `/mcp`.

### WF-019 — Pre-hydration motion bootstrap mutates the root class

- Date: 2026-10-18. Area: website motion. Priority: P2. Status: resolved.
- Observed cause: Italy homepage head script added `js` to the root class before React hydration, differing from the server/client layout props and triggering the reported hydration warning.
- Impact: development hydration warning on the shared layout. Fix: enable motion inside the hydrated motion component and remove the marker during effect cleanup; preserve readable content without JavaScript.
- Closure: TypeScript check passed. Chromium against the existing `http://localhost:3000` development server passed initial navigation and reload with no console/page errors and motion enabled. A JavaScript-disabled browser confirmed arrival content remains visible. Access through `127.0.0.1` instead produced development HMR websocket errors; verification used the server's localhost origin. No production deployment performed.
- Evidence: `projects/us-retirees-italy/web-site/app/layout.tsx`, `projects/us-retirees-italy/web-site/app/motion-client.tsx`.

| ID | Priority | Status | Area | Issue |
| --- | --- | --- | --- | --- |
| WF-027 | P2 | resolved | Website SEO launch | Production host canonicals unverified; no Search Console owner handoff |
| WF-023 | P2 | in_progress | Visa-check email | Raw JSON email and unclear successful-send state |
| WF-024 | P2 | resolved | Validation loop | Modules shared no checked state; experiments and truthfulness were unenforced |
| WF-001 | P1 | resolved | Placement evidence | Inert template anchor incorrectly completes a placement |
| WF-002 | P1 | resolved | Capture privacy | Rejected sensitive URL retained in failure record |
| WF-003 | P2 | resolved | SEO comparison | Aborted audit incorrectly resolves earlier defects |
| WF-004 | P2 | resolved | Marketing provenance | Opportunity stays current after its source changes |
| WF-005 | P2 | resolved | Public fetching | Trickled headers bypass total deadline |
| WF-006 | P2 | resolved | Evidence recovery | Original capture/observation cannot be restored transactionally |
| WF-007 | P2 | resolved | Research tests | Competitor-query warning expectation fails |
| WF-008 | P3 | resolved | Skill maintenance | Three existing skill entries exceed line budget |
| WF-009 | P3 | open | Review tooling | Provider/model identity diagnostic needs verification |
| WF-010 | P1 | resolved | Non-video contracts | Retry, preservation and audience gaps fixed |
| WF-011 | P3 | open | Model evaluation | Expired OAuth prevents live trials |
| WF-012 | P2 | resolved | SEO audit | Equivalent root canonical URLs produce a false failure |
| WF-014 | P2 | resolved | Skill imports | Copied app-specific skills bypass catalog and context boundaries |
| WF-015 | P2 | resolved | Website QA | Passing contract tests miss checker and offer-scope inconsistencies |
| WF-016 | P2 | resolved | Website lifecycle | Link maintenance and privacy design lacked reusable implementation guidance |
| WF-017 | P1 | resolved | Payment state | Test payments could survive a switch to live configuration |
| WF-018 | P2 | open | Marketing operations | Campaign planning and export analysis lack recurring connected execution |

## Entries

### WF-018 — Connected marketing operations remain unimplemented

- First/last observed: 2026-10-17 / 2026-10-24. Owner: Marketing workflow maintainer. Priority/status: P2/open; local reporting review corrections verified, connected operation pending.
- Observed: `references/modules/marketing.md` explicitly documents no sender or scheduler. `scripts/marketing/observations.py` normalizes local aggregate exports; `scripts/marketing/execution.py` validates/renders action packets. Root MCP configuration contains research providers, not own-account advertising or publishing connections. This establishes a repository capability gap, not the user's account eligibility or campaign quality.
- Reproduction/evidence: inspect those files and `scripts/sync-brand-mcp-config.py`; the latter currently emits local command transports only. Proposed scope and dated source checks: `docs/agent-improvements/2026-10-17-marketing-automation-plan.md`.
- Impact: the agent can prepare useful work and interpret uploads but cannot yet provide dependable scheduled campaign management or connected publishing/ads execution. Instructions alone cannot enforce spend or delivery authority.
- Next action: select the first real project/export pilot, then implement P3 isolated reporting connections, P4 scheduling and separately authorized publishing/advertising operations. P0/P1 and minimum P2 are implemented locally; the five follow-up review corrections and their verification are recorded in `evals/marketing-local-review-2026-10-18.md`. Extend transport generation or use a reviewed bridge when a chosen MCP requires HTTP; preserve existing workflow ownership and project artifacts.
- Research limitation: Firecrawl prerequisite scrape failed with `Insufficient credits`; status reported -451 credits. Public HTTP recovered the ChatGPT input, while Gemini/Claude returned shells and DeepSeek returned 403; browser retries timed out. Independent official sources support the plan, but the three unread chats remain a coverage gap. This repeats the provider-credit limitation recorded under WF-016; it is not negative marketing evidence.
- Second pass 2026-10-17: all four shared chats were retrieved through the Firecrawl MCP hosted scrape and incorporated (adopt/covered/reject table in the plan). Plan revised with the official write-capable Meta Ads MCP (S14), Claude Code routines as candidate unattended runtime (S18), a `campaign-context.md` plus claims/compliance gate (Phase 1b), selective evaluation of `coreyhaines31/marketingskills` and `aaron-he-zhu/seo-geo-claude-skills` instead of bulk install (S16, S17), and a content-refresh PR loop (Phase 3c). The earlier coverage gap is closed; the capability gap remains open. Second fresh-context review scored 67/100 (BLOCK unattended writes, FLAG connected observation, PASS-with-flags upload loop); its two blocks (execute profile leaking into repository harness configs via `sync-brand-mcp-config.py`; no enforcement point for the write-capability rule) and five flags were resolved in the plan and recorded under “Second-pass resolution” in the review document. Next implementation step is Phase 1a (thin upload report with export presets).
- Recurrence 2026-10-21: Firecrawl CLI returned HTTP 429 on a parallel search burst, then `Insufficient credits` on scrape; methodology research fell back to `scripts/serper_fetch.py`, `gh api` and plain web fetch. Coverage gap only (one 429 from bigideasdb.com); not research evidence.
- Closure evidence: pending implementation and relevant deterministic checks, independent agent evaluation, and separately authorized observed scheduled/account delivery. A plan review does not close this capability gap.
- Follow-up source correction 2026-10-17: Meta's official [MCP setup documentation](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-get-started/?locale=en_US), retrieved through public HTTP after web-reader failures, documents OAuth, user tokens and Employee-role system-user tokens. Minimum permissions are `ads_mcp_management` plus `ads_read` or `ads_management`; additional permissions enable more tools. The plan's blanket execute-only/proxy requirement was based on the overview and is too broad: evaluate a credential with only the minimum read permissions, inspect actual available tools/account reach and establish denied mutations before allowing unattended reporting. No authenticated behavior was checked. Anthropic's [routines documentation](https://code.claude.com/docs/en/routines#connectors), checked the same date, permits removing connectors per routine; an account-wide Meta connector ban is a conservative policy choice, not a documented technical requirement. Also reconcile the Phase 1b row's direct reuse of case-specific claim checkers with the detailed section that explicitly rejects direct reuse.
- Multi-project requirement 2026-10-17: the user needs shared marketing workflows with separate project connections. Bind each run to explicit project/account allowlists and credential references; keep credential material out of committed project/config/context files, load only the selected project's connection and separate reporting from execution authority. Current root-profile merging and local-command-only transport generation do not enforce those boundaries. Separate token files alone do not constrain account reach or isolate agents sharing filesystem access. Next action: include project-selected connection loading and hosted HTTP/OAuth transport where needed in the implementation design; live permissions, renewal and cross-project isolation remain unverified.
- Implementation planning 2026-10-17: user accepted project configuration → local weekly report → one reporting pilot → separately authorized publishing/spend. The current plan now specifies P0–P7 file targets, staged owner inputs and acceptance boundaries; the earlier second-pass plan is archived locally. Fresh reviewer findings were verified against code: `route_workflow.py` hard-codes Marketing ownership and gates stale workstreams; execution schema v1/v2 has no declined/snoozed campaign occurrence contract; observation freshness uses raw input bytes only; current normalization requires one metric/value column rather than standard multi-metric exports. Impact: catalog-only integration, raw-hash reuse and direct export normalization would misroute work, lose task intent or miss corrected metadata. Planned remedies explicitly cover router mode separation, versioned task schema preserving v2 guards, composite import/review identities and versioned wide-to-long presets. Protected project/account enrollment and isolated collectors are assigned to P3 before credential loading. These are reviewed design corrections only; implementation evidence is still pending.
- Plan review 2026-10-17: a fresh subagent required protected execution credentials/policy, an explicit unattended reasoning runtime, a first-channel pilot and separate recurring/restated reports. All four were addressed in the plan and reassessed with no remaining material planning blockers. Evidence: `docs/agent-improvements/2026-10-17-marketing-automation-review.md`. WF-018 remains open until implementation and its acceptance evidence exist.
- Implementation-handoff recheck 2026-10-17: a new fresh-context reviewer confirmed all four implementation-planning flags were resolved in the current plan and found no remaining material blocker to P0/P1/minimum P2. Evidence: the implementation-handoff review and correction recheck in `docs/agent-improvements/2026-10-17-marketing-automation-review.md`. Static review only; no implementation tests or account operations were performed. WF-018 remains open.
- Local implementation 2026-10-17: P0/P1/minimum P2 delivered with exact export presets, metadata/filter-sensitive identities, private preparation, reviewed atomic publication, v3 recurring tasks preserving v2 evidence guards, basic claims checks and Website handoff. Fresh code review reproduced cross-account/campaign scope unions, silently discarded task-ID follow-ups and historical report replacement through the shared publisher. All three were fixed and independently rechecked; 72 affected Marketing/router checks pass and the reviewer independently passed 32 campaign-cycle tests plus alias/traversal/symlink/restoration probes. Additional fixes bind task freshness to config/context/claims and reject undeclared metadata. Evidence: `tests/test_marketing_campaign_cycle.py`, `evals/marketing-local-release.md`, local implementation review under `docs/agent-improvements/`. Structural skill validation, route validation and synthetic two-cycle CLI demo pass. No authenticated access, unattended operation, publishing/spending or improved model/business quality is claimed; full WF-018 remains open. Final `scripts/evaluate.py check` receipt: `evals/local-runs/20261017T160705Z-6f4985ee48ed/result.json` (deterministic PASS).

- Follow-up implementation review 2026-10-18: reproduced five remaining P2 defects: basename-only campaign artifact dispatch rejects existing `sources/review.json`; an older-period correction replaces the newer-period pointer without restatement labeling; a freshly reviewed carried task can retain stale context and remain impossible to accept; campaign finalization drops existing owner prerequisites/materials/destination instructions; and three snoozed tasks hide later due work. Observed causes and reproduction/fix expectations are retained in `evals/marketing-local-review-2026-10-18.md`. Original 72 checks pass; additional shared-publication checks yield 95 passed/1 failed. The failed customer-question publication test passes with only the pre-change dispatcher substituted in memory, isolating a new regression. Workaround: retain the full execution plan, inspect dates and stale tasks manually, and defer affected customer-question publication until corrected. Confidence impact: prior local-release acceptance was too narrow; no live-account impact observed. Closure pending implementation and regression checks; no fixes applied during this review.

- Correction closure 2026-10-18: all five local review defects above were fixed after explicit user instruction. Campaign-only artifact dispatch preserves source reviews; ordered bound history handles out-of-order corrections and pending comparison reconciliation; stale tasks require explicit replacement and renewed acceptance; shared owner rendering preserves existing packets and prioritizes due work. Nine added regression cases bring the distinct targeted checks to 177 passing (175 combined plus two focused follow-ups). Route validation passes; deterministic repository evaluation is PASS at `evals/local-runs/20261018T084645Z-56166f081de2/result.json`. Evidence and exact closure boundaries: `evals/marketing-local-review-2026-10-18.md`. Local defects are closed; WF-018 remains open for the connected-operation capability gap and actual pilot validation.

- Journey/measurement extension 2026-10-24: review of the supplied shared discussion and current primary platform documentation reproduced narrower local gaps: journey reconstruction did not require explicit intervention placements/access, campaign context did not carry the sales/event contract, the website reference blurred Meta browser `eventID` versus server `event_id`, and TikTok was absent from connection definitions/export presets. Observed impact: disconnected research-to-campaign handoffs and ambiguous conversion interpretations; no live-account defect or business outcome is claimed. Added `references/journey-activation-and-measurement.md` and `references/ad-platform-connections.md`, linked six existing skills, expanded context/website handoffs, replaced brittle universal paid-learning anchors with dated checks, and added TikTok campaign-level spend/destination-click reporting. New behavioral prompts are prepared specifications, not evaluated model-quality evidence.
- Verification 2026-10-24: `tests/test_marketing_campaign_cycle.py` passes 47 tests, covering TikTok metric semantics, required measurement metadata, project/account/campaign bounds, publication and pending-context invalidation. An initial new test incorrectly expected an already-published immutable report to be invalidated; corrected it to exercise an unpublished pending packet while preserving historical idempotency. Route validation and the explicit `marketing-connections` route pass; `scripts/evaluate.py check` is deterministic PASS at `evals/local-runs/20261024T102704Z-9ed5b4584425/result.json`. Five affected skill entrypoints pass the generic quick validator; the website entrypoint still triggers its standalone-directory restriction on a pre-existing sibling `image-sourcing.md` link. All selected entrypoint/shared-reference local links resolve. Preserve that existing shared-repo convention; no standalone packaging or cross-host quality claim. `git diff --check` passes.
- Practitioner follow-up 2026-10-24: reviewed public material from the discussion's eight named accounts (Jon Loomer, Savannah Sanchez, Kirk Williams, Harry Dry, Peep Laja, Kieran Flanagan, Aleyda Solis and Avinash Kaushik), plus selected original podcast show notes/transcripts. Account retrieval returned historical, non-chronological samples, not verified current timelines; full paid newsletters and untranscribed videos were not reviewed. Their own articles supplied the substantive evidence. Observed instruction gaps: no explicit review of overlapping agent interventions, attribution-definition changes not called out despite metadata support, paid delivery allocation insufficiently distinguished from creative experiments, and buyer comprehension not operationalized. These are local instruction gaps, not observed live account failures.
- Material adaptations: added intervention history/observation windows and valid zero-task decisions to `references/marketing-campaign-operations.md`; attribution component/definition checks to `references/ad-platform-connections.md`; exposure/allocation checks to `references/comparative-creative-analysis.md`; and an unpaid buyer comprehension/choice diagnostic to the Marketing Strategy workflow. Linked the controls from paid campaign planning. Sources and dates are retained at each changed instruction. Aleyda's [business-value content prioritization](https://www.aleydasolis.com/en/ai-search/content-prioritization-ai-search/), Avinash's [attribution versus incrementality](https://www.kaushik.net/avinash/marketing-analytics-attribution-is-not-incrementality/), and Kieran's [skills guidance](https://www.kieranflanagan.io/p/claude-skills-give-your-ai-assistant) (public preview only) mainly overlap existing outcome/gating/modular-skill rules; no extra framework or bulk skill installation. Selected Paid Search, Perpetual Traffic and Elena Verna/Lenny material did not justify universal channel, volume or spending defaults. No creator performance claims were independently validated.
- Follow-up verification 2026-10-24: both changed skills pass quick validation; route validation and `git diff --check` pass. `scripts/evaluate.py check` is deterministic PASS at `evals/local-runs/20261024T103637Z-a40624593ef5/result.json`. Four additional behavioral prompts cover intervention overlap, attribution-definition drift, uneven creative allocation and buyer comprehension; they are prepared specifications, not executed or independently graded model trials. No claim of measured model or campaign uplift. Review-only controls remain unenforced by a live adapter; preserve WF-018's open connected-operation boundary.
- Remaining boundary: the new guides define review/QA obligations; no executable event-delivery validator, real TikTok export acceptance, live Meta/Google/TikTok authentication, CRM join, scheduled monitor, ad mutation or spend controller was installed or verified. Keep WF-018 open for the selected protected reporting pilot and subsequent separately authorized capabilities.

### WF-017 — Persisted test payments need explicit mode isolation

- First/last observed: 2026-10-17. Owner: Italy website payment maintainer. Scope/status: resolved for the local implementation; no live activation occurred.
- Observed: independent review found that a stored `paid` order could short-circuit checkout/status/retry after a switch from test to live configuration because the original draft order had no mode field. Impact: a test payment could appear serviceable under live configuration; no real charge or customer incident was observed.
- Reproduction/evidence: synthetic paid test order followed by a live-mode service using the same PostgreSQL record. `projects/us-retirees-italy/web-site/scripts/tests/review-payments.test.ts` now requires all three access paths to reject it; UI test checks no-charge/no-call test wording.
- Fix: persist `livemode`, verify it before paid-state shortcuts, label test confirmations, filter operator servicing to live paid orders, and retain mode checks on signed events. Independent follow-up review found no remaining HIGH/MEDIUM blockers within its bounded scope.
- Closure: 11 PostgreSQL-backed payment checks and all 134 local browser tests passed; build/typecheck/lint passed. Evidence: website `qa/stripe-payment-2026-10-17/report.json`. Browser fixtures do not establish Stripe account acceptance or webhook delivery. Production database TLS configuration, Stripe test-key/webhook setup and owner-authorized live activation remain separate prerequisites.

### WF-016 — External-link maintenance and broader privacy design gaps

- First/last observed: 2026-10-17. Owner: website skill maintainer. Priority: P2.
- Observed: maintenance requested an owner/cadence but provided no outbound discovery/check procedure; launch criteria treated all external 4xx as broken. Consent guidance prescribed banner controls without first establishing whether consent-requiring technology existed, and lacked a broader form/data-lifecycle design reference.
- Impact: incomplete maintenance handoff, bot-block false positives, unnecessary consent interfaces and policy-only privacy review. These are instruction gaps; no production incident is inferred.
- Change/evidence: website `references/external-link-maintenance.md`, `references/privacy-design.md`, revised consent/launch/testing guidance and quality-review entrypoint; `scripts/brand/discover_external_links.py` with synthetic regressions. Dated research documents retain source provenance.
- Closure 2026-10-17: 9 synthetic discovery regressions pass; both edited skills structurally validate (existing reviewer description warning); repository evaluation `20261017T110133Z-36f4683df7d8` PASS. Research in `evals/website-maintenance/` records official-source retrieval and Firecrawl-credit/EUR-Lex-access limitations with successful regulator-source fallback. Live checker/scheduler operation, agent behavior across hosts and application-specific legal compliance remain unverified; this closes the reusable instruction/tooling gap only.
- Application follow-up 2026-10-17: Italy website now has route/rendered discovery plus conditional consulate-source coverage, pinned Lychee setup, reports and a disabled-by-default scheduled job. Initial Lychee connection resets on five public destinations were independently confirmed as HTTP 200 with curl; one delayed independent client confirmation is now limited to connection errors, retaining both observations and never retrying 403/429 or disabling TLS. Evidence: `projects/us-retirees-italy/web-site/qa/external-link-baseline/2026-10-17/`; all 32 routes and 15 outbound destinations checked, six offline decisions tests/build/lint/typecheck pass. Scheduled execution and notifications remain unverified; eight source-content reviews are due. This adds live transport evidence for that website, not general legal/content or scheduler assurance.
- Authorized activation 2026-10-17: enabled `EXTERNAL_LINK_MONITOR_ENABLED=true` in the website GitHub repository. Manual GitHub run `39029493664` passed; downloaded artifact confirms 32 pages, 15 external links, zero transport issues, eight editorial reviews due. Evidence: website `qa/activation-2026-10-17/receipt.json`. The future calendar-triggered run and notification delivery remain unobserved. Railway schema setup in the same receipt required authenticated Railway SSH because external verified TLS returned `SELF_SIGNED_CERT_IN_CHAIN`; use `psql -P pager=off` in headless SSH to avoid the terminal pager stalling readback. No certificate-verification bypass was used. Schema commit, synthetic insert/rollback and fresh readback passed; website-to-database/Brevo delivery remains separate.
- Owner correction 2026-10-17: link QA must automatically deliver CI, rather than leaving workflow creation/activation as an optional owner task. Updated skill entrypoint and link/maintenance/testing/launch references to require runnable weekly/manual GitHub Actions (or existing-provider equivalent), no default extra opt-in switch, artifact retention and initial-run verification under existing publication authorization. Explicit user opt-outs and remote-access gaps remain visible. Skill structural validation and repository evaluation `20261017T115706Z-8bddb8340d62` PASS; these are instruction/contract checks, not a new live agent-quality evaluation.

### WF-001 — Inert template anchor completes placement

- First/last observed: 2026-10-11. Owner: Marketing evidence maintainer.
- Observed: `scope_complete=True` for a link inside `<template>`; Chromium found zero live anchors. Impact: false completed backlink.
- Expected/change: ignore template descendants, including nested templates and base elements, while retaining real anchors.
- Evidence: `tests/test_seo_review_fixes.py::test_inert_templates_cannot_complete_and_cannot_override_base`; `scripts/marketing/link_observations.py`.
- Next action/closure: resolved 2026-10-11; inert/nested/self-closing template regression and Marketing publication tests pass. This establishes parser behavior, not live SEO impact.

### WF-002 — Sensitive URLs retained after rejection

- First/last observed: 2026-10-11. Owner: Public-capture maintainer.
- Observed: a synthetic `?token=` value remained in failure observation source/final URLs despite fetch rejection. Impact: secrets could be written to disk.
- Expected/change: reject source and target before creating a record or output directory; sanitized CLI error.
- Evidence: `tests/test_seo_review_fixes.py::test_sensitive_url_is_rejected_without_artifacts_or_diagnostics`; `scripts/marketing/verify_links.py`.
- Next action/closure: resolved 2026-10-11; both source/target CLI regressions pass, with no output directory or synthetic secret in diagnostics.

### WF-003 — Aborted audit reports resolved defects

- First/last observed: 2026-10-11. Owner: Website audit maintainer.
- Observed: browser-launch failure with no measured pages marked a prior canonical defect resolved. Impact: false technical improvement report.
- Expected/change: record complete audit coverage and compared routes; incomplete/legacy coverage is non-comparable.
- Evidence: `tests/test_seo_review_fixes.py::test_failed_or_unknown_audit_coverage_cannot_resolve_defects`; `scripts/brand/compare_seo_audits.py`.
- Next action/closure: resolved 2026-10-11; comparison regressions and Chromium audit tests pass. Unknown/aborted coverage remains non-comparable.

### WF-004 — Opportunity provenance not validated on resume

- First/last observed: 2026-10-11. Owner: Marketing publication maintainer.
- Observed: source replacement kept workstream `valid_for_use=True`, while the opportunity validator rejected its digest. Impact: stale qualification can appear current.
- Expected/change: shared artifact validation covers singular/plural opportunity records at publication, source-only updates and resume.
- Evidence: `tests/test_seo_review_fixes.py::test_opportunity_provenance_checked_on_publication_source_change_and_resume`; `scripts/subprojects.py`.
- Next action/closure: resolved 2026-10-11; source-update rejection, unchanged manifest revision, stale resume detection and exact source restoration pass.

### WF-005 — Header trickling exceeds fetch deadline

- First/last observed: 2026-10-11. Owner: Public-fetch maintainer.
- Observed: a 0.1-second fixture took 0.322 seconds because each arriving header reset the inactivity timeout. Impact: untrusted endpoints can stall work beyond the declared deadline.
- Expected/change: every underlying header/body read uses remaining total transport time. OS DNS resolution remains an explicitly separate limitation.
- Evidence: `tests/test_seo_review_fixes.py::test_trickled_headers_obey_total_deadline`; `scripts/marketing/public_fetch.py`.
- Next action/closure: resolved 2026-10-11; trickled-header deadline and normal/redirected HTTP capture tests pass. OS resolver timeout remains a limitation.

### WF-006 — Original evidence restoration rejected

- First/last observed: 2026-10-11. Owner: Marketing publication maintainer.
- Observed: replacing corrupted bytes with the original digest-matching capture was rejected as an immutable rewrite; damaged observation failed before staged bytes were considered. Impact: normal transaction cannot recover valid historical evidence.
- Expected/change: compare staged restoration to historical digests, not damaged disk bytes; continue rejecting rewritten history.
- Evidence: `tests/test_seo_review_fixes.py::test_restore_original_evidence_without_rewriting_history`; `scripts/subprojects.py`.
- Next action/closure: resolved 2026-10-11; all four missing/corrupted capture/observation cases restore transactionally; alternate historical bytes are rejected.

### WF-007 — Competitor-query warning test failure

- First/last observed: 2026-10-11 during implementation validation. Owner: Research collector maintainer.
- Observed: `tests/test_research_query_expansion.py::test_competitor_plan_preserves_input_and_does_not_inject_english` expected warnings but received an empty list. Latest broad rerun after the review fixes: 1146 passed, 1 failed (2026-10-11). Cause not yet assessed; unrelated to SEO changes.
- Impact/next action: full validation is not green; reproduce on current code and reconcile intended locale/query behavior with the assertion. Do not remove the assertion merely to pass.
- Evidence: `docs/agent-improvements/2026-10-11-seo-and-earned-media-implementation.md`. Closure: pending.
- Recurrence 2026-10-11, shared-post agent review: unrestricted setup rerun produced 1147 passed, 1 failed, the same competitor-query warning assertion. Sandbox-only subprocess/browser/network failures cleared outside the sandbox. Evidence: `docs/agent-improvements/2026-10-11-shared-posts-review.md`. No fix attempted in this review.

- Closure 2026-10-21: cause verified — `COMPETITOR_TERMS['ja']` was added to `scripts/evidence_scout/discover_competitors.py`, so the test's Japanese fixture stopped being an unsupported language; the code was correct. Test now uses Korean (still unsupported) with both original assertions kept, plus a new test pinning Japanese vocabulary without English injection. `tests/test_research_query_expansion.py` 67 passed.

### WF-008 — Existing skill entry line budgets

- First/last observed: 2026-10-11 during setup validation. Owner: Skill maintenance.
- Observed: evidence-scout 32 lines, idea-grill 31, market-problem-discovery 31 versus the 30-line entry budget. Reconfirmed by setup validation after the review fixes on 2026-10-11.
- Impact/next action: setup validation fails; compact or move detail to direct references without losing required guidance, then rerun the entry checks.
- Evidence: `docs/agent-improvements/2026-10-11-seo-and-earned-media-implementation.md`. Closure: pending.
- Recurrence 2026-10-11, shared-post agent review: setup again detected evidence-scout 32 lines, idea-grill 31 and market-problem-discovery 31 against the 30-line budget. Evidence: `docs/agent-improvements/2026-10-11-shared-posts-review.md`. No skill changes made.

- Closure 2026-10-21: removed redundant blank lines (no guidance cut) so idea-grill, evidence-scout, market-problem-discovery and stripe-best-practices are at 30 lines; `scripts/validate_setup.sh` reports 0 errors.

### WF-009 — Independent review provider produced no findings

- First/last observed: 2026-10-11. Owner: Review tooling maintainer.
- Observed: review-with selected DeepSeek; sandbox and unrestricted attempts produced only an unrecognized-model diagnostic and no usable review before being stopped. Root cause unknown.
- Impact/next action: independent review evidence unavailable; reproduce provider/model resolution with sanitized diagnostics, then verify a bounded read-only review completes. Local inspection/reproductions must remain separately attributed.
- Evidence: the implementation review in this conversation; transient provider outputs under `.agent-review/deepseek/`. Closure: pending; no successful provider review is claimed.

- WF-009 recurrence 2026-10-12: review-with auto retry produced no usable external-provider result and was stopped. Sanitized result: `projects/us-retirees-italy/web-site/.agent-review/auto/20261012-085709-result.md`. Independent agent fallback reviewed the plan and implementation; a newsletter state inconsistency was corrected. Provider completion/identity remains open.

### WF-010 — Non-video correction and evidence contract gaps

- Priority/status: P1/resolved. First/last observed: 2026-10-11. Owner: shared packet/Marketing/website maintainers.
- Observed: independent local reviewer reproduced exhausted rejected work becoming eligible by resetting state to pending, preservation silently skipped on redirect routes, and oversized-count ratio overflow. Cross-provider review found briefs could consume questions from a different reviewed audience.
- Impact: bounded corrections and evidence applicability could be bypassed; page audit could omit declared value checks.
- Fix/closure: exhausted pending/rejected units remain blocked, redirect preservation is rejected, overflow stays undefined, brief audience matches reviewed question segment. Synthetic regressions in `tests/test_source_work_packets.py`, `tests/test_website_browser_audit.py`, `tests/test_creative_evidence.py`, `tests/test_customer_questions.py`. Deterministic behavior only, not live research quality. Receipt: `docs/agent-improvements/2026-10-11-non-video-implementation-receipt.md`.

### WF-011 — Live workflow evaluation authentication failure

- Priority/status: P3/open. First/last observed: 2026-10-11. Owner: local Claude runtime maintainer.
- Observed: five development current-arm trials exited before inference with expired OAuth session that could not refresh; zero output tokens. No quality score produced. Cause: reported authentication failure; no provider diagnosis attempted.
- Impact/next action: authenticate the selected runtime and rerun both arms, then inspect outputs/traces; keep held-out work separate and run operator usability independently.
- Evidence: `evals/non-video/README.md`, implementation receipt. Closure pending successful inference and output review.

### WF-012 — Equivalent root canonical URLs produce a false failure

- Priority/status: P2/resolved. First observed: 2026-10-11; closure: 2026-10-12. Owner: Website audit maintainer.
- Observed/reproduction: Italy local production HTML declares `https://italyforretirees.com`; Chromium resolves the link href to `https://italyforretirees.com/`. Explicit expectations using either spelling fail the canonical check. Evidence: `projects/us-retirees-italy/web-site/qa/website-review-2026-10-11/seo-audit.json` and `seo-routes.json`.
- Cause: confirmed raw string comparison in `scripts/brand/seo_checks.py` compares expected, HTML and DOM canonicals without normalizing an empty origin path.
- Impact/expected: a correct root canonical is reported as a site defect. Treat these two root spellings as equivalent while preserving meaningful path/query differences.
- Fix/closure: normalize only an empty origin path to `/` in expected/HTTP/DOM/sitemap comparisons. Four focused regressions pass, including real path/query mismatch rejection (`tests/test_seo_root_canonical.py`); the complete 31-route local browser SEO audit has no errors (`projects/us-retirees-italy/web-site/qa/website-fixes-2026-10-12/seo-audit.json`). This closes the comparator defect only, not production SEO/launch readiness.

## Latest verification receipt

- WF-007/WF-008 recurrence 2026-10-11 non-video implementation: unrestricted setup reported 1171 passed/1 failed, plus the same three line budgets; no unrelated fixes. Receipt below.
- WF-009 follow-up 2026-10-11: review-with DeepSeek returned a usable read-only review with concrete findings, despite an unrecognized-model diagnostic. Findings assessed and audience gap corrected; exact served model identity remains unverified. Do not equate this review with workflow-quality evaluation.



2026-10-11: `tests/test_seo_review_fixes.py` and `tests/test_verify_links.py`: 22 passed. Final browser/coverage and review regressions: 28 passed; the final unmeasured-coverage comparison check: 10 passed. Full Python suite: 1146 passed, the known WF-007 test failed. Setup also reconfirmed WF-008. These checks establish deterministic behavior and local browser/HTTP handling; they do not establish live agent quality or SEO uplift. Detailed transient log: `/tmp/seo-review-fix-validation.log`.

## New entry template

### WF-NNN — Short symptom

- Priority/status: P1/P2/P3; open/in_progress/blocked/deferred/resolved. Add/update the queue row too.
- First/last observed: YYYY-MM-DD. Owner: component or role.
- Observed behavior and reproduction/evidence: sanitized repository-relative links; identify synthetic, live or unverified evidence.
- Expected behavior and impact: affected workflow and consequence.
- Cause: confirmed facts versus hypothesis.
- Next action: bounded improvement; dependency or resume condition if blocked/deferred.
- Resolution/history: dated change, command/result or evaluation receipt, remaining limits. Preserve past incidents.

### WF-013 — Repository-local evaluation ownership

- Priority/status: P2/resolved for local entrypoint and result-contract implementation; live quality remains WF-011.
- First/last observed: 2026-10-13. Owner: Agent evaluation maintainer.
- Observation/impact: local evaluation tools existed without one independently runnable check/trial/review/report path; central broker runs were not full domain quality evaluation.
- Change: scripts/evaluate.py delegates existing checks, records local immutable results and bounded selected-skill native trials, supports blind independent review, and exports summaries only by explicit request. No central runtime dependency.
- Verification/evidence: evals/test_local_evaluation.py (32 tests), real Bubblewrap network/key/home exclusion probes, and evals/local-implementation-report.md. Native pilot hit expired OAuth before inference; no quality improvement or baseline acceptance is claimed.
- WF-011 recurrence 2026-10-13: bounded native pilot returned “OAuth session expired and could not be refreshed”; append-only classification records INFRASTRUCTURE_ERROR. Existing authentication blocker remains open. After reauthentication, obtain observed native responses and independent grades; do not rotate credentials or silently substitute a paid provider.

### WF-014 — Imported application skills need context and routing adaptation

- Priority/status: P2/resolved for structural integration; live behavior unverified. First/last observed: 2026-10-17. Owner: Skill maintenance.
- Observed/reproduction: seven copied skill folders included insurance-specific paths, providers, release defaults and missing dependencies. None had catalog/routes entries; the lightweight local evaluation PASS alone did not establish route parity.
- Cause/impact: confirmed raw folder copy carried source-application assumptions and bypassed explicit catalog registration, risking wrong dispatch and invalid execution paths.
- Resolution: removed overlapping/domain-bound add-flow, add-brand and frontend-design copies; generalized four retained helpers, registered explicit routes and website ownership, removed stale version defaults and unused examples/adapters. See `config/skill-catalog.json`, `config/workflow-routes.json`, `references/modules/website.md`.
- Closure evidence: `python3 scripts/validate_skill_routes.py` passes; all four skill-creator quick validations pass; `python3 scripts/evaluate.py check` passes. These are deterministic checks, not live task-quality or production-payment evidence.
- Next action: use selected-application context during real tasks; retain native trial and independent grading before claiming model-quality improvement.

### WF-015 — Passing website contracts miss semantic and fallback defects

- Priority/status: P2/resolved for the three local implementation defects. First/last observed: 2026-10-17. Owner: Italy website maintainer.
- Observed: 100 existing browser tests pass against the existing local build while a remote-work selection still produces an ERV income headline; comparison-page promises exceed the narrower call/recap framing. Synthetic module execution also shows an invalid successful FX response overwrites last-good cache and makes the next load reject.
- Reproduction/evidence: `projects/us-retirees-italy/web-site/qa/implementation-review-2026-10-17/findings.json`; implementation in `app/check/checker.tsx`, `app/check/fx.ts`, and `app/compare/page.tsx` within that website. No real customer data used.
- Observed cause: checker evaluation omits selected activity, FX persistence precedes validation, and existing price/route assertions do not compare deliverable scope. Frequency of malformed provider responses is unknown.
- Impact: green browser contracts do not establish correct route interpretation, robust last-good fallback, or consistent purchase expectations.
- Fix: label other plans' results and email summaries as ERV income-only comparisons; label ERV documents/processing explicitly. Validate rate values and calendar dates before caching, reject invalid cache entries, and preserve last-good/built-in fallback. Align the comparison CTA with the $49 call/recap and separately priced full plan.
- Closure evidence 2026-10-17: lint, TypeScript and fresh build pass; 115 local Chromium tests pass, including 15 new regressions in `projects/us-retirees-italy/web-site/tests/review-fixes.spec.ts`. Source hashes and checks are recorded in the findings JSON. Historical screenshots generated by tests were restored.
- Remaining boundary: manual booking and paid-test scope preserved. This closes local implementation defects only; production verification, actual provider failure frequency and existing launch requirements remain unestablished.
