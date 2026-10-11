"""Per-case publication must preserve research, review and execution boundaries."""
import copy
import json

import pytest

from scripts import case_workspace as cases, case_business_plan as plans
from scripts import validate_case_insights as insights
from scripts.business_plan_render import financial_tables
from scripts.case_economics import calculate
from appraisal_gate_fixture import install
from test_case_insights import setup_case, packet as insights_packet
from test_case_end_to_end import inputs


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    install(monkeypatch)
    root, scope = setup_case(tmp_path)
    packet = insights_packet(root)
    cases.publish_insights(root, 'a', packet, 'insights', 'Consolidate sources')
    cm = cases.case_manifest(root, 'a')
    plan = {'schema_version': '1.0', 'case_id': 'a', 'assessment_revision': cm['assessment_revision'],
            'manifest_revision': cm['manifest_revision'], 'publication_base_digest': None,
            'insights_digest': cases.digest((scope / 'case_insights.md').read_bytes()), 'economics_input_digest': None,
            'evidence_maturity': 'desk_research', 'publication_status': 'progress',
            'business_plan_sections': {key: {'status': 'provisional', 'text': 'Conditional case analysis: evidence is scoped and consequential assumptions remain unresolved.'} for key in cases.PLAN_SECTIONS},
            'source_bindings': packet['source_bindings'], 'publication_claims': [], 'numeric_claims': []}
    return root, scope, plan


def test_unselected_case_gets_full_plan_without_execution_selection(prepared):
    root, scope, plan = prepared
    plans.publish(root, 'a', plan, 'plan', 'Publish provisional plan')
    assert cases.read_project(root)['selection'] is None
    assert not (root / 'strategy').exists()
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert plans.current(root, 'a')['evidence_maturity'] == 'desk_research'
    assert (scope / 'business-plan.md').read_text().count('\n## ') == 11
    assert 'business-plan.md' in (root / 'README.md').read_text()


def test_case_plan_rejects_stale_draft_sources_and_new_findings(prepared):
    root, scope, plan = prepared
    plans.publish(root, 'a', plan, 'plan', 'Publish provisional plan')
    before = (scope / 'business-plan.md').read_bytes()
    with pytest.raises(ValueError, match='revision conflict'):
        plans.publish(root, 'a', plan, 'stale', 'Overlap')
    new = scope / 'market_research/deep_dives/new.md'
    new.write_text('A new material answer changes the target buyer.')
    with pytest.raises(ValueError, match='changed case inputs'):
        plans.current(root, 'a')
    assert (scope / 'business-plan.md').read_bytes() == before


def test_final_review_binds_exact_case_plan_and_survives_its_publication(prepared):
    root, scope, plan = prepared
    plan['publication_status'] = 'final'
    preview = plans.publish(root, 'a', plan, 'preview', 'Review', preview=True)
    review = scope / 'plan-reviews/review.json'; review.parent.mkdir()
    review.write_text(cases.encoded({'author': 'author', 'reviewer': 'reviewer', 'review_task_id': 'review-task',
        'bundle_digest': preview['bundle_digest'], 'reviewed_sources': preview['reviewed_sources'], 'outcome': 'pass', 'material_findings': []}))
    plan['independent_review'] = cases.source_binding(root, str(review.relative_to(root)), locator='whole review', applicability='a final plan review')
    changed = copy.deepcopy(plan)
    changed['business_plan_sections']['business']['text'] += ' Changed conclusion.'
    with pytest.raises(ValueError, match='exact rendered publication'):
        plans.publish(root, 'a', changed, 'bad', 'Changed after review')
    plans.publish(root, 'a', plan, 'final', 'Publish reviewed final document')
    plans.current(root, 'a', require_final=True)
    assert insights.current_status(root, 'a')['status'] == 'current'
    review.write_text(review.read_text().replace('reviewer', 'changed-reviewer'))
    with pytest.raises(ValueError, match='review changed'):
        plans.current(root, 'a', require_final=True)


def test_financial_tables_reconcile_and_keep_missing_scenarios_visible():
    economics = calculate(inputs())
    text = financial_tables(economics)
    assert '```json' not in text
    assert str(economics['results']['contribution_per_unit']) in text
    assert 'Downside unresolved' in text and 'Sensitivity unresolved' in text


def test_wrong_insights_digest_and_unsupported_section_do_not_publish(prepared):
    root, scope, plan = prepared
    bad = copy.deepcopy(plan); bad['insights_digest'] = 'a' * 64
    with pytest.raises(ValueError, match='insights changed'):
        plans.publish(root, 'a', bad, 'bad', 'Wrong source')
    bad = copy.deepcopy(plan); bad['business_plan_sections']['business']['status'] = 'supported'
    with pytest.raises(ValueError, match='supported section requires'):
        plans.publish(root, 'a', bad, 'bad', 'Unsupported section')
    assert not (scope / 'business-plan.md').exists()


def test_structured_plan_changes_cannot_reuse_rendered_review(prepared):
    root, scope, plan = prepared
    plans.publish(root, 'a', plan, 'plan', 'Publish provisional plan')
    record = json.loads((scope / 'business-plan.json').read_text())
    record['business_plan_sections']['business']['text'] += ' Different structured advice.'
    (scope / 'business-plan.json').write_text(json.dumps(record))
    with pytest.raises(ValueError, match='structured inputs changed'):
        plans.current(root, 'a')
