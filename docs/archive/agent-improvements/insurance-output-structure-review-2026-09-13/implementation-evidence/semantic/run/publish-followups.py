import json
from pathlib import Path
from scripts import case_workspace as c, route_workflow as r
base=Path('/tmp/case-semantic-eval-20260913'); root=base/'projects/topic'; run=base/'run'; r.ROOT=base
prompt='Interpretive correction: the complaint was hypothetical roleplay, not a firsthand customer report. Update all affected A conclusions, preserve prior versions, and do not select an execution target.'
(run/'followup-1-prompt.txt').write_text(prompt+'\n')
old={case:{n:(root/f'cases/{case}/{n}').read_text() for n in ['README.md','feasibility.md','business-case.md']} for case in ['a','b']}
reason='The complaint was hypothetical roleplay, not a firsthand customer report. Withdraw firsthand pain interpretations for A and refresh cross-case comparisons; no execution selection.'
c.correct(root,['a'],reason,'correct-roleplay',source_path='cases/a/market_research/pain_points/evidence.md')
initial_comparison="Both cases remain under investigation with no execution selection. A has a reported wording complaint and unmeasured launch interest; B has only a supplier discount promise. These are different evidence types, not comparable proof of paid demand. A's annual assistance cycle requires next-renewal evidence; B's one-off model requires transaction economics and a repeat-use rationale. Missing founder budget, time, skills and intended scale prevent a founder-fit ranking. The older recommendation for A is superseded by the latest unresolved buying-trigger note. Neither a forced winner nor rejection of both is justified."
comparison="Both cases remain under investigation with no execution selection. A has a hypothetical roleplay scenario and unmeasured launch interest; there is no firsthand customer pain report in the supplied record. B has only a supplier discount promise. The correction weakens A's pain support; it supplies no new support for B and does not justify a winner. A's annual assistance cycle requires evidence from actual renewals; B's one-off model requires funded transaction economics and an observed repeat-use rationale. Missing founder budget, time, skills and intended scale prevent a founder-fit ranking. The older recommendation for A is superseded by the latest unresolved buying-trigger note and this roleplay clarification. Neither a forced winner nor rejection of both is justified."
replacements={
'A is annual renewal language assistance, provisionally for a German resident facing complex wording.':'A is annual renewal language assistance, provisionally aimed at German residents. The supposed resident complaint was hypothetical roleplay; it cannot establish an experienced wording problem or validate this segment.',
'Investigate. The supplied complaint is a pain clue, with no purchase, paid workaround or willingness to pay.':'Investigate from an unvalidated problem hypothesis. The supplied complaint was hypothetical roleplay, not a firsthand report or observed pain clue; it establishes no purchase, paid workaround or willingness to pay.',
'Propose an unpaid recent-renewal interview with a screened resident, recording their actual trigger, workaround, consequences and who would pay.':'First establish whether an actual screened resident recently experienced the hypothesized wording problem. Propose an unpaid recent-renewal interview, recording their actual trigger, workaround, consequences and who would pay.',
'The reported wording problem provides a candidate task but does not establish what output a buyer needs.':'The hypothetical wording scenario supplies an imagined task only. No actual customer task, affected resident or needed buyer output has been established; feasibility remains conditional on discovering that task.',
'The candidate trigger is an annual renewal whose wording a resident finds difficult.':'The hypothesized trigger is an annual renewal with difficult wording; the roleplay does not establish that a real resident experienced it.',
'The reported complaint contains no purchase, paid workaround or stated willingness to pay.':'The complaint is hypothetical roleplay, not firsthand customer evidence; it establishes neither experienced pain nor purchase, paid workaround or stated willingness to pay.',
'The pivotal question is whether a recent renewal produces a sufficiently consequential job for an identifiable payer.':'The pivotal question now starts earlier: whether actual residents experience this renewal problem at all, before testing consequence and identifying a payer.'}
for case in ['a','b']:
 route=r.route_request(prompt,project='topic',case_id=case,intent='case-appraisal',task_scope='strategy',check_skill='opportunity-risk-designer')
 (run/f'route-followup-1-{case}.json').write_text(json.dumps(route,indent=2)+'\n')
 docs={n:body.replace(initial_comparison,comparison) for n,body in old[case].items()}
 if case=='a':
  for n in docs:
   for previous,current in replacements.items(): docs[n]=docs[n].replace(previous,current)
 for n in docs:
  docs[n]+='\nCurrent interpretation: the [recorded roleplay correction](../../history/decisions/correct-roleplay.md) overrides the original synthetic fixture wording wherever that wording appears. Original evidence bytes and superseded advice remain archived.\n'
 bindings=json.loads((run/f'initial-{case}-input.json').read_text())['source_bindings']
 bindings.append(c.source_binding(root,'history/decisions/correct-roleplay.md',locator='Decision reason: complaint was hypothetical roleplay',applicability='Overrides the apparent firsthand complaint in all duplicate fixture evidence; A pain/segment/journey and cross-case comparison must reflect this clarification'))
 packet={'assessment_revision':c.case_manifest(root,case)['assessment_revision'],'documents':docs,'source_bindings':bindings}
 (run/f'followup-1-{case}-input.json').write_text(json.dumps(packet,indent=2)+'\n')
 c.publish_assessment(root,case,packet,f'appraise-{case}-roleplay','Reappraise after material roleplay clarification and refresh all affected current narratives')
response='''The correction removes A's apparent firsthand pain evidence. A now rests on a hypothetical customer/problem scenario plus unmeasured launch interest; its segment, buying trigger and payer require direct investigation. I updated all three A narratives and B's comparison, archived the prior advice through the correction/publication helpers, and bound the clarification to both cases. B receives no new evidence from this correction, so both remain under investigation with no selected execution target. Economic unknowns remain unresolved.'''
(run/'response-followup-1.md').write_text(response+'\n'); print(response)
(run/'comparison-after-followup-1.md').write_text(comparison+'\n')
prompt2="Correct B's document title spelling from 'Discount transations' to 'Discount transactions' only. No meaning changes. Preserve its assessment revision, source bindings, comparison conclusion and unset execution selection."
(run/'followup-2-prompt.txt').write_text(prompt2+'\n')
route=r.route_request(prompt2,project='topic',case_id='b',intent='case-appraisal',task_scope='strategy',check_skill='opportunity-risk-designer')
(run/'route-followup-2-b.json').write_text(json.dumps(route,indent=2)+'\n')
before=c.case_manifest(root,'b'); docs={n:(root/f'cases/b/{n}').read_text() for n in ['README.md','feasibility.md','business-case.md']}
packet={'assessment_revision':before['assessment_revision'],'material_change':False,'source_bindings':before['source_bindings'],'documents':{n:body.replace('Discount transations','Discount transactions') for n,body in docs.items()}}
(run/'followup-2-b-input.json').write_text(json.dumps(packet,indent=2)+'\n')
c.publish_assessment(root,'b',packet,'spell-b-title','Correct controlled clerical typo in B document titles; no meaning or evidence change')
after=c.case_manifest(root,'b'); project=c.read_project(root)
checks={'b_assessment_revision_before':before['assessment_revision'],'b_assessment_revision_after':after['assessment_revision'],'b_revision_preserved':before['assessment_revision']==after['assessment_revision'],'b_source_bindings_preserved':before['source_bindings']==after['source_bindings'],'only_spelling_changed':all((root/f'cases/b/{n}').read_text()==body.replace('Discount transations','Discount transactions') for n,body in docs.items()),'comparison_preserved':all(comparison in (root/f'cases/{case}/business-case.md').read_text() for case in ['a','b']),'selection':project['selection'],'selection_generation':project['selection_generation'],'assessment_revisions':{case:c.case_manifest(root,case)['assessment_revision'] for case in ['a','b']},'pending_transaction':(root/'history/pending.json').exists(),'calculator_run':False,'evidence_note':'Original fixture files unchanged; interpretation correction recorded and bound in history.'}
assert checks['b_revision_preserved'] and checks['b_source_bindings_preserved'] and checks['only_spelling_changed'] and checks['comparison_preserved'] and checks['selection'] is None and checks['selection_generation']==0 and not checks['pending_transaction']
(run/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
response2=f"Corrected B's three document headings from 'Discount transations' to 'Discount transactions'. Its assessment revision remains {after['assessment_revision']}; source bindings and comparison wording are unchanged. Both cases remain under investigation, and execution selection remains null. Prior versions are retained in the normal publication history."
(run/'response-followup-2.md').write_text(response2+'\n'); print(response2)
(run/'final-comparison.md').write_text(comparison+'\n\nLimits: synthetic evidence only; no market retrieval, customer contact, paid calls or numerical economics model. Equal missing monetary inputs are visible; the evidence types and unknown founder constraints do not support a feasibility or profitability ranking. The roleplay correction reduces confidence in A without changing the no-selection conclusion. The spelling correction changes no conclusion.\n')
print(json.dumps(checks,indent=2))
