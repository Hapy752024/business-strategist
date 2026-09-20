import json
import pytest
from scripts.monitoring.ai_answer_probe import normalize_observation, diff_observations, build_summary, load_panel

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
        {'prompt_id': 'p01', 'engine': 'openai', 'field': 'brand_mentioned', 'from': False, 'to': True}
    ]
    assert result['coverage']['compared'] == 1
    assert result['coverage']['skipped_failed'] == 1


def test_diff_skips_incompatible_config():
    prior = [obs(model='gpt-old'), obs(prompt_id='p03', locale='de-DE')]
    current = [obs(), obs(prompt_id='p03')]
    result = diff_observations(current, prior)
    assert result['changes'] == []
    assert result['coverage']['skipped_incompatible'] == 2


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
