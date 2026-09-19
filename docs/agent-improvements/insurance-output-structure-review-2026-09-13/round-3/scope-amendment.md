# Round 3 scope amendment: reusable agent, not a one-project cleanup

User clarification received during finalization: “The idea is not only to structure this project, but to adjust the agent so that future projects follow the same structure and allow the user to investigate different variants of an ideas / topics.”

Round 2's 84/87 scores and stop decision applied to the two insurance-grounded designs. They are retained as history, not used to claim the broadened task complete. Round 3 reviews reusable agent behavior and generic new-project defaults. The maximum remains five rounds total. The requested deliverable remains two strong restructuring proposals; no architecture has been selected for implementation.

## New required coverage

1. Fresh broad topic: research begins without pretending a venture or customer hypothesis has been selected; discovered candidates become visible without automatic execution.
2. Fresh single idea: minimal scaffold, stable identity, no duplicate root/child representation and no unnecessary question about technical structure.
3. Follow-ups: resolve existing idea/variant from user intent and session context; reuse matching scope, ask one question only for consequential ambiguity.
4. Lifecycle: distinguish identity from display name/rank; define rename, split, merge, park/reopen and promotion to a separately operated project with preserved provenance.
5. Cross-cutting work: compare multiple variants in shared outputs, bind applicability separately, and avoid inherited readiness or evidence double-counting.
6. Cross-skill consistency: all relevant writers and dispatch paths receive the same resolved scope; root summaries and variant outputs follow one reusable contract.
7. Downstream work: selected variant handoffs remain scoped and checked. Standalone brand/website and focused execution retain their existing bypasses; variant tracking must not impose full business validation on unrelated tasks.
8. Compatibility: new projects use the selected structure by default after implementation; legacy projects remain readable and do not migrate silently. Generic non-insurance behavior is demonstrated on paper with a synthetic example.
9. **Explicit user follow-up: current outputs and history are separate.** Current/final documents present the latest findings and uncertainty, without chronological follow-up blocks, superseded recommendations or an execution diary. Separate human-readable logs explain when/why decisions changed and how the topic evolved. Preserve prior output snapshots and source/run provenance with links, but readers must not need the history to understand the current result. “Current” is document freshness, not validation or approval. Authors must specify paths, authority and an update workflow for both project-level and variant-level outputs.

## Root's current-code observations for authors/judge

- `scripts/evidence_scout/init_project.py` calls `create_project_workspace` and describes a venture workspace with startup canvases. `--topic` is an alias, not a separate topic-oriented scope model.
- `scripts/evidence_scout/workspace.py:create_project_workspace` currently creates all listed research/strategy directories, thesis/canvases, a full set of pending stages and a business controller link. Its default next action asks for a startup thesis even when a collector reaches it from a broad topic.
- `resolve_run_dir` calls that initializer, then uses a caller-supplied fixed workstream subdirectory. An explicit `--out-dir` returns no workspace; it is not a safe substitute for registered variant state.
- `collect.py`, `discover_market_problems.py`, `discover_competitors.py`, `analyze_competitor_marketing.py` and `collect_ads.py` use the shared resolver and then call `update_stage`. Fixing destination paths without fixing stage ownership is insufficient.
- `build_entity_landscape.py` and `build_landscape_artifacts.py` call `update_stage` directly with a workspace argument.
- `research_founder_playbooks.py` separately initializes a topic workspace and constructs `strategy/playbooks/runs/` itself before invoking collection with `--out-dir`. It would be missed by a collector-only change.
- `build_interview_kit.py` writes screener/guide/tracker under the provided output directory. Its scoped owner and evidence applicability must be set by a checked caller or adapter.
- `references/runtime-routing.md` currently sends project-or-standalone metadata, not a variant scope. The checked Claude dispatch adapter and portable CLI contract need consistent schema changes. Emitting a new optional ID is not enforcement.
- `templates/project/README.md` has one current recommendation and options table but no durable candidate/variant identity or per-variant dossier contract. Initializers, templates and specialist output references must agree.
- Core research skills currently describe topic/project-level output paths. A shared contract should be referenced from applicable skills, not copied in slightly different forms into every skill.

This is a targeted producer/control-plane sample, not an exhaustive audit of every writer in the repository. Before implementation is declared complete, a caller inventory and regression suite must cover all affected write and dispatch paths.

## Evidence and safeguards

Use existing primary-source packet as bounded structural analogies. No new insurance or synthetic-domain market claims are needed. The synthetic example tests organization and state behavior only. Root's inventory confirms that all 376 insurance-project files remained byte-identical through Round 2.

Authors A/B revise the two distinct reusable models. Author C independently challenges integration coverage and generic acceptance. Judge applies the original rubric to the broader scope and explicitly checks these additional scenarios before declaring convergence.
