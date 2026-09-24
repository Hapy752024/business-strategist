import json
from pathlib import Path
from scripts import case_workspace as c
base=Path('/tmp/case-semantic-eval-20260913'); root=base/'projects/topic'; run=base/'run'
prompt='''Run a controlled actual-agent semantic evaluation, not a code review. Workspace repo /mnt/c/coding/general/business-strategist. Disposable synthetic project /tmp/case-semantic-eval-20260913/projects/topic already exists with cases a,b and fixed evidence. No web, live-project evidence, paid calls, other agents or repo edits. Task: assess feasibility and high-level economics of both cases, compare them without implicitly choosing an execution target, using existing opportunity-risk-designer appraisal mode and references/case-assessment.md. Read those declared inputs only plus necessary helper API. Obtain real route packets via scripts.route_workflow.route_request with ROOT temporarily set to Path('/tmp/case-semantic-eval-20260913'), project='topic', case_id, intent='case-appraisal', task_scope='strategy', check_skill='opportunity-risk-designer'; config paths retain real repo. Publish actual authored README.md, feasibility.md and business-case.md through case_workspace.publish_assessment using evidence bindings/current revision. Save route packets, exact task prompt, your actual response and host/model identification (unknown if unavailable) to /tmp/case-semantic-eval-20260913/run/. Do not invent economics inputs to fill gaps; use calculator only if appropriate. Then perform two recorded follow-ups through normal publication: (1) interpretive correction: the complaint was hypothetical roleplay, not a firsthand customer report; update all affected A conclusions, preserve prior versions and no selection; (2) B title spelling correction with no meaning change, preserving assessment revision and comparison conclusion. Save both follow-up prompts and your actual response. Work independently, report artifact paths and limitations. This is evaluation against supplied synthetic evidence, not market research.'''
(run/'task-prompt.txt').write_text(prompt+'\n')
(run/'host-model.json').write_text(json.dumps({'host':'Codex agent tool session','agent_task':'/root/case_semantic_runner','model':'unknown','model_note':'No exact model identifier exposed to this agent. Developer describes agent as based on GPT-6; this is not independent runtime identification.','evaluation':'actual agent-authored appraisal of synthetic fixed evidence','web_retrieval':False,'numerical_model':'not run: material monetary and operating inputs absent','fixture_note':'B document headings intentionally contain the clerical typo transations to exercise a later spelling correction. Registry title is correctly spelled and unchanged.'},indent=2)+'\n')
comparison='''Both cases remain under investigation with no execution selection. A has a reported wording complaint and unmeasured launch interest; B has only a supplier discount promise. These are different evidence types, not comparable proof of paid demand. A's annual assistance cycle requires next-renewal evidence; B's one-off model requires transaction economics and a repeat-use rationale. Missing founder budget, time, skills and intended scale prevent a founder-fit ranking. The older recommendation for A is superseded by the latest unresolved buying-trigger note. Neither a forced winner nor rejection of both is justified.'''
a={
'README.md':'''# Language assistance

## Current concept and scope
A is annual renewal language assistance, provisionally for a German resident facing complex wording. User fit, buyer and payer remain unresolved. This is a synthetic appraisal, not a market finding.

## Current decision
Investigate. The supplied complaint is a pain clue, with no purchase, paid workaround or willingness to pay. The latest field note leaves the buying trigger unresolved; the older opinion favoring A does not settle it.

## Findings that matter
The foreign bilingual-staff job posting has a different geography and buyer. It may suggest a staffing capability to examine, but establishes no local contract or demand for A. The 1,000 first-day visits are exposure only: qualified visitors, contacts, purchases and subsequent renewal behavior are unmeasured. Losing money on support, errors or acquisition is a consequential possibility, not an observed outcome.

See [feasibility](feasibility.md) and [business case](business-case.md). '''+comparison+'''

## Next action
Propose an unpaid recent-renewal interview with a screened resident, recording their actual trigger, workaround, consequences and who would pay. A specific recent incident supports further investigation; vague opinions leave the hypothesis unresolved. A discussion alone cannot pass a paid-demand gate. No outreach is authorized or performed. Prior versions: [project history](../../history/evolution.md).
''',
'feasibility.md':'''# Feasibility: Language assistance

## Delivery requirements
The concept could be examined first as manually reviewed language assistance; that is an option, not a confirmed operating capability. Bilingual skill, access to appropriate documents, consent/data handling, scope boundaries and any applicable permissions remain unknown. Build, buy and partner choices cannot be settled by the foreign job posting. No evidence establishes access to staff or partners. AI is not required by the concept; if later used, reliability would need task-specific review.

## Time, cost and capacity
Setup time and cash, minutes per case, manual review, rework, support, seasonal workload and founder availability are unknown. Review capacity is a plausible bottleneck, not an observed one. Founder dependence and reversal costs are unquantified. No throughput or launch date can be responsibly given.

## Blockers and next check
The reported wording problem provides a candidate task but does not establish what output a buyer needs. Propose a consented example walkthrough with a capable reviewer, identifying effort, errors and escalation boundaries before building. Accept as a feasibility learning result only if the reviewer can describe a bounded deliverable and its measured effort; unresolved access or safe scope keeps delivery feasibility open. This does not validate payment or authorize implementation.
''',
'business-case.md':'''# Business case: Language assistance

## Customer choice and commercial evidence
The candidate trigger is an annual renewal whose wording a resident finds difficult. User, contracting buyer and payer must be established separately. The reported complaint contains no purchase, paid workaround or stated willingness to pay. Actual alternatives, including self-reading, seeking informal help or doing nothing, are hypotheses for inquiry, not observed workarounds. Trust, switching friction and reasons to choose this entrant are unknown. The foreign staffing example supplies no contract for this case.

## Reach, revenue and delivery economics
The launch post's 1,000 first-day visits are not customers or conversion evidence. Audience fit, unique-person denominator, acquisition spend, founder time, qualified inquiries and purchases are unknown; CAC cannot be calculated. Annual assistance does not need daily usage, but renewal, referral, time to value and cancellation reasons were not measured.

A per-assistance venture fee is a possible mechanism, not an established price or recurring subscription. Revenue basis, currency, fee, refunds, partner/service expense, owner cash, fixed cost, capacity and acquisition basis are unknown. Opening cash, sales schedule and payment lags are also missing. Contribution would depend on venture receipts less delivery, partner, refunds and attributable acquisition cost, without counting founder effort twice. No margin, break-even, LTV, runway or profit estimate is supported. No calculator was run and no economics input digest exists because the record lacks the model-defining inputs.

## Alternatives and decision
'''+comparison+'''

Doing nothing avoids committing scarce resources while uncertainties remain; its customer cost is unmeasured. The pivotal question is whether a recent renewal produces a sufficiently consequential job for an identifiable payer. The next unpaid interview can establish an experienced problem and workaround; only later behavioral/payment evidence could establish demand for this entrant. No commitments or selection follow from this appraisal.
'''}
b={
'README.md':'''# Discount transations

## Current concept and scope
B concerns one-off discounted transactions. The supplied material does not identify the target customer, buyer, payer or transaction category precisely. This is a synthetic appraisal, not a market finding.

## Current decision
Investigate the discount's source and enforceability. A supplier brochure promises lower prices, but provides no agreement or identified party funding the reduction. This does not establish obtainable pricing or customer demand.

## Findings that matter
No evidence establishes customer purchases, entrant choice, an acquisition route or delivery capacity. A discount that the venture must absorb could erase contribution; that is a failure hypothesis, not a measured loss. See [feasibility](feasibility.md) and [business case](business-case.md). '''+comparison+'''

## Next action
Propose inspection of an applicable written quote/agreement identifying who funds the discount, eligible transactions, settlement and clawbacks. Clear applicable terms permit an economics appraisal, not a demand claim. Missing or conditional funding leaves the offer unresolved. No supplier contact or spending is authorized or performed. Prior versions: [project history](../../history/evolution.md).
''',
'feasibility.md':'''# Feasibility: Discount transations

## Delivery requirements
The decisive dependency is obtaining applicable supplier terms and identifying discount funding. A brochure is insufficient evidence of access or enforceability. Partner integration, order/payment handling, eligibility checks, permissions, refunds and dispute ownership are unestablished requirements to investigate. A manual process could be explored after terms are known; no build, buy or partner choice is supported yet.

## Time, cost and capacity
Agreement lead time, setup cash, labor per transaction, review/rework/support, founder availability, settlement lag and reversal cost are unknown. Supplier availability or exception handling might limit capacity; neither has been measured. There is no supported delivery date or throughput forecast.

## Blockers and next check
Inspect written terms applicable to the actual customer and transaction, with a traceable source of the price reduction and responsibilities. If they show an accessible, funded discount and workable fulfillment boundaries, proceed to costing. If funding remains unidentified, delivery and commercial feasibility remain unresolved. No implementation or supplier action is authorized.
''',
'business-case.md':'''# Business case: Discount transations

## Customer choice and commercial evidence
The only supplied commercial statement is supplier marketing that promises lower prices. No agreement, funded discount, completed purchase, paid workaround or willingness to pay the entrant is established. The trigger, user/buyer/payer, alternatives including buying directly or doing nothing, trust and switching effort are unknown. Lower advertised price alone does not explain entrant choice.

## Reach, revenue and delivery economics
Acquisition channel, eligible-customer denominator, effort, spend and conversion are missing. One-off transactions need no daily engagement, but any repeat or referral value must be observed before assuming it. Time to value, dispute/refund behavior and repeat occasions are unknown.

The entrant could hypothetically earn a fee or commission, but neither is evidenced. Gross transaction value is not automatically venture revenue. Identify who funds the discount and who bears refunds before estimating contribution. Currency, venture receipts, supplier/service/partner expense, acquisition cost, fixed costs, owner cash, capacity, opening cash, monthly transaction schedule and payment lags are unknown. Hence margin, required volume, break-even and working-capital need cannot be quantified. No calculator was run and no economics input digest exists because material inputs and revenue basis are absent.

## Alternatives and decision
'''+comparison+'''

Doing nothing avoids exposure to unsupported discount economics. The pivotal uncertainty is a funded, accessible supplier arrangement; reviewing applicable terms is the next check. Favorable terms would support costing only, not customer demand or execution selection. Unfavorable terms may warrant redesign; absence of terms today is insufficient to declare the whole concept impossible.
'''}
for case,docs in [('a',a),('b',b)]:
 bindings=[c.source_binding(root,f'cases/{case}/market_research/{s}/evidence.md',locator='Fixed synthetic evaluation evidence, paragraph 1',applicability=f'Case {case.upper()} appraisal: use relevant case facts only; synthetic fixture, not external market proof') for s in ['customer_segments','customer_journey','pain_points']]
 peer='b' if case=='a' else 'a'
 bindings.append(c.source_binding(root,f'cases/{peer}/market_research/pain_points/evidence.md',locator='Fixed synthetic evaluation evidence, paragraph 1: cross-case facts',applicability='Comparison only; do not transfer foreign staffing or supplier claims into proof of local customer demand'))
 packet={'assessment_revision':c.case_manifest(root,case)['assessment_revision'],'documents':docs,'source_bindings':bindings}
 (run/f'initial-{case}-input.json').write_text(json.dumps(packet,indent=2)+'\n')
 c.publish_assessment(root,case,packet,f'appraise-{case}-initial','Initial bounded synthetic case appraisal; no execution selection')
response='''Both synthetic cases remain under investigation; neither is selected for execution. A has a reported wording complaint and unmeasured launch interest, but no paid-demand evidence. Its foreign staffing example does not transfer to the German resident/buyer, and 1,000 first-day visits do not establish annual renewal value. The latest unresolved buying-trigger note supersedes the older recommendation. B has a supplier discount promise with neither an agreement nor identified funding. Neither case supports numerical margins, break-even or cash forecasts. The next checks are A's actual recent-renewal behavior and payer, and B's applicable funded supplier terms. Published each case's README.md, feasibility.md and business-case.md with source bindings; calculator omitted because material inputs are absent. Selection remains null. B headings contain an explicitly recorded controlled spelling typo for the follow-up exercise.'''
(run/'response-initial.md').write_text(response+'\n')
print(response)
