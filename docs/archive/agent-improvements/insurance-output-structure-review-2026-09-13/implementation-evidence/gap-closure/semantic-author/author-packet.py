import json
from pathlib import Path
from scripts.economics_text import render
root=Path('/tmp/gap-closure-semantic')
inputs=json.loads((root/'economics-inputs.json').read_text())
record=json.loads((root/'economics-record.json').read_text())
comparison='The supplied base case cannot meet its fixed expenses and additional owner cash requirement within the stated capacity. This is conditional arithmetic, not proof that customers will buy or that every alternative is infeasible. Doing nothing avoids committing resources to an unvalidated offer. Redesign may be investigated, but no alternative case or supported downside range was supplied, so there is no justified winner or execution selection.'
uncertainty='Whether an identifiable buyer will complete a purchase on terms that support a capacity-feasible model. Current complaints do not answer that question; the supplied economics also fail the current capacity test.'
next_action='Investigate the actual buyer, recent problem, workaround and credible purchase terms without launching. Separately obtain support for decision-changing fee, delivery cost, owner-cash and capacity assumptions, then recalculate only evidenced or explicitly supplied alternatives. A specific experienced problem supports further investigation; stated intent or complaints alone do not establish purchase demand. Supported economics that fit capacity permit further consideration but still do not prove demand or authorize execution. If neither willingness to transact nor feasible delivery terms can be substantiated, pause commitment.'
docs={
'README.md':'''# Synthetic transactional service

## Current concept and scope
A service sold by completed sale, with supplied hypothetical financial inputs in EUR per month. Customer segment, buyer, payer, transaction trigger, workaround and reasons to trust or choose this entrant are unspecified. Complaints are possible pain evidence, not completed purchases or willingness to pay this entrant. No proven purchase demand is supplied.

## Current decision
Investigate and revise before considering commitment. The conditional contribution per completed sale is EUR {{economics.results.contribution_per_unit}}. Required monthly sales to cover the supplied fixed expenses and additional owner cash are {{economics.results.required_sales}}, against a capacity limit of {{economics.inputs.capacity_per_month}} completed sales per month. The model's capacity-meets-target result is {{economics.results.capacity_meets_target}}. The present assumptions therefore fail that capacity test even before demand is established.

## Findings and next action
'''+comparison+'''

The acquisition calculation applies the supplied customer acquisition cost once per completed sale; customer-to-sale mapping and repeat behavior are not validated. The inputs are scenario assumptions, not observed operating results. Cash sufficiency, payback, downside ranges and imputed owner labor remain unresolved. See [feasibility](feasibility.md) and [business case](business-case.md).

'''+next_action+'''
''',
'feasibility.md':'''# Feasibility: Synthetic transactional service

## Delivery requirements
A completed sale is the unit of delivery. The type of service, required people, tools, partner availability, data access, permissions and skill requirements have not been supplied. Build, buy and partner choices remain open. No claim of technical or regulatory feasibility follows from the financial inputs. Founder dependence, setup lead time, manual review, rework and support needs require task-specific observation.

## Cost and capacity
The supplied service expense per completed sale is EUR {{economics.inputs.service_per_unit}}, partner expense is EUR {{economics.inputs.partner_per_unit}}, and refund expense is EUR {{economics.inputs.refund_per_unit}}. These are assumptions, not verified rates or a claim that refunds cannot occur. Monthly fixed expense is EUR {{economics.inputs.fixed_per_month}}; additional owner cash is EUR {{economics.inputs.owner_cash_per_month}}. That owner cash is explicitly additional to service expense, so it must not be counted there again. Imputed owner opportunity cost remains unresolved and is not silently treated as zero.

The assumed capacity limit is {{economics.inputs.capacity_per_month}} completed sales per month, while required monthly sales are {{economics.results.required_sales}}. Capacity meets target: {{economics.results.capacity_meets_target}}. The current model cannot deliver enough sales to cover its specified requirements. Extra sales cannot solve this without a supported capacity change; extra capacity might also change expenses and founder effort.

## Blockers and next check
Measure the delivery task and limiting resource, verify the partner and service terms, and identify whether a bounded redesign can change a decision-relevant input. Recalculate the full affected model rather than holding related expenses constant without justification. Unknown cash horizon, startup cash, opening cash, collection/payment timing and volume schedule prevent a cash-sufficiency or launch-funding conclusion. This assessment does not authorize implementation.
''',
'business-case.md':'''# Business case: Synthetic transactional service

## Customer choice and commercial evidence
No completed purchase demand is proven. Customer complaints do not establish current spending, a paid workaround, a buyer, a payer or willingness to buy from this entrant. The supplied receipt per completed sale is a modeling assumption, not an observed price accepted by customers. Trigger, alternatives including doing nothing, trust, switching friction and entrant preference remain unknown.

## Reach and bounded economics
The model is transactional, monthly, denominated in EUR, with venture receipts rather than pass-through transaction value. Venture revenue per completed sale is EUR {{economics.inputs.revenue_per_unit}}. Acquisition expense is EUR {{economics.inputs.acquisition_per_new_customer}} per acquired customer; the conditional calculation allocates it once per sale. A repeat-purchase or multi-sale relationship has not been supplied and must not be assumed to improve the result. Acquisition channels, qualified audience denominator, spend efficiency and founder selling effort are unverified.

Conditional contribution per completed sale is EUR {{economics.results.contribution_per_unit}} after the supplied service, partner, refund and allocated acquisition expenses. Required monthly sales are {{economics.results.required_sales}} to cover fixed expenses plus additional owner cash. Capacity limit is {{economics.inputs.capacity_per_month}} completed sales per month; capacity meets target: {{economics.results.capacity_meets_target}}. This conditional result fails the supplied capacity test and is not a forecast or purchase validation.

Imputed owner labor is unresolved. There is no supported cash horizon, opening cash, startup cash, payment timing or sales schedule. Payback month is {{economics.results.payback_month}}. Cash sufficiency and runway cannot be determined. Downside ranges and sensitivity intervals are unsupported, so none are invented. Time to customer value, refunds in practice, repeat use, referral and reasons for cancellation are also unmeasured; a one-off service does not require daily use.

## Alternatives and decision
'''+comparison+'''

Principal uncertainty: '''+uncertainty+'''

Next action: '''+next_action+'''
'''}
packet={'documents':docs,'economics_inputs':inputs,'economics_input_digest':record['input_digest'],'comparison_summary':comparison,'principal_uncertainty':uncertainty,'next_action':next_action}
(root/'author-initial.json').write_text(json.dumps(packet,indent=2)+'\n')
# Read-only rendering verifies numeric tokens and authored digest against calculator output.
for name,body in docs.items():
 (root/('rendered-'+name)).write_text(render(body,record,record['input_digest']))
(root/'author-validation.json').write_text(json.dumps({'rendered_all_documents':True,'economics_input_digest':record['input_digest'],'revisions_and_source_bindings':'intentionally omitted; harness supplies','publication':'not performed; author packet only','limits':'synthetic supplied inputs, no web or live research'},indent=2)+'\n')
print(root/'author-initial.json')
print(root/'pilot-amendment.md')
