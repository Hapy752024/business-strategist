> Archived draft. Relative links were rebased for this archive location; the proposal text is retained.

# Two ways to make the insurance investigation understandable

Design review, 13 September 2026. Existing research was inspected; its market conclusions were not revalidated. No insurance-project files have been reorganized.

The complaint is supported by the files: **the output hierarchy tells you what kind of work the agent performed, but not which possibility the work belongs to or what you currently think about that possibility.** There are 376 files, including 130 Markdown files. The missing concept is a durable, visible investigated idea with its own scope, current interpretation and links to evidence.

The answer should preserve one German-insurance umbrella while making its alternatives explicit. Chinese-speaking insurance, English-speaking insurance and discount motor must be directly visible. They do not have to become three companies, three copied evidence stores or three independent brands.

## What is wrong today

| Finding | Evidence in the actual workspace | Consequence |
|---|---|---|
| Organization follows research stages | 322 files in `market_research/`, 51 in `strategy/`; idea-specific material spread across intake, segments, annexes, pain runs and deep dives | You reconstruct each idea manually. |
| Languages lack direct entry points | English/Chinese share multilingual reports and comparisons | A meaningful investigated alternative looks like an incidental subsection. |
| Several different concepts coexist | Language variants, IT/doctors, motor MGA, cyber, retirement, Surelius and register mail | A folder per keyword would mix businesses, audiences, capabilities and channels. |
| Current and historical guidance compete | README retains old scorecard/action plan beneath corrections; `strategy/current-recommendation.md` still looks current | A reader or agent can pick up an outdated instruction. |
| Status is project-wide | One research manifest, multiple historical next actions; a conditional pain pass with an explicit synthesis gap | The folders cannot express independently reviewed readiness of each alternative. |
| Operational links already have drift | Nine missing relative targets in a five-document sample | A later migration must repair and verify links, not just preserve filenames. |

Three previous workspaces were deliberately consolidated here on 11 September. Their shared history should remain connected. Research is gitignored, so any later migration needs a filesystem backup and a reversible path map.

The [local findings](../local-findings.md) map the actual investigated branches to their source files. The [inventory](../workspace-inventory.json) records every current file and its SHA-256 baseline; the [sample link audit](../sample-link-audit.json) is explicitly partial.

## What comparable agents contribute

| Public agent workflow | Relevant pattern | What it does not establish |
|---|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md) | Umbrella roadmap with separately scoped sub-features; decomposition has overhead | Business evidence applicability or per-language validation |
| [Spec Kit scope selection](https://github.com/github/spec-kit/blob/main/docs/guides/monorepo.md) | Explicit project/feature selection; invalid destinations do not silently fall back | Compatibility with this repo's current project-only router |
| [BMad planning paths](https://docs.bmad-method.org/cs/plan/choose-a-planning-path/) | Different questions warrant different, proportionate planning artifacts | A demonstrated hierarchy for overlapping venture hypotheses |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher/blob/main/README.md) | Bounded research reports remain useful outputs of individual runs | A report being the same thing as a durable business idea |

All references retrieved 2026-09-13. These are three implementation families, not four independent comparables. The proposed layouts and evidence contracts are our design inferences from these patterns and the local defects. [External-pattern notes](../external-patterns.md) preserve retrieval limits. Firecrawl returned HTTP 402; the source material came from the already-issued web-search batch.

## Option A: an idea library over the existing research folders

The idea folders contain readable, current dossiers. The existing research folders continue to hold source reports, evidence and new runs. You browse by idea; agents preserve the current evidence storage conventions.

```text
german-insurance-opportunity/
├── README.md                         # current comparison of alternatives
├── ideas/
│   ├── index.json                    # identities and relationships
│   ├── personal-insurance-decisions/
│   │   ├── brief.md
│   │   ├── english-speaking-residents.md
│   │   ├── chinese-speaking-residents.md
│   │   └── japanese-and-korean-comparisons.md
│   ├── professional-and-personal-cover/
│   │   ├── independent-it-consultants.md
│   │   ├── doctors.md
│   │   └── arabic-speaking-doctors.md
│   ├── discounted-motor-cover/brief.md
│   ├── cyber-readiness-and-placement/brief.md
│   ├── retirement-decision-support/
│   │   ├── self-employed.md
│   │   └── age-55-plus.md
│   ├── broker-portfolio-acquisition/brief.md
│   └── related/                      # Surelius, simulator, register-mail links
├── market_research/
│   ├── manifest.json                 # one authority, scoped idea assessments
│   └── ...                           # existing stage folders and evidence
└── strategy/decisions/               # dated history and corrections
```

Every dossier answers: **What is this? What did we investigate? What did we learn and not establish? What is the current disposition? What would change it? What comes next?** The root table links directly to English, Chinese and motor, rather than making you expand a parent category to discover them.

The revised design stores candidate narrative/status fields in `idea_assessments[ID]` inside the research manifest and generates dossiers and comparison rows from them. The identity index does not duplicate mutable status. This prevents competing summaries, but makes authoring less convenient: narrative lives in JSON and needs an update/render command.

Example: continuing Chinese research writes a scoped run under the existing `market_research/pain_points/runs/`, updates only the Chinese assessment, and refreshes its dossier and the root table. Motor's assessment and evidence remain unchanged. Shared findings are updated only through explicit reviewed corrections.

**Strength:** less disruption to existing storage and historical links; good for understanding the corpus and continuing bounded research.

**Weakness:** opening an idea folder does not reveal all of its underlying files. It is a curated view over stage-based storage. Scoped writing, rendering, correction handling and admission still require development. The central manifest grows and serializes updates. This is not a no-code fix, and a lower total engineering cost has not been demonstrated.

**Execution limit:** the proposed first implementation supports scoped desk research, evidence review and recruitment planning. Independent full stages and downstream execution are explicitly unsupported until their scoped contracts exist. Displaying an assessment cannot authorize a launch.

Full contract, file mapping and scenarios: [revised proposal A](../round-2/proposal-a.md).

## Option B: physical research cases inside the umbrella

Each separately investigated case owns its current dossier, future research and research state. Shared and historical evidence stays at the umbrella level and is referenced. A case is an investigation, not automatically another business.

```text
german-insurance-opportunity/
├── README.md                         # umbrella comparison and owner decision
├── cases.json                        # identities, facets and relationships
├── cases/
│   ├── personal-cover-english/
│   ├── personal-cover-chinese/
│   │   ├── README.md                 # current Chinese-case interpretation
│   │   ├── market_research/
│   │   │   ├── manifest.json         # this case's state
│   │   │   ├── customer_segments/
│   │   │   ├── customer_journey/
│   │   │   ├── pain_points/runs/
│   │   │   └── solution_alternatives/
│   │   └── strategy/                 # only as actual work requires
│   ├── it-professional-and-personal/
│   ├── doctors-professional-and-personal/
│   ├── arabic-employed-doctors/
│   ├── discounted-motor-mga/
│   ├── cyber-insurability-precheck/
│   ├── self-employed-retirement/
│   ├── retirement-55plus/
│   └── broker-portfolio-acquisition/
├── market_research/                  # common and frozen historical evidence
│   ├── evidence-corrections.jsonl
│   └── ...
└── strategy/                         # umbrella decisions and shared concepts
```

Start dormant cases with only a dossier and minimal state; do not generate a full empty workstream tree. The expanded Chinese subtree above shows where actual future outputs would go.

Keep the case list flat and use relationships to group it in the root comparison. This avoids forcing Arabic doctors under either “languages” or “professions.” Japanese/Korean comparisons remain directly discoverable entries pointing to shared work; a separate case is optional until separately resumed. Broad personal cover retains BU and sickness-income findings as well as health decisions.

Example: continuing Chinese research resolves the Chinese case, reads its own next action and evidence assessments, and writes under `cases/personal-cover-chinese/`. Its manifest advances independently. The root comparison refreshes; motor's files and state remain unchanged.

**Strength:** the clearest physical organization for ongoing investigations. Each case has a natural future output destination and can eventually progress independently, while retaining a connected umbrella comparison.

**Weakness:** current tooling recognizes project roots, not nested cases. The scope resolver must reach routing, collection, stage updates, resume/discovery, locking, overrides and downstream handoffs. More cases mean more state and explicit shared-evidence review. This requires an infrastructure change, not simply moving folders.

**Execution limit:** independent case progression becomes possible only after that implementation. No existing project-level conditional pass transfers to a new case. Selecting a case for investigation still does not authorize launching it.

Full contract, actual-file treatments and migration sequence: [revised proposal B](../round-2/proposal-b.md).

## What both designs must preserve

| User question | Required answer in either layout |
|---|---|
| What did we investigate for Chinese speakers? | A directly linked scoped dossier, with unequal/limited coverage visible. |
| Is English the preferred idea now? | One current scoped disposition; old English-first instructions visibly marked historical at their original entry points. Conflicts stay `needs_reconciliation` until reviewed. |
| Did we reject discount car insurance? | The exact investigated motor-MGA mechanism and recorded constraints, not an invented rejection of every discount model. |
| Where do Arabic doctors belong? | One case/dossier with language and profession relationships and shared source links. |
| Does a corrected source affect other ideas? | A correction record identifies affected evidence uses; related conclusions become review-required until reassessed. |
| Can I revisit something parked? | Parked cases remain visible with reasons and reopening conditions. |

Both designs retain original evidence and register its uses by source/record or section. Corrections preserve the old artifact, identify consumers and mark affected interpretations stale. A digest alone cannot do this: an interpretation can be wrong even when its source bytes never changed. Dependent findings must declare their sources; no automatic discovery of all semantic dependencies is promised.

On resume/admission, compare reviewed correction revisions before relying on an assessment. This prevents an interrupted summary refresh from leaving outdated guidance actionable. A new cyber case cannot inherit validation from earlier personal-insurance research. These are proposed implementation requirements, not features verified in the current agent.

## Which I would choose

**For the repeated, separate investigations described in this request, B is the stronger long-term target.** It makes an idea the natural unit for both reading and future work. A is a credible alternative when preserving existing storage and supporting bounded follow-ups matters more than independent case progression.

Do not adopt A merely because it sounds like “just an index.” The revised A also requires scoped state and rendering machinery. If independent case progression is expected soon, implementing A and then retrofitting B could duplicate work. Conversely, if the task is chiefly to make existing findings readable, B's lifecycle machinery may be unnecessary.

In either option, keep `README.md` as the current umbrella comparison, not a chronological pile of follow-up summaries. Candidate-level interpretation stays scoped to that candidate: A stores it in its assessment and renders the brief; B authors it in the case README. Material previous decisions belong in dated history, accessible from both the candidate and umbrella.

## Later migration, if selected

1. Back up the local-only project, inventory evidence hashes and classify each existing file as retained, moved, newly synthesized or unresolved. Preserve frozen runs and the earlier consolidation map.
2. Reconcile scope and document authority without inventing a new business winner. Keep uncertain status explicit. Ensure English/Chinese labels do not erase BU or sickness-income investigation.
3. Implement only the selected option's resolver, state and output contract before enabling scoped writes. Reuse current controls; no new agent framework is necessary.
4. Trial English, Chinese and motor plus one shared-source correction. Repair known broken links and validate all affected local paths/anchors, revisions, unrelated-state preservation, gate non-inheritance and rollback.
5. Extend to the remaining reviewed branches only after the trial. Do not recreate archived projects or copy shared raw evidence merely to make folders look self-contained.

No relocation or code implementation was performed in this review.

## Transparent review record

Three proposal agents worked independently in Round 1. All initially preferred a reader library. Root asked B to develop a serious physical-case alternative, and the independent judge explicitly rejected counting A and C as two separate options.

| Cross-pollination | Resulting change |
|---|---|
| A's visible language/profession variants → B | English/Chinese, Arabic doctors, 55+ and broker acquisition became explicit destinations. |
| B's identity-only registry → A/C | Mutable status stopped being independently maintained in an index and a brief. |
| C's idea/facet/variant distinction → A/B | Language, customer problem, operating path and channel no longer imply separate companies. |
| Judge's correction/resume challenge → A/B | Both added actual source-consumer review and Chinese-only state/write contracts. |
| C's final interruption/dependency challenge → A/B | Stale views and declared indirect evidence dependencies became explicit, with no claim of automatic semantic discovery. |

Round 1 scores were A **79**, B **80**, C **83**; none passed because key design blockers remained. Scores are weighted reviewer judgments, not benchmark results. Round 2 retained A and B as finalists while C stress-tested both.

Review artifacts: [review brief and rubric](../review-brief.md); [initial A](../round-1/proposal-a.md), [B](../round-1/proposal-b.md), [C](../round-1/proposal-c.md); [Round 1 judge](../round-1/judge.md); [revised A](../round-2/proposal-a.md), [B](../round-2/proposal-b.md); [C's comparative stress test](../round-2/cross-review-c.md). The final judge verdict and verification results are appended after review completion.
