import json
from copy import deepcopy
from pathlib import Path

from scripts.marketing.keyword_map import validate,validate_resource

FIXTURE=Path(__file__).resolve().parents[1]/'fixtures/marketing/earned-media'


def test_existing_page_reuse_and_evidence_binding(tmp_path):
    doc=json.loads((FIXTURE/'keyword-map.json').read_text())
    assert not validate(doc,FIXTURE)
    doc['rows'][0]['decision']='create'
    assert any('existing page' in e for e in validate(doc,FIXTURE))
    doc['rows'][0]['decision']='improve'
    assert validate(doc,tmp_path)


def test_volume_conflicting_assignment_and_locale():
    doc=json.loads((FIXTURE/'keyword-map.json').read_text())
    second={**deepcopy(doc['rows'][0]),'id':'other','target_url':'https://workshop.example/other'}
    doc['rows'].append(second)
    assert any('conflicting primary' in e for e in validate(doc,FIXTURE))
    second['locale']='DE:de'
    assert not validate(doc,FIXTURE)
    second['volume']=100
    assert any('provider and date' in e for e in validate(doc,FIXTURE))


def test_public_resource_requires_real_source_binding():
    binding=json.loads((FIXTURE/'keyword-map.json').read_text())['rows'][0]['evidence_refs'][0]
    resource={k:'Reviewed public fixture' for k in ['audience_job','utility','original_vs_compiled','limitations',
        'public_use_suitability','maintenance_trigger','maintenance_owner','distribution_rationale']}
    resource.update(source_bindings=[binding],destination_url='https://workshop.example/guide')
    assert not validate_resource(resource,FIXTURE)
    resource['source_bindings'][0]['sha256']='a'*64
    assert validate_resource(resource,FIXTURE)
