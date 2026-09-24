# Round 3 — generic-agent cross-review

2026-09-13. Reviewed `scope-amendment.md` and both Round 3 proposals, using the amendment's targeted current-code observations. This is a design review and proposed acceptance plan. No code, migration or scenario tests were executed.

## Verdict and meaningful distinction

Both proposals now address a reusable agent, including full scoped research and downstream handoffs. A's earlier research-only restriction is superseded and must not appear in the final comparison.

The durable distinction is where future outputs and authoritative lifecycle state live:

- **A:** `market_research/manifest.json:scopes[ID]`, stage-based original outputs and generated `ideas/` dossiers. One lock and scope-aware updates coordinate the whole investigation.
- **B:** `cases/<case>/market_research/manifest.json`, physically case-owned future research/strategy and a case dossier. Shared studies remain at project scope; case locks isolate updates.

Both still need the same substantial routing, writer, gate, correction and handoff work. A avoids nested lifecycle ownership; it is not a nearly zero-code overlay. Its central JSON also holds authored narrative and can become cumbersome. B makes case export and independent ownership easier but has more state files and shared-versus-case destination decisions. Neither automatically deserves a lower complexity score without the implementation inventory.

Both pass the proposed information-model review: a topic can remain exploratory, an idea has a stable identity, a variant is an actually investigated difference, and a run can inform several scopes without becoming their identity. Empty topic discovery must not generate a venture thesis. Separate evidence assessments alone do not justify separate businesses.

## Logging recommendation: one history entry point for both options

Logging policy is independent of physical output storage. For a founder repeatedly comparing branches, recommend **one project evolution timeline, tagged by scope**, for either A or B. Multiple independently maintained human logs introduce another place to hunt for shared reversals. Physical cases do not require that burden.

| Policy | Advantage | Cost and appropriate trigger |
|---|---|---|
| One project timeline; optional filtered case views | One chronology of what changed and why; shared decisions appear once. | Filter long histories by scope; a renderer is needed. Best default here. |
| Separate authoritative case logs plus umbrella log | Local writing ownership for independently staffed investigations. | Cross-case reconstruction and shared-event placement are harder. Consider only when independent ownership makes this worthwhile. |
| Manually copy entries into both | None that requires duplicated authority. | Reject: corrections and explanations drift. |

Minimal common contract:

1. One canonical decision record per substantive event, for example `history/decisions/<event-id>.md`, owns date, affected scope IDs, what changed, why, reviewer and before/after concept/output snapshot references. A multi-scope decision is one record with several scope IDs.
2. Manifest operational events reference the decision's ID/path and commit revision. They do not maintain a second editable decision explanation. Machine stage events without a substantive decision remain operational history.
3. `history/evolution.md` is the generated human chronology. Optional scope-filtered views are generated from the same committed records. Raw collection/provider logs remain in runs.
4. Snapshots preserve actual prior concepts and outputs. A may archive centrally; B may keep case-local snapshots. Snapshot location does not determine decision-log authority.
5. Snapshot/create decision record, commit reviewed state plus its reference under the appropriate revision-checked lock, then regenerate current views. Uncommitted records are not published in the timeline; interrupted rendering exposes a revision mismatch. Do not present new status alongside unreviewed old prose.

This borrows A's single-entry history experience for B while retaining B's physical case/state ownership. If B retains its separate-log default, describe that as a trade-off requiring user selection, not a technical requirement.

## Clean latest outputs: hard acceptance contract

Latest deliverables must explain the present findings, uncertainty and next action without reading history. Chronological follow-up blocks, superseded scorecards and earlier recommendations belong in history/snapshots, not lower down the current document.

A already specifies current scope/stage destinations such as `market_research/<stage>/<scope-id>/current.md`. B should explicitly standardize `cases/<case>/market_research/<stage>/current.md` and `cases/<case>/strategy/<family>/current.md`, with shared equivalents at project scope. README rules alone will not fix specialist reports. Machine deliverables such as JSON/CSV also need one declared latest artifact reference and immutable prior versions; do not force every format into Markdown.

Current means latest reviewed synthesis, not passed validation or owner approval. Source citations and concise uncertainty belong in current outputs; execution diaries do not. Historical current-looking documents need direct-entry supersession notices linking the appropriate latest output.

## Proposed generic scenario checks

These are acceptance cases to implement, not claims of executed passes.

| Scenario | Expected assertion in A and B |
|---|---|
| Fresh broad topic | Topic/shared discovery initializes without startup canvas or commitment stage activity. Substantively investigated alternatives become visible, unselected scopes. |
| One supplied idea | Exactly one authoritative idea/case assessment; short project context links it. No variant placeholders or duplicate manually maintained conclusion at root. |
| Reuse/rename | “Continue the Chinese version” resolves known scope; title/rank changes retain identity. Consequential ambiguity prompts one question before dependent writes. |
| Split/merge | Preserve prior IDs, evidence and snapshots; new scopes reassess applicability and do not clone passes. Retired aliases are read redirects, never silent write destinations. Conflicting merges remain unresolved. |
| Shared comparison | One comparative run declares its owning project/topic scope and consumer IDs; customer applicability is assessed separately. Shared source does not multiply independent evidence counts. |
| Scoped continuation | A changes only the addressed `scopes[ID]` and scope-tagged stage outputs; B changes only the selected case tree/state. Other scope state hashes remain unchanged except explicit shared-correction effects. |
| Concept/evidence correction | Changed customer/job/model or declared source dependency invalidates affected applicability/readiness; original source and prior concept stay accessible. Unknown dependencies cannot establish readiness. |
| Selection/handoff | Selected scope, assessment revision and evidence snapshot identify brand/GTM/pilot input. Topic completion and another variant's pass cannot admit it. Stale handoff is denied. |
| Standalone/focused bypass | Unrelated logo, supplied-copy rewrite or factual request does not create a topic/case or inherit venture gates. Existing task scope and side-effect authorization still apply. |
| Latest/history separation | After a reversal, current root, scope and specialist outputs contain only the revised coherent synthesis. One history event explains the change and links both versions. Interrupted refresh displays stale state. |
| Legacy adoption | Existing project remains readable and unmoved until explicit adoption; initializer never silently migrates. After opt-in, legacy root pass cannot bypass scope gates. |
| Generic producer coverage | Restaurant/repair synthetic topic exercises each writer family and its actual stage updater, not merely the new initializer and router. No synthetic market claim is treated as evidence. |

## Exact reusable component change matrix

File prefixes below are repository-relative. Named producer scripts are under `scripts/evidence_scout/` unless stated otherwise. This is the minimum known surface from supplied code observations, not an exhaustive caller audit.

| Component | Required integration for both designs |
|---|---|
| `init_project.py`; `workspace.py:create_project_workspace`; `templates/project/README.md` | Topic versus single-idea, lazy defaults, stable initial scope and coherent current/history templates; preserve existing workspaces. |
| `workspace.py:resolve_run_dir`, `create_run_manifest`, `update_stage` | Resolve explicit owning scope; allocate original/current/history paths; revision-checked scoped stage writes and immutable run metadata. A targets central records; B targets case manifests. |
| `scripts/route_workflow.py`; `scripts/enforce_skill_route.py`; `references/runtime-routing.md` | Same checked scope envelope at CLI and configured dispatch; prerequisite checks, pain gates, overrides and path restrictions cannot fall back to another scope. |
| `collect.py`, `discover_market_problems.py`, `discover_competitors.py` | Pass scope through both run allocation and subsequent stage writes; discovery registers researched candidates without granting their gates. |
| `analyze_competitor_marketing.py`, `collect_ads.py` | Adapt their resolver and `update_stage` calls; avoid correct case files accompanied by incorrect umbrella state updates. |
| `build_entity_landscape.py`, `build_landscape_artifacts.py` | Replace direct workspace stage assumptions with the checked scope; preserve existing quality gates. |
| `research_founder_playbooks.py` | Adapt separate initialization, constructed `strategy/playbooks/runs/` destination and collector `--out-dir` bridge; this path is missed by changing collectors alone. |
| `build_interview_kit.py` | Checked caller/adapter supplies output owner and source applicability; a raw output directory is not scope authorization. |
| `scripts/project_workspace.py`; `scripts/brand/build_business_to_brand_handoff.py`; handoff validator | Discovery/next-action aggregation plus explicitly selected business scope and revision-pinned handoffs; standalone tracks remain valid. |
| Research/stage/project/handoff schemas; catalog and lifecycle references | Version identity, selected scope, checkpoints, bindings, decision references and compatibility. Use a shared contract across skills rather than inconsistent copied instructions. |
| Templates, projection/history utilities, validation and existing regression suites | Latest outputs, timeline, snapshots, freshness, unknown/retired scope rejection, split/merge, concurrent updates, interruption and legacy no-write checks. |

Producer coverage must also account for monitoring, customer-perspective challenge, risk, operator research, marketing/social, pilots, operations and brand/UI/web outputs. Some rely on agent-authored files rather than the named helpers: their skill instructions and checked caller adapters need the same envelope. Specialized stores such as town data should expose references through their existing owner, not be copied into every variant.

## Remaining design clarifications and recommendation

I sent root four bounded clarifications for A/B: enumerate the already-known direct writer exceptions; make the decision payload/reference direction unambiguous; give B exact latest specialist paths; and reject new writes through retired split/merge aliases. A's patched Round 3 document was reread and resolves its applicable items. B's patch remains pending this review's final verification. These are small contract completions, not reasons to reopen architecture exploration.

Subject to those clarifications, both are credible reusable designs with different storage/state ownership. Keep one evolution entry point for the founder in either design. The implementation decision should turn on whether physically self-contained case work outweighs centralized workflow administration, not an artificial difference in supported capabilities or number of logs.
