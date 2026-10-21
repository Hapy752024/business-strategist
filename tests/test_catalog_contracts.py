"""Typed produce/consume contracts in the skill catalog."""
import json
from pathlib import Path

from scripts import validate_skill_routes as v

ROOT = Path(__file__).resolve().parents[1]


def item(name, schema=None, external=False):
    out = {'artifact': name, 'schema': schema, 'path_patterns': ['cases/{case}/x.json'], 'freshness': 'digest'}
    if external:
        out['external'] = True
    return out


def test_catalog_consumes_must_be_produced():
    catalog = {'a': {'produces': [item('ledger')], 'consumes': []},
               'b': {'consumes': [item('ledger'), item('orphan')]}}
    errors = v.validate_contracts(catalog, ROOT)
    assert errors == ['consumed artifact orphan by b is not produced by any skill and not external']


def test_catalog_external_consume_allowed():
    assert v.validate_contracts({'b': {'consumes': [item('founder-brief', external=True)]}}, ROOT) == []


def test_catalog_mode_contracts_count():
    catalog = {'a': {'modes': {'m': {'produces': [item('card')]}}}, 'b': {'consumes': [item('card')]}}
    assert v.validate_contracts(catalog, ROOT) == []


def test_catalog_missing_schema_reported():
    errors = v.validate_contracts({'a': {'produces': [item('x', schema='schemas/nope.schema.json')]}}, ROOT)
    assert errors == ['schema schemas/nope.schema.json missing']


def test_catalog_bad_contract_shape_reported():
    errors = v.validate_contracts({'a': {'produces': [{'artifact': 'x'}]}}, ROOT)
    assert errors and 'a' in errors[0]


def test_repository_catalog_contracts_valid():
    catalog = json.loads((ROOT / 'config/skill-catalog.json').read_text())['skills']
    assert v.validate_contracts(catalog, ROOT) == []
    assert any(c['artifact'] == 'assumption-register' for c in catalog['idea-grill']['produces'])
    assert any(c['artifact'] == 'experiment-card' for c in catalog['opportunity-risk-designer']['modes']['smoke_test']['produces'])
