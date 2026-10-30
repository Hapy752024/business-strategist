"""Prepare and finalize project-bound local marketing reviews. No network/model invocation."""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import date
import html
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.marketing import campaign as c, import_presets as imports, execution
from scripts import case_workspace as cases, subprojects


def display(value):
    text=html.escape(str(value),quote=True).replace('\n',' ')
    return re.sub(r'([\\`*_{}\[\]()#+!|])',r'\\\1',text)


def runtime(root, campaign_id, runtime_root=None):
    base=Path(runtime_root or c.ROOT/'.marketing-runtime')
    if base.is_symlink(): raise ValueError('runtime root must not be a symlink')
    base.mkdir(parents=True,exist_ok=True,mode=0o700)
    destination=c.safe(base,f'{Path(root).name}/{c.identifier(campaign_id)}')
    destination.mkdir(parents=True,exist_ok=True,mode=0o700)
    return destination


def workstream_inputs(root):
    state=subprojects.validate_marketing_workstream(root)
    return {'brief':state['state']['brief'],'imported_decisions':state['state']['imported_decisions']},state


def bindings(root, campaign_id):
    doc=c.load(root,campaign_id); destination=c.marketing(root)
    inputs,_=workstream_inputs(root)
    return {'campaign':c.digest(doc),'context':c.bytes_digest(c.safe(destination,f'campaigns/{campaign_id}/campaign-context.md').read_bytes()),
        'claims':c.digest(c.read_json(c.safe(destination,f'campaigns/{campaign_id}/approved-claims.json'))),
        'task_context':c.context_digest(root,campaign_id),'connections':c.digest(c.read_json(c.safe(destination,'connections.json'))),'queue':c.digest(c.queue(root)),
        'workstream_inputs':c.digest(inputs)}


def packet_identity(packet):
    return c.digest({k:v for k,v in packet.items() if k not in {'packet_id','prepared_at'}})


def validate_packet(packet):
    if not isinstance(packet,dict) or packet.get('schema_version')!=1: raise ValueError('invalid review packet')
    c.identifier(packet['project_id']);c.identifier(packet['campaign_id'])
    if packet_identity(packet)!=packet.get('packet_id'): raise ValueError('review packet integrity mismatch')
    for snapshot in (packet.get('current'),packet.get('baseline')):
        if snapshot is not None and c.digest({k:v for k,v in snapshot.items() if k!='import_id'})!=snapshot.get('import_id'):
            raise ValueError('normalized snapshot integrity mismatch')


def report(packet, review=None, plan=None, publication=None):
    current=packet['current']; metadata=current['metadata']
    lines=['# Weekly marketing review','',f"Project: {display(packet['project_id'])}; campaign: {display(packet['campaign_id'])}",
        f"Period: {display(metadata['period_start'])} to {display(metadata['period_end'])}; timezone: {display(metadata['timezone'])}",
        f"Source: {display(current['provider'])}; account/property: {display(metadata['property'])}; exported: {display(metadata['exported_at'])}",
        '', 'Status: reviewed' if review else 'Status: data_report_only — agent review pending', '',
        '## Observed metrics','', '| Metric | Current | Baseline | Change |','|---|---:|---:|---:|']
    for metric,cell in current['summary'].items():
        comp=packet['comparison'].get('metrics',{}).get(metric,{})
        fmt=lambda v:'unknown' if v is None else f'{v:.6g}'
        unit=metadata.get('currency','currency') if cell['unit']=='currency' else cell['unit']
        lines.append(f"| {display(metric)} ({display(unit)}) | {fmt(cell['value'])} | {fmt(comp.get('before'))} | {fmt(comp.get('difference'))} |")
    lines+=['', 'Comparison: '+display(packet['comparison']['status'])+'. '+display(packet['comparison'].get('reason','Observed changes do not establish causal uplift.')),
        '', '## Coverage and limits','', '- Only the selected export and its reporting definitions are covered.',
        '- Platform-attributed conversions are not reconciled qualified leads, sales or unique customers.',
        '- Metrics absent from the preset remain unknown; clicks or ambiguous Results do not establish customer outcomes.']
    for metric,cell in current['summary'].items():
        if cell['limitation']: lines.append('- '+display(metric)+': '+display(cell['limitation']))
    for issue in packet['gate_reasons']: lines.append('- Publication pending: '+display(issue))
    if publication:
        if publication['supersedes']:
            label='Restatement of earlier observations' if publication['restatement'] else 'Review revision with unchanged observations'
            lines+=['',label+'; supersedes packet `'+publication['supersedes']+'`.']
        elif publication['backfill']:
            lines+=['','Historical backfill; this does not replace the latest reporting period.']
        if publication['reconciliation_pending']:
            lines+=['','Comparisons awaiting reconciliation: '+', '.join('`'+p+'`' for p in publication['reconciliation_pending'])+'. Re-import revised data and review these periods before relying on their conclusions.']
    if review:
        lines+=['','## Diagnosis and next decision','',display(review['diagnosis']),'','Decision: '+display(review['decision'])]
        lines += ['- '+display(limit) for limit in review['limitations']]
    lines+=['','## Owner actions','']
    lines+=owner_sections(plan or {'actions':[]},
        {packet['campaign_id']:packet['bindings']['task_context']},packet['campaign_id'])
    lines+=['','## Provenance','', 'Packet: `'+packet['packet_id']+'`', 'Current import: `'+current['import_id']+'`',
        '', 'No publication, account change or advertising spend was performed by this report.','']
    return '\n'.join(lines)


def prepare(root,campaign_id,preset,current_path,current_metadata,baseline_path=None,baseline_metadata=None,runtime_root=None):
    doc=c.load(root,campaign_id)
    current=imports.import_export(current_path,preset,dict(doc['measurement'])|current_metadata)
    baseline=imports.import_export(baseline_path,preset,dict(doc['measurement'])|(baseline_metadata or {})) if baseline_path else None
    connection_doc=c.read_json(c.safe(c.marketing(root),'connections.json'))
    selected=[entry for entry in connection_doc['connections'] if entry['id'] in doc['connection_ids']]
    if selected:
        for snapshot in (current,baseline):
            if snapshot is None: continue
            applicable=[entry for entry in selected if entry['provider']==snapshot['provider'] and snapshot['metadata']['property'] in entry['account_ids']]
            if not applicable: raise ValueError('export account/property differs from the selected project connection')
            # Scope belongs to this account, never to a union of unrelated accounts.
            if all(entry.get('campaign_ids') for entry in applicable):
                allowed={v for entry in applicable for v in entry['campaign_ids']}
                if any(row['dimension'] not in allowed for row in snapshot['observations']):
                    raise ValueError('export includes a campaign outside this account connection scope')
    _,state=workstream_inputs(root)
    packet={'schema_version':1,'project_id':Path(root).name,'campaign_id':campaign_id,
        'occurrence_id':current['metadata']['period_end'],'bindings':bindings(root,campaign_id),
        'current':current,'baseline':baseline,'comparison':imports.compare(baseline,current),
        'gate_reasons':state['stale_bindings']}
    packet['packet_id']=packet_identity(packet);packet['prepared_at']=c.now()
    folder=c.safe(runtime(root,campaign_id,runtime_root),packet['packet_id'])
    if folder.exists():
        old=c.read_json(c.safe(folder,'packet.json'));validate_packet(old)
        if old['packet_id']!=packet['packet_id']: raise ValueError('existing packet differs')
        return old,folder
    folder.mkdir(mode=0o700)
    def private(name,text):
        path=c.safe(folder,name)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:stream.write(text)
    private('packet.json',c.encoded(packet));private('report.md',report(packet,plan=c.queue(root)))
    private('review-template.json',c.encoded({'schema_version':1,'project_id':Path(root).name,'campaign_id':campaign_id,
        'packet_id':packet['packet_id'],'decision':'collect_more_data','diagnosis':'REPLACE: agent diagnosis after reading the packet',
        'limitations':['REPLACE: source coverage, maturity and uncertainty'], 'tasks':[]}))
    return packet,folder


def validate_review(packet,review):
    c.require_schema('marketing-review.schema.json',review)
    for key in ('project_id','campaign_id','packet_id'):
        if review[key]!=packet[key]: raise ValueError('review '+key+' binding mismatch')
    if 'REPLACE:' in c.encoded(review): raise ValueError('complete the review template before finalizing')
    if packet['comparison']['status']!='descriptive' and review['decision']!='collect_more_data':
        raise ValueError('non-comparable or first-report data requires collect_more_data')
    ids=[task['id'] for task in review['tasks']]
    if len(ids)!=len(set(ids)): raise ValueError('task IDs must be unique')
    evidence={'metric:'+key for key in packet['current']['summary']}|{'comparison:'+key for key in packet['comparison'].get('metrics',{})}|{'coverage'}
    for task in review['tasks']:
        if set(task['evidence'])-evidence: raise ValueError('task evidence must reference metric:<name>, comparison:<name> or coverage')


def finalized_plan(root,packet,review):
    plan=deepcopy(c.queue(root));plan['schema_version']=3;plan['revision']+=1
    for action in plan['actions']:
        action.setdefault('action_kind','generic');action.setdefault('intended_result',action['objective'])
    existing={a['id']:a for a in plan['actions']}
    for task in review['tasks']:
        ident=packet['campaign_id']+'--'+task['id']
        if ident in existing:
            old=existing[ident]
            if old.get('context_sha256')!=packet['bindings']['task_context']:
                raise ValueError('existing task context changed; decline the stale task with a reason and propose a new task ID for renewed owner acceptance')
            if old['commitment_state'] in {'completed','declined'}:
                raise ValueError('completed/declined task cannot be re-proposed; omit it or propose a materially new task ID')
            fields={'objective':'objective','actor':'actor','next_step':'next_step','completion_criterion':'completion_criterion','owner_reason':'reason','estimated_minutes':'estimated_minutes','evidence':'evidence'}
            if any(old.get(field)!=task.get(source) for field,source in fields.items()):
                raise ValueError('existing task proposal changed; use a new task ID for reviewed follow-up work')
            continue
        action={'id':ident,'campaign_id':packet['campaign_id'],'occurrence_id':packet['occurrence_id'],
            'context_sha256':packet['bindings']['task_context'],'objective':task['objective'],'actor':task['actor'],
            'dependencies':[],'prepared_materials':[],'next_step':task['next_step'],'completion_criterion':task['completion_criterion'],
            'commitment_state':'proposed','execution_status':'prepared','required_for_scope':False,
            'action_kind':'generic','intended_result':task['completion_criterion'],'evidence':task['evidence'],
            'owner_reason':task['reason'],'estimated_minutes':task['estimated_minutes']}
        plan['actions'].append(action)
    return plan


def website_brief(doc):
    return '\n'.join(['# Campaign website handoff','', 'Status: brief for review; no deployment or tracking activation.',
        '', 'Audience: '+display(doc['audience']), 'Offer: '+display(doc['offer']), 'Objective: '+display(doc['objective']),
        'Destination: '+display(doc.get('page_url') or 'owner/page selection pending'), '',
        '- Match page intent, evidence, offer and CTA; preserve useful interactive tools.',
        '- Define the full form-to-destination path and confirmed customer outcome.',
        '- Carry the sourced journey hook, useful tool/asset, distribution route and sales follow-up owner from campaign context.',
        '- Apply references/journey-activation-and-measurement.md; keep native forms, messaging and website conversions distinct.',
        '- Confirm event definitions, consent, deduplication and test exclusions before activation.',
        '- For Meta copies of one action: same destination/name and Pixel eventID = CAPI event_id; keep IDs stable on retry.',
        '- Map Google bidding/observation goals and TikTok Pixel/Events API separately; later CRM milestones get new occurrence IDs.',
        '- Technical SEO, speed, accessibility and release checks remain with the website builder.',
        '- Claims need approved sources; measurement installation does not verify lead receipt.', ''])


def snapshot_key(snapshot):
    """Stable occurrence identity; corrected filters/units remain revisions."""
    meta=snapshot['metadata']
    return (snapshot['provider'],meta['property'],meta['period_start'],meta['period_end'])


def validate_history(document,destination,staged=None):
    from scripts.marketing.link_observations import resolve_bytes
    if document.get('schema_version')!=1 or not isinstance(document.get('packets'),list):
        raise ValueError('invalid campaign review history')
    if len(document['packets'])!=len(set(document['packets'])):
        raise ValueError('duplicate campaign review history entries')
    packets=[]
    for relative in document['packets']:
        c.safe(destination,relative)
        parts=Path(relative).parts
        if (Path(relative).as_posix()!=relative or len(parts)!=6 or
            parts[:3]!=('campaigns',document['campaign_id'],'reviews') or parts[-1]!='packet.json'):
            raise ValueError('invalid campaign history packet location')
        packet=json.loads(resolve_bytes(destination,relative,staged))
        validate_packet(packet)
        if (packet['project_id']!=document['project_id'] or packet['campaign_id']!=document['campaign_id'] or
            parts[3]!=packet['occurrence_id'] or parts[4]!=packet['packet_id']):
            raise ValueError('campaign history packet binding mismatch')
        # Every history entry must have its reviewed publication alongside it.
        review=json.loads(resolve_bytes(destination,str(Path(relative).with_name('review.json')),staged))
        validate_review(packet,review)
        packets.append(packet)
    return packets


def publication_history(root,packet,state):
    destination=c.marketing(root);campaign_id=packet['campaign_id']
    history_path=c.safe(destination,f'campaigns/{campaign_id}/review-history.json')
    last_path=c.safe(destination,f'campaigns/{campaign_id}/latest-review.json')
    last=c.read_json(last_path) if last_path.is_file() else None
    if history_path.is_file():
        history=c.read_json(history_path)
        packets=validate_history(history,destination)
    else:
        # Upgrade earlier local releases without modifying immutable evidence.
        paths=[entry['path'] for entry in state['state']['artifact_refs']
               if entry['path'].startswith(f'campaigns/{campaign_id}/reviews/') and entry['path'].endswith('/packet.json')]
        paths.sort(key=lambda path:(c.read_json(c.safe(destination,path))['prepared_at'],path))
        if last:
            last_packet=str(Path(last['path']).with_name('packet.json'))
            if last_packet in paths: paths.remove(last_packet);paths.append(last_packet)
        history={'schema_version':1,'project_id':Path(root).name,'campaign_id':campaign_id,'packets':paths}
        packets=validate_history(history,destination)
    key=snapshot_key(packet['current'])
    previous=next((p for p in reversed(packets) if snapshot_key(p['current'])==key),None)
    period=[packet['current']['metadata']['period_start'],packet['current']['metadata']['period_end']]
    publication={'supersedes':previous['packet_id'] if previous else None,
        'restatement':bool(previous and previous['current']['import_id']!=packet['current']['import_id']),
        'backfill':bool(last and tuple(reversed(period))<tuple(reversed(last['period'])))}
    heads={snapshot_key(p['current']):p for p in packets+[packet]}
    pending=[]
    for head in heads.values():
        baseline=head.get('baseline')
        replacement=heads.get(snapshot_key(baseline)) if baseline else None
        if replacement and replacement['current']['import_id']!=baseline['import_id']:
            pending.append(head['packet_id'])
    publication['reconciliation_pending']=sorted(pending)
    relative=f'campaigns/{campaign_id}/reviews/{packet["occurrence_id"]}/{packet["packet_id"]}'
    history['packets'].append(relative+'/packet.json')
    # Select by reporting window, even if a pre-fix latest pointer had moved backwards.
    all_packets=packets+[packet]
    newest=max(heads.values(),key=lambda p:(p['current']['metadata']['period_end'],
        p['current']['metadata']['period_start'],all_packets.index(p)))
    newest_key=snapshot_key(newest['current'])
    newest_previous=next((p for p in reversed(all_packets[:all_packets.index(newest)])
        if snapshot_key(p['current'])==newest_key),None)
    latest={
        'schema_version':1,'project_id':Path(root).name,'campaign_id':campaign_id,
        'packet_id':newest['packet_id'],
        'path':f'campaigns/{campaign_id}/reviews/{newest["occurrence_id"]}/{newest["packet_id"]}/review.json',
        'period':[newest['current']['metadata']['period_start'],newest['current']['metadata']['period_end']],
        'supersedes':newest_previous['packet_id'] if newest_previous else None,
        'restatement':bool(newest_previous and newest_previous['current']['import_id']!=newest['current']['import_id'])}
    publication['backfill']=tuple(reversed(period))<tuple(reversed(latest['period']))
    latest.update(last_processed_packet_id=packet['packet_id'],reconciliation_pending=sorted(pending))
    return history,latest,publication


def finalize(root,campaign_id,packet_id,review,runtime_root=None):
    if not re.fullmatch('[a-f0-9]{64}',packet_id): raise ValueError('invalid packet ID')
    folder=c.safe(runtime(root,campaign_id,runtime_root),packet_id)
    packet=c.read_json(c.safe(folder,'packet.json'));validate_packet(packet)
    if packet['project_id']!=Path(root).name or packet['campaign_id']!=campaign_id or packet['packet_id']!=packet_id:
        raise ValueError('packet belongs to another project/campaign')
    validate_review(packet,review)
    destination=c.marketing(root)
    relative=f'campaigns/{campaign_id}/reviews/{packet["occurrence_id"]}/{packet_id}'
    published=c.safe(destination,relative+'/review.json')
    if published.exists():
        if c.read_json(published)!=review: raise ValueError('review occurrence is immutable; prepare a new packet for a revision')
        state=c.read_json(c.safe(destination,'workstream.json'))
        refs={entry['path']:entry['sha256'] for entry in state['artifact_refs']}
        for name in ('packet.json','review.json','report.md'):
            path=c.safe(destination,relative+'/'+name)
            if not path.is_file() or c.bytes_digest(path.read_bytes())!=refs.get(relative+'/'+name):
                raise ValueError('published review evidence is missing/changed; restore its original bytes before reuse')
        return {'status':'already_published','report':str(c.safe(destination,relative+'/report.md'))}
    revision=cases.read_project(root)['manifest_revision']
    if bindings(root,campaign_id)!=packet['bindings']: raise ValueError('campaign/context/tasks changed; prepare a fresh packet')
    if c.digest(imports.preset(packet['current']['preset']))!=packet['current']['preset_sha256']:
        raise ValueError('export preset changed; prepare a fresh packet')
    _,state=workstream_inputs(root)
    if not state['valid_for_use']: raise ValueError('Marketing inputs need review: '+ '; '.join(state['stale_bindings']))
    plan=finalized_plan(root,packet,review)
    errors=execution.validate(plan,destination)
    if errors: raise ValueError('invalid task plan: '+'; '.join(errors))
    plan_text,_=execution.render(plan)
    doc=c.load(root,campaign_id)
    history,latest,publication=publication_history(root,packet,state)
    files={relative+'/packet.json':c.encoded(packet),relative+'/review.json':c.encoded(review),
        relative+'/report.md':report(packet,review,plan,publication),'execution-plan.json':c.encoded(plan),'execution-plan.md':plan_text,
        'owner-actions.md':owner_actions(plan,root),f'campaigns/{campaign_id}/latest-review.json':c.encoded(latest),
        f'campaigns/{campaign_id}/review-history.json':c.encoded(history),
        f'campaigns/{campaign_id}/website-brief.md':website_brief(doc)}
    c.publish(root,files,'Publish reviewed local campaign report and proposed tasks',expected_revision=revision)
    return {'status':'published','report':str(c.safe(destination,relative+'/report.md')),'external_actions':False}


def owner_sections(plan,contexts=None,campaign_id=None):
    """One selection/rendering contract for weekly and shared owner views."""
    contexts=contexts or {}
    by_id={a['id']:a for a in plan['actions']}
    grouped={}
    for action in plan['actions']:
        if action['actor']!='owner' or action['commitment_state'] in {'declined','completed'}:
            continue
        group=action.get('campaign_id','other')
        if campaign_id is not None and group!=campaign_id: continue
        grouped.setdefault(group,[]).append(action)
    lines=[]
    for group,actions in grouped.items():
        lines+=['### '+display(group),'']
        due=[];snoozed=[];stale=[];blocked=[];waiting=[]
        for action in actions:
            blockers=[ident for ident in action.get('dependencies',[]) if
                by_id.get(ident,{}).get('commitment_state')!='completed' or
                by_id.get(ident,{}).get('execution_status') not in {'submitted','verified'}]
            if group in contexts and action.get('context_sha256')!=contexts[group]:
                stale.append(action)
            elif blockers:
                blocked.append((action,blockers))
            elif action.get('deferred_until') and action['deferred_until']>date.today().isoformat():
                snoozed.append(action)
            elif action['execution_status'] not in {'prepared','awaiting_owner'}:
                waiting.append(action)
            else:
                due.append(action)
        def detail(action,annotation=''):
            result=[f"- {display(action['id'])}: {display(action['objective'])} — {display(action['commitment_state'])}{annotation}; next step: {display(action.get('user_step') or action['next_step'])}; completion: {display(action['completion_criterion'])}."]
            for field,label in [('destination','Destination'),('owner_reason','Why owner'),('estimated_minutes','Estimated minutes'),
                                ('authorization_basis','Authorization'),('fee','Fee'),('follow_up','Follow-up')]:
                if action.get(field) is not None:
                    result.append(f"  - {label}: {display(action[field])}")
            for material in action.get('prepared_materials',[]):
                result.append(f"  - Prepared material: {display(material['path'])} (SHA-256: {display(material['sha256'])})")
            return result
        for action in due[:3]:lines+=detail(action)
        if not due:lines.append('No due owner tasks.')
        if len(due)>3:lines.append(f'{len(due)-3} additional due tasks remain in execution-plan.json.')
        for action,blockers in blocked:
            lines+=detail(action,'; blocked by '+', '.join(display(v) for v in blockers))
        for action in snoozed:
            lines.append(f"- Snoozed: {display(action['id'])} until {display(action['deferred_until'])}.")
        for action in stale:
            lines.append(f"- Needs context review: {display(action['id'])}. Decline the stale task with a reason, then propose a new task ID for renewed owner acceptance.")
        for action in waiting:
            lines.append(f"- Needs outcome review: {display(action['id'])}; progress: {display(action['execution_status'])}. Check the execution plan before repeating any operation.")
    return lines or ['No due owner tasks.']


def owner_actions(plan,root=None):
    contexts={}
    if root is not None:
        for campaign_id in {a['campaign_id'] for a in plan['actions'] if a.get('campaign_id')}:
            contexts[campaign_id]=c.context_digest(root,campaign_id)
    return '\n'.join(['# Owner actions','', 'Task decisions do not authorize publishing or spending.','']+
                     owner_sections(plan,contexts))+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--project',required=True);a.add_argument('--campaign',required=True)
    a.add_argument('--preset',required=True);a.add_argument('--current',type=Path,required=True);a.add_argument('--baseline',type=Path)
    for key in ('period-start','period-end','exported-at','baseline-start','baseline-end','baseline-exported-at','property','timezone','currency','attribution','maturity','report-scope'):
        a.add_argument('--'+key)
    b=sub.add_parser('finalize')
    for key in ('project','campaign','packet'):b.add_argument('--'+key,required=True)
    b.add_argument('--review-json',type=Path,required=True)
    args=p.parse_args()
    try:
        root=c.resolve_project(args.project)
        if args.command=='prepare':
            metadata={key:getattr(args,key) for key in ('period_start','period_end','exported_at','property','timezone','currency','attribution','maturity','report_scope') if getattr(args,key)}
            baseline_metadata={key:metadata[key] for key in ('property','timezone','currency','attribution','maturity','report_scope') if key in metadata}
            baseline_metadata.update({key:getattr(args,'baseline_'+alias) for key,alias in [('period_start','start'),('period_end','end'),('exported_at','exported_at')] if getattr(args,'baseline_'+alias)})
            packet,folder=prepare(root,args.campaign,args.preset,args.current,metadata,args.baseline,baseline_metadata)
            result={'status':'data_report_only','packet_id':packet['packet_id'],'private_packet':str(folder),'gate_reasons':packet['gate_reasons']}
        else:result=finalize(root,args.campaign,args.packet,c.read_json(args.review_json))
        print(c.encoded(result));return 0
    except (ValueError,OSError,KeyError) as exc:
        print(c.encoded({'status':'error','message':str(exc)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
