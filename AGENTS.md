# Evidence Scout Agent Set

This repo contains a portable business-idea validation skill set for Claude Code.

## Operating Stance

**Founder recruitment preference:** recruit interview participants without payment. Do not offer cash, vouchers, gifts or compensated-panel participation unless the founder explicitly changes this preference. Advertising/distribution spend is separate and still needs its own authorization. Screen target fit and recent experience independently; unpaid signups are not automatically valid customer evidence. Apply `references/interview-recruitment.md` for researched access routes.

Be direct and truthful. Do not validate the founder's idea by default. Separate what users actually said or did from interpretation. Push back on vague segments, weak pain, missing buyers, and unsupported demand claims.

**Pain-first rule for Business.** For venture investigation, first establish customer segments, journeys and pain points with web evidence, even when the user arrives with a solution. Paths below are relative to the Business or investigated-case root: `market_research/customer_segments/`, `market_research/customer_journey/`, and `market_research/pain_points/` (runs under `pain_points/runs/`). Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded. Branding, Website and other Digital Assets can start independently from their own brief; only explicitly business-linked consumption inherits Business checks. Apply `references/task-scope.md` to narrow requests.

**Evidence first — always search before answering.** Never answer market, audience, competitor, platform, pricing, or marketing-channel questions from training memory. Before answering, run at least one retrieval (web search via `scripts/serper_fetch.py`, social/community source, or a provider from `config/source-capabilities.json` — podcast, trends, and social sources included). End research answers with a source list with dates. If a retrieval route fails, state what could not be checked instead of filling the gap from memory.

## Workspace Lifecycle — Always Check First

Before starting ANY research workflow, check for existing project workspaces:

```bash
ls -d projects/*/project-manifest.json projects/*/business/project-manifest.json projects/*/business/market_research/manifest.json projects/*/business/cases/*/market_research/manifest.json projects/*/business-analysis/project-manifest.json projects/*/business-analysis/market_research/manifest.json projects/*/business-analysis/cases/*/market_research/manifest.json projects/*/market_research/manifest.json projects/*/cases/*/market_research/manifest.json 2>/dev/null
```

If the conversation already selects a workspace or clearly requests continuation, read that manifest and resume without asking again. Otherwise, if existing workspaces are found, present them as numbered options and ask exactly one question:

```
I found existing research workspaces:

1. projects/<project-slug-1>/ — stage: <current_stage>, last updated: <date>
2. projects/<project-slug-2>/ — stage: <current_stage>, last updated: <date>

Which path: continue [1], continue [2], or start new research?
```

Read each manifest's `current_stage`, `updated_at`, `next_action`, and `open_blockers` before presenting options. Use `python3 -c "import json; m=json.load(open('projects/<slug>/market_research/manifest.json')); print(m['current_stage'], m['updated_at'], m['next_action'])"` to extract key fields.

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

For substantive customer-input research, always run a topic-led VOC pass from the customer job/problem/trigger without requiring competitor names. When verified competitors, substitutes or similar services exist, also apply `references/customer-voice.md`: run a separate entity-led feedback pass across applicable independent review sites, Google business/location reviews, company Facebook/Instagram comments, Apple App Store reviews, Google Play reviews and external forums; keep supplier posts/replies/testimonials separately attributed. If no entity is yet known, mark entity-led analysis pending, discover candidates, then run it after verification. Keep the two sampling frames separate, map independent customer needs separately from solution-use requirements, and assess each before segment/journey/pain and risk synthesis. Evidence-scout owns customer voice; competitor-marketing-analyzer owns supplier claims. Read applicable `required_references` returned by the route packet before specialist dispatch. Reuse current evidence; focused factual lookups do not trigger a full study.

1. Use `idea-grill` to clarify the idea, target segment, core hypothesis, alternatives, workaround, urgency, and riskiest assumption.
2. Use `evidence-scout` to validate API access and collect source-grounded evidence.
3. Use `service-customer-perspective-challenger` to construct evidence-grounded buying contexts.
4. Use `competitive-landscape-builder` to separate same-market competitors, similar companies, and capability references, then analyze offers, prices, social usage, and positioning.
5. Use `opportunity-risk-designer` to rank risks and design low-cost tests. Only the competitive-market lane may support competitive whitespace claims.

Before specialist dispatch, run `scripts/route_workflow.py` with the understood `--intent`, `--task-scope`, and `--check-skill <selected-skill>`; include `--project <slug>` and the investigated `--case <id>` for a versioned venture. Research focus never selects execution. Use the route ID `case-appraisal` for provisional feasibility/economics; `opportunity-risk-designer` now has multiple modes, so its bare alias is ambiguous. Exit 2 means stop dispatch (blocked gate or invalid selection). For explicit specialist requests, use the configured route ID; an unambiguous skill name is accepted as an alias. Multi-mode specialists require the specific route ID. Empty `match` lists are intentional internal-stage routes, not orphan skills. Routing does not waive specialist prerequisites or authorize side effects. Claude skill-tool and direct slash dispatch use the checked envelope in `references/runtime-routing.md`; the caller supplies its metadata from known user scope. `scripts/validate_skill_routes.py` checks catalog/disk parity and route reachability in CI. These checks enforce the CLI contract and configured Claude skill-dispatch boundary; arbitrary shell/file access is not sandboxed by the router.

Situational capabilities: select from the installed skill descriptions and `config/workflow-routes.json`; use `.agents/skills/business-strategist/references/routing.md` only when ownership is unclear. Load the selected specialist, not the entire catalog of workflows. `config/skill-catalog.json` lists prerequisites, outputs and side-effect boundaries. Brand, website, marketing, operations and monitoring requests retain their own scope; they do not automatically start business validation.

Business, Branding, Website and other Digital Assets are independently startable subprojects; follow `references/subprojects.md`. Brand and Website commands default to standalone entry and require no prior research, even inside a project that also has a Business subproject. After a user explicitly selects a validated business handoff, branding may reuse its segment and positioning snapshot. A completed business validation never starts branding automatically. For GTM, marketing-strategy, positioning and operations, or explicitly business-linked brand/website work (`--entry-mode business_linked`), route with `scripts/route_workflow.py --project <slug>`: the pain-first gate returns `gate_blocked` with `first_skill: idea-grill` until `problem_validation` has passed (or the user records an explicit `--override-gate`).

For chosen-idea and strategic continuation work, follow `references/research-coaching.md`: persist known answers, ask one decision-changing question early, apply or explicitly reuse the required skill elements in order, and retain unresolved choices while independent desk work proceeds. Interview/GTM/risk planning must apply `references/interview-recruitment.md` and provide researched, idea-specific routes to the first interviewees, including zero-network access. Recruitment planning is allowed before the pain gate; launches remain gated.

## Commands

Use the selected skill's `references/workflow.md` and `references/commands.md`; do not load unrelated command references. Common entry points:

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

Business reuses the version-2 case controller: an identity registry and nullable execution selection, current comparison in `business-analysis/README.md`, and variants under `business-analysis/cases/<id>/`. Each case owns current `README.md`, `feasibility.md`, `business-case.md`, optional `economics.json`, and its own `market_research/manifest.json`. Shared research belongs to `business-analysis/market_research/`. Existing legacy/version-2 projects retain their original paths. A case may use shared inputs only with explicit source/locator/digest/applicability bindings; shared evidence never inherits validation passes.

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

- **Agent modes:** `agent-modes/` — mode-specific tool permissions, required checks, and stop conditions for `research`, `source-audit`, and `coding`.
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
