# Proposal C — decision dossiers over canonical research storage

Round 1, 2026-09-13. Design proposal only; no project files changed.

## Diagnosis from the actual workspace

The storage hierarchy describes how agents worked, but the founder asks what choices were investigated. A reader must combine `strategy/intake/ideas/`, `market_research/customer_segments/`, `pain_points/idea-*/`, date-named deep dives and the root README to reconstruct one option.

The taxonomy is also mixed. `idea-1-personal.md` explicitly calls language cohorts subsegments of consequential personal insurance decisions. Motor MGA is a different business model, professionals are a customer/application branch, Surelius is a shared product thesis, and register mail is a proposed access mechanism. Giving everything an equal project folder would conceal these differences.

The root README has a September 11 cyber-first update above an older English-first conclusion. The controller has no blockers while the research manifest lists three. `problem_validation` is marked passed/conditional_pass from a legacy evidence run while segment selection remains in progress. A tidier directory alone will not fix these competing current claims or establish candidate validation.

## The proposal

Add an `ideas/` folder as the reader's front door. Give every independently discussable candidate or investigated variant a short, self-contained dossier. Retain existing evidence and workflow paths. The dossier is a maintained conclusion about one option, with links into canonical research, rather than a copy of every report.

```text
german-insurance-opportunity/
  README.md                       # sole current portfolio narrative and comparison
  ideas/
    index.json                    # IDs, type, parent, state, summary, next question
    personal-decision-advice/
      README.md                   # common problem and business hypothesis
      english-speaking-residents.md
      chinese-speaking-residents.md
      other-investigated-languages.md
    professional-and-personal-cover/
      README.md
      it-self-employed.md
      doctors.md
      other-investigated-professions.md
    discounted-motor/
      README.md
    cyber-insurability-precheck/
      README.md
    retirement-decision-support/
      README.md
    broker-succession/
      README.md
  market_research/                 # current canonical sources, stages and runs
  strategy/
    decisions/                    # dated changes and comparison snapshots
    experiments/                  # actual test specifications and results
    ...                           # existing paths remain initially
  project-manifest.json
```

These initial labels are migration classifications, not new venture endorsements. Existing mentions with insufficient investigation go in a brief's “mentioned, not yet investigated” list, not a folder. Broker succession deserves a discoverable card because an actual annex exists; it may be typed `operating-path` rather than a customer proposition.

The root comparison has columns: option/variant, customer and decision, value hypothesis, business model, evidence maturity, current disposition, decisive unknown, last reviewed. Explicit English and Chinese rows link directly to their cards; no need to infer them from a “multilingual” filename. Status vocabulary: `exploring`, `candidate`, `selected-for-test`, `parked`, `rejected`, `superseded`. These are decision dispositions, never gate passes.

Each card answers: who and when; pain hypothesis; proposed value; what was investigated; supporting evidence and counter-evidence; current conclusion and its date; unresolved questions; next test; related variants; decision history. An option can be parked while its sources remain useful elsewhere.

## Idea, facet, variant, experiment

An **idea** has a distinguishable customer/job/value or delivery/economics hypothesis that could receive a separate investment decision. A **facet** describes language, profession, channel, product or geography. A **variant** is a facet combination that has actually received separate investigation or needs a separately recorded decision. An **experiment** tests a stated uncertainty against a predetermined observation and decision rule.

Thus Chinese is a facet; “Chinese-speaking residents facing a German health-cover decision” is a visible variant. Register mail is an acquisition facet and might become an experiment; it is not automatically a new business. A lifetime simulator can be shared solution capability unless evidence and a distinct commercial hypothesis justify promotion to a standalone idea. These types avoid a folder for every language × profession × product combination.

Use stable IDs independent of display names. `index.json` records `id`, `kind`, optional `parent_id`, `facets`, `brief_path`, `disposition`, dated short conclusion, next question and evidence references. Shared capabilities can be referenced by several cards without forcing a single-parent truth onto the research. One comparison generator reads these entries into a clearly delimited root README table; detailed prose stays human reviewed.

## Actual routing map

| Existing artifact | Reader destination and treatment |
|---|---|
| `strategy/intake/ideas/idea-1-personal.md` | Personal decision advice dossier links it as the dated hypothesis; do not overwrite it. |
| `market_research/customer_segments/surelius-and-language-segments.md` and `strategy/language-market-scenarios.csv` | Both English and Chinese cards link applicable passages; scenarios retain unvalidated labels. |
| `market_research/solution_alternatives/runs/2026-09-06-four-languages/` | Shared reference for language variants; failed quality gate remains visible. |
| `strategy/annex-b-motor-mga.md` and `pain_points/idea-3-motor-mga/run-2026-09-06/` | Discounted motor dossier links both hypothesis/economics and evidence run. |
| `customer_segments/profession-segments-and-relationship-model.md` and `customer_journey/self-employment-journeys-it-and-doctors.md` | IT and doctor variants reuse relevant sections under the professional idea. |
| `deep_dives/2026-09-11-segment-pain-deep-dive.md` | Cyber card and relevant personal/professional cards link individual sections with scope limitations. |
| `strategy/annex-c-broker-succession.md` | Broker succession operating-path card. |
| `strategy/current-recommendation.md` | Retain as explicitly dated historical source; remove any implication it competes with root README. |

Abbreviated `customer_segments/`, `customer_journey/`, `pain_points/` and `deep_dives/` above remain under `market_research/`. This is an additive routing map, not an evidence relocation map. New runs use existing output conventions; the run manifest gains optional `idea_ids`/`variant_ids` references. One cross-language run can support several cards. A reference must identify the relevant passage/record and applicability; assigning a whole report to a card does not make every included source relevant.

## State and executable boundary

Keep the current project stage machine authoritative for existing project state. The idea registry does not invent independent passed stages. All migrated cards start with explicit “candidate validation not assessed” unless a scoped assessment is available; existing global conditional passes cannot be copied as candidate passes.

Before implementing candidate commitment workflows, extend routing to accept a candidate ID and require the referenced segment/journey/pain evidence to cover that candidate. Store that assessment in the existing stage contract, keyed by candidate ID, rather than maintaining a second complete manifest per dossier. A commitment route lacking candidate scope must fail closed when the workspace contains competing candidates. Record overrides with candidate scope. Focused research and navigation need no new gate.

This is a necessary tooling change, not an enforcement claim about today's router: `route_workflow.py` currently reads one project pain manifest, and `workspace.py` assumes evidence under `market_research/pain_points/`. Keeping that storage avoids wholesale path-validator changes. Before candidate-aware admission exists, this structure improves reading only; it must not advertise safe independent branch execution.

## Migration and rollback

1. Inventory files and inbound references; capture hashes of raw evidence, run records and frozen baselines. Projects are gitignored according to the existing consolidation record: Git is not the rollback plan.
2. Back up the affected README/manifests outside their active paths and record an additive path map. Draft cards from audited existing text, labeling old conclusions and contradictions rather than resolving them by filename dates.
3. Reconcile one portfolio recommendation in README; preserve material prior decisions under `strategy/decisions/`. Keep research blockers and controller summary consistent without changing gate outcomes.
4. Validate unique IDs, parent references, target paths, current-summary consistency, source applicability, and unchanged protected hashes. Test lookup of English, Chinese, motor and cyber from the root within two clicks.
5. Roll back by restoring the recorded README/manifests and removing only files listed as additions. Original evidence does not move.

## Trade-offs and growth trigger

This solves findability quickly and preserves tool compatibility. It adds some curated writing and a small index, but cannot make the underlying stage-oriented file browser itself idea-oriented. Cards can become stale; generation handles repeated metadata, while a substantive-follow-up rule requires updating the affected card and root comparison together. A broken reference validator cannot verify that prose correctly reflects evidence.

If several ideas enter independent concurrent pilots with different owners, budgets and schedules, promote selected ideas to separate workspaces using an explicit lineage record and evidence references. Do not create independent full venture trees for every language variant during exploration. This option is strongest when the founder still has one opportunity investigation and wants to understand the alternatives before choosing.
