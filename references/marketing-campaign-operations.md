# Local campaign operations

This is the P0/P1/minimum-P2 release. Shared code operates on explicit projects and campaigns; each Marketing root owns its connection definitions, context, reports and execution plan. Actual account connections, protected collectors, scheduled reasoning, publishing and spending are subsequent releases.

## Select and set up

Resolve `projects/<slug>` through its manifest; use its registered Marketing path. Existing legacy paths are preserved. Start Marketing through `scripts/subprojects.py` only when the user selected that project and supplied its brief. No Business research is started by an export import.

```bash
python3 scripts/marketing/campaign.py setup --project <slug> --campaign <id> \
  --objective '<commercial outcome>' --audience '<selected audience>' --offer '<confirmed offer>' \
  --property '<account or property ID>' --timezone '<IANA timezone>' \
  --report-scope '<confirmed export filters and scope>'
```

For advertising exports also confirm `--currency`, `--attribution` and `--maturity`. The command writes campaign configuration, supplied context and an empty claims registry through Marketing publication. Unknown facts remain missing. Configuration does not authorize external activity. To define connections, supply `--connections <secret-free.json>` and one or more `--connection <id>`; their schema is `schemas/marketing-connections.schema.json`. Credential references have the form `<project-slug>/<connection-name>`. Only the selected project's references are valid; this release never resolves them.

Default runtime packets live under ignored `.marketing-runtime/<project>/<campaign>/` with private file permissions. They contain sanitized aggregate data, not raw uploads or tokens. Keep raw exports in an access-controlled inbox; delete them when the user-selected retention period ends. Same-user permissions are not a secret-isolation boundary. Future connected operation requires protected enrollment, an isolated collector identity and scope enforcement before real credentials load.

## Export presets

Presets declare exact supported English CSV layouts, not every provider export variant. Dates, timezone, property, report filters/scope and export date must be confirmed. These are export instructions checked against synthetic examples; real-account export compatibility remains unverified. Use an equivalent custom-column aggregate report when a standard export differs. A named column error requires the appropriate export or a reviewed new preset; never silently rename ambiguous metrics.

| Preset | Export scope and required columns | Optional metrics and limits |
|---|---|---|
| `gsc-pages-v1` | Search Console Performance → Search results → Pages → Export CSV; use the Pages table: `Top pages,Clicks,Impressions,CTR,Position` | CTR is recomputed; position is weighted by impressions. Confirm report filters and full date range. |
| `ga4-pages-v1` | Pages and screens aggregate CSV with `Page path and screen class,Views,Active users,Event count,Key events` | Comment preambles are supported. Users across page rows are not additive. Confirm reporting identity/settings as applicable. |
| `google-ads-campaigns-v1` | Campaigns aggregate report with `Campaign,Campaign ID,Cost,Clicks,Impressions` | `Conversions` is optional and otherwise unknown. Confirm conversion definition, attribution, currency and maturity. |
| `meta-ads-campaigns-v1` | Ads Manager campaign-level report with `Campaign name,Campaign ID,Amount spent (<confirmed currency>),Impressions` | `Link clicks`, `Website leads` optional. Ambiguous `Results` is not treated as leads. Row reporting dates, when supplied, must match confirmed dates. |

Exclude breakdowns, customer rows and duplicated totals. Query strings are stripped from page dimensions; apparent email/token dimensions are rejected. The importer supports UTF-8/BOM, English thousands separators and known blank/suppressed cells. Other locales, negative amounts, oversized files, non-finite values and unknown layouts produce explicit errors. This does not certify absence of all personal data; inspect source scope before import.

## Prepare, review and finalize

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

## Task decisions

```bash
python3 scripts/marketing/campaign.py task --project <slug> --campaign <id> \
  --action <campaign-id>--<task-id> --event accept
```

Other events are `decline --reason '<reason>'`, `snooze --until <future-date>` and `complete --evidence '<owner attestation>'`. Completion requires prior acceptance and generic task scope. Existing placement/delivery actions use their evidence-specific workflows. Owner attestation is labeled explicitly; it is not an independent platform verification. Task changes use revision-checked Marketing publication. Private future execution journals do not control commitments. A declined required action remains a scope exception until the owner revises the requirement explicitly.

If campaign facts, context or approved claims change, unfinished tasks with the old context are marked `Needs context review` and excluded from due work. A fresh review cannot silently carry the stale proposal as current. Decline the old task with a supersession reason, then prepare a new packet and propose a replacement under a new task ID. The replacement starts as proposed and requires renewed owner acceptance.

## Claims and website handoff

`campaign-context.md` carries the supplied audience, offer and objective. Add reviewed sources to `approved-claims.json` with claim IDs, text, source, review and expiry dates. A line containing a declared factual claim uses `[[claim:<id>]]`.

```bash
python3 scripts/marketing/claims.py --project <slug> --campaign <id> --draft <draft.md>
```

The checker verifies declared markers, review dates and numeric tokens against the registry. It cannot detect every unmarked or semantically misleading claim. Editorial review remains required; no draft enters a publishing queue in this release. Jurisdiction/industry overlays are selected per project, never assumed from earlier examples.

The generated `website-brief.md` is a handoff for the existing website builder: confirm intent/offer/CTA, evidence, useful interactive features, accessible form-to-destination journey, consent, deduplication and actual lead receipt. Technical SEO/performance checks remain with Website. A plan or tracking installation does not prove deployment, delivery or marketing improvement.

## Offline demonstration and connection status

`python3 scripts/marketing/demo.py --out <new-empty-directory>` creates a synthetic project, imports two example periods, finalizes a review and exercises task continuity. Fixture data proves only deterministic local behavior. `python3 scripts/marketing/connections.py --project <slug>` validates definitions and explicitly reports that live access is unverified. Provider preferences/auth notes are in `config/marketing/providers.json`; Google/Meta eligibility and exact current permissions must be checked when implementing the isolated reporting pilot. Do not add an execution route or globally inherited write connector for this local release.
