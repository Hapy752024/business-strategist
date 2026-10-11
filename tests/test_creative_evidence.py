from copy import deepcopy
import json
import shutil
from pathlib import Path

import pytest

from scripts.marketing import creative_evidence as c
from scripts import subprojects, case_workspace

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/marketing/creative-evidence'


def fixture(tmp_path):
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    return json.loads((tmp_path/'creative-evidence.json').read_text())


def test_ratios_cohorts_and_replication(tmp_path):
    doc=fixture(tmp_path); assert not c.validate(doc,tmp_path)
    report=c.compare(doc); assert len(report['cohorts']) == 2 and len(report['excluded']) == 1
    organic=report['cohorts'][0]; assert organic['examples'][0]['ratios']['shares_per_1000_views'] == 20
    assert organic['examples'][0]['ratios']['saves_per_1000_views'] is None
    assert organic['patterns'][0]['replicated']
    assert not report['cohorts'][1]['patterns'][0]['replicated']


@pytest.mark.parametrize('value', [True, -1, float('nan'), float('inf'), 1.5])
def test_invalid_counts(tmp_path,value):
    doc=fixture(tmp_path); doc['examples'][0]['metrics']['views']['value']=value
    assert c.validate(doc,tmp_path)


def test_zero_unknown_and_source_mismatch(tmp_path):
    doc=fixture(tmp_path); doc['examples'][0]['metrics']['views']['value']=0
    assert c.compare(doc)['cohorts'][0]['examples'][0]['ratios']['shares_per_1000_views'] is None
    assert 'differ from retained' in str(c.validate(doc,tmp_path))
    doc=fixture(tmp_path); doc['examples'][0]['metrics']['shares']['availability']='suppressed'
    assert c.validate(doc,tmp_path)


def test_distinct_windows_definitions_and_unknown_creators(tmp_path):
    doc=fixture(tmp_path); doc['examples'][1]['observed_at']='2026-10-09T00:00:00Z'
    assert len(c.compare(doc)['cohorts']) == 3
    doc=fixture(tmp_path); doc['examples'][1]['metrics']['views']['definition']='different view event'
    assert len(c.compare(doc)['cohorts']) == 3
    doc=fixture(tmp_path); doc['examples'][1]['creator']=None
    assert not c.compare(doc)['cohorts'][0]['patterns'][0]['replicated']
    doc['examples'][1]['url']=doc['examples'][0]['url']
    assert 'duplicate example URL' in str(c.validate(doc,tmp_path))


def test_publisher_validates_staged_evidence_and_resume(tmp_path):
    root=tmp_path/'project'; subprojects.start(root,'marketing','Synthetic','No live channel')
    files={p.relative_to(FIXTURE).as_posix():p.read_bytes() for p in FIXTURE.rglob('*.json')}
    subprojects.publish_marketing_workstream(root,files,expected_manifest_revision=case_workspace.read_project(root)['manifest_revision'],decision_id='creative-test',reason='Synthetic comparison')
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    with pytest.raises(ValueError):
        subprojects.publish_marketing_workstream(root,{'sources/1.json':b'{}'},expected_manifest_revision=case_workspace.read_project(root)['manifest_revision'],decision_id='bad-source',reason='Must reject')
    (subprojects.path(root,'marketing')/'sources/1.json').write_text('{}')
    assert not subprojects.validate_marketing_workstream(root)['valid_for_use']


def test_overflow_is_undefined(tmp_path):
    doc = fixture(tmp_path); doc['examples'][0]['metrics']['shares']['value'] = 10**400
    assert c.compare(doc)['cohorts'][0]['examples'][0]['ratios']['shares_per_1000_views'] is None
