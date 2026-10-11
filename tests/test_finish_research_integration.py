"""Metadata, originals and company records must retain their evidence boundaries."""
import json
from argparse import Namespace

import pytest

from scripts.market_research import institutional_sources as institutions
from scripts.market_research import registry_sources as registers
from scripts.market_research import fetch_research_document as documents
from scripts.market_research.research_facts import check_fact
from scripts.evidence_scout import provider_doctor as doctor


def test_new_readiness_aliases_and_cached_success_are_visible():
    for name in ['ecb', 'fred', 'bis', 'world_bank', 'companies_house']:
        assert doctor.VALIDATION_PROVIDER_ALIASES[name] == name
        item = doctor.BackendStatus(name, 'credentials_present', 'Unchecked')
        assert doctor.apply_live_validation(item, {name: {'status': 'ok'}}).usable
        assert not doctor.apply_live_validation(item, {name: {'status': 'stale'}}).usable


def test_sdmx_definitions_never_become_statistical_observations(monkeypatch):
    args = institutions.parser().parse_args(['--provider','ecb','--discover','--dataset','EXR','--out','/unused'])
    def get(url, **kwargs):
        assert '/dataflow/ECB/EXR/latest' in url
        return {'ok': True, 'body': {'text': '<Structure><Dataflow id="EXR"><Name>Exchange rates</Name></Dataflow></Structure>'}}
    monkeypatch.setattr(institutions, 'http_get', get)
    capture = institutions.collect('ecb', args)
    assert capture['metadata'][0]['id'] == 'EXR'
    assert capture['observations'] == [] and capture['kind'] == 'dataset_metadata'
    with pytest.raises(ValueError, match='SDMX structure'):
        institutions.metadata_records('bis', {'text': '<html>Failure</html>'})


def test_original_fulltext_is_pending_and_original_change_is_detected(tmp_path, monkeypatch):
    original = tmp_path/'input.xml'
    original.write_text('<TEI><text>Measured results belong to a limited sample and require methods review.</text></TEI>')
    out = tmp_path/'captured'
    monkeypatch.setattr('sys.argv', ['fetch','--input',str(original),'--source-url','https://university.example/study.xml',
        '--publisher','University','--out',str(out)])
    assert documents.main() == 0
    fact = json.loads((out/'research-facts.jsonl').read_text())
    assert fact['review_status'] == 'pending'
    check_fact(fact, out)
    (out/'original.xml').write_text('<TEI>Changed original</TEI>')
    with pytest.raises(ValueError, match='Original research document changed'):
        check_fact(fact, out)


def test_xml_entities_are_rejected_and_spreadsheet_rows_are_bounded():
    with pytest.raises(ValueError, match='entity declarations'):
        documents.extract(b'<!DOCTYPE x [<!ENTITY a "boom">]><x>&a;</x>', 'xml')
    from openpyxl import Workbook
    import io
    workbook=Workbook(); sheet=workbook.active
    sheet.append(['metric','value']);sheet.append(['count',0]);sheet.append(['unknown',None])
    raw=io.BytesIO();workbook.save(raw)
    texts, complete=documents.extract(raw.getvalue(),'xlsx',limit=2)
    assert not complete and '0' in texts[0][1]


def test_registry_export_preserves_identifiers_original_rows_and_caps(tmp_path):
    original=tmp_path/'register.csv'; original.write_text('registration,name\n123,First\n456,Second\n')
    args=Namespace(provider='register_export',input=original,source_url='https://official.example/export.csv',
        identifier_field='registration',limit=1,publisher='Official register',country='Germany')
    capture=registers.collect(args)
    assert not capture['complete_within_query']
    assert capture['observations'][0]['identity']=='123'
    assert capture['observations'][0]['original_row']['name']=='First'
    assert capture['observations'][0]['commercial_success']=='unresolved'


def test_public_document_urls_reject_private_networks(monkeypatch):
    monkeypatch.setattr(documents.socket,'getaddrinfo',lambda *_args,**_kwargs:[(None,None,None,None,('127.0.0.1',443))])
    with pytest.raises(ValueError,match='Private/local'):
        documents.public_address('https://localhost/secret')
    with pytest.raises(ValueError,match='without embedded credentials'):
        documents.public_address('https://user:password@example.com/paper')
