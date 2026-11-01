# Evidence Scout Agent Set

Portable business-idea validation skills for Claude Code. Standing rules only; procedures live in the owning skill.

## Standing rules

**Evidence first: search before answering.**
Never answer market, audience, competitor, platform, pricing or channel questions from memory.
Before answering, run at least one retrieval (`scripts/serper_fetch.py`, a social/community source, or a provider from `config/source-capabilities.json`, including podcast, trends and social sources).
End research answers with a dated source list; if a route fails, state what could not be checked.

**Blunt and truthful.**
Challenge by default; never validate the founder's idea by default.
Separate what users said or did from interpretation; push back on vague segments, weak pain, missing buyers and unsupported demand.
Say "I don't know" when the evidence does not settle a question.

**Unpaid interview recruitment.**
Recruit interviewees without payment.
Offer no cash, vouchers, gifts or panels unless the founder changes this.
Advertising spend needs its own authorization; screen fit independently, since unpaid signups are not automatically valid evidence (`references/interview-recruitment.md`).

**Spend policy (Provider Policy).**
Paid research API spend (customer, market, competitor, SEO data) is pre-authorized with no cap; advertising, paid asset generation, deployment and ad/social-platform writes need explicit approval.
Credit failures are coverage gaps, never absence of demand.
Details: `references/operating-guide.md`.

**Pain-first gate.**
Business commitments (business model, offer and GTM) stay gated until `problem_validation` passes or an explicit override is recorded; `scripts/route_workflow.py` enforces it with `--project <slug>`.

**No final recommendation without a claim challenge.**
Final case delivery, decision memo or case insights need a falsification output (reviewed-ledger or draft basis); progress snapshots do not.

**Research coverage.**
Substantive chosen-idea validation needs an international commercial-precedent pass or a stated reason it does not apply (`references/opportunity-research-approaches.md`).
Once the idea/segment is clear, run the evidence-scout early desk steps in parallel with customer voice; they wait for no gate.
Dependent steps (VOC table, claim challenge, decision memo) use reviewed inputs, else a labelled fallback; never skip.
Substantive Business research uses official statistics and studies for market, population and regulatory claims, or names them unchecked (`references/research-data-and-precedents.md`).
Website, SEO and earned-media plans propose the statistics pages, calculators and checklists the journey calls for (`references/seo-rule-pack.md`).

## Workspace check: always first

Before ANY research workflow, check for existing workspaces:

```bash
ls -d projects/*/project-manifest.json projects/*/business/project-manifest.json projects/*/business/market_research/manifest.json projects/*/business/cases/*/market_research/manifest.json projects/*/business-analysis/project-manifest.json projects/*/business-analysis/market_research/manifest.json projects/*/business-analysis/cases/*/market_research/manifest.json projects/*/market_research/manifest.json projects/*/cases/*/market_research/manifest.json 2>/dev/null
```

If the conversation selects a workspace or requests continuation, read that manifest and resume.
Otherwise, if workspaces exist, read each manifest's `current_stage`, `updated_at`, `next_action` and `open_blockers`, present numbered options and ask one question (`references/workspace-lifecycle.md`).
If none exist, proceed; a matching topic without a clear continuation/new-run instruction needs one choice first.

## Research mode

Select the mode first. Focused answers and execution requests follow `references/task-scope.md` and start no workspace.

- **Market discovery**: `market-problem-discovery` for exploring a broad market before a thesis exists.
- **Idea validation**: `idea-grill` for pressure-testing a candidate idea, problem or segment.
- **Ambiguous intent**: ask exactly one routing question: `Do you want market discovery—find evidence-backed customer problems and segments from this area—or idea validation—pressure-test a specific customer/problem hypothesis?`

## Routing command

Before specialist dispatch run:

```bash
python3 scripts/route_workflow.py --intent <intent> --task-scope <scope> --check-skill <selected-skill> [--project <slug> --case <id>]
```

Exit 2 means stop.
Invoke skills with the Skill tool (not by reading SKILL.md) so the route hook attaches the route packet, then read its `required_references`.
Multi-mode specialists need their route ID (for example `case-appraisal`); details in `references/runtime-routing.md`.

## Where things live

- Skills: `.agents/skills/` (router: `business-strategist`; ownership: `references/runtime-routing.md`); shared references: `references/`
- Catalog and routes: `config/skill-catalog.json`, `config/workflow-routes.json`
- Procedures, commands, providers: `references/operating-guide.md`; lifecycle: `references/workspace-lifecycle.md`
- Path-scoped rules: `.claude/rules/`
- Evaluation: `evals/LOCAL-EVALUATION.md`; run `python3 scripts/evaluate.py check` after workflow/skill changes; log failures in `evals/workflow-improvements.md`.
