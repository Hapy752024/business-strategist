# Operating guide

AGENTS.md keeps rules that apply in every session; this file keeps commands, output layouts and infrastructure pointers. Read the section you need. Each script's `--help` lists its full flag set; do not copy variants here.

## Commands

Use the selected skill's own workflow and command references. Common entry points:

- Topic init: `python3 scripts/evidence_scout/init_project.py --project "<project>" --customer-segment "<segment>"`
- Market discovery: `python3 scripts/evidence_scout/discover_market_problems.py --topic "<market>" --focus "<hunch>" --collect` (finalize with `--finalize --run-dir <run>`)
- Provider validation: `python3 scripts/validate_apis/run_all.py`; provider health: `python3 scripts/evidence_scout/provider_doctor.py --json`; setup: `bash scripts/validate_setup.sh`
- Route lookup: `python3 scripts/capability_lookup.py --question "<need>" --compact`
- Evidence collection: `python3 scripts/evidence_scout/collect.py ... --providers default` (add `social`, `scrapecreators`, `crawl4ai`, `markitdown` or `sonar` as needed). Query calibration: repo-root `references/customer-voice.md` (Pain-query calibration section).
- Community discovery: `python3 scripts/evidence_scout/discover_communities.py --topic ... --locale <country>:<language> ...`; promote only sources whose audience, market, activity and access route were checked, via `review_community_candidates.py` (signed discovery/review keys; `--help`) and `recheck_community_source.py` for freshness. Search-index status cannot establish target access or activity. This is an internal collection gate, not permission from Meta or another platform. Private material must be user-supplied from legitimate access. Never steal/share credentials, bypass technical controls or use deceptive membership.
- Competitors: `discover_competitors.py` (explicit analog/reference scopes), `analyze_competitor_marketing.py`, `collect_social_presence.py`, `build_entity_landscape.py`, `build_landscape_artifacts.py`; stop when its quality gate fails.
- Ads: `python3 scripts/evidence_scout/collect_ads.py ...` (official Meta Ad Library first; the paid Apify fallback needs `--approve-paid`).
- Founder/operator playbooks: `research_founder_playbooks.py ... --query-preview`; podcasts: `scripts/podcast_feed_fetch.py search|episodes`; trends fallback: `scripts/google_trends_fetch.py compare|related`.
- Interview kit: `build_interview_kit.py --run-dir <run>`; whitespace: `build_whitespace_matrix.py`.
- Strategy execution review: `scripts/strategy_review.py validate|freeze|weekly-review`. Freeze before collecting results; missing, mismatched or immature observations return `incomplete`, never success; the report does not infer a business verdict from a ratio alone.

`collect.py` stops at `--max-http-requests` (default 100), preserves collected records, marks the run blocked and lists `remaining_tasks`; resolve these before claiming complete coverage. The limit is not a dollar budget.

## Provider Policy

Default providers, spend authorization, credit-failure handling, weak-evidence rules, China coverage and source priority order: `.agents/skills/evidence-scout/references/provider-policy.md`. Run `capability_lookup.py` before substantial research, enrichment, China coverage, app-store work or paid fallback routing.

## Outputs

Each topic is one project folder: `projects/<project-slug>/`. New projects use layout version 3 with independent `business-analysis/`, `branding/`, `digital-assets/website/` and `digital-assets/others/` subprojects; create only the requested subproject through `scripts/subprojects.py` (see `references/subprojects.md`).

Business uses the version-2 case controller: cases under `business-analysis/cases/<id>/`, each owning current `case_insights.md` ([case-insights.md](case-insights.md)) with `feasibility.md`, `business-case.md`, optional `economics.json` and `market_research/manifest.json` as supporting analysis; shared research under `business-analysis/market_research/`. A case uses shared inputs only with explicit source/locator/digest/applicability bindings; shared evidence never inherits validation passes. Case outputs, economics and publication: [the case assessment contract](references/case-assessment.md). The startup builder owns the selected plan and GTM under `business-analysis/strategy/`. Publish current documents and metadata together through the shared helper; recover a pending publication before resuming.

Legacy projects keep their paths and stage rules; migration is explicit and rehearsed on a copy first. Shared provider state lives in `projects/_infra/`; `projects/_archive/` is read-only.

Run outputs: `raw/` (redacted provider responses), `evidence.jsonl`, `summary.json` (provider statuses), `report.md`, plus discovery, competitor, interview-kit and whitespace artifacts under `market_research/`.

## Infrastructure

- Project subagents: `.claude/agents/`. Schemas: `schemas/`. Harness config: `.claude/settings.json` (shared guardrails), `.claude/settings.local.json` (personal, gitignored).
- Workspace lifecycle: `references/workspace-lifecycle.md`. Cross-skill evidence registry: `references/evidence-registry.md`. Owner-action contract: `references/marketing-execution.md`. Context budget: `templates/CONTEXT-BUDGET.md`.
- CI: `.github/workflows/validate.yml` runs `scripts/validate_setup.sh` and `scripts/run_evals.py`; keep both green. Live evals (opt-in, spends tokens): `python3 scripts/run_live_evals.py --skill <name> --live`.

## Skill listing budget

`.claude/settings.json` sets `skillListingBudgetFraction` to 0.03 so skill descriptions stay in the listing (https://code.claude.com/docs/en/skills). Three side-effect skills set `disable-model-invocation: true` and are invoked explicitly only: setup-multiharness-project, marketing-campaign-operator, pre-release-regression. The `brand-identity` export and workspace modes write files and run only on explicit request. User-level firecrawl skills in `~/.claude/skills` cannot be disabled from this repo.
