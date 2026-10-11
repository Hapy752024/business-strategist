from copy import deepcopy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.marketing import customer_questions as q
from scripts import subprojects, case_workspace

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/marketing/customer-questions'


def fixture(tmp_path):
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    return json.loads((tmp_path/'customer-questions.json').read_text()), json.loads((tmp_path/'content-brief.json').read_text())


def test_reviewed_question_and_brief(tmp_path):
    doc, brief = fixture(tmp_path)
    assert not q.validate(doc, tmp_path)
    assert not q.validate_brief(brief, tmp_path)
    assert 'How long does setup take?' in q.render(doc)
    brief['customer_questions']['question_ids'] = ['unknown']
    assert q.validate_brief(brief, tmp_path)
    assert not q.validate_brief({'brief_id':'CB-002'}, tmp_path)


def test_fabricated_quote_and_supplier_cannot_be_customer(tmp_path):
    doc, _ = fixture(tmp_path)
    doc['questions'][0]['passage'] = 'Please charge me more'
    assert 'absent from source' in str(q.validate(doc, tmp_path))
    doc, _ = fixture(tmp_path)
    record = json.loads((tmp_path/'sources/question.json').read_text()); record['classification_basis'] = 'explicit_supplier_identity'
    raw = json.dumps(record).encode(); (tmp_path/'sources/question.json').write_bytes(raw)
    doc['questions'][0]['source']['sha256'] = hashlib.sha256(raw).hexdigest()
    assert 'cannot become customer voice' in str(q.validate(doc, tmp_path))


def test_private_render_and_unknowns(tmp_path):
    doc, _ = fixture(tmp_path)
    row = doc['questions'][0]; row['visibility'] = 'private'
    assert q.validate(doc, tmp_path)
    row.update(access_context='Owner supplied synthetic sanitized extract for this task', sanitized_extract=True, current_answer='private synthetic answer')
    assert not q.validate(doc, tmp_path)
    rendered = q.render(doc)
    assert row['passage'] not in rendered and row['current_answer'] not in rendered
    assert 'unknown' in rendered


def test_publication_staged_sources_refresh_and_resume(tmp_path):
    root = tmp_path/'project'; subprojects.start(root, 'marketing', 'Synthetic', 'Supplied data only')
    files = {p.relative_to(FIXTURE).as_posix():p.read_bytes() for p in FIXTURE.rglob('*.json')}
    def publish(payload):
        return subprojects.publish_marketing_workstream(root, payload,
            expected_manifest_revision=case_workspace.read_project(root)['manifest_revision'], decision_id='questions-test-' + str(case_workspace.read_project(root)['manifest_revision']), reason='Synthetic question fixture')
    publish(files)
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']
    revision = case_workspace.read_project(root)['manifest_revision']
    with pytest.raises(ValueError): publish({'sources/question.json':b'{}'})
    assert case_workspace.read_project(root)['manifest_revision'] == revision
    target = subprojects.path(root,'marketing')/'sources/review.json'; target.write_text('{}')
    assert not subprojects.validate_marketing_workstream(root)['valid_for_use']
    publish({'sources/review.json':files['sources/review.json']})
    assert subprojects.validate_marketing_workstream(root)['valid_for_use']


def test_outcome_tracks_exact_answer(tmp_path):
    doc, _ = fixture(tmp_path); row=doc['questions'][0]; row['current_answer']='Synthetic answer'
    out={'question_id':'Q1','answer_sha256':hashlib.sha256(row['current_answer'].encode()).hexdigest(),
         'observed_at':'2026-10-10T00:00:00Z','outcome':'inconclusive','limits':'Synthetic, no effectiveness established'}
    raw=json.dumps(out).encode(); (tmp_path/'outcome.json').write_bytes(raw)
    row['outcome']={'path':'outcome.json','sha256':hashlib.sha256(raw).hexdigest()}
    assert not q.validate(doc,tmp_path)
    row['current_answer']='Changed answer'
    assert q.validate(doc,tmp_path)


def test_brief_cannot_change_question_audience(tmp_path):
    shutil.copytree(FIXTURE,tmp_path,dirs_exist_ok=True)
    brief=json.loads((tmp_path/'content-brief.json').read_text()); brief['audience_segment']='Enterprise CTOs'
    assert 'audience differs' in str(q.validate_brief(brief,tmp_path))
