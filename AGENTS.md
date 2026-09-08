# Evidence Scout Agent Set

This repo contains a portable business-idea validation skill set for Claude Code.

## Operating Stance

Be direct and truthful. Do not validate the founder's idea by default. Separate what users actually said or did from interpretation. Push back on vague segments, weak pain, missing buyers, and unsupported demand claims.

**Evidence first — always search before answering.** Never answer market, audience, competitor, platform, pricing, or marketing-channel questions from training memory. Before answering, run at least one retrieval (web search via `scripts/serper_fetch.py`, social/community source, or a provider from `config/source-capabilities.json` — podcast, trends, and social sources included). End research answers with a source list with dates. If a retrieval route fails, state what could not be checked instead of filling the gap from memory.

## Workspace Lifecycle — Always Check First

Before starting ANY research workflow, check for existing topic workspaces:

```bash
ls -d projects/research/topics/*/manifest.json 2>/dev/null
```

If the conversation already selects a workspace or clearly requests continuation, read that manifest and resume without asking again. Otherwise, if existing workspaces are found, present them as numbered options and ask exactly one question:

```
I found existing research workspaces:

1. projects/research/topics/<topic-slug-1>/ — stage: <current_stage>, last updated: <date>
2. projects/research/topics/<topic-slug-2>/ — stage: <current_stage>, last updated: <date>

Which path: continue [1], continue [2], or start new research?
```

Read each manifest's `current_stage`, `updated_at`, `next_action`, and `open_blockers` before presenting options. Use `python3 -c "import json; m=json.load(open('projects/research/topics/<slug>/manifest.json')); print(m['current_stage'], m['updated_at'], m['next_action'])"` to extract key fields.

If no workspaces exist, proceed directly to the workflow below. A matching topic without a clear continuation/new-run instruction needs one choice before creating anything new.

See `references/workspace-lifecycle.md` for the full resume procedure.

## Workflow

Keep simple requests simple: apply `references/task-scope.md` before dispatch. Explicit user intent and exclusions override phrase matching and unrelated workspace state. Focused answers and execution do not automatically initiate research workspaces or full strategy outputs. Verify new market/platform claims when needed; rewriting supplied copy and synthetic code tests do not require market research.

Start by selecting the research mode. Do not treat every rough input as a request to be grilled.

Before material opportunity ranking, apply `references/strategic-positioning.md`: reuse supplied founder context, ask only decision-changing gaps, and compare viable alternatives with comparable initial evidence coverage. Narrow factual and execution requests bypass this intake. Founder constraints and preferences are inputs, not market evidence.

The competitive decision is whether this entrant can succeed at the founder's intended scale. Existing supply is not saturation; an empty niche is not demand. Apply the served-versus-entrant-feasibility assessment and recommendation-change check in `references/strategic-positioning.md`. Claim completion only for requested coverage actually audited and delivered.

When the idea is clear enough to identify its industry, business model and target customer, use `business-archetype-playbook-researcher` before strategic or launch recommendations: search the web and relevant social media for named founders/operators who built comparable successful businesses, including other countries as a source of venture ideas and adaptations. Verify the claimed outcomes, extract patterns, practical to-dos and mistakes to avoid, and check applicability to the target market and founder's resources and stage. Reuse current research; narrow factual or execution requests do not trigger a full playbook study.

- **Market discovery**: use `market-problem-discovery` when the user wants to explore a broad market, find customer problems, discover possible segments, or identify underserved pockets before they have a thesis.
- **Idea validation**: use `idea-grill` when the user has a candidate idea, problem, or segment and wants to make it researchable or pressure-test it.
- **Ambiguous intent**: ask exactly one routing question: `Do you want market discovery—find evidence-backed customer problems and segments from this area—or idea validation—pressure-test a specific customer/problem hypothesis?`

Market-discovery sequence:

1. Use `market-problem-discovery` to collect public evidence and write a detailed discovery report.
2. Ask the user to choose one candidate, change the scope, extend the research, or stop.
3. Once the user selects a candidate, use `idea-grill` to fill remaining hypothesis gaps, then continue with the validation sequence.

Core sequence for validating a founder-chosen startup idea:

1. Use `idea-grill` to clarify the idea, target segment, core hypothesis, alternatives, workaround, urgency, and riskiest assumption.
2. Use `evidence-scout` to validate API access and collect source-grounded evidence.
3. Use `service-customer-perspective-challenger` to construct evidence-grounded buying contexts.
4. Use `competitive-landscape-builder` to separate same-market competitors, similar companies, and capability references, then analyze offers, prices, social usage, and positioning.
5. Use `opportunity-risk-designer` to rank risks and design low-cost tests. Only the competitive-market lane may support competitive whitespace claims.

Situational capabilities: select from the installed skill descriptions and `config/workflow-routes.json`; use `.agents/skills/business-strategist/references/routing.md` only when ownership is unclear. Load the selected specialist, not the entire catalog of workflows. `config/skill-catalog.json` lists prerequisites, outputs and side-effect boundaries. Brand, website, marketing, operations and monitoring requests retain their own scope; they do not automatically start business validation.

Brand requests do not require market research. After a user explicitly selects a validated business handoff, branding may reuse its segment and positioning snapshot. A completed business validation never starts branding automatically.

## Commands

Use the selected skill's `references/workflow.md` and `references/commands.md`; do not load unrelated command references. Common entry points:

- Topic init: `python3 scripts/evidence_scout/init_topic.py --topic "<topic>" --customer-segment "<segment>"`
- Market discovery: `python3 scripts/evidence_scout/discover_market_problems.py --topic "<market>" --focus "<hunch>" --collect`
- Provider validation: `python3 scripts/validate_apis/run_all.py`
- Route lookup: `python3 scripts/capability_lookup.py --question "<need>" --compact`
- Evidence collection: `python3 scripts/evidence_scout/collect.py ... --providers default`
- Competitors: `python3 scripts/evidence_scout/discover_competitors.py ...`
- Full landscape: run `discover_competitors.py` with explicit analog/reference scopes, verify shortlisted official pages with `analyze_competitor_marketing.py`, normalize checked social observations, classify with `build_entity_landscape.py`, then run `build_landscape_artifacts.py`. Stop when its quality gate fails.
- Ads: `python3 scripts/evidence_scout/collect_ads.py ...`; social: `collect.py --providers scrapecreators ...` (paid; ask first).

## Provider Policy

- Default providers: Reddit, SerpAPI Google Trends, YouTube Data API, Serper.dev Google SERP, Firecrawl, Brave Search, plus the zero-credential set HN Algolia (`hn`), GitHub issue search (`github`), and Google autocomplete (`google_autocomplete`) included in `default`. iTunes review RSS (`itunes_reviews`) is free but explicit (needs `--itunes-app-ids`).
- Firecrawl always uses `FIRECRAWL_API_KEY_HGINVESTOR`.
- Ask the user before running paid-credit providers (social, Sonar, China social).
- If a paid provider reports `insufficient_credits`/`billing_required`, pause and ask the user: top up or continue without the source. On top-up, re-validate and rerun the provider; on continue, record the coverage gap. Never treat a credit-blocked source as absence of demand. Full protocol: `.agents/skills/evidence-scout/references/provider-policy.md`.
- YouTube transcripts: `collect.py --youtube-transcripts` (via `youtube_transcript_api`, free, no quota). Transcripts are creator voice, not customer voice.
- Google Trends is a search-demand proxy only. Likes, views, and comments are weak evidence.
- Full provider routing, China coverage, app-store enrichment, and source priority order: `.agents/skills/evidence-scout/references/provider-policy.md`.

Run `scripts/capability_lookup.py --question "<research need>" --compact` before substantial research, enrichment, China coverage, app-store work, or paid fallback routing. Run `scripts/evidence_scout/provider_doctor.py --json` when setup, routing, China coverage, or fallback availability matters.

Founder/operator source discovery: `scripts/podcast_feed_fetch.py search|episodes` (Apple iTunes keyless; Podcast Index and Spotify optional free credentials). Google Trends zero-cost fallback: `scripts/google_trends_fetch.py compare|related` (pytrends, optional dependency) when SerpAPI/DataForSEO credentials are missing.

## Outputs

New runs default to `projects/research/topics/<topic-slug>/`; `--legacy-output` preserves the former global layout.

Maintain `README.md` as the one current executive narrative at the topic root, with supporting narratives under `deep-dives/`. Update its affected sections after substantive follow-ups; do not create another current recommendation memo. Follow `references/workspace-lifecycle.md` for history, links, state consistency and explicit migrations. Existing raw/run artifacts keep their current paths.

- `raw/`: redacted provider responses.
- `evidence.jsonl`: normalized evidence records.
- `summary.json`: provider statuses and output paths.
- `report.md`: human-readable evidence summary.
- `market-discovery/runs/<run>/market-discovery-report.md`: evidence-backed candidate problems and segments.
- `competitors/runs/<run>/competitor_plan.md` and `competitors/marketing/<run>/marketing_plan.md`: script-generated audit trails (objective, scope, questions, limits) for competitor steps.
- `interview/interview-{screener,guide,tracker}.md` (via `build_interview_kit.py`): primary-research kit when evidence is mostly weak/medium.
- `risks/whitespace-matrix.md` (via `build_whitespace_matrix.py`): pains × competitors coverage scaffold for candidate white spots.

## Infrastructure

- **Agent modes:** `agent-modes/` — mode-specific tool permissions, required checks, and stop conditions for `research`, `source-audit`, and `coding`.
- **Schemas:** `schemas/` — JSON schemas for evidence records, competitor data, stage checkpoints, and topic manifests.
- **Setup validation:** `bash scripts/validate_setup.sh` — checks .gitignore, .env.example, settings files, skill structure, symlinks, and schema validity.
- **Harness config:** `.claude/settings.json` (shared permission guardrails), `.claude/settings.local.json` (personal overrides, gitignored).
- **Implementation plan:** `docs/implementation-plan.md` — full architecture and phase details.
- **Workspace lifecycle:** `references/workspace-lifecycle.md` — resume, replay, and run-manifest procedures.
- **Cross-skill evidence registry:** `references/evidence-registry.md` — distilled sourced findings (sequencing rule, weak-evidence list, pull signals, regional notes) shared across GTM and marketing skills.
- **Command reference:** `references/commands.md` — full CLI command variants and provider routing.
- **Context budget:** `templates/CONTEXT-BUDGET.md` — planning checklist for broad, multi-topic, or long-running work (scope, action boundaries, load plan, subagent splits, evaluation plan).
- **CI:** `.github/workflows/validate.yml` runs `scripts/validate_setup.sh` and `scripts/run_evals.py` on push and pull requests; keep both green.
