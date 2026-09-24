import json, os, subprocess, sys
from pathlib import Path
sys.path[:0]=['/mnt/c/coding/general/business-strategist','/mnt/c/coding/general/business-strategist/tests']
from scripts import case_workspace as c, route_workflow as r
from scripts.evidence_scout import workspace as w
from test_case_end_to_end import setup, selected_plan, appraisal
from scripts.evidence_scout.test_landscape_artifacts import LandscapeArtifactTests
from test_case_economics import inputs
base=Path('/tmp/fresh-case-adversary'); base.mkdir(exist_ok=True)
repo=Path('/mnt/c/coding/general/business-strategist')
def cli(*args):
 p=subprocess.run(args,cwd=repo,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
 return {'returncode':p.returncode,'stdout':p.stdout[-600:],'stderr':p.stderr[-600:]}
results={}
root=setup(base/'publication'); data=selected_plan(root)
# Existing supported consumer can write outside its purpose, including a different case.
target=root/'cases/b/new-baseline.md'
results['freeze_cross_case']=cli('python3','scripts/strategy_review.py','freeze','--plan',str(root/'strategy/strategy-plan.json'),'--output',str(target))
results['freeze_cross_case']['exists']=target.exists()
results['freeze_cross_case']['project_revision']=c.read_project(root)['manifest_revision']
# Declared direct CLI input is not bound into the case checkpoint.
root2=setup(base/'dependency'); source=root2/'market_research/shared-entities.json'; source.parent.mkdir(exist_ok=True)
source.write_text(json.dumps(LandscapeArtifactTests().landscape([{'name':'DirectCo','url':'https://direct.example','primary_lane':'competitive_market','competitive_role':'direct','verification_status':'verified','social_presence':[{'status':'not_found_in_checked_sources'}]}])))
out=root2/'cases/a/market_research/solution_alternatives/runs/derived'
results['shared_builder']=cli('python3','scripts/evidence_scout/build_landscape_artifacts.py','--entities-json',str(source),'--workspace',str(root2),'--case','a','--out-dir',str(out))
cm=c.case_manifest(root2,'a'); results['shared_builder']['stage_before']=cm['stages']['competitive_landscape']['status']; results['shared_builder']['bindings']=[b['path'] for b in cm['stages']['competitive_landscape']['source_bindings']]
c.correct(root2,[],'Official source interpretation withdrawn','source-withdrawn',source_path='market_research/shared-entities.json')
cm2=c.case_manifest(root2,'a'); results['shared_builder']['revision_before_after']=[cm['assessment_revision'],cm2['assessment_revision']]; results['shared_builder']['stage_after']=cm2['stages']['competitive_landscape']['status']
# Input workspace overrides detection of versioned output root, skipping protection.
legacy=w.create_project_workspace('Legacy',str(base/'legacy'),layout_version=1)
old=out/'competitive-market-matrix.md'; old.write_text('PRESERVE ORIGINAL RUN')
results['builder_conflicting_workspace']=cli('python3','scripts/evidence_scout/build_landscape_artifacts.py','--entities-json',str(source),'--workspace',str(legacy),'--out-dir',str(out))
results['builder_conflicting_workspace']['original_run_preserved']=old.read_text()=='PRESERVE ORIGINAL RUN'
# Pending project does not block normal brand and website commands.
root3=setup(base/'downstream')
def stop(where):
 if where=='pending': raise RuntimeError('stop')
try:c.publish(root3,{'cases/a/README.md':'new'},expected_revision=c.read_project(root3)['manifest_revision'],decision_id='pending-check',reason='repro',fault=stop)
except RuntimeError:pass
results['brand_pending']=cli('python3','.agents/skills/brand-workspace-manager/scripts/workspace_cli.py','create','--name','branding','--base-dir',str(root3))
results['brand_pending']['brand_manifest_exists']=(root3/'branding/brand-manifest.json').exists()
results['website_pending']=cli('node','.agents/skills/brand-website-designer-builder/scripts/scaffold-site.mjs',str(root3/'web-site'))
results['website_pending']['scaffold_exists']=(root3/'web-site/scaffold-command.txt').exists()
# Consumer route only checks pain + case bindings, not the selected plan.
r.ROOT=base/'routing'; root4=setup(r.ROOT/'projects'); # setup produces projects/topic
selected_plan(root4)
plan_path=root4/'strategy/strategy-plan.json'; pd=c.load(plan_path); pd['business_plan_sections']['finances']['text']='UNREVIEWED DRAFT'; pd['review_required']='Known plan-only correction'; plan_path.write_text(c.encoded(pd))
results['route_review_required_plan']=r.route_request('Build website',intent='website-build',project='topic',case_id='a',task_scope='execution',check_skill='brand-website-designer-builder')
# Apparent positive own margin but owner labor extra inputs ignored.
d=inputs(); d['imputed_founder_labor_per_month']=10000; d['owner_labor_in_service_cost']=True
from scripts.case_economics import calculate
results['ignored_economics_inputs']=calculate(d)['results']
(base/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
