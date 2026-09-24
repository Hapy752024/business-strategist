# Evidence Scout Agent Set

This repo contains a portable business-idea validation skill set for Claude Code.

## Operating Stance

**Founder recruitment preference:** recruit interview participants without payment. Do not offer cash, vouchers, gifts or compensated-panel participation unless the founder explicitly changes this preference. Advertising/distribution spend is separate and still needs its own authorization. Screen target fit and recent experience independently; unpaid signups are not automatically valid customer evidence. Apply `references/interview-recruitment.md` for researched access routes.

Be direct and truthful. Do not validate the founder's idea by default. Separate what users actually said or did from interpretation. Push back on vague segments, weak pain, missing buyers, and unsupported demand claims.

**Pain-first rule for Business.** For venture investigation, first establish customer segments, journeys and pain points with web evidence, even when the user arrives with a solution. Paths below are relative to the Business or investigated-case root: `market_research/customer_segments/`, `market_research/customer_journey/`, and `market_research/pain_points/` (runs under `pain_points/runs/`). Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded. Branding, standalone Marketing and other Digital Assets can start from their own brief; only explicitly business-linked consumption inherits Business checks. Marketing inside a project that also contains Business defaults to business-linked. An independent Marketing route inside that project must include an established-business brief; a routing flag alone does not bypass the gate. Apply `references/task-scope.md` to narrow requests.

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
- Preserve the user's selected outcome throughout research: validate/challenge their stated idea, or explain a customer segment's pain points about a topic. Similar companies, including companies in other countries, are optional comparison evidence selected only when they help answer that question; do not redirect the task into finding businesses to import or copy. Read `references/opportunity-research-approaches.md` for substantive work that benefits from distinct evidence approaches.
- Research approaches may run concurrently when they examine different source frames or competing explanations. The coordinator owns the shared scope and final synthesis; workers use isolated work packets, retain provenance and counterevidence, deduplicate shared sources/incidents, and do not count agreement as independent evidence. Customer-voice requirements and the Business pain-first gate still apply.
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

Business, Branding, Marketing, Website and other Digital Assets are independently startable subprojects; follow `references/subprojects.md`. Brand and Website commands default to standalone entry and require no prior research, even inside a project that also has a Business subproject. After a user explicitly selects a validated business handoff, branding may reuse its segment and positioning snapshot. A completed business validation never starts branding automatically. GTM, business positioning and explicitly business-linked marketing/brand/website work route with `scripts/route_workflow.py --project <slug>`: the pain-first gate returns `gate_blocked` with `first_skill: idea-grill` until the required `problem_validation` receipt is current (or the user records an explicit `--override-gate`).

For chosen-idea and strategic continuation work, follow `references/research-coaching.md`: persist known answers, ask one decision-changing question early, apply or explicitly reuse the required skill elements in order, and retain unresolved choices while independent desk work proceeds. Interview/GTM/risk planning must apply `references/interview-recruitment.md` and provide researched, idea-specific routes to the first interviewees, including zero-network access. Recruitment planning is allowed before the pain gate; launches remain gated.

## Provider Policy

Paid customer-evidence API spend is pre-authorized with no cap; advertising, paid asset generation and deployment need explicit approval. Credit failures are coverage gaps, never absence of demand. Details: `references/operating-guide.md`.

## Where things live

- Skills: `.agents/skills/`
- Shared references: `references/`
- Catalog and routes: `config/`
- Procedures: `references/operating-guide.md`
- Lifecycle: `references/workspace-lifecycle.md`
