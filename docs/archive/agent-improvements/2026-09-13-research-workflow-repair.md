# Research workflow repair plan

Scope: reusable infrastructure; project research is handled separately. Preserve raw runs, existing history, harness settings and permissions. No spend, outreach, deployment or commits.

1. Extend existing route/catalog stage prerequisites for full strategy; keep focused discovery, source repair, interview recruitment and provisional risk planning available before pain validation. Resolve unambiguous specialist-name intent aliases. Never infer completion from a document name or prose assertion.
2. Persist founder answers and a single pending decision-changing question in the research manifest. Resume known answers; continue independent desk work while material user choices remain open. Maintain separate user authorization for external actions.
3. Require idea-specific, researched interview recruitment in applicable interview, risk and GTM skills, with zero-network access, screening, effort/cost and a learning funnel. Distinguish interview recruitment, demand tests and sales.
4. Keep README as the sole current synthesis with contradictions, decisions, research gaps, recruitment and links to deep dives. Correct the schema's rejection of workspace-produced manifest_revision.
5. Require a digest-bound semantic source review before generating evidence-derived interview probes; reject missing, stale, unrelated and non-customer inputs. Preserve hypotheses separately.
6. Narrow sentiment/pain collection after a provisional segment hypothesis: require target/audience terms at the validation CLI, label raw collection as unresolved segment membership, and retain adjacent/unresolved reviewed sources as context only. Preserve broad discovery mode.
7. Add regression tests, run focused tests and required setup/eval checks. Report deterministic coverage separately from live coaching quality.

## Selective external implementation review

Primary sources inspected 2026-09-13; no third-party code or dependencies imported.

| Source | Inspected pattern | Decision and applicability |
|---|---|---|
| [Open Deep Research implementation](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/deep_researcher.py) | clarify_with_user precedes a research brief and may return a question before continuing | Adopt explicit clarification state before consequential selection. Reject wholesale adoption: a broad autonomous research supervisor does not establish founder/customer validation and would duplicate the existing workspace. Repository is archived; this is a design reference, not a recommended runtime dependency. |
| [LangGraph interrupts documentation](https://docs.langchain.com/oss/python/langgraph/interrupts) | Persist a checkpoint and resume with explicit human input; replay can repeat side effects | Adopt durable known-answer/pending-question records and preserve external-action boundaries. Use the current manifest/atomic writer instead of adding a graph runtime or database. A timeout cannot become an approval. |
| [GPT Researcher / AG2 example and code excerpts](https://github.com/assafelovic/gpt-researcher/blob/main/docs/blog/2026-03-03-gpt-researcher-ag2/index.md), 3 March 2026 | Explicit research/review/revision handoffs and a human-facing outline with gaps and sources before writing | Adopt visible gaps/source review and explicit handoff prerequisites in the existing workflow. Do not import its eight-agent runtime, numeric quality score as a truth gate, or blanket approval before every report; ask only decision-changing founder questions while completing authorized independent work. Root reviewed these primary documentation/code excerpts after the implementation checks; no additional runtime code was changed. |

These examples inform implementation choices; they do not prove that this agent's live coaching or research quality improves. The explicit acceptance review for sources addresses this repository's observed unrelated-record failure rather than relying on an external framework.

## Validation record

Implemented against the existing router/catalog, collector, interview generator, manifest schemas and skill references. No new runtime, dependencies, harness settings or research migrations.

- Full Python suite: 300 passed on the final implementation, including the routing-default recheck (10.46 seconds in the final setup run).
- Focused regressions cover skipped intake/risk, explicit route aliases, reused/missing artifacts, one audited override, unreviewed/stale sources, source-role and segment contradictions, retailer-versus-contractor cases, target-scoped queries, broad discovery, and placeholder targets.
- `bash scripts/validate_setup.sh`: 0 errors; existing town-db-curator quality-checklist warning. `python3 scripts/run_evals.py`: 143 structurally valid cases, 0 errors; town-db-curator still has no eval set.
- Nine touched skills passed quick_validate.py. Existing compact-description warnings remain; no new names, domain-specific assumptions or host features were introduced. Python syntax and diff whitespace checks passed.
- During implementation, setup caught a new 31-line skill entry (reduced to 30) and a legacy budget fixture missing the newly required target anchor (updated so it still tests HTTP-budget behavior). Both were fixed before the full-pass claim.

Quality self-review: routing and genericity pass; instructions/resources pass; repository dependencies are explicitly named and resolve. Structural portability only: live Claude/Codex/OpenCode coaching adherence, customer recruitment performance, semantic judgment quality and token savings were not benchmarked. Explicit checkpoint/artifact checks do not verify the truth of research; semantic source-review records can still contain mistaken human/agent judgment. Direct shell/file actions remain outside skill-dispatch enforcement.
