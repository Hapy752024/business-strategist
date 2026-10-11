"""Publish provisional plans for registered cases through the shared transaction."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator

from scripts import case_workspace as cases
from scripts.business_plan_render import SECTIONS, financial_tables

SCHEMA = json.loads((cases.ROOT / 'schemas/case-business-plan.schema.json').read_text())


def review_inputs(record):
    return {key: record[key] for key in SCHEMA['properties'] if key in record and key != 'independent_review'}


def review_content(case_id, body, record):
    return {f'cases/{case_id}/business-plan.md': body,
            f'cases/{case_id}/business-plan.inputs.json': cases.encoded(review_inputs(record))}


def current(root, case_id, *, require_final=False):
    from scripts.validate_case_insights import current_status
    root = Path(root).absolute()
    path = cases.resolve(root, case_id) / 'business-plan.json'
    if not path.is_file():
        raise ValueError('case business plan is missing')
    record = cases.load(path)
    cm = cases.case_manifest(root, case_id)
    if record.get('authored_digest') != cases.digest(cases.encoded(review_inputs(record)).encode()):
        raise ValueError('case business plan structured inputs changed')
    body = path.with_suffix('.md')
    insight = cases.resolve(root, case_id) / 'case_insights.md'
    if (record.get('state') != 'current' or record.get('case_id') != case_id
            or record.get('assessment_revision') != cm['assessment_revision']
            or current_status(root, case_id).get('status') != 'current'
            or not insight.is_file() or record.get('insights_digest') != cases.digest(insight.read_bytes())
            or not body.is_file() or record.get('document_digest') != cases.digest(body.read_bytes())):
        raise ValueError('case business plan needs review after changed case inputs')
    cases.sources_current(root, record)
    econ = cases.resolve(root, case_id) / 'economics.json'
    model_digest = cases.load(econ)['input_digest'] if econ.is_file() else None
    if record.get('economics_input_digest') != model_digest:
        raise ValueError('case business plan economics changed')
    if require_final:
        from scripts.publication_claims import bundle_digest, check_separate_review
        if record.get('publication_status') != 'final':
            raise ValueError('case business plan needs final review')
        check_separate_review(root, case_id, record.get('independent_review'),
                              bundle_digest(review_content(case_id, body.read_text(), record), record['source_bindings']),
                              record['source_bindings'], f'cases/{case_id}/plan-reviews/')
    return record


def publish(root, case_id, packet, decision_id, reason, *, preview=False):
    from scripts.validate_case_insights import current_status
    from scripts.evidence_scout.validate_research_completion import initial_case_evidence
    from scripts.economics_text import render as render_economics
    from scripts.verify_numeric_claims import checked_claims
    from scripts.publication_claims import render, check_numeric_citations, bundle_digest, check_separate_review
    root = Path(root).absolute()
    with cases.project_lock(root):
        errors = list(Draft202012Validator(SCHEMA).iter_errors(packet))
        if errors:
            raise ValueError('invalid case plan: ' + errors[0].message)
        cm, project = cases.case_manifest(root, case_id), cases.read_project(root)
        scope = cases.resolve(root, case_id)
        if packet['case_id'] != case_id or packet['assessment_revision'] != cm['assessment_revision'] or packet['manifest_revision'] != cm['manifest_revision']:
            raise ValueError('case plan revision conflict')
        existing = scope / 'business-plan.json'
        if packet['publication_base_digest'] != (cases.digest(existing.read_bytes()) if existing.is_file() else None):
            raise ValueError('case plan publication conflict')
        if current_status(root, case_id).get('status') != 'current':
            raise ValueError('current reviewed case insights required')
        insight_digest = cases.digest((scope / 'case_insights.md').read_bytes())
        if packet['insights_digest'] != insight_digest:
            raise ValueError('case plan insights changed')
        sections = packet['business_plan_sections']
        bindings = list(packet['source_bindings'])
        for row in sections.values():
            for binding in row.get('source_bindings', []):
                if binding not in bindings:
                    bindings.append(binding)
        for binding in bindings:
            if binding['path'] in {f'cases/{case_id}/business-plan.md', f'cases/{case_id}/business-plan.json'}:
                raise ValueError('case plan cannot cite itself')
            if binding != cases.source_binding(root, binding['path'], locator=binding['locator'], applicability=binding['applicability']):
                raise ValueError('case plan source changed')
        evidence = initial_case_evidence(root, case_id, bindings)
        if evidence['status'] != 'eligible' or not any(row['claim_ledger'] in {b['path'] for b in bindings} for row in evidence['eligible_runs']):
            raise ValueError('case plan requires an eligible reviewed case run and bound claim ledger')
        econ_path = scope / 'economics.json'
        economics = cases.load(econ_path) if econ_path.is_file() else None
        if packet['economics_input_digest'] != (economics['input_digest'] if economics else None):
            raise ValueError('case plan economics digest changed')
        texts = {'section.' + key: sections[key]['text'] for key in SECTIONS}
        check_numeric_citations(texts, packet['numeric_claims'], packet['publication_claims'])
        texts, receipt = checked_claims(root, texts, packet['numeric_claims'], bindings)
        texts = {key: render_economics(text, economics, packet['economics_input_digest']) for key, text in texts.items()}
        texts = render(root, texts, packet['publication_claims'], bindings)
        lines = ['# Business plan: ' + case_id, '', 'Last updated: ' + cases.now()[:10], '',
                 'Evidence maturity: ' + packet['evidence_maturity'], '',
                 'Publication: ' + packet['publication_status'] + '. Business execution retains its separate gates.', '']
        for key in SECTIONS:
            row = sections[key]
            if row['status'] == 'supported' and not row.get('source_bindings'):
                raise ValueError('supported section requires source bindings: ' + key)
            if row['status'] in {'missing', 'not_applicable'} and not row.get('next_action'):
                raise ValueError('section requires gap explanation and next action: ' + key)
            lines += ['## ' + key.replace('_', ' ').title(), '', 'Status: ' + row['status'], '', texts['section.' + key], '']
            if row.get('next_action'):
                lines += ['Next action: ' + row['next_action'], '']
        lines += [financial_tables(economics), '## Source appendix', '',
                  *['- `' + b['path'] + '#' + b['locator'] + '` — ' + b['applicability'] for b in bindings], '']
        body = '\n'.join(lines)
        authored = {**copy.deepcopy(packet), 'source_bindings': bindings}
        content = review_content(case_id, body, authored)
        review_hash = bundle_digest(content, bindings)
        if preview:
            return {'outputs': content, 'bundle_digest': review_hash, 'reviewed_sources': sorted(b['path'] + '#' + b['digest'] for b in bindings)}
        if packet['publication_status'] == 'final':
            check_separate_review(root, case_id, packet.get('independent_review'), review_hash, bindings, f'cases/{case_id}/plan-reviews/')
        content.pop(f'cases/{case_id}/business-plan.inputs.json')
        record = {**authored, 'state': 'current', 'source_bindings': bindings,
                  'document_digest': cases.digest(body.encode()), 'numeric_receipt': receipt, 'published_at': cases.now()}
        record['authored_digest'] = cases.digest(cases.encoded(review_inputs(record)).encode())
        content[f'cases/{case_id}/business-plan.json'] = cases.encoded(record)
        updated = copy.deepcopy(cm)
        updated['manifest_revision'] += 1
        updated['case_business_plan'] = {'state': 'current', 'document_digest': record['document_digest'],
                                         'assessment_revision': cm['assessment_revision'], 'publication_status': packet['publication_status']}
        updated['case_plan_contract_version'] = 1
        content[f'cases/{case_id}/market_research/manifest.json'] = cases.encoded(updated)
        if (project.get('selection') or {}).get('case_id') == case_id:
            content.update(cases.mark_plan_review(root, 'Selected case business plan changed'))
        return cases.publish_locked(root, content, expected_revision=project['manifest_revision'], decision_id=decision_id, reason=reason, affected=[case_id])
