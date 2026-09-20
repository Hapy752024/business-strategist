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


def _run_cli(monkeypatch, tmp_path, panel, recorded, prior=None):
    (tmp_path / 'panel.json').write_text(json.dumps(panel))
    (tmp_path / 'recorded.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in recorded))
    argv = ['ai_answer_probe', '--panel', str(tmp_path / 'panel.json'),
            '--recorded', str(tmp_path / 'recorded.jsonl'),
            '--out', str(tmp_path / 'out')]
    if prior is not None:
        (tmp_path / 'prior.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in prior))
        argv += ['--prior', str(tmp_path / 'prior.jsonl')]
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
    dup = build_summary([obs(prompt_id='p01', repetition=1),
                         obs(prompt_id='p01', repetition=1, brand_mentioned=False)], [], panel)
    assert dup['coverage']['covered_prompts'] == 0
    reasons = {g['reason'] for g in dup['coverage_gaps']}
    assert 'duplicate_repetitions' in reasons
    assert 'insufficient_repetitions' in reasons


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
    assert 'p01/perplexity (error)' in report
    assert 'p02 (missing_no_observation)' in report
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
