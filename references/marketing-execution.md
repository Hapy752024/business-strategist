# Marketing execution plan

Use `scripts/marketing/execution.py` with the optional `marketing/execution-plan.json` artifact bound in `workstream.json`. The helper validates and renders `execution-plan.md` and `owner-actions.md`; publish artifact changes with `publish_marketing_workstream()` so artifact and hash binding advance together. Do not create this artifact for a narrow copy edit.

## Ownership and completion

Turn a selected objective into small sequential actions owned by an `agent`, `owner`, or `third_party`. Reuse existing user instructions and delegated authority for in-scope agent work; `commitment_state` is a resume record, not another approval checkpoint. For an external action, `accepted` records the decision to pursue it; it does not mean a publisher approved it.

Set `required_for_scope` for each action. Optional ideas do not block the selected deliverable. Required actions remain incomplete until their own criterion is evidenced, or an authorized scope change removes them. A user's send/post/account step can finish while a publisher review or placement remains pending. Keep `commitment_state` separate from `execution_status`; a proposal never becomes accepted on resume. Recheck hashes when prepared materials change and invalidate only affected verification. Never infer permission for a new send, payment, account connection, or publication from an unrelated prior task.

Each owner or third-party packet should contain the exact destination, current eligibility/rules, audience fit, ready text/assets, precise user step, fee, authorization basis, follow-up, and observable completion criterion. Research candidate targets and prepare the materials before handing work to the owner. Ask only for identity, private account access, first-hand facts, or a material business choice the agent cannot supply. Preserve unrelated accepted actions and existing authorization on update.

For backlinks, verify the live source page, destination, redirects and anchor attributes after publication. A submitted pitch, directory form, favorable reply, or response header is not a verified placement. Record publisher rejection and an evidence-based alternative. Do not buy links, fabricate reviews, or claim ranking/uplift without observations.

## Measurement handoff

Use `scripts/marketing/observations.py` for supplied local aggregate CSV/JSON exports. Explicitly map the fields and preserve property, source, window, timezone, metric/unit, availability, export date, optional denominator and input digest. Never use lead names, emails, IDs or free-text bodies in the normalized view. Unknown and suppressed values stay distinct from zero. `compare()` requires matching property, source, metric, dimensions, timezone and equal window duration; observed changes do not prove causality. `decision_record()` binds baseline and follow-up digests to an action, expected effect, applied change date, confounders, limitations and next decision. A changed export makes the prior record stale. See the synthetic, non-production example in `fixtures/marketing/demo-baseline.csv`, `demo-followup.csv`, and `demo-decision.json`; the matched change is not a business result. With no export or account access, give the owner the exact setup/export steps and continue independent work.

## Example action template

```json
{
  "id": "directory-review",
  "objective": "Submit a relevant, eligible business listing",
  "evidence": ["verified directory audience overlaps the target buyer"],
  "actor": "owner",
  "dependencies": [],
  "prepared_materials": [],
  "destination": "exact listing URL",
  "eligibility_checked_at": "YYYY-MM-DD",
  "audience_fit": "reason supported by evidence",
  "user_step": "sign in, review prepared copy, submit",
  "fee": null,
  "authorization_basis": "selected listing task",
  "follow_up": "check listing status after stated review period",
  "next_step": "submit prepared listing",
  "completion_criterion": "public listing page resolves and matches submitted destination",
  "commitment_state": "accepted",
  "execution_status": "awaiting_owner",
  "required_for_scope": false,
  "verification": null,
  "result": null,
  "outcome_review": null
}
```

## Version 2 placement evidence

New earned-media actions use `schema_version: 2`, `action_kind` and `intended_result`. Kinds distinguish generic work, prepare_packet, submit_listing, send_pitch and verify_placement. A verified placement requires source_url, target_url and an `observation: {path, sha256}` binding. The observation contains a capture binding, actual anchors/rel attributes, method, URLs, redirects and checked_at. Both paths are relative to the Marketing root. `scripts/marketing/link_observations.py` re-parses the retained HTML/DOM and checks the exact source/target and digests; a positive reply or authored verification string cannot complete this action. Publication validates staged bytes before commit and persisted bytes on resume. A rootless structural check cannot certify placement completion.

Version-1 plans remain readable and render legacy verification explicitly. They are not automatically converted to verified backlinks. Preparation and submission can finish separately from a required public placement. Optional proposed opportunities do not block the selected scope.

External-delivery authorization in v2 binds recipient, destination, action kind, intended result, materials and authorization basis with `authorization_digest`. Generate it with `authorization_digest(action)` only when actual authorization is established; a digest is a consistency record, not proof the user gave consent. Changing those fields invalidates the prepared delivery. Changing expected placement source/target invalidates its observation; rewriting unrelated pitch materials preserves historical placement evidence. No pitch or listing sender is implemented; the only external marketing write path is the approval-bound executor below.

## Executing approved actions

`scripts/marketing/execute.py` is the only code path for an external marketing write: schedule a Postiz post (`schedule_post`), create a Meta campaign (`create_campaign`, always `PAUSED`, positive `spend_cap` required), send a Resend broadcast (`send_broadcast`, defaults to a test email to the approval's `founder_email`; a full audience send needs `test_send: false`), or create a PostHog draft experiment (`create_experiment`, no `start_date`). The `meta-ads` and `postiz` MCP servers are for reading only: their write tools are in `permissions.deny` (see `ad-platform-connections.md`). The action file carries `id`, `action_kind` and the exact `provider_request`; `authorization_digest` binds `provider_request`, so any change after approval invalidates it.

Approvals are SSH signatures from the founder; the agent can prepare a request and read the public key but cannot sign.

0. One-time founder setup in their own terminal: create a DEDICATED, passphrase-protected key (`ssh-keygen -t ed25519 -f ~/.ssh/marketing_approval`), never add it to ssh-agent, keep it out of the repo, and add `<principal> namespaces="marketing-approval" <public key>` to `~/.config/business-strategist/allowed_signers` under the real home directory (fixed path, no environment override). The agent runs as your OS user, so it could edit any file you own: the signers file and its directory must be root-owned and not group/world-writable (`sudo chown root:root` on both, `sudo chmod 0644` the file, `sudo chmod 0755` the directory; `sudo chattr +i` on the file is optional extra protection). A user-owned file is refused even when read-only. Execution is refused when the file is missing (with these steps), when the file, its resolved path or either parent directory is not owned by root or is group/world-writable, or when the file or its directory is a symlink into the repo or a temp directory. Verification uses only a root-owned `/usr/bin/ssh-keygen` or `/bin/ssh-keygen`, never `$PATH`.
1. `python3 scripts/marketing/execute.py approval-request <action.json> --by <principal> --marketing-root <marketing dir> [--founder-email <own address>] [--valid-days N]` validates the action, shows it in plain language and writes the exact message `digest|scope|granted_at|valid_until|action_id|granted_by|marketing_root|founder_email` (validity 7 days by default, at most 14, chosen before signing and not extendable afterwards) plus the `ssh-keygen -Y sign -n marketing-approval` command. An agent may run this step.
2. The founder signs that file in their own terminal, then `execute.py attach-signature <action.json> <message>.sig` verifies it and writes `<action>.approval.json`.
3. `python3 scripts/marketing/execute.py run <action.json> --approval <approval.json> --marketing-root <marketing dir>` re-verifies the signature (`ssh-keygen -Y verify`) and prints exactly what would be sent (dry run, no network). `--execute` performs the send and verifies the signature again.

Agents must never sign approvals, edit approval files, receipts or the allowed_signers file, or name themselves as the principal. Residual risk: the agent runs as your OS user. Only the required root-owned signers file plus a passphrase-protected approval key kept out of ssh-agent and outside the repository separates the founder from the agent. Project permission rules deny the obvious command and file paths, but they match command text only. Deleting receipts weakens repeat-send protection; it does not enable an unapproved send.

Execution refuses unless the digest matches, `granted_by` is a human (agent/tool identities are rejected), the current time is before the signed `valid_until` (window at most 14 days), `scope` equals `action_kind`, the approval names this action id and marketing root, and no prior executed, failed or uncertain attempt or unfinished claim exists for that action id. Each attempt writes `receipts/<action-id>-<timestamp>.json` with outcome, digest and provider ids, never credentials. An `uncertain` outcome (network failure mid-request) blocks retries: check the provider account and use a new action id and approval. Activating a paused campaign or launching an experiment remains a manual founder step. Credentials come from the environment (`POSTIZ_BASE_URL`, `POSTIZ_API_KEY`, `META_ACCESS_TOKEN`, `RESEND_API_KEY`, `POSTHOG_HOST`, `POSTHOG_PERSONAL_API_KEY`, `POSTHOG_PROJECT_ID`).

For page planning use `scripts/marketing/keyword_map.py` and the optional `public_resource` section of content briefs. Preserve source bindings, original-versus-compiled contribution, public-use suitability and maintenance responsibility. The publisher validates keyword maps and `content-brief.json` resource evidence within the same transaction. Imported resources use the `public_resource` purpose and explicit applicability review.

Known placements use `verify_links.py`; capture directories are immutable and may be nested using `--evidence-root`. Public fetching validates and pins DNS addresses and every redirect, with bounded responses. Untrusted browser fallback is disabled. Failure/access blocks stay unknown; a 200 response without the expected anchor is absent, and a provider snapshot is a separate observation.

Opportunity artifacts use `opportunity.json` or `opportunities.json` (optionally nested under earned-media). Publication and resume revalidate their source bindings alongside maps and resource briefs, including source-only updates. Restore missing or corrupted placement evidence by staging the original digest-matching bytes; alternate contents still require a new observation/capture path. Template descendants are inert and cannot establish a placement. Sensitive source/target URLs are rejected before any observation is created.

For question-led content and creative comparison, apply [question tracking](customer-question-tracking.md) and [creative analysis](comparative-creative-analysis.md). Publish optional `customer-questions.json` and `creative-evidence.json` with bound captures through Marketing; source-only changes/resume revalidate use. These artifacts neither establish demand nor authorize posting.

## Owner-action contract

Use when a deliverable surfaces work only the owner can do or decide. Apply with references/task-scope.md: include only decisions and actions relevant to the requested deliverable; never append recurring programs to narrow copy or execution work.

States: `proposed` (agent suggestion, not adopted), `accepted` (owner agreed), `deferred` (explicitly postponed), `completed`. Only `accepted` actions and genuine blockers persist; a `proposed` action never recurs on resume as if adopted.

Persistence: resolve the active track's manifest (website work uses its website-manifest.json, Branding its brand manifest, Business its current case/research manifest); do not overwrite the umbrella or unrelated next steps. Accepted actions are losslessly encoded as one `Owner action: {JSON}` line each in the existing `next_action` string. Each object contains `id`, `state: accepted`, `action`, `reason_owner`, `cadence`, `effort`, `review_at`, `completion`, `outcome`, `stop_rule`, and `details` (relative path/anchor to the human row). Stable IDs permit updates without duplication. All fields are nonempty strings. Keep unrelated text and owner rows byte-for-byte where possible. `scripts/monitoring/owner_actions.py` provides `update_action` and `accepted_actions` without writing files or granting acceptance; stage its returned manifest through the active owner's normal publication flow. Advance manifest revision/timestamp with that publication.

Render full rows in the active track's owner-actions.md. Proposed, deferred and completed rows can remain there as history, but are not active commitments. Acceptance of a human-owned action must come from the user or existing explicit authorization; agent-owned work inside the user's selected scope does not need another acceptance. Transition to completed/deferred removes only that ID from the active manifest; record the result/reason in its human row. Never silently replace accepted work with a new proposal. For recurring work record the next review/due point, customer outcome and stop/change rule; completing one occurrence does not authorize a new cadence.

On resume read the active manifest, parse accepted rows and open their detail links; reconcile state before recommending action. Do not resurrect completed/deferred/proposed rows from the rendering. Legacy free-text tasks stay intact until their acceptance and details are established. Reserve `open_blockers` for actual dependencies and preserve unrelated blockers. Optional accepted work is never a blocker merely because it is accepted.

Each row: stable ID, action, layer/area, why only the owner can supply it, cadence, rough effort, needed-by/review point, expected customer outcome/evidence payoff, definition of completion, stop/change rule, state. Cadence remains proposed until accepted.

Owner-only vs agent-verifiable: ask the owner only for unavailable firsthand facts, changed commercial commitments (prices, policies, guarantees) and actual decisions (publishes, sends, platform applications, spend). Facts verifiable against current authoritative sources or an approved source record are rechecked by the agent without asking.

Preserve publication/send authorization already granted in the session; do not re-ask. Identity-gated approvals (merchant programs, business-profile verification) are always owner actions.

Example rows (illustrative, not defaults):
- Publish one founder post per week from the listening-driven topic queue | SMO→GEO corroboration | weekly | 1h | earned-mention growth | proposed
- Provide real return-window terms for policy markup | DEO trust inputs | one-off | 15min | accurate Offer/Policy encoding | accepted
- Fact-check 12 drafted answer capsules on /pricing and /compare | AEO accuracy | one-off | 45min | safe publication | proposed

## Local campaign operations

This is the P0/P1/minimum-P2 release. Shared code operates on explicit projects and campaigns; each Marketing root owns its connection definitions, context, reports and execution plan. Actual account connections, protected collectors, scheduled reasoning, publishing and spending are subsequent releases.

### Select and set up

For campaign design and tracking, apply [journey activation and measurement](journey-activation-and-measurement.md). Record hooks, sales paths, event mappings and QA in the existing campaign context. For asset inventory, provider onboarding and monitoring, apply [ad platform connections](ad-platform-connections.md). These are planning/implementation requirements; the local report validator does not certify event delivery or launch readiness. Descriptive imports remain available with measurement gaps disclosed.

Resolve `projects/<slug>` through its manifest; use its registered Marketing path. Existing legacy paths are preserved. Start Marketing through `scripts/subprojects.py` only when the user selected that project and supplied its brief. No Business research is started by an export import.

```bash
python3 scripts/marketing/campaign.py setup --project <slug> --campaign <id> \
  --objective '<commercial outcome>' --audience '<selected audience>' --offer '<confirmed offer>' \
  --property '<account or property ID>' --timezone '<IANA timezone>' \
  --report-scope '<confirmed export filters and scope>'
```

For advertising exports also confirm `--currency`, `--attribution` and `--maturity`. The command writes campaign configuration, supplied context and an empty claims registry through Marketing publication. Unknown facts remain missing. Configuration does not authorize external activity. To define connections, supply `--connections <secret-free.json>` and one or more `--connection <id>`; their schema is `schemas/marketing-connections.schema.json`. Credential references have the form `<project-slug>/<connection-name>`. Only the selected project's references are valid; this release never resolves them.

Default runtime packets live under ignored `.marketing-runtime/<project>/<campaign>/` with private file permissions. They contain sanitized aggregate data, not raw uploads or tokens. Keep raw exports in an access-controlled inbox; delete them when the user-selected retention period ends. Same-user permissions are not a secret-isolation boundary. Future connected operation requires protected enrollment, an isolated collector identity and scope enforcement before real credentials load.

### Export presets

Presets declare exact supported English CSV layouts, not every provider export variant. Dates, timezone, property, report filters/scope and export date must be confirmed. These are export instructions checked against synthetic examples; real-account export compatibility remains unverified. Use an equivalent custom-column aggregate report when a standard export differs. A named column error requires the appropriate export or a reviewed new preset; never silently rename ambiguous metrics.

| Preset | Export scope and required columns | Optional metrics and limits |
|---|---|---|
| `gsc-pages-v1` | Search Console Performance → Search results → Pages → Export CSV; use the Pages table: `Top pages,Clicks,Impressions,CTR,Position` | CTR is recomputed; position is weighted by impressions. Confirm report filters and full date range. |
| `gsc-queries-v1` | Search Console Performance → Search results → Queries → Export CSV: `Top queries,Clicks,Impressions,CTR,Position` | Query text is kept verbatim (no URL stripping); same limits as `gsc-pages-v1`. Used by `search_feedback.py`. |
| `ga4-pages-v1` | Pages and screens aggregate CSV with `Page path and screen class,Views,Active users,Event count,Key events` | Comment preambles are supported. Users across page rows are not additive. Confirm reporting identity/settings as applicable. |
| `ga4-events-v1` | GA4 Events report (event name by count, no breakdowns): `Event name,Event count` | Used only by `verify_tracking.py`; event names are kept verbatim. Required properties cannot be confirmed from it. |
| `posthog-events-v1` | PostHog events table exported as `Event name,Event count` | Same limits as `ga4-events-v1`. |
| `google-ads-campaigns-v1` | Campaigns aggregate report with `Campaign,Campaign ID,Cost,Clicks,Impressions` | `Conversions` is optional and otherwise unknown. Confirm conversion definition, attribution, currency and maturity. |
| `meta-ads-campaigns-v1` | Ads Manager campaign-level report with `Campaign name,Campaign ID,Amount spent (<confirmed currency>),Impressions` | `Link clicks`, `Website leads` optional. Ambiguous `Results` is not treated as leads. Row reporting dates, when supplied, must match confirmed dates. |
| `tiktok-ads-campaigns-v1` | Exact English custom-column campaign aggregate with `Campaign name,Campaign ID,Cost,Impressions,Clicks (destination)` | Spend and destination-click CTR only; `Results` and generic `Conversions` are deliberately not interpreted. Qualification/conversion reporting requires a separately reviewed event-specific mapping. Fixture-tested layout; actual account export compatibility remains unverified. |

Exclude breakdowns, customer rows and duplicated totals. Query strings are stripped from page dimensions; apparent email/token dimensions are rejected. The importer supports UTF-8/BOM, English thousands separators and known blank/suppressed cells. Other locales, negative amounts, oversized files, non-finite values and unknown layouts produce explicit errors. This does not certify absence of all personal data; inspect source scope before import.

### Verify tracking before launch

After the site gate and before any spend, keep a tracking plan (`schemas/tracking-plan.schema.json`: events, trigger, required properties, consent category, destinations, owner, `required_for_launch`) and run `python3 scripts/marketing/verify_tracking.py <plan.json> --source ga4|posthog`. It compares the plan with event names seen in the last 7 days. Without a connection it reports `unconnected` with owner steps and makes no network call; with an aggregate export use `--export events.csv --meta property=... --meta period_start=... --meta period_end=... --meta timezone=... --meta exported_at=...` (presets `ga4-events-v1`, `posthog-events-v1`). Verdict `ready` needs every launch-required event observed with its required properties confirmed by the source; `unknown`, consent-gated zeros and exports that cannot show properties are `not_ready`, never counted as observed. Fire the events from the real production site first; configuration alone is not evidence (WF-025).

### Post-launch search review

Before a review that relies on Google data, run `python3 scripts/marketing/connections.py probe <gsc|ga4|google_ads>`; `unconnected` is a gap with owner steps (`references/ad-platform-connections.md`, Read connectors), not a zero. After a page set has been live for a full Search Console window, export Queries with `gsc-queries-v1` and run `python3 scripts/marketing/search_feedback.py <keyword-map.json> <queries.csv> --metadata <meta.json> --out <dir>/keyword-map.search-feedback.proposed.json`. It reports planned clusters with no observed impressions (anonymised queries are omitted, so not proven zero), blank-value clusters as unknown, impressions without clicks (a title/snippet hypothesis, not a finding) and unplanned queries with impressions (content opportunities). Output is a proposal for the map's `decision` field; the reviewed map is never edited, and a human review applies any change.

### Prepare, review and finalize

```bash
python3 scripts/marketing/review_cycle.py prepare --project <slug> --campaign <id> \
  --preset gsc-pages-v1 --current <current.csv> \
  --period-start 2026-01-08 --period-end 2026-01-14 --exported-at 2026-01-15 \
  --baseline <baseline.csv> --baseline-start 2026-01-01 --baseline-end 2026-01-07 \
  --baseline-exported-at 2026-01-08
```

Dates above are synthetic examples. Two files are the same source in distinct comparable windows; different platforms do not form a before/after experiment. Omit baseline for the first report. Metadata can be supplied once through campaign setup and reporting-period flags; the owner never needs to author column-mapping JSON. Use `--property`, `--timezone`, `--currency`, `--attribution`, `--maturity`, `--report-scope` to supply confirmed report-specific metadata.

Preparation writes `packet.json`, `report.md` and `review-template.json`. With stale Marketing inputs the descriptive preview remains private and visibly gated. Read the packet as evidence, complete the template in a separate file and leave the packet unchanged. Task evidence uses `metric:<name>`, `comparison:<name>` or `coverage`. The diagnosis/limitations are agent judgments, not deterministic causal proof. First/non-comparable reports require `collect_more_data`.

```bash
python3 scripts/marketing/review_cycle.py finalize --project <slug> --campaign <id> \
  --packet <packet-id> --review-json <completed-review.json>
```

Finalization validates schemas, project/account bindings, current context/tasks, preset version and Marketing prerequisites. It atomically publishes an immutable report occurrence, packet/review, ordered review history, latest pointer, website brief and shared execution plan. Identical finalization is idempotent. Changed metadata/transform produces a new import revision; changed tasks/context require a new review. A correction to an existing source/account/period is labeled a restatement and supersedes that period's prior revision; it is not additional acquisition. A review with unchanged observations is labeled a review revision. Older corrections and backfills preserve the latest reporting period. `last_processed_packet_id` identifies the most recently processed review separately.

When corrected observations affect another period's baseline comparison, the correction report and latest pointer explicitly list `reconciliation_pending` packet IDs. Re-import the affected period with the corrected baseline and complete a new review to clear its flag; earlier reports remain immutable historical records. The history index is initialized from bound published packets when resuming an older local release. Stale or invalid input leaves the last good canonical report intact. Unrelated concurrent publication uses the existing project revision guard and requires retry/reconciliation after a conflict.

The report opens with available spend/outcomes, exposes coverage limits and gives the diagnosis, decision and owner work. It does not add attributed conversions across providers or infer CRM outcomes. Larger action histories remain in one execution plan. A declined task is not re-proposed under the same ID; a materially changed proposal needs a new ID with an explanation.

The weekly report and shared owner summary use the same task selection rules. Up to three due tasks per campaign appear first; snoozed tasks and blocked tasks appear separately. Existing owner steps, destinations, prepared-material paths and dependency blockers remain visible. Submitted work is marked for outcome review so it is not presented as a new action to repeat.

### Observe changes before proposing more

Before recommending another bid, budget, targeting, creative or landing-page change, inspect the campaign's recent interventions. In the existing `campaign-context.md` and execution plan, retain the hypothesis, affected IDs/versions, actual implementation time/evidence, baseline, expected qualified-customer effect, conversion-lag/observation window, next review and rollback condition. Acceptance or task completion alone does not prove a live change occurred.

Avoid overlapping interventions that make the question unanswerable. Bundle necessary changes as one intervention when their individual effects cannot be separated; use a controlled design for individual causal claims. Review actual exposure and mature outcomes before another discretionary change to the same scope. Compare business/CRM aggregates where available, while labeling before/after associations as observational. No fixed waiting period fits every campaign.

Zero new tasks is valid. Use `continue` with an explicit no-change rationale when comparable evidence supports it; use `collect_more_data` for insufficient evidence, including first/non-comparable reports. Record what evidence/date will reopen the decision. Broken tracking, disapprovals or a breached spending boundary may need urgent action within existing authority; record the exception and its interference with the test. Frequent recommendations and owner approval are not evidence of improvement. These are reasoning requirements; the local controller does not enforce a cooldown or control live ads.

Source checked 2026-10-24: [Kirk Williams on agent over-optimization](https://zatomarketing.com/blog/ai-ppc-agents-and-the-over-optimization-trap-are-claudgents-hurting-your-accounts) (2026-10-02). The record and decision rules above are repository adaptations of the identified risk, not measured performance gains.

### Task decisions

```bash
python3 scripts/marketing/campaign.py task --project <slug> --campaign <id> \
  --action <campaign-id>--<task-id> --event accept
```

Other events are `decline --reason '<reason>'`, `snooze --until <future-date>` and `complete --evidence '<owner attestation>'`. Completion requires prior acceptance and generic task scope. Existing placement/delivery actions use their evidence-specific workflows. Owner attestation is labeled explicitly; it is not an independent platform verification. Task changes use revision-checked Marketing publication. Private future execution journals do not control commitments. A declined required action remains a scope exception until the owner revises the requirement explicitly.

If campaign facts, context or approved claims change, unfinished tasks with the old context are marked `Needs context review` and excluded from due work. A fresh review cannot silently carry the stale proposal as current. Decline the old task with a supersession reason, then prepare a new packet and propose a replacement under a new task ID. The replacement starts as proposed and requires renewed owner acceptance.

### Claims and website handoff

`campaign-context.md` carries the supplied audience, offer and objective. Add reviewed sources to `approved-claims.json` with claim IDs, text, source, review and expiry dates. A line containing a declared factual claim uses `[[claim:<id>]]`.

```bash
python3 scripts/marketing/claims.py --project <slug> --campaign <id> --draft <draft.md>
```

The checker verifies declared markers, review dates and numeric tokens against the registry. It cannot detect every unmarked or semantically misleading claim. Editorial review remains required; no draft enters a publishing queue in this release. Jurisdiction/industry overlays are selected per project, never assumed from earlier examples.

The generated `website-brief.md` is a handoff for the existing website builder: confirm intent/offer/CTA, evidence, useful interactive features, accessible form-to-destination journey, consent, deduplication and actual lead receipt. Technical SEO/performance checks remain with Website. A plan or tracking installation does not prove deployment, delivery or marketing improvement.

### Offline demonstration and connection status

`python3 scripts/marketing/demo.py --out <new-empty-directory>` creates a synthetic project, imports two example periods, finalizes a review and exercises task continuity. Fixture data proves only deterministic local behavior. `python3 scripts/marketing/connections.py --project <slug>` validates definitions and explicitly reports that live access is unverified. Provider preferences/auth notes are in `config/marketing/providers.json`; Google/Meta/TikTok eligibility and exact current permissions must be checked when implementing the isolated reporting pilot. See `ad-platform-connections.md` for dated setup guidance. Do not add an execution route or globally inherited write connector for this local release.
