"""Responder import: per-variant funnel counts, unmapped reporting, identity stripping."""
import csv
import json
import subprocess
import sys
from pathlib import Path

from scripts.evidence_scout import import_responders as imp

ROOT = Path(__file__).resolve().parents[1]
PRESETS = imp.load_presets()


def rows():
    return [
        {'email': 'ana@example.org', 'name': 'Ana', 'variant': 'V1', 'channel': 'linkedin', 'stage': 'booked'},
        {'email': 'bo@example.org', 'name': 'Bo', 'variant': 'V1', 'channel': 'linkedin', 'stage': 'signed_up'},
        {'email': 'cy@example.org', 'name': 'Cy', 'variant': 'V2', 'channel': 'reddit', 'stage': 'interviewed'},
    ]


def test_import_counts_per_variant_channel():
    responders, counts, unmapped = imp.import_rows(rows(), PRESETS['generic_csv'], {'V1', 'V2'})
    assert unmapped == []
    assert counts['V1']['linkedin']['responded'] == 2 and counts['V1']['linkedin']['booked'] == 1
    assert counts['V2']['reddit']['attended'] == 1 and counts['V2']['reddit']['booked'] == 1
    assert counts['V2']['reddit']['usable_incident'] == 0
    assert len(responders) == 3


def test_import_reports_unmapped_rows():
    data = rows() + [{'email': 'x@example.org', 'variant': 'V9', 'channel': 'ads', 'stage': 'booked'},
                     {'email': 'y@example.org', 'variant': 'V1', 'channel': '', 'stage': 'booked'},
                     {'email': 'z@example.org', 'variant': 'V1', 'channel': 'ads', 'stage': 'mystery'}]
    responders, counts, unmapped = imp.import_rows(data, PRESETS['generic_csv'], {'V1', 'V2'})
    assert [u['reason'] for u in unmapped] == ['unknown variant V9', 'missing channel', 'unknown stage mystery']
    assert 'ads' not in counts.get('V1', {})
    assert len(responders) == 3


def test_import_strips_identity_fields():
    responders, _, _ = imp.import_rows(rows(), PRESETS['generic_csv'], {'V1', 'V2'})
    text = json.dumps(responders)
    assert 'example.org' not in text and 'Ana' not in text
    assert all(set(r) == {'id', 'variant', 'source', 'stage', 'segment_fit'} for r in responders)
    assert responders[0]['id'].startswith('R-') and responders[0]['id'] == imp.import_rows(rows(), PRESETS['generic_csv'], {'V1', 'V2'})[0][0]['id']


def test_presets_cover_named_sources():
    assert {'generic_csv', 'growthbook', 'posthog'} <= set(PRESETS)


def test_import_cli_writes_result_and_appends_responders(tmp_path):
    source = tmp_path / 'signups.csv'
    with source.open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['email', 'name', 'variant', 'channel', 'stage'])
        writer.writeheader(); writer.writerows(rows())
    ledger = tmp_path / 'responders.json'; ledger.write_text('[]\n')
    card = tmp_path / 'experiment-card.json'
    card.write_text(json.dumps({'variants': ['V1', 'V2'], 'responders_ref': {'path': str(ledger), 'digest': 'x' * 64}}))
    out = tmp_path / 'result.json'
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/import_responders.py'), '--card', str(card),
                           '--source', str(source), '--preset', 'generic_csv', '--out', str(out), '--responders', str(ledger)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    result = json.loads(out.read_text())
    assert result['interpretation'] is None and result['counts']['V1']['linkedin']['booked'] == 1
    assert len(json.loads(ledger.read_text())) == 3


def test_import_cli_fails_on_unmapped(tmp_path):
    source = tmp_path / 's.json'
    source.write_text(json.dumps([{'variant': 'V9', 'channel': 'ads', 'stage': 'booked'}]))
    card = tmp_path / 'card.json'; card.write_text(json.dumps({'variants': ['V1'], 'responders_ref': None}))
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/import_responders.py'), '--card', str(card),
                           '--source', str(source), '--preset', 'generic_csv', '--out', str(tmp_path / 'r.json')],
                          capture_output=True, text=True)
    assert done.returncode == 1 and 'unknown variant V9' in done.stderr


def test_posthog_nested_fields():
    data = [{'distinct_id': 'u1', 'event': 'booking_confirmed',
             'properties': {'$feature_flag_response': 'V1', 'utm_source': 'newsletter'}}]
    _, counts, unmapped = imp.import_rows(data, PRESETS['posthog'], {'V1'})
    assert unmapped == [] and counts['V1']['newsletter']['booked'] == 1


def test_flat_dotted_key_wins():
    assert imp._field({'a.b': 1, 'a': {'b': 2}}, 'a.b') == 1


def test_event_export_counts_each_person_once_at_furthest_stage():
    events = [{'distinct_id': 'u1', 'event': e, 'properties': {'$feature_flag_response': 'V1', 'utm_source': 'ads'}}
              for e in ('$pageview', 'cta_clicked', 'booking_confirmed')]
    responders, counts, unmapped = imp.import_rows(events, PRESETS['posthog'], {'V1'})
    assert unmapped == [] and len(responders) == 1 and responders[0]['stage'] == 'booked'
    assert counts['V1']['ads']['exposed'] == 1 and counts['V1']['ads']['booked'] == 1


def test_growthbook_control_variant_zero_is_counted():
    rows_ = [{'user_id': 'u1', 'variation_id': 0, 'utm_source': 'ads', 'event': 'signup'}]
    _, counts, unmapped = imp.import_rows(rows_, PRESETS['growthbook'], {'0'})
    assert unmapped == [] and counts['0']['ads']['responded'] == 1


def test_pseudonym_is_salted_and_segment_fit_whitelisted():
    data = [dict(rows()[0], segment_fit='Ana, CFO at Acme'), dict(rows()[1], segment_fit='fit')]
    a, _, _ = imp.import_rows(data, PRESETS['generic_csv'], {'V1', 'V2'}, salt='s1')
    b, _, _ = imp.import_rows(data, PRESETS['generic_csv'], {'V1', 'V2'}, salt='s2')
    import hashlib
    assert a[0]['id'] != b[0]['id'] and a[0]['id'] != 'R-' + hashlib.sha256(b'ana@example.org').hexdigest()[:12]
    assert [r['segment_fit'] for r in a] == ['unresolved', 'fit']


def test_import_cli_default_ledger_resolves_in_workspace(tmp_path):
    from scripts import case_workspace as c
    ws = tmp_path / 'ws'
    c.initialize(ws, 'W'); c.add_case(ws, 'a', 'A')
    kit_dir = ws / 'cases/a/market_research/smoke'; kit_dir.mkdir(parents=True)
    (kit_dir / 'responders.json').write_text('[]\n')
    card = kit_dir / 'experiment-card.json'
    card.write_text(json.dumps({'variants': ['V1', 'V2'],
                                'responders_ref': {'path': 'cases/a/market_research/smoke/responders.json', 'digest': 'x' * 64}}))
    source = tmp_path / 's.json'; source.write_text(json.dumps(rows()))
    done = subprocess.run([sys.executable, str(ROOT / 'scripts/evidence_scout/import_responders.py'), '--card', str(card),
                           '--source', str(source), '--preset', 'generic_csv', '--out', str(tmp_path / 'r.json')],
                          capture_output=True, text=True, cwd=str(ROOT))
    assert done.returncode == 0, done.stderr
    assert len(json.loads((kit_dir / 'responders.json').read_text())) == 3
    assert (kit_dir / 'responders.salt').is_file()
    assert not (ROOT / 'cases').exists()
