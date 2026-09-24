# Option A — reusable idea library with centralized scoped workflows

Round 3, 13 September 2026. Supersedes A's research-only limitation for the **target agent design**. Earlier rounds remain design history. No implementation, migration or market revalidation performed.

## What becomes the default

Future projects use one workstream evidence store, one central scoped manifest and a generated idea library. Insurance is a test fixture, not a special convention.

| Unit | Meaning |
|---|---|
| Topic | Broad question/domain that may produce zero, one or several viable ideas; not itself a venture commitment. |
| Project | Durable workspace for a coherent investigation or selected venture, founder context and related workstreams. A topic project may remain exploratory. |
| Idea | Distinct customer/job/value or operating/economics hypothesis that can receive a separate decision. |
| Variant | Actually investigated variation within an idea; language, customer cohort, channel or product are facets, not automatic businesses. |
| Run | Dated execution with inputs, sources, outputs and outcome; can serve several scopes but never substitute for their identity/readiness. |

Single-idea intake creates one idea and its dossier, no variant placeholders. Broad-topic discovery starts with a topic scope and empty idea registry; it does not create speculative canvases for nonexistent businesses. On discovery completion, actually researched candidates gain IDs and brief records; registration is not founder selection or automatic validation. The user chooses the next investigation under existing discovery rules.

```text
projects/<slug>/
  README.md                         # one current portfolio narrative/comparison
  project-manifest.json              # controller and selected business-scope link
  ideas/index.json                   # identity/facets/relations/paths only
  ideas/<idea>/brief.md               # generated current dossier
  ideas/<idea>/<variant>.md           # generated only when investigated
  market_research/manifest.json       # topic + scopes[ID], central authority
  market_research/<stage>/…           # existing workstream destinations
  strategy/<workstream>/…
  history/evolution.md                # derived chronological work/evolution log
  history/decisions/<date>-<id>.md    # when, what changed, why, affected scopes
  history/snapshots/<date>-<revision>-<event-id>/… # immutable concept/output versions
  branding/…                         # only actual authorized brand work
```

Future scope-specific artifacts use `<stage>/<scope-id>/…` for authored foundations and `<stage>/runs/<run-id>/…` for evidence. Historical paths remain valid. Shared comparisons use the topic scope and explicit affected IDs. Dossiers link all outputs by scope, so their evidence need not live beneath `ideas/`.

## Hard rule: latest outputs and evolution logs are separate

| Scope | Latest reader output | Evolution/provenance |
|---|---|---|
| Project | `README.md` | `history/decisions/`, `history/evolution.md` |
| Idea / variant | `ideas/<idea>/brief.md` / `<variant>.md` | Same history, filtered by stable scope ID |
| Shared research | `market_research/deep_dives/shared/<subject>/current.md` | Dated runs plus history records |
| Scoped specialist | `market_research/<stage>/<id>/current.md` or `strategy/<workstream>/<id>/current.md` | Original runs and `history/snapshots/<date>-<revision>-<event-id>/…` |

For every deliverable, the owning scope records a `latest_artifacts` entry with purpose, format, path and reviewed revision. JSON, CSV, images and other formats keep their native extension; `current.md` is the narrative convention only. Replacing a latest artifact first preserves its immutable prior version, and history links both versions.

Current documents contain only the latest reviewed synthesis, remaining uncertainty and next action. No appended chronological updates, superseded scores or old recommendations survive in their main content. “Current” or “final deliverable” does not mean validated. History is linked separately and explains when/what/why a view changed; raw runs record how research was executed.

Before replacing current content, archive immutable concept/output versions under `<date>-<revision>-<event-id>`; decision records link exact before/after snapshots. The sole decision payload lives in `history/decisions/`; manifest decision events contain only ID/path references, and activity is derived. Changed customer/job/model scope invalidates applicability/readiness pending reassessment. Commit state/reference under lock, then regenerate latest outputs. Interrupted refresh creates a detectable revision mismatch. Existing `strategy/decisions/` history remains linked.

Default to **one project decision/evolution log**, tagged by scope, linking detailed decisions and concept snapshots. Raw operational/provider logs stay in runs. Per-scope logs help independently staffed investigations but fragment shared reversals; add filtered views when volume obscures navigation, never duplicate authoritative events.

## Lifecycle and natural-language resolution

**Create** an ID when a supplied hypothesis or researched alternative needs its own conclusion/next action. Mere mentions stay in the parent's related-possibilities list. **Reuse** the stable ID when wording changes but the underlying question remains. **Split** when a combined hypothesis contains independently actionable questions; record `split_from`, retain the original and reassess evidence applicability without inheriting passes. **Merge** true duplicates after semantic review; preserve aliases, both histories and source references; conflicting states become unresolved. **Park** leaves the dossier visible with reason/date/reopening conditions. **Promote** to a separate project only for an explicitly selected independent operating lifecycle/ownership or delivery commitment; another language or evidence assessment alone is insufficient. Promotion creates a linked lineage snapshot, not copied proof of validation.

The agent resolves scope from explicit IDs/names, current conversational selection, unambiguous saved aliases, then sole active idea. “Investigate the Chinese version further” resumes the known Chinese variant. “Compare both languages” resolves both IDs with a topic-owned comparative run. “What about Spanish?” within that discussion creates a variant only when investigation is requested; it does not create a new venture. No user-facing ID syntax is required.

Split/merged retired IDs become read-only. Aliases never silently write to retired scopes: resolve an unambiguous survivor and announce it; otherwise clarify.

Ask one question only when multiple plausible targets would materially change research or writing. While unresolved, inspect existing context but do not collect paid sources or write candidate state. Before dispatch, briefly state the resolved target and task; never silently fall back to an umbrella gate. Explicit standalone/focused intent outranks stale workspace context.

## State and cross-skill writing contract

`ideas/index.json` owns identity only. `market_research/manifest.json:scopes[ID]` owns current conclusion/narrative, disposition, next action, evidence bindings, revision and **sparse stage checkpoints**, created when used. Topic scope owns discovery/comparison state, not permission for child execution. Generated dossiers and root-table rows carry input revisions; resume rebuilds or flags stale views. The root authored narrative may compare scopes but cannot override their status.

Every specialist receives one checked envelope: project, task scope, target scope(s), owning scope, allowed artifact family, input references, expected revision and authorization boundaries. It writes original outputs through the common path allocator, then submits an update for only the owning/explicitly affected records under the manifest lock. Multi-scope evidence runs do not mark all children passed. A shared updater records events and refreshes projections; skills do not independently rewrite current status in several Markdown files.

| Specialist family | Canonical outputs |
|---|---|
| Discovery | `market_research/market_discovery/runs/<run>/`; registers researched candidate briefs. |
| Idea grill / customer foundation | `strategy/intake/<id>/`, `customer_segments/<id>/`, `customer_journey/<id>/`. |
| Evidence / customer voice | `pain_points/runs/<run>/`; scoped applicability assessments reference records. |
| Competition / playbooks | Existing alternatives/playbook run roots; scope-tagged comparative or individual outputs. |
| Interviews / risk / strategy | Existing interviews/risks/strategy families with scope-ID destination; update only addressed hypotheses. |
| Brand / website | Existing track manifests; consume explicitly selected scope's immutable handoff. |

Research-folder abbreviations above are beneath `market_research/`. This is one shared output contract referenced by specialists, not many divergent skill templates.

## Full workflow support and honest implementation cost

A's Round 2 research-only restriction is too limiting as the final reusable default. The revised design must support scope-specific `update_stage`, prerequisites, pain gates, overrides and downstream handoffs. A pass for English cannot admit cyber, nor can selecting a topic authorize branding. Missing scope, invalid destinations, unassessed applicability, stale source corrections or unsupported stages fail closed. Overrides record the target ID, reason and user authorization; they do not imply provider/spending/publication consent.

The selected scope's segment/journey/pain coverage and current bindings govern its gate. Shared foundations require applicability assessment. Central checkpoints avoid child manifests, but full support requires substantive code changes.

One central lock plus expected manifest/scope revisions prevents parallel agents from overwriting unrelated changes. On conflict, reread and merge the intended scope update. Corrected sources retain immutable originals and dated replacement/correction events. Consumer bindings include source selector, dependencies, applicability and reviewed correction revision. Scan direct and declared derived consumers; invalidate affected readiness and conclusions until reviewed individually. Unknown derived dependencies invalidate all consumers of the affected report. Unrelated motor or other candidate state remains unchanged. Admission checks correction revisions even if projection rendering was interrupted.

## Synthetic example outside insurance

“Explore reducing restaurant food waste” creates `projects/restaurant-food-waste/` with topic discovery only. Suppose research investigates surplus pickup, demand forecasting and staff waste logging: three idea dossiers appear, all unselected. These are synthetic examples, not market findings.

“Explore forecasting for independent cafés and school kitchens” adds two investigated variants under forecasting. “Continue cafés” resolves that variant, writes `customer_journey/forecasting-cafes/journey.md` and `pain_points/runs/<timestamp>-forecasting-cafes/`, updates only its central checkpoints and regenerates its dossier/root row. School-kitchen evidence and parked surplus pickup remain visible and unchanged.

“Build a landing page for the café pilot” uses café-specific prerequisites/authorization and a scope-pinned handoff. An unrelated bakery logo remains standalone brand work. A shared forecasting correction reopens cafés/schools, not pickup. Separate operating lifecycle/ownership may warrant project separation.

## Exact reusable change surface

| Existing component | Required change |
|---|---|
| `scripts/evidence_scout/init_project.py`; `workspace.py:create_project_workspace` | Explicit topic/single-idea initialization; versioned defaults; no premature thesis/canvas scaffolding for broad discovery. |
| `workspace.py:resolve_run_dir`, `create_run_manifest`, `update_stage` | Shared scope/path resolver, scope metadata, sparse central checkpoints, locked revision updates/corrections. |
| `scripts/route_workflow.py`; `scripts/enforce_skill_route.py`; `references/runtime-routing.md` | Carry and validate scope envelope through checked dispatch, prerequisites and overrides. |
| `scripts/project_workspace.py` | Discover projects plus their idea summaries; derive next actions from scope authority; scope-pin linked business handoffs. |
| `collect.py`, `discover_market_problems.py`, `discover_competitors.py`, `build_interview_kit.py` under `scripts/evidence_scout/` | Pass envelope to existing output/update helpers; avoid unscoped root mutations and run-derived wrong destinations. Audit remaining helper callers. |
| `analyze_competitor_marketing.py`, `collect_ads.py`, `build_entity_landscape.py`, `build_landscape_artifacts.py` under `scripts/evidence_scout/` | Propagate scope through outputs and direct stage-update callers; prevent umbrella fallback. |
| `scripts/evidence_scout/research_founder_playbooks.py` | Adapt custom initialization/path allocation and nested collector `--out-dir`; retain scope through both. |
| `schemas/research-manifest.schema.json`, `stage-checkpoint.schema.json`, `project-manifest.schema.json`, `business-to-brand.schema.json` | Versioned scope/checkpoint/binding and handoff contracts; optional legacy compatibility. |
| `scripts/brand/build_business_to_brand_handoff.py`; `validate_business_to_brand_handoff.py` | Bind source scope, gate/assessment revision and evidence snapshot. |
| `templates/project/README.md`, discovery/intake templates; new dossier template/renderer/index validator | Topic/single-idea views; one current authority and scope-aware references. |
| `AGENTS.md`; `references/workspace-lifecycle.md`; `references/research-coaching.md`; relevant skill workflow references | Generic lifecycle, natural-language resolution and shared output contract; preserve `task-scope.md` bypasses. |
| `config/skill-catalog.json`; `scripts/validate_skill_routes.py`; existing workspace/discovery/routing tests | Scope capabilities plus meaningful regressions across fresh topic, single idea, variants, correction, concurrency and standalone bypass. |

Use existing workspace helpers plus a projection utility/shared reference. Update dispatcher, discovery, validation, competition, risk and downstream writer skills; audit remaining callers. No new specialist skill.

## Compatibility and selection

Fresh research projects receive the versioned default only after end-to-end checks pass. Existing projects retain current paths and manifests until explicit adoption; initialization never rewrites them. Adoption inventories candidate identity, source applicability and current-status conflicts, preserves events/hashes, records a reversible local backup/map, and never copies a historical umbrella pass into new scopes. An unconverted multi-idea workspace cannot advertise safe scope-specific execution.

Focused answers and standalone execution/brand tasks bypass project creation as today. A simple single-idea project gets one readable dossier, not an empty portfolio forest. Compared with B, A centralizes state and keeps future originals in workstream folders; B physically owns future files/state per case. Choose A when uniform cross-skill tooling and shared evidence outweigh self-contained case export. Central-manifest growth, serialized writes and generated-view maintenance remain its costs.
