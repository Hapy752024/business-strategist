# VoC and customer-needs discovery: implementation plan

Date: 2026-09-16. Status: core implementation delivered and adversarially reviewed; full research-quality release evaluation remains incomplete. See [implementation-report.md](implementation-report.md) for delivered changes, tests and remaining acceptance work. No third-party dependency was installed.

## Objective

Make discovering and understanding customers the agent's primary capability: explain who is trying to accomplish what, in which circumstances, how they currently do it, where it succeeds or fails, and what remains unknown. Every consequential finding must be traceable to reviewed experience. The outcome is better research and better decisions, not a larger collection of reviews or a sentiment dashboard.

The seven reproduced review findings are the initial repair backlog. Closing them alone is insufficient: the upgraded workflow must also improve source discovery, episode extraction, qualitative analysis, customer-needs synthesis and selection of the next investigation. The design retains mandatory topic-led discovery and adds entity-led feedback whenever verified competitors, substitutes or analogs exist.

Research rationale and the open-source shortlist are in [open-source-research.md](open-source-research.md). Repository licenses, code paths and activity were checked on the date above; actual packages have not been installed or benchmarked.

## The research contract

Every substantive discovery or needs study produces a coherent research pack:

1. Research questions, scope and sampling plan: requested markets/languages, customer roles, relevant journey stages, known and unknown entities, accessible source families and decision-changing unknowns.
2. Discovery and coverage ledger: planned and executed queries, source candidates and review outcomes, attempted captures, retrieved/reviewed/accepted counts, failures, fallback routes and missing perspectives.
3. Source-linked experience ledger: distinct speakers and episodes, original wording and translations, observations, context and review decisions. Supplier replies remain separately attributed.
4. Customer-needs map (U): independent outcomes, role, trigger, constraints, current alternatives, observed behavior, consequences, contrary evidence and unresolved motivation.
5. Solution-requirements map (R): evaluation/use conditions, actual solution performance and supported U links; operational requirements can retain an unknown motivational root.
6. Segment/journey comparison and confidence assessment: where a finding applies, where it does not, whether alternatives already satisfy it, and whether support concerns occurrence, unmetness, importance, switching or payment.
7. Next-investigation brief: the unanswered question, why it matters, the appropriate method and the evidence that could change the conclusion.

Unknown values are valid outputs. Neither a review count, a cluster, star ratings, a feature request nor a supplier promise establishes a customer need by itself. Customer-stated outcomes and analyst interpretations remain distinct. A need can be important and already satisfied; report both.

## Initial defects and their closure evidence

| ID | Confirmed weakness | Implementation change | Required acceptance scenario |
|---|---|---|---|
| F1 | Keyword classifications permanently exclude genuine local forum voices | Preserve automated source/voice suggestions separately from reviewed classifications; permit evidence-backed correction of heuristic labels | Firsthand local posts containing `Erfahrungen`, `best service`, or an insurance-provider reference can be accepted after source review; actual supplier text cannot be accepted merely by changing a label |
| F2 | Generic entity web/forum records lack the lane/locator required for synthesis | Route targeted captures through a shared reviewed-source binding; write exact entity, locale, source family and locator to each captured observation | An unfamiliar local review site and an external forum pass discovery, capture, review and U/R synthesis through the ordinary CLI without manual record repair |
| F3 | Topic coverage passes with a whole requested market missing | Add topic-specific coverage cells keyed by locale and the relevant job/role/source/query intent; retain them through finalization | A two-market request with evidence from one market reports the second as missing; it cannot claim two-market coverage |
| F4 | One unavailable source blocks all useful synthesis | Separate execution completeness, coverage gaps and claim-specific evidential support; permit scoped/provisional outputs | A blocked Facebook source remains visible while supported findings from other sources can be reported; cross-source or cross-market claims lacking support remain blocked |
| F5 | Pain-first truncation removes contrary cases from interview preparation | Select a reasoned set of distinct episodes, jobs and perspectives, including material counterexamples | Eight pain records cannot silently crowd out the one materially different successful alternative or non-adopter; omissions and selection reasons are recorded |
| F6 | Fixed confirmation/refutation rules contradict the tracker | Replace fixed-count promotion/demotion throughout instructions and generated artifacts with hypothesis-specific criteria and contextual interpretation | Five painful incidents plus one successful alternative leads to contextual comparison, not automatic validation or erasure of the five incidents |
| F7 | Aggregate weak/strong labels choose research methods | Select methods according to the unresolved question, access and useful evidence | Strong public pain with an unknown buying process routes to interviews; weak coverage caused by absent local sources routes to better discovery |

F1 corrections apply only to provisional classifications. A reviewer must identify the actual source and author context and cite the relevant content; a known company reply does not become customer voice. All reviewed observations remain reversible to unresolved/rejected without editing original captures.

## Broader capability improvements

### A. Discovery that follows customers and their jobs

- Start from customer language, circumstances, triggers, jobs, desired outcomes and existing alternatives. Include successful journeys, positive experiences, non-adoption, switching and exit queries alongside pain queries.
- When the segment is unknown, discover plausible roles and jobs before narrowing. Distinguish user, buyer, payer, decision-maker, intermediary and supporting person where relevant; record perspectives separately from those roles.
- Generate native-language query variants per requested locale. Cover forum and Facebook discovery explicitly where relevant, as well as local review ecosystems. Find unknown competitors through topic discovery and revisit the entity-feedback plan when new alternatives appear.
- Schedule representative query intents across relevant cells before spending all retrieval on the first seed. Track actual executed queries rather than treating a generated plan as completed coverage. Expand using new customer vocabulary, surprising alternatives and missing perspectives.
- Use multiple appropriate search/capture routes. Existing paid API permission remains unlimited; neither low credits nor provider unavailability is absence evidence. Stale validation means recheck the relevant route, not that the provider is broken. Reconcile outdated paid-approval instructions with the standing authorization.
- Plan sampling within each source, not just between sources. Record requested and actual sort order, rating/text filters, time windows, product/version where available, pagination depth, returned versus accessible totals and provider-selected subset limits. Where rankings or a recent event dominate, make a reasoned attempt to retrieve contrasting relevant slices or explicitly limit the conclusions. Do not impose equal star-rating quotas or imply representativeness. Preserve invited/transaction-linked/aggregated review provenance and possible solicitation or duplication bias.
- Identify digitally underrepresented or inaccessible groups as coverage limits and research questions. Do not manufacture online voices or assume an online sample represents them.
- Record stopping reasons: questions answered within scope, new retrieval yielding duplicates, unresolved access, or a different research method offering better information. A tool-call target or fixed record quota is not a quality criterion.

### B. Capture experiences, not undifferentiated pages

- Search snippets discover sources. Extract and inspect the relevant full content before relying on an account; remove the current dependence on the first 1,500 characters of a page.
- Split multi-author threads and review pages into speaker/episode units, with thread and reply context. Keep supplier replies and quotations of another person separate from the speaker's own experience.
- Preserve original text, stable document/episode IDs, source URL, available publication time, retrieval time, requested locale, observed language and evidenced author geography. A storefront or query locale is not proof of the author's residence.
- Retain the source-sampling record with each observation. Separate transient outages, resolved historical defects and version-specific experiences from ongoing needs; compare relevant slices before declaring a need dominant or exhaustive. An API returning a handful of ranked reviews remains a restricted view even when the request succeeds.
- Extract explicit triggers, actions, alternatives, outcomes, consequences and evaluation criteria with supporting text spans. Preserve negation, chronology, conditional statements and unknown motivations. Translation links back to the original passage.
- Track documents, observations, incidents and independent people separately. The same observation found through both topic and entity searches has multiple discovery memberships but is counted once. Cross-site identity remains unknown unless evidenced; plausible duplicate clusters must not inflate independent-customer counts.
- Prototype LangExtract for structured extraction and Trafilatura for recoverable HTML content. Both operate behind the existing collection/review flow and must retain author/reply boundaries; neither is sufficient on its own to interpret a forum.

### C. Qualitative analysis that produces useful needs

- Introduce a small, evolving codebook with definitions, inclusion/exclusion examples, source-linked instances and revision notes. Combine research-question codes with new codes emerging from the material. Avoid a compulsory industry taxonomy.
- Code multiple motives and needs per experience when supported. Preserve rare but consequential needs and contradictory experiences instead of letting large clusters dominate.
- Compare cases across roles, contexts, journey moments and alternatives. Explain differences before merging them into a single theme. Pair every proposed pattern with its supporting observations, contrary observations and missing comparisons.
- Give each U need a role/context, desired outcome, current approach, satisfaction/unmetness evidence, consequences, source IDs, inference rationale and a bounded assessment. Separate functional, emotional and social outcomes only when the account supports them.
- Give each R requirement a use/evaluation episode, acceptable outcome, actual performance evidence, U links or unknown root, applicability and a next test. A requested feature remains an implementation suggestion until its underlying condition is understood.
- Preserve claim-specific confidence: source authenticity/role, target fit, independence, contextual coherence, recency, contrary evidence and coverage. Unknown dimensions remain unknown. Repeated mentions do not automatically establish prevalence, importance or willingness to pay.
- Replace the blanket confidence/count thresholds in the existing claim validator with claim-type-aware checks. One well-evidenced firsthand incident can establish that incident's occurrence without establishing prevalence or an unmet market; many weak records cannot turn an unsupported buying motive into a supported one. Reuse the current independence computation conservatively, keeping unknown author independence distinct from zero observed incidents.
- Rank the next learning priorities using consequence, observed unmetness, decision relevance and uncertainty. Show the reasoning; avoid a single opaque score or ranking purely by mention volume.

### D. Coverage and synthesis with explicit limits

Use three separate concepts:

| Concept | Meaning |
|---|---|
| Execution status | Every planned relevant query/source has an outcome: attempted, not applicable with reason, failed, inaccessible or still pending |
| Coverage status | What the collected material covers across markets, roles, perspectives, journey stages and source families; missing cells remain visible |
| Claim status | Supported within stated scope, provisional hypothesis, unresolved, contradicted or unsupported |

A completed attempt is not complete market coverage. A missing source need not block unrelated findings. A complete study with zero accepted customer voice must produce an explicit insufficient-evidence result, not invent U/R items to satisfy a minimum count. Known entities with no accessible feedback must not prevent reporting qualified topic findings.

The validator checks provenance, counts, reviewed scope, required reasoning fields and contradiction references. It cannot establish semantic truth merely by accepting JSON. Consequential interpretations receive semantic review against the original episodes. Business-validation gates remain separate from publication of provisional research.

### E. Research questions drive interviews and follow-up

- Select interview seeds for relevant differences and uncertainty: successful and failed workarounds, current and former users, prospective users/non-adopters, and materially different contexts where evidenced. Do not impose arbitrary equal quotas.
- Build a neutral guide around the participant's own chronology before introducing evidence-derived probes. Retain both E evidence probes and H clearly labelled hypotheses.
- Choose further source research for missing coverage/current facts; interviews or observation for motivations, context and handoffs; usability/performance studies for R requirements; and separately authorized behavioral tests for switching/payment hypotheses.
- Reintegrate actual interview observations into the same episode/need/requirement model. Preserve how new evidence confirms, narrows or contradicts previous findings. Retire unsupported conclusions rather than silently dropping them.
- Keep the unpaid recruitment preference. This implementation plan does not launch recruitment, advertising or a live pilot.

## Implementation sequence and file ownership

Deliver in reviewable vertical increments. Keep existing workspace paths and current research intact; new fields receive explicit versioning and legacy records remain visibly incomplete where context cannot be recovered.

| Phase | Deliverable | Main files / boundaries | Exit condition |
|---|---|---|---|
| 0 — Baseline | Freeze current behavior, seven failure fixtures, evaluation corpus specification and baseline outputs | Existing VoC/interview tests; proposed `evals/voc/`; evidence-scout and market-discovery eval definitions | Known failures reproduced; positive controls pass; scoring and held-out split recorded before changes |
| 1 — Repair the research workflow | Close F1–F7 and remove contradictory instructions | `collect.py`, `plan_customer_feedback.py`, `finalize_customer_feedback.py`, `validate_customer_voc_synthesis.py`, `build_interview_kit.py`, shared customer-voice and affected skill workflows | All seven realistic acceptance scenarios pass, including generic forum-to-synthesis and partial-coverage outputs |
| 2 — Improve source coverage and experience extraction | Topic coverage cells, balanced query execution, within-source sampling, full-content and multi-speaker extraction, reviewed binding across providers | `discover_communities.py`, `discover_market_problems.py`, collector/provider routing; proposed focused `voc_observations.py`; evidence schema | Held-out local forums and review pages produce attributable episodes; missing locales/pagination/time windows cannot disappear; a recent outage does not erase onboarding and ongoing-use needs found in other relevant review slices |
| 3 — Improve needs synthesis | Codebook, contextual U/R assessments, contrary cases, independence and scope-aware claims | Shared `references/customer-voice.md`, U/R schema/validator; reuse `build_claim_ledger.py` and `validate_synthesis.py`; proposed focused synthesis helper only where repeated logic warrants it | Decision-relevant outcome/context concepts recovered in the final maps, including a rare but consequential need amid common convenience complaints; no unsupported target-market transfer or invented motivation |
| 4 — Integrate all entry and handoff paths | Same research-quality contract for broad discovery, specific hypothesis validation, known-competitor feedback and interview continuation | Skill catalog/routes, market-problem-discovery, evidence-scout, interview-bridge, customer-perspective-challenger; downstream landscape/risk consumers | Starting from unknown competitors still runs topic discovery and adds entity analysis when discovered; finalizers check actual research artifacts rather than report headings alone |
| 5 — Establish end-to-end quality | Frozen-corpus comparison, live discovery studies and fresh adversarial review | `evals/voc/`, existing test runner; optional promptfoo configuration and review reports | Release criteria below pass; no remaining blocker/significant research-quality findings within audited scope |

Suggested new helpers are local research transformations, not new services. Extend existing claim/independence machinery rather than adding competing ledgers. Source-review sidecars and existing inline `analyst_review` consumers need one consistent reviewed view so acceptance cannot differ by downstream command.

The skill entrypoints should state the core research decisions succinctly and route to concrete method references. Replace current success criteria about maximum tool calls and required headings with outcome-quality criteria. Broad discovery must consume the same shared customer-voice contract as focused validation, without requiring the founder to preselect a segment or competitor.

## Open-source adoption decisions

- **Prototype first:** LangExtract for exact-span extraction, and Trafilatura for HTML recovery. Compare against the current flow on identical source material and languages; retain only demonstrated improvements.
- **Adopt process/data patterns now:** QualCoder/Taguette for coded passages, case comparisons and analytic memos; Argilla for separating model suggestions from reviewed corrections. Existing JSON/Markdown artifacts can implement these patterns without deploying their applications.
- **Evaluate for testing:** promptfoo for repeatable agent evaluations, deterministic assertions and calibrated semantic rubrics. Reuse the existing test infrastructure where equivalent; do not introduce a second mandatory application runtime.
- **Optional later:** BERTopic for navigating a large reviewed corpus. Clusters propose groupings; they do not determine needs, importance, independence or demand. Keep outliers and multilingual distinctions inspectable.
- **Reference only:** Rereflect offers a feedback workflow and correction/evaluation ideas, but the inspected keyword categorizer uses a fixed product-problem taxonomy and defaults unmatched text to a major functionality issue. Do not adopt that classifier as our needs-analysis core.
- Retain existing paid source providers. An OSS extractor does not replace paid access or guarantee capture of Facebook, Google or app-store content. Direct forum/app adapters are added only for a demonstrated missing source capability.

For each adopted dependency, record the exact version/commit, license/notice obligations, compatibility, measured gain and fallback behavior before integration. QualCoder's inspected code is LGPL-3.0-or-later: take conceptual inspiration here; do not casually copy it into the collector. No UI deployment is required by this plan.

## Evaluation and release criteria

### Dataset and comparison

Build an initial 12-case benchmark spanning local consumer services, B2B workflows, consumer software and multi-stakeholder services; at least four languages and three country contexts, including a multilingual-country case. Countries/languages are fixtures, never unconditional skill defaults. Use roughly 20–30 source units per case as an initial annotation workload, expanding when an important quality dimension is underrepresented.

Include forums, local reviews, Google/app reviews, social threads with supplier replies, positive and negative experiences, non-adopters, successful alternatives, mixed author threads, older/current product behavior and inaccessible-source cases. Distinguish synthetic fault reproductions from frozen real-source cases.

Split eight cases for development and four held out by topic/source domain. Freeze capture files, retrieval metadata, prompts, models/settings and expected critical observations. Run baseline and candidate with identical evidence; evaluate live discovery separately so a changed search result is not mistaken for better reasoning. If cases become tuning material, replace the held-out cases.

Domain-informed independent reviewers establish acceptable interpretations, source/role annotations, important distinctions and uncertainty. Before tuning, annotate the distinct decision-relevant outcome/context concepts that the final U/R maps should recover, distinguishing critical concepts from secondary ones and recording why each matters. Multiple valid formulations and justified merges/splits are allowed. Match concepts semantically with supporting context; a generic convenience theme does not count as recovering a specific eligibility or access need. Every omitted critical concept requires a source-supported unresolved status or a defensible exclusion, rather than disappearing. Do not score theme wording against a single preferred prose answer. Automated judges assist; disagreements and consequential claims are adjudicated against sources. Agent-only review is labelled as such and cannot be described as a human gold standard.

### Proposed quality targets

These are engineering acceptance targets to test and calibrate, not researched universal thresholds or population estimates. Freeze the initial thresholds before candidate tuning; disclose any justified changes.

| Dimension | Acceptance target |
|---|---|
| Provenance | 100% of cited quotations resolve to the preserved source passage; every consequential claim has reviewed source IDs and stated scope |
| Role integrity | Zero observed supplier-to-customer promotions in audited accepted evidence; at least 95% precision on held-out source/voice classifications, with per-class denominators |
| Experience recall | At least 90% of independently annotated, decision-relevant episodes recovered from the supplied benchmark documents; inspect losses per language/source |
| Customer-need recovery | Every benchmark-critical outcome/context concept appears in the final maps or has an adjudicated source-supported unresolved/excluded disposition; at least 90% of supported secondary concepts recovered, allowing valid merges/splits. Score this separately from episode extraction and assertion precision, with omissions by role/language/source |
| Discovery coverage | Every requested relevant market/source/perspective cell has an explicit disposition; at least 90% retrieval of the benchmark's known reachable relevant sources under the frozen search setup; no claim of open-web recall |
| Within-source sampling | Sort/filter/time/version/pagination/subset choices are explicit; outage-heavy newest reviews are compared with another relevant accessible slice or conclusions are bounded. A provider-selected handful of reviews cannot stand for the full needs landscape |
| Interpretation | At least 95% of audited asserted need/requirement statements supported within scope; zero unlabelled invented motives, cross-market generalizations or demand/prevalence claims in consequential findings |
| Context and counterevidence | All benchmark-designated recommendation-changing contrary cases retained; important role/journey/alternative distinctions recovered or explicitly unresolved |
| U/R distinction | At least 90% correct distinctions on held-out annotated examples; no forced motivational root for an operational requirement |
| Partial evidence | Missing sources/locales cannot be labelled covered; useful scoped findings remain possible; zero accepted voice produces an honest insufficient-evidence result |
| Follow-up quality | Every recommended method answers a named unresolved question; no fixed-count validation or automatic one-refutation demotion; no silent loss of material interview perspectives |
| Overall usefulness | Independent blind baseline/candidate comparison on the held-out cases demonstrates a material gain in finding useful needs, explaining context and identifying the next uncertainty; no case may introduce a significant research defect |

Report numerators/denominators and slice results; aggregate percentages must not hide a failing language, source family or role. The initial benchmark is a practical release test, not proof of universal performance. Track costs and latency diagnostically; there is no monetary cap or arbitrary maximum tool-call gate.

### Live and adversarial review

Run three bounded live studies in isolated agent-evaluation outputs: one topic with unknown competitors, one with known competitors/apps and one multilingual local-service topic with incomplete online coverage. Preserve actual queries, provider responses and reviewed findings. These are agent evaluations and do not update a venture's validation state or initiate funeral-case research automatically.

For each material implementation increment, use a fresh reviewer after consulting relevant external implementation/method references. Review normal research scenarios, not only crafted fixture failures. Classify findings using the user's rubric:

- Blocker: collection from an unreviewed targeted source or supplier content accepted as customer voice.
- Significant: material distortion of coverage, customer needs or conclusions.
- Minor/out of scope: cryptographic portability, sophisticated local-state tampering, theoretical multi-process attacks and cosmetic architecture changes.

Correct findings, rerun the affected realistic evaluation, and review with a fresh agent until no blocker/significant finding remains within the audited scope. A zero-finding review is necessary but not sufficient: release also requires behavioral and live evidence above. Do not repeat unrelated full-suite tests without a changed boundary or new failure.

## Completion evidence

The final implementation handoff must include: F1–F7 closure evidence; any additional material defects and their dispositions; changed skill/CLI entry paths; frozen-corpus scores and blind comparisons; live study artifacts and access gaps; dependency decisions; and the final fresh-review report. State exactly which languages, source families and paths were tested. Do not call the capability top-tier based only on passing unit tests or reviewer approval.

## Current operational observations

Firecrawl search using the designated HGINVESTOR credential succeeded during this research after a sandbox DNS failure was retried with approved network access. No credit failure was observed. Provider doctor reports many other validations as stale and its optional direct probes encountered sandbox networking limits; these are not confirmed provider outages. Revalidate only the routes needed for the later live benchmarks.

The repository has substantial unrelated in-progress work. Implement against the current working tree with a task-specific baseline snapshot; preserve existing project research and unrelated edits. This plan does not require a worktree migration, new database, service deployment or additional compliance paperwork.

## Plan-review record

The first fresh independent plan review found no blocker and two significant omissions: within-source sampling bias and explicit measurement of customer-need recovery. Both were added to the method, phase acceptance scenarios and release criteria. A second fresh independent reviewer assessed the revised plan, including the claim-type-aware confidence/count checks, and returned **0 Blocker / 0 Significant** on 2026-09-16. Its primary-source checks included GOV.UK research planning/user needs, LangExtract's data model, Trafilatura and promptfoo assertions. It could not independently refetch the Rereflect categorizer or Argilla schema; those code-specific observations rely on the author's successful direct-source retrieval recorded in the companion research note. This is a bounded plan-review verdict only; none of the future implementation acceptance criteria has been demonstrated by these documents.
