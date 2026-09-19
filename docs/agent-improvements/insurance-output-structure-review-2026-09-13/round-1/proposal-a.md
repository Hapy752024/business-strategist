# Proposal A — a founder-facing idea library over the existing evidence store

Round 1, 13 September 2026. Independent local inspection; market conclusions below describe existing documents, not newly verified claims. No research files moved or edited.

## Diagnosis grounded in the workspace

The workspace groups outputs by research activity, while the founder asks by investigated possibility. The same possibility is distributed across segments, intake, annexes, competitor runs and chronological deep dives. Chinese and English work is particularly difficult to reconstruct because much of it shares documents.

Observed examples (paths below are relative to `projects/german-insurance-opportunity/`):

- `strategy/intake/ideas/idea-1-personal.md` explicitly makes language a subsegment of consequential personal-insurance decisions. `idea-2-professionals.md` combines professional AND personal cover; IT and doctors are comparison branches. `idea-3-motor-mga.md` describes a different business model with carrier/claims dependencies.
- `README.md` prepends September 11 cyber/simulator/pension findings to a September 7 reopening, then preserves a superseded “Blunt conclusion,” scorecard and first-30-days plan. A reader can reasonably mistake old execution instructions for current ones.
- `strategy/current-recommendation.md` still calls itself current and gives English first priority. `market_research/customer_segments/surelius-and-language-segments.md` contains both an English-first introductory banner and later instructions to remove default English priority. This is document-authority drift, not just missing folders.
- `strategy/arabic-brokerage-assessment.md` studies Arabic-speaking employed doctors: a language/profession intersection that a strict language tree would split from related doctor evidence.
- `strategy/decisions/2026-09-11-workspace-consolidation-map.md` records the merger of three earlier projects. Restoring separate projects for every language would recreate fragmented history. It also states research workspaces are gitignored; reversibility cannot depend on Git.
- `market_research/manifest.json` has one global stage, `synthesis`, and `problem_validation: passed` with `gate_result: conditional_pass` and an unsynthesized-pain-ranking gap. `customer_profile` is pending. `project-manifest.json` has empty blockers while the research manifest lists three. Neither represents readiness separately for Chinese, motor, cyber and professionals.

## Design

Keep one venture. Add a prominent, small idea library that contains the current scoped brief for each candidate and links into the evidence store. Keep canonical runs and stage output paths unchanged. The root README remains the sole **portfolio-level** executive narrative; an idea brief is authoritative only for its named candidate, not another competing portfolio recommendation.

```text
german-insurance-opportunity/
├── README.md                         # current portfolio map + next owner decision
├── ideas/
│   ├── index.json                    # stable IDs, relations, state and brief paths
│   ├── personal-insurance-decisions/
│   │   ├── brief.md                  # shared customer/job hypothesis
│   │   └── variants/
│   │       ├── english-speaking-residents.md
│   │       ├── chinese-speaking-residents.md
│   │       └── other-language-comparisons.md
│   ├── professional-and-personal-cover/
│   │   ├── brief.md
│   │   └── variants/
│   │       ├── independent-it-consultants.md
│   │       └── doctors.md
│   ├── discounted-motor-cover/
│   │   └── brief.md
│   ├── cyber-readiness-and-placement/
│   │   └── brief.md
│   ├── retirement-decision-support/
│   │   └── brief.md
│   └── broker-portfolio-acquisition/
│       └── brief.md
├── market_research/                  # existing stage folders, raw runs unchanged
├── strategy/
│   ├── decisions/                    # dated decision history, scoped by idea IDs
│   └── ...                           # existing economics, intake and playbooks
└── project-manifest.json             # existing controller
```

The root comparison table exposes **every investigated candidate and material variant**, including Chinese and English as separate clickable rows even though they share a parent. Columns: candidate, customer/job, proposed model, research state, latest decision, uncertainty, next action. A collapsed parent-only table would fail the user's actual problem.

Use stable human-readable IDs rather than `idea-1`, whose meaning changes when ranking changes. Index fields remain small: ID, kind (`candidate`, `variant`, `channel`, `capability`), parent/related IDs, brief path, evidence paths, last review date, research state, decision state, next action. Tags such as language, profession, trigger and product permit overlaps; they do not create the full Cartesian product of all possibilities.

Arabic doctors appears in the doctors variant with a direct cross-link from other-language comparisons. The English personal decision variant links to the IT variant for the shared self-employment health decision. Surelius is linked as a shared delivery concept, not silently ranked against customer segments. Register mail remains an acquisition hypothesis linked to relevant candidates, not a seventh business. Create a separate candidate only when its customer/job, business model or decision to pursue becomes independently meaningful.

## How existing material maps

| Reader entry | Existing evidence and narratives to reference | Initial state imported with caution |
|---|---|---|
| Personal decisions → Chinese | `strategy/annex-a-personal-insurance.md`; `market_research/customer_segments/surelius-and-language-segments.md`; four-language competitor run; June multilingual materials | Investigated comparison; unequal source coverage; not selected |
| Personal decisions → English | Same shared materials; `strategy/current-recommendation.md`; September 11 segment deep dive | Investigated; historical default superseded/reopened; not selected |
| Discounted motor cover | `strategy/intake/ideas/idea-3-motor-mga.md`; `strategy/annex-b-motor-mga.md`; motor pain run; challenge review | Historical stop/park recommendation; preserve rationale and explicit reopening conditions |
| Professionals → IT/doctors | `strategy/intake/ideas/idea-2-professionals.md`; profession-segment analysis; self-employment journey; July discovery; Arabic assessment | Investigated comparison; no final cohort selection |
| Cyber / retirement | Three September 11 deep dives | Newly prioritized hypotheses; inherited general research is not their validation |
| Broker portfolio acquisition | `strategy/annex-c-broker-succession.md`; traditional-broker acquisition deep dive | Alternative entry route; current founder-fit assessment must be made explicit |

These are provisional metadata imports from existing text, not newly adjudicated business recommendations. Conflicting current claims receive `needs_reconciliation` rather than an invented definitive winner.

## Brief contract and evidence reuse

Each brief answers, in order: What exactly is this idea? Who and what trigger? What was investigated? What did evidence establish versus leave unknown? Which variants overlap? Why retain, park or reject it? What would change that decision? What next?

Include a dated status box with **research state** (scoped, collecting, audited, incomplete) separate from **decision state** (unselected, shortlisted, selected, parked, rejected). A finished report is not a validated idea. Evidence references name source/run and relevant section or record ID; a competitor page may support several briefs without becoming several independent observations. Review quality belongs to the evidence reference; applicability belongs to its use in each brief.

New cross-cutting reports stay where the current workflow writes them and list affected IDs. New brief content summarizes and links; it never copies raw evidence or broad sections of a shared report. The index can generate the root table, but the narrative body remains authored prose with review responsibility.

Do **not** turn the new index into a second executable stage machine. Existing manifests remain execution authority. However, any proposed launch for a specific ID must explicitly show that the existing gate evidence covers that candidate. The current portfolio-wide conditional pass cannot be inherited by new branches. Proper per-candidate gating would be a subsequent, separately scoped workflow change if independent execution becomes necessary.

## Current versus history and migration

Snapshot the existing README into `strategy/decisions/` before rewriting it. Replace appended recaps and old scorecards with one current comparison. Add conspicuous historical/superseded banners to existing recommendation documents and link to the new brief plus dated decision record. Keep historic source timestamps and original claims accessible. Do not move frozen runs or archived merged projects.

Begin with an inventory of narratives, local links and manifest targets; record old-to-new narrative mapping and checksums for evidence. Create the idea library from existing research, then resolve status conflicts explicitly. Because research is local-only, save a filesystem backup outside the active tree before any later approved migration. Verify all links, unique IDs, valid relations, index/brief status agreement, root table coverage and unchanged evidence bytes. A useful acceptance test is a founder opening Chinese, English, motor and professionals from the root and finding status, reasoning and sources in at most two clicks.

Minimum reusable workflow change: update the output/lifecycle contract, add the brief template and optional index schema, and instruct follow-ups to identify affected existing IDs, update their brief and refresh the root comparison. No new skill or provider is needed. Do not create empty variant folders for merely mentioned possibilities.

## Trade-offs and rejection conditions

This design gives a tangible output-folder improvement with limited disruption and keeps shared evidence reusable. It adds another authored summary surface, so drift remains the main risk. An index validator catches structural disagreement, not semantic contradictions; substantive reviews still matter. Keeping technical files in stage folders means an idea's dossier is navigable but not entirely self-contained for file export.

Reject this option if the founder needs separately owned ventures with independent budgets, deliverables and launch gates immediately. In that situation genuine child workspaces may justify the larger schema/router migration. For the present record of overlapping experiments inside one insurance investigation, that cost is premature.
