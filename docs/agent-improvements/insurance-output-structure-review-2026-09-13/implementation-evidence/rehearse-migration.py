from pathlib import Path
import json, shutil, sys, re
sys.path.insert(0, '/mnt/c/coding/general/business-strategist')
from scripts import case_workspace as c
repo=Path('/mnt/c/coding/general/business-strategist')
source=repo/'projects/german-insurance-opportunity'
parent=Path('/tmp/insurance-case-migration-20260913-final')
copy=parent/'german-insurance-opportunity'
parent.mkdir(exist_ok=True)
shutil.copytree(source,copy)
before={str(p.relative_to(source)): c.digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
links=[]
for p in source.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text(errors='replace')):
  raw=target.split('#')[0].strip('<>')
  if raw and not raw.startswith(('http:', 'https:', 'mailto:', '#')):
   dest=(p.parent/raw)
   links.append({'document':str(p.relative_to(source)), 'target':raw,'exists_before':dest.exists()})
mapping={
 'chinese-speakers':{'title':'Insurance for Chinese speakers','sources':[{'path':'market_research/customer_segments/2026-06-multilingual-segments-and-journey.md','locator':'Multilingual segments and journey','applicability':'Historical Mandarin cohort hypotheses only; reassess applicability and buying evidence.'}]},
 'english-speakers':{'title':'Insurance for English speakers','sources':[{'path':'market_research/deep_dives/2026-09-11-segment-pain-deep-dive.md','locator':'English-speaking cohort','applicability':'Historical English-speaking segment research; no inherited validation or selection.'}]},
 'discount-car-insurance':{'title':'Discount car insurance','sources':[{'path':'strategy/annex-b-motor-mga.md','locator':'Motor MGA analysis','applicability':'Legacy model/cost analysis to review; not current execution approval.'}]}}
(parent/'mapping.json').write_text(c.encoded(mapping))
# Crash after the first current replacement; exact before-images must return.
def crash(point):
 if point=='replace':raise RuntimeError('rehearsal interruption')
try:c.migrate(copy,mapping,'migration-interrupted','Rehearsal only',fault=crash)
except RuntimeError:pass
assert (copy/c.PENDING).exists()
assert c.recover(copy)=='rolled_back'
assert all(c.digest((copy/name).read_bytes())==value for name,value in before.items())
assert c.recover(copy)=='clean'
c.migrate(copy,mapping,'migration-complete','Rehearsal only; no live migration authorized')
assert c.read_project(copy)['selection'] is None
assert all(c.case_manifest(copy,cid)['stages']=={} for cid in mapping)
c.select(copy,'english-speakers','Illustrative single scope','select-en','Synthetic rehearsal choice')
binding=c.binding(copy,'english-speakers')
c.correct(copy,['chinese-speakers'],'Interpretation-only rehearsal correction','correct-zh')
assert c.binding(copy,'english-speakers')==binding
c.select(copy,'discount-car-insurance','Illustrative single scope','select-motor','Synthetic rehearsal choice')
c.select(copy,'english-speakers','Illustrative single scope','return-en','Synthetic rehearsal choice')
try:c.check_binding(copy,binding);raise AssertionError('old binding accepted')
except ValueError:pass
c.select(copy,'','','clear-selection','Rehearsal ends with no execution choice')
changes=[name for name,value in before.items() if c.digest((copy/name).read_bytes())!=value]
assert set(changes).issubset({'README.md','project-manifest.json','strategy/strategy-plan.json'})
assert all(c.digest((source/name).read_bytes())==value for name,value in before.items())
assert len(before)==sum(p.is_file() for p in source.rglob('*'))
refs=[]
for cid in mapping:
 for b in c.case_manifest(copy,cid)['source_bindings']:
  refs.append({'case':cid,'source':b['path'],'hash_matches_original':c.digest((copy/b['path']).read_bytes())==before[b['path']]})
report={'source':str(source),'rehearsal_copy':str(copy),'original_file_count':len(before),'original_unchanged':True,
 'copy_changed_original_paths':changes,'all_original_research_and_run_hashes_preserved':True,'old_selected_plan_archived_and_marked_review_required':True,
 'rollback_exact_before_images':True,'recovery_idempotent':True,'no_inherited_case_passes':True,
 'unrelated_case_preserves_binding':True,'switch_back_rejects_old_binding':True,
 'final_selection':c.read_project(copy)['selection'],'source_bindings':refs,'link_inventory':links,
 'link_note':'Existing files remain in place. Original root README is byte-preserved in history; its relative links are interpreted from the recorded original project-root location. No archived Markdown rewriting.',
 'limits':['Structural migration rehearsal only; case findings were not reassessed. No live project migration.']}
(parent/'report.json').write_text(c.encoded(report))
print(json.dumps({k:v for k,v in report.items() if k!='link_inventory'},indent=2))
