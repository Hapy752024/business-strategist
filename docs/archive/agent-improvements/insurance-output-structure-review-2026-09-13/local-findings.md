# Local evidence for the output-structure review

Inspected 2026-09-13. Paths in this document are relative to `projects/german-insurance-opportunity/` unless stated otherwise. This is an organization audit, not renewed endorsement of the market claims in these documents.

## Where the investigated possibilities actually live

| Possibility or dimension | Concrete existing trail | Structural implication |
|---|---|---|
| Personal insurance decisions | `strategy/intake/ideas/idea-1-personal.md`; `strategy/annex-a-personal-insurance.md` | Parent hypothesis covers consequential health/income decisions; language is explicitly a subsegment. |
| Chinese / Mandarin speakers | `market_research/customer_segments/2026-06-multilingual-segments-and-journey.md`; `market_research/customer_segments/surelius-and-language-segments.md`; `strategy/language-market-scenarios.csv` | Deserves a visible investigated branch; it is currently embedded in multilingual material. Do not equate nationality population scenarios with a verified customer segment. |
| English speakers | Same segment documents; `strategy/current-recommendation.md`; September 11 segment deep dive | Its historic default priority and later reopening must be visible separately from a current business decision. |
| Japanese / Korean comparisons | `strategy/annex-a-personal-insurance.md`; `strategy/progressive-advice-language-markets-and-coverage.md`; four-language competitor run | Preserve unequal source coverage rather than give every language the same apparent evidence maturity. |
| Arabic-speaking doctors | `strategy/arabic-brokerage-assessment.md` | Crosses language and profession: a rigid one-parent business taxonomy is inadequate. |
| Combined professional and personal cover | `strategy/intake/ideas/idea-2-professionals.md`; `market_research/customer_segments/profession-segments-and-relationship-model.md` | Distinct relationship proposition, with professional cohorts as investigations. |
| IT consultants and doctors | `market_research/customer_journey/self-employment-journeys-it-and-doctors.md`; July discovery run | Related but separately assessable triggers and access; shared report must remain traceable from both. |
| Discount motor / motor MGA | `strategy/intake/ideas/idea-3-motor-mga.md`; `strategy/annex-b-motor-mga.md`; motor-specific pain and competitor runs | Clearer dedicated trail already exists. Historical MGA stop/park judgments must not become rejection of every possible discount-car-insurance model. |
| Cyber insurability / readiness | `market_research/deep_dives/2026-09-11-segment-pain-deep-dive.md`; challenge review | Emerging branch in a multi-topic report; it has no independent current research manifest. |
| Retirement / self-employed / 55+ | `market_research/deep_dives/2026-09-11-retirement-55plus-selfemployed-register-mail-channel.md` | Separate candidate, segment and exclusion questions are bundled in one report. |
| GKV/PKV lifetime simulator | September 11 segment deep dive and README | Could be a shared capability or a distinct commercial hypothesis; classification requires an explicit scope decision, not an automatic new venture. |
| Broker succession / portfolio acquisition | `strategy/annex-c-broker-succession.md`; `market_research/deep_dives/traditional-broker-acquisition-and-portfolio.md` | Alternative entry/operating path merits discoverability without pretending it is a language segment. |
| Register mail | September 11 retirement/register-mail deep dive and README | Described as a channel, with claims corrected in the latest narrative; link to applicable ideas rather than rank as a standalone business. |
| Surelius | `strategy/surelius-personalised-why-and-simulation.md`; `strategy/surelius-pilot-mvp-brief.md`; June pain-point material | Shared product/delivery thesis crossing customer hypotheses. |

This is a substantive branch inventory from entry documents, named analyses and key follow-ups, not a claim to have audited every assertion in all 130 Markdown files. Smaller mentions should remain discoverable as related investigations without automatically creating empty case trees.

## Authority and navigation findings

- README is 96 lines but contains several chronological correction layers, a superseded scorecard and an older action plan. Length alone understates its interpretation burden.
- `strategy/current-recommendation.md` and annex banners still present historically current instructions. A status reconciliation policy is necessary even if no evidence moves.
- `market_research/manifest.json` has one shared stage history and different historical next actions. It cannot directly answer “what is the Chinese case's current status?”
- Stored `problem_validation` is passed/conditional_pass with a pain-synthesis gap and a layout-migration backfill event. This review does not change or reinterpret that historical gate into candidate validation.
- `project-manifest.json` has no blockers; the research manifest has three. Track status and summarized research readiness need clear authority and derivation.
- The September 11 consolidation map records that three overlapping projects were merged here and their originals archived. Reversing that organizational intent without a portfolio relationship would reintroduce fragmentation.

## Sample link check

Checked target existence for Markdown links in five central documents: README, historical current recommendation, personal annex, motor annex, language assessment. Nine relative targets were missing. For example, the personal annex links `player-directory.md` relative to `strategy/`, but the current directory file is under `market_research/solution_alternatives/`.

`sample-link-audit.json` records every sampled failure. This is not an exhaustive link audit and does not check anchors or external sites. No links were repaired in this design review.

## Current implementation constraints

- Repository `references/workspace-lifecycle.md` establishes one venture root, one research manifest, fixed workstream destinations, root README as the current executive narrative, and preservation of frozen evidence paths.
- Repository `scripts/route_workflow.py:pain_gate_state` accepts a slug, rejects symlinked gate components, and reads only the project's `market_research/manifest.json`. It has no candidate argument or candidate applicability check.
- Repository `scripts/project_workspace.py` controls project/workstream links; its track manifests remain authoritative for their own stages. Directory nesting does not automatically make a new recognized research scope.
- Research is excluded from Git tracking; later migration needs a local backup and reversible manifest/path changes.

Both designs must separate a founder's view of alternatives from the agent's authority to advance them. The distinction should not appear as technical jargon in the founder's primary comparison table.
