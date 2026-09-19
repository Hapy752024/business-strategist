# Multiple investigations, one executable idea

Current design clarification and capability audit, 13 September 2026. This extends the [current structure proposal](REPORT.md). It changes the proposed reusable-agent contract; it does not implement routing, move research files, or produce a business plan for German insurance. The earlier three-round judge scores predate this clarification.

## Open-source comparables

These are closer business-workflow examples than the general coding/research frameworks in the first review. Inspection covered public instructions, README material and repository structure, not installed execution or independent quality benchmarks. The repositories identify themselves as MIT licensed; this is not a dependency or bundled-content license audit.

| Repository | Relevant observed pattern | What to borrow / limitation |
|---|---|---|
| [MaxKmet/idea-validation-agents](https://github.com/MaxKmet/idea-validation-agents) | Narrow validation skills write structured outputs into a directory per idea; shared market intelligence sits separately. Dropped ideas are retained. [Agent contract](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/AGENTS.md), [memory layout](https://github.com/MaxKmet/idea-validation-agents/blob/main/memory/README.md). | Closest folder/workflow match. Borrow idea identity, reusable shared research and durable assessments. Its B2C-app scope and scoring estimates do not establish observed demand or a single-execution invariant. |
| [ANVEAI/idea-hunt-skill](https://github.com/ANVEAI/idea-hunt-skill) | Pain discovery and candidate filtering lead to selection of one candidate, then an execution blueprint for that survivor. [Skill](https://github.com/ANVEAI/idea-hunt-skill/blob/main/SKILL.md). | Closest selection pattern. Its running document does not satisfy our current/history separation. Treat job postings, incumbent spending and intent as their actual evidence type, not automatic proof that a new entrant will get paid. |
| [MackDing/ai-native-founder-playbook-skill](https://github.com/MackDing/ai-native-founder-playbook-skill) | README describes discovery, MVP, PMF, launch and scale workflows with stage gates and supporting templates. | Useful lifecycle and readiness reference, focused on AI-native startups. This assessment used README/structure; a complete skill-file audit and live evaluation were not performed. |
| [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | Separate [business strategist](https://github.com/msitarzewski/agency-agents/blob/main/specialized/business-strategist.md) and [financial analyst](https://github.com/msitarzewski/agency-agents/blob/main/finance/finance-financial-analyst.md) role documents include feasibility, roadmaps, modeling and scenarios. | Useful coverage checklists, especially finance. These are role instructions; a persona's claimed experience is not evidence of expertise, correct calculations, or integrated workflow enforcement. |

My assessment: borrow selected patterns, rather than replace the existing evidence and routing system. None of this inspection establishes that a repository already provides our complete combination of case assessments, one selected execution target, clean current documents, immutable history and enforced evidence gates.

## Ownership and minimum outputs

One project can contain many investigated ideas or variants. Each substantive case needs a stable identity and a current concept; deeper files appear only when used.

| Location | Question answered | Minimum useful content |
|---|---|---|
| Project `README.md` | Where do we stand? | Investigated cases, comparable status/coverage, selected idea or no selection, decisive uncertainty, next action; links to assessments and plan. |
| Case `README.md` | What is this idea now? | Segment, problem, proposed value, scope/facets, latest findings, counter-evidence and disposition. |
| Case `feasibility.md` | Can we deliver it, and what would that involve? | Build/buy/partner options; skills, people, technology/data, permissions and partners; effort, lead time, capacity, setup costs, dependencies, unresolved blockers and cheapest informative checks. |
| Case `business-case.md` | Is choosing it economically attractive? | Buyer/revenue mechanism; reachable-demand evidence; price, acquisition, service and fixed-cost assumptions; founder compensation; startup cash and cash timing; break-even and downside; confidence and next decision-changing test. |
| Case `economics/` when needed | Where do those numbers come from? | Source-backed assumptions, explicit estimates, formulas, units and time periods, scenarios, model revision and limitations. |
| Root `strategy/business-plan.md` | How will the selected idea become a business? | Coherent selected strategy, market/customer thesis, product/service, business model, GTM, operating model/team, financial plan, milestones, risks and dependencies. Supporting models and roadmap belong alongside it. |

Compare cases using the same founder constraints, time horizon and economic definitions. Unknown demand or cost inputs remain unknown or explicit ranges. Researching implementation requirements must not become a production commitment. A lightweight case appraisal should be possible before pain validation; the implementation must distinguish this from gated business-model/offer/GTM commitments. The current router has not been changed to provide that distinction.

## Selection contract

- Keep `selected_idea_id` nullable and single-valued. Keep research focus and per-case validation status separate. Several promising or validated cases are possible; simultaneous execution selections are not.
- Bind selection to the defined execution scope/configuration and a revision. Selecting a broad parent does not authorize every related variant. A selected idea can include multiple features or audiences only when they belong to its explicitly chosen scope.
- Before selection, root materials compare alternatives and constraints. Do not present an approved full business plan for an unchosen idea. Selection does not itself prove feasibility, pass the pain gate or authorize external action.
- After selection, one root business plan and one set of execution handoffs must match that selection revision. Case assessments remain available and research on alternatives can continue.
- Switching requires an explicit user decision. Archive the prior concept/plan, update the single canonical decision record, and make prior execution handoffs unusable. The state change does not itself cancel external contracts or other real-world commitments.
- Corrected evidence or changed assumptions can make the selected plan review-required without silently choosing a different idea. The relevant readiness checks must be rerun.
- Do not aggregate revenues of mutually exclusive alternatives. Account for shared overhead and overlapping demand once within the selected scope.

Use one project evolution timeline generated from canonical decision records, tagged by case. Store actual previous concepts/plans in immutable snapshots. Keep source retrieval and operational logs with their runs. Current documents link to history without narrating every previous update.

## Business-plan coverage in this agent

The [SBA planning outline](https://www.sba.gov/counseling/plan-your-business/) is used as a completeness reference, not as German legal guidance. It covers business description, markets, organization, product/service, sales, funding and financial projections; it also permits a proportionate lean format. The following judgments compare that breadth with the inspected local workflows and output contracts. They concern documented capability, not the completeness or truth of existing insurance research.

| Business-plan area | Current coverage | Local evidence and remaining gap |
|---|---|---|
| Customer, problem, journey, market and competition | Substantial workflow coverage | Evidence/discovery/competitor workflows and pain-first rules. Actual evidence and selected-case applicability still have to be established. |
| Positioning, value proposition, business model and pricing | Substantial high-level coverage | [Strategic positioning](../../../references/strategic-positioning.md), [business model canvas](../../../templates/project/business-model-canvas.md), startup builder. This is not automatic approval of every model assumption. |
| Product/service, MVP and validation milestones | Substantial planning coverage | [Startup builder](../../../.agents/skills/startup-business-builder/references/workflow.md) and [pilot designer](../../../.agents/skills/saas-fintech-pilot-designer/references/workflow.md). Detailed engineering and sector-specific delivery require more evidence/work. |
| Marketing, sales, acquisition and retention | Substantial workflow coverage | Marketing/GTM specialists and startup builder. Forecast conversion and acquisition costs still need validation. |
| Implementation feasibility | Partial, distributed | [Risk designer](../../../.agents/skills/opportunity-risk-designer/references/workflow.md), pilot designer and operating-system workflow cover dependencies and tests. No consistent case-level feasibility artifact/completeness contract. |
| Organization and operations | Partial to substantial at planning level | [Company operating system](../../../.agents/skills/company-operating-system/references/workflow.md) covers roles, accountability, capacity, routines and cash. Detailed supply chains, facilities, inventory and sector-specific costed staffing are not standardized. |
| Unit economics and break-even | Existing coverage, incomplete standardized model | Strategic positioning explicitly requires contribution, required customer volume, labor, partner shares, churn/cancellation, cash timing and downside. The gap is a reusable model with reconciled assumptions and calculations, not an absence of economics thinking. |
| Integrated financial projections | Material output-contract gap | Cash/runway and margin prompts exist, but no established linked income/cash/balance-sheet model, working-capital/capex schedules or reconciliation checks were found in the targeted inventory. Depth should match the venture and plan audience. |
| Funding, ownership and financing | Material gap for a financing-oriented plan | Startup builder explicitly excludes fundraising mechanics from its default remit. Funding request, use of funds, debt/equity, ownership and repayment planning are not a complete established workflow. |
| Legal structure, tax, IP and regulatory implementation | Partial risk identification | Pilots can flag counsel/regulated-partner needs. That does not supply a complete legal/tax/IP plan or verified compliance feasibility. Specific diligence remains separate work. |
| One complete, coherent business plan | Assembly/validation gap | [Strategy schema](../../../schemas/strategy-plan.schema.json) focuses on positioning, experiments, KPIs and commitments. It is not a full business-plan section contract with evidence, missing-section checks and financial consistency. |

This was a targeted skill/reference/template/schema audit, not exhaustive execution testing. A language model's ability to draft a missing section does not mean the repository reliably requests, verifies or maintains it.

## Smallest useful agent adjustment

1. Introduce one case/selection/output contract used by initialization, routing, writers and downstream handoffs; keep both folder designs viable while recommending physical cases.
2. Reuse risk, pilot and operating-model capabilities to populate a standard case feasibility assessment. Reuse positioning/startup capabilities for the high-level business case, with explicit evidence and estimate labels.
3. Add a small economics model contract: assumptions, periods/units, formulas, source links and base/downside sensitivity. Increase financial-model depth only when the selected venture and plan audience need it.
4. Give the existing startup builder ownership of assembling the root business plan from current selected-case assessments and specialist outputs. Validate section coverage and cross-document consistency; represent omissions as unknown, not applicable with reason, or follow-up work.
5. Treat financing mechanics and legal/tax/IP diligence as explicit conditional gaps. Add specialist support only when the selected business actually needs it; folder restructuring alone does not create those capabilities.

Acceptance must show that comparison and feasibility work on an unselected case cannot alter the execution target; selection changes invalidate old handoffs; existing pain/authorization checks still apply; current files stay clean; history and archived versions remain discoverable. No implementation tests were run for these proposed behaviors.

Sources inspected 13 September 2026: [idea-validation agent contract](https://raw.githubusercontent.com/MaxKmet/idea-validation-agents/main/AGENTS.md), [idea memory layout](https://github.com/MaxKmet/idea-validation-agents/blob/main/memory/README.md), [idea-hunt skill](https://github.com/ANVEAI/idea-hunt-skill/blob/main/SKILL.md), [founder-playbook README](https://github.com/MackDing/ai-native-founder-playbook-skill), [agency business strategist](https://github.com/msitarzewski/agency-agents/blob/main/specialized/business-strategist.md), [agency financial analyst](https://github.com/msitarzewski/agency-agents/blob/main/finance/finance-financial-analyst.md), [SBA business-plan outline](https://www.sba.gov/counseling/plan-your-business/). Local paths above were inspected in the current checkout. No remote repository was installed or run.
