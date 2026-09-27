"""Input-derived checks for source numbers in externally consumed case appraisals."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from scripts import case_workspace as cases
from scripts.verify_numeric_claims import checked_claims, pointer
from test_case_end_to_end import appraisal, setup
from appraisal_gate_fixture import install as isolate_research_gate


@pytest.fixture(autouse=True)
def _isolated_research_gate(monkeypatch):
    isolate_research_gate(monkeypatch)

ROOT = Path(__file__).resolve().parents[1]


def packet_with_number(root):
    draft = appraisal(root)
    draft.pop('economics_inputs')
    source = root / 'cases/a/market_research/pain_points/figures.json'
    observation = {'metric':'gross_written_premium', 'value':'-42.5', 'period':'FY2025',
                   'currency':'EUR', 'unit':'million', 'scope':'Germany'}
    source.write_text(json.dumps({'observations':[observation]}))
    binding = cases.source_binding(root, 'cases/a/market_research/pain_points/figures.json',
                                   locator='/observations/0', applicability='Case A report figure')
    draft['source_bindings'].append(binding)
    draft['documents']['business-case.md'] = 'The source reports {{source_numeric.premium}} EUR million in FY2025.'
    draft['numeric_claims'] = [{**observation, 'id':'premium', 'document':'business-case.md',
                                'status':'verified', 'source_binding':binding}]
    return draft, source


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file() and p.name != 'project.lock'}


def test_verified_number_publishes_rendered_prose_and_receipt(tmp_path):
    root = setup(tmp_path)
    draft, source = packet_with_number(root)
    cases.publish_assessment(root, 'a', draft, 'numeric-ok', 'Checked source figure')
    case = root / 'cases/a'
    assert '-42.5 EUR million' in (case / 'business-case.md').read_text()
    receipt = json.loads((case / 'numeric-claims.json').read_text())
    assert receipt['verified_count'] == 1 and receipt['unverified_count'] == 0
    assert receipt['claims'][0]['source_sha256'] == draft['numeric_claims'][0]['source_binding']['digest']
    assert '{{source_numeric.' not in (case / 'business-case.md').read_text()


@pytest.mark.parametrize('field,value', [
    ('value','42.5'), ('metric','debt'), ('period','FY2024'), ('currency','USD'),
    ('unit','thousand'), ('scope','Italy')])
def test_wrong_context_or_sign_blocks_publication_without_writes(tmp_path, field, value):
    root = setup(tmp_path)
    draft, _ = packet_with_number(root)
    draft['numeric_claims'][0][field] = value
    before = snapshot(root)
    with pytest.raises(ValueError, match='differs from source'):
        cases.publish_assessment(root, 'a', draft, 'numeric-wrong', 'Wrong figure')
    assert snapshot(root) == before
    assert not (root / 'cases/a/numeric-claims.json').exists()


def test_changed_source_or_unbound_pointer_blocks_publication(tmp_path):
    root = setup(tmp_path)
    draft, source = packet_with_number(root)
    source.write_text(source.read_text().replace('-42.5','-43'))
    with pytest.raises(ValueError, match='stale source-use binding'):
        cases.publish_assessment(root, 'a', draft, 'numeric-stale', 'Stale figure')
    draft, _ = packet_with_number(root)
    draft['numeric_claims'][0]['source_binding']['locator'] = '/observations/99'
    with pytest.raises(ValueError, match='source locator does not resolve'):
        cases.publish_assessment(root, 'a', draft, 'numeric-pointer', 'Wrong pointer')


def test_unverified_claim_is_visible_and_does_not_pass_as_verified(tmp_path):
    root = setup(tmp_path)
    draft, _ = packet_with_number(root)
    row = draft['numeric_claims'][0]
    row.pop('source_binding')
    row['status'] = 'unverified'; row['reason'] = 'Original PDF figure not structured or checked'
    cases.publish_assessment(root, 'a', draft, 'numeric-open', 'Flag unsupported figure')
    case = root / 'cases/a'
    assert '[unverified numeric value: premium]' in (case / 'business-case.md').read_text()
    receipt = json.loads((case / 'numeric-claims.json').read_text())
    assert receipt['verified_count'] == 0 and receipt['unverified_count'] == 1


def test_markers_duplicates_and_missing_bindings_fail(tmp_path):
    root = setup(tmp_path); draft, _ = packet_with_number(root)
    row = draft['numeric_claims'][0]
    with pytest.raises(ValueError, match='marker'):
        checked_claims(root, {'business-case.md':'No marker'}, [row], draft['source_bindings'])
    with pytest.raises(ValueError, match='unique'):
        checked_claims(root, {'business-case.md':'{{source_numeric.premium}}'}, [row,row], draft['source_bindings'])
    with pytest.raises(ValueError, match='undeclared'):
        checked_claims(root, {'business-case.md':'{{source_numeric.other}}'}, [], draft['source_bindings'])
    with pytest.raises(ValueError, match='binding is missing'):
        checked_claims(root, {'business-case.md':'{{source_numeric.premium}}'}, [row], [])
    with pytest.raises(ValueError, match='exactly once'):
        checked_claims(root, {'business-case.md':'{{source_numeric.premium}} {{source_numeric.premium}}'}, [row], draft['source_bindings'])


def test_comparison_claim_and_economics_placeholder_coexist(tmp_path):
    root = setup(tmp_path); draft, _ = packet_with_number(root)
    from test_case_economics import inputs
    from scripts.case_economics import calculate
    draft['economics_inputs'] = inputs()
    digest = calculate(inputs())['input_digest']
    draft['economics_input_digest'] = digest
    draft['documents']['business-case.md'] = 'Source monthly revenue {{source_numeric.premium}}. Model contribution {{economics.results.contribution_per_unit}}.'
    draft['comparison']['summary'] = 'External observed value {{source_numeric.summary}}.'
    draft['numeric_claims'].append({**draft['numeric_claims'][0], 'id':'summary', 'document':'comparison.summary'})
    cases.publish_assessment(root, 'a', draft, 'numeric-and-model', 'Publish both checked figures')
    case = root / 'cases/a'
    assert '-42.5' in (case / 'business-case.md').read_text()
    assert '50' in (case / 'business-case.md').read_text()
    assert '-42.5' in cases.case_manifest(root,'a')['comparison']['summary']


def test_cli_checks_packet_without_writing(tmp_path):
    root = setup(tmp_path); draft, _ = packet_with_number(root)
    packet = tmp_path / 'draft.json'; packet.write_text(json.dumps(draft))
    before = snapshot(root)
    run = subprocess.run([sys.executable,str(ROOT/'scripts/verify_numeric_claims.py'),
                          '--workspace',str(root),'--packet',str(packet)],capture_output=True,text=True)
    assert run.returncode == 0 and json.loads(run.stdout)['verified_count'] == 1
    assert snapshot(root) == before
    draft['numeric_claims'][0]['currency'] = 'USD'; packet.write_text(json.dumps(draft))
    run = subprocess.run([sys.executable,str(ROOT/'scripts/verify_numeric_claims.py'),
                          '--workspace',str(root),'--packet',str(packet)],capture_output=True,text=True)
    assert run.returncode != 0 and 'currency differs from source' in json.loads(run.stdout)['error']
    assert snapshot(root) == before


def test_json_pointer_escapes_and_bad_paths():
    assert pointer({'a/b':{'~key':7}},'/a~1b/~0key') == 7
    for invalid in ('a', '/bad~2escape', '/missing', '/list/99'):
        with pytest.raises(ValueError):
            pointer({'list':[1]}, invalid)


def test_claims_cannot_disappear_on_cosmetic_revision_and_material_revision_clears_receipt(tmp_path):
    root = setup(tmp_path); draft, _ = packet_with_number(root)
    cases.publish_assessment(root,'a',draft,'numeric-first','First bound figure')
    current = cases.case_manifest(root,'a')
    revised = copy.deepcopy(draft)
    revised.update(manifest_revision=current['manifest_revision'], assessment_revision=current['assessment_revision'], material_change=False)
    revised.pop('numeric_claims')
    with pytest.raises(ValueError, match='retain current numeric claims'):
        cases.publish_assessment(root,'a',revised,'numeric-omitted','Cosmetic wording')
    revised['material_change'] = True
    revised['documents']['business-case.md'] = 'Figure withdrawn pending fresh review.'
    cases.publish_assessment(root,'a',revised,'numeric-withdrawn','Withdraw figure and reassess')
    receipt = json.loads((root/'cases/a/numeric-claims.json').read_text())
    assert receipt['claims'] == [] and receipt['verified_count'] == 0


def test_numeric_claim_schema_matches_checked_payload(tmp_path):
    from jsonschema import Draft202012Validator
    root = setup(tmp_path); draft, _ = packet_with_number(root)
    schema = json.loads((ROOT/'schemas/numeric-claim.schema.json').read_text())
    validator = Draft202012Validator(schema)
    assert list(validator.iter_errors(draft['numeric_claims'][0])) == []
    bad = dict(draft['numeric_claims'][0], currency='usd')
    assert list(validator.iter_errors(bad))
    unverified = dict(draft['numeric_claims'][0]); unverified.pop('source_binding')
    unverified.update(status='unverified', reason='Source unresolved')
    assert list(validator.iter_errors(unverified)) == []
