# Operating guide

Procedures moved out of AGENTS.md on 2026-09-24. AGENTS.md keeps rules that apply in every session; this file keeps commands, provider mechanics, output layouts and infrastructure pointers. Read the section you need.

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

- Default providers: Reddit, SerpAPI Google Trends, YouTube Data API, Serper.dev Google SERP, Firecrawl, Brave Search, plus the zero-credential set HN Algolia (`hn`), GitHub issue search (`github`), and Google autocomplete (`google_autocomplete`) included in `default`. iTunes review RSS (`itunes_reviews`) is free but explicit (needs `--itunes-app-ids`).
- Firecrawl always uses `FIRECRAWL_API_KEY_HGINVESTOR`.
- Paid API spend for customer evidence and voice-of-customer research is pre-authorized with no monetary spending cap. Use appropriate paid providers without a spend question and expand coverage when evidence quality requires it. Query/sample bounds may exist for reproducibility, relevance and safe execution, not as spending limits. During the current private exploratory/academic phase, do not add GDPR paperwork, a formal ethics review or a privacy-compliance checkpoint. This does not authorize credential theft/sharing, technical access-control bypass, deceptive private-community entry, or advertising spend.
- If a paid evidence provider reports `insufficient_credits`/`billing_required`, notify the user with the lost coverage and top-up route, continue with valid fallbacks where possible, and preserve the gap. After a reported top-up, re-validate and rerun that provider. Never treat a credit-blocked source as absence of demand. Full protocol: `.agents/skills/evidence-scout/references/provider-policy.md`.
- YouTube transcripts: `collect.py --youtube-transcripts` (via `youtube_transcript_api`, free, no quota). Transcripts are creator voice, not customer voice.
- Google Trends is a search-demand proxy only. Likes, views, and comments are weak evidence.
- Full provider routing, China coverage, app-store enrichment, and source priority order: `.agents/skills/evidence-scout/references/provider-policy.md`.

Run `scripts/capability_lookup.py --question "<research need>" --compact` before substantial research, enrichment, China coverage, app-store work, or paid fallback routing. Run `scripts/evidence_scout/provider_doctor.py --json` when setup, routing, China coverage, or fallback availability matters.

Founder/operator source discovery: `scripts/podcast_feed_fetch.py search|episodes` (Apple iTunes keyless; Podcast Index and Spotify optional free credentials). Google Trends zero-cost fallback: `scripts/google_trends_fetch.py compare|related` (pytrends, optional dependency) when SerpAPI/DataForSEO credentials are missing.

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
- **Command reference:** `references/commands.md` — full CLI command variants and provider routing.
- **Context budget:** `templates/CONTEXT-BUDGET.md` — planning checklist for broad, multi-topic, or long-running work (scope, action boundaries, load plan, subagent splits, evaluation plan).
- **CI:** `.github/workflows/validate.yml` runs `scripts/validate_setup.sh` and `scripts/run_evals.py` on push and pull requests; keep both green.

- **Live evals (opt-in, spends tokens):** `python3 scripts/run_live_evals.py --skill <name> --live`; results under `evals/live-results/`.
