import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
from scripts.monitoring import ai_answer_probe
from scripts.monitoring.ai_answer_probe import (
    normalize_observation, diff_observations, build_summary, load_panel, main)

BASE = {
    'engine': 'openai', 'model': 'gpt-x', 'search_config': 'web_search:on',
    'locale': 'en-US', 'timestamp': '2026-09-20T10:00:00Z', 'surface': 'api',
    'prompt_type': 'unbranded_discovery',
    'prompt_id': 'p01', 'prompt_version': 1, 'repetition': 1,
    'status': 'success', 'brand_mentioned': True, 'url_cited': False,
    'recommended': False, 'answer_text': '...',
}


def obs(**kw):
    return normalize_observation({**BASE, **kw})


def test_success_observation_normalized():
    row = obs()
    assert row['status'] == 'success' and row['brand_mentioned'] is True


def test_failed_probe_is_unknown_not_absent():
    row = obs(status='error', brand_mentioned=None, url_cited=None, recommended=None, answer_text='')
    assert row['brand_mentioned'] is None
    with pytest.raises(ValueError, match='status'):
        obs(status='error', brand_mentioned=False)


def test_invalid_status_rejected():
    with pytest.raises(ValueError, match='status'):
        obs(status='ok')


def test_surface_labels_separated():
    assert obs(surface='consumer')['surface'] == 'consumer'
    with pytest.raises(ValueError, match='surface'):
        obs(surface='chatgpt')


def test_prompt_type_labels_separated():
    assert obs(prompt_type='decision_stage')['prompt_type'] == 'decision_stage'
    with pytest.raises(ValueError, match='prompt_type'):
        obs(prompt_type='branded')


def test_diff_compares_only_compatible_successful():
    prior = [obs(brand_mentioned=False), obs(prompt_id='p02', brand_mentioned=True)]
    current = [obs(brand_mentioned=True), obs(prompt_id='p02', status='error', brand_mentioned=None, url_cited=None, recommended=None, answer_text='')]
    result = diff_observations(current, prior)
    assert result['changes'] == [
        {'prompt_id': 'p01', 'engine': 'openai', 'repetition': 1, 'field': 'brand_mentioned',
         'from': False, 'to': True}
    ]
    p01 = [t for t in result['trends'] if t['prompt_id'] == 'p01' and t['field'] == 'brand_mentioned']
    assert len(p01) == 1 and p01[0]['prior_rate'] == 0.0 and p01[0]['current_rate'] == 1.0
    assert {t['prompt_id'] for t in result['trends']} == {'p01'}
    assert result['coverage']['compared'] == 1
    assert result['coverage']['skipped_failed'] == 1
    # The p02 prior observation has no compatible current counterpart (its current
    # sample failed), so it is one incompatible/unpaired observation on each side:
    # the count is symmetric over current and prior rows.
    assert result['coverage']['skipped_incompatible'] == 1


def test_diff_skips_incompatible_config():
    prior = [obs(model='gpt-old'), obs(prompt_id='p03', locale='de-DE')]
    current = [obs(), obs(prompt_id='p03')]
    result = diff_observations(current, prior)
    assert result['changes'] == []
    assert result['trends'] == []
    assert result['coverage']['compared'] == 0
    # Two configurations are incompatible on each side (p01 by model, p03 by
    # locale), so the symmetric count is 4, not the 2 an asymmetric count reports.
    assert result['coverage']['skipped_incompatible'] == 4


PANEL = {
    'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'},
        {'id': 'p02', 'version': 1, 'type': 'educational', 'text': 'How does this work?'},
    ],
}


def test_success_without_context_is_rejected():
    for missing in ('locale', 'timestamp', 'answer_text'):
        raw = {k: v for k, v in BASE.items() if k != missing}
        with pytest.raises(ValueError, match=missing):
            normalize_observation(raw)


def test_unparseable_timestamp_rejected():
    with pytest.raises(ValueError, match='timestamp'):
        obs(timestamp='last Tuesday')
    with pytest.raises(ValueError, match='timezone'):
        obs(timestamp='2026-09-20T10:00:00')


def test_panel_requires_id_version_type_text():
    with pytest.raises(ValueError, match='prompts'):
        load_panel({'prompts': []})
    with pytest.raises(ValueError, match='id'):
        load_panel({'prompts': [{'version': 1, 'type': 'educational', 'text': 'x'}]})
    with pytest.raises(ValueError, match='version'):
        load_panel({'prompts': [{'id': 'p01', 'type': 'educational', 'text': 'x'}]})
    with pytest.raises(ValueError, match='type'):
        load_panel({'prompts': [{'id': 'p01', 'version': 1, 'text': 'x'}]})
    with pytest.raises(ValueError, match='duplicate'):
        load_panel({'prompts': [dict(PANEL['prompts'][0]), dict(PANEL['prompts'][0])]})


def test_missing_panel_prompts_are_reported_as_unknown():
    summary = build_summary([obs(prompt_id='p01')], [], load_panel(PANEL))
    gaps = {(g['prompt_id'], g['reason']) for g in summary['coverage_gaps']}
    assert gaps == {('p02', 'missing_no_observation')}
    assert summary['unmeasured'] is False


def test_empty_recording_is_unmeasured_not_zero_gaps():
    summary = build_summary([], [], load_panel(PANEL))
    assert summary['unmeasured'] is True
    assert {g['prompt_id'] for g in summary['coverage_gaps']} == {'p01', 'p02'}


def test_off_panel_rows_are_separated_not_counted_as_coverage():
    summary = build_summary([obs(prompt_id='not_in_panel')], [], load_panel(PANEL))
    assert summary['off_panel'] == {'count': 1, 'prompt_ids': ['not_in_panel']}
    assert {g['prompt_id'] for g in summary['coverage_gaps']} == {'p01', 'p02'}
    assert summary['unmeasured'] is True


def test_declared_engines_and_repetitions_produce_coverage_gaps():
    panel = load_panel({**PANEL, 'engines': ['openai', 'perplexity'], 'repetitions': 2})
    summary = build_summary([obs(prompt_id='p01', engine='openai')], [], panel)
    gaps = {(g['prompt_id'], g.get('engine'), g['reason']) for g in summary['coverage_gaps']}
    assert ('p01', 'perplexity', 'missing_engine_observation') in gaps
    assert ('p01', 'openai', 'insufficient_repetitions') in gaps


def test_summary_reports_coverage_gap_for_failed_engine():
    rows = [obs(engine='perplexity', status='error', brand_mentioned=None,
                url_cited=None, recommended=None, answer_text='')]
    summary = build_summary(rows, [], load_panel({'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'}]}))
    assert summary['coverage_gaps'] == [
        {'prompt_id': 'p01', 'prompt_version': 1, 'prompt_type': 'unbranded_discovery',
         'engine': 'perplexity', 'reason': 'error'}]
    assert summary['boundary'] == (
        'observation of configured surfaces only; not customer-demand evidence; failures are unknown, not absence'
    )


def test_reordering_the_prior_file_does_not_change_the_result():
    prior = [obs(repetition=1, brand_mentioned=False), obs(repetition=2, brand_mentioned=True)]
    current = [dict(r, timestamp='2026-09-21T10:00:00Z') for r in prior]
    assert diff_observations(current, prior)['changes'] == []
    assert diff_observations(current, list(reversed(prior)))['changes'] == []


def test_identical_windows_report_no_movement_in_either_direction():
    prior = [obs(repetition=1, brand_mentioned=False), obs(repetition=2, brand_mentioned=True)]
    current = [dict(r, timestamp='2026-09-21T10:00:00Z') for r in prior]
    trends = diff_observations(current, prior)['trends']
    mention = [t for t in trends if t['field'] == 'brand_mentioned'][0]
    assert mention['prior_rate'] == mention['current_rate'] == 0.5
    assert mention['delta'] == 0
    assert mention['prior_n'] == mention['current_n'] == 2


def test_duplicate_repetition_in_one_window_is_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        diff_observations([obs(repetition=1), obs(repetition=1, brand_mentioned=False)], [])


def test_prompt_type_is_part_of_comparison_identity():
    result = diff_observations([obs(prompt_type='brand_seeded')], [obs(brand_mentioned=False)])
    assert result['changes'] == []
    assert result['trends'] == []
    assert result['coverage']['compared'] == 0
    # One current row and one prior row, each without a compatible counterpart.
    assert result['coverage']['skipped_incompatible'] == 2


PANEL_ONE = {'prompts': [{'id': 'p01', 'version': 1, 'type': 'unbranded_discovery',
                          'text': 'Which provider?'}]}


def _run_cli(monkeypatch, tmp_path, panel, recorded, prior=None, prior_panel=None):
    (tmp_path / 'panel.json').write_text(json.dumps(panel))
    (tmp_path / 'recorded.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in recorded))
    argv = ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
            '--recorded', str(tmp_path / 'recorded.jsonl'),
            '--out', str(tmp_path / 'out')]
    if prior is not None:
        (tmp_path / 'prior.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in prior))
        argv += ['--prior', str(tmp_path / 'prior.jsonl')]
    if prior_panel is not None:
        (tmp_path / 'prior_panel.json').write_text(json.dumps(prior_panel))
        argv += ['--prior-panel', str(tmp_path / 'prior_panel.json')]
    monkeypatch.setattr(sys, 'argv', argv)
    return main()


def test_coverage_counts_only_fully_covered_prompts():
    panel = load_panel({**PANEL_ONE, 'engines': ['openai', 'perplexity']})
    incomplete = build_summary([obs(prompt_id='p01', engine='openai')], [], panel)
    assert incomplete['coverage']['covered_prompts'] == 0
    complete = build_summary([obs(prompt_id='p01', engine='openai'),
                              obs(prompt_id='p01', engine='perplexity')], [], panel)
    assert complete['coverage']['covered_prompts'] == 1
    assert complete['coverage_gaps'] == []


def test_distinct_repetitions_satisfy_coverage_but_duplicates_do_not():
    panel = load_panel({**PANEL_ONE, 'engines': ['openai'], 'repetitions': 2})
    good = build_summary([obs(prompt_id='p01', repetition=1),
                          obs(prompt_id='p01', repetition=2, brand_mentioned=False)], [], panel)
    assert good['coverage']['covered_prompts'] == 1
    assert good['coverage_gaps'] == []
    # Contract correction (Round 3 finding 5, extended by Round 4 finding 5): rows
    # sharing a repetition index are not independent samples and no longer earn
    # coverage at all. Round 3 only rejected them at `main`'s load step, so the same
    # rows handed straight to `build_summary` were credited as a fully covered prompt
    # while the CLI path raised — the verdict depended on whether an unrelated
    # `--prior` window happened to be supplied. The rejection now lives in the
    # coverage path too, so a direct library call cannot grant credit to duplicates.
    with pytest.raises(ValueError, match='duplicate'):
        build_summary([obs(prompt_id='p01', repetition=1),
                       obs(prompt_id='p01', repetition=1, brand_mentioned=False)], [], panel)


def test_undeclared_engine_rows_are_off_panel_and_fail_closed():
    panel = load_panel({**PANEL_ONE, 'engines': ['openai']})
    summary = build_summary([obs(prompt_id='p01', engine='gemini')], [], panel)
    assert summary['off_panel'] == {'count': 1, 'prompt_ids': ['p01']}
    assert summary['coverage']['covered_prompts'] == 0
    assert summary['coverage']['successful_observations'] == 0
    assert summary['unmeasured'] is True
    assert [g['reason'] for g in summary['coverage_gaps']] == ['missing_no_observation']


def test_all_failed_on_panel_recording_is_unmeasured():
    panel = load_panel({**PANEL_ONE, 'engines': ['openai']})
    rows = [obs(prompt_id='p01', status='error', brand_mentioned=None,
                url_cited=None, recommended=None, answer_text='')]
    summary = build_summary(rows, [], panel)
    assert summary['unmeasured'] is True
    assert summary['coverage']['successful_observations'] == 0
    assert summary['coverage_gaps'] == [
        {'prompt_id': 'p01', 'prompt_version': 1, 'prompt_type': 'unbranded_discovery',
         'engine': 'openai', 'reason': 'error'}]


def test_unmeasured_run_exits_nonzero_and_says_so_in_report(monkeypatch, tmp_path):
    failed = {**BASE, 'status': 'error', 'brand_mentioned': None,
              'url_cited': None, 'recommended': None, 'answer_text': ''}
    assert _run_cli(monkeypatch, tmp_path, {**PANEL_ONE, 'engines': ['openai']}, [failed]) is True
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'Status: unmeasured' in report
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['unmeasured'] is True and summary['status'] == 'unmeasured'


def test_prior_only_observation_counts_as_incompatible():
    result = diff_observations([obs()], [obs(), obs(prompt_id='p02')])
    assert result['coverage']['compared'] == 1
    assert result['coverage']['skipped_incompatible'] == 1


def test_overlapping_windows_are_compared_as_instants_not_strings():
    prior = [obs(timestamp='2026-09-20T10:00:00Z', brand_mentioned=False)]
    current = [obs(timestamp='2026-09-20T05:00:00-05:00', brand_mentioned=True)]
    coverage = diff_observations(current, prior)['coverage']
    assert coverage['overlapping_windows'] is True
    apart = diff_observations([obs(timestamp='2026-09-21T10:00:00Z')], prior)['coverage']
    assert apart['overlapping_windows'] is False


def test_panel_engines_validation_rejects_malformed_declarations():
    for bad in ([], '', 'openai', [1], [None]):
        with pytest.raises(ValueError, match='engines'):
            load_panel({**PANEL_ONE, 'engines': bad})
    assert load_panel({**PANEL_ONE, 'engines': ['openai']})['engines'] == ['openai']
    assert load_panel(PANEL_ONE)['engines'] is None


def test_multi_key_comparison_is_input_order_independent():
    ids = ('p08', 'p01', 'p07', 'p02', 'p06', 'p03', 'p05', 'p04')
    prior = [obs(prompt_id=pid, brand_mentioned=False) for pid in ids]
    current = [dict(r, timestamp='2026-09-21T10:00:00Z', brand_mentioned=True)
               for r in reversed(prior)]
    forward = diff_observations(current, prior)
    backward = diff_observations(current, list(reversed(prior)))
    assert forward['trends'] == backward['trends']
    assert forward['changes'] == backward['changes']
    # Comparison output is ordered by comparison key, not by the file order the
    # rows arrived in and not by set-iteration (hash) order.
    trend_ids = [t['prompt_id'] for t in forward['trends']]
    assert len(trend_ids) == 24 and trend_ids == sorted(trend_ids)
    assert trend_ids[::3] == sorted(ids)
    change_ids = [c['prompt_id'] for c in forward['changes']]
    assert len(change_ids) == 8 and change_ids == sorted(ids)


def test_report_names_gaps_and_skipped_counts(monkeypatch, tmp_path):
    panel = {'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'},
        {'id': 'p02', 'version': 1, 'type': 'educational', 'text': 'How does this work?'}],
        'engines': ['openai', 'perplexity']}
    blocked = {**BASE, 'engine': 'perplexity', 'status': 'error', 'brand_mentioned': None,
               'url_cited': None, 'recommended': None, 'answer_text': ''}
    assert _run_cli(monkeypatch, tmp_path, panel, [BASE, blocked], prior=[BASE]) is False
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'Status: pass' in report
    assert 'Coverage: 0/2 declared prompts fully covered' in report
    # Contract correction (Round 3, nit 6): a gap row is identified by prompt id and
    # version, so a panel declaring the same id at two versions no longer renders two
    # identical lines.
    assert 'p01 v1/perplexity (error)' in report
    assert 'p02 v1 (missing_no_observation)' in report
    assert 'Compared: 1 probe targets' in report
    assert 'skipped incompatible: 0' in report
    assert 'skipped failed: 1' in report
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['status'] == 'pass'


def test_unwritable_out_returns_fail_envelope(monkeypatch, tmp_path, capsys):
    blocker = tmp_path / 'blocked'
    blocker.write_text('not a directory')
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
                                      '--recorded', str(tmp_path / 'recorded.jsonl'),
                                      '--out', str(blocker)])
    assert main() is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and envelope['errors']


# --- Round 3 (Task 6): the rendered artifact surface ------------------------

ERROR_BASE = {**BASE, 'status': 'error', 'brand_mentioned': None,
              'url_cited': None, 'recommended': None, 'answer_text': ''}


def err_obs(**kw):
    return obs(status='error', brand_mentioned=None, url_cited=None,
               recommended=None, answer_text='', **kw)


def test_diff_reports_prior_window_failures_separately():
    coverage = diff_observations([obs()], [err_obs()])['coverage']
    assert coverage['skipped_failed'] == 0
    assert coverage['skipped_failed_prior'] == 1
    assert coverage['prior_window'] is None


def test_credit_blocked_prior_window_is_not_rendered_as_a_clean_pass(monkeypatch, tmp_path):
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE], prior=[ERROR_BASE]) is False
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'skipped failed prior: 1' in report
    assert 'Warning: the prior window contained 1 failed observation' in report
    assert 'no successful prior observation established a prior collection window' in report
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['diff']['coverage']['skipped_failed_prior'] == 1
    assert summary['diff']['coverage']['skipped_failed'] == 0
    assert summary['diff']['coverage']['prior_window'] is None


def test_clean_prior_window_prints_no_prior_failure_warning(monkeypatch, tmp_path):
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z'}]
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE], prior=prior) is False
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'skipped failed prior: 0' in report
    assert 'Warning: the prior window contained' not in report


def test_panel_is_preserved_with_the_output_and_its_version_is_printed(monkeypatch, tmp_path):
    panel = {**PANEL_ONE, 'panel_version': '2026-09'}
    assert _run_cli(monkeypatch, tmp_path, panel, [BASE]) is False
    copied = (tmp_path / 'out' / 'panel.json').read_text()
    assert json.loads(copied) == panel
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'Panel version: 2026-09' in report


def test_changed_panel_version_is_recorded_and_not_compared(monkeypatch, tmp_path):
    prior_panel = {**PANEL_ONE, 'panel_version': 'v1'}
    current_panel = {**PANEL_ONE, 'panel_version': 'v2'}
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z', 'brand_mentioned': False}]
    # Contract correction (Round 4, nit 7): a measured run whose panel changed
    # between windows abandoned the comparison, so it must not report `pass` in the
    # machine-readable status. The exit code follows the status, so this now exits
    # non-zero as well, and report.md renders the same status the envelope carries.
    assert _run_cli(monkeypatch, tmp_path, current_panel, [BASE], prior=prior,
                    prior_panel=prior_panel) is True
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['status'] == 'incomparable'
    assert summary['unmeasured'] is False
    assert summary['diff']['coverage']['panel_version'] == {
        'current': 'v2', 'prior': 'v1', 'compatible': False}
    assert summary['diff']['changes'] == []
    assert summary['diff']['trends'] == []
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'Status: incomparable' in report
    assert 'panel version differs between windows (v1 -> v2)' in report
    assert '/brand_mentioned:' not in report


def test_same_panel_version_compares_normally(monkeypatch, tmp_path):
    panel = {**PANEL_ONE, 'panel_version': 'v1'}
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z', 'brand_mentioned': False}]
    assert _run_cli(monkeypatch, tmp_path, panel, [BASE], prior=prior,
                    prior_panel=panel) is False
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['diff']['coverage']['panel_version']['compatible'] is True
    assert summary['diff']['coverage']['compared'] == 1
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert '/brand_mentioned:' in report


def test_missing_prior_panel_version_is_recorded_as_unverified(monkeypatch, tmp_path):
    panel = {**PANEL_ONE, 'panel_version': 'v1'}
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z'}]
    assert _run_cli(monkeypatch, tmp_path, panel, [BASE], prior=prior) is False
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['diff']['coverage']['panel_version'] == {
        'current': 'v1', 'prior': None, 'compatible': None}
    # The rendered line names both sides and each unknown version, so a reader can
    # tell `compatible: null` from `compatible: true` and can tell which window was
    # the unversioned one.
    assert ('Panel-version comparability unverified (current: v1, prior: unversioned); '
            'an unversioned or unsupplied panel version cannot be shown to be '
            'comparable.') in (tmp_path / 'out' / 'report.md').read_text()


def test_failed_run_leaves_no_pass_claiming_summary(monkeypatch, tmp_path, capsys):
    # Round 4 (finding 1) changed the trigger. Round 3's version made `out/report.md`
    # a directory so the per-file write would fail after `summary.json` was already
    # live, which is the non-atomic publish this task removes. Directory rename has no
    # per-file step to fail, so the equivalent failure is injected at the rename that
    # moves the outgoing `out` aside — the run fails with the previous out untouched.
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'summary.json').write_text('{"status": "stale-prior-run"}')
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
                                      '--recorded', str(tmp_path / 'recorded.jsonl'),
                                      '--out', str(out)])
    _fail_rename_on_call(monkeypatch, 1, OSError('simulated rename failure'))
    assert main() is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and envelope['errors']
    # The failed run must not have published a pass claim, and must not have
    # overwritten the previous run's summary either.
    assert (out / 'summary.json').read_text() == '{"status": "stale-prior-run"}'
    assert sorted(p.name for p in out.iterdir()) == ['summary.json']
    assert list(tmp_path.glob('.out.*')) == []


def test_duplicate_repetitions_fail_closed_identically_with_and_without_prior(
        monkeypatch, tmp_path, capsys):
    dup = [BASE, {**BASE, 'brand_mentioned': False}]
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, dup) is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and 'duplicate' in envelope['errors'][0]
    assert not (tmp_path / 'out').exists()
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z'}]
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, dup, prior=prior) is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and 'duplicate' in envelope['errors'][0]
    assert not (tmp_path / 'out').exists()
    # The same validation applies to the prior file, so neither window can smuggle a
    # shared repetition index past the gate.
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE], prior=dup) is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and 'prior' in envelope['errors'][0]


def test_multi_row_mixed_offset_windows_use_instants_for_bounds_and_overlap():
    # Prior instants are 11:00Z and 12:00Z, written with different offsets. String
    # ordering inverts them, so both the bounds and the overlap verdict depend on
    # comparing instants.
    prior = [obs(repetition=1, timestamp='2026-09-20T11:00:00Z'),
             obs(repetition=2, timestamp='2026-09-20T07:00:00-05:00')]
    overlapping = [obs(repetition=1, timestamp='2026-09-20T06:30:00-05:00'),   # 11:30Z
                   obs(repetition=2, timestamp='2026-09-20T12:30:00Z')]        # 12:30Z
    apart = [obs(timestamp='2026-09-20T08:00:00-05:00')]                       # 13:00Z
    coverage = diff_observations(overlapping, prior)['coverage']
    assert coverage['prior_window'] == {'start': '2026-09-20T11:00:00Z',
                                        'end': '2026-09-20T07:00:00-05:00'}
    assert coverage['current_window'] == {'start': '2026-09-20T06:30:00-05:00',
                                          'end': '2026-09-20T12:30:00Z'}
    assert coverage['overlapping_windows'] is True
    assert diff_observations(apart, prior)['coverage']['overlapping_windows'] is False


def test_gap_rows_carry_prompt_version(monkeypatch, tmp_path):
    panel = {'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'},
        {'id': 'p01', 'version': 2, 'type': 'unbranded_discovery', 'text': 'Which provider now?'}]}
    assert _run_cli(monkeypatch, tmp_path, panel, []) is True
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert '- coverage gap: p01 v1 (missing_no_observation)' in report
    assert '- coverage gap: p01 v2 (missing_no_observation)' in report


def test_off_panel_line_is_unambiguous_when_the_id_is_also_declared(monkeypatch, tmp_path):
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE,
                    [BASE, {**BASE, 'prompt_version': 2}]) is False
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert 'Off-panel rows (excluded from coverage): 1 [p01]' in report
    assert 'matched on prompt id, version, type and declared engine' in report


def test_unmeasured_envelope_carries_out(monkeypatch, tmp_path, capsys):
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, []) is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'unmeasured'
    assert envelope['out'] == str(tmp_path / 'out')


# --- Round 3 (Task 7): the artifact-consistency layer ------------------------
#
# The probe renders one internal state four ways: `report.md`, `summary.json`,
# the stdout envelope and the exit code. Asserting the internal dict cannot
# catch a rendering that disagrees with it, so the tests below read the
# rendered artifacts back and cross-check them against each other and against
# the exit code. Every scenario picks inputs whose correct value is non-trivial
# and non-zero: an assertion such as `skipped incompatible: 0` on a run whose
# true value is 0 is satisfied by hard-coding `0`, which is how Round 1's
# lock-in pattern arose.
#
# The two formatters are reimplemented here rather than imported from the
# module under test: an oracle that calls the code it is checking cannot detect
# a change to that code.

TREND_FIELDS = ('brand_mentioned', 'url_cited', 'recommended')


def _rate(value):
    return 'n/a' if value is None else f'{value:.2f}'


def _version(value):
    return 'unversioned' if value is None else str(value)


def _line(report, label):
    """The single rendered `Label: value` line, or a failure naming the count."""
    prefix = label + ': '
    hits = [ln for ln in report.splitlines() if ln.startswith(prefix)]
    assert len(hits) == 1, f'expected exactly one {label!r} line, found {hits}'
    return hits[0][len(prefix):]


def _artifacts(monkeypatch, tmp_path, capsys, panel, recorded, prior=None, prior_panel=None):
    """Run the CLI and return (exit_code, stdout_envelope, report.md, summary.json, out)."""
    rc = _run_cli(monkeypatch, tmp_path, panel, recorded, prior=prior, prior_panel=prior_panel)
    envelope = json.loads(capsys.readouterr().out)
    out = tmp_path / 'out'
    return (rc, envelope, (out / 'report.md').read_text(),
            json.loads((out / 'summary.json').read_text()), out)


def _expected_gap_lines(summary):
    lines = []
    for gap in summary['coverage_gaps']:
        target = f"{gap['prompt_id']} v{gap['prompt_version']}"
        target += f"/{gap['engine']}" if gap.get('engine') else ''
        lines.append(f'- coverage gap: {target} ({gap["reason"]})')
    return lines


def _expected_off_panel_lines(summary):
    off = summary['off_panel']
    if not off['count']:
        return []
    return [f"Off-panel rows (excluded from coverage): {off['count']} "
            f"[{', '.join(off['prompt_ids'])}] "
            '(matched on prompt id, version, type and declared engine, so an id that is '
            'also declared in the panel appears here when its version, type or engine '
            'was not selected)']


def _expected_compared_line(summary):
    diff = summary['diff']
    if diff is None:
        return []
    coverage = diff['coverage']
    return [f"Compared: {coverage['compared']} probe targets; "
            f"response changes: {len(diff['changes'])}; "
            f"unpaired repetitions: {coverage['skipped_unpaired']}; "
            f"skipped incompatible: {coverage['skipped_incompatible']}; "
            f"skipped failed: {coverage['skipped_failed']}; "
            f"skipped failed prior: {coverage['skipped_failed_prior']}"]


def _expected_trend_lines(summary):
    diff = summary['diff']
    if diff is None:
        return []
    return [f"{t['prompt_id']}/{t['engine']}/{t['field']}: "
            f"{_rate(t['prior_rate'])} (n={t['prior_n']}) -> "
            f"{_rate(t['current_rate'])} (n={t['current_n']})"
            for t in diff['trends']]


def _expected_report_lines(summary):
    """The complete `report.md` body, reimplemented from the summary.

    Round 3's oracle compared filtered per-category subsets, so it could not see a
    line that was added, a line that was deleted, or a line emitted in the wrong
    category — only a wrong *value* inside a category it already looked at. This
    reconstructs the whole document instead, so the assertion below is over the exact
    line set and the exact line order.
    """
    coverage = summary['coverage']
    lines = ['# AI-answer observation report', '', f"Boundary: {summary['boundary']}", '',
             f"Status: {summary['status']}",
             f"Panel version: {_version(summary['panel_version'])}",
             f"Observations: {summary['observations']}; coverage gaps: {len(summary['coverage_gaps'])}",
             f"Coverage: {coverage['covered_prompts']}/{coverage['declared_prompts']} "
             'declared prompts fully covered']
    if summary['unmeasured']:
        lines.append('No successful observation: nothing was measured; failures are unknown, not absence.')
    lines.extend(_expected_gap_lines(summary))
    lines.extend(_expected_off_panel_lines(summary))
    diff = summary['diff']
    if diff is None:
        return lines
    cov = diff['coverage']
    lines.extend(_expected_compared_line(summary))
    if cov['skipped_failed_prior']:
        lines.append(f"Warning: the prior window contained {cov['skipped_failed_prior']} "
                     'failed observation(s); failures are unknown, not absence, so the '
                     'comparison is partial and the prior window is not a clean baseline.')
    if cov['prior'] == 0:
        lines.append('Warning: the prior window was supplied but contains no observations; '
                     'no movement is comparable.')
    elif cov['prior_window'] is None:
        lines.append('Warning: no successful prior observation established a prior collection '
                     'window; no movement is comparable.')
    versions = cov['panel_version']
    if versions['compatible'] is False:
        lines.append(f"Warning: panel version differs between windows "
                     f"({_version(versions['prior'])} -> {_version(versions['current'])}); "
                     'observations from different panel versions are not comparable, so no '
                     'movement is reported.')
    elif versions['compatible'] is None:
        lines.append('Panel-version comparability unverified '
                     f"(current: {_version(versions['current'])}, "
                     f"prior: {_version(versions['prior'])}); an unversioned or "
                     'unsupplied panel version cannot be shown to be comparable.')
    if cov['overlapping_windows']:
        lines.append('Warning: prior and current collection windows overlap; '
                     'treat movement as unestablished.')
    lines.extend(_expected_trend_lines(summary))
    return lines


def _assert_no_warnings(report):
    """No `Warning:`/qualifier line may render in a scenario that does not warrant one.

    The per-category oracle only ever asserted a warning's *presence*; a mutation
    that emits a warning unconditionally adds a line nothing was looking for.
    """
    assert [ln for ln in report.splitlines() if ln.startswith('Warning:')] == []
    assert 'Panel-version comparability unverified' not in report


def _assert_renderings_agree(rc, envelope, report, summary, out):
    """The four renderings of one run must not disagree with each other."""
    # stdout envelope <-> summary.json <-> exit code
    assert envelope['out'] == str(out)
    assert {k: v for k, v in envelope.items() if k != 'out'} == summary
    assert envelope['status'] == summary['status']
    assert rc == (summary['status'] != 'pass')
    # report.md is the expected document exactly: same lines, same order, no extras.
    assert report.splitlines() == _expected_report_lines(summary)
    # report.md <-> summary.json, line by line
    assert _line(report, 'Status') == summary['status']
    assert _line(report, 'Panel version') == _version(summary['panel_version'])
    assert _line(report, 'Observations') == (
        f"{summary['observations']}; coverage gaps: {len(summary['coverage_gaps'])}")
    coverage = summary['coverage']
    assert _line(report, 'Coverage') == (
        f"{coverage['covered_prompts']}/{coverage['declared_prompts']} "
        'declared prompts fully covered')
    assert [ln for ln in report.splitlines() if ln.startswith('- coverage gap: ')] == \
        _expected_gap_lines(summary)
    assert [ln for ln in report.splitlines() if ln.startswith('Off-panel rows ')] == \
        _expected_off_panel_lines(summary)
    assert [ln for ln in report.splitlines() if ln.startswith('Compared: ')] == \
        _expected_compared_line(summary)
    assert [ln for ln in report.splitlines() if '(n=' in ln] == _expected_trend_lines(summary)


RICH_PANEL = {
    'panel_version': '2026-09',
    'engines': ['openai', 'perplexity'],
    # Declared out of sorted order, so a report that falls back to panel order is
    # distinguishable from one that renders the declared sorted order.
    'prompts': [
        {'id': 'pC', 'version': 1, 'type': 'decision_stage', 'text': 'C'},
        {'id': 'pA', 'version': 1, 'type': 'unbranded_discovery', 'text': 'A'},
        {'id': 'pB', 'version': 1, 'type': 'educational', 'text': 'B'},
    ],
}


def test_rich_run_renders_one_state_across_all_four_artifacts(monkeypatch, tmp_path, capsys):
    recorded = [
        err_obs(prompt_id='pC', prompt_type='decision_stage', engine='perplexity'),
        obs(prompt_id='pA', engine='openai', brand_mentioned=True),
        obs(prompt_id='pA', engine='perplexity', brand_mentioned=False),
        obs(prompt_id='pB', prompt_type='educational', engine='openai', brand_mentioned=True),
        # Off-panel rows: two ids, one repeated, plus a declared id whose prompt_type
        # was not selected. The count (4) differs from the deduped count (3) and from
        # the truncated list (1), and the ids are not already in sorted order.
        obs(prompt_id='z9', repetition=1),
        obs(prompt_id='m4', repetition=1),
        obs(prompt_id='z9', repetition=2, brand_mentioned=False),
        obs(prompt_id='pA', prompt_type='brand_seeded'),
    ]
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, RICH_PANEL, recorded)
    _assert_renderings_agree(rc, envelope, report, summary, out)
    assert rc is False and envelope['status'] == 'pass'
    # The module's evidence-discipline statement is the report's own statement of what
    # an observation is not; deleting the line leaves nothing else asserting it.
    assert _line(report, 'Boundary') == summary['boundary'] == (
        'observation of configured surfaces only; not customer-demand evidence; '
        'failures are unknown, not absence')
    # A run with no prior window must render no comparison warning of any kind.
    _assert_no_warnings(report)
    # Rendered coverage, spelled out rather than cross-checked: 8 rows, 3 gaps and
    # 1 of 3 prompts fully covered are all values a hard-coded rendering cannot fake.
    assert _line(report, 'Observations') == '8; coverage gaps: 3'
    assert _line(report, 'Coverage') == '1/3 declared prompts fully covered'
    # Gap rows are rendered in sorted (prompt_id, engine) order, which is neither the
    # panel's declaration order (pC, pA, pB) nor the order the gaps were detected in.
    assert [ln for ln in report.splitlines() if ln.startswith('- coverage gap: ')] == [
        '- coverage gap: pB v1/perplexity (missing_engine_observation)',
        '- coverage gap: pC v1/openai (missing_engine_observation)',
        '- coverage gap: pC v1/perplexity (error)',
    ]
    # The off-panel line is the only user-visible trace of the excluded rows: the
    # count is the row count, the ids are sorted and deduped, and a declared id is
    # listed when its version, type or engine was not selected.
    assert 'Off-panel rows (excluded from coverage): 4 [m4, pA, z9]' in report
    # A measured run must not claim nothing was measured.
    assert not any(ln.startswith('No successful observation') for ln in report.splitlines())
    # The same values, read back from summary.json, must be what report.md rendered.
    assert summary['coverage'] == {'declared_prompts': 3, 'covered_prompts': 1,
                                   'successful_observations': 3}
    assert [g['prompt_id'] for g in summary['coverage_gaps']] == ['pB', 'pC', 'pC']
    assert summary['off_panel'] == {'count': 4, 'prompt_ids': ['m4', 'pA', 'z9']}


DIFF_PANEL = {'panel_version': 'v1',
              'prompts': [{'id': 'pA', 'version': 1, 'type': 'unbranded_discovery',
                           'text': 'Which provider?'}]}


def test_diff_run_renders_compared_counts_overlap_and_trends(monkeypatch, tmp_path, capsys):
    prior = [
        {**BASE, 'prompt_id': 'pA', 'timestamp': '2026-09-19T10:00:00Z', 'repetition': 1,
         'brand_mentioned': False},
        {**BASE, 'prompt_id': 'pA', 'timestamp': '2026-09-19T11:00:00Z', 'repetition': 2,
         'brand_mentioned': False},
        {**BASE, 'prompt_id': 'pD', 'timestamp': '2026-09-19T12:00:00Z', 'brand_mentioned': False},
    ]
    current = [
        # Inside the prior window (10:00Z-12:00Z), so the overlap warning must render.
        {**BASE, 'prompt_id': 'pA', 'timestamp': '2026-09-19T10:30:00Z', 'brand_mentioned': True},
        {**BASE, 'prompt_id': 'pE', 'timestamp': '2026-09-19T10:30:00Z', 'brand_mentioned': False},
    ]
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, DIFF_PANEL, current, prior=prior, prior_panel=DIFF_PANEL)
    _assert_renderings_agree(rc, envelope, report, summary, out)
    coverage = summary['diff']['coverage']
    # Every count on the rendered line is non-zero and distinct, so a hard-coded
    # rendering cannot satisfy it by accident.
    assert coverage['compared'] == 1
    assert coverage['skipped_unpaired'] == 1
    assert coverage['skipped_incompatible'] == 2
    assert coverage['overlapping_windows'] is True
    assert _line(report, 'Compared') == (
        '1 probe targets; response changes: 1; unpaired repetitions: 1; '
        'skipped incompatible: 2; skipped failed: 0; skipped failed prior: 0')
    assert ('Warning: prior and current collection windows overlap; '
            'treat movement as unestablished.') in report.splitlines()
    assert [ln for ln in report.splitlines() if '(n=' in ln] == [
        'pA/openai/brand_mentioned: 0.00 (n=2) -> 1.00 (n=1)',
        'pA/openai/url_cited: 0.00 (n=2) -> 0.00 (n=1)',
        'pA/openai/recommended: 0.00 (n=2) -> 0.00 (n=1)',
    ]


def test_unmeasured_run_renders_unknown_not_absence(monkeypatch, tmp_path, capsys):
    failed = {**BASE, 'status': 'error', 'brand_mentioned': None,
              'url_cited': None, 'recommended': None, 'answer_text': ''}
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, {**PANEL_ONE, 'engines': ['openai']}, [failed])
    _assert_renderings_agree(rc, envelope, report, summary, out)
    assert rc is True and envelope['status'] == 'unmeasured'
    # The sentence that says nothing was measured is the whole user-visible point of
    # an unmeasured run; the status line alone does not carry it.
    assert ('No successful observation: nothing was measured; failures are unknown, not absence.'
            in report.splitlines())
    assert '- coverage gap: p01 v1/openai (error)' in report.splitlines()


def test_panel_repetitions_are_validated_at_load():
    for bad in (0, -1, 2.0, '2', True):
        with pytest.raises(ValueError, match='repetitions'):
            load_panel({**PANEL_ONE, 'repetitions': bad})
    assert load_panel({**PANEL_ONE, 'repetitions': 1})['repetitions'] == 1
    assert load_panel(PANEL_ONE)['repetitions'] is None


def test_panel_repetitions_zero_fails_the_run_before_any_artifact(monkeypatch, tmp_path, capsys):
    # Rendered consequence: a panel declaring zero repetitions would make every prompt
    # vacuously covered, so it must fail the run and leave no artifact behind.
    assert _run_cli(monkeypatch, tmp_path, {**PANEL_ONE, 'repetitions': 0}, [BASE]) is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and 'repetitions' in envelope['errors'][0]
    assert not (tmp_path / 'out').exists()


# --- Round 4 (Task 9): the publish path and the report's remaining blind spots -
#
# Round 3 published by writing each artifact over its live counterpart in order,
# with `staging.rmdir()` as the last statement inside the `try`. Anything failing
# after that loop left all four artifacts live beside a non-zero exit. The publish
# is now a directory rename, so the failure injection point is the rename itself:
# `_rename` is a one-line module-level seam, and these tests drive it to fault at
# a chosen one of the two renames. That is what makes the crash window testable
# rather than asserted in a comment.


def _fail_rename_on_call(monkeypatch, call, exc):
    """Make the `call`-th `_rename` raise `exc`, letting earlier ones work."""
    real = ai_answer_probe._rename
    seen = []

    def fake(src, dst):
        seen.append((src, dst))
        if len(seen) == call:
            raise exc
        return real(src, dst)

    monkeypatch.setattr(ai_answer_probe, '_rename', fake)


def _out_setup(monkeypatch, tmp_path):
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
                                      '--recorded', str(tmp_path / 'recorded.jsonl'),
                                      '--out', str(tmp_path / 'out')])


def _no_pass_claiming_out(out):
    """`out/summary.json` must be absent or must not claim a pass."""
    summary = out / 'summary.json'
    assert not summary.exists() or json.loads(summary.read_text())['status'] != 'pass'


def test_interrupt_mid_publish_leaves_no_out_and_no_pass_claim(monkeypatch, tmp_path, capsys):
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'summary.json').write_text('{"status": "pass"}')   # a previous run's claim
    _out_setup(monkeypatch, tmp_path)
    # The second rename is the crash window: the outgoing `out` has been moved
    # aside and the staged tree has not yet taken its place.
    _fail_rename_on_call(monkeypatch, 2, KeyboardInterrupt())
    rc = main()                     # `raise SystemExit(main())` exits 1 here
    envelope = json.loads(capsys.readouterr().out)
    assert rc is True, 'an interrupted publish must exit non-zero'
    assert envelope['status'] == 'fail' and envelope['errors']
    _no_pass_claiming_out(out)
    # The chosen trade-off: no `out` at all reads as "the run did not complete",
    # where a mixed-epoch `out` would carry the previous run's pass claim beside
    # fresh evidence from the interrupted one.
    assert not out.exists()
    assert list(tmp_path.glob('.out.*')) == []


def test_exception_mid_publish_leaves_no_out_and_no_pass_claim(monkeypatch, tmp_path, capsys):
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'summary.json').write_text('{"status": "pass"}')
    _out_setup(monkeypatch, tmp_path)
    _fail_rename_on_call(monkeypatch, 2, OSError('simulated publish failure'))
    rc = main()
    envelope = json.loads(capsys.readouterr().out)
    assert rc is True, 'a failed publish must exit non-zero'
    assert envelope['status'] == 'fail' and envelope['errors']
    _no_pass_claiming_out(out)
    assert not out.exists()
    assert list(tmp_path.glob('.out.*')) == []


def test_successful_run_leaves_no_staging_or_outgoing_directory(monkeypatch, tmp_path, capsys):
    rc, envelope, report, summary, out = _artifacts(monkeypatch, tmp_path, capsys, PANEL_ONE, [BASE])
    assert rc is False and envelope['status'] == 'pass'
    assert sorted(p.name for p in out.iterdir()) == [
        'evidence.jsonl', 'panel.json', 'report.md', 'summary.json']
    assert list(tmp_path.glob('.out.*')) == []


def test_concurrent_runs_sharing_out_never_publish_a_mixed_tree(tmp_path):
    # The staging directory is named with the process id, so two runs sharing `--out`
    # can no longer write into the same staging directory. The published tree is
    # always one run's complete output, and a run that fails to publish says so in
    # its envelope instead of leaving a pass claim behind.
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'monitoring' / 'ai_answer_probe.py'
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    out = tmp_path / 'out'
    argv = [sys.executable, str(script), '--panel', str(tmp_path / 'panel.json'),
            '--recorded', str(tmp_path / 'recorded.jsonl'), '--out', str(out)]
    procs = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) for _ in range(6)]
    results = [(p.wait(), p.stdout.read(), p.stderr.read()) for p in procs]
    assert any(rc == 0 for rc, _, _ in results), results
    for rc, stdout, stderr in results:
        if rc != 0:
            assert json.loads(stdout)['status'] == 'fail', (rc, stdout, stderr)
    assert sorted(p.name for p in out.iterdir()) == [
        'evidence.jsonl', 'panel.json', 'report.md', 'summary.json']
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['status'] == 'pass'
    evidence = [json.loads(ln) for ln in (out / 'evidence.jsonl').read_text().splitlines()]
    assert len(evidence) == summary['observations']
    assert list(tmp_path.glob('.out.*')) == []


def test_out_dot_publishes_into_the_resolved_directory(monkeypatch, tmp_path, capsys):
    root = tmp_path / 'root'
    root.mkdir()
    (root / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (root / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    cwd = root / 'here'
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(root / 'panel.json'),
                                      '--recorded', str(root / 'recorded.jsonl'), '--out', '.'])
    assert main() is False
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'pass'
    assert envelope['out'] == str(cwd.resolve())
    assert sorted(p.name for p in cwd.iterdir()) == [
        'evidence.jsonl', 'panel.json', 'report.md', 'summary.json']


def test_out_filesystem_root_fails_naming_the_out_flag(monkeypatch, tmp_path, capsys):
    # A resolved path with no name has no staging name to derive; the failure must
    # name the flag the user can fix rather than the internal `PosixPath` type.
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
                                      '--recorded', str(tmp_path / 'recorded.jsonl'),
                                      '--out', str(Path('/').resolve())])
    assert main() is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail'
    assert '--out' in envelope['errors'][0]


def test_unversioned_current_panel_renders_comparability_as_unverified(monkeypatch, tmp_path):
    # Round 4, finding 3: the unverified branch tested `prior is None`, so an
    # unversioned *current* panel against a versioned prior compared away and printed
    # no comparability line at all — a reader could not tell `null` from `true`.
    prior_panel = {**PANEL_ONE, 'panel_version': 'v1'}
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z'}]
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE], prior=prior,
                    prior_panel=prior_panel) is False
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['diff']['coverage']['panel_version'] == {
        'current': None, 'prior': 'v1', 'compatible': None}
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert ('Panel-version comparability unverified (current: unversioned, prior: v1); '
            'an unversioned or unsupplied panel version cannot be shown to be '
            'comparable.') in report
    assert 'panel version differs' not in report


def test_empty_prior_file_is_unknown_not_absence(monkeypatch, tmp_path):
    # Round 4, finding 4: `if prior_rows else None` made a supplied-but-empty
    # `--prior` byte-identical to omitting it. The probe's own zero-row run writes an
    # empty evidence.jsonl, so this is a natural artifact, and the two states must not
    # render the same.
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE], prior=[]) is False
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['diff'] is not None
    assert summary['diff']['coverage']['prior'] == 0
    assert summary['diff']['coverage']['prior_window'] is None
    report = (tmp_path / 'out' / 'report.md').read_text()
    assert ('Warning: the prior window was supplied but contains no observations; '
            'no movement is comparable.') in report.splitlines()
    # Omitting the flag is a different state: no comparison at all.
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE]) is False
    omitted = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert omitted['diff'] is None
    assert 'prior window was supplied' not in (tmp_path / 'out' / 'report.md').read_text()


def test_panel_version_must_be_a_nonempty_string_when_present():
    for bad in (1, 1.0, True, '', [], {}):
        with pytest.raises(ValueError, match='panel_version'):
            load_panel({**PANEL_ONE, 'panel_version': bad})
    assert load_panel({**PANEL_ONE, 'panel_version': 'v1'})['panel_version'] == 'v1'
    assert load_panel(PANEL_ONE)['panel_version'] is None


def test_panel_version_comparison_is_like_for_like():
    # Round 4, nit 6: `1` vs `'1'` rendered "panel version differs (1 -> 1)". A
    # non-string version cannot be compared with a string one, so the pair is
    # unknown rather than reported as a change that did not happen.
    versions = diff_observations([obs()], [obs(brand_mentioned=False)],
                                 {'current': '1', 'prior': 1})['coverage']['panel_version']
    assert versions == {'current': '1', 'prior': 1, 'compatible': None}


def test_panel_copy_is_read_once_and_matches_the_measured_panel(monkeypatch, tmp_path, capsys):
    # Round 4, nit 8: the panel was read twice, so a change between the two reads
    # would publish a panel.json that was not the one measured. Counting reads of the
    # panel path is the direct assertion that the copy comes from the parsed object.
    real_read_text = Path.read_text
    reads = []

    def counting(self, *args, **kwargs):
        reads.append(self)
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', counting)
    rc, envelope, report, summary, out = _artifacts(monkeypatch, tmp_path, capsys, PANEL_ONE, [BASE])
    assert rc is False
    assert reads.count(tmp_path / 'panel.json') == 1
    assert json.loads((out / 'panel.json').read_text()) == PANEL_ONE


# --- Round 4 (Task 10): the oracle's remaining blind spots ------------------
#
# Round 3's oracle compared *filtered per-category* line lists. That shape has no
# "no unexpected lines" assertion, never asserts a warning's absence, and cannot see
# cross-category order, so eight mutations survived it: the panel's version/type
# dimensions, the off-panel id order (which the old assertions only caught under
# most hash seeds, by luck), the `Boundary:` line, an added line, an unconditional
# warning, and a reorder across categories. `_assert_renderings_agree` now compares
# the whole document, which is the general fix; the tests below add the inputs whose
# correct answer is non-trivial, so the general fix has something to bite on.


def test_panel_declaring_two_versions_credits_only_the_measured_version(
        monkeypatch, tmp_path, capsys):
    # A panel may declare `p01` at two versions. Crediting the v1 observation to the
    # v2 declaration reports 2/2 covered where the correct answer is 1/2, and the
    # `mine` filter is the only place the version dimension is applied.
    panel = {'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'},
        {'id': 'p01', 'version': 2, 'type': 'unbranded_discovery', 'text': 'Which provider now?'}]}
    rc, envelope, report, summary, out = _artifacts(monkeypatch, tmp_path, capsys, panel, [BASE])
    _assert_renderings_agree(rc, envelope, report, summary, out)
    assert rc is False and envelope['status'] == 'pass'
    assert summary['coverage'] == {'declared_prompts': 2, 'covered_prompts': 1,
                                   'successful_observations': 1}
    assert _line(report, 'Coverage') == '1/2 declared prompts fully covered'
    assert [ln for ln in report.splitlines() if ln.startswith('- coverage gap: ')] == [
        '- coverage gap: p01 v2 (missing_no_observation)']


def test_coverage_credits_only_rows_of_the_declared_prompt_type():
    # The type dimension of prompt identity. `load_panel` refuses two prompts sharing
    # (id, version) — `duplicate panel prompt id/version` — so this panel cannot be
    # expressed through the CLI and the mutation is not CLI-reachable; `_panel_coverage`
    # is reachable as a library call, and the report's own off-panel line documents that
    # type is part of prompt identity. Crediting an `unbranded_discovery` row to an
    # `educational` declaration reports 2/2 where the correct answer is 1/2.
    panel = load_panel({'prompts': [
        {'id': 'p01', 'version': 1, 'type': 'unbranded_discovery', 'text': 'Which provider?'}]})
    panel['declared'].append({'prompt_id': 'p01', 'prompt_version': 1,
                              'prompt_type': 'educational'})
    summary = build_summary([obs(prompt_id='p01')], [], panel)
    assert summary['coverage'] == {'declared_prompts': 2, 'covered_prompts': 1,
                                   'successful_observations': 1}
    assert summary['coverage_gaps'] == [
        {'prompt_id': 'p01', 'prompt_version': 1, 'prompt_type': 'educational',
         'reason': 'missing_no_observation'}]


def test_off_panel_ids_render_sorted_regardless_of_hash_order(monkeypatch, tmp_path, capsys):
    # Six off-panel ids whose set-iteration order differs from sorted order under every
    # hash seed 0-20 tested, including PYTHONHASHSEED=2 — where a `list(set(...))`
    # mutant renders `pA, k1, z9, m4, q3, b7`. Round 3's assertion was a membership
    # check on a three-id line, so the mutant survived whenever the hash order happened
    # to coincide with sorted order. This asserts the exact rendered order, and the
    # order of the summary's own list, so the kill does not depend on the seed.
    ids = ['z9', 'm4', 'pA', 'k1', 'b7', 'q3']
    recorded = [BASE] + [obs(prompt_id=pid) for pid in ids]
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, PANEL_ONE, recorded)
    _assert_renderings_agree(rc, envelope, report, summary, out)
    assert summary['off_panel'] == {'count': 6, 'prompt_ids': sorted(ids)}
    assert summary['off_panel']['prompt_ids'] == sorted(summary['off_panel']['prompt_ids'])
    assert [ln for ln in report.splitlines() if ln.startswith('Off-panel rows')] == [
        'Off-panel rows (excluded from coverage): 6 [b7, k1, m4, pA, q3, z9] '
        '(matched on prompt id, version, type and declared engine, so an id that is '
        'also declared in the panel appears here when its version, type or engine '
        'was not selected)']


def test_clean_diff_run_renders_exactly_the_expected_lines(monkeypatch, tmp_path, capsys):
    # A comparable, non-overlapping prior window: every warning branch is false, so the
    # report must contain no warning line at all. An unconditional overlap or
    # comparability warning is invisible to the per-category oracle in the overlapping
    # scenario (where the warning is expected anyway) and only shows up here.
    prior = [{**BASE, 'prompt_id': 'pA', 'timestamp': '2026-09-19T10:00:00Z',
              'brand_mentioned': False}]
    current = [{**BASE, 'prompt_id': 'pA', 'timestamp': '2026-09-20T10:00:00Z',
                'brand_mentioned': True}]
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, DIFF_PANEL, current, prior=prior, prior_panel=DIFF_PANEL)
    _assert_renderings_agree(rc, envelope, report, summary, out)
    assert rc is False and envelope['status'] == 'pass'
    coverage = summary['diff']['coverage']
    assert coverage['compared'] == 1 and coverage['overlapping_windows'] is False
    assert coverage['panel_version']['compatible'] is True
    _assert_no_warnings(report)
    assert _line(report, 'Compared') == (
        '1 probe targets; response changes: 1; unpaired repetitions: 0; '
        'skipped incompatible: 0; skipped failed: 0; skipped failed prior: 0')
    # The comparison line precedes the trend lines: a pure cross-category reorder keeps
    # every within-category list intact, so only the full-document comparison sees it.
    body = report.splitlines()
    assert next(i for i, ln in enumerate(body) if ln.startswith('Compared: ')) < \
        min(i for i, ln in enumerate(body) if '(n=' in ln)


def test_prior_duplicate_rejection_leaves_no_out_and_no_staging_residue(
        monkeypatch, tmp_path, capsys):
    # A shared repetition index in the prior window fails the run closed before any
    # artifact is published: no `out`, and no staging or set-aside directory left in
    # its parent. The check also runs at load time in `main`, so it cannot be reached
    # only after `build_summary` has already done work.
    dup = [BASE, {**BASE, 'brand_mentioned': False}]
    assert _run_cli(monkeypatch, tmp_path, PANEL_ONE, [BASE], prior=dup) is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and 'prior' in envelope['errors'][0]
    assert not (tmp_path / 'out').exists()
    assert list(tmp_path.glob('.out.*')) == []


# --- Round 5 (Task 11): the cleanup path ------------------------------------
#
# Round 4's publish was atomic but its *cleanup* was not safe. Staging and outgoing
# paths were hand-rolled as `.<out-name>.<role>.<pid>` in `out.parent` and the
# `finally` discarded **both unconditionally**, whether or not this run created them.
# A run could therefore delete a directory it never created — and, worse, do so while
# reporting `status: pass`. The two data-loss tests below are the reason this section
# exists; both were verified in-process with the pid pinned, because the derived name
# is pid-dependent and the collision is only reachable when the pids coincide.
#
# The fix removes the possibility rather than defending the name: `tempfile.mkdtemp`
# reserves the staging name with an exclusive create, so no user path and no
# concurrent run can already be sitting at it, and `finally` now discards only the
# paths this run actually created.


def _pid_pinned_derived_names():
    """The sibling names Round 4 derived from `out` and the current pid."""
    pid = os.getpid()
    return [f'.out.staging.{pid}', f'.out.outgoing.{pid}']


@pytest.mark.parametrize('derived', _pid_pinned_derived_names())
def test_preexisting_directory_at_a_derived_sibling_name_is_never_discarded(
        monkeypatch, tmp_path, capsys, derived):
    # F-A, reproduced before the fix: a real directory pre-existing at
    # `.out.outgoing.<pid>` with `out` absent was **destroyed** by a run that never
    # created it, and the run returned `status: pass`. The probe itself creates these
    # names on a crash, so pid reuse after a crash is a live route to the same
    # collision. A run must never discard a path it did not create.
    occupant = tmp_path / derived
    occupant.mkdir()
    (occupant / 'user-data.txt').write_text('precious user data')
    (occupant / 'nested').mkdir()
    (occupant / 'nested' / 'deep.txt').write_text('deeper user data')
    _out_setup(monkeypatch, tmp_path)
    rc = main()
    envelope = json.loads(capsys.readouterr().out)
    assert rc is False, envelope
    assert envelope['status'] == 'pass'
    assert sorted(p.name for p in (tmp_path / 'out').iterdir()) == [
        'evidence.jsonl', 'panel.json', 'report.md', 'summary.json']
    assert (occupant / 'user-data.txt').read_text() == 'precious user data'
    assert (occupant / 'nested' / 'deep.txt').read_text() == 'deeper user data'


@pytest.mark.parametrize('derived', _pid_pinned_derived_names())
def test_symlink_at_a_derived_sibling_name_is_not_followed_or_emptied(
        monkeypatch, tmp_path, capsys, derived):
    # F-B, reproduced before the fix: a symlink at `.out.outgoing.<pid>` pointing at a
    # directory made the run **succeed** while the symlink's target was **emptied** and
    # the symlink itself was left behind. `_discard_tree` checked *children*
    # (`if child.is_dir() and not child.is_symlink()`) but never the root it was handed,
    # while its docstring claimed "A symlink is unlinked rather than followed".
    target = tmp_path / 'user-dir'
    target.mkdir()
    (target / 'keep.txt').write_text('keep me')
    (target / 'nested').mkdir()
    (target / 'nested' / 'deep.txt').write_text('keep me too')
    link = tmp_path / derived
    link.symlink_to(target, target_is_directory=True)
    _out_setup(monkeypatch, tmp_path)
    rc = main()
    envelope = json.loads(capsys.readouterr().out)
    assert rc is False, envelope
    assert envelope['status'] == 'pass'
    assert link.is_symlink()
    assert (target / 'keep.txt').read_text() == 'keep me'
    assert (target / 'nested' / 'deep.txt').read_text() == 'keep me too'


def test_out_symlink_loop_fails_with_an_envelope_naming_the_flag(monkeypatch, tmp_path, capsys):
    # F-C, reproduced before the fix: on Python 3.12 `Path.resolve()` raises
    # `RuntimeError` — not the `OSError`/`ValueError`/`AttributeError` the fail-envelope
    # tuple catches — for a symlink loop, so `--out <loop>` exited 1 with a traceback
    # and **empty stdout**. That breaks the machine-readable-envelope contract the
    # module states elsewhere: a caller parsing stdout gets nothing at all.
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    loop, other = tmp_path / 'loop', tmp_path / 'other'
    loop.symlink_to(other)
    other.symlink_to(loop)
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
                                      '--recorded', str(tmp_path / 'recorded.jsonl'),
                                      '--out', str(loop)])
    assert main() is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and envelope['errors']
    assert '--out' in envelope['errors'][0]


def test_version_incompatible_skipped_count_is_symmetric(monkeypatch, tmp_path, capsys):
    # F-F: the version-incompatible branch must count the observations it skipped on
    # *both* sides, exactly as the version-compatible path does. Two current and two
    # prior observations make the correct value 4 and the current-window-only value 2
    # — the mutation `len(indexed_current) + len(indexed_prior)` -> `len(indexed_current)`
    # (Round 4 survivor M22) — and the two are distinguishable only because the inputs
    # are non-empty on both sides. The compatible path already asserts this symmetry
    # (`test_diff_skips_incompatible_config`); this is the branch Round 4 added.
    prior_panel = {**PANEL_ONE, 'panel_version': 'v1'}
    current_panel = {**PANEL_ONE, 'panel_version': 'v2'}
    prior = [{**BASE, 'timestamp': '2026-09-19T10:00:00Z', 'brand_mentioned': False},
             {**BASE, 'timestamp': '2026-09-19T11:00:00Z', 'repetition': 2}]
    current = [{**BASE, 'timestamp': '2026-09-20T10:00:00Z'},
               {**BASE, 'timestamp': '2026-09-20T11:00:00Z', 'repetition': 2,
                'brand_mentioned': False}]
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, current_panel, current,
        prior=prior, prior_panel=prior_panel)
    _assert_renderings_agree(rc, envelope, report, summary, out)
    coverage = summary['diff']['coverage']
    assert coverage['panel_version']['compatible'] is False
    assert coverage['skipped_incompatible'] == 4
    assert _line(report, 'Compared') == (
        '0 probe targets; response changes: 0; unpaired repetitions: 0; '
        'skipped incompatible: 4; skipped failed: 0; skipped failed prior: 0')


def test_unmeasured_outranks_incomparable(monkeypatch, tmp_path, capsys):
    # F-G: with no successful observation there is no measurement to declare
    # incomparable, so a changed panel version must not downgrade the status — the
    # order of `build_summary`'s status branches is load-bearing. The scenario is
    # reachable end to end: one declared engine, a single `error` row, and a `--prior`
    # window collected under a different panel version, so both conditions hold at once
    # and the correct answer is `unmeasured`.
    panel = {**PANEL_ONE, 'engines': ['openai'], 'panel_version': 'v2'}
    prior_panel = {**PANEL_ONE, 'engines': ['openai'], 'panel_version': 'v1'}
    prior = [{**ERROR_BASE, 'timestamp': '2026-09-19T10:00:00Z'}]
    rc, envelope, report, summary, out = _artifacts(
        monkeypatch, tmp_path, capsys, panel, [ERROR_BASE],
        prior=prior, prior_panel=prior_panel)
    _assert_renderings_agree(rc, envelope, report, summary, out)
    assert summary['unmeasured'] is True
    assert summary['diff']['coverage']['panel_version']['compatible'] is False
    assert summary['status'] == envelope['status'] == 'unmeasured'
    assert rc is True


def test_read_only_tree_set_aside_by_a_successful_run_is_not_left_behind(
        monkeypatch, tmp_path, capsys):
    # F-H, reproduced before the fix: with read-only content inside the outgoing `out`
    # (here `out/sub` at mode 0555) `_discard_tree` swallowed the `OSError`, so the run
    # **succeeded** and left the whole previous epoch sitting beside `out` forever —
    # while the `finally` comment claims nothing is left behind. The tree is one this
    # run created, so its modes are the run's to change: the directory is made
    # removable and the claim is made true rather than hedged.
    out = tmp_path / 'out'
    (out / 'sub').mkdir(parents=True)
    (out / 'sub' / 'prior-epoch.txt').write_text('the whole previous epoch')
    (out / 'summary.json').write_text('{"status": "pass"}')
    os.chmod(out / 'sub', 0o555)
    _out_setup(monkeypatch, tmp_path)
    try:
        rc = main()
        envelope = json.loads(capsys.readouterr().out)
    finally:
        # Leave the tmp tree removable even if the run did leak it.
        for stale in tmp_path.glob('.out.*'):
            for d in stale.rglob('*'):
                if d.is_dir():
                    os.chmod(d, 0o755)
    assert rc is False and envelope['status'] == 'pass'
    assert list(tmp_path.glob('.out.*')) == []
    assert sorted(p.name for p in out.iterdir()) == [
        'evidence.jsonl', 'panel.json', 'report.md', 'summary.json']


def test_interrupt_during_cleanup_still_reports_the_envelope(monkeypatch, tmp_path, capsys):
    # Nit: a second interrupt during the `finally` cleanup escaped as an unhandled
    # `KeyboardInterrupt` — exit 130, no envelope — even though the run had already
    # decided its outcome. The caller is owed the machine-readable envelope whatever
    # the cleanup does, and one interrupted target must not abandon the other.
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'summary.json').write_text('{"status": "pass"}')
    _out_setup(monkeypatch, tmp_path)
    _fail_rename_on_call(monkeypatch, 2, KeyboardInterrupt())
    discarded = []

    def interrupting(path):
        discarded.append(path)
        raise KeyboardInterrupt()

    monkeypatch.setattr(ai_answer_probe, '_discard_tree', interrupting)
    rc = main()
    envelope = json.loads(capsys.readouterr().out)
    assert rc is True
    assert envelope['status'] == 'fail' and envelope['errors']
    assert len(discarded) == 2, 'both cleanup targets are still attempted'
