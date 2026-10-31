# Operating guide

Procedures moved out of AGENTS.md on 2026-09-24. AGENTS.md keeps rules that apply in every session; this file keeps commands, output layouts and infrastructure pointers. Read the section you need.

## Commands

Use the selected skill's own workflow and command references; do not load unrelated command references. Common entry points:

- Topic init: `python3 scripts/evidence_scout/init_project.py --project "<project>" --customer-segment "<segment>"`
- Market discovery: `python3 scripts/evidence_scout/discover_market_problems.py --topic "<market>" --focus "<hunch>" --collect`
- Provider validation: `python3 scripts/validate_apis/run_all.py`
- Route lookup: `python3 scripts/capability_lookup.py --question "<need>" --compact`
- Evidence collection: `python3 scripts/evidence_scout/collect.py ... --providers default`
- Community discovery: `python3 scripts/evidence_scout/discover_communities.py --topic "<problem/job>" --customer-segment "<segment>" --locale <country>:<language> --locale-keywords '<country>:<language>=<audience>|<pain>' ...`; repeat locale-specific pairs for other markets and supply `--locale-source-terms` for languages without a built-in pack. Review metadata-only candidates, then promote only sources whose audience, market, activity and access route were checked. Paid-API spending is authorized by the user; Facebook collection is only internally allowlisted and makes no claim of Meta permission or terms compliance. Private material must be user-supplied from legitimate access. Never steal/share credentials, bypass technical controls or use deceptive membership.
- Community promotion: configure separate Ed25519 discovery/review keypairs (`COMMUNITY_DISCOVERY_PRIVATE_KEY_B64`, `COMMUNITY_DISCOVERY_PUBLIC_KEY_B64`, `COMMUNITY_REVIEW_PRIVATE_KEY_B64`, `COMMUNITY_REVIEW_PUBLIC_KEY_B64`) and expose private keys only to their signing stage, then run `python3 scripts/evidence_scout/review_community_candidates.py --candidates <run>/review_candidates.json --discovery-receipt <run>/community_discovery_receipt.json --discovery-audit <run>/raw.json --decisions <review.json> --out-dir <run>/review`; only its signed, stable-lineage current-generation `capture_authorization.json`, `verified_communities.json`, and `community_review_current.json`, matching the authoritative state registry, can unlock reviewed public Facebook targets in `collect.py`. Search-index status cannot establish target access/activity/entity shape; those dimensions require a semantic direct recheck. This is an internal collection gate, not permission or authorization from Meta or another platform. A failed signed re-review revokes the current generation; missing/invalid signing keys cannot overwrite authoritative state. User-supplied private material is kept in a separate non-API artifact.
- Community freshness recheck: run `python3 scripts/evidence_scout/recheck_community_source.py --url <canonical-url> --entity-type <forum|facebook_group|facebook_page> --out <receipt.json>` with only the discovery private key, then add the complete signed receipt to the review packet's `direct_rechecks`. Unsigned, edited, failed, stale or redirected receipts cannot support promotion.
- Competitors: `python3 scripts/evidence_scout/discover_competitors.py ...`
- Full landscape: run `discover_competitors.py` with explicit analog/reference scopes, verify shortlisted official pages with `analyze_competitor_marketing.py`, normalize checked social observations, classify with `build_entity_landscape.py`, then run `build_landscape_artifacts.py`. Stop when its quality gate fails.
- Ads: `python3 scripts/evidence_scout/collect_ads.py ...`; customer-evidence social: `collect.py --providers scrapecreators ...` (paid API spend is pre-authorized; use reviewed public/API sources or user-supplied material from legitimate access).

## Provider Policy

Default providers, spend authorization, credit-failure handling, weak-evidence rules, China coverage and source priority order: `.agents/skills/evidence-scout/references/provider-policy.md`.

Run `scripts/capability_lookup.py --question "<research need>" --compact` before substantial research, enrichment, China coverage, app-store work, or paid fallback routing. Run `scripts/evidence_scout/provider_doctor.py --json` when setup, routing, China coverage, or fallback availability matters.

Founder/operator source discovery: `scripts/podcast_feed_fetch.py search|episodes` (Apple iTunes keyless; Podcast Index and Spotify optional free credentials). Google Trends zero-cost fallback: `scripts/google_trends_fetch.py compare|related` (pytrends, optional dependency) when SerpAPI/DataForSEO credentials are missing.

## Command reference

Extended CLI command variants for each skill. Prefer the entry points under Commands for common use; load this section when the full variant set is needed.

### Evidence Scout

#### Default providers

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --topic-keywords "<short search phrase>" --customer-segment "<segment>" --problem-keywords "<pain phrase 1>,<pain phrase 2>" --workaround-keywords "<workaround 1>,<workaround 2>" --hypothesis-id H1 --days 30 --limit 20 --providers default
```

For generated searches, pass short `--topic-keywords`; calibration uses exact
`--query-plan <path>` candidates (schema: `schemas/pain-query-plan.schema.json`).
Supply matching explicit `--geo`, `--language` and `--providers` (Reddit, Brave,
Serper or Firecrawl). Preview with `--query-preview`. Set `--results-per-query`
(1–10) and a per-provider `--limit` covering every selected allowance;
`--query-limit` selects declared rows per provider. Collection saves the plan and
its digest plus actual query/result ledgers. Brainstorm wording and source
locations, review the plan, probe, review source experiences and refine; full
method and runnable example: repo-root `references/customer-voice.md` (Pain-query calibration section).

#### With social enrichment (paid, ask first)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --workaround-keywords "<workaround>" --hypothesis-id H1 --days 30 --limit 20 --providers default,social
```

#### Facebook/Instagram social evidence (ScrapeCreators, paid — ask first)

```bash
# Public Facebook groups + Instagram hashtags for pain evidence
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --providers scrapecreators --fb-groups "<public-group-url>" --ig-hashtags "<tag1,tag2>" --social-comments

# Competitor/niche Facebook pages and Instagram profiles for content intel
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --providers scrapecreators --fb-pages "<page-url>" --ig-handles "<handle1,handle2>" --fb-max-posts 15
```

### Competitor Ads Intelligence

```bash
# Known competitors (free official Meta Ad Library; EU/UK/EEA commercial ads only)
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json" --countries DE,AT,CH --limit 20

# Keyword mode — discover WHO advertises
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --keywords "<keyword 1>,<keyword 2>" --countries DE --limit 30

# Non-EU market or missing Meta token — Apify fallback (paid, requires --approve-paid after user approval)
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --keywords "<keyword>" --countries US --providers auto --approve-paid
```

#### China-market coverage (public only)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --workaround-keywords "<workaround>" --hypothesis-id H1 --days 30 --limit 20 --providers default,china_public --geo CN --language zh
```

#### With local extraction (crawl4ai)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --workaround-keywords "<workaround>" --hypothesis-id H1 --days 30 --limit 20 --providers default,crawl4ai --local-extract-url-limit 5
```

#### With document ingestion (markitdown)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --document-paths "path/to/doc.pdf,https://example.com/report" --providers default,markitdown --document-limit 5
```

#### App-store enrichment (Sonar, paid — ask first)

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain>" --providers default,sonar --sonar-apps ios:<app_id>,android:<package_name>
```

### Market Problem Discovery

#### Start a discovery run

```bash
python3 scripts/evidence_scout/discover_market_problems.py --topic "<market or domain>" --focus "<optional rough hunch>" --geo AUTO --language AUTO --collect
```

#### Finalize after synthesis

```bash
python3 scripts/evidence_scout/discover_market_problems.py --finalize --run-dir "<run path>" --candidate-count <0-7>
```

#### Narrow scope discovery

```bash
python3 scripts/evidence_scout/discover_market_problems.py --topic "<market>" --focus "<hunch>" --problem-keywords "<pain 1>,<pain 2>" --workaround-keywords "<workaround 1>" --collect
```

### Competitor Discovery

```bash
python3 scripts/evidence_scout/discover_competitors.py --topic "<topic>" --customer-segment "<segment>" --known-competitors "<optional comma-separated names>" --limit 20

# Add Lane B and Lane C scopes explicitly (lane provenance is preserved per source observation)
python3 scripts/evidence_scout/discover_competitors.py --topic "<topic>" --customer-segment "<segment>" --analog-market "<other country or segment>" --reference-capability "website" --reference-capability "YouTube" --limit 20
```

### Competitor Marketing Analysis

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<topic>" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json" --limit 10

# Analyze only one lane
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<topic>" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json" --lane similar_company --limit 5
```

### Lane-aware landscape artifacts

```bash
python3 scripts/evidence_scout/collect_social_presence.py --entities-json "<competitors.json>" --marketing-json "<marketing_analysis.json>" --out "<run>/social-observations.json"
python3 scripts/evidence_scout/build_entity_landscape.py --competitors-json "<competitors.json>" --discovery-summary-json "<discovery-summary.json>" --marketing-json "<marketing_analysis.json>" --social-json "<run>/social-observations.json" --service "<service>" --job "<customer job>" --target-segment "<segment>" --geography "<country/market>" --out "<run>/entity-landscape.json"
python3 scripts/evidence_scout/build_landscape_artifacts.py --entities-json "<entity-landscape.json>" --marketing-json "<marketing_analysis.json>" --out-dir "<run>/landscape"
```

### Founder/Operator Playbooks

```bash
python3 scripts/evidence_scout/research_founder_playbooks.py --topic "<topic>" --archetype "<business archetype>" --customer-segment "<segment>" --geo <country> --language <language> --topic-keywords "<short source-language phrase>" --query-preview
```

### Interview Kit (interview-bridge)

```bash
python3 scripts/evidence_scout/build_interview_kit.py --run-dir "projects/<topic>/market_research/pain_points/runs/<run>" --limit 8
```

### Whitespace Matrix

```bash
python3 scripts/evidence_scout/build_whitespace_matrix.py --topic "<topic>" --evidence-jsonl "projects/<topic>/market_research/pain_points/runs/<run>/evidence.jsonl" --competitors-json "projects/<topic>/market_research/solution_alternatives/runs/<run>/competitors.json"
```

### Infrastructure commands

#### Validate APIs

```bash
python3 scripts/validate_apis/run_all.py
```

#### Capability lookup

```bash
python3 scripts/capability_lookup.py --question "<research need>" --compact
```

#### Provider doctor

```bash
python3 scripts/evidence_scout/provider_doctor.py --json
```

#### Setup validation

```bash
bash scripts/validate_setup.sh
```

#### Initialize project workspace

```bash
python3 scripts/evidence_scout/init_project.py --project "<project>" --customer-segment "<segment>"
```
### Strategy execution review

Run from the repository root. KPI definitions in `schemas/strategy-plan.schema.json` require `direction: at_least` or `at_most`; do not assume larger values are better. Existing plans must add direction before validation.

```bash
python3 scripts/strategy_review.py validate --plan <strategy-plan.json>
python3 scripts/strategy_review.py freeze --plan <strategy-plan.json> --output <baseline.json>
python3 scripts/strategy_review.py weekly-review --plan <strategy-plan.json> --baseline <baseline.json> --observations <observations.json>
```

Freeze before collecting results. Baseline creation refuses overwrite. Review rejects changed experiment/KPI definitions; preserve the baseline and start a new experiment revision when rules change. Numeric observations use the numerator/denominator field names. For scoped KPIs, include `_metadata` keyed by KPI name with matching `window`, `currency`, and/or `cohort`; cohort observations also require `mature: true`. Missing, invalid, mismatched, or immature observations return `incomplete`, never success. Commitments may include `completed_at`; uncompleted commitments are reported as pending or overdue. The report retains the supplied strategic verdict for founder review; it does not infer a business verdict from a ratio alone.


### Bounded evidence collection

`collect.py` now defaults to `--max-http-requests 100` for calls through the shared HTTP helper. Reaching the cap stops later providers, preserves collected records, marks the run blocked, and exits 2. `summary.json` includes `request_budget`, `collection_complete`, and structured `remaining_tasks`; `report.md` lists unfinished provider/quality work. Resolve these tasks before claiming complete coverage. This limit excludes SDK/CLI traffic and implicit redirects, and is not a dollar or wall-clock budget.

Identical successful GETs are reused only when the response explicitly supplies a positive HTTP `max-age`, capped at 60 seconds and adjusted for `Age`. Credentials and headers are part of the in-memory cache identity. POSTs, failures and non-cacheable responses stay live. The bounded cache is cleared at run end and is never written to disk. Use `--fresh-http` to disable reuse. No automatic retries or cross-run cache were introduced.

## Outputs

Each topic is one project folder: `projects/<project-slug>/`. New projects use layout version 3 with independent `business-analysis/`, `branding/`, `digital-assets/website/` and `digital-assets/others/` subprojects. The root README provides navigation; create only the requested subproject through `scripts/subprojects.py`. Each can start independently or consume an explicit upstream handoff. See `references/subprojects.md`.

Business reuses the version-2 case controller: an identity registry and nullable execution selection, current comparison in `business-analysis/README.md`, and variants under `business-analysis/cases/<id>/`. Each case owns current `case_insights.md`; `feasibility.md`, `business-case.md`, optional `economics.json`, and its `market_research/manifest.json` remain supporting analysis and state. New cases have no case-level README. Shared research belongs to `business-analysis/market_research/`. Existing legacy/version-2 projects retain their original paths. Convert an old case README only through the recoverable publisher after source reconciliation. A case may use shared inputs only with explicit source/locator/digest/applicability bindings; shared evidence never inherits validation passes. See [case-insights.md](case-insights.md) for consolidation and review.
Current case advice uses the v2 citation and review contract in [case-assessment.md](case-assessment.md). The researched-appraisal gate requires a reviewed run, while the final research-delivery check requires the exact run in current complete insights. An authored summary or selected-plan heading is not a completion receipt. New local deep dives are inventoried and can make selected insights—and their downstream plan—pending review.

Use [the case assessment contract](references/case-assessment.md) for case outputs, economics, current revision checks and publication commands. The startup builder owns the selected Business plan and GTM under `business-analysis/strategy/` (root `strategy/` in existing version-2 projects). Selection does not waive Business prerequisites. Keep history separate from current narratives: Business owns `business-analysis/history/evolution.md`; Branding and Digital Assets share umbrella `history/evolution.md`, with per-decision details and snapshots. Publish current documents and metadata together through the shared helper; recover the affected owner's pending publication before resuming.

Legacy projects continue ordinary research under their existing paths and stage rules. New case work, selected root plans and downstream execution require explicit migration, rehearsed on a copy first. Do not migrate live work automatically. Standalone brand/website work retains its own scope. Shared provider state lives in `projects/_infra/`; `projects/_archive/` remains read-only. `--legacy-output` is removed; explicit exports cannot bypass a case's output scope.

- `raw/`: redacted provider responses (inside the run that produced them).
- `evidence.jsonl`: normalized evidence records.
- `summary.json`: provider statuses and output paths.
- `report.md`: human-readable evidence summary.
- `market_research/market_discovery/runs/<run>/market-discovery-report.md`: evidence-backed candidate problems and segments.
- `market_research/solution_alternatives/runs/<run>/competitor_plan.md` and `market_research/solution_alternatives/marketing/<run>/marketing_plan.md`: script-generated audit trails (objective, scope, questions, limits) for competitor steps.
- `market_research/interviews/interview-{screener,guide,tracker}.md` (via `build_interview_kit.py`): primary-research kit when evidence is mostly weak/medium.
- `market_research/solution_alternatives/whitespace-matrix.md` (via `build_whitespace_matrix.py`): pains × competitors coverage scaffold for candidate white spots.

## Infrastructure

- **Project subagents:** `.claude/agents/` — bounded research and independent review workers.
- **Schemas:** `schemas/` — JSON schemas for evidence records, competitor data, stage checkpoints, and project/research manifests.
- **Setup validation:** `bash scripts/validate_setup.sh` — checks .gitignore, .env.example, settings files, skill structure, symlinks, and schema validity.
- **Harness config:** `.claude/settings.json` (shared permission guardrails), `.claude/settings.local.json` (personal overrides, gitignored).
- **Implementation plan:** `docs/implementation-plan.md` — full architecture and phase details.
- **Workspace lifecycle:** `references/workspace-lifecycle.md` — resume, replay, and run-manifest procedures.
- **Cross-skill evidence registry:** `references/evidence-registry.md` — distilled sourced findings (sequencing rule, weak-evidence list, pull signals, regional notes) shared across GTM and marketing skills.
- **Owner-action contract:** `references/owner-actions.md` — states, manifest persistence, row shape, and the owner-only vs agent-verifiable split for work only the owner can do or decide.
- **Context budget:** `templates/CONTEXT-BUDGET.md` — planning checklist for broad, multi-topic, or long-running work (scope, action boundaries, load plan, subagent splits, evaluation plan).
- **CI:** `.github/workflows/validate.yml` runs `scripts/validate_setup.sh` and `scripts/run_evals.py` on push and pull requests; keep both green.

- **Live evals (opt-in, spends tokens):** `python3 scripts/run_live_evals.py --skill <name> --live`; results under `evals/live-results/`.

## Skill listing budget

Claude Code drops skill descriptions from the listing when it exceeds a share of context, so skills show by name only and cannot be routed to. `.claude/settings.json` sets `skillListingBudgetFraction` to 0.03 (setting documented at https://code.claude.com/docs/en/skills). Five side-effect skills set `disable-model-invocation: true` and are invoked explicitly only: brand-exporter, brand-workspace-manager, setup-multiharness-project, marketing-campaign-operator, pre-release-regression. The ~30 firecrawl skills in `~/.claude/skills` are user-level and cannot be disabled from this repo; move them to a plugin or prune them to keep the listing under budget.
