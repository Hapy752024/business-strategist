"""Behavioral boundaries across appraisal, stage closure, plan and handoff."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts import case_workspace as c, route_workflow as routing
from scripts.evidence_scout import workspace as w
from scripts.brand.build_business_to_brand_handoff import build_snapshot
from scripts.brand.validate_business_to_brand_handoff import validate as validate_handoff
from test_case_economics import inputs
from test_strategy_review import plan, position


def setup(tmp_path):
    root = tmp_path / 'topic'
    c.initialize(root, 'Synthetic topic')
    for cid in ['a', 'b']:
        scope = c.add_case(root, cid, cid)
        for section in ['customer_segments', 'customer_journey', 'pain_points']:
            p = scope / 'market_research' / section / 'evidence.md'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('Synthetic evidence; conditional interpretation, no market claim.')
    return root


def appraisal(root, cid='a'):
    return {'manifest_revision': c.case_manifest(root, cid)['manifest_revision'], 'assessment_revision': c.case_manifest(root, cid)['assessment_revision'],
            'documents': {n: '# Conditional assessment\n\nUnknown demand.' for n in ['README.md', 'feasibility.md', 'business-case.md']},
            'source_bindings': [c.source_binding(root, f'cases/{cid}/market_research/pain_points/evidence.md', locator='first line', applicability=cid)],
            'comparison': {'summary': 'Conditional ' + cid + ' assessment; investigate before commitment.', 'principal_uncertainty': 'Unproven demand', 'next_action': 'Seek customer evidence'},
            'economics_inputs': inputs()}


def test_appraisal_inputs_cannot_silently_change_or_publish_stale_drafts(tmp_path):
    root = setup(tmp_path)
    draft = appraisal(root)
    c.publish_assessment(root, 'a', draft, 'appraise-a', 'Evaluate case')
    before = (root / c.PROJECT).read_bytes()
    with pytest.raises(ValueError, match='revision conflict'):
        c.publish_assessment(root, 'a', draft, 'stale', 'Old parallel draft')
    draft = appraisal(root)
    draft.update(material_change=False)
    draft['economics_inputs']['fixed_per_month'] = 0
    with pytest.raises(ValueError, match='material revision'):
        c.publish_assessment(root, 'a', draft, 'cosmetic', 'Changed economics')
    assert (root / c.PROJECT).read_bytes() == before
    assert c.read_project(root)['selection'] is None
    assert not (root / 'strategy').exists()


def test_old_run_cannot_restore_corrected_gate(tmp_path):
    root = setup(tmp_path)
    run, scope = w.resolve_run_dir(topic='a', workspace_arg=str(root), case_id='a', out_dir='', legacy_output=False,
                                   workspace_subdir='market_research/pain_points/runs')
    evidence = run / 'evidence.md'; evidence.write_text('Old review')
    c.correct(root, ['a'], 'Old interpretation was wrong', 'correction')
    before = (scope / w.RESEARCH_MANIFEST_REL).read_bytes()
    with pytest.raises(ValueError, match='stale'):
        w.update_stage(scope, 'problem_validation', status='passed', gate_result='pass', artifacts=[evidence], run_dir=run)
    assert (scope / w.RESEARCH_MANIFEST_REL).read_bytes() == before
    assert evidence.read_text() == 'Old review'


def selected_plan(root):
    c.publish_assessment(root, 'a', appraisal(root), 'appraise-a', 'Conditional assessment')
    c.select(root, 'a', 'One service', 'select-a', 'Explicit user choice')
    scope = c.resolve(root, 'a')
    cm = c.case_manifest(root, 'a')
    for stage in routing.load_catalog()['startup-business-builder']['strategy_stage_prerequisites']:
        file = scope / 'market_research/pain_points' / (stage + '.md')
        file.write_text('Explicit synthetic review for ' + stage)
        w.update_stage(scope, stage, status='passed', gate_result='pass', artifacts=[file], expected_assessment_revision=cm['assessment_revision'])
    data = plan(); data['publication_base_digest'] = None; data['positioning'] = position(); data['execution_binding'] = c.binding(root, 'a')
    data['business_plan_sections'] = {name: {'status': 'provisional', 'text': 'Synthetic conditional plan; open evidence gaps.'} for name in c.PLAN_SECTIONS}
    c.publish_business_plan(root, 'a', data, 'plan-a', 'Assemble one selected plan')
    return data


def test_selected_plan_handoff_switch_back_and_shared_interpretation(tmp_path):
    root = setup(tmp_path)
    data = selected_plan(root)
    path = root / 'strategy/strategy-plan.json'
    snapshot = build_snapshot(path, path)
    handoff = root / 'branding/handoff.json'; handoff.parent.mkdir(); handoff.write_text(c.encoded(snapshot))
    assert validate_handoff(handoff, check_sources=True) == []
    c.correct(root, ['b'], 'Unrelated B change', 'correct-b')
    assert validate_handoff(handoff, check_sources=True) == []
    shared = root / 'market_research/shared.md'; shared.parent.mkdir(exist_ok=True); shared.write_text('Shared plan-only source')
    data['business_plan_sections']['funding_legal_ip'] = {'status': 'supported', 'text': 'Synthetic source interpretation',
        'source_bindings': [c.source_binding(root, 'market_research/shared.md', locator='line 1', applicability='selected A legal research')]}
    data['publication_base_digest'] = c.digest(path.read_bytes())
    c.publish_business_plan(root, 'a', data, 'plan-source', 'Bind plan-only input')
    old = shared.read_bytes()
    c.correct(root, [], 'Interpretation correction, bytes unchanged', 'shared-correction', source_path='market_research/shared.md')
    assert shared.read_bytes() == old
    assert c.case_manifest(root, 'a')['assessment_revision'] == 3
    assert c.load(path)['review_required']
    assert validate_handoff(handoff)
    c.select(root, 'b', 'Other service', 'select-b', 'User selected B')
    c.select(root, 'a', 'One service', 'select-a-again', 'User returned to A')
    assert validate_handoff(handoff)
    assert (root / 'history/snapshots/shared-correction/strategy/strategy-plan.json').exists()


def test_case_output_scope_and_parallel_draft_conflicts(tmp_path):
    root = setup(tmp_path)
    for output in [root / 'cases/unknown/market_research/pain_points/runs/new', root / 'strategy/runs/new']:
        with pytest.raises(ValueError):
            w.prepare_research_output(output)
        assert not output.exists()
    with pytest.raises(ValueError):
        w.prepare_research_output(root / 'cases/b/market_research/pain_points/runs/new', workspace_arg=str(root), case_id='a')
    rev = c.read_project(root)['manifest_revision']
    def publish(n):
        try:
            c.publish(root, {'cases/a/README.md': str(n)}, expected_revision=rev, decision_id='parallel-' + str(n), reason='Owner draft')
            return 'published'
        except ValueError:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(publish, [1, 2])) == ['conflict', 'published']


def test_cosmetic_drafts_and_root_plan_drafts_reject_overlapping_writes(tmp_path):
    root = setup(tmp_path)
    c.publish_assessment(root, 'a', appraisal(root), 'initial', 'Assess')
    first = appraisal(root); first['material_change'] = False
    second = json.loads(json.dumps(first))
    first['documents']['README.md'] = '# First spelling fix'
    second['documents']['README.md'] = '# Other stale spelling fix'
    c.publish_assessment(root, 'a', first, 'first-spelling', 'Cosmetic edit')
    with pytest.raises(ValueError, match='publication revision conflict'):
        c.publish_assessment(root, 'a', second, 'stale-spelling', 'Parallel cosmetic edit')
    assert c.case_manifest(root, 'a')['assessment_revision'] == 2
    # Selected-plan publication has its own document digest, independent of case revision.
    other = setup(tmp_path / 'other')
    data = selected_plan(other)
    with pytest.raises(ValueError, match='publication conflict'):
        c.publish_business_plan(other, 'a', data, 'stale-plan', 'Second stale root plan draft')


def test_retained_economics_cannot_drop_its_evidence_binding(tmp_path):
    root = setup(tmp_path)
    draft = appraisal(root)
    source = draft['source_bindings'][0]['path']
    draft['economics_inputs']['provenance'] = {'revenue_per_unit': {'status':'evidence_backed','source_refs':[source]}}
    c.publish_assessment(root, 'a', draft, 'initial-economics', 'Assess')
    revised = appraisal(root); revised.pop('economics_inputs')
    revised['source_bindings'] = [c.source_binding(root, 'cases/a/market_research/customer_journey/evidence.md', locator='line 1', applicability='journey only')]
    with pytest.raises(ValueError, match='economic evidence'):
        c.publish_assessment(root, 'a', revised, 'drop-source', 'Change research coverage')


def test_old_plan_source_correction_does_not_invalidate_new_selected_case(tmp_path):
    root = setup(tmp_path)
    data = selected_plan(root)
    source = root / 'market_research/plan-only.md'; source.parent.mkdir(exist_ok=True); source.write_text('Synthetic source')
    data['publication_base_digest'] = c.digest((root / 'strategy/strategy-plan.json').read_bytes())
    data['business_plan_sections']['business'] = {'status':'supported','text':'Conditional case A interpretation',
        'source_bindings':[c.source_binding(root,'market_research/plan-only.md',locator='line 1',applicability='case A only')]}
    c.publish_business_plan(root,'a',data,'plan-with-source','Bind A source')
    c.select(root,'b','B scope','select-b','Explicit user switch')
    before = c.binding(root,'b')
    c.correct(root,[],'Correct A source','correct-a-source',source_path='market_research/plan-only.md')
    assert c.binding(root,'b') == before
    assert c.case_manifest(root,'a')['assessment_revision'] == 3


def test_extended_strategy_publication_preserves_contract_and_source_freshness(tmp_path):
    from test_strategy_review import detailed_position
    root = setup(tmp_path)
    data = selected_plan(root)
    path = root / 'strategy/strategy-plan.json'
    data['positioning'] = detailed_position()
    data['publication_base_digest'] = c.digest(path.read_bytes())
    c.publish_business_plan(root, 'a', data, 'extended-position', 'Review delivery and defense hypotheses')
    saved = c.load(path)
    assert saved['positioning'] == data['positioning']
    snapshot = build_snapshot(path, path)
    handoff = root / 'branding/handoff.json'; handoff.parent.mkdir(); handoff.write_text(c.encoded(snapshot))
    assert snapshot['positioning'] == data['positioning']
    assert validate_handoff(handoff, check_sources=True) == []
    data['publication_base_digest'] = c.digest(path.read_bytes())
    data['positioning']['defensibility']['hypotheses'][0]['entrant_response'] = 'New evidence changes the imitation risk'
    c.publish_business_plan(root, 'a', data, 'revised-defense', 'Reassess competitive response')
    assert any('source changed' in e for e in validate_handoff(handoff, check_sources=True))
