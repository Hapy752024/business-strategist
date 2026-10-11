import json
from pathlib import Path
import pytest

from scripts.marketing.earned_media import catalogue_candidates,import_links,validate,prepare
from scripts.marketing import execution,observations

FIXTURE=Path(__file__).resolve().parents[1]/'fixtures/marketing/earned-media'


def test_catalogue_claims_remain_unknown_and_invalid_urls_removed():
    rows=catalogue_candidates(json.loads((FIXTURE/'catalogue.json').read_text()))
    assert len(rows)==1
    assert rows[0]['fee'] is None and rows[0]['link_inclusion']=='unknown'


def test_qualified_opportunity_and_exact_material_packet():
    row=json.loads((FIXTURE/'opportunity.json').read_text())
    assert not validate(row,FIXTURE)
    plan=prepare(row,base=FIXTURE,material='pitch.md')
    assert not execution.validate(plan,FIXTURE)
    assert plan['actions'][0]['commitment_state']=='proposed'
    plan['actions'][0]['execution_status']='submitted'
    assert any('authorization' in e for e in execution.validate(plan,FIXTURE))
    row['official_domain']='lookalike.example'
    assert validate(row,FIXTURE)
    with pytest.raises(ValueError):prepare(row,base=FIXTURE,material='pitch.md')


def test_duplicate_and_missing_qualification_facts():
    row=json.loads((FIXTURE/'opportunity.json').read_text())
    assert any('duplicate' in e for e in validate([row,row],FIXTURE))
    row['fee']=None
    assert validate(row,FIXTURE)
    row['qualification']='unresolved'
    assert not validate(row,FIXTURE)


def test_links_export_not_live_or_domain_only(tmp_path):
    result=import_links(FIXTURE/'links.csv',source_column='Source',target_column='Target',
        property_url='https://workshop.example/',exported_at='2026-10-11')
    assert result['candidates'][0]['qualification']=='candidate'
    assert 'historical' in result['limits']
    path=tmp_path/'domains.csv';path.write_text('Domain\nexample.com\n')
    with pytest.raises(ValueError):import_links(path,source_column='Domain',target_column='Target',property_url='x',exported_at='2026-10-11')


def test_search_console_export_uses_explicit_mapping_and_unknowns(tmp_path):
    path=tmp_path/'gsc.csv';path.write_text('Query,Clicks,Extra\nbicycle repair,12,private lead data\nunavailable,,private lead data\n')
    mapping={k:k for k in ['property','source','period_start','period_end','timezone','metric','unit']}
    mapping.update(query='Query',value='Clicks')
    context={'property':'https://workshop.example/','source':'google_search_console','period_start':'2026-10-01',
        'period_end':'2026-10-07','timezone':'UTC','metric':'clicks','unit':'count','exported_at':'2026-10-11'}
    doc=observations.normalize(path,mapping,context)
    assert doc['observations'][0]['value']==12
    assert doc['observations'][1]['availability']=='unknown'
    assert 'private lead data' not in json.dumps(doc)
