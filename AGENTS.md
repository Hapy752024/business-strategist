# Evidence Scout Agent Set

This repo contains a portable business-idea validation skill set for Claude Code.
This file holds facts and standing rules for every session.
Procedures live in the skill that owns them; invoke the selected skill, not the whole catalog.

## Standing rules

**Evidence first: search before answering.**
Never answer market, audience, competitor, platform, pricing, or marketing-channel questions from training memory.
Before answering, run at least one retrieval (web search via `scripts/serper_fetch.py`, a social/community source, or a provider from `config/source-capabilities.json`, including podcast, trends and social sources).
End research answers with a source list with dates.
If a retrieval route fails, state what could not be checked instead of filling the gap from memory.

**Blunt and truthful.**
Be direct and challenge by default; do not validate the founder's idea by default.
Separate what users actually said or did from interpretation.
Push back on vague segments, weak pain, missing buyers, and unsupported demand claims.
Say "I don't know" when the evidence does not settle a question.

**Unpaid interview recruitment.**
Recruit interview participants without payment.
Do not offer cash, vouchers, gifts or compensated-panel participation unless the founder explicitly changes this preference.
Advertising/distribution spend is separate and still needs its own authorization.
Screen target fit and recent experience independently; unpaid signups are not automatically valid customer evidence.
Apply `references/interview-recruitment.md` for researched access routes.

**Spend policy (Provider Policy).**
Paid customer-evidence API spend is pre-authorized with no cap.
Advertising, paid asset generation, deployment and ad/social-platform writes need explicit approval.
Credit failures are coverage gaps, never absence of demand.
Details: `references/operating-guide.md`.

**Pain-first gate.**
Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded; `scripts/route_workflow.py` enforces it with `--project <slug>`.
Gate details: `.agents/skills/business-strategist/SKILL.md` and `.claude/rules/business-gate.md`.

**No final recommendation without a claim challenge.**
Final case delivery, a final decision memo or final case insights need a falsification output (reviewed-ledger or draft basis); progress snapshots do not.

**Research coverage.**
For substantive chosen-idea validation, run a targeted international commercial-precedent pass or state why it does not apply (`references/opportunity-research-approaches.md`).
Once the idea/segment is clear, run the evidence-scout early desk steps (search journey, competitor content, keyword volumes, social topics) in parallel with customer voice; they wait for no review, ledger or gate.
Dependent steps (VOC table, claim challenge, decision memo) use reviewed inputs when they exist, otherwise their labelled fallback; never skip them.
For substantive Business research, use official statistics and studies for market, population and regulatory claims, or name them as unchecked (`references/research-data-and-precedents.md`).
When planning website content, SEO pages or earned media, propose the statistics pages, calculators and checklists the customer journey calls for, built from the wired statistics sources (`references/seo-rule-pack.md`).

## Workspace check: always first

Before starting ANY research workflow, check for existing project workspaces:

```bash
ls -d projects/*/project-manifest.json projects/*/business/project-manifest.json projects/*/business/market_research/manifest.json projects/*/business/cases/*/market_research/manifest.json projects/*/business-analysis/project-manifest.json projects/*/business-analysis/market_research/manifest.json projects/*/business-analysis/cases/*/market_research/manifest.json projects/*/market_research/manifest.json projects/*/cases/*/market_research/manifest.json 2>/dev/null
```

If the conversation already selects a workspace or clearly requests continuation, read that manifest and resume without asking again.
Otherwise, if workspaces exist, read each manifest's `current_stage`, `updated_at`, `next_action` and `open_blockers`, present them as numbered options and ask exactly one question:

```
I found existing research workspaces:

1. projects/<project-slug-1>/ — stage: <current_stage>, last updated: <date>
2. projects/<project-slug-2>/ — stage: <current_stage>, last updated: <date>

Which path: continue [1], continue [2], or start new research?
```

Extract fields with `python3 -c "import json; m=json.load(open('projects/<slug>/market_research/manifest.json')); print(m['current_stage'], m['updated_at'], m['next_action'])"`.
If no workspaces exist, proceed directly.
A matching topic without a clear continuation/new-run instruction needs one choice before creating anything new.
Full resume procedure: `references/workspace-lifecycle.md`.

## Research mode

Select the research mode first; do not treat every rough input as a request to be grilled.
Focused answers and execution requests: apply `references/task-scope.md`; they do not start research workspaces or full strategy outputs.

- **Market discovery**: use `market-problem-discovery` when the user wants to explore a broad market, find customer problems, discover possible segments, or identify underserved pockets before they have a thesis.
- **Idea validation**: use `idea-grill` when the user has a candidate idea, problem, or segment and wants to make it researchable or pressure-test it.
- **Ambiguous intent**: ask exactly one routing question: `Do you want market discovery—find evidence-backed customer problems and segments from this area—or idea validation—pressure-test a specific customer/problem hypothesis?`

## Routing command

Before specialist dispatch run:

```bash
python3 scripts/route_workflow.py --intent <intent> --task-scope <scope> --check-skill <selected-skill> [--project <slug> --case <id>]
```

Exit 2 means stop dispatch (blocked gate or invalid selection).
Invoke repository skills with the Skill tool (not by reading SKILL.md), so the route hook can attach the route packet; then read the packet's `required_references`.
Multi-mode specialists need their route ID (for example `case-appraisal`), not the bare skill name.
Claude skill-tool and slash dispatch use the checked envelope; details in `references/runtime-routing.md`.

## Where things live

- Skills: `.agents/skills/` (router: `.agents/skills/business-strategist/`; ownership: `references/runtime-routing.md`)
- Shared references: `references/` (request scope: `references/task-scope.md`)
- Catalog and routes: `config/` (`config/skill-catalog.json`, `config/workflow-routes.json`)
- Procedures, commands and providers: `references/operating-guide.md`
- Lifecycle: `references/workspace-lifecycle.md`
- Path-scoped rules: `.claude/rules/`
- Local evaluation: `evals/LOCAL-EVALUATION.md`; run `python3 scripts/evaluate.py check` after workflow/skill changes.
- Improvement log: record material workflow failures and improvement candidates in `evals/workflow-improvements.md`, following its "How to use" rules.
