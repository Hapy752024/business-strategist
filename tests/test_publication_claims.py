import json
import hashlib

import pytest

from scripts import case_workspace as cases
from scripts.publication_claims import render, bundle_digest, check_separate_review, check_numeric_citations
from scripts import validate_case_insights as insights
from test_case_insights import setup_case, packet


def reviewed_claim(tmp_path):
    root = tmp_path / 'venture'
    cases.initialize(root, 'Venture')
    cases.add_case(root, 'a', 'A')
    pack = root / 'cases/a/market_research/pain_points/runs/one/customer-feedback'
    pack.mkdir(parents=True)
    (pack / 'claim-ledger.json').write_text(json.dumps([{
        'claim_id': 'wait', 'supporting_evidence': ['e1'],
        'verification': {'support_assessment': 'supported'}}]))
    (pack / 'evidence.jsonl').write_text(json.dumps({
        'evidence_id': 'e1', 'source_url': 'https://example.org/review/1',
        'text': 'A customer reported a long wait.'}) + '\n')
    (pack / 'source-review.json').write_text(json.dumps({'reviews': [{
        'evidence_id': 'e1', 'source_url': 'https://example.org/review/1',
        'status': 'accepted'}]}))
    bindings = [cases.source_binding(root, str(path.relative_to(root)),
                   locator='e1', applicability='case a customer wait')
                for path in sorted(pack.iterdir())]
    ref = {'id': 'wait_source', 'document': 'case_insights.md', 'claim_id': 'wait',
           'evidence_id': 'e1', 'ledger_binding': next(b for b in bindings if b['path'].endswith('claim-ledger.json')),
           'source_kind': 'original', 'limitation': ''}
    return root, pack, bindings, ref


def test_reviewed_original_link_is_rendered_at_claim(tmp_path):
    root, _, bindings, ref = reviewed_claim(tmp_path)
    body = 'A customer reported a long wait {{evidence_claim.wait_source}}.'
    rendered = render(root, {'case_insights.md': body}, [ref], bindings)['case_insights.md']
    assert '[Source: e1](https://example.org/review/1)' in rendered
    with pytest.raises(ValueError, match='marker'):
        render(root, {'case_insights.md': body}, [], bindings)


def test_unreviewed_or_stale_source_cannot_be_laundered(tmp_path):
    root, pack, bindings, ref = reviewed_claim(tmp_path)
    body = 'Long wait {{evidence_claim.wait_source}}'
    review_file = pack / 'source-review.json'
    review_file.write_text(review_file.read_text().replace('/review/1', '/home'))
    with pytest.raises(ValueError, match='current bindings'):
        render(root, {'case_insights.md': body}, [ref], bindings)
    bindings = [cases.source_binding(root, b['path'], locator=b['locator'], applicability=b['applicability'])
                for b in bindings]
    with pytest.raises(ValueError, match='not accepted'):
        render(root, {'case_insights.md': body}, [ref], bindings)


def test_secondary_limitation_and_private_reference(tmp_path):
    root, _, bindings, ref = reviewed_claim(tmp_path)
    body = 'A report described a wait {{evidence_claim.wait_source}}'
    ref['source_kind'] = 'secondary'
    ref['limitation'] = 'The original account could not be inspected.'
    assert 'secondary account:' in render(root, {'case_insights.md': body}, [ref], bindings)['case_insights.md']
    ref['source_kind'] = 'private'
    assert 'https://' not in render(root, {'case_insights.md': body}, [ref], bindings)['case_insights.md']


def test_contextual_original_citation_requires_retained_exact_passage(tmp_path):
    root, _, _, _ = reviewed_claim(tmp_path)
    run = root / 'cases/a/market_research/pain_points/runs/official'
    raw = run / 'raw/authority.md'
    raw.parent.mkdir(parents=True)
    raw.write_text('Official report: late payments were observed among surveyed construction firms.')
    manifest = run / 'manual-captures.json'
    manifest.write_text(json.dumps({'captures': [{'capture_path': 'raw/authority.md',
        'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
        'retrieved_at': '2026-09-26T08:00:00Z',
        'source_url': 'https://authority.example/report'}]}))
    binding = cases.source_binding(root, str(manifest.relative_to(root)),
                                   locator='/captures/0', applicability='case a contextual source')
    ref = {'id': 'official_wait', 'document': 'case_insights.md', 'capture_binding': binding,
           'capture_index': 0, 'supporting_passage': 'late payments were observed among surveyed construction firms',
           'source_kind': 'original', 'limitation': ''}
    body = 'A survey reported late payments {{evidence_claim.official_wait}}.'
    assert '[Source: 2026-09-26](https://authority.example/report)' in render(
        root, {'case_insights.md': body}, [ref], [binding])['case_insights.md']
    ref['supporting_passage'] = 'unrelated homepage sentence'
    with pytest.raises(ValueError, match='passage'):
        render(root, {'case_insights.md': body}, [ref], [binding])
    ref['supporting_passage'] = 'late payments were observed among surveyed construction firms'
    raw.write_text('Updated report without the old passage.')
    with pytest.raises(ValueError, match='capture changed'):
        render(root, {'case_insights.md': body}, [ref], [binding])


def test_verified_observed_figure_needs_adjacent_captured_source():
    claim = {'id': 'amount', 'document': 'case_insights.md', 'status': 'verified',
             'value': '42', 'period': 'FY2025'}
    body = 'The report shows {{source_numeric.amount}} units in FY2025 {{evidence_claim.amount_source}}.'
    ref = {'id': 'amount_source', 'document': 'case_insights.md', 'numeric_claim_id': 'amount',
           'capture_binding': {}, 'supporting_passage': '42 units in FY2025'}
    check_numeric_citations({'case_insights.md': body}, [claim], [ref])
    ref['supporting_passage'] = '42 units in FY2024'
    with pytest.raises(ValueError, match='retain value and period'):
        check_numeric_citations({'case_insights.md': body}, [claim], [ref])


def test_separate_review_bound_to_exact_output_and_sources(tmp_path):
    root, _, bindings, _ = reviewed_claim(tmp_path)
    digest = bundle_digest({'case.md': '# First\n'}, bindings)
    record_path = root / 'cases/a/market_research/appraisal/reviews/independent.json'
    record_path.parent.mkdir(parents=True)
    record_path.write_text(json.dumps({'author': 'writer-task', 'reviewer': 'review-task',
        'review_task_id': 'independent-1', 'bundle_digest': digest,
        'reviewed_sources': sorted(b['path'] + '#' + b['digest'] for b in bindings),
        'outcome': 'pass', 'material_findings': []}))
    binding = cases.source_binding(root, str(record_path.relative_to(root)), locator='whole review', applicability='case a')
    check_separate_review(root, 'a', binding, digest, bindings, 'cases/a/market_research/appraisal/reviews/')
    with pytest.raises(ValueError, match='exact rendered'):
        check_separate_review(root, 'a', binding, bundle_digest({'case.md': '# Changed\n'}, bindings),
                              bindings, 'cases/a/market_research/appraisal/reviews/')


def test_complete_insights_v2_renders_source_and_requires_fresh_separate_review(tmp_path):
    root, case = setup_case(tmp_path)
    draft = packet(root)
    pack = case / 'market_research/pain_points/runs/new/customer-feedback'
    pack.mkdir(parents=True)
    (pack / 'claim-ledger.json').write_text(json.dumps([{'claim_id': 'wait',
        'supporting_evidence': ['e1'], 'verification': {'support_assessment': 'supported'}}]))
    (pack / 'evidence.jsonl').write_text(json.dumps({'evidence_id': 'e1',
        'source_url': 'https://example.org/review/1', 'text': 'A customer reported a long wait.'}) + '\n')
    (pack / 'source-review.json').write_text(json.dumps({'reviews': [{'evidence_id': 'e1',
        'source_url': 'https://example.org/review/1', 'status': 'accepted'}]}))
    bindings = [cases.source_binding(root, str(path.relative_to(root)), locator='e1',
                              applicability='case a reviewed customer experience') for path in pack.iterdir()]
    draft['source_bindings'].extend(bindings)
    rows = insights.inventory(root, 'a', source_bindings=draft['source_bindings'])
    old = {row['path']: row for row in draft['coverage']}
    draft['coverage'] = [old[row['path']] if row['path'] in old else {
        'path': row['path'], 'digest': row['digest'], 'disposition': 'incorporated',
        'reason': 'Reviewed customer account directly supports the scoped wait statement.',
        'section': 'Customer and problem'} for row in rows]
    draft['document'] = draft['document'].replace(
        'One customer in segment A described a repeated two-week wait.',
        'One customer in segment A described a repeated two-week wait {{evidence_claim.wait_source}}.')
    draft['publication_contract_version'] = 2
    draft['publication_claims'] = [{'id': 'wait_source', 'document': 'case_insights.md',
        'claim_id': 'wait', 'evidence_id': 'e1',
        'ledger_binding': next(b for b in bindings if b['path'].endswith('claim-ledger.json')),
        'source_kind': 'original', 'limitation': ''}]
    rendered = insights._body(root, 'a', draft)
    inventory_hash = insights.inventory_digest(root, 'a', rows=rows)
    draft['review']['rendered_digest'] = insights.sha(rendered.encode())
    draft['review']['inventory_digest'] = inventory_hash
    review_path = case / 'market_research/case_insights/reviews/independent.json'
    review_path.parent.mkdir(parents=True)
    review_path.write_text(json.dumps({'author': 'author-task', 'reviewer': 'reviewer-task',
        'review_task_id': 'review-a', 'rendered_digest': insights.sha(rendered.encode()),
        'inventory_digest': inventory_hash, 'outcome': 'pass', 'material_findings': [],
        'reviewed_sources': sorted(b['path'] + '#' + b['digest'] for b in draft['source_bindings'])}))
    draft['independent_review'] = cases.source_binding(root, str(review_path.relative_to(root)),
                                                      locator='whole review', applicability='case a final review')
    assert insights.validate_packet(root, 'a', draft)[0] == rendered
    cases.publish_insights(root, 'a', draft, 'v2-insights', 'Publish cited reviewed case')
    assert insights.current_status(root, 'a')['quality_status'] == 'v2_final_reviewed'
    assert '[Source: e1](https://example.org/review/1)' in (case / 'case_insights.md').read_text()
    review_path.write_text(review_path.read_text().replace('reviewer-task', 'changed-reviewer'))
    assert insights.current_status(root, 'a')['status'] == 'invalid'
