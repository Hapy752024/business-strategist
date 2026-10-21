"""Run the local campaign workflow using synthetic data in a new directory."""
from __future__ import annotations
import argparse
from datetime import date, timedelta
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.marketing import campaign as c, review_cycle as r
from scripts import subprojects


def run(out):
    out=Path(out)
    if out.exists():raise ValueError('demo output must be a new directory')
    out.mkdir(parents=True)
    root=out/'demo-project'
    subprojects.start(root,'marketing','Synthetic workshop project','Established workshop business; synthetic operating review only.')
    document={'schema_version':1,'project_id':root.name,'campaign_id':'workshop-signups','objective':'Understand qualified workshop requests',
        'audience':'Local workshop organizers','offer':'Supplied workshop planning call','connection_ids':[],
        'measurement':{'property':'https://example.test/','timezone':'UTC','report_scope':'Synthetic all-pages export with unchanged filters'},'page_url':'https://example.test/workshops'}
    c.setup(root,document)
    fixtures=c.ROOT/'fixtures/marketing/exports'
    current={'period_start':'2026-01-08','period_end':'2026-01-14','exported_at':'2026-01-15'}
    baseline={'period_start':'2026-01-01','period_end':'2026-01-07','exported_at':'2026-01-08'}
    packet,folder=r.prepare(root,document['campaign_id'],'gsc-pages-v1',fixtures/'gsc-current.csv',current,fixtures/'gsc-baseline.csv',baseline,out/'private-runtime')
    review={'schema_version':1,'project_id':root.name,'campaign_id':document['campaign_id'],'packet_id':packet['packet_id'],
        'decision':'collect_more_data','diagnosis':'Search clicks increased in the synthetic export; qualified requests are not supplied.',
        'limitations':['Synthetic data only. No CRM outcomes, customer activity or causal marketing result is established.'],
        'tasks':[{'id':'confirm-outcomes','objective':'Confirm qualified request measurement','actor':'owner',
            'next_step':'Record the number of qualified requests for the same reporting window; retain customer details in the CRM.',
            'completion_criterion':'Owner supplies aggregate qualified requests and the definition used.',
            'reason':'Only the owner can confirm whether a request fits the intended audience.','estimated_minutes':10,'evidence':['coverage']}]}
    result=r.finalize(root,document['campaign_id'],packet['packet_id'],review,out/'private-runtime')
    c.task_event(root,document['campaign_id'],'workshop-signups--confirm-outcomes','accept')
    c.task_event(root,document['campaign_id'],'workshop-signups--confirm-outcomes','snooze',until=(date.today()+timedelta(days=7)).isoformat())
    # Prepare another occurrence without silently accepting/completing its carried task.
    following={'period_start':'2026-01-15','period_end':'2026-01-21','exported_at':'2026-01-22'}
    packet2,_=r.prepare(root,document['campaign_id'],'gsc-pages-v1',fixtures/'gsc-current.csv',following,fixtures/'gsc-current.csv',current,out/'private-runtime')
    review2=review|{'packet_id':packet2['packet_id'],'diagnosis':'Synthetic metrics are unchanged; the outstanding owner task remains snoozed.'}
    result2=r.finalize(root,document['campaign_id'],packet2['packet_id'],review2,out/'private-runtime')
    return {'status':'synthetic_demo_complete','first_report':result['report'],'latest_report':result2['report'],
        'owner_actions':str(c.marketing(root)/'owner-actions.md'),'project':str(root),'external_actions':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);args=p.parse_args()
    try:print(c.encoded(run(args.out)));return 0
    except (ValueError,OSError,KeyError) as exc:print(c.encoded({'status':'error','message':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
