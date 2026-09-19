# Finalist B — physical cases with independent research state

Round 2, 13 September 2026. Design only. This is the larger alternative: case-specific future research and strategy physically live together, and each case owns its research lifecycle. Current software does not support this yet. The insurance corpus, gates and source claims remain unchanged.

## What changed through cross-pollination

| Input | Borrowed or rejected | Reason |
|---|---|---|
| A: explicit visible variants and operating paths | Borrowed | English, Chinese, Arabic doctors and broker acquisition must be directly discoverable. |
| C: idea/facet/variant distinctions | Borrowed | An independently assessed case need not be a separate business; avoid language/profession hierarchy and combinatorial folders. |
| A/C: preserve dated shared research | Borrowed | One historical report can serve several cases without duplicated evidence. |
| A/C: stage-oriented future write locations | Rejected for this finalist | Physical ownership of new case outputs is its substantive difference from the lean library. |
| A/C Round 1: mutable state in both index and brief | Rejected | Case manifest owns state; index is identity-only and status displays are derived. |
| B Round 1: health-only English/Chinese names and digest-only correction | Rejected | They narrowed the original hypothesis and did not propagate invalidation. |
| Judge: full scope contract and direct-entry history | Borrowed | Folder nesting alone does not establish routing, gates or trustworthy current conclusions. |

## Folder contract and complete visible coverage

```text
german-insurance-opportunity/
  README.md                         # current umbrella comparison
  project-manifest.json              # controller; existing workstream authority
  cases.json                        # ID, kind, facets, related IDs, path only
  cases/
    personal-cover-english/
    personal-cover-chinese/
    it-professional-and-personal/
    doctors-professional-and-personal/
    arabic-employed-doctors/
    discounted-motor-mga/
    cyber-insurability-precheck/
    self-employed-retirement/
    retirement-55plus/
    broker-portfolio-acquisition/
  market_research/
    manifest.json                   # umbrella comparisons; no case gate inheritance
    evidence-corrections.jsonl       # append-only correction/replacement register
    customer_segments/language-comparisons.md
    pain_points/runs/               # existing frozen runs; future common runs
    solution_alternatives/          # shared competitors and cross-case studies
    deep_dives/                     # dated comparative reports retained
  strategy/
    decisions/                     # umbrella decisions and migration history
    surelius-personalised-why-and-simulation.md
    ...                             # shared economics, delivery, channel analyses
```

Each case starts with `README.md` and `market_research/manifest.json`; create additional folders only when work requires them. Future case-specific segment, journey, pain, competitor and strategy files use that case's `market_research/` and `strategy/` subtrees. No automatic brand, website or empty pilot scaffold.

English/Chinese retain the broad consequential personal-cover hypothesis. Their dossier explicitly indexes GKV/PKV, BU/income protection and sickness-income work, marking each researched, mentioned or unassessed from the inventory. A health-only follow-up must state its restricted scope. Japanese/Korean comparisons remain directly linked rows pointing to `language-comparisons.md`; unequal source depth stays visible. Arabic doctors has its own dossier and links to general doctor and language findings. The same evidence is referenced, never copied.

Surelius is a delivery concept; the lifetime simulator remains a linked capability unless a distinct commercial hypothesis is selected. Register mail is a channel linked to applicable cases. Broker acquisition is typed `operating-path`, and 55+ is a visible segment investigation with its historical exclusion rationale. Motor is explicitly the investigated MGA model; other discounted-car-insurance models are not silently rejected. Labels and imported dispositions remain provisional until conflicting source guidance is reconciled.

Root rows link directly to EN, ZH, motor, Arabic doctors and parked cases: one click to the case, another to evidence. Families/facets organize the table, not filesystem ancestry or gate inheritance.

## Authority without parallel mutable summaries

| Information | Single authority |
|---|---|
| Case identity, type, facets, path | `cases.json` |
| Disposition, review date, next action, blockers, stage readiness | Case `market_research/manifest.json` |
| Evidence applicability and reviewed correction revision | `evidence_bindings` in that same manifest |
| Substantive current interpretation | Scoped case README body |
| Change rationale and previous decisions | Manifest events linking dated case `strategy/decisions/` records |
| Umbrella strategic choice | Root README and umbrella manifest events |
| Source replacement/correction | Append-only umbrella correction register; original bytes retained |

Disposition (`investigating`, `parked`, `selected-for-test`, etc.) is distinct from gate readiness. Imported contradictions use `needs_reconciliation`; a test selection is not a pass. README status boxes and root comparison rows derive from case manifests, including a freshness indicator. Human synthesis must be reviewed when supporting bindings become stale; generation does not prove semantic consistency.

The authored README body records the assessment revision and evidence/correction revision its substantive prose was reviewed against. A generated status-box update never advances those prose-review markers. Scope entry and summary generation compare all three: current assessment, applicable evidence corrections, and prose-review markers. After an interrupted update, mismatched prose or projections are explicitly stale and cannot supply a current recommendation or downstream handoff until the responsible reviewer completes the review.

Use existing `project_workspace.next_actions` track traversal as the basis for derived aggregate case blockers. Do not maintain an additional manual controller blocker list. Existing historical umbrella gates remain intact; they do not create case passes.

## Shared-source correction: concrete trace

Suppose a reviewed claim in `customer_segments/surelius-and-language-segments.md` is corrected by a new dated audit. English and Chinese case manifests bind that document's relevant section; motor binds only motor evidence.

1. Preserve the original document and write the dated replacement/audit. Append correction `C-001`, identifying old artifact + section, replacement path, reason and monotonic correction revision.
2. Enumerate `evidence_bindings` across registered case manifests. Exact matching selectors are affected; an unknown or whole-document selector is conservatively affected. This is a scan of a small case registry, not a new graph service. For admission-relevant claims taken from derived reports, bindings must also declare the report's underlying source-claim dependencies; consumers are matched through those declarations. If an affected report's source dependencies are unknown or incomplete, conservatively stale every consumer of that report. A report lacking sufficient dependency declarations cannot establish current admission readiness until reviewed. This does not promise automatic semantic discovery of undeclared dependencies.
3. Immediately on read or admission, any binding reviewed before the applicable correction is stale. EN/ZH derived conclusions show “review required” and commitment admission fails even before their manifests are rewritten. Motor has no matching binding and its state is unchanged.
4. The designated research reviewer updates EN/ZH applicability, synthesis and next actions, then uses the normal scoped stage-update path to reassess readiness. Record previous disposition/gate and reason in events; preserve their earlier evidence history.
5. A replacement source does not auto-restore a pass. An explicitly reviewed reassessment can reopen the case. Unaffected findings may remain usable when the review documents their independence.

Digests detect unexpected byte changes; they do not replace this consumer lookup. Direct edits outside sanctioned writers remain outside enforcement. Scheduled/command-entry validation should detect changed referenced artifacts and require correction review.

## End-to-end scope contract

Add one shared resolver returning `project_root`, `case_root`, `manifest_path`, allowed write roots and artifact base. Artifact references remain **umbrella-root-relative everywhere**, including child manifests. Resolve `--project german-insurance-opportunity --case personal-cover-chinese`; reject unknown IDs, symlink escapes and invalid explicit destinations without root fallback.

Affected components are bounded: `scripts/route_workflow.py`, `scripts/evidence_scout/workspace.py`, collectors using its run allocation helpers, `scripts/project_workspace.py`, relevant manifest schemas, lifecycle guidance and downstream handoff readers. Audit remaining direct path assumptions before claiming compatibility; no new agent framework is proposed.

- **Discovery/resume:** list one umbrella project and its registered cases. Read the selected case manifest, dossier, applicable corrections and sources. Multiple cases require explicit scope for case-specific advancement; an explicitly comparative request selects umbrella scope.
- **Collection:** Chinese-only output goes to `cases/personal-cover-chinese/market_research/pain_points/runs/<run>/`. Runs record case ID and immutable source references. Comparative runs stay under umbrella research and declare affected IDs. A new shared report never advances every consumer automatically.
- **Updates/concurrency:** case-scoped advisory lock plus expected manifest revision prevents concurrent overwrites. Read the correction revision before assessment; recheck before commit, retry if changed. Shared correction writes use a separate short umbrella lock. Root summaries regenerate from committed manifests rather than updating another case's state.
- **Gates/overrides:** both router admission and stage-update checks resolve the same case and its assessed segment/journey/pain bindings. Local pain assessments may reference reviewed shared sources. Root passes cannot substitute. Explicit overrides record case ID, stage, actor/reason and evidence revision; never widen to sibling cases.
- **Handoffs:** brand/GTM/pilot inputs carry case ID, assessed manifest revision and evidence revision. Consumers revalidate these on use. A later correction invalidates a stale handoff. An independent scope does not authorize launch or external actions.

**Chinese-only walkthrough:** read registry → Chinese manifest/README → relevant source bindings/corrections; write its new run and assessment → update Chinese manifest under its lock → revise Chinese synthesis and derive root table. English changes only if new findings generate an explicit shared correction; motor files and stage history remain untouched. This supports full independent stages after implementation, unlike a reading-only folder addition.

**Cyber admission:** a cyber launch request resolves its own manifest. With pain validation unassessed, the router and stage updater deny commitment despite the umbrella's stored conditional pass. No manifest is manually marked passed during migration.

## Concrete migration map and rollback

| Actual existing source | Destination/treatment |
|---|---|
| `strategy/annex-b-motor-mga.md`; `strategy/intake/ideas/idea-3-motor-mga.md` | New motor README synthesis; move suitable case-only narrative into motor `strategy/history/` with path map. Frozen intake/evidence retained where preservation applies. |
| Personal annex; `customer_segments/surelius-and-language-segments.md`; four-language run | Retain comparative originals; create broad EN/ZH synthesis and shared language comparison. Do not move/copy whole reports into both cases. |
| `customer_journey/self-employment-journeys-it-and-doctors.md`; profession analysis | Retain shared originals; separately attributed IT and doctor dossiers. |
| `strategy/arabic-brokerage-assessment.md` | Move narrative to Arabic-doctor `strategy/history/`; new current dossier links it and shared doctor evidence. |
| `strategy/annex-c-broker-succession.md`; broker-acquisition deep dive | Case-only annex may move to acquisition history; shared deep dive remains linked. |
| September 11 retirement/register-mail and segment-pain deep dives | Preserve dated shared reports; new cyber, self-employed-retirement and 55+ syntheses. Channel findings stay shared. |
| `strategy/current-recommendation.md`, old README, current-looking annex banners | Snapshot exact originals; direct-entry historical banner links current case/root and dated supersession record. Do not leave an apparent English-first instruction active. |

All abbreviated research paths above start under `market_research/`. Ambiguous/multi-case files stay put and receive explicit ownership review; new synthesis is labeled newly authored, not a moved original. Inventory product coverage before creating cases so BU and sickness-income findings are not lost.

Before migration: back up gitignored files outside active paths; capture protected hashes, references and a per-file old/new/retained/generated map. Repair the nine sampled missing links and complete the scoped link/anchor audit. Build resolver/schema support and dry-run the mapping before any output relocation. Trial EN/ZH/motor and a cross-case correction; require untouched motor state and evidence hashes, exact admission denial and readable supersession handling. Then migrate remaining reviewed cases. Rollback restores backed-up state/narratives and reverses only mapped moves/additions; it never relies on Git history or deleting unlisted files.

## Fit, cost and external evidence

This needs moderate engineering and ongoing per-case reviews; it is excessive for a one-time filing exercise. A separate sibling project becomes justified by independently owned operation, launch budget, deliverables and lifecycle—not simply language or independently assessed evidence. Nested cases preserve one venture until that threshold is explicit.

[Spec Kit decomposition](https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md) supports umbrella/child cycles but warns of overhead; its [scope guidance](https://github.com/github/spec-kit/blob/main/docs/guides/monorepo.md) supports rejecting invalid explicit destinations. [BMad](https://docs.bmad-method.org/cs/plan/choose-a-planning-path/) supports proportionate scaffolding; [GPT Researcher](https://github.com/assafelovic/gpt-researcher/blob/main/README.md) supports retaining bounded reports. Retrieved by root 2026-09-13; these analogies do not establish this evidence-correction or insurance-gating design. No claim of implemented safety or tested founder usability is made.
