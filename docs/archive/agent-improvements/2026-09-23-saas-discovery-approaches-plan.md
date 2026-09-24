# Idea validation and customer-problem research: complementary approaches

Date: 23 September 2026. Status: core intent, packet-planning and skill-entry changes implemented; comparative quality evaluation remains pending. Read with the [implementation and skill-scope audit](../audits/2026-09-23-plan-implementation-and-skill-scope-review.md).

## Decision

**Scope clarified by the user:** the agent's research serves two primary outcomes:

- **Validate or challenge the user's idea:** investigate its customer/problem assumptions, actual alternatives, supporting and contrary evidence, and the uncertainties that could change the decision.
- **Understand a customer segment's pain points regarding a topic:** explain situations, tasks, consequences, workarounds, satisfactory experiences and differences within the segment. This can conclude with findings and open questions without proposing a product or business.

The user's question determines the scope. Similar companies in the same or other countries are optional comparison evidence: they can reveal relevant customer experiences, alternatives, mechanisms and failure cases. Their applicability to the target segment must be assessed. Importing ideas or replicating a business from another country is not a default objective; adaptation becomes an objective only if the user explicitly requests it.

Adopt customer-workflow observation, switching research, ecosystem evidence and relevant company-change analysis as complementary methods serving those outcomes. Extend existing skills and contracts. Select methods for the question instead of creating a new permanent agent for every framework or source.

The main improvement is to investigate the same user question from different evidence sources and competing explanations. In exploratory problem research, these may reveal different problem hypotheses; in idea validation, they challenge the supplied hypothesis. Running several agents on the same companies and reviews would give repeated interpretations of the same sample. The planner records this intent and makes selected approaches into separate coordinator-owned work packets; the discovery and validation skill entry instructions now preserve intent and expose that workflow.

The practitioner sources support useful methods. They do not establish a causal success rate for geographical replication, a universal interview quota, or proof that parallel agents outperform a careful single researcher. That benefit must be evaluated.

## What the supplied proposal gets right, and what to change

| Proposal | Assessment and agent adjustment |
| --- | --- |
| Begin with monetized foreign workflows | Do not adopt as a default starting point. Start with the user's idea or segment/topic. Relevant paid offerings, wherever located, may provide comparative evidence; pricing and portfolio membership establish an offer, not profit or demand in the target segment. |
| Reviews and switching research | High value. Add purchase chronology, why customers stayed, who could approve a switch, migration effort and value that must be preserved. Complaints alone do not establish a viable entrant. |
| Monitor pricing/product changes | Useful conditional route. Require a real dated baseline, normalized comparison and affected-customer evidence. A first capture is not a change. |
| Platform marketplaces and agencies | Useful additional sampling frames when they illuminate the customer's task. Verify platform access and delivery feasibility when relevant to the user's idea. Agency testimony is intermediary evidence; several projects may involve one underlying client or bespoke requirements. |
| Founder acquisition reconstruction | Already substantially present. Use when validating commercial feasibility or when the user requests founder lessons; it is not mandatory for a pain-point study. Include failed attempts and contextual limits. |
| Foreign success adapted locally | Adaptation is outside the default objective. Study comparable companies to inform or challenge the user's question. Separate headquarters, markets served and evidenced customer locations; a foreign vendor serving the target segment may be an actual competitor. |
| Mobile app stream | Keep conditional and separate from B2B SaaS. Store/date/country definitions and estimated net app revenue must remain visible. Do not infer retention or cohort economics from cross-sectional downloads and revenue. |
| 50–100 companies; 10–15 interviews; weekly checks | Treat as example operating choices, not defaults or validation thresholds. Begin with a small varied sample and expand to resolve a named decision gap. Monitoring cadence follows the event and decision. |
| Buy several intelligence tools | Defer. Use current capabilities first, then select enrichment for a specific unresolved question. No new provider is justified merely by appearing in a source list. |
| Require paid pilots after interviews | Paid commitment can strengthen evidence, but test design should follow the risk. A migration trial, authorized integration spike, procurement check or manual delivery test may be the next useful step. Existing launch/side-effect gates still apply. |

## Primary-source findings that add value

**Test the ability to switch, including organizational authority.** Walling and Reimer recommend challenging a differentiation hypothesis and researching dissatisfaction and acquisition before building. More revealing is Reimer's account of closing Level: personal frustration did not translate into organizational willingness to replace Slack. His later process examined tools he had used and paid for, considered adoption friction, and checked his own hypotheses with others. This supports explicitly distinguishing user, buyer, approver and implementation participants. It also supplies a failed case alongside the successful-founder advice. [Episode 666, 20 June 2023](https://www.startupsfortherestofus.com/episodes/episode-666-entering-a-competitive-market-books-for-saas-founders-and-more-listener-questions-with-derrick-reimer); [Episode 506, 21 July 2020](https://www.startupsfortherestofus.com/episodes/episode-506-shutting-down-and-starting-up-with-derrick-reimer).

**Study the customer's real alternatives.** Dunford distinguishes products discovered by an analyst from alternatives that actually enter the buying decision. Keep spreadsheets, internal labor and doing nothing in the comparison. Keep future competitors as a separate threat set; do not let an exhaustive software directory dictate positioning. [Positioning and Competition, 28 December 2020](https://www.aprildunford.com/post/positioning-and-competition).

**Reconstruct the decision, not just the complaint.** Moesta's method tracks movement from initial struggle through search, choice and use, including attraction to the new option, anxiety and habit. Extend existing experience records and interview questions with observed chronology and barriers. Missing parts stay unknown; do not calculate invented numerical “forces” scores. [Demand-Side Sales 101, undated retrieved page](https://businessofsoftware.org/talks/demand-side-sales-101-bob-moesta-online/).

**Observe vocabulary and trusted recommendations before choosing a solution.** Amy Hoy and Alex Hillman's Sales Safari adds attention to customer language, beliefs and recommendations alongside pain. This can improve native-language queries and reveal where customers seek advice. It is an extension of topic-led customer research, not a separate new evidence system. [Alex Hillman interview, 5 November 2020](https://stackingthebricks.com/podcast/ep42-what-is-sales-safari-with-eteinne-garbugli/).

**Use lived experience as one origin, then corroborate it.** Paul Graham's essay offers an additional route: noticing concrete problems through one's work and experience. Use genuine founder access when supplied, while checking the problem in other target customers. It can coexist with observation-led research; neither founder intuition nor public discussion automatically wins. [How to Get Startup Ideas, November 2012](https://www.paulgraham.com/startupideas.html).

**Narrow differentiation is a testable option.** Lemkin discusses specialist buyers, industries, features and integrations. Use these to generate alternatives, then test their importance, buyer reachability and delivery economics. Do not encode rhetorical multipliers or revenue targets as validation rules. [SaaStr article, undated retrieved page](https://www.saastr.com/how-can-a-saas-startup-survive-in-a-crowded-market/).

## Reuse before adding

| Existing owner/reference | Already covers | Incremental improvement |
| --- | --- | --- |
| `idea-grill`; `market-problem-discovery` | User-idea validation and broad segment/problem research | Preserve the selected intent; select complementary methods and track contributions and blind spots |
| `evidence-scout`; `references/customer-voice.md`; `references/voc-research-method.md` | Topic/entity separation, positive and negative experience, alternatives, uncertainty, source identity | Vocabulary/recommendation observation; fuller switching timeline and decision participants |
| `business-archetype-playbook-researcher` | Named founders, early customers, foreign cases, failed cases, inherited assets and transfer limitations | Conditional early-acquisition/delivery reconstruction that tests the user's business hypothesis |
| `competitive-landscape-builder` | Market competitors, foreign analogs, capability references | Cases selected for relevance to the user's customer/problem question; marketplace and implementation-service evidence; real customer shortlist versus future threats |
| `competitor-monitoring` | Watchlists, snapshots and differences | Change-to-customer-impact hypotheses, dated baselines and explicit evidence of reaction |
| `interview-bridge` | Recent experiences, non-leading interviews, unresolved questions | Switching chronology, authority, migration and why satisfactory alternatives were retained |
| `opportunity-risk-designer`; `references/strategic-positioning.md` | Entrant feasibility, differentiation, tests, build/buy/partner choices | Compare competing explanations and assess business feasibility when requested; check cross-context applicability where external analogs inform claims |
| `saas-fintech-pilot-designer` | Staged product/pilot tests | Early integration/access and migration feasibility tests when these could invalidate the opportunity |

Many supplied recommendations are already written into these owners. The implementation should make them appear reliably in research and decisions, rather than add synonymous instructions.

## Four complementary research approaches

These are selectable ways of investigating a question, not four new skills. More than one can run concurrently when their evidence collection is independent.

| Approach | Starting point and work | Existing owner(s) | Distinct blind spot addressed |
| --- | --- | --- | --- |
| A. Customer workflow | Observe target customers' tasks, consequences, successful workarounds, vocabulary and advice sources without requiring vendor names | `market-problem-discovery`, `evidence-scout` | Needs invisible in startup/product directories; people who do not use software |
| B. Existing alternatives and comparable cases | Examine how the same or a similar customer problem is handled by products, services or manual processes; include relevant companies in other countries. Add founder history when commercial validation calls for it | `competitive-landscape-builder`, `evidence-scout`, conditionally `business-archetype-playbook-researcher` | Existing solutions, satisfactory outcomes and contextual differences that complaint searches miss |
| C. Switching and company changes | Investigate dated price/packaging changes, closures, deprecations or integration changes; find affected customers and those who stayed | `competitor-monitoring`, `evidence-scout`, later `interview-bridge` | A newly disadvantaged segment or migration opportunity hidden by static research |
| D. Ecosystems and paid implementation | Explore specialist marketplaces, integrations and repeated implementation work; examine platform access and actual recurring spend | `competitive-landscape-builder`, `evidence-scout`, later pilot/operating-model owners | Valuable work paid for as services, connectors or implementation rather than standalone SaaS |

Founder experience is an optional input to A or D, explicitly attributed. It does not become independent corroboration. **Target-segment fit, competing explanations and counterevidence apply to every synthesis.** Buyer access and delivery economics are added when the requested idea validation requires them. Cross-country applicability is assessed only when such evidence is used.

For a customer-segment/topic study, start A and select another approach only when it addresses a useful question or blind spot. For a user's concrete idea, persist the hypothesis and use A plus relevant alternatives/counterexamples from B to test it. Add C when changes may explain customer experiences, and D when ecosystem or implementation evidence illuminates the task. These approaches may run in parallel. Neither foreign-company search nor a fixed set of methods is required for every request.

Research storage should center on **the user's question, customer segment, and problem/task hypothesis**, with trigger and context preserved. Do not merge materially different needs just because they share a profession. Geography is a scope/applicability field when relevant. Companies and sources attach as evidence to the question or finding, not as ideas that must be replicated.

## Protocol for parallel work

1. **Shared scope, independent first pass.** The coordinator persists the selected intent (idea validation or customer-problem understanding), user question, supplied hypothesis, known constraints, target scope, question IDs and counter-hypotheses. Reuse known answers; ask only decision-changing gaps. Workers receive the same question without another worker's preferred conclusion.
2. **A small work packet.** Record approach, assigned questions, allowed source families, expected deliverable, output directory and stopping condition. Preserve the existing permissions and source-use boundaries. Separate worker outputs avoid competing writes to the canonical study.
3. **Collect evidence, not persona votes.** Workers return source locators/captured spans, dates, observation versus interpretation, source role, target fit, question/finding IDs, counterexamples and gaps. Use candidate IDs when the scope includes candidate comparison. An intermediary, supplier or founder assertion retains its role.
4. **One merge owner.** The coordinator deduplicates sources, incidents and organizations across approaches; uncertain identity remains uncertain. Repeated quotation of a company announcement is one origin. Different approaches discovering the same story do not create independent evidence.
5. **Compare evidence coverage.** Assess coverage of the relevant customer situations, actual alternatives and competing explanations. Payment, switching, acquisition and delivery evidence are included where needed for the user's decision. Missing coverage is not evidence of absent pain or demand. If the user requests ranking, gather comparable initial coverage before ranking materially different hypotheses.
6. **Challenge the main conclusion.** A separately tasked reviewer seeks explanations for why customers experience a problem, situations where it does not occur, satisfactory alternatives and evidence against the user's idea. Check contextual differences when using analogous companies. The reviewer follows original source passages. Another model's agreement is not customer evidence.
7. **Resolve decision-changing disagreements.** Preserve disagreements and choose a targeted next retrieval, interview or feasibility test. Stop when further desk research is unlikely to change the next action, or disclose the specific access/provider gap. Do not hide disagreement in an averaged score.
8. **One reviewed synthesis.** Existing question/experience/claim IDs and source hashes carry into the report. Workers cannot mark the study or business gate passed. Answer the user's selected question: a pain-point study may end with an explanation and unresolved questions; idea validation may support, qualify or reject the hypothesis. Proposing a new venture or a foreign adaptation is not required. Where candidate selection or business commitments are requested, existing gates retain their roles.

Parallelism can reduce shared anchoring only if evidence sources and subquestions differ. It also increases coordination costs. Select the smallest useful set of approaches, using more than one when they address distinct uncertainties. No new dollar cap is implied by execution/sample bounds.

## What the output must help decide

For **customer-problem understanding**, produce:

- Specific customer situations, triggers, tasks, consequences and current workarounds.
- Differences within the segment, successful experiences and satisfactory alternatives, including why imperfect alternatives are tolerated.
- Observed facts, competing explanations, counterexamples, evidence limits and unresolved questions about the topic.
- Relevant lessons from comparable companies, explicitly bounded by context, only where they help explain those findings.

For **idea validation/challenge**, additionally map the user's material assumptions to support, contradiction or insufficient evidence. Examine buyer/approver roles, switching barriers, existing spend and feasibility where relevant. Explain what the idea would need to address and the next test that could change the assessment. Founder acquisition history, delivery economics and build/integrate/partner choices are conditional on the requested commercial decision.

Neither output requires an adaptation hypothesis or a shortlist of companies to copy. If research suggests a different problem or direction, present the evidence and ask the user to select a scope change before adopting it.

Keep evidence confidence and commercial attractiveness separate. Founder preferences are constraints, not proof. Interview recruitment remains unpaid by default; specific access routes must be researched, and planning does not authorize outreach, advertising or a pilot launch.

**Illustrative synthesis, not a market finding:** the user asks why small service firms struggle with reporting. Customer episodes reveal a recurring manual export, while other firms complete the task satisfactorily using an existing integration. A similar company abroad provides evidence about one possible mechanism. The report explains which circumstances differ and what remains unknown. If the user supplied a reporting-tool idea, those findings test that idea; they do not automatically generate an adaptation project.

## Monitoring and provider choices

Extend the existing monitor before installing another service. A material event needs canonical URL, previous/current observation dates and hashes, comparable fields, original evidence, hypothesized affected segment and the next check. Price comparisons must preserve currency, billing period, seat/usage assumptions, region and packaging. A changed page or job posting is supplier activity; customer reaction and commercial outcome require separate evidence.

Firecrawl documents text/structured comparisons and baseline behavior. `changedetection.io` is an alternative if a scheduling/hosting need justifies it. Neither should be introduced automatically. [Firecrawl change tracking](https://docs.firecrawl.dev/features/change-tracking); [changedetection.io repository](https://github.com/dgtlmoon/changedetection.io).

Use current search, review, app-store and capture capabilities first. BuiltWith may address externally detectable technology adoption; traffic tools address traffic; job APIs address hiring; app intelligence addresses modeled store metrics. None supplies a general revenue, profit or retention ground truth. Record the missing question before proposing access to an additional paid provider.

For this review, the required `FIRECRAWL_API_KEY_HGINVESTOR` returned `Unauthorized: Invalid token`. Web retrieval through the available fallback succeeded. This is an access gap for that designated integration, not evidence about the markets or a reason to substitute another credential silently.

## Ordered implementation batches

### Batch 1 — Restore trustworthy acceptance and evaluation

**Files:** `scripts/evidence_scout/{workspace,discover_market_problems,validate_synthesis,validate_customer_voc_synthesis}.py`, the existing corresponding schemas/tests, `scripts/validate_analysis_eval.py`, evaluation manifest and implementation record.

Implement the audit's first four repairs. Establish authoritative study/scope/question/finding bindings and disposition handling, resolvable passage checks and report assertion coverage. Keep valid insufficient-evidence completion available without a commitment pass. Make the eval summarizer incapable of presenting incomplete or design-only material as a quality decision.

**Acceptance:** full-workflow fixtures reject unsourced “validated” artifacts, stale/foreign packs, edited findings and unsupported promoted claims. Legitimate scoped evidence reuse and honest insufficiency still work. Empty/unknown/incomplete ratings cannot pass. Fidelity/uncertainty regression cannot be offset by presentation scores. Record exact tested boundaries.

### Batch 2 — Complete the existing capture and module commitments

**Files:** collector/checkpoint helpers and tests; router/catalog/module references; `scripts/subprojects.py`; existing publication/handoff helpers; compaction hooks; conflicting paid-provider guidance.

Repair retry dispositions and capture recovery. Complete module ownership and required reference loading. Make Marketing publication consume and maintain its workstream, honor registered paths, and validate current imported decisions. Make compaction restoration session-specific and modern-layout aware. Keep Research, Branding, Marketing and Website independently scoped, with explicit Business-linked consumption retaining its gates.

**Acceptance:** fault-injection reproductions retain captured evidence/memberships; repaired providers can retry without duplicating completed work. Module dispatch loads the applicable guidance. Changed upstream evidence invalidates linked decisions; standalone supplied briefs remain usable. Custom output paths and two simultaneous session restores stay isolated.

### Batch 3 — Put project-specific maintenance in the project

**Files:** `town-db-curator`, `scripts/town_db/`, global catalog/routes/parity tests, owning-project entry instructions and local evals; the three project-bound shared references listed in the audit.

Establish versioned project ownership before relocation because `projects/` is ignored. Rehearse path rebasing on a copy, preserve the DB/provenance and confirm each harness's loading behavior. Remove the global advertisement only after the local path works. Generic skills retain self-contained reviewed lessons with optional project provenance.

**Acceptance:** clean shared installation exposes reusable skills only; entering the Italy project exposes curation; fixture operations stay within that project; generated data is unchanged by relocation; project-specific maintenance remains versioned.

### Batch 4 — Add complementary research approaches with existing owners

**Files:** `idea-grill` and `market-problem-discovery` workflows and commands, `business-archetype-playbook-researcher` workflow, `references/customer-voice.md`, `references/voc-research-method.md`, `references/strategic-positioning.md`, `interview-bridge` workflow, discovery/feedback planning producer and report template.

Add one focused shared reference, `references/opportunity-research-approaches.md`, and load it for substantive idea validation or customer-segment/topic research when complementary methods are useful. Encode the selected intent, user question, approach selection and parallel-work packet in the existing research plan; extend a schema only where a consuming script must validate a new field. Preserve canonical question, episode, evidence and claim objects rather than creating duplicate ledgers.

Add the switching timeline/participants, advice vocabulary, actual competitive shortlist, ecosystem/agency sourcing and first-customer reconstruction. Existing playbooks should link this reference, avoiding duplicated method text. Keep native-language collection and separate topic/entity sampling.

**Acceptance:** a supplied idea stays the subject of validation and can receive a negative assessment; a segment/topic study can finish with evidence-backed pain-point understanding without generating products or business plans. Foreign analogs are optional and cannot become a replication objective without an explicit request. Relevant domestic and foreign comparables remain available. A narrow factual question does not start all approaches. Duplicate sources across workers count once. Differences and missing coverage survive the merge. Unknown chronology and founder claims remain explicitly attributed. Workers write isolated packets; only the coordinator publishes the synthesis.

### Batch 5 — Turn monitored changes into investigable hypotheses

**Files:** `competitor-monitoring` references and current snapshot/diff producer; existing watchlist and evidence contracts; conditional mobile-app guidance in the relevant research references.

Add event type, comparable old/new facts, hypothesized customer exposure, corroborating/contrary customer evidence and next check. Baseline-only captures cannot be reported as changes. Reuse current providers; propose an adapter only for a demonstrated coverage gap. Keep desktop SaaS and mobile estimates distinguishable.

**Acceptance:** changing whitespace does not create a business event; an annual/monthly price mismatch cannot become a claimed increase; a closure generates a migration hypothesis without inventing an installed base; a hiring event remains intent; modeled app revenue cannot be relabelled company profit. No recurring monitor starts from a one-off research request.

### Batch 6 — Measure incremental quality

Finish P0/P7 using actual frozen packets and blind reviews. Recover the baseline from a reproducible prior snapshot if available; otherwise label the comparison honestly as a new baseline. Do not manufacture pre-change results.

Compare current single-approach outputs with selected complementary approaches on the same task scope. Use an equal-evidence comparison for synthesis quality and a separately reported live-discovery comparison for additional coverage, documenting retrieval effort and resources. Added word count or agent agreement is not an outcome metric.

Include intent-preservation cases: a user idea contradicted by evidence; a customer-segment/topic request satisfied by problem understanding without a proposed product; and a relevant foreign comparable used without redirecting the task into replication. Also include strong frustration but no switch authority; a successful workaround; a foreign vendor already serving target buyers; an agency task that is too bespoke; a discontinued product without reachable buyers; source overlap between workers; and an apparently promising integration whose platform access fails. Keep connected sources/incidents together across development and held-out splits. These described audit cases are development cases, not secret holdouts.

**Acceptance:** saved paired outputs, source fidelity review, calibrated independent ratings, no critical attribution/payment/prevalence errors, and a frozen adoption decision. Compare actionable distinctions, missed counterexamples, uncertainty and decision usefulness separately. Complete the original Branding/Marketing/Website comparisons too; SaaS discovery work does not discharge those commitments.

## Source verification register

All links below were checked on **23 September 2026** using live web retrieval. Publication dates are listed where visible; “undated” means the retrieved page did not establish one. This verifies the cited source content, not commercial outcomes, API execution, subscriptions or coverage in a particular destination market.

### All 14 supplied links

| # | Source and publication date | Verification and limits |
| --- | --- | --- |
| 1 | [Walling/Reimer episode 666](https://www.startupsfortherestofus.com/episodes/episode-666-entering-a-competitive-market-books-for-saas-founders-and-more-listener-questions-with-derrick-reimer), 20 Jun 2023 | Supports differentiated competition, disconfirmation, reviews and early acquisition investigation; practitioner advice |
| 2 | [April Dunford](https://www.aprildunford.com/post/positioning-and-competition), 28 Dec 2020 | Supports actual customer alternatives, including existing processes |
| 3 | [Bob Moesta talk](https://businessofsoftware.org/talks/demand-side-sales-101-bob-moesta-online/), undated | Supports purchase timeline and forces encouraging/preventing change |
| 4 | [SaaStr](https://www.saastr.com/how-can-a-saas-startup-survive-in-a-crowded-market/), undated | Jason Lemkin byline present; narrow differentiation discussion, not an empirical success guarantee |
| 5 | [TinySeed portfolio](https://tinyseed.com/portfolio), current directory | RentKit, Tooltribe and ClientRock examples appear; inclusion does not establish profitability |
| 6 | [Shopify App Store](https://apps.shopify.com/), current directory | Task/category listings and reviews; this link alone does not document Atlassian |
| 7 | [ITreview](https://www.itreview.jp/), current directory | Japanese software categories/reviews; this link alone does not support the AIBoomi assertion |
| 8 | [changedetection.io](https://github.com/dgtlmoon/changedetection.io), current repository | Monitoring/API/webhook capabilities; not an implemented system in this repo |
| 9 | [Firecrawl change tracking](https://docs.firecrawl.dev/features/change-tracking), current docs | Text/structured comparison and baseline behavior; API integration access failed separately in this review |
| 10 | [BuiltWith API](https://api.builtwith.com/), current docs | Technology detection/history; detectable use is not a paid subscription |
| 11 | [Similarweb API](https://developers.similarweb.com/docs/similarweb-web-traffic-api), current docs; supplied root redirects | Traffic/audience API, not revenue evidence; does not by itself establish Semrush capability |
| 12 | [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html), current docs; supplied URL redirects | Published jobs/departments/offices; GET access documented without authentication; employer coverage is limited to this system |
| 13 | [Appfigures estimates](https://docs.appfigures.com/api/reference/v2/estimates), current docs | Modeled downloads and net app revenue, selected access/licensing; not total company profit or retention |
| 14 | [Product Hunt API](https://api.producthunt.com/v2/docs), current docs | Commercial API use requires contact/permission; this link does not document TrustMRR restrictions |

### Additional primary sources and citation repairs

| Source | Publication date | What it adds |
| --- | --- | --- |
| [Reimer episode 506](https://www.startupsfortherestofus.com/episodes/episode-506-shutting-down-and-starting-up-with-derrick-reimer) | 21 Jul 2020 | Failed switch proposition, own-tool discovery and low-friction adoption considerations |
| [Sales Safari interview](https://stackingthebricks.com/podcast/ep42-what-is-sales-safari-with-eteinne-garbugli/) | 5 Nov 2020 | Observation of language, beliefs and advice sources; distinct starting approach |
| [Paul Graham](https://www.paulgraham.com/startupideas.html) | Nov 2012 | Lived-workflow idea origin; use as candidate generation, not demand proof |
| [Atlassian Marketplace](https://marketplace.atlassian.com/) | Current directory | Separately verifies the marketplace named alongside Shopify |
| [SaaSBoomi homepage](https://saasboomi.org/) and [handbook](https://saasboomi.org/saas-handbook/) | Current pages | Homepage announces AIBoomi rebrand and links to aiboomi.org; founder resource context |
| [Semrush Trends API](https://developer.semrush.com/api/v3/trends/overview/) | Current docs | Separately supports the traffic-data API claim |
| [42matters changelog docs](https://42matters.com/docs/changelog) | Current docs | Separately supports app change/history capabilities; plan coverage still needs checking for actual use |
| [TrustMRR API documentation](https://trustmrr.com/docs/api) | Current docs | Explicit API-use restrictions include cloning businesses; do not build a cloning workflow on that API. This is a source-specific restriction, not a prohibition on all competitor research |

Several multi-product statements in the supplied answer were broadly supportable but attached to a citation for only one product. These additional official sources repair that attribution. None of the sources establishes that importing a foreign product concept is generally more successful than another discovery method.
