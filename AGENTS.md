# Evidence Scout Agent Set

This repo contains a portable business-idea validation skill set for Claude Code.

## Operating Stance

Be direct and truthful. Do not validate the founder's idea by default. Separate what users actually said or did from interpretation. Push back on vague segments, weak pain, missing buyers, and unsupported demand claims.

## Workflow

Core sequence for validating a new startup idea:

1. Use `idea-grill` to clarify the idea, target customer segment, core hypothesis, alternatives, current workaround, urgency, and riskiest assumption.
2. Use `evidence-scout` to validate API access and collect source-grounded evidence from Reddit, YouTube, forums, search, Trends, and approved enrichment providers.
3. Use `service-customer-perspective-challenger` to construct evidence-grounded buying contexts and challenge the idea from customer perspectives. Treat simulated customer voice as hypotheses, never research evidence.
4. Use `competitor-scout` to identify direct, indirect, and substitute competitors.
5. Use `competitor-marketing-analyzer` to analyze competitor positioning, CTAs, pricing signals, proof points, and channel clues.
6. Use `opportunity-risk-designer` to rank risks and design low-cost tests.

Situational skills — invoke when the description matches:

- `startup-business-builder` — zero-to-one plan, customer discovery, MVP, first customers, business model, failure-avoidance checks.
- `saas-fintech-pilot-designer` — SaaS, fintech, and insurtech MVP, POC, paid pilot, sandbox trial, or regulated test design.
- `company-operating-system` — company setup, execution cadence, goals, metrics, decision rights, hiring discipline, management routines.
- `marketing-strategy-builder` — marketing strategy, go-to-market, segmentation, positioning, messaging, offers, funnels, channels, campaign planning, growth metrics.
- `archetype-gtm-strategist` — end-to-end, stage-gated GTM strategy from MVP test through launch and scale, especially when SaaS vs fintech/service archetype, first customers, partnerships, or Europe/US/China adaptation materially changes the plan. Use the general marketing skill afterward for campaign detail.
- `social-digital-marketing-planner` — social media and digital marketing plans, paid/organic platform strategy, content calendars, creative testing, campaign measurement.
- `growth-case-analyzer` — successful/failed company case studies and practical lessons from company outcomes.
- `business-archetype-playbook-researcher` — sourced founder/operator lessons by business archetype. Keep operator anecdotes separate from customer-demand evidence.
- `startup-challenge-panel` — high-stakes thesis, segment, launch, business-model, or scale challenges with multi-role panel. Give each role a bounded objective and evidence contract.
- `competitor-monitoring` — recurring competitor monitoring, web-traffic estimates, and local/physical-location evidence. Use as a separate workflow; do not model monitoring as a `--providers` alias in Evidence Scout.

Create or reuse `research/topics/<topic-slug>/` before substantial research. Keep the startup thesis, evidence-tagged Business Model Canvas, one Value Proposition Canvas per segment, provider runs, experiments, playbooks, reviews, and decisions together. `manifest.json` is the durable workflow state.

## Commands

Initialize a topic workspace and canvases:

```bash
python3 scripts/evidence_scout/init_topic.py --topic "<topic>" --customer-segment "<segment>"
```

Validate API access:

```bash
python3 scripts/validate_apis/run_all.py
```

Discover the best current source route for a research need:

```bash
python3 scripts/capability_lookup.py --question "<research need>" --compact
```

Check provider/backend readiness and active routes:

```bash
python3 scripts/evidence_scout/provider_doctor.py --json
```

Default evidence run:

```bash
python3 scripts/evidence_scout/collect.py --topic "<topic>" --customer-segment "<segment>" --problem-keywords "<pain phrase 1>,<pain phrase 2>" --workaround-keywords "<workaround 1>,<workaround 2>" --hypothesis-id H1 --days 30 --limit 20 --providers default
```

Competitor discovery:

```bash
python3 scripts/evidence_scout/discover_competitors.py --topic "<topic>" --customer-segment "<segment>" --known-competitors "<optional comma-separated names>" --limit 20
```

Competitor marketing analysis:

```bash
python3 scripts/evidence_scout/analyze_competitor_marketing.py --topic "<topic>" --competitors-json "research/topics/<topic>/competitors/runs/<run>/competitors.json" --limit 10
```

Founder/operator playbook collection:

```bash
python3 scripts/evidence_scout/research_founder_playbooks.py --topic "<topic>" --archetype "<business archetype>" --customer-segment "<segment>"
```

Full command variants (social, China, app-store, deep marketing analysis) live in each skill's `references/workflow.md`.

## Provider Policy

- Default providers: Reddit, SerpAPI Google Trends, YouTube Data API, Serper.dev Google SERP, Firecrawl, Brave Search.
- Firecrawl always uses `FIRECRAWL_API_KEY_HGINVESTOR`; do not silently fall back to another Firecrawl account.
- Ask the user before running paid-credit providers (social, Sonar, China social) unless they explicitly requested them.
- Google Trends is a search-demand proxy only. Likes, views, and comments are weak evidence unless paired with repeated pain, urgency, and workaround/spend.
- Full provider routing rules, China coverage, app-store enrichment, local extraction, and source priority order are in `.agents/skills/evidence-scout/references/provider-policy.md`.

Run `scripts/capability_lookup.py --question "<research need>" --compact` before substantial research, source enrichment, China coverage, app-store work, document ingestion, or paid fallback routing. Run `scripts/evidence_scout/provider_doctor.py --json` when setup, provider routing, China coverage, or fallback availability matters. Treat `scripts/validate_apis/run_all.py` as runtime truth for whether a provider currently works.

## Outputs

New runs default to `research/topics/<topic-slug>/`; `--legacy-output` preserves the former global layout when explicitly needed.

- `raw/`: redacted provider responses.
- `evidence.jsonl`: normalized evidence records.
- `summary.json`: provider statuses and output paths.
- `report.md`: human-readable evidence summary.

## Infrastructure

- **Agent modes:** `agent-modes/` — mode-specific tool permissions, required checks, and stop conditions for `research`, `source-audit`, and `coding`.
- **Schemas:** `schemas/` — JSON schemas for evidence records, competitor data, stage checkpoints, and topic manifests.
- **Setup validation:** `bash scripts/validate_setup.sh` — checks .gitignore, .env.example, settings files, skill structure, symlinks, and schema validity.
- **Harness config:** `.claude/settings.json` (shared permission guardrails), `.claude/settings.local.json` (personal overrides, gitignored).
- **Implementation plan:** `docs/implementation-plan.md` — full architecture and phase details.

## File Layout

```
.agents/skills/          # Harness-neutral skill definitions
agent-modes/             # Mode-specific rules
schemas/                 # JSON schemas for outputs
scripts/
  validate_apis/         # API credential validation
  evidence_scout/        # Evidence collection, competitor discovery, marketing analysis
  validate_setup.sh      # Infrastructure validation
research/
  topics/<topic-slug>/    # Canonical thesis, canvases, manifest, evidence, reviews, and decisions
  evidence-scout/
    api-validation/      # Cross-topic provider validation results
docs/                    # Implementation plan, improvement notes, access matrix
config/                  # Provider configuration
```
