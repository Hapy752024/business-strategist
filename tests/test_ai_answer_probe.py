"""Input-derived regression expectations for the v2 recording contract.

Replaces v1 rotation/render-oracle tests that required destructive replacement or
accepted unknown comparisons. No expectation is calculated from a produced summary.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path
import pytest
from scripts.monitoring import ai_answer_probe as p

PANEL = {'schema_version': 2, 'panel_version': 'v1',
         'subject': {'name': 'Cedar', 'domains': ['cedar.example']},
         'prompts': [{'id': 'discover', 'version': 1, 'type': 'unbranded_discovery',
                      'text': 'Which garden service can I use?', 'source': 'synthetic fixture, not demand evidence'}],
         'targets': [{'engine': 'example', 'model': 'model-v1', 'search_config': 'search:on',
                      'surface': 'api', 'locale': 'en-GB', 'repetitions': 1}]}
BASE = {**{k: PANEL['targets'][0][k] for k in p.TARGET_FIELDS},
        'prompt_id': 'discover', 'prompt_version': 1, 'prompt_type': 'unbranded_discovery',
        'prompt_text': PANEL['prompts'][0]['text'], 'repetition': 1,
        'timestamp': '2026-09-21T10:00:00Z', 'target_brand': 'Cedar',
        'target_url': 'https://cedar.example', 'recording_source': 'synthetic:test',
        'annotation_method': 'synthetic fixture checked by test author',
        'status': 'success', 'brand_mentioned': False, 'recommended': False,
        'url_cited': False, 'citation_urls': [], 'answer_text': 'A recorded answer.'}


def old(**changes):
    return {**BASE, 'timestamp': '2026-09-20T10:00:00Z', **changes}


def summary(rows, prior=None, panel=None, prior_panel=None):
    return p.build_summary([p.normalize_observation(r) for r in rows],
                           [p.normalize_observation(r) for r in prior or []],
                           p.load_panel(panel or PANEL),
                           p.load_panel(prior_panel) if prior_panel else None, prior is not None)


def command(tmp_path, rows=None, panel=None, out=None, extra=()):
    inputs = tmp_path / 'inputs'
    inputs.mkdir(exist_ok=True)
    (inputs / 'panel.json').write_text(json.dumps(panel or PANEL))
    (inputs / 'rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in ([BASE] if rows is None else rows)))
    return [sys.executable, str(Path(p.__file__).resolve()), '--panel', str(inputs/'panel.json'),
            '--recorded', str(inputs/'rows.jsonl'), '--out', str(out or tmp_path/'run'), *extra]


def cli(tmp_path, **kwargs):
    result = subprocess.run(command(tmp_path, **kwargs), capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout)


def test_complete_baseline_retains_raw_and_annotations(tmp_path):
    row = {**BASE, 'url_cited': True, 'citation_urls': ['https://cedar.example/about'],
           'citation_annotations': [{'start': 0, 'end': 8}], 'provider_request_id': 'fixture-42'}
    rc, envelope = cli(tmp_path, rows=[row])
    loaded = p.load_run(tmp_path/'run')
    assert rc == 0 and envelope['completion'] == 'complete'
    assert loaded['summary']['status'] == 'baseline'
    assert not loaded['summary']['eligible_for_trend']
    assert loaded['rows'] == [row]
    assert json.loads((tmp_path/'run/raw.jsonl').read_text()) == row
    assert loaded['summary']['run_id'] == envelope['run_id']
    assert 'Measurement status: baseline' in (tmp_path/'run/report.md').read_text()


@pytest.mark.parametrize('kind', ['directory', 'file', 'symlink', 'dangling', 'dot', 'parent'])
def test_existing_output_is_never_touched(tmp_path, kind):
    protected = tmp_path/'protected'; protected.mkdir()
    sentinel = protected/'user.txt'; sentinel.write_bytes(b'important original bytes')
    out = tmp_path/'out'
    if kind == 'directory': out.mkdir(); (out/'existing.txt').write_text('keep')
    elif kind == 'file': out.write_text('keep')
    elif kind == 'symlink': out.symlink_to(protected, target_is_directory=True)
    elif kind == 'dangling': out.symlink_to(tmp_path/'absent')
    elif kind == 'dot': out = protected/'.'
    elif kind == 'parent': out = protected/'..'
    rc, result = cli(tmp_path, out=out)
    assert rc == 1 and result['status'] == 'fail'
    assert sentinel.read_bytes() == b'important original bytes'
    assert not (protected/'run.json').exists()
    if kind in ('symlink', 'dangling'): assert out.is_symlink()
    if kind == 'directory': assert (out/'existing.txt').read_text() == 'keep'
    if kind == 'file': assert out.read_text() == 'keep'


@pytest.mark.parametrize('error', [OSError('disk failure'), KeyboardInterrupt()])
@pytest.mark.parametrize('fail_at', ['raw.jsonl', 'summary.json', 'run.json'])
def test_interrupted_new_run_keeps_history_and_cannot_be_consumed(tmp_path, monkeypatch, capsys, error, fail_at):
    prior_dir = tmp_path/'prior'; prior_dir.mkdir(); (prior_dir/'original').write_bytes(b'old evidence')
    cmd = command(tmp_path)
    monkeypatch.setattr(sys, 'argv', cmd[1:])
    original = p._write
    def fail(path, value):
        if path.name == fail_at: raise error
        original(path, value)
    monkeypatch.setattr(p, '_write', fail)
    assert p.main() == 1
    assert json.loads(capsys.readouterr().out)['completion'] == 'incomplete'
    assert (prior_dir/'original').read_bytes() == b'old evidence'
    assert not (tmp_path/'run/run.json').exists()
    with pytest.raises((OSError, ValueError)): p.load_run(tmp_path/'run')


def test_same_destination_has_exactly_one_writer(tmp_path):
    cmd = command(tmp_path)
    jobs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
    results = [(job, job.communicate(timeout=20)) for job in jobs]
    assert sorted(job.returncode for job, _ in results) == [0, 1, 1, 1]
    winner = next(json.loads(streams[0]) for job, streams in results if job.returncode == 0)
    assert p.load_run(tmp_path/'run')['summary']['run_id'] == winner['run_id']


@pytest.mark.parametrize('artifact', p.ARTIFACTS)
def test_reader_rejects_changed_artifact(tmp_path, artifact):
    assert cli(tmp_path)[0] == 0
    file = tmp_path/'run'/artifact
    file.write_text(file.read_text()+' ')
    with pytest.raises(ValueError, match='changed/incomplete'): p.load_run(tmp_path/'run')


def test_prior_run_comparison_is_a_real_consumer(tmp_path):
    assert cli(tmp_path, rows=[old()], out=tmp_path/'baseline')[0] == 0
    rc, data = cli(tmp_path, rows=[{**BASE, 'brand_mentioned': True}],
                   extra=['--prior-run', str(tmp_path/'baseline')])
    assert rc == 0 and data['status'] == 'compared'
    trends = p.load_run(tmp_path/'run')['summary']['diff']['trends']
    mention = next(t for t in trends if t['field'] == 'brand_mentioned')
    assert (mention['prior_rate'], mention['current_rate'], mention['delta'], mention['prior_n'], mention['current_n']) == (0, 1, 1, 1, 1)
    assert all(k in mention for k in p.KEY)
    report = (tmp_path/'run/report.md').read_text()
    assert 'example / model-v1 / search:on / api / en-GB / discover / 1 / unbranded_discovery' in report


@pytest.mark.parametrize('change', [{'prompt_id': 'other'}, {'engine': 'other'}, {'surface': 'consumer'}, {'repetition': 2}])
def test_off_panel_rows_cannot_change_selected_trends(change):
    before = summary([BASE], [old()], prior_panel=PANEL)
    after = summary([{**BASE, **change, 'brand_mentioned': True}, BASE],
                    [old(**change), old()], prior_panel=PANEL)
    assert after['diff'] == before['diff']
    assert after['coverage'] == before['coverage']
    assert after['off_panel']['count'] == 1
    assert all(t['delta'] == 0 for t in after['diff']['trends'])


@pytest.mark.parametrize('prior', [[], [old()]])
def test_unknown_prior_context_has_no_trends(prior):
    result = summary([{**BASE, 'brand_mentioned': True}], prior)
    assert result['status'] == 'incomparable'
    assert result['diff']['reason'] == 'prior_panel_unknown'
    assert result['diff']['trends'] == []


@pytest.mark.parametrize('stamp', ['2026-09-21T10:00:00Z', '2026-09-22T10:00:00Z', '2026-09-21T12:00:00+02:00'])
def test_overlap_reversed_and_equivalent_instants_never_become_trends(stamp):
    result = summary([BASE], [old(timestamp=stamp)], prior_panel=PANEL)
    assert result['status'] == 'incomparable'
    assert result['diff']['reason'] == 'overlapping_or_reversed_windows'
    assert result['diff']['trends'] == []


def test_changed_prompt_under_same_version_is_not_comparable():
    panel = copy.deepcopy(PANEL); panel['prompts'][0]['text'] = 'A materially different question?'
    result = summary([{**BASE, 'prompt_text': panel['prompts'][0]['text']}], [old()], panel, PANEL)
    assert result['diff']['reason'] == 'panel_or_collection_context_changed'
    assert not result['eligible_for_trend']


@pytest.mark.parametrize('field,value', [('model', 'model-v2'), ('locale', 'de-DE'), ('search_config', 'off'), ('surface', 'consumer')])
def test_changed_target_context_is_not_comparable(field, value):
    panel = copy.deepcopy(PANEL); panel['targets'][0][field] = value
    result = summary([{**BASE, field: value}], [old()], panel, PANEL)
    assert result['status'] == 'incomparable' and result['diff']['trends'] == []


def test_no_pooling_across_surfaces_or_configurations():
    panel = copy.deepcopy(PANEL); panel['targets'][0]['repetitions'] = 2
    rows = [BASE, {**BASE, 'surface': 'consumer', 'repetition': 2}]
    result = summary(rows, panel=panel)
    assert result['status'] == 'partial'
    assert result['coverage']['successful_observations'] == 1
    assert result['coverage']['expected_observations'] == 2
    assert result['coverage_gaps'][0]['repetition'] == 2
    assert result['off_panel']['count'] == 1


def test_multiple_declared_targets_each_require_their_own_samples():
    panel = copy.deepcopy(PANEL); panel['targets'].append({**panel['targets'][0], 'surface': 'consumer'})
    result = summary([BASE], panel=panel)
    assert result['status'] == 'partial'
    assert result['coverage_gaps'][0]['surface'] == 'consumer'


@pytest.mark.parametrize('status', ['error', 'unsupported'])
def test_failure_is_unknown_and_keeps_reason(tmp_path, status):
    failure = {**BASE, 'status': status, 'brand_mentioned': None, 'url_cited': None,
               'recommended': None, 'error_detail': 'insufficient_credits; top-up required'}
    rc, result = cli(tmp_path, rows=[failure])
    assert rc == 2 and result['completion'] == 'complete' and result['status'] == 'unmeasured'
    assert result['coverage']['successful_observations'] == 0
    assert result['coverage_gaps'][0]['detail'] == failure['error_detail']
    assert p.load_run(tmp_path/'run')['rows'][0]['brand_mentioned'] is None
    assert 'insufficient_credits' in (tmp_path/'run/report.md').read_text()


def test_failed_prior_cannot_be_clean_baseline():
    failure = old(status='error', brand_mentioned=None, url_cited=None, recommended=None, error_detail='billing_required')
    result = summary([BASE], [failure], prior_panel=PANEL)
    assert result['status'] == 'incomparable'
    assert result['diff']['prior_coverage_gaps'][0]['reason'] == 'error'
    assert result['diff']['trends'] == []


def test_empty_input_writes_honest_unmeasured_artifacts(tmp_path):
    rc, result = cli(tmp_path, rows=[])
    assert rc == 2 and result['status'] == 'unmeasured'
    assert len(result['coverage_gaps']) == 1
    assert p.load_run(tmp_path/'run')['summary']['status'] == 'unmeasured'


def test_duplicates_rejected_before_output_allocation(tmp_path):
    rc, result = cli(tmp_path, rows=[BASE, BASE])
    assert rc == 1 and 'duplicate' in result['errors'][0]
    assert not (tmp_path/'run').exists()


def test_repetition_order_invariance():
    panel = copy.deepcopy(PANEL); panel['targets'][0]['repetitions'] = 2
    now = [BASE, {**BASE, 'repetition': 2, 'brand_mentioned': True}]
    prior = [old(), old(repetition=2, brand_mentioned=True)]
    a = summary(now, prior, panel, panel)
    b = summary(list(reversed(now)), list(reversed(prior)), panel, panel)
    assert a == b
    assert a['diff']['trends'][0]['current_n'] == 2
    assert all(t['delta'] == 0 for t in a['diff']['trends'])


@pytest.mark.parametrize('field', ['locale', 'timestamp', 'answer_text', 'recording_source', 'annotation_method', 'prompt_text', 'target_brand', 'target_url', 'citation_urls'])
def test_missing_context_is_rejected(field):
    row = dict(BASE); row.pop(field)
    with pytest.raises(ValueError): p.normalize_observation(row)


@pytest.mark.parametrize('changes', [{'repetition': True}, {'prompt_version': 0}, {'timestamp': '2026-09-21T10:00:00'}, {'brand_mentioned': 'yes'}, {'url_cited': True}, {'target_url': 'file:///etc/passwd'}])
def test_bad_context_is_rejected(changes):
    with pytest.raises(ValueError): p.normalize_observation({**BASE, **changes})


@pytest.mark.parametrize('changes', [{'prompt_text': 'wrong'}, {'target_brand': 'Someone else'}, {'target_url': 'https://other.example'}, {'url_cited': True, 'citation_urls': ['https://other.example']}])
def test_misbound_selected_observations_rejected(changes):
    with pytest.raises(ValueError): summary([{**BASE, **changes}])


def test_old_panel_format_gets_migration_instructions():
    with pytest.raises(ValueError, match='version 2'): p.load_panel({'prompts': PANEL['prompts']})


def test_panel_order_does_not_change_identity():
    panel = copy.deepcopy(PANEL)
    panel['targets'].append({**panel['targets'][0], 'locale': 'fr-FR'})
    original = p.load_panel(panel)['digest']
    panel['targets'].reverse(); panel['prompts'][0]['source'] = 'updated source note'
    assert p.load_panel(panel)['digest'] == original
