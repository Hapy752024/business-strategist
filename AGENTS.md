# Evidence Scout Agent Set

This repo contains a portable business-idea validation skill set for Claude Code.

## Operating Stance

Be direct and truthful. Do not validate the founder's idea by default. Separate what users actually said or did from interpretation. Push back on vague segments, weak pain, missing buyers, and unsupported demand claims.

**Evidence first — always search before answering.** Never answer market, audience, competitor, platform, pricing, or marketing-channel questions from training memory. Before answering, run at least one retrieval (web search via `scripts/serper_fetch.py`, social/community source, or a provider from `config/source-capabilities.json` — podcast, trends, and social sources included). End research answers with a source list with dates. If a retrieval route fails, state what could not be checked instead of filling the gap from memory.

## Workspace Lifecycle — Always Check First

Before starting ANY research workflow, check for existing topic workspaces:

```bash
ls -d research/topics/*/manifest.json 2>/dev/null
```

If existing workspaces are found, present them as numbered options and ask exactly one question:

```
I found existing research workspaces:

1. research/topics/<topic-slug-1>/ — stage: <current_stage>, last updated: <date>
2. research/topics/<topic-slug-2>/ — stage: <current_stage>, last updated: <date>

Which path: continue [1], continue [2], or start new research?
```

Read each manifest's `current_stage`, `updated_at`, `next_action`, and `open_blockers` before presenting options. Use `python3 -c "import json; m=json.load(open('research/topics/<slug>/manifest.json')); print(m['current_stage'], m['updated_at'], m['next_action'])"` to extract key fields.

If no workspaces exist, proceed directly to the workflow below. If the user provides a topic name that matches an existing workspace slug, ask whether to continue that workspace before creating anything new.

See `references/workspace-lifecycle.md` for the full resume procedure.

## Workflow

Start by selecting the research mode. Do not treat every rough input as a request to be grilled.

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
4. Use `competitor-scout` to identify direct, indirect, and substitute competitors.
5. Use `competitor-marketing-analyzer` to analyze competitor positioning, CTAs, pricing, and channels.
6. Use `opportunity-risk-designer` to rank risks and design low-cost tests.

Situational skills — invoke when the description matches:

- `startup-business-builder` — zero-to-one plan, customer discovery, MVP, first customers, business model.
- `saas-fintech-pilot-designer` — SaaS, fintech, and insurtech MVP, POC, paid pilot, or regulated test design.
- `company-operating-system` — company setup, execution cadence, goals, metrics, decision rights, hiring.
- `marketing-strategy-builder` — marketing strategy, GTM, segmentation, positioning, messaging, funnels, channels.
- `archetype-gtm-strategist` — end-to-end stage-gated GTM strategy from MVP test through launch and scale.
- `social-digital-marketing-planner` — social media and digital marketing plans, paid/organic platform strategy.
- `social-media-idea-validator` — validate a social media/content/channel idea before investing: audience presence, demand evidence, founder fit, white space, channel economics, GO/PIVOT/KILL verdict.
- `growth-case-analyzer` — successful/failed company case studies and practical lessons.
- `business-archetype-playbook-researcher` — sourced founder/operator lessons by business archetype.
- `startup-challenge-panel` — high-stakes thesis, segment, launch, or scale challenges with multi-role panel.
- `competitor-monitoring` — recurring competitor monitoring, web-traffic estimates, and local/physical-location evidence.

## Commands

Initialize a topic workspace:

```bash
python3 scripts/evidence_scout/init_topic.py --topic "<topic>" --customer-segment "<segment>"
```

Market-problem discovery:

```bash
python3 scripts/evidence_scout/discover_market_problems.py --topic "<market or domain>" --focus "<optional rough hunch>" --collect
```

Validate API access:

```bash
python3 scripts/validate_apis/run_all.py
```

Discover the best source route for a research need:

```bash
python3 scripts/capability_lookup.py --question "<research need>" --compact
```

Default evidence run:

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain phrase 1>,<pain phrase 2>" --workaround-keywords "<workaround 1>,<workaround 2>" --hypothesis-id H1 --days 30 --limit 20 --providers default
```

Competitor discovery:

```bash
python3 scripts/evidence_scout/discover_competitors.py --topic "<topic>" --customer-segment "<segment>" --known-competitors "<optional comma-separated names>" --limit 20
```

Competitor ads intelligence (Meta Ad Library; EU/UK/EEA commercial ads; Apify paid fallback for other markets):

```bash
python3 scripts/evidence_scout/collect_ads.py --topic "<topic>" --competitors-json "research/topics/<topic>/competitors/runs/<run>/competitors.json" --countries DE --limit 20
```

Facebook/Instagram social evidence (ScrapeCreators, paid — ask first):

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --providers scrapecreators --fb-groups "<public-group-url>" --ig-hashtags "<tag1,tag2>"
```

Full command variants and provider routing details live in each skill's `references/workflow.md` and `references/commands.md`.

## Provider Policy

- Default providers: Reddit, SerpAPI Google Trends, YouTube Data API, Serper.dev Google SERP, Firecrawl, Brave Search.
- Firecrawl always uses `FIRECRAWL_API_KEY_HGINVESTOR`.
- Ask the user before running paid-credit providers (social, Sonar, China social).
- Google Trends is a search-demand proxy only. Likes, views, and comments are weak evidence.
- Full provider routing, China coverage, app-store enrichment, and source priority order: `.agents/skills/evidence-scout/references/provider-policy.md`.

Run `scripts/capability_lookup.py --question "<research need>" --compact` before substantial research, enrichment, China coverage, app-store work, or paid fallback routing. Run `scripts/evidence_scout/provider_doctor.py --json` when setup, routing, China coverage, or fallback availability matters.

Founder/operator source discovery: `scripts/podcast_feed_fetch.py search|episodes` (Apple iTunes keyless; Podcast Index and Spotify optional free credentials). Google Trends zero-cost fallback: `scripts/google_trends_fetch.py compare|related` (pytrends, optional dependency) when SerpAPI/DataForSEO credentials are missing.

## Outputs

New runs default to `research/topics/<topic-slug>/`; `--legacy-output` preserves the former global layout.

- `raw/`: redacted provider responses.
- `evidence.jsonl`: normalized evidence records.
- `summary.json`: provider statuses and output paths.
- `report.md`: human-readable evidence summary.
- `market-discovery/runs/<run>/market-discovery-report.md`: evidence-backed candidate problems and segments.

## Infrastructure

- **Agent modes:** `agent-modes/` — mode-specific tool permissions, required checks, and stop conditions for `research`, `source-audit`, and `coding`.
- **Schemas:** `schemas/` — JSON schemas for evidence records, competitor data, stage checkpoints, and topic manifests.
- **Setup validation:** `bash scripts/validate_setup.sh` — checks .gitignore, .env.example, settings files, skill structure, symlinks, and schema validity.
- **Harness config:** `.claude/settings.json` (shared permission guardrails), `.claude/settings.local.json` (personal overrides, gitignored).
- **Implementation plan:** `docs/implementation-plan.md` — full architecture and phase details.
- **Workspace lifecycle:** `references/workspace-lifecycle.md` — resume, replay, and run-manifest procedures.
- **Command reference:** `references/commands.md` — full CLI command variants and provider routing.
- **Context budget:** `templates/CONTEXT-BUDGET.md` — planning checklist for broad, multi-topic, or long-running work (scope, action boundaries, load plan, subagent splits, evaluation plan).
- **CI:** `.github/workflows/validate.yml` runs `scripts/validate_setup.sh` and `scripts/run_evals.py` on push and pull requests; keep both green.