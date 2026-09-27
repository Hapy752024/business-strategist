"""End-to-end publication checks for the one current case assessment."""
import json
from pathlib import Path
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator

from scripts import case_workspace as cases
from scripts import validate_case_insights as insights
from scripts.evidence_scout import workspace as research_workspace
from scripts.verify_numeric_claims import checked_claims
from appraisal_gate_fixture import install as isolate_research_gate


@pytest.fixture(autouse=True)
def _isolated_research_gate(monkeypatch):
    isolate_research_gate(monkeypatch)


def setup_case(tmp_path):
    root = tmp_path / 'venture'
    cases.initialize(root, 'Venture')
    case = cases.add_case(root, 'a', 'A')
    assert not (case / 'README.md').exists()
    base = case / 'market_research/pain_points/runs'
    for name, text in {
        'old': 'In segment A, a customer described a repeated two-week wait. This is one occurrence, not prevalence.',
        'new': 'In segment B, a customer described same-day service. This has a different buyer and market scope.',
    }.items():
        path = base / name / 'report.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    answer = case / 'market_research/deep_dives/size/answer.md'
    answer.parent.mkdir(parents=True, exist_ok=True)
    answer.write_text('The available material does not define a reliable denominator for this segment. Market size is not established.')
    binding = cases.source_binding(root, 'cases/a/market_research/deep_dives/size/answer.md',
                                   locator='first paragraph', applicability='a market size answer')
    cases.record_question(root, 'a', {'id': 'market-size', 'question': 'How large is the reachable market?',
                                     'status': 'answered', 'answer_binding': binding},
                          'record-size-question', 'Record answered founder question')
    return root, case


def document():
    return '''# A
Last updated: 2026-09-25

## Executive assessment
Segment A may have a meaningful delay problem, but available customer accounts do not establish its prevalence or purchase demand. Further customer evidence is needed before a commercial commitment.

## Customer and problem
One customer in segment A described a repeated two-week wait. The buyer and payer remain unclear, and the impact of the wait has not been measured. The customer may continue the existing workaround.

## Market and demand
The reachable market cannot be estimated reliably because the current material does not define its denominator. The available accounts provide no purchase conversion rate.

## Alternatives and competitive position
An account from segment B described same-day service, but it involves a different buyer and market scope. It does not show that segment A is well served. Doing nothing remains an alternative.

## Business potential and feasibility
The possible offer and delivery model are still hypotheses. Pricing, capacity and customer acquisition have not been tested, so economic viability is unresolved.

## Risks, conflicting evidence and open questions
The two service-time accounts concern different segments and do not establish a contradiction in the same customer group. The unanswered question is whether delay causes a costly enough outcome to motivate action.

## Recommended next decisions
Interview recent segment A customers about the delay, its consequences and completed workarounds. Reassess the opportunity if repeated costs and credible buyer action emerge.

## Sources
The [older segment A account](market_research/pain_points/runs/old/report.md),
the [newer segment B account](market_research/pain_points/runs/new/report.md), and
the [market-size answer](market_research/deep_dives/size/answer.md) are available
in the supporting case research. Their scope limits apply throughout this assessment.
'''


def packet(root, *, text=None):
    cm = cases.case_manifest(root, 'a')
    rows = insights.inventory(root, 'a')
    answer_binding = cm['coaching']['research_questions'][0]['answer_binding']
    bindings = [answer_binding if row['path'] == answer_binding['path']
                else cases.source_binding(root, row['path'], locator='whole report', applicability='a scoped finding')
                for row in rows if row['kind'] == 'research_output']
    bindings.extend(b for row in rows for b in row.get('bindings', []))
    text = text or document()
    coverage = []
    for row in rows:
        section = ('Market and demand' if 'answer.md' in row['path'] else
                   'Customer and problem' if '/old/' in row['path'] else 'Alternatives and competitive position')
        coverage.append({'path': row['path'], 'digest': row['digest'], 'disposition': 'incorporated',
                         'reason': 'Its scoped finding is summarized in the current assessment.', 'section': section})
    comparison = {key: cm['comparison'][key] for key in ('summary', 'principal_uncertainty', 'next_action')} if cm.get('comparison') else {
        'summary': 'Segment A delay is plausible but demand is unproven.',
        'principal_uncertainty': 'Frequency and buyer action are unmeasured.',
        'next_action': 'Interview recent segment A customers.'}
    result = {'assessment_revision': cm['assessment_revision'], 'manifest_revision': cm['manifest_revision'],
              'scope_status': 'complete',
              'impact': 'presentation_only' if cm.get('comparison') else 'reviewed_findings',
              'document': text, 'source_bindings': bindings, 'comparison': comparison,
              'coverage': coverage,
              'question_coverage': [{'id': 'market-size', 'section': 'Market and demand',
                                     'reason': 'The lack of a denominator is explained.'}],
              'conflicts': [{'left': next(r['path'] for r in rows if '/old/' in r['path']),
                             'right': next(r['path'] for r in rows if '/new/' in r['path']),
                             'scope': 'A versus B customer segments', 'resolution': 'scope_qualified',
                             'rationale': 'Different buyers and markets; neither account establishes prevalence.',
                             'section': 'Alternatives and competitive position'}]}
    rendered = insights._body(root, 'a', result)
    result['review'] = {'reviewer_type': 'analyst', 'review_mode': 'inline',
                        'outcome': 'pass', 'blocking_findings': [],
                        'summary': 'Compared each source and question with the complete assessment.',
                        'checks': {key: {'status': 'pass', 'rationale': 'Reviewed the source scope and the complete rendered section.'}
                                   for key in insights.REVIEW_CHECKS},
                        'rendered_digest': insights.sha(rendered.encode()),
                        'inventory_digest': insights.inventory_digest(root, 'a', rows=rows)}
    return result


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and p.name != 'project.lock'}


def test_new_deep_dive_makes_selected_plan_consumer_pending(tmp_path):
    root, case = setup_case(tmp_path)
    cases.publish_insights(root, 'a', packet(root), 'insight-for-plan', 'Publish current case view')
    cases.select(root, 'a', 'Synthetic choice', 'select-for-plan', 'Exercise selected dependency')
    plan = {'execution_binding': cases.binding(root, 'a'), 'source_bindings': []}
    new = case / 'market_research/deep_dives/new-answer.md'
    new.parent.mkdir(parents=True, exist_ok=True)
    new.write_text('A newly answered material question about payment eligibility.')
    with pytest.raises(ValueError, match='selected-case insights are missing or stale'):
        cases.check_plan(root, plan)


def test_publish_complete_case_brief_and_detect_new_deep_dive(tmp_path):
    root, case = setup_case(tmp_path)
    draft = packet(root)
    text, _, _ = insights.validate_packet(root, 'a', draft)
    assert 'market cannot be estimated' in text
    cases.publish_insights(root, 'a', draft, 'insight-first', 'Publish reviewed case assessment')
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert (case / 'case_insights.md').read_text() == text
    assert 'cases/a/case_insights.md' in (root / 'README.md').read_text()
    assert not (case / 'README.md').exists()
    new = case / 'market_research/deep_dives/access/finding.md'
    new.parent.mkdir(parents=True)
    new.write_text('Access route is unverified for segment A.')
    assert insights.current_status(root, 'a')['status'] == 'update_pending'


def test_missing_old_run_or_question_fails_without_publication(tmp_path):
    root, _ = setup_case(tmp_path)
    draft = packet(root)
    before = snapshot(root)
    draft['coverage'] = [r for r in draft['coverage'] if '/old/' not in r['path']]
    with pytest.raises(ValueError, match='every inventoried'):
        cases.publish_insights(root, 'a', draft, 'missing-old', 'Incorrect consolidation')
    assert snapshot(root) == before
    draft = packet(root)
    draft['question_coverage'] = []
    with pytest.raises(ValueError, match='question needs coverage'):
        cases.publish_insights(root, 'a', draft, 'missing-answer', 'Omitted founder answer')
    assert snapshot(root) == before


def test_stale_review_and_shared_binding_fail_closed(tmp_path):
    root, _ = setup_case(tmp_path)
    draft = packet(root)
    before = snapshot(root)
    draft['document'] += '\nUnreviewed change.\n'
    with pytest.raises(ValueError, match='stale or incomplete semantic review'):
        cases.publish_insights(root, 'a', draft, 'stale-review', 'Unreviewed edit')
    assert snapshot(root) == before
    draft = packet(root)
    shared = root / 'market_research/shared.md'
    shared.parent.mkdir(parents=True)
    shared.write_text('Different case only')
    draft['source_bindings'].append(cases.source_binding(root, 'market_research/shared.md',
                                                       locator='whole report', applicability='case b only'))
    with pytest.raises(ValueError, match='case applicability'):
        insights.validate_packet(root, 'a', draft)


def test_followup_question_marks_published_assessment_pending(tmp_path):
    root, case = setup_case(tmp_path)
    cases.publish_insights(root, 'a', packet(root), 'insight-first', 'Reviewed assessment')
    cases.record_question(root, 'a', {'id': 'purchase', 'question': 'Will buyers actually pay?',
                                     'status': 'open'}, 'ask-purchase', 'Capture next founder question')
    assert insights.current_status(root, 'a')['status'] == 'update_pending'
    assert 'Assessment update pending' in (case / 'case_insights.md').read_text()


def test_numeric_marker_does_not_expose_internal_id(tmp_path):
    root, case = setup_case(tmp_path)
    draft = packet(root)
    draft['document'] = draft['document'].replace('Pricing, capacity and customer acquisition have not been tested',
                                                    'A reported price {{source_numeric.price}} and customer acquisition have not been tested')
    draft['numeric_claims'] = [{'id': 'price', 'document': 'case_insights.md', 'status': 'unverified',
                                'value': '99', 'metric': 'price', 'period': 'current', 'currency': 'EUR',
                                'unit': 'per month', 'scope': 'A', 'reason': 'No reviewed source'}]
    rendered = insights._body(root, 'a', draft)
    draft['review']['rendered_digest'] = insights.sha(rendered.encode())
    cases.publish_insights(root, 'a', draft, 'insight-open-price', 'Publish uncertainty')
    text = (case / 'case_insights.md').read_text()
    assert '[figure not established]' in text
    assert 'price]' not in text
    receipt = json.loads((case / 'numeric-claims.json').read_text())
    assert receipt['unverified_count'] == 1


def test_packet_and_manifest_match_shipped_schemas(tmp_path):
    root, _ = setup_case(tmp_path)
    p = packet(root)
    schema_root = Path(__file__).resolve().parents[1] / 'schemas'
    packet_schema = json.loads((schema_root / 'case-insights.schema.json').read_text())
    manifest_schema = json.loads((schema_root / 'research-manifest.schema.json').read_text())
    assert not list(Draft202012Validator(packet_schema).iter_errors(p))
    cases.publish_insights(root, 'a', p, 'insight-schema', 'Reviewed case assessment')
    assert not list(Draft202012Validator(manifest_schema).iter_errors(cases.case_manifest(root, 'a')))


def test_unfilled_template_guidance_cannot_publish(tmp_path):
    root, _ = setup_case(tmp_path)
    draft = packet(root, text=document().replace('Segment A may', '<!-- draft guidance --> Segment A may'))
    draft['review']['rendered_digest'] = insights.sha(draft['document'].encode())
    with pytest.raises(ValueError, match='authoring placeholder'):
        cases.publish_insights(root, 'a', draft, 'template-leak', 'Unfinished document')


def test_internal_workflow_details_do_not_enter_client_brief(tmp_path):
    root, _ = setup_case(tmp_path)
    draft = packet(root, text=document().replace('The reachable market',
                                                 'The provider status and run ID were checked. The reachable market'))
    draft['review']['rendered_digest'] = insights.sha(draft['document'].encode())
    with pytest.raises(ValueError, match='internal research workflow language'):
        cases.publish_insights(root, 'a', draft, 'process-leak', 'Unfinished document')


def test_stage_update_and_source_correction_mark_insights_pending(tmp_path):
    root, case = setup_case(tmp_path)
    cases.publish_insights(root, 'a', packet(root), 'insight-first', 'Reviewed assessment')
    new = case / 'market_research/customer_journey/new-finding.md'
    new.parent.mkdir(parents=True)
    new.write_text('A new reviewed journey observation.')
    research_workspace.update_stage(case, 'customer_profile', status='in_progress', gate_result='not_run',
                                    artifacts=[new], expected_assessment_revision=1)
    assert cases.case_manifest(root, 'a')['insights']['state'] == 'update_pending'
    assert 'Assessment update pending' in (case / 'case_insights.md').read_text()
    # A source consumed only by insights still identifies this case on correction.
    before = cases.case_manifest(root, 'a')['assessment_revision']
    cases.correct(root, [], 'Old source interpretation needs repair', 'source-correction',
                  source_path='cases/a/market_research/pain_points/runs/old/report.md')
    assert cases.case_manifest(root, 'a')['assessment_revision'] == before + 1


def test_legacy_readme_is_reconciled_and_archived_on_conversion(tmp_path):
    root, case = setup_case(tmp_path)
    old = case / 'README.md'
    old.write_text('# A\n\nEarlier provisional view based on one customer account.\n')
    (case / 'feasibility.md').write_text('# Feasibility\n\nNo reviewed delivery model yet.\n')
    (case / 'business-case.md').write_text('# Business case\n\nDemand remains unresolved.\n')
    draft = packet(root)
    old_path = 'cases/a/README.md'
    row = next(row for row in draft['coverage'] if row['path'] == old_path)
    row.update(disposition='superseded', reason='Compared with the original account and replaced by the current assessment.',
               replacement='cases/a/market_research/pain_points/runs/old/report.md')
    row.pop('section', None)
    for row in draft['coverage']:
        if row['path'].endswith(('/feasibility.md', '/business-case.md')):
            row.update(disposition='no_material_finding', reason='Already reflected as an explicit unknown in the current brief.')
            row.pop('section', None)
    draft['review']['inventory_digest'] = insights.inventory_digest(root, 'a')
    cases.publish_insights(root, 'a', draft, 'convert-old', 'Convert earlier case narrative')
    assert not old.exists()
    assert (root / 'history/snapshots/convert-old/cases/a/README.md').read_text().startswith('# A')
    assert insights.current_status(root, 'a')['status'] == 'current'


def test_insights_refresh_retains_checked_number_in_untouched_annex(tmp_path):
    root, case = setup_case(tmp_path)
    cases.publish_insights(root, 'a', packet(root), 'insight-first', 'Reviewed assessment')
    source = case / 'market_research/pain_points/figure.json'
    observation = {'value': '42.5', 'metric': 'observed_amount', 'period': 'FY2025',
                   'currency': 'EUR', 'unit': 'per case', 'scope': 'segment A'}
    source.write_text(json.dumps({'figure': observation}))
    binding = cases.source_binding(root, 'cases/a/market_research/pain_points/figure.json',
                                   locator='/figure', applicability='case a only')
    claim = {**observation, 'id': 'annex-amount', 'document': 'feasibility.md',
             'status': 'verified', 'source_binding': binding}
    rendered, receipt = checked_claims(root, {'feasibility.md': 'Observed amount {{source_numeric.annex-amount}}.'},
                                       [claim], [binding])
    cases.publish(root, {'cases/a/feasibility.md': rendered['feasibility.md'],
                         'cases/a/numeric-claims.json': cases.encoded(receipt)},
                  expected_revision=cases.read_project(root)['manifest_revision'],
                  decision_id='annex-amount', reason='Add checked annex observation', affected=['a'])
    draft = packet(root)
    draft['source_bindings'] = [b for b in draft['source_bindings'] if b['path'] != binding['path']]
    for row in draft['coverage']:
        if row['path'].endswith(('/figure.json', '/feasibility.md')):
            row.update(disposition='no_material_finding',
                       reason='This supporting amount does not change the current customer conclusion.')
            row.pop('section', None)
    cases.publish_insights(root, 'a', draft, 'insight-refreshed', 'Reconcile supporting figure')
    after = cases.load(case / 'numeric-claims.json')
    assert after['verified_count'] == 1
    assert after['claims'][0]['id'] == 'annex-amount'
    assert insights.current_status(root, 'a')['status'] == 'current'


def shared_input(root, case, *, owner='case'):
    path = root / 'market_research/access.md'
    path.parent.mkdir(exist_ok=True)
    path.write_text('A second segment A account reports no delay in the same period. The disagreement is unresolved.')
    binding = cases.source_binding(root, 'market_research/access.md', locator='first paragraph',
                                   applicability='case a: same customer segment and period')
    cm = cases.case_manifest(root, 'a')
    if owner == 'case':
        cm['source_bindings'].append(binding)
    elif owner == 'stage':
        cm.setdefault('stages', {})['customer_profile'] = {'source_bindings': [binding]}
    elif owner == 'question':
        cm['coaching']['research_questions'].append({'id': 'access', 'question': 'Is service delayed?',
                                                    'status': 'partial', 'answer_binding': binding})
    cases.atomic(case / 'market_research/manifest.json', cases.encoded(cm))
    return path, binding


def refresh_review(root, draft):
    rows = insights.inventory(root, 'a', source_bindings=draft['source_bindings'])
    draft['review']['rendered_digest'] = insights.sha(insights._body(root, 'a', draft).encode())
    draft['review']['inventory_digest'] = insights.inventory_digest(root, 'a', rows=rows)


def reconcile_shared(root, draft, binding):
    if binding not in draft['source_bindings']:
        draft['source_bindings'].append(binding)
    rows = insights.inventory(root, 'a', source_bindings=draft['source_bindings'])
    if not any(row['path'] == binding['path'] for row in draft['coverage']):
        row = next(row for row in rows if row['path'] == binding['path'])
        draft['coverage'].append({'path': row['path'], 'digest': row['digest'], 'disposition': 'incorporated',
                                  'reason': 'The conflicting service experience qualifies the customer finding.',
                                  'section': 'Risks, conflicting evidence and open questions'})
    draft['document'] = draft['document'].replace('The unanswered question is',
        'A second account from segment A reports no delay in the same period. '
        'The accounts disagree; the frequency and conditions of delay remain unresolved. The unanswered question is')
    draft['document'] += '\n[Same-segment account](../../market_research/access.md)\n'
    draft['conflicts'].append({'left': binding['path'],
                               'right': 'cases/a/market_research/pain_points/runs/old/report.md',
                               'scope': 'Segment A service time in the same period',
                               'resolution': 'unresolved_disclosed',
                               'rationale': 'The disagreement is disclosed; the recommendation remains investigation, not commitment.',
                               'section': 'Risks, conflicting evidence and open questions'})
    refresh_review(root, draft)
    return draft


@pytest.mark.parametrize('owner', ['case', 'stage', 'question'])
def test_shared_input_cannot_be_omitted_and_conflict_can_publish(tmp_path, owner):
    root, case = setup_case(tmp_path)
    path, binding = shared_input(root, case, owner=owner)
    draft = packet(root)
    if owner == 'question':
        draft['question_coverage'].append({'id': 'access', 'section': 'Risks, conflicting evidence and open questions',
                                           'reason': 'The answer remains partial because same-scope accounts disagree.'})
    excluded = root / 'market_research/unrelated.md'
    excluded.write_text('A different market that this case did not import.')
    rows = insights.inventory(root, 'a')
    assert any(row['path'] == binding['path'] for row in rows)
    assert not any(row['path'].endswith('unrelated.md') for row in rows)
    omitted = json.loads(json.dumps(draft))
    omitted['coverage'] = [row for row in draft['coverage'] if row['path'] != binding['path']]
    before = snapshot(root)
    with pytest.raises(ValueError, match='every inventoried'):
        cases.publish_insights(root, 'a', omitted, 'omit-shared', 'Incomplete reconciliation')
    assert snapshot(root) == before
    draft = reconcile_shared(root, draft, binding)
    cases.publish_insights(root, 'a', draft, 'shared-reviewed', 'Disclose conflicting customer accounts')
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert 'The accounts disagree' in (case / 'case_insights.md').read_text()
    assert cases.case_manifest(root, 'a')['source_bindings'] == ([binding] if owner == 'case' else [])
    path.write_text('Corrected account: delay was reported, but its cause is different.')
    assert insights.current_status(root, 'a')['status'] == 'update_pending'


@pytest.mark.parametrize('change', ['delete', 'applicability', 'locator', 'add_stage_binding'])
def test_shared_inventory_freshness_includes_missing_and_changed_context(tmp_path, change):
    root, case = setup_case(tmp_path)
    path, binding = shared_input(root, case)
    cases.publish_insights(root, 'a', reconcile_shared(root, packet(root), binding),
                           'shared-current', 'Review shared source')
    cm = cases.case_manifest(root, 'a')
    if change == 'delete':
        path.unlink()
        row = next(row for row in insights.inventory(root, 'a') if row['path'] == binding['path'])
        assert row['kind'] == 'missing' and row['digest'] is None
    elif change == 'add_stage_binding':
        cm.setdefault('stages', {})['customer_profile'] = {'source_bindings': [{**binding, 'locator': 'second paragraph'}]}
    else:
        cm['source_bindings'][0][change] = ('case a: a different target segment' if change == 'applicability' else 'second paragraph')
    cases.atomic(case / 'market_research/manifest.json', cases.encoded(cm))
    assert insights.current_status(root, 'a')['status'] == 'update_pending'


def test_new_packet_shared_input_persists_and_can_be_explicitly_retired(tmp_path):
    root, case = setup_case(tmp_path)
    _, binding = shared_input(root, case, owner='packet')
    draft = reconcile_shared(root, packet(root), binding)
    draft_path = tmp_path / 'draft.json'
    draft_path.write_text(cases.encoded(draft))
    out = tmp_path / 'prepared'
    before = snapshot(root)
    result = subprocess.run([sys.executable, str(Path(insights.__file__)), '--workspace', str(root),
                             '--case', 'a', '--packet', str(draft_path), '--prepare', '--out', str(out)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    prepared = json.loads(result.stdout)
    assert prepared['inventory_digest'] == draft['review']['inventory_digest']
    assert prepared['rendered_digest'] == draft['review']['rendered_digest']
    assert any(row['path'] == binding['path'] for row in cases.load(out / 'inventory.json'))
    assert snapshot(root) == before
    cases.publish_insights(root, 'a', draft, 'shared-packet', 'Review newly supplied shared input')
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert any(row['path'] == binding['path'] for row in insights.inventory(root, 'a'))
    # Account for this input before retiring it, even though it has no stage binding.
    replacement = packet(root)
    replacement['source_bindings'] = [b for b in replacement['source_bindings'] if b['path'] != binding['path']]
    row = next(row for row in replacement['coverage'] if row['path'] == binding['path'])
    row.update(disposition='out_of_scope', reason='A subsequent scope review established that this account concerns a different service.')
    row.pop('section')
    refresh_review(root, replacement)
    cases.publish_insights(root, 'a', replacement, 'shared-retired', 'Retire inapplicable evidence after review')
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert not any(row['path'] == binding['path'] for row in insights.inventory(root, 'a'))


@pytest.mark.parametrize('defect', ['wrong_case', 'missing_applicability', 'different_case_prefix'])
def test_declared_shared_inputs_do_not_broaden_case_scope(tmp_path, defect):
    root, case = setup_case(tmp_path)
    _, binding = shared_input(root, case)
    cm = cases.case_manifest(root, 'a')
    if defect == 'wrong_case':
        cases.add_case(root, 'b', 'B')
        binding['path'] = 'cases/b/case_insights.md'
    elif defect == 'missing_applicability':
        binding['applicability'] = 'Relevant general research'
    else:
        binding['applicability'] = 'case a-other: a different investigated case'
    cm['source_bindings'] = [binding]
    cases.atomic(case / 'market_research/manifest.json', cases.encoded(cm))
    with pytest.raises(ValueError, match='another case|case applicability'):
        insights.inventory(root, 'a')


def test_shared_sources_deduplicate_repeated_bindings_without_losing_context(tmp_path):
    root, case = setup_case(tmp_path)
    _, binding = shared_input(root, case)
    before = insights.inventory_digest(root, 'a')
    cm = cases.case_manifest(root, 'a')
    cm.setdefault('stages', {})['customer_profile'] = {'source_bindings': [binding, binding]}
    cases.atomic(case / 'market_research/manifest.json', cases.encoded(cm))
    assert insights.inventory_digest(root, 'a') == before
    rows = [row for row in insights.inventory(root, 'a') if row['path'] == binding['path']]
    assert len(rows) == 1 and rows[0]['bindings'] == [binding]


@pytest.mark.parametrize('defect', ['revise', 'failed_check', 'unreviewed_check', 'open_finding', 'old_format'])
def test_semantic_review_rejection_cannot_publish_or_modify_case(tmp_path, defect):
    root, _ = setup_case(tmp_path)
    draft = packet(root)
    review = draft['review']
    if defect == 'revise':
        review['outcome'] = 'revise'
    elif defect in {'failed_check', 'unreviewed_check'}:
        review['checks']['contradictions'] = {'status': 'fail' if defect == 'failed_check' else 'not_reviewed',
                                             'rationale': 'Same-scope customer accounts still need reconciliation before publication.'}
    elif defect == 'open_finding':
        review['blocking_findings'] = ['The recommendation ignores a material conflicting customer account.']
    else:
        review.pop('outcome')
        review.pop('blocking_findings')
    before = snapshot(root)
    with pytest.raises(ValueError, match='semantic review'):
        cases.publish_insights(root, 'a', draft, 'rejected-review', 'Review has unresolved defects')
    assert snapshot(root) == before


def test_rejected_brief_requires_corrected_text_and_a_new_passing_review(tmp_path):
    root, case = setup_case(tmp_path)
    draft = packet(root, text=document().replace('do not establish its prevalence or purchase demand',
                                                 'prove widespread demand and justify immediate investment'))
    draft['review']['outcome'] = 'revise'
    draft['review']['checks']['accuracy'] = {'status': 'fail',
        'rationale': 'One scoped customer account cannot establish widespread purchase demand.'}
    draft['review']['blocking_findings'] = ['The executive assessment overstates prevalence and purchase demand.']
    with pytest.raises(ValueError, match='semantic review blocks'):
        cases.publish_insights(root, 'a', draft, 'overclaim', 'Reject unsupported recommendation')
    reviewed = packet(root)
    # A correct text with the earlier text hash still cannot inherit its review.
    reviewed['review']['rendered_digest'] = draft['review']['rendered_digest']
    with pytest.raises(ValueError, match='stale or incomplete'):
        cases.publish_insights(root, 'a', reviewed, 'stale-correction', 'Corrected prose needs review')
    refresh_review(root, reviewed)
    cases.publish_insights(root, 'a', reviewed, 'corrected-reviewed', 'Reviewed bounded conclusion')
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert 'do not establish its prevalence' in (case / 'case_insights.md').read_text()


@pytest.mark.parametrize('old_review', [True, False])
def test_current_status_never_grandfathers_missing_or_failed_review_outcomes(tmp_path, old_review):
    root, case = setup_case(tmp_path)
    cases.publish_insights(root, 'a', packet(root), 'published', 'Reviewed case')
    cm = cases.case_manifest(root, 'a')
    path = root / cm['insights']['review_path']
    receipt = cases.load(path)
    if old_review:
        receipt['review'].pop('outcome')
    else:
        receipt['review']['outcome'] = 'revise'
    # Simulate an earlier publisher that accepted this review, with intact hashes.
    path.write_text(cases.encoded(receipt))
    cm['insights']['review_digest'] = cases.digest(path.read_bytes())
    cases.atomic(case / 'market_research/manifest.json', cases.encoded(cm))
    assert insights.current_status(root, 'a')['status'] == 'invalid'


@pytest.mark.parametrize('target', ['../../../outside.md', '../../market_research/missing.md',
                                    'alias.md', 'alias/../market_research/safe.md'])
def test_invalid_source_links_still_fail_without_publication(tmp_path, target):
    root, case = setup_case(tmp_path)
    (tmp_path / 'outside.md').write_text('Outside this Business workspace.')
    local = case / 'market_research'
    (local / 'safe.md').write_text('Local source that must not hide a symlink traversal.')
    (case / 'alias.md').symlink_to(tmp_path / 'outside.md')
    (case / 'alias').symlink_to(tmp_path, target_is_directory=True)
    draft = packet(root, text=document() + f'\n[Additional source]({target})\n')
    before = snapshot(root)
    with pytest.raises(ValueError, match='escapes workspace|broken insights source link|symlinks'):
        cases.publish_insights(root, 'a', draft, 'invalid-source-link', 'Reject invalid citation')
    assert snapshot(root) == before


def conversion_packet(root):
    draft = packet(root)
    row = next(row for row in draft['coverage'] if row['path'] == 'cases/a/README.md')
    row.update(disposition='superseded', replacement='cases/a/market_research/pain_points/runs/old/report.md',
               reason='The earlier assessment was reconciled with its original customer account.')
    row.pop('section', None)
    return draft


def test_legacy_stage_dependency_requires_refresh_before_conversion(tmp_path):
    root, case = setup_case(tmp_path)
    old = case / 'README.md'
    old.write_text('# A\n\nEarlier interpretation of the customer account.\n')
    research_workspace.update_stage(case, 'customer_profile', status='passed', gate_result='pass',
                                    artifacts=[old], expected_assessment_revision=1)
    draft = conversion_packet(root)
    before = snapshot(root)
    with pytest.raises(ValueError, match='legacy README.*customer_profile'):
        insights.validate_packet(root, 'a', draft)
    with pytest.raises(ValueError, match='legacy README.*customer_profile'):
        cases.publish_insights(root, 'a', draft, 'blocked-conversion', 'Reconcile legacy assessment')
    assert snapshot(root) == before
    # Use the supported owner workflow to review original evidence instead.
    source = case / 'market_research/pain_points/runs/old/report.md'
    research_workspace.update_stage(case, 'customer_profile', status='passed', gate_result='pass',
                                    artifacts=[source], expected_assessment_revision=1)
    cm = cases.case_manifest(root, 'a')
    assert 'README.md' in cm['artifacts']  # cumulative registration still needs retirement
    cases.publish_insights(root, 'a', conversion_packet(root), 'safe-conversion', 'Reconciled original sources')
    after = cases.case_manifest(root, 'a')
    assert 'README.md' not in after['artifacts']
    assert after['stages'] == cm['stages']
    assert not old.exists()
    assert (root / 'history/snapshots/safe-conversion/cases/a/README.md').read_bytes() == before['cases/a/README.md']
    cases.sources_current(root, after)
    assert insights.current_status(root, 'a')['status'] == 'current'


@pytest.mark.parametrize('consumer', ['case', 'question', 'plan', 'stage_artifact'])
def test_legacy_conversion_checks_other_current_consumers(tmp_path, consumer):
    root, case = setup_case(tmp_path)
    (case / 'README.md').write_text('# A\n\nEarlier interpretation that is still used by a current consumer.\n')
    binding = cases.source_binding(root, 'cases/a/README.md', locator='whole document', applicability='case a assessment')
    cm = cases.case_manifest(root, 'a')
    if consumer == 'case':
        cm['source_bindings'].append(binding)
    elif consumer == 'question':
        cm['coaching']['research_questions'].append({'id': 'legacy-answer', 'question': 'What was established?',
                                                    'status': 'answered', 'answer_binding': binding})
    elif consumer == 'stage_artifact':
        cm['stages']['customer_profile'] = {'artifacts': [{'path': 'README.md', 'type': 'md'}]}
    else:
        plan = root / 'strategy/strategy-plan.json'
        plan.parent.mkdir(exist_ok=True)
        plan.write_text(cases.encoded({'business_plan_sections': {'customer_market': {'source_bindings': [binding]}}}))
    cases.atomic(case / 'market_research/manifest.json', cases.encoded(cm))
    draft = conversion_packet(root)
    if consumer == 'question':
        draft['source_bindings'].append(binding)
        draft['question_coverage'].append({'id': 'legacy-answer', 'section': 'Customer and problem',
                                           'reason': 'The answer needs reconciliation with its original source.'})
    before = snapshot(root)
    with pytest.raises(ValueError, match='legacy README'):
        cases.publish_insights(root, 'a', draft, 'blocked-consumer', 'Convert legacy assessment')
    assert snapshot(root) == before


def assessed_number_case(tmp_path):
    root, case = setup_case(tmp_path)
    for folder in ('customer_segments', 'customer_journey'):
        path = case / 'market_research' / folder / 'notes.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Scoped source analysis with untested demand.')
    source = case / 'market_research/pain_points/figure.json'
    observation = {'value': '42.5', 'metric': 'observed_amount', 'period': 'FY2025',
                   'currency': 'EUR', 'unit': 'per case', 'scope': 'segment A'}
    source.write_text(json.dumps({'figure': observation}))
    binding = cases.source_binding(root, 'cases/a/market_research/pain_points/figure.json',
                                   locator='/figure', applicability='case a only')
    claim = {**observation, 'id': 'annex-amount', 'document': 'feasibility.md',
             'status': 'verified', 'source_binding': binding}
    cm = cases.case_manifest(root, 'a')
    cases.publish_assessment(root, 'a', {
        'assessment_revision': cm['assessment_revision'], 'manifest_revision': cm['manifest_revision'],
        'documents': {'feasibility.md': 'Observed amount {{source_numeric.annex-amount}}.'},
        'source_bindings': [binding], 'numeric_claims': [claim],
        'comparison': {'summary': 'Scoped customer problem remains provisional.',
                       'principal_uncertainty': 'Purchase behavior is not established.',
                       'next_action': 'Interview recent target customers.'}},
        'checked-appraisal', 'Publish the reviewed annex number')
    return root, case, source, claim


def packet_without_annex(root):
    draft = packet(root)
    for row in draft['coverage']:
        if row['path'].endswith('/feasibility.md'):
            row.update(disposition='no_material_finding', reason='This supporting amount is not used by the scoped customer assessment.')
            row.pop('section', None)
    return draft


def test_source_correction_retires_withdrawn_annex_claims_and_allows_insights(tmp_path):
    root, case, source, claim = assessed_number_case(tmp_path)
    draft = packet_without_annex(root)
    draft['document'] = draft['document'].replace('Pricing, capacity',
                                                  'An observed amount is {{source_numeric.brief-amount}} EUR per case in FY2025 for segment A. Pricing, capacity')
    draft['numeric_claims'] = [{**claim, 'id': 'brief-amount', 'document': 'case_insights.md'}]
    draft['source_bindings'].append(claim['source_binding'])
    refresh_review(root, draft)
    cases.publish_insights(root, 'a', draft, 'before-correction', 'Reviewed brief with an observed number')
    receipt_path = case / 'numeric-claims.json'
    prior_receipt = receipt_path.read_bytes()
    prior_claims = cases.load(receipt_path)['claims']
    source.write_text(source.read_text().replace('42.5', '24.5'))
    cases.correct(root, [], 'Transcription error: withdraw the previous annex amount',
                  'correct-amount', source_path='cases/a/market_research/pain_points/figure.json')
    assert (case / 'feasibility.md').read_text().startswith('# Review required')
    retained = cases.load(receipt_path)
    assert retained['claims'] == [c for c in prior_claims if c['document'] == 'case_insights.md']
    assert retained['verified_count'] == 1 and retained['unverified_count'] == 0
    assert (root / 'history/snapshots/correct-amount/cases/a/numeric-claims.json').read_bytes() == prior_receipt
    corrected = packet_without_annex(root)
    insights.validate_packet(root, 'a', corrected)
    cases.publish_insights(root, 'a', corrected, 'corrected-brief', 'Reviewed corrected source; old annex withdrawn')
    assert insights.current_status(root, 'a')['status'] == 'current'
    assert cases.load(receipt_path)['claims'] == []


def test_stale_number_in_unchanged_annex_still_blocks_insights(tmp_path):
    root, case, source, _ = assessed_number_case(tmp_path)
    source.write_text(source.read_text().replace('42.5', '24.5'))
    before = snapshot(root)
    with pytest.raises(ValueError, match='annex-amount: stale source binding'):
        cases.publish_insights(root, 'a', packet_without_annex(root), 'stale-annex', 'Unchanged annex still requires checking')
    assert snapshot(root) == before
    assert '42.5' in (case / 'feasibility.md').read_text()


def test_interrupted_correction_restores_annex_and_numeric_receipt(tmp_path, monkeypatch):
    root, case, _, _ = assessed_number_case(tmp_path)
    receipt_path = case / 'numeric-claims.json'
    receipt_before = receipt_path.read_bytes()
    annex_before = (case / 'feasibility.md').read_bytes()
    manifest_before = (case / 'market_research/manifest.json').read_bytes()
    original = cases.publish_locked

    def interrupted(*args, **kwargs):
        def fault(phase):
            if phase == 'replace' and receipt_path.read_bytes() != receipt_before:
                raise RuntimeError('interrupted after numeric receipt replacement')
        kwargs['fault'] = fault
        return original(*args, **kwargs)

    monkeypatch.setattr(cases, 'publish_locked', interrupted)
    with pytest.raises(RuntimeError, match='numeric receipt replacement'):
        cases.correct(root, ['a'], 'Withdraw incorrect annex', 'interrupted-correction')
    assert cases.recover(root) == 'rolled_back'
    assert receipt_path.read_bytes() == receipt_before
    assert (case / 'feasibility.md').read_bytes() == annex_before
    assert (case / 'market_research/manifest.json').read_bytes() == manifest_before
