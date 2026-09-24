import json,os,sys,subprocess
from pathlib import Path
sys.path[:0]=['/mnt/c/coding/general/business-strategist','/mnt/c/coding/general/business-strategist/tests']
from test_case_end_to_end import setup,appraisal
from scripts import case_workspace as c
base=Path('/tmp/fresh-case-adversary/more');base.mkdir(exist_ok=True)
root=setup(base)
def app(d,name):
 p=base/(name+'.json');p.write_text(json.dumps(d))
 return subprocess.run(['python3','scripts/case_workspace.py','appraise','--workspace',str(root),'--case','a','--input',str(p),'--decision-id',name,'--reason','Synthetic appraisal'],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
d=appraisal(root);d['documents']['business-case.md']='# Current business case\n\nContribution is EUR 50 per completed sale; 80 completed sales are required per month.'
r1=app(d,'initial'); d2=appraisal(root);d2['documents']=d['documents'];d2['economics_inputs']['revenue_per_unit']=150;r2=app(d2,'updated')
result={'initial_returncode':r1.returncode,'updated_returncode':r2.returncode,'business_case':(root/'cases/a/business-case.md').read_text(),'calculated':c.load(root/'cases/a/economics.json')['results'],'root_readme':(root/'README.md').read_text()}
(base/'results.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
