import json
import sys
import pytest
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
    # Contract correction (Round 3, finding 5): rows sharing a repetition index are
    # no longer an accepted coverage input that merely reports a `duplicate_repetitions`
    # gap. `main` now rejects them at load time for both files, so the surviving
    # coverage statement is that shared indices do not count as independent samples:
    # coverage is incomplete for want of distinct samples, not satisfied.
    dup = build_summary([obs(prompt_id='p01', repetition=1),
                         obs(prompt_id='p01', repetition=1, brand_mentioned=False)], [], panel)
    assert dup['coverage']['covered_prompts'] == 0
    assert [g['reason'] for g in dup['coverage_gaps']] == ['insufficient_repetitions']
    assert dup['coverage_gaps'][0]['observed'] == 1


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
    assert _run_cli(monkeypatch, tmp_path, current_panel, [BASE], prior=prior,
                    prior_panel=prior_panel) is False
    summary = json.loads((tmp_path / 'out' / 'summary.json').read_text())
    assert summary['diff']['coverage']['panel_version'] == {
        'current': 'v2', 'prior': 'v1', 'compatible': False}
    assert summary['diff']['changes'] == []
    assert summary['diff']['trends'] == []
    report = (tmp_path / 'out' / 'report.md').read_text()
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
    assert 'Prior panel version not supplied' in (tmp_path / 'out' / 'report.md').read_text()


def test_failed_run_leaves_no_pass_claiming_summary(monkeypatch, tmp_path, capsys):
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'report.md').mkdir()          # the later artifact write cannot succeed
    (out / 'summary.json').write_text('{"status": "stale-prior-run"}')
    (tmp_path / 'panel.json').write_text(json.dumps(PANEL_ONE))
    (tmp_path / 'recorded.jsonl').write_text(json.dumps(BASE) + '\n')
    monkeypatch.setattr(sys, 'argv', ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
                                      '--recorded', str(tmp_path / 'recorded.jsonl'),
                                      '--out', str(out)])
    assert main() is True
    envelope = json.loads(capsys.readouterr().out)
    assert envelope['status'] == 'fail' and envelope['errors']
    # The failed run must not have published a pass claim, and must not have
    # overwritten the previous run's summary either.
    assert (out / 'summary.json').read_text() == '{"status": "stale-prior-run"}'
    assert not (tmp_path / 'out.staging').exists()


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


def _assert_renderings_agree(rc, envelope, report, summary, out):
    """The four renderings of one run must not disagree with each other."""
    # stdout envelope <-> summary.json <-> exit code
    assert envelope['out'] == str(out)
    assert {k: v for k, v in envelope.items() if k != 'out'} == summary
    assert envelope['status'] == summary['status']
    assert rc == (summary['status'] != 'pass')
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
