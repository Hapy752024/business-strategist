# Agent and business-coaching review — 5 September 2026

The project has a useful foundation, but it is not yet a reliably enforced business coach. Its strongest qualities are its evidence discipline in prose, specialist boundaries, short skill entrypoints, and existing validators. Its main weakness is the gap between those instructions and what execution actually guarantees.

The recommendation is to repair and simplify the existing system. No new specialist skills, agent framework, dashboard, vector database, or default review panel are needed for the first improvement pass.

Scope: current working-tree agent setup, skills, configuration, scripts, schemas, tests, and reusable strategy methods. Existing research reports and conclusions were excluded. Existing uncommitted changes were preserved. Provider readiness summaries were used only as infrastructure diagnostics. This review adds this document and its [check results](2026-09-05-agent-strategy-checks.json); it does not implement the proposed changes.

## 1. What is already worth keeping

- All **38 skills** have eval definitions. Entrypoints are only **21–30 lines**; shortening them indiscriminately would remove useful routing boundaries.
- Research, brand, website, and experiment state already have manifests. Branding is optional, and competitor work separates actual competitors, analogues, and capability references.
- GTM instructions already emphasize a beachhead, first customers, retained value, one primary acquisition motion, contribution economics, and stop rules. These do not need to be reinvented.
- The current setup validator passes. The problem is coverage and enforcement, not a lack of validation machinery.
- Existing Python scripts are a sensible place for deterministic operations. Keep business judgment in the agent and make its evidence, calculations, transitions, and permissions checkable. This follows the simple-workflow approach described in [Anthropic’s agent architecture guidance](https://www.anthropic.com/engineering/building-effective-agents).

## 2. Fix these execution gaps first

Priorities below reflect impact on trustworthy decisions. “Confirmed” means static inspection or a bounded local reproduction; it does not mean a live host failure was observed.

| Priority | Confirmed finding | Consequence | Smallest useful correction |
|---|---|---|---|
| P0 | Six source literals emitted by collectors are absent from the evidence schema | Normalized records and the advertised contract disagree | Reconcile names and validate normalized records before saving |
| P0 | A Reddit search returning HTTP 429 is summarized as `ok` with zero records | An inaccessible source can look like a successfully searched source | Aggregate request outcomes and distinguish empty success, partial success, rate limit, and failure |
| P0 | Evidence strength increases with engagement; synthesis trusts supplied independence counts | Weak or duplicated observations can support excessive confidence | Separate engagement from strength and recompute independence in the validator |
| P1 | The router misses core GTM/marketing intents; monitoring is absent from the catalog | The main coaching capabilities are not reliably dispatched | Complete existing routing and validate catalog/route/delegation coverage |
| P1 | Stage updates accept a final decision with missing artifacts and unfinished intake | A manifest can record success without verified prerequisites | Put transition and artifact checks inside the existing state mutation boundary |
| P1 | Claude hook inputs/outputs disagree with current documented contracts | Correct outputs can be misread; restoration is not proven | Correct event adapters and test documented payloads plus a real host smoke test |
| P1 | Provider readiness has no freshness boundary and can overwrite newer individual results | Routing can rely on an old environment failure or success | Select results by time and environment, with explicit stale/unknown states |
| P1 | Geography inference and capability lookup are narrow and language-biased | Wrong market scope or missed sources | Persist explicit locale scope and test Unicode/local-language behavior |
| P1 | Evaluations mostly establish structure and phrase routing | Green checks do not establish honest coaching or strategy quality | Add a small held-out behavior suite with traces and outcome checks |

### Source contracts and provenance

In [collect.py](../../scripts/evidence_scout/collect.py), emitted names missing from [evidence-record.schema.json](../../schemas/evidence-record.schema.json) are `hn`, `github`, `google_autocomplete`, `itunes_reviews`, `youtube_transcript`, and `xai_x_search`. The first three are default providers. All six were identified from executable call sites; schema rejection was reproduced for the first three.

The collection loop saves records without enforcing this schema. Thus the current collector can write incompatible data; a strict downstream consumer would reject it. Fixing only the enum would still leave semantic gaps: creator transcripts, customer reviews, discovery summaries, and search suggestions must retain distinct evidence roles. `infer_source_intent()` has no explicit handling for several of these emitted names.

Use the existing capability catalog to record the actual adapter or standalone command, emitted source kind, validator, evidence role, cost class, and fallback. Validate those links. Do not add another parallel registry. For example, the catalog describes podcasts with `collector_provider=podcasts` and alias `default`, but `collect.py` neither includes podcasts in `default` nor implements that provider. The standalone podcast script exists: label and route it accurately instead of forcing it into every collection run.

`collect_reddit()` unconditionally returns `status=ok` after its search loop. A mocked successful authentication followed by a 429 search reproduced `ok / record_count=0`. Add fixtures for empty 200, 429, 402, malformed responses, and mixed success. Other collectors need the same contract review; this one reproduction does not prove every adapter is broken.

Record the backend that actually made each request. The final collection loop currently decorates records using family-level routing information, which may describe a preferred route rather than that record’s actual retrieval path.

### Evidence quality and synthesis

`estimate_strength()` at approximately line 683 promotes identical pain/workaround text from `medium` to `strong` when upvotes change from 0 to 25. This does not establish repeated independent behavior, spending, or willingness to pay.

[validate_synthesis.py](../../scripts/evidence_scout/validate_synthesis.py) accepts one weak supporting record with `independence_count=999` and `confidence=high`. It checks the supplied count against a threshold without deriving it. It also does not schema-validate the claim and evidence inputs. The ledger builder calculates counts, but falls back to distinct URLs; syndicated copies or multiple posts by the same person can still appear independent.

Extend the existing normalizer and validator to:

- Derive independence from the underlying author/event/source provenance and duplicate clusters; represent unknown independence honestly.
- Preserve stable evidence identity across refetches. The fallback ID currently includes retrieval time, so identical material gets a new identity on another retrieval.
- Require traceable support for material observations, and distinguish observation confidence from confidence in a commercial recommendation.
- Validate counter-search scope content, not merely the presence of scope keys.
- Treat heuristics as triage. Neither three sources nor a high engagement count proves a business proposition.

### Routing and orphan prevention

There are **38 skill directories, 37 catalog entries, and 11 route rules**. `competitor-monitoring` is missing from [skill-catalog.json](../../config/skill-catalog.json), although it is documented elsewhere. It is therefore a catalog omission, not an entirely undiscoverable skill.

Reproduced routes:

| Input | Current result | Appropriate destination |
|---|---|---|
| Build a GTM strategy for my SaaS | `business-strategist` clarification fallback | `archetype-gtm-strategist` |
| Create a marketing strategy | `business-strategist` clarification fallback | `marketing-strategy-builder` |
| Monitor competitor pricing weekly | `competitor-marketing-analyzer` | `competitor-monitoring` |

The router uses the longest matching English substring. Add explicit intent/mode selection and missing core routes first. For ambiguous natural language, allow a bounded classification or one useful clarification; do not attempt to solve arbitrary intent with an ever-growing phrase list. Once the intent is selected, dispatch and stage checks should be deterministic.

Make the validator assert that every skill is either directly routable, an explicitly declared child, or an installation/manual utility. Brand production children do not each need a top-level route. Validate referenced skills, local resources, command entrypoints, and expected outputs, with explicit exemptions for runtime-generated paths. The current checks do not establish a complete no-orphan guarantee.

The route packet should return the existing catalog’s prerequisites, expected artifacts, side effects, and next action. The current function omits several fields promised by the skill workflow.

### State and hook enforcement

[workspace.update_stage()](../../scripts/evidence_scout/workspace.py) accepts caller-provided success and artifact paths. A temporary workspace advanced to `final_decision=pass` while intake remained `in_progress`, citing a nonexistent file. Individual callers have some gates, so this is a missing shared enforcement boundary, not proof that every workflow skips validation.

Extend this helper with route-specific prerequisites, artifact existence/schema checks, content revisions, and explicit invalidation after upstream changes. Preserve optional branches; do not force every request through all stages. Use a revision check or single writer for manifest updates. Atomic replacement alone does not prevent lost updates from concurrent writers.

The hook path fix already present in the working tree is useful. The remaining issue is event semantics. `subagent_stop.py` reads `agent_name` and `agent_output`; current documentation specifies `agent_type` and `last_assistant_message`. Replaying a nonempty documented payload produced an empty-output diagnostic. Its nested `decision` values also differ from the documented top-level blocking contract. `postcompact.py` returns a `message` payload without establishing supported context injection. Correct these adapters and verify restoration through a supported event such as `SessionStart` with the compact matcher. See the [official hook contracts](https://code.claude.com/docs/en/hooks).

The resume file is also global to the repository: it scans every topic, sorts run paths lexically, and writes one `.claude/plans/resume.json`. Scope it by session and selected manifest, and restore the current task, last decision, pending action, and revision. This reduces context noise and cross-session collisions.

### Readiness and harness scope

Both the doctor and capability lookup load individual validation summaries, then overwrite them with the aggregate summary without comparing timestamps. They have no result TTL or environment fingerprint. This review’s doctor output described old sandbox/network failures, while a new Serper request succeeded after an approved network retry. The doctor was not rerun after that search; this is evidence that snapshot status and a live request are different things.

Use timestamps plus a sanitized fingerprint of endpoint, configuration revision, and network context. Keep `not_checked`, `stale`, `credentials_present`, `usable`, and `failed` distinct. Validate only the selected source family before a run; keep broad diagnostics as a setup command.

`.mcp.json` contains two unpinned `npx -y` servers. Pin tested versions for reproducible setup and make updates deliberate. `CLAUDE.md` mentions filesystem/sqlite servers absent from this project config; either document them as external prerequisites or remove that claim. No live multi-host compatibility was established here. Native host discovery of `.agents/skills` is separate from host-specific hook and MCP configuration.

The broad `Bash(python3 -c *)` allowance also means file-read deny patterns should not be described as a credential-isolation boundary. Review the necessary command permissions and use the host sandbox for actual isolation. No secret reads or bypass attempts were performed in this audit.

## 3. Make honest coaching observable

The agent should optimize for better decisions and useful execution, including challenging the founder. The current directness instructions are appropriate. Their enforcement needs work: historical research demonstrates that assistants can favor a user’s stated belief over truth, so a “be blunt” sentence is not sufficient evidence of resistance to agreement pressure. [Anthropic’s sycophancy research](https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models).

Add a short shared coaching contract to the existing business orchestrator, with these outcomes:

1. Give a provisional verdict: investigate, test, commit, pivot, park, or stop. State the decisive uncertainty.
2. Identify the weakest material assumption and the strongest opposing explanation.
3. Say what evidence would change the verdict. Revise when new evidence warrants it.
4. Separate founder preference, public observations, commercial proof, and speculation.
5. Recommend the next action, owner, deadline, spending/time cap, and decision rule.
6. At the next review, compare commitments and results. Surface missed actions and moving goalposts directly.

Challenge the claim or behavior precisely. Avoid unsupported certainty, insults, or automatic opposition. If the founder chooses a reasonable path against the agent’s advice, record the tradeoff and help execute within the agreed boundaries.

An important contradiction to remove: [opportunity-risk-designer](../../.agents/skills/opportunity-risk-designer/references/workflow.md) says missing evidence is uncertainty, but its decision list includes weak evidence as grounds to stop. Introduce an explicit insufficient-evidence/park outcome. “This failed its test” and “we have not tested this properly” require different advice.

Example of the desired coaching style: **“You have a reachable audience, but no purchase evidence. A content calendar will not resolve that. The next task is to test a paid offer with qualified buyers. If you postpone that again, we are spending effort around the main uncertainty.”** This is an illustrative response pattern, not a finding about the user’s current business.

## 4. Better idea and segment prioritization

Reuse `opportunity-risk-designer` for a comparison mode and `business-strategist` for orchestration. Do not create a new idea-ranking skill or duplicate topic evidence into a portfolio database.

Use one comparison table referencing selected idea manifests. Capture founder objectives and constraints first: desired income or scale, available time/cash, relevant access, delivery appetite, and acceptable downside. A promising venture-scale company and a profitable solo service should not be ranked against unstated goals.

Keep **commercial attractiveness** separate from **evidence confidence**. Strategyzer’s portfolio method makes a similar separation between expected return and innovation risk. Apply that distinction to the existing comparison output. [Portfolio reference](https://www.strategyzer.com/library/business-model-portfolio-part-2-manage-new-business-initiatives).

Compare customer urgency and consequences, observed spending, reachable buying events, founder access, delivery feasibility, contribution potential, switching friction, test cost, and time to first revenue. Show unknowns and sensitivity to assumptions. Rank the next affordable test when evidence is weak; do not manufacture decimal rankings for untested businesses. End with one active priority and explicit reasons to park the others, unless the founder has capacity for more.

The discovery rubric currently multiplies severity by counts of public records/source types. Retain it as a signal-triage view, not the sole commercial ranking. A publicly noisy segment can outrank a quiet but expensive B2B problem simply because it is easier to observe. Existing reachability-bias instructions are good; connect that caveat to ranking eligibility.

Extend the current segment card with the buying episode: trigger, job, desired outcome, present workaround, user/buyer/payer/blocker, consequences of delay, required trust, switching friction, and route to reach qualified people. Compare recent switchers, non-buyers, lost deals, and retained customers when available. Demand-side interviews should reconstruct actual purchase sequences and tradeoffs. [Bob Moesta’s practitioner explanation](https://businessofsoftware.org/talks/demand-side-sales-101-bob-moesta-online/) and [the Value Proposition Canvas](https://www.strategyzer.com/library/the-value-proposition-canvas) provide useful complementary lenses.

## 5. GTM and marketing that lead to execution

Keep the existing split: archetype GTM decides the acquisition motion and stage; marketing turns the positioning and offer into campaigns; social/digital handles channel execution; the operating-system skill reviews progress. Pass one shared segment/offer/experiment record between them rather than regenerating strategy in each skill.

Position against the customer’s actual alternatives, including doing nothing, spreadsheets, manual work, and an existing supplier. A discovered company is not automatically on the buyer’s shortlist. Add a compact chain to the existing marketing template: **alternative → relevant advantage → customer outcome → proof → objection → test**. [April Dunford’s positioning guidance](https://www.aprildunford.com/post/positioning-and-competition).

Define the GTM motion from buyer access, price, sales cycle, onboarding effort, trust, delivery capacity, and retention behavior. Preserve the existing first-ten-customer and primary-channel rules. Add explicit handoffs from acquisition to sales, onboarding, value delivery, retention, and expansion, with owners and observable exit criteria.

Adapt stage gates to the business. A one-off consumer service needs delivery quality, contribution, complaints/refunds, and relevant referrals; it should not fail because customers do not buy every month. An enterprise pilot needs sponsor commitment, procurement progress, implementation, and demonstrated value. A self-serve SaaS product needs activation and mature usage cohorts.

For marketing, test message comprehension, credibility, relevance, and qualified conversion before multiplying creative variants. Change one strategically important variable at a time when the learning objective requires attribution. Keep founder labor, creative costs, refunds, and servicing costs visible. Preserve the existing distinction between attributed results and incremental impact; do not install a marketing-mix model or elaborate attribution stack before data and decision stakes justify it.

Growth-loop guidance is already substantial. Consolidate it into the shared evidence reference and retain only skill-specific application steps. Reforge’s loop model is useful for identifying a repeatable reinvestment mechanism; it does not make a referral button evidence of growth. [Growth-loop reference](https://www.reforge.com/blog/growth-loops).

## 6. A small KPI contract and weekly coaching loop

Use one scorecard in the existing execution artifacts. Start with **3–5 decision-relevant metrics**, chosen for the current stage. Each needs its formula, source, segment/cohort, observation window, baseline, target, warning/stop threshold, owner, and action. Missing observations are unknown, not zero. Thresholds must come from the business’s economics or an explicitly labeled test hypothesis, not universal startup benchmarks.

| Stage | Useful outcome metric | Definition and decision |
|---|---|---|
| Problem learning | Qualified participants with a recent costly problem and active workaround | Count and proportion within the screened sample; compare segments and investigate disconfirming cases. This is not population prevalence or purchase validation. |
| Offer test | Paid commitments / qualified prospects receiving the same offer | Specify price, exposure, collection window, exclusions, and refunds. Weak conversion prompts diagnosis of segment, offer, proof, price, or access. |
| Activation | Customers reaching the defined first value event / eligible new customers | Include time to value. Fix onboarding or delivery when acquisition succeeds but activation fails. |
| Retained value | Eligible customers repeating the core job or renewing / original eligible cohort | Use a mature window matched to natural purchase frequency. Keep immature cohorts separate. |
| Repeatable acquisition | Acquisition cost per new paying customer, retained contribution, and payback | Define included acquisition costs and avoid counting them twice in contribution. Track by source cohort; use incremental customers when a valid lift design exists. |
| Execution guardrail | Cash/runway, delivery capacity, or complaints/refunds | Choose the binding constraint. Trigger a spending or scope decision when the agreed boundary is crossed. |

For each experiment, reuse the existing test template and add sample eligibility, denominator, duration/maturation window, threshold rationale, budget, and the decision after each possible result. This extends the hypothesis/test/metric/threshold structure in [Strategyzer’s Test Card](https://www.strategyzer.com/library/validate-your-ideas-with-the-test-card). Small-sample commercial tests are learning gates, not claims of statistical certainty.

Weekly output should fit on one page: previous commitments versus completion; actual versus target with sample/window caveats; current bottleneck; evidence that changed the verdict; continue/change/stop decision; next commitments. The agent should call out missed customer contact, deferred tests, and repeated target changes when the record supports that critique.

Execution means producing the concrete test assets, recruiting criteria, interview guide, offer, landing-page copy, tracking sheet, and follow-up analysis that are in scope. Sending outreach, publishing, spending, or deploying still follows explicit user authorization. The agent should prepare reviewable work before asking for a final action approval.

## 7. Languages and geographic scope

This review treats “languages” as both multilingual business work and portable execution. Python does not need to be replaced to improve reliability.

`infer_geo_language()` recognizes Germany/China markers and otherwise returns US/English. Swiss retirement planning, French freelancers, Italian accounting software, and an Arabic Saudi-service prompt all reproduced that fallback. `capability_lookup.words()` drops Arabic and Chinese characters entirely.

Use explicit, reusable run fields for market geography, query language, source language, and output language. Respect supplied scope; when missing and consequential, ask once or mark it unresolved. Geography and language must be independent: an English-speaking buyer in Switzerland is not a US market.

Store original text and source identity alongside any translation, translation method, review status, and material ambiguity. Preserve local currencies and units, and distinguish normalization from translation. Localize trigger terms, buying roles, proof requirements, and channels using retrieved evidence rather than literal translation alone. Replace the unconditional Europe home-market row in the GTM template with the selected home market.

Test the supported languages with equivalent intents and evidence cases. Begin with the languages the user actually needs; add a locale only with meaningful fixtures. Do not claim broad multilingual competence from a language flag.

## 8. Remove bloat while improving assurance

| Existing overhead | Recommended change |
|---|---|
| 12,594-byte root `AGENTS.md` plus skill/catalog duplication | Keep the root stance, scope rules, permission boundaries, and pointers; move task-specific detail behind conditional reads |
| 14 workflow references repeat YAML frontmatter | Remove duplicate metadata during cleanup; maintain routing metadata at the entrypoint/catalog boundary |
| Repeated channel, loop, and founder-story rules across GTM/marketing/social | Maintain one authoritative shared rule and concise specialist applications |
| Nine default collectors, including developer sources for unrelated audiences | Select a minimal source plan from segment and question; add a source only for a named gap |
| All-provider validation before routine work | Validate the chosen route and cached readiness freshness; retain broad doctor mode for setup |
| Multiple runs of overlapping Python suites in setup and CI | Collect the relevant suite once; keep cheap structural checks separate |
| Global workspace scans and generic clarification loops | Resolve the selected workspace/session and ask only when the answer changes the next action |
| Fixed long strategy output contracts | Offer decision brief, experiment plan, and full strategy depth within the existing skills |
| Panel/tournament availability | Keep optional and bounded for consequential disagreement; routine coaching uses one agent |

Progressive disclosure should reduce what is actually loaded, not merely move a wall of instructions into a mandatory reference. The [Agent Skills specification](https://agentskills.io/specification) and [Anthropic’s context-engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) support loading resources as needed.

Measure loaded prompt/reference tokens, tool-result bytes, repeated URLs, tool calls, latency, and successful decision completion in sampled agent runs. The existing offline runner reports fixed tool counts and zero reference loads; those are fixture metrics, not measured agent efficiency. Establish a baseline before promising percentage savings.

A useful admission rule for future additions: name the failure, explain why an existing skill/helper cannot handle it, identify the owner and consuming workflow, and supply a meaningful test. Remove or simplify the redundant path when adding its replacement.

## 9. Evaluation and implementation order

**First: restore trust in execution.** Fix source/schema drift, failure aggregation, strength/independence, hook contracts, and stage validation. Extend existing tests with the demonstrated failures. No new runtime framework.

**Second: make the coaching path complete.** Repair core routes and catalog coverage; add the short coaching contract, insufficient-evidence verdict, idea comparison mode, shared strategy handoff, and KPI fields. Reuse existing skills and manifests.

**Third: simplify and measure.** Deduplicate rules and checks, select sources by need, scope resume context, make locale handling explicit, and add a small live behavior suite. Expand only where failures or measured cost justify it.

Start the behavior suite with difficult cases: a founder insists a favorite idea is validated; 1,000 signups with no retained use; a failed provider; a quiet expensive segment versus a noisy low-value one; two competing ideas; a one-off service; an enterprise pilot; pressure to change thresholds after seeing results; a week of missed commitments; and new evidence that should reverse an earlier negative verdict. Include short paraphrases and supported non-English variants.

Check actual routes, requested tools, resulting artifacts, calculations, permissions, and decisions. Grade whether criticism is justified and actionable, not whether the response contains skeptical words. Use human calibration for any model-based judge, and repeated trials for agent variability. [Anthropic’s evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

Validation performed in this review:

- `bash scripts/validate_setup.sh`: passed; includes the existing 44-test `tests/` suite and offline routing checks.
- `python3 scripts/run_evals.py`: 109 structurally valid skill cases across 38 skills; 24 routing cases across nine collision pairs. These are definition checks.
- Plain `pytest -q scripts/evidence_scout`: three import errors during collection.
- With `PYTHONPATH=scripts/evidence_scout:scripts/validate_apis`: all 59 tests in that directory passed. Make collection work through the standard test command and include these tests in CI; the current `tests/` invocation excludes them.
- Synthetic probes reproduced the routing, schema, strength, confidence, stage, locale, hook-payload, and Reddit-status findings above.
- A real Serper query succeeded after a sandbox DNS retry. Public primary-source pages were retrieved through web search/open. Firecrawl CLI, all-provider live validation, live host hooks, live cross-harness agents, and website visual/browser checks were not run.
- `git diff --check`: passed before report creation; report/check files were also reviewed for scope and internal consistency.

The audit is complete. The suggested implementation remains outstanding; no existing research needs to be changed to carry it out.

## Sources

All sources retrieved **5 September 2026**. Publication dates are listed when visible; undated or maintained documentation is identified explicitly. These sources support design principles, not validation of any existing business idea.

1. Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), 19 December 2024; maintained page notes later tooling changes.
2. Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), 29 September 2025.
3. Agent Skills, [Specification](https://agentskills.io/specification), maintained documentation; no publication date used.
4. Claude Code, [Hooks reference](https://code.claude.com/docs/en/hooks), maintained documentation; no publication date used.
5. Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 9 January 2026.
6. Anthropic, [Towards Understanding Sycophancy in Language Models](https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models), 23 October 2023; historical findings, not a measurement of this project’s current model.
7. Strategyzer, [Business model portfolio part 2](https://www.strategyzer.com/library/business-model-portfolio-part-2-manage-new-business-initiatives), 28 August 2017.
8. Strategyzer, [Value Proposition Canvas](https://www.strategyzer.com/library/the-value-proposition-canvas), official tool page; no publication date used.
9. Strategyzer, [Validate Your Ideas with the Test Card](https://www.strategyzer.com/library/validate-your-ideas-with-the-test-card), publication date not independently extracted in this review.
10. April Dunford, [Positioning and Competition](https://www.aprildunford.com/post/positioning-and-competition), 28 December 2020.
11. Business of Software / Bob Moesta, [Demand-Side Sales 101](https://businessofsoftware.org/talks/demand-side-sales-101-bob-moesta-online/), practitioner talk/transcript; publication date not independently extracted.
12. Reforge, [Growth Loops are the New Funnels](https://www.reforge.com/blog/growth-loops), practitioner framework; publication date not independently extracted.
