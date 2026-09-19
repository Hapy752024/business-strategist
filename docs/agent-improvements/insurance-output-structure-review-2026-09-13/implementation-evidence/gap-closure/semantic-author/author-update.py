import json,hashlib
from pathlib import Path
from scripts.economics_text import render
p=Path('/tmp/gap-closure-semantic')
historical=['author-initial.json','economics-inputs.json','economics-record.json']
before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in historical}
a=json.loads((p/'author-initial.json').read_text())
record=json.loads((p/'economics-record-updated.json').read_text())
comparison='The corrected receipt assumption makes required sales fit within the supplied capacity while covering fixed expenses and additional owner cash. This is conditional arithmetic, not proof of purchase demand, verified operational capacity or cash sufficiency. Doing nothing remains an alternative to committing resources to an unvalidated offer. Further investigation is justified, but no other case or supported downside range was supplied, so there is no comparative winner or execution selection.'
uncertainty='Whether an identifiable buyer will complete a purchase on the corrected receipt terms at a sustainable acquisition and delivery cost. Complaints do not answer that question. The numerical capacity hurdle is now cleared conditionally, while actual demand, delivery capacity and cash timing remain unverified.'
next_action='Investigate actual buyers, recent problems, workarounds and evidence of acceptance of the corrected receipt terms without launching. Verify acquisition, delivery and capacity assumptions, and obtain supported cash timing and downside inputs before judging resilience. A specific experienced problem supports further investigation; complaints or stated intent alone do not establish purchase demand. The conditional capacity fit permits further consideration but does not authorize execution. If purchase behavior or operational terms cannot be substantiated, pause commitment.'
replacements={
 a['comparison_summary']:comparison,
 a['principal_uncertainty']:uncertainty,
 a['next_action']:next_action,
 'Investigate and revise before considering commitment.':'Investigate demand and verify operations before considering commitment.',
 'The present assumptions therefore fail that capacity test even before demand is established.':'The corrected assumptions therefore pass that numerical capacity test; demand and the assumed operating capacity still require validation.',
 'The current model cannot deliver enough sales to cover its specified requirements. Extra sales cannot solve this without a supported capacity change; extra capacity might also change expenses and founder effort.':'The corrected model fits the required volume inside the assumed capacity. This removes the previous numerical mismatch; it does not demonstrate that enough customers will buy or that the assumed throughput is deliverable. Review, rework, support and founder constraints still need measurement.',
 'Measure the delivery task and limiting resource, verify the partner and service terms, and identify whether a bounded redesign can change a decision-relevant input. Recalculate the full affected model rather than holding related expenses constant without justification.':'Measure the delivery task and limiting resource, and verify the partner and service terms against the assumed throughput. A redesign is no longer required solely to fix the base-case numerical capacity mismatch. Recalculate if the operating checks change any affected input; do not hold related expenses constant without justification.',
 'This conditional result fails the supplied capacity test and is not a forecast or purchase validation.':'This conditional result passes the supplied capacity test and is not a forecast or purchase validation.'}
docs={}
for name,text in a['documents'].items():
 for old,new in replacements.items(): text=text.replace(old,new)
 docs[name]=text
packet={'documents':docs,'economics_inputs':record['inputs'],'economics_input_digest':record['input_digest'],'comparison':{'summary':comparison,'principal_uncertainty':uncertainty,'next_action':next_action}}
(p/'author-updated.json').write_text(json.dumps(packet,indent=2)+'\n')
for name,text in docs.items(): (p/('rendered-updated-'+name)).write_text(render(text,record,record['input_digest']))
assert before=={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in historical}
(p/'author-update-validation.json').write_text(json.dumps({'rendered_all_documents':True,'historical_inputs_preserved':before,'economics_input_digest':record['input_digest'],'capacity_conclusion':'conditional fit; does not authorize execution','metadata':'revision/source bindings intentionally absent'},indent=2)+'\n')
(p/'correction-response.md').write_text('With the corrected EUR 150 receipt assumption, calculator contribution is EUR 100 per completed sale and required sales are 40 per month against capacity of 60. The numerical capacity conclusion changes from failure to conditional fit. Purchase demand remains unproven, operating assumptions are unverified, and cash timing, downside ranges and imputed labor remain unresolved. This correction does not authorize execution or select a business. All three current narratives and the comparison object were updated; original authored inputs are unchanged.\n')
print(p/'author-updated.json')
