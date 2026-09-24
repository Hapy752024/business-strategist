> Historical plan reviewed with verdict REVISE. Relative links rebased for archive location.

# Agent improvement plan: better case research, one selected business

13 September 2026. Status: proposed implementation plan; no agent code or research migration implemented. Uses physical case folders (Option B) as the planning baseline. It incorporates the user's requirements for multiple investigations, feasibility and economics per case, one executable idea, a root business plan, and separate current documents/history/archives. Earlier tournament scores do not constitute independent approval of this new plan.

## Outcome and scope

The user should be able to compare investigated ideas, understand the evidence and economics behind each, select one, and receive a coherent business plan for that selection. The improvement must also make the research more useful: explain customer choice, delivery requirements, cash and uncertainty rather than simply accumulating sources.

Four bounded work packages extend existing skills, state helpers and validators. Do not import the four external repositories or create another framework, database, dashboard, standing agent panel or parallel stage machine. New templates and small helper code are justified only by the specific outputs/checks below. Existing research and unrelated uncommitted changes are preserved.

## Lessons to adopt, adapt and reject

| Source inspected | Useful lesson | Our adaptation and actual novelty |
|---|---|---|
| MaxKmet [memory contract](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/memory/README.md) and [decision memo](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/skills/decision-memo/SKILL.md) | Durable per-idea assessments, shared research, a concise recommendation, explicit uncertainty, failure scenarios and a next test. | Case-local current outputs are a structural addition. Put a short decision summary in each case README, with the three most consequential failure paths and one next action when the evidence supports one. Preserve uncertainty and do not add another competing recommendation memo. |
| MaxKmet [pricing](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/skills/pricing-and-wtp/SKILL.md), [CAC](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/skills/cac-modeler/SKILL.md) and [retention](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/skills/retention-predictor/SKILL.md) | Make pricing, acquisition and continued value explicit research dimensions. | These topics already exist locally. Improve the deliverable: separate observed prices/spend from hypothetical willingness to pay; show the acquisition funnel and contribution; explain renewal/repeat-value mechanisms. Reject invented price-survey thresholds, desire-based price multipliers, unsupported default retention/CAC estimates and revenue-only lifetime value for profitability decisions. |
| ANVEAI [idea-hunt](https://raw.githubusercontent.com/ANVEAI/idea-hunt-skill/main/SKILL.md) | Investigate the existing workaround and spending, record rejected alternatives, define a commercial test and choose one candidate before execution planning. | Pain-first research and test design already exist. Add a visible comparison and explicit user selection. Do not import its universal 72-hour build/reachability rules, compulsory AI/software model, automatic rejection of infrequent needs, or treatment of a job posting as a purchase order. Tests do not authorize taking payments or contacting customers. |
| MackDing [stage gates](https://raw.githubusercontent.com/MackDing/ai-native-founder-playbook-skill/main/ai-native-founder-playbook/references/stage-gates.md) and [templates](https://raw.githubusercontent.com/MackDing/ai-native-founder-playbook-skill/main/ai-native-founder-playbook/references/templates.md) | Match research to maturity; investigate false positives, define MVP exclusions/amendment criteria, and expose founder-dependent operations. | Reuse our stage machine and pilot/operations skills. Add a skeptical interpretation to outcome evidence, an evidence requirement for expanding MVP scope, and founder-attention/capacity questions to feasibility. Do not import app retention thresholds or a new lifecycle. Detailed files were successfully inspected for this plan; the earlier audit had only README coverage. |
| Agency-agents [business strategist](https://raw.githubusercontent.com/msitarzewski/agency-agents/main/specialized/business-strategist.md) and [financial analyst](https://raw.githubusercontent.com/msitarzewski/agency-agents/main/finance/finance-financial-analyst.md) | Evaluate alternatives including doing nothing; state investment, dependencies, cash flows, sensitivity and reversible decision points. | Formalize a lightweight case business case and auditable economics. Existing positioning already covers many questions; standardized calculations and linked plan completeness are the additions. Avoid default DCF/LBO/M&A work, arbitrary scenario probabilities and unsupported market-share forecasts. Role prompts are not verified analytical software. |

These are design lessons from source inspection, not evidence that the repositories outperform this agent. Preserve our explicit evidence provenance, comparable coverage, unpaid interview recruitment preference, pain gate and authorization boundaries.

## Work package 1 — Case identity, selection and clean outputs

**Value:** the reader can find every investigated case; the agent cannot confuse a research follow-up with execution selection. This is the most involved infrastructure change and must be delivered as a complete path through the relevant writers.

Extend the existing project manifest with an identity-only case registry and one nullable selection with scope and revision. This consolidates the earlier proposed `cases.json` into an existing authority. Keep case research stages in their own research manifests; do not duplicate stage status in the registry. Research focus and `active_track` are not selection. Stable IDs survive renaming; relations/facets handle variants without automatically creating a business for every combination.

Minimum default layout:

```text
projects/<project>/
  project-manifest.json          # Case identities and one execution selection
  README.md                     # Current comparison and navigation
  cases/<id>/
    README.md                   # Current concept, assessment summary, next action
    market_research/manifest.json
    market_research/...         # Created as used; original runs retain provenance
    feasibility.md              # Created when assessed
    business-case.md            # Created when assessed
    economics.json              # Created when calculations are needed
  market_research/...           # Shared studies and preserved legacy runs
  strategy/...                  # Only the selected idea's business plan/execution
  history/decisions/<id>.md      # Canonical rationale, affected cases, snapshot links
  history/evolution.md           # Generated project timeline
  history/snapshots/<revision>/  # Actual prior concepts and current outputs
```

Use a shared resolver that returns project root, case identity, research root and output base explicitly. Remove callers' assumptions that walking up from a manifest always reaches the project root. Do not silently fall back to project-wide output when a case was requested. Shared evidence needs an explicit per-case applicability assessment; a shared source never confers a shared validation pass.

Add a bounded exploratory case-appraisal route using existing specialists. It may describe hypothetical feasibility/economics before pain validation. It may not advance commitment stages, create approved launch artifacts or bypass prerequisites by labeling the request focused. Execution routes require the selected scope/revision plus existing evidence and authorization checks. Standalone work retains its existing explicit bypass.

Use existing locking/atomic-write patterns. For the first implementation, serialize state-changing commits at project scope; avoid a custom distributed transaction system. Snapshot affected current artifacts before replacing them. Record rationale once; machine events reference that decision. Interrupted multi-file updates remain pending/stale and are recoverable on resume; the timeline publishes only completed decisions. Raw run collection can remain parallel. Selection changes archive the old plan and invalidate its handoffs; they do not perform external cancellation actions.

**Existing surfaces:** [project control](../../../../scripts/project_workspace.py), [workspace helpers](../../../../scripts/evidence_scout/workspace.py), [initializer](../../../../scripts/evidence_scout/init_project.py), [router](../../../../scripts/route_workflow.py), route enforcement, project/research/handoff schemas, lifecycle reference and project templates. Audit and adapt collection, discovery, competitor marketing/ads, landscape builders, founder-playbook research, interview-kit and downstream brand/website writers. Reuse the producer list in [the structure report](../REPORT.md); add any direct writer found during implementation.

**Acceptance:** initialize a topic without empty venture workstreams; resume a known case without duplication; update A without changing B or execution selection; reject retired/ambiguous/escaping paths; reject multiple selections and old-revision handoffs; detect interrupted publication; preserve original source files. Audit every producer before making case mode the default. A partial implementation stays explicitly experimental.

## Work package 2 — A compact, comparable research assessment

**Value:** every case answers the decision-changing questions, while existing evidence is reused. This is primarily workflow/template work, not new specialist skills.

Create one shared assessment reference and three small templates: case README, feasibility and business case. Existing specialists own their relevant sections and cite source records. The README holds a short current decision summary; detail stays in the two assessments and research artifacts. A focused question updates only affected sections.

| Research dimension | Required substance when relevant | Existing owner |
|---|---|---|
| Customer choice | Trigger; user/buyer/payer; current workaround; switching friction; evidence the customer notices, trusts and prefers the entrant; doing nothing as an alternative. | Idea grill, evidence scout, customer-perspective challenger |
| Commercial evidence | Who pays whom today, for what; actual prices/spend versus statements of intent; reasons to decline; cheapest appropriate next test. An existing provider's revenue is not our willingness-to-pay validation. | Evidence scout, opportunity risk, startup builder |
| Reach and retention | Concrete first-customer access, funnel denominators, founder time, time to receive value, renewal/repeat/referral mechanism and cancellation causes. Choose a measurement window appropriate to the service. | GTM/marketing, startup builder, pilot designer |
| Delivery feasibility | Build/buy/partner options, critical dependencies, people/skills/data/permissions, lead times, capacity, manual review/rework/support burden, upfront costs and what fails if the founder is unavailable. AI-specific reliability questions only when AI is material. | Operating system, pilot designer, opportunity risk |
| Decision and disconfirmation | Strongest support, strongest counter-evidence, three plausible failure paths, most consequential unresolved assumption, next test and its predeclared interpretation. | Opportunity risk, startup builder |

Reuse [strategic positioning](../../../../references/strategic-positioning.md) as the shared source for entrant fit, comparative coverage and economic definitions. Do not repeat its full rules in each skill. Distinguish evidence, inference, assumption and unknown; missing evidence is not a hard failure. A necessary unknown prevents a confident recommendation but can justify another investigation. Document demonstrated incompatibilities separately from weak coverage. Do not force selection if no case is ready.

**Insurance illustration, not new findings:** the Chinese-language case should ask which journey actually requires language support, how customers currently cope and whether language changes trust or conversion; the discount-motor case should ask what could fund the discount and what partner/access dependencies exist. Both need comparable acquisition, service effort and cash assumptions. These are research questions, not claims of demand, margin or legal permission. Annual insurance renewal should not be judged by daily app use.

**Acceptance:** use fixed evidence fixtures containing a complaint without spend, a job posting without a purchase, a one-off launch spike, and missing acquisition costs. The assessment must preserve those distinctions and avoid invented numbers. Review a one-off service and recurring business to ensure the template does not impose subscription/app assumptions. For implemented behavior, run the existing eval harness on these tasks and manually inspect outputs; headings alone do not establish research quality.

## Work package 3 — Small, auditable economics

**Value:** distinguish a plausible market story from a business that can meet the founder's income, cash and capacity constraints.

Add one compact economics data contract for cases: currency, period, unit/customer definition, model type, source-linked input status, one-time costs, recurring fixed costs, variable delivery/acquisition costs, founder compensation, cash timing and scenario assumptions. Unknown inputs remain null/unresolved. Use an explicit small set of supported calculation types; do not evaluate arbitrary formula strings. Add a small calculation helper only where current code has no equivalent.

Calculate contribution, required customer/sale volume, affordable acquisition spend/payback when meaningful, monthly cash needs and capacity constraints. Separate cash cost from founder opportunity cost and avoid charging the same labor twice. Recurring models need cohort/renewal assumptions; transactional models need net contribution per completed sale. Use base/downside and decision-changing sensitivities, with upside optional. No probability-weighted forecast without defensible probabilities.

The model is authoritative for numbers; narrative documents reference its revision/results. Extend existing strategy validation to check required inputs, units, period alignment, calculations and selected-plan dependencies. Structural correctness cannot validate demand or estimates.

**Synthetic acceptance fixture:** revenue per sale 100, variable service cost 25, partner cost 10 and acquisition cost 15 give contribution 50. Fixed costs 1,500 plus owner compensation 2,500 require 80 completed sales/month. If demonstrated capacity is 60, the case does not meet the target under those assumptions despite positive contribution. Also test zero/negative contribution, delayed cash receipt, upfront versus recurring revenue, absent inputs and double-counted labor.

**Depth limit:** do not make five-year forecasts, valuation, integrated three-statement accounts or financing mechanics mandatory for early idea comparison. Escalate detail only for the selected business and its planning audience. Missing financing/legal/tax/IP work stays visible rather than being filled with generic prose.

## Work package 4 — Root business plan and safe adoption

**Value:** one coherent plan for the chosen business, supported by current research and calculations.

Give the existing startup builder responsibility for assembling root `strategy/business-plan.md`. Reuse the existing `strategy-plan.json` as the authority for selected positioning, experiments, KPIs and commitments; add selection/revision and section/source bindings rather than introduce another strategy state store. The Markdown plan synthesizes those records and current case evidence. Financial values come from the supporting model. The project README remains a brief overview.

Check coverage proportionately: business/customer description, market and competitive choice, product/service and revenue model, acquisition/sales, delivery/team, finances, milestones/risks, and conditional funding/legal/IP requirements. Each section is supported, provisional, missing or not applicable with a reason. Preserve the distinction between a complete document and a validated/executable plan. If selected evidence changes, mark affected sections/handoffs review-required; do not silently select another case.

Fold scope-amendment criteria into the existing MVP/pilot output: a new feature requires evidence that it enables the chosen outcome or required trust, together with cost/capacity consequences. Do not create full product/marketing/brand plans for all alternatives.

**Existing surfaces:** startup-builder workflow, [strategy schema](../../../../schemas/strategy-plan.schema.json), [strategy review](../../../../scripts/strategy_review.py), strategy/business-to-brand handoff builders and validators, project templates and lifecycle docs. Case-aware route/selection checks from package 1 must be consumed here too.

**Acceptance and rollout:** first use disposable synthetic projects; then rehearse on a copy of German insurance. Inventory all existing files and links, create a reversible mapping, and preserve raw/run paths. Existing umbrella conditional passes do not qualify every new case. Compare hashes and source references; exercise switch, correction, archive, interruption and rollback. Do not migrate the live insurance workspace or unrelated projects automatically. After the full case path passes, new projects use it by default; legacy projects remain readable under their existing layout until explicit migration.

## Implementation order and review boundary

1. Package 1 defines the identities, selection and output boundaries; write its meaningful regression cases first and inventory affected writers.
2. Package 2 supplies the human-readable content contract, reusing existing specialist ownership.
3. Package 3 provides calculations and consistency checks for that content.
4. Package 4 assembles the selected plan and completes end-to-end rehearsal before default enablement.

Extend existing tests where possible: [workspace gates](../../../../tests/test_workspace_gates.py), [workspace tests](../../../../scripts/evidence_scout/test_workspace.py), [strategy review](../../../../tests/test_strategy_review.py), routing and handoff suites. Run applicable targeted tests, then `python3 scripts/validate_skill_routes.py`, `bash scripts/validate_setup.sh` and `python3 scripts/run_evals.py`. Record pre-existing failures separately; never claim all checks passed without running them. Include a small fixed-task semantic evaluation for research quality; structural checks alone are insufficient.

Stop expanding when users can compare current cases, inspect feasibility/economics, choose one, read its coherent plan and trace history, with the isolation and evidence checks above passing. Add no new skill, provider, app, automatic recurring research, scoring engine or UI unless a demonstrated remaining failure needs it. Folder/history rules belong in one contract; specialized detail loads only when relevant. Preserve attribution/license notices for any actual copied source material; this plan proposes adapted requirements rather than wholesale prompt imports.

Plan review by the root agent: the concrete risks are hardcoded output roots, duplicated state, weak evidence promoted into numerical certainty, and stale execution handoffs. The packages and checks address those risks. No independent reviewer or implementation tests were run for this plan. The inspected external files are design references, not tested dependencies.

Sources retrieved 13 September 2026: the source links in the adoption table; [MackDing main skill](https://raw.githubusercontent.com/MackDing/ai-native-founder-playbook-skill/main/ai-native-founder-playbook/SKILL.md). MackDing's detailed references were retrieved directly from raw GitHub after the web renderer failed to fetch them. Local contracts were checked in the current checkout. See also the earlier [coverage audit](../business-plan-coverage-and-open-source.md) and [review history](../REVIEW-LOG.md).
