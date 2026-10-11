from copy import deepcopy
import hashlib
import json
import shutil
from pathlib import Path

from scripts.evidence_scout.work_packets import assess, validate

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/research/work-packets'


def setup(tmp_path):
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    return json.loads((tmp_path / 'ledger.json').read_text())


def test_failed_unit_only_and_exhaustion(tmp_path):
    doc = setup(tmp_path)
    before = {p: p.read_bytes() for p in (tmp_path / 'outputs').glob('*.txt')}
    result = assess(doc, tmp_path)
    assert result['valid'] and not result['complete']
    assert [r['id'] for r in result['units'] if r['ready']] == ['d']
    assert all(p.read_bytes() == raw for p, raw in before.items())
    doc['units'][3]['attempts'] = 3
    row = assess(doc, tmp_path)['units'][3]
    assert row['status'] == 'blocked' and not row['ready']


def test_change_propagates_to_consumers_and_not_siblings(tmp_path):
    doc = setup(tmp_path)
    a, b = doc['units'][:2]
    a_out = {'path':'outputs/a.txt', 'sha256':hashlib.sha256((tmp_path/'outputs/a.txt').read_bytes()).hexdigest()}
    b['inputs'] = [a_out]; b['dependencies'] = ['a']
    receipt = json.loads((tmp_path/'receipts/b.json').read_text()); receipt['inputs'] = b['inputs']
    raw = json.dumps(receipt).encode(); (tmp_path/'receipts/b.json').write_bytes(raw)
    b['receipt']['sha256'] = hashlib.sha256(raw).hexdigest()
    assert assess(doc, tmp_path)['units'][1]['status'] == 'accepted'
    (tmp_path/'outputs/a.txt').write_text('changed')
    rows = {r['id']:r for r in assess(doc, tmp_path)['units']}
    assert rows['a']['status'] == rows['b']['status'] == 'stale'
    assert rows['c']['status'] == 'accepted' and rows['d']['ready']


def test_receipt_binding_scope_and_required_checks(tmp_path):
    doc = setup(tmp_path)
    (tmp_path/'checks/a.json').write_text('changed')
    assert assess(doc, tmp_path)['units'][0]['status'] == 'stale'
    doc['units'][0]['checks'].append('source-review')
    assert 'required checks' in str(assess(doc, tmp_path))


def test_history_counters_and_accepted_rewrites(tmp_path):
    old = setup(tmp_path); new = deepcopy(old)
    new['units'][3]['attempts'] = 0
    assert 'counter cannot decrease' in str(assess(new, tmp_path, old))
    new = deepcopy(old); new['units'][0]['scope'] = 'Rewrite everything'
    assert 'unchanged accepted work' in str(assess(new, tmp_path, old))


def test_ownership_dependencies_and_path_boundaries(tmp_path):
    doc = setup(tmp_path)
    doc['units'][1]['output_paths'] = ['outputs/a.txt']
    assert validate(doc)
    doc = setup(tmp_path); doc['units'][0]['output_paths'] = ['../escape']
    assert not assess(doc, tmp_path)['valid']
    doc = setup(tmp_path); doc['units'][1]['dependencies'] = ['a']
    assert 'named input' in str(validate(doc))
    doc = setup(tmp_path); doc['units'][0]['dependencies'] = ['missing']
    assert validate(doc)


def test_return_scope_and_attempt_bool(tmp_path):
    doc = setup(tmp_path); doc['units'][3]['return']['allowed_outputs'] = ['outputs/a.txt']
    assert not assess(doc, tmp_path)['valid']
    doc = setup(tmp_path); doc['units'][0]['attempts'] = True
    assert validate(doc)


def test_exhausted_pending_cannot_resume_and_accepted_cannot_disappear(tmp_path):
    old = setup(tmp_path); doc = deepcopy(old)
    doc['units'][3].update(state='pending', attempts=3)
    assert not assess(doc,tmp_path,old)['units'][3]['ready']
    doc = deepcopy(old); doc['units'].pop(0)
    assert not assess(doc,tmp_path,old)['valid']
    doc = deepcopy(old); doc['units'][3]['output_paths'] = ['.']
    assert not assess(doc,tmp_path)['valid']
