from pathlib import Path
import sys,subprocess,os,json
sys.path.insert(0,'/mnt/c/coding/general/business-strategist')
from scripts import case_workspace as c
root=Path('/tmp/fresh-case-adversary/symlink/topic');c.initialize(root,'Topic');scope=c.add_case(root,'a','A')
outside=root.parent/'outside';outside.mkdir()
(scope/'market_research/market_discovery').symlink_to(outside,target_is_directory=True)
p=subprocess.run(['python3','scripts/evidence_scout/discover_market_problems.py','--topic','Synthetic topic','--workspace',str(root),'--case','a'],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
r={'returncode':p.returncode,'stderr':p.stderr[-1200:],'outside_files':[str(x.relative_to(outside)) for x in outside.rglob('*') if x.is_file()]};print(json.dumps(r,indent=2));(root.parent/'results.json').write_text(json.dumps(r,indent=2))
