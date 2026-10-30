"""Integration regressions for local reporting and its project/publication boundaries."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import pytest
from scripts import case_workspace as cases, subprojects
from scripts.marketing import campaign as c, connections, import_presets as imp, review_cycle as r, execution, claims

FIX=c.ROOT/'fixtures/marketing/exports'
CURRENT={'period_start':'2026-01-08','period_end':'2026-01-14','exported_at':'2026-01-15','report_scope':'Synthetic unchanged report filters'}
BASELINE={'period_start':'2026-01-01','period_end':'2026-01-07','exported_at':'2026-01-08','report_scope':'Synthetic unchanged report filters'}


def project(tmp_path,name='alpha-project',campaign='workshops'):
    root=tmp_path/name
    subprojects.start(root,'marketing',name,'Established workshop service; supplied standalone brief.')
    doc={'schema_version':1,'project_id':name,'campaign_id':campaign,'objective':'Understand qualified requests',
         'audience':'Workshop organizers','offer':'Confirmed planning call','connection_ids':[],
         'measurement':{'property':'site-example','timezone':'UTC'}}
    c.setup(root,doc)
    return root


def prepared(root,tmp_path,**kwargs):
    return r.prepare(root,'workshops','gsc-pages-v1',FIX/'gsc-current.csv',CURRENT,
        FIX/'gsc-baseline.csv',BASELINE,runtime_root=tmp_path/'runtime',**kwargs)


def review(packet,task_id='check-quality'):
    return {'schema_version':1,'project_id':packet['project_id'],'campaign_id':packet['campaign_id'],
        'packet_id':packet['packet_id'],'decision':'collect_more_data','diagnosis':'Clicks increased; qualified demand remains unknown.',
        'limitations':['Aggregate export only; no confirmed customer outcome or causal inference.'],
        'tasks':[{'id':task_id,'objective':'Confirm qualified outcomes','actor':'owner','next_step':'Supply aggregate qualified requests for the reporting window.',
            'completion_criterion':'Owner confirms count and qualification definition.','reason':'Private qualification is known only by the owner.',
            'estimated_minutes':5,'evidence':['coverage']}]}


def test_end_to_end_local_report_is_bound_idempotent_and_noncausal(tmp_path):
    root=project(tmp_path);packet,folder=prepared(root,tmp_path)
    assert (folder/'report.md').read_text().find('data_report_only')>=0
    assert packet['current']['summary']['clicks']['value']==25
    assert packet['comparison']['metrics']['clicks']['difference']==10
    output=r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    report=Path(output['report']).read_text()
    assert 'qualified demand remains unknown' in report and 'causal uplift' in report
    revision=cases.read_project(root)['manifest_revision']
    assert r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')['status']=='already_published'
    assert cases.read_project(root)['manifest_revision']==revision
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    assert (c.marketing(root)/'campaigns/workshops/website-brief.md').is_file()
    assert c.queue(root)['actions'][0]['commitment_state']=='proposed'
    assert all('?' not in row['dimension'] for row in packet['current']['observations'])
    assert (folder/'packet.json').stat().st_mode & 0o077 == 0


@pytest.mark.parametrize('preset,filename,expected',[
    ('gsc-pages-v1','gsc-current.csv',('clicks',25)),
    ('ga4-pages-v1','ga4-pages.csv',('views',150)),
    ('google-ads-campaigns-v1','google-ads-campaigns.csv',('spend',42.5)),
    ('meta-ads-campaigns-v1','meta-ads-campaigns.csv',('spend',30)),
    ('tiktok-ads-campaigns-v1','tiktok-ads-campaigns.csv',('spend',40)),
])
def test_each_shipped_wide_export_preset(preset,filename,expected):
    doc=imp.import_export(FIX/filename,preset,CURRENT|{'property':'example','timezone':'UTC','currency':'USD','attribution':'confirmed-platform-setting','maturity':'pending'})
    metric,value=expected
    assert doc['summary'][metric]['value']==value
    assert doc['input_sha256'] and doc['import_id']
    if preset=='ga4-pages-v1':assert doc['summary']['active_users']['value'] is None
    if preset=='meta-ads-campaigns-v1':assert doc['summary']['website_leads']['value'] is None
    if preset=='gsc-pages-v1':
        assert doc['summary']['ctr']['value']==pytest.approx(25/200)
        assert doc['summary']['position']['value']==7


@pytest.mark.parametrize('value',['NaN','inf','-1','1,23','€10','1e309'])
def test_unsupported_numeric_data_cannot_be_silently_coerced(tmp_path,value):
    file=tmp_path/'bad.csv';file.write_text('Top pages,Clicks,Impressions,CTR,Position\n/a,"'+value+'",10,0%,1\n')
    with pytest.raises(ValueError):imp.import_export(file,'gsc-pages-v1',CURRENT|{'property':'site','timezone':'UTC'})


def test_missing_suppressed_and_zero_and_duplicate_dimensions(tmp_path):
    file=tmp_path/'a.csv';file.write_text('Top pages,Clicks,Impressions,CTR,Position\n/a,0,10,0%,1\n/b,,10,0%,1\n/c,--,10,0%,1\n')
    out=imp.import_export(file,'gsc-pages-v1',CURRENT|{'property':'site','timezone':'UTC'})
    clicks=[row for row in out['observations'] if row['metric']=='clicks']
    assert [(r['value'],r['availability']) for r in clicks]==[(0,'available'),(None,'unknown'),(None,'unavailable')]
    assert out['summary']['clicks']['value'] is None
    file.write_text(file.read_text()+'/a,1,10,10%,1\n')
    with pytest.raises(ValueError,match='duplicate dimensions'):imp.import_export(file,'gsc-pages-v1',CURRENT|{'property':'site','timezone':'UTC'})


def test_import_identity_includes_confirmed_metadata_and_preset(tmp_path,monkeypatch):
    metadata=CURRENT|{'property':'site','timezone':'UTC'}
    a=imp.import_export(FIX/'gsc-current.csv','gsc-pages-v1',metadata)
    b=imp.import_export(FIX/'gsc-current.csv','gsc-pages-v1',metadata|{'timezone':'Europe/Zurich'})
    assert a['input_sha256']==b['input_sha256'] and a['import_id']!=b['import_id']
    original=imp.preset
    monkeypatch.setattr(imp,'preset',lambda name:original(name)|{'transform_version':2})
    new=imp.import_export(FIX/'gsc-current.csv','gsc-pages-v1',metadata)
    assert new['import_id']!=a['import_id']


def test_tiktok_destination_clicks_are_not_all_clicks_or_customer_results(tmp_path):
    metadata=CURRENT|{'property':'advertiser-a','timezone':'UTC','currency':'USD',
        'attribution':'confirmed setting','maturity':'pending'}
    output=imp.import_export(FIX/'tiktok-ads-campaigns.csv','tiktok-ads-campaigns-v1',metadata)
    assert output['summary']['destination_clicks']['value']==25
    assert output['summary']['destination_ctr']['value']==pytest.approx(25/1500)
    assert not {'clicks','results','conversions','leads','sales'} & output['summary'].keys()
    file=tmp_path/'ambiguous.csv'
    file.write_text((FIX/'tiktok-ads-campaigns.csv').read_text().replace('Clicks (destination)','Clicks (all)'))
    with pytest.raises(ValueError,match='requires columns'):
        imp.import_export(file,'tiktok-ads-campaigns-v1',metadata)
    file.write_text('Campaign name,Campaign ID,Cost,Impressions,Clicks (destination)\nDemo,701,10,100,--\n')
    output=imp.import_export(file,'tiktok-ads-campaigns-v1',metadata)
    assert output['summary']['destination_clicks']['value'] is None
    assert output['summary']['destination_ctr']['value'] is None


@pytest.mark.parametrize('missing',['currency','attribution','maturity'])
def test_tiktok_requires_advertising_measurement_context(missing):
    metadata=CURRENT|{'property':'advertiser-a','timezone':'UTC','currency':'USD',
        'attribution':'confirmed setting','maturity':'pending'}
    del metadata[missing]
    with pytest.raises(ValueError,match='confirm export metadata: '+missing):
        imp.import_export(FIX/'tiktok-ads-campaigns.csv','tiktok-ads-campaigns-v1',metadata)


def test_tiktok_reporting_preserves_account_campaign_and_context_boundaries(tmp_path):
    root=tmp_path/'alpha-project'
    subprojects.start(root,'marketing','Alpha','Established repair workshop; standalone brief')
    config={'schema_version':1,'project_id':root.name,'connections':[
        {'id':'video','provider':'tiktok_ads','account_ids':['advertiser-a'],
         'campaign_ids':['701','702'],'credential_ref':'alpha-project/video',
         'capability':'reporting','status':'unconfigured','transport':'export'}]}
    assert not connections.validate(config,root.name)
    wrong=deepcopy(config);wrong['connections'][0]['credential_ref']='another-project/video'
    assert connections.validate(wrong,root.name)
    wrong=deepcopy(config);wrong['connections'][0]['status']='connected'
    assert connections.validate(wrong,root.name)
    c.setup(root,{'schema_version':1,'project_id':root.name,'campaign_id':'workshops',
        'objective':'Qualified repairs','audience':'Equipment owners','offer':'Repair booking',
        'connection_ids':['video'],'measurement':{'property':'advertiser-a','timezone':'UTC',
        'currency':'USD','attribution':'confirmed setting','maturity':'pending'}},config)
    packet,_=r.prepare(root,'workshops','tiktok-ads-campaigns-v1',FIX/'tiktok-ads-campaigns.csv',
        CURRENT,runtime_root=tmp_path/'runtime')
    response=review(packet);response['diagnosis']='Destination traffic observed; qualified repairs remain unknown.'
    output=r.finalize(root,'workshops',packet['packet_id'],response,tmp_path/'runtime')
    assert packet['current']['provider']=='tiktok_ads'
    assert packet['current']['summary']['spend']['value']==40
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    assert 'qualified repairs remain unknown' in Path(output['report']).read_text()
    with pytest.raises(ValueError,match='selected project connection'):
        r.prepare(root,'workshops','tiktok-ads-campaigns-v1',FIX/'tiktok-ads-campaigns.csv',
            CURRENT|{'property':'advertiser-b'},runtime_root=tmp_path/'runtime')
    wrong_csv=tmp_path/'wrong-campaign.csv'
    wrong_csv.write_text((FIX/'tiktok-ads-campaigns.csv').read_text().replace(',701,',',999,'))
    with pytest.raises(ValueError,match='this account connection scope'):
        r.prepare(root,'workshops','tiktok-ads-campaigns-v1',wrong_csv,CURRENT,runtime_root=tmp_path/'runtime')
    pending,_=r.prepare(root,'workshops','tiktok-ads-campaigns-v1',FIX/'tiktok-ads-campaigns.csv',
        CURRENT,runtime_root=tmp_path/'runtime')
    context_path=c.marketing(root)/'campaigns/workshops/campaign-context.md'
    c.publish(root,{'campaigns/workshops/campaign-context.md':context_path.read_text()+
        '\nOptimization event changed from enquiry to qualified repair.\n'},'Reviewed event contract update')
    with pytest.raises(ValueError,match='changed|stale'):
        r.finalize(root,'workshops',pending['packet_id'],review(pending),tmp_path/'runtime')
    assert r.finalize(root,'workshops',packet['packet_id'],response,tmp_path/'runtime')['status']=='already_published'


def test_first_noncomparable_and_overlapping_periods_do_not_claim_winners(tmp_path):
    root=project(tmp_path)
    packet,_=r.prepare(root,'workshops','gsc-pages-v1',FIX/'gsc-current.csv',CURRENT,runtime_root=tmp_path/'runtime')
    assert packet['comparison']['status']=='no_baseline'
    with pytest.raises(ValueError,match='collect_more_data'):r.validate_review(packet,review(packet)|{'decision':'change'})
    before=imp.import_export(FIX/'gsc-baseline.csv','gsc-pages-v1',BASELINE|{'property':'a','timezone':'UTC'})
    after=imp.import_export(FIX/'gsc-current.csv','gsc-pages-v1',CURRENT|{'property':'b','timezone':'UTC'})
    assert imp.compare(before,after)['status']=='non_comparable'
    assert imp.compare(after,after)['status']=='non_comparable'


def test_task_decline_snooze_and_completion_survive_reviews(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    ident='workshops--check-quality';future=(date.today()+timedelta(days=7)).isoformat()
    with pytest.raises(ValueError,match='accepted task'):c.task_event(root,'workshops',ident,'complete',evidence='done')
    c.task_event(root,'workshops',ident,'accept');c.task_event(root,'workshops',ident,'snooze',until=future)
    packet2,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet2['packet_id'],review(packet2),tmp_path/'runtime')
    assert len(c.queue(root)['actions'])==1
    assert c.queue(root)['actions'][0]['deferred_until']==future
    c.task_event(root,'workshops',ident,'decline',reason='No longer the current priority')
    packet3,_=prepared(root,tmp_path)
    with pytest.raises(ValueError,match='cannot be re-proposed'):
        r.finalize(root,'workshops',packet3['packet_id'],review(packet3),tmp_path/'runtime')
    r.finalize(root,'workshops',packet3['packet_id'],review(packet3)|{'tasks':[]},tmp_path/'runtime')
    assert c.queue(root)['actions'][0]['commitment_state']=='declined'
    assert ident not in (c.marketing(root)/'owner-actions.md').read_text()
    c.task_event(root,'workshops',ident,'accept');c.task_event(root,'workshops',ident,'complete',evidence='Owner confirmed three qualified requests')
    assert c.queue(root)['actions'][0]['verification'].startswith('Owner attestation:')


def test_stale_review_does_not_replace_last_good_report(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    latest=(c.marketing(root)/'campaigns/workshops/latest-review.json').read_bytes()
    second,_=prepared(root,tmp_path)
    c.task_event(root,'workshops','workshops--check-quality','decline',reason='Defer this approach')
    with pytest.raises(ValueError,match='changed'):r.finalize(root,'workshops',second['packet_id'],review(second),tmp_path/'runtime')
    assert (c.marketing(root)/'campaigns/workshops/latest-review.json').read_bytes()==latest


def test_stale_workstream_allows_only_private_preview(tmp_path):
    root=project(tmp_path);(c.marketing(root)/'brief.md').write_text('Changed unreviewed brief')
    packet,folder=prepared(root,tmp_path)
    assert packet['gate_reasons'] and folder.is_dir()
    with pytest.raises(ValueError,match='Marketing inputs need review'):r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    assert not (c.marketing(root)/'campaigns/workshops/latest-review.json').exists()


def test_publication_race_and_two_campaigns_do_not_overwrite_tasks(tmp_path,monkeypatch):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    original=c.publish
    def race(root,files,reason,**kwargs):
        original(root,{'unrelated.md':'Another writer\n'},'Concurrent publication')
        return original(root,files,reason,**kwargs)
    monkeypatch.setattr(c,'publish',race)
    with pytest.raises(ValueError,match='revision conflict'):r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    assert not (c.marketing(root)/'campaigns/workshops/latest-review.json').exists()
    monkeypatch.setattr(c,'publish',original)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    doc=c.load(root,'workshops')|{'campaign_id':'webinars'};c.setup(root,doc)
    second,_=r.prepare(root,'webinars','gsc-pages-v1',FIX/'gsc-current.csv',CURRENT,runtime_root=tmp_path/'runtime')
    r.finalize(root,'webinars',second['packet_id'],review(second),tmp_path/'runtime')
    assert {a['campaign_id'] for a in c.queue(root)['actions']}=={'workshops','webinars'}


def test_restatement_keeps_original_immutable(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    output=r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    original=Path(output['report']).read_bytes()
    source=tmp_path/'corrected.csv';source.write_text((FIX/'gsc-current.csv').read_text().replace(',20,150,',',22,150,'))
    corrected,_=r.prepare(root,'workshops','gsc-pages-v1',source,CURRENT,runtime_root=tmp_path/'runtime')
    r.finalize(root,'workshops',corrected['packet_id'],review(corrected),tmp_path/'runtime')
    pointer=c.read_json(c.marketing(root)/'campaigns/workshops/latest-review.json')
    assert pointer['restatement'] and pointer['supersedes']==packet['packet_id']
    assert Path(output['report']).read_bytes()==original


def test_project_token_reference_account_and_path_mixups_are_rejected(tmp_path):
    config={'schema_version':1,'project_id':'alpha-project','connections':[{'id':'search','provider':'gsc',
        'account_ids':['site-example'],'credential_ref':'alpha-project/search','capability':'reporting','status':'unconfigured'}]}
    assert not connections.validate(config,'alpha-project')
    other=deepcopy(config);other['connections'][0]['credential_ref']='beta-project/search'
    assert connections.validate(other,'alpha-project')
    other=deepcopy(config);other['connections'][0]['access_token']='never-store-me'
    assert connections.validate(other,'alpha-project')
    root=tmp_path/'alpha-project';subprojects.start(root,'marketing','Alpha','Established service brief')
    c.setup(root,{'schema_version':1,'project_id':root.name,'campaign_id':'workshops','objective':'Requests','audience':'Organizers','offer':'Call',
        'connection_ids':['search'],'measurement':{'property':'wrong-account','timezone':'UTC'}},config)
    with pytest.raises(ValueError,match='account/property'):prepared(root,tmp_path)
    with pytest.raises(ValueError):c.safe(c.marketing(root),'../beta-project')
    (c.marketing(root)/'outside').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):c.safe(c.marketing(root),'outside/anything')


def test_cannot_finalize_another_projects_packet_or_tampered_review(tmp_path):
    alpha=project(tmp_path);beta=project(tmp_path,'beta-project')
    packet,_=prepared(alpha,tmp_path)
    with pytest.raises(ValueError,match='binding mismatch'):r.finalize(alpha,'workshops',packet['packet_id'],review(packet)|{'project_id':beta.name},tmp_path/'runtime')
    bad=deepcopy(packet);bad['current']['summary']['clicks']['value']=1000
    with pytest.raises(ValueError,match='integrity'):r.validate_packet(bad)


def test_v3_does_not_skip_existing_placement_or_delivery_guards():
    action={'id':'workshops--placement','campaign_id':'workshops','occurrence_id':'2026-01-14','objective':'Verify placement','actor':'agent',
        'dependencies':[],'prepared_materials':[],'next_step':'Verify','completion_criterion':'Captured placement',
        'commitment_state':'completed','execution_status':'verified','required_for_scope':True,'action_kind':'verify_placement','intended_result':'Captured evidence','verification':'text is insufficient'}
    document={'schema_version':3,'scope':'Placement','revision':1,'actions':[action]}
    assert any('placement' in error for error in execution.validate(document))
    action.update(action_kind='send_pitch',recipient='publisher',prepared_materials=[])
    assert any('authorization' in error for error in execution.validate(document))


def test_declared_claim_checks_do_not_claim_full_fact_checking():
    registry={'schema_version':1,'claims':[{'id':'availability','text':'Available in 3 cities','source':'Owner-approved service record','reviewed_at':'2026-01-01','expires_at':'2026-12-31'}]}
    assert not claims.check('Available in 3 cities [[claim:availability]]',registry,date(2026,2,1))
    assert claims.check('Available in 4 cities [[claim:availability]]',registry,date(2026,2,1))
    assert claims.check('Available in 3 cities [[claim:availability]]',registry,date(2027,1,1))
    assert claims.check('Text [[claim:missing]]',registry,date(2026,2,1))


def test_report_escapes_untrusted_markup(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    doc=review(packet);doc['diagnosis']='<script>alert(1)</script> [bad](javascript:alert(1))'
    output=r.finalize(root,'workshops',packet['packet_id'],doc,tmp_path/'runtime')
    text=Path(output['report']).read_text()
    assert '<script>' not in text and '[bad](javascript:' not in text


def test_account_and_campaign_allowlists_are_bound_as_pairs(tmp_path):
    root=tmp_path/'alpha-project';subprojects.start(root,'marketing','Alpha','Established service brief')
    config={'schema_version':1,'project_id':root.name,'connections':[
        {'id':'first','provider':'google_ads','account_ids':['account-a'],'campaign_ids':['111'],'credential_ref':'alpha-project/first','capability':'reporting','status':'unconfigured'},
        {'id':'second','provider':'google_ads','account_ids':['account-b'],'campaign_ids':['222'],'credential_ref':'alpha-project/second','capability':'reporting','status':'unconfigured'}]}
    c.setup(root,{'schema_version':1,'project_id':root.name,'campaign_id':'workshops','objective':'Requests','audience':'Organizers','offer':'Call',
        'connection_ids':['first','second'],'measurement':{'property':'account-a','timezone':'UTC','currency':'USD','attribution':'confirmed','maturity':'pending'}},config)
    file=tmp_path/'mixed.csv';file.write_text('Campaign,Campaign ID,Cost,Clicks,Impressions\nOther account,222,1,1,10\n')
    with pytest.raises(ValueError,match='this account connection scope'):
        r.prepare(root,'workshops','google-ads-campaigns-v1',file,CURRENT,runtime_root=tmp_path/'runtime')
    file.write_text(file.read_text().replace(',222,',',111,'))
    packet,_=r.prepare(root,'workshops','google-ads-campaigns-v1',file,CURRENT,runtime_root=tmp_path/'runtime')
    assert packet['current']['metadata']['property']=='account-a'


def test_completed_and_changed_task_proposals_require_explicit_followup_ids(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    next_packet,_=prepared(root,tmp_path);changed=review(next_packet)
    changed['tasks'][0]['next_step']='A materially different next step'
    with pytest.raises(ValueError,match='proposal changed'):r.finalize(root,'workshops',next_packet['packet_id'],changed,tmp_path/'runtime')
    c.task_event(root,'workshops','workshops--check-quality','accept')
    c.task_event(root,'workshops','workshops--check-quality','complete',evidence='Owner confirmed data')
    packet2,_=prepared(root,tmp_path)
    with pytest.raises(ValueError,match='cannot be re-proposed'):r.finalize(root,'workshops',packet2['packet_id'],review(packet2),tmp_path/'runtime')
    r.finalize(root,'workshops',packet2['packet_id'],review(packet2,'check-next-period'),tmp_path/'runtime')
    assert len(c.queue(root)['actions'])==2


def test_claim_and_campaign_fact_changes_invalidate_pending_review_and_task(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    second,_=prepared(root,tmp_path)
    registry={'schema_version':1,'claims':[{'id':'availability','text':'Available in 3 cities','source':'Reviewed record','reviewed_at':'2026-01-01','expires_at':'2027-01-01'}]}
    c.publish(root,{'campaigns/workshops/approved-claims.json':c.encoded(registry)},'Update approved claims')
    with pytest.raises(ValueError,match='changed'):r.finalize(root,'workshops',second['packet_id'],review(second),tmp_path/'runtime')
    with pytest.raises(ValueError,match='task context changed'):c.task_event(root,'workshops','workshops--check-quality','accept')
    config=c.load(root,'workshops');config['offer']='New supplied offer'
    c.publish(root,{'campaigns/workshops/campaign.json':c.encoded(config)},'Reviewed offer update')
    with pytest.raises(ValueError,match='task context changed'):c.task_event(root,'workshops','workshops--check-quality','accept')


def test_shared_publisher_enforces_history_and_allows_exact_restoration(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    result=r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    report=Path(result['report']);original=report.read_text();relative=report.relative_to(c.marketing(root)).as_posix()
    with pytest.raises(ValueError,match='history is immutable'):c.publish(root,{relative:'Overwritten history'},'Attempt history rewrite')
    report.unlink()
    c.publish(root,{relative:original},'Restore original report bytes')
    assert report.read_text()==original
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']


def test_totals_skip_does_not_discard_a_real_campaign_named_total(tmp_path):
    file=tmp_path/'ads.csv';file.write_text('Campaign,Campaign ID,Cost,Clicks,Impressions\nTotal: real campaign,123,10,5,100\nTotal: Campaigns,,10,5,100\n')
    doc=imp.import_export(file,'google-ads-campaigns-v1',CURRENT|{'property':'a','timezone':'UTC','currency':'USD','attribution':'confirmed','maturity':'pending'})
    assert doc['summary']['spend']['value']==10 and doc['excluded_total_rows']==1


def test_router_keeps_stale_descriptive_preview_private_and_recommendations_gated(tmp_path,monkeypatch):
    from scripts import route_workflow as routing
    projects=tmp_path/'projects';projects.mkdir();root=project(projects)
    monkeypatch.setattr(routing,'ROOT',tmp_path)
    (c.marketing(root)/'brief.md').write_text('Changed unreviewed brief')
    packet=routing.route_request('Import campaign results',intent='marketing-results-import',task_scope='execution',project=root.name,entry_mode='business_linked',check_skill='marketing-campaign-operator')
    assert packet['subproject']=='marketing' and packet['read_only_preview'] and not packet['canonical_publication_allowed']
    assert not packet.get('gate_blocked') and not packet['marketing_workstream']['valid_for_use']
    gated=routing.route_request('Review campaign results',intent='marketing-campaign-review',task_scope='execution',project=root.name,entry_mode='business_linked',check_skill='marketing-campaign-operator')
    assert gated['gate_blocked'] and gated['gate']=='marketing_workstream_review'


def test_history_aliases_and_missing_receipts_cannot_bypass_immutability(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    output=r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    path=Path(output['report']);original=path.read_text();relative=path.relative_to(c.marketing(root)).as_posix()
    path.unlink()
    alias=relative.replace('reviews/','reviews/unrelated/../')
    with pytest.raises(ValueError):c.publish(root,{alias:'Bad replacement'},'Attempt path alias')
    with pytest.raises(ValueError,match='missing/changed'):r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    c.publish(root,{relative:original},'Restore missing original')
    assert r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')['status']=='already_published'


def test_changed_report_filters_are_noncomparable_and_extra_metadata_is_rejected():
    a=imp.import_export(FIX/'gsc-baseline.csv','gsc-pages-v1',BASELINE|{'property':'site','timezone':'UTC'})
    b=imp.import_export(FIX/'gsc-current.csv','gsc-pages-v1',CURRENT|{'property':'site','timezone':'UTC','report_scope':'Different filters'})
    assert imp.compare(a,b)['status']=='non_comparable'
    with pytest.raises(ValueError,match='unsupported fields'):
        imp.import_export(FIX/'gsc-current.csv','gsc-pages-v1',CURRENT|{'property':'site','timezone':'UTC','customer_name':'Private name'})


def test_campaign_dispatch_is_namespaced_and_rejects_misplaced_campaign_artifacts(tmp_path):
    root=project(tmp_path)
    # A review from a different Marketing workflow is not a campaign review.
    c.publish(root,{'sources/review.json':'{"kind":"synthetic source review"}'},'Publish source evidence')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    for relative in ('campaigns/workshops/review.json','campaigns/workshops/nested/campaign.json',
                     'campaigns/workshops/connections.json'):
        with pytest.raises(ValueError,match='invalid location'):
            c.publish(root,{relative:'{}'},'Reject misplaced campaign artifact')


def test_late_correction_preserves_latest_week_and_requires_comparison_reconciliation(tmp_path):
    root=project(tmp_path);runtime=tmp_path/'runtime'
    first,_=prepared(root,tmp_path)
    first_result=r.finalize(root,'workshops',first['packet_id'],review(first),runtime)
    following=CURRENT|{'period_start':'2026-01-15','period_end':'2026-01-21','exported_at':'2026-01-22'}
    second,_=r.prepare(root,'workshops','gsc-pages-v1',FIX/'gsc-current.csv',following,
        FIX/'gsc-current.csv',CURRENT,runtime)
    second_result=r.finalize(root,'workshops',second['packet_id'],review(second)|{'tasks':[]},runtime)
    originals={path:Path(path).read_bytes() for path in (first_result['report'],second_result['report'])}
    correction=tmp_path/'corrected.csv'
    correction.write_text((FIX/'gsc-current.csv').read_text().replace(',20,150,',',22,150,'))
    corrected_metadata=CURRENT|{'exported_at':'2026-01-23'}
    corrected,_=r.prepare(root,'workshops','gsc-pages-v1',correction,corrected_metadata,
        FIX/'gsc-baseline.csv',BASELINE,runtime)
    result=r.finalize(root,'workshops',corrected['packet_id'],review(corrected)|{'tasks':[]},runtime)
    latest=c.read_json(c.marketing(root)/'campaigns/workshops/latest-review.json')
    assert latest['packet_id']==second['packet_id'] and latest['period']==['2026-01-15','2026-01-21']
    assert latest['last_processed_packet_id']==corrected['packet_id']
    assert latest['reconciliation_pending']==[second['packet_id']]
    text=Path(result['report']).read_text()
    assert 'Restatement of earlier observations' in text
    assert 'supersedes packet `'+first['packet_id']+'`' in text
    assert 'Comparisons awaiting reconciliation' in text
    assert all(Path(path).read_bytes()==raw for path,raw in originals.items())
    # Re-review the latest week against the corrected baseline, clearing its flag.
    refreshed,_=r.prepare(root,'workshops','gsc-pages-v1',FIX/'gsc-current.csv',following,
        correction,corrected_metadata,runtime)
    r.finalize(root,'workshops',refreshed['packet_id'],review(refreshed)|{'tasks':[]},runtime)
    latest=c.read_json(c.marketing(root)/'campaigns/workshops/latest-review.json')
    assert latest['packet_id']==refreshed['packet_id'] and latest['reconciliation_pending']==[]
    assert latest['supersedes']==second['packet_id'] and not latest['restatement']
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']


def test_history_backfill_and_legacy_history_migration(tmp_path):
    root=project(tmp_path);runtime=tmp_path/'runtime'
    packet,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),runtime)
    # Simulate a release predating the history index; immutable packets still exist.
    history_path=c.marketing(root)/'campaigns/workshops/review-history.json'
    history_path.unlink()
    state_path=c.marketing(root)/'workstream.json';state=c.read_json(state_path)
    state['artifact_refs']=[ref for ref in state['artifact_refs'] if ref['path']!='campaigns/workshops/review-history.json']
    state_path.write_text(c.encoded(state))
    earlier,_=r.prepare(root,'workshops','gsc-pages-v1',FIX/'gsc-baseline.csv',BASELINE,runtime_root=runtime)
    result=r.finalize(root,'workshops',earlier['packet_id'],review(earlier)|{'tasks':[]},runtime)
    latest=c.read_json(c.marketing(root)/'campaigns/workshops/latest-review.json')
    assert latest['packet_id']==packet['packet_id']
    assert 'Historical backfill' in Path(result['report']).read_text()
    assert len(c.read_json(history_path)['packets'])==2
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']


@pytest.mark.parametrize('change',['offer','claims'])
def test_stale_task_reproposal_rejected_and_owner_can_replace_it(tmp_path,change):
    root=project(tmp_path);packet,_=prepared(root,tmp_path);runtime=tmp_path/'runtime'
    r.finalize(root,'workshops',packet['packet_id'],review(packet),runtime)
    if change=='offer':
        doc=c.load(root,'workshops');doc['offer']='Updated offer'
        files={'campaigns/workshops/campaign.json':c.encoded(doc)}
    else:
        files={'campaigns/workshops/approved-claims.json':c.encoded({'schema_version':1,'claims':[
            {'id':'scope','text':'Available in 3 cities','source':'Reviewed record','reviewed_at':'2026-01-01','expires_at':'2027-01-01'}]})}
    c.publish(root,files,'Reviewed context update')
    fresh,_=prepared(root,tmp_path)
    with pytest.raises(ValueError,match='existing task context changed'):
        r.finalize(root,'workshops',fresh['packet_id'],review(fresh),runtime)
    result=r.finalize(root,'workshops',fresh['packet_id'],review(fresh)|{'tasks':[]},runtime)
    for text in (Path(result['report']).read_text(),(c.marketing(root)/'owner-actions.md').read_text()):
        assert 'Needs context review: workshops--check-quality' in text
        assert 'No due owner tasks.' in text
    c.task_event(root,'workshops','workshops--check-quality','decline',reason='Superseded after context review')
    replacement,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',replacement['packet_id'],review(replacement,'recheck-quality'),runtime)
    assert c.queue(root)['actions'][-1]['commitment_state']=='proposed'
    c.task_event(root,'workshops','workshops--recheck-quality','accept')
    assert c.queue(root)['actions'][-1]['commitment_state']=='accepted'
    assert c.queue(root)['actions'][0]['commitment_state']=='declined'


def test_existing_owner_packet_survives_campaign_finalization_and_task_event(tmp_path):
    root=project(tmp_path);material='Synthetic reviewed listing.\n'
    prerequisite={'id':'eligibility','objective':'Confirm eligibility','actor':'agent','dependencies':[],
        'prepared_materials':[],'next_step':'Review eligibility','completion_criterion':'Eligibility confirmed',
        'commitment_state':'proposed','execution_status':'prepared','required_for_scope':True,
        'action_kind':'generic','intended_result':'Eligibility confirmed'}
    delivery=deepcopy(prerequisite)|{'id':'submit-listing','objective':'Submit listing','actor':'owner',
        'dependencies':['eligibility'],'commitment_state':'accepted','execution_status':'awaiting_owner',
        'action_kind':'submit_listing','recipient':'Example publisher','destination':'https://example.test/portal',
        'user_step':'Paste the reviewed packet into the portal','eligibility_checked_at':'2026-10-18',
        'audience_fit':'Workshop audience','authorization_basis':'Owner to review','follow_up':'Check response','fee':'none',
        'prepared_materials':[{'path':'listing.md','sha256':c.bytes_digest(material.encode())}]}
    plan={'schema_version':2,'scope':'Existing listing','revision':1,'actions':[prerequisite,delivery]}
    plan_text,owners=execution.render(plan)
    c.publish(root,{'listing.md':material,'execution-plan.json':c.encoded(plan),
        'execution-plan.md':plan_text,'owner-actions.md':owners},'Existing owner work')
    packet,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',packet['packet_id'],review(packet),tmp_path/'runtime')
    def assert_packet():
        text=(c.marketing(root)/'owner-actions.md').read_text()
        for phrase in ('blocked by eligibility','https://example.test/portal','listing.md','Paste the reviewed packet into the portal'):
            assert phrase in text
        assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    assert_packet()
    c.task_event(root,'workshops','workshops--check-quality','accept')
    assert_packet()


def test_owner_views_prioritize_due_work_over_snoozed_work(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    task=r.finalized_plan(root,packet,review(packet))['actions'][0]
    actions=[]
    for index in range(5):
        action=deepcopy(task);action['id']=f'workshops--item-{index}'
        if index<3:
            action.update(commitment_state='deferred',deferred_until=(date.today()+timedelta(days=7)).isoformat())
        elif index==3:
            action.update(commitment_state='deferred',deferred_until=(date.today()-timedelta(days=1)).isoformat())
        actions.append(action)
    plan={'schema_version':3,'scope':'Workshops','revision':1,'actions':actions}
    for text in (r.owner_actions(plan,root),r.report(packet,review(packet),plan)):
        assert text.index('workshops--item-3')<text.index('workshops--item-0')
        assert text.index('workshops--item-4')<text.index('workshops--item-0')
        assert 'Snoozed: workshops--item-0' in text
        assert 'Snoozed: workshops--item-3' not in text


def test_history_repairs_old_latest_pointer_and_rejects_foreign_history(tmp_path):
    root=project(tmp_path);runtime=tmp_path/'runtime';first,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',first['packet_id'],review(first),runtime)
    latest_path='campaigns/workshops/latest-review.json';old_latest=c.read_json(c.marketing(root)/latest_path)
    following=CURRENT|{'period_start':'2026-01-15','period_end':'2026-01-21','exported_at':'2026-01-22'}
    second,_=r.prepare(root,'workshops','gsc-pages-v1',FIX/'gsc-current.csv',following,runtime_root=runtime)
    r.finalize(root,'workshops',second['packet_id'],review(second)|{'tasks':[]},runtime)
    c.publish(root,{latest_path:c.encoded(old_latest)},'Reproduce pre-fix pointer rollback')
    correction,_=prepared(root,tmp_path)
    r.finalize(root,'workshops',correction['packet_id'],review(correction)|{'tasks':[]},runtime)
    assert c.read_json(c.marketing(root)/latest_path)['packet_id']==second['packet_id']
    history_path='campaigns/workshops/review-history.json'
    history=c.read_json(c.marketing(root)/history_path)
    history['packets'][0]=history['packets'][0].replace('/workshops/','/other-campaign/')
    with pytest.raises(ValueError,match='invalid Marketing artifact'):
        c.publish(root,{history_path:c.encoded(history)},'Reject history scope mismatch')


def test_owner_summary_does_not_recommend_repeating_submitted_work(tmp_path):
    root=project(tmp_path);packet,_=prepared(root,tmp_path)
    action=r.finalized_plan(root,packet,review(packet))['actions'][0]
    action.update(commitment_state='accepted',execution_status='submitted')
    text=r.owner_actions({'actions':[action]},root)
    assert 'No due owner tasks.' in text
    assert 'Needs outcome review: workshops--check-quality' in text
