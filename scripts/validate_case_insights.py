#!/usr/bin/env python3
"""Inventory and validate the current, reader-facing case synthesis.

Mechanical checks prove coverage declarations and binding freshness. The semantic
review recorded in the packet remains a human/agent judgment, not a text matcher.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from scripts import case_workspace as cases
    from scripts.economics_text import render as render_economics
    from scripts.verify_numeric_claims import checked_claims
except ModuleNotFoundError:
    import case_workspace as cases
    from economics_text import render as render_economics
    from verify_numeric_claims import checked_claims

NAME = 'case_insights.md'
HEADINGS = ('Executive assessment', 'Customer and problem', 'Market and demand',
            'Alternatives and competitive position', 'Business potential and feasibility',
            'Risks, conflicting evidence and open questions', 'Recommended next decisions', 'Sources')
DISPOSITIONS = {'incorporated', 'superseded', 'duplicate', 'no_material_finding', 'out_of_scope', 'pending'}
REVIEW_CHECKS = {'accuracy', 'completeness', 'contradictions', 'clarity'}
REVIEW_TYPES = {'analyst', 'independent_human', 'model'}
REVIEW_MODES = {'inline', 'fresh_context', 'independent_review'}
TECHNICAL_NAMES = {'manifest.json', 'run-manifest.json', 'raw.json', 'summary.json',
                   'numeric-claims.json', 'economics.json', 'research-query-plan.json'}


def shared_applies(case_id: str, applicability: str) -> bool:
    return bool(isinstance(applicability, str) and re.search(
        r'\bcase(?:[_ -]?id)?[:= -]+' + re.escape(case_id) + r'(?![a-z0-9_-])', applicability, re.I))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checked_path(root: Path, path: str, case_id: str) -> Path:
    if not isinstance(path, str) or not path.startswith((f'cases/{case_id}/', 'market_research/')):
        raise ValueError('insights input must be case-local or explicitly shared')
    return cases.safe(root, path)


def inventory(root: Path, case_id: str, *, manifest: dict | None = None,
              source_bindings: list | None = None, include_previous: bool = True) -> list[dict]:
    """Discover every local narrative output, including unregistered deep dives."""
    root = Path(root).absolute()
    scope = cases.resolve(root, case_id)
    manifest = manifest or cases.case_manifest(root, case_id)
    candidates = set()
    for path in (scope / 'market_research').rglob('*'):
        if not path.is_file() and not path.is_symlink():
            continue
        rel = path.relative_to(scope)
        parts = rel.parts
        if (path.name.startswith('.') or any(part.startswith('.') for part in parts)
                or 'raw' in parts or 'case_insights' in parts or path.name in TECHNICAL_NAMES):
            continue
        if path.suffix.lower() in {'.md', '.json', '.jsonl', '.csv'}:
            candidates.add(str(path.relative_to(root)))
    # Supporting assessments remain inputs; an old case README is reconciled once.
    for name in ('feasibility.md', 'business-case.md'):
        path = scope / name
        if path.exists() or path.is_symlink():
            candidates.add(str(path.relative_to(root)))
    if manifest.get('insights', {}).get('state') in {None, 'draft'}:
        path = scope / 'README.md'
        if path.exists() or path.is_symlink():
            candidates.add(str(path.relative_to(root)))
    for item in manifest.get('artifacts', []):
        if not isinstance(item, str):
            raise ValueError('invalid research artifact path')
        path = scope / item
        if 'raw' not in path.parts and path.suffix.lower() in {'.md', '.json', '.jsonl', '.csv'}:
            candidates.add(str(path.relative_to(root)))
    # Only explicit case applicability admits shared research. Keep all declared
    # contexts, even when several stages use different passages of the same file.
    declared = list(manifest.get('source_bindings', []))
    for stage in manifest.get('stages', {}).values():
        declared.extend(stage.get('source_bindings', []))
    for question in manifest.get('coaching', {}).get('research_questions', []):
        if question.get('answer_binding'):
            declared.append(question['answer_binding'])
    if include_previous:
        declared.extend(cases.insights_bindings(root, manifest))
    declared.extend(source_bindings or [])
    shared = {}
    for binding in declared:
        if not isinstance(binding, dict) or not isinstance(binding.get('path'), str):
            raise ValueError('invalid declared research binding')
        rel = binding['path']
        if rel.startswith('cases/') and not rel.startswith(f'cases/{case_id}/'):
            raise ValueError('insights cannot consume another case directly')
        if not rel.startswith('market_research/'):
            continue
        if (set(binding) != {'path', 'digest', 'locator', 'applicability'}
                or not isinstance(binding['locator'], str) or not binding['locator'].strip()
                or not shared_applies(case_id, binding['applicability'])):
            raise ValueError('shared source needs explicit case applicability and locator')
        candidates.add(rel)
        shared.setdefault(rel, {})[cases.encoded(binding)] = binding
    # A run's machine-generated derivatives are one review unit. Their member
    # paths and digests remain bound below, so grouping reduces human work
    # without hiding changes or removing source-level provenance.
    machine_suffixes = {'.json', '.jsonl', '.csv'}
    grouped: dict[str, list[str]] = {}
    for rel in list(candidates):
        path = _checked_path(root, rel, case_id)
        if path.suffix.lower() in machine_suffixes and path.parent != scope:
            directory = str(path.parent.relative_to(root))
            grouped.setdefault(directory, []).append(rel)
    group_rows = {}
    for directory, members in grouped.items():
        if len(members) < 3:
            continue
        member_rows = []
        for member in sorted(members):
            path = _checked_path(root, member, case_id)
            member_rows.append({'path': member, 'digest': sha(path.read_bytes()) if path.is_file() else None})
            candidates.discard(member)
        marker = directory + '/@derived-artifacts'
        group_digest = sha(json.dumps(member_rows, sort_keys=True, separators=(',', ':')).encode())
        group_rows[marker] = {'path': marker, 'digest': group_digest, 'kind': 'derived_group', 'members': member_rows}
    rows = []
    for rel in sorted(candidates):
        path = _checked_path(root, rel, case_id)
        if not path.is_file():
            rows.append({'path': rel, 'digest': None, 'kind': 'missing'})
        else:
            rows.append({'path': rel, 'digest': sha(path.read_bytes()),
                         'kind': 'shared_research' if rel in shared else
                                 'prior_narrative' if path.parent == scope else 'research_output'})
        if rel in shared:
            rows[-1]['bindings'] = [shared[rel][key] for key in sorted(shared[rel])]
    rows.extend(group_rows.values())
    return sorted(rows, key=lambda row: row['path'])


def inventory_digest(root: Path, case_id: str, *, manifest: dict | None = None,
                     rows: list[dict] | None = None) -> str:
    manifest = manifest or cases.case_manifest(root, case_id)
    rows = rows if rows is not None else inventory(root, case_id, manifest=manifest)
    economics = cases.resolve(root, case_id) / 'economics.json'
    material = {'case_id': case_id, 'assessment_revision': manifest['assessment_revision'],
                'sources': rows,
                'research_assignment': manifest.get('research_assignment'),
                'coaching': {key: manifest.get('coaching', {}).get(key)
                             for key in ('known_answers', 'unresolved_inputs', 'pending_question', 'research_questions')},
                'economics_digest': sha(economics.read_bytes()) if economics.is_file() else None}
    return sha(json.dumps(material, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':')).encode())


def _body(root: Path, case_id: str, packet: dict) -> str:
    if not isinstance(packet.get('document'), str):
        raise ValueError('insights document must be a string')
    text = packet['document']
    bindings = packet.get('source_bindings', [])
    if not isinstance(bindings, list):
        raise ValueError('source_bindings must be a list')
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {'path', 'digest', 'locator', 'applicability'}:
            raise ValueError('invalid source binding')
        if binding['path'].startswith(f'cases/{case_id}/') and Path(binding['path']).name == NAME:
            raise ValueError('insights cannot cite itself')
        if binding['path'].startswith('cases/') and not binding['path'].startswith(f'cases/{case_id}/'):
            raise ValueError('insights cannot consume another case directly')
        if not binding['path'].startswith((f'cases/{case_id}/', 'market_research/')):
            raise ValueError('insights source must be case-local or shared research')
        if binding != cases.source_binding(root, binding['path'], locator=binding['locator'],
                                           applicability=binding['applicability']):
            raise ValueError('stale source binding: ' + binding['path'])
        if not binding['path'].startswith(f'cases/{case_id}/'):
            if not shared_applies(case_id, binding['applicability']):
                raise ValueError('shared source needs explicit case applicability')
    claims = packet.get('numeric_claims', [])
    if not isinstance(claims, list) or any(c.get('document') != NAME for c in claims):
        raise ValueError('insights numeric claims must target case_insights.md')
    if packet.get('publication_contract_version') == 2:
        try:
            from scripts.publication_claims import check_numeric_citations
        except ModuleNotFoundError:
            from publication_claims import check_numeric_citations
        check_numeric_citations({NAME: text}, claims, packet.get('publication_claims', []))
    economics = cases.resolve(root, case_id) / 'economics.json'
    if economics.is_file():
        try:
            from scripts.case_economics import validate
        except ModuleNotFoundError:
            from case_economics import validate
        model = cases.load(economics)
        validate(model)
        text = render_economics(text, model, packet.get('economics_input_digest'))
    elif '{{economics.' in text:
        raise ValueError('economics references require a model')
    rendered, _ = checked_claims(root, {NAME: text}, claims, bindings)
    text = rendered[NAME]
    if packet.get('publication_contract_version') == 2:
        try:
            from scripts.publication_claims import render as render_claims
        except ModuleNotFoundError:
            from publication_claims import render as render_claims
        text = render_claims(root, {NAME: text}, packet.get('publication_claims', []), bindings)[NAME]
    if packet.get('scope_status') == 'progress':
        summary = str(packet.get('pending_summary') or '').strip()
        if not summary:
            raise ValueError('progress publication needs a plain-language account of remaining questions')
        marker = '\n## Sources\n'
        if marker not in text:
            raise ValueError('progress publication needs a Sources section')
        text = text.replace(marker, '\nResearch is continuing: ' + summary + '\n' + marker, 1)
    # The receipt keeps claim IDs; the founder sees the uncertainty in prose.
    text = re.sub(r'\[unverified numeric value: [a-z][a-z0-9_-]*\]',
                  '[figure not established]', text)
    return text


def _validate_content(text: str, title: str) -> None:
    if not text.startswith('# ' + title + '\n'):
        raise ValueError('insights title must match registered case')
    if not re.search(r'^Last updated: \d{4}-\d{2}-\d{2}$', text, re.M):
        raise ValueError('insights need a dated assessment')
    for heading in HEADINGS:
        if not re.search(r'^## ' + re.escape(heading) + r'$', text, re.M):
            raise ValueError('missing insights section: ' + heading)
    if re.search(r'\{\{[^}]+\}\}|<!--|-->|\b(?:TODO|TBD|PLACEHOLDER)\b|Economics input digest:|Calculated contribution per unit:', text, re.I):
        raise ValueError('insights contain an authoring placeholder or technical footer')
    if re.search(r'\b(?:manifest|source[_ -]?bindings?|run[_ -]?id|provider status|validation receipt|assessment_revision|skill coverage)\b', text, re.I):
        raise ValueError('insights contain internal research workflow language')
    if len(text.strip()) < 350:
        raise ValueError('insights too thin to explain the case')


def _validate_links(root: Path, case_id: str, text: str, *, has_sources: bool) -> None:
    scope = cases.resolve(root, case_id)
    source_section = text.split('## Sources\n', 1)[-1]
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', source_section)
    if has_sources and not links:
        raise ValueError('insights sources need at least one usable link')
    for target in links:
        link = target.split('#', 1)[0]
        if re.match(r'^https?://', link):
            continue
        if not link or re.match(r'^[a-z]+:', link, re.I) or link.startswith('/'):
            raise ValueError('unsupported insights source link')
        # Walk before collapsing '..': resolving first would hide symlinks such
        # as link/../source.md and bypass the existing no-symlink contract.
        path = scope
        for component in Path(link).parts:
            path = path.parent if component == '..' else path / component
            if not path.is_relative_to(root):
                raise ValueError('insights source link escapes workspace')
            if path.is_symlink():
                raise ValueError('insights source links must not use symlinks')
        path = cases.safe(root, str(path.relative_to(root)))
        if not path.is_file():
            raise ValueError('broken insights source link: ' + target)


def validate_packet(root: Path, case_id: str, packet: dict, *, manifest: dict | None = None) -> tuple[str, list[dict], str]:
    root = Path(root).absolute()
    cm = manifest or cases.case_manifest(root, case_id)
    project = cases.read_project(root)
    expected = {'assessment_revision', 'manifest_revision', 'document', 'source_bindings',
                'coverage', 'question_coverage', 'conflicts', 'review', 'numeric_claims',
                'economics_input_digest', 'impact', 'comparison', 'scope_status', 'pending_summary',
                'publication_contract_version', 'publication_claims', 'independent_review'}
    if not isinstance(packet, dict) or set(packet) - expected:
        raise ValueError('unknown insights publication fields')
    if packet.get('assessment_revision') != cm['assessment_revision'] or packet.get('manifest_revision') != cm['manifest_revision']:
        raise ValueError('stale case assessment or manifest revision')
    cases.check_legacy_insights_conversion(root, case_id, cm)
    if packet.get('impact') not in {'presentation_only', 'reviewed_findings'}:
        raise ValueError('insights impact must be explicitly classified')
    if packet.get('scope_status', 'complete') not in {'progress', 'complete'}:
        raise ValueError('insights scope_status must be progress or complete')
    if packet.get('scope_status') == 'progress' and (
            not isinstance(packet.get('pending_summary'), str) or len(packet['pending_summary'].strip()) < 20):
        raise ValueError('progress publication must state the remaining research scope in plain language')
    if packet.get('impact') == 'reviewed_findings' and cm.get('comparison'):
        raise ValueError('changed assessed conclusions require case-appraisal or correction')
    comparison = packet.get('comparison')
    if comparison is None and not cm.get('comparison'):
        raise ValueError('first insights publication needs a case comparison summary')
    if comparison is not None:
        if (not isinstance(comparison, dict) or set(comparison) != {'summary', 'principal_uncertainty', 'next_action'}
                or any(not isinstance(value, str) or len(value.strip()) < 10 or '{{' in value for value in comparison.values())):
            raise ValueError('insights comparison needs three substantive plain-language fields')
        if cm.get('comparison') and any(cm['comparison'][key] != comparison[key] for key in comparison):
            raise ValueError('changing an assessed comparison requires case-appraisal')
    text = _body(root, case_id, packet)
    rows = inventory(root, case_id, manifest=cm, source_bindings=packet.get('source_bindings', []))
    inv_digest = inventory_digest(root, case_id, manifest=cm, rows=rows)
    _validate_content(text, project['cases'][case_id]['title'])
    _validate_links(root, case_id, text, has_sources=bool(packet.get('source_bindings')))
    coverage = packet.get('coverage')
    if not isinstance(coverage, list) or len(coverage) != len(rows):
        raise ValueError('every inventoried research output needs a disposition')
    by_path = {}
    for item in coverage:
        if not isinstance(item, dict) or set(item) - {'path', 'digest', 'disposition', 'reason', 'section', 'replacement'}:
            raise ValueError('invalid research coverage row')
        path = item.get('path')
        if not isinstance(path, str) or path in by_path:
            raise ValueError('duplicate or invalid research coverage path')
        by_path[path] = item
        if item.get('disposition') not in DISPOSITIONS or not isinstance(item.get('reason'), str) or len(item['reason'].strip()) < 15:
            raise ValueError('research coverage needs a reasoned disposition')
        if item['disposition'] == 'incorporated':
            section = item.get('section')
            if section not in HEADINGS or not isinstance(section, str):
                raise ValueError('incorporated output needs a substantive insights section')
            member_paths = {member['path'] for row in rows if row['path'] == path for member in row.get('members', [])}
            if not any(b['path'] == path or b['path'] in member_paths for b in packet['source_bindings']):
                raise ValueError('incorporated output needs a current source binding')
        if item['disposition'] == 'superseded' and not isinstance(item.get('replacement'), str):
            raise ValueError('superseded output needs a replacement path')
    expected_rows = {r['path']: r['digest'] for r in rows}
    known_sources = set(expected_rows) | {member['path'] for row in rows for member in row.get('members', [])}
    if {p: r.get('digest') for p, r in by_path.items()} != expected_rows:
        raise ValueError('research inventory changed or a run was omitted')
    for item in coverage:
        if item['disposition'] == 'pending' and packet.get('scope_status') != 'progress':
            raise ValueError('complete publication cannot leave research inputs pending')
        if item.get('replacement') and (item['replacement'] not in known_sources or item['replacement'] == item['path']):
            raise ValueError('invalid superseding research output')
        allowed_missing = {'no_material_finding', 'out_of_scope'} | ({'pending'} if packet.get('scope_status') == 'progress' else set())
        if expected_rows[item['path']] is None and item['disposition'] not in allowed_missing:
            raise ValueError('missing research output cannot be incorporated')
    questions = {q['id']: q for q in cm.get('coaching', {}).get('research_questions', [])}
    question_coverage = packet.get('question_coverage')
    if not isinstance(question_coverage, list) or len(question_coverage) != len(questions):
        raise ValueError('every persisted research question needs coverage')
    qseen = set()
    for row in question_coverage:
        if not isinstance(row, dict) or set(row) != {'id', 'section', 'reason'} or row.get('id') not in questions or row['id'] in qseen:
            raise ValueError('invalid or duplicate question coverage')
        qseen.add(row['id'])
        if row['section'] not in HEADINGS or not isinstance(row['reason'], str) or len(row['reason'].strip()) < 15:
            raise ValueError('question coverage needs a section and reason')
        q = questions[row['id']]
        if q['status'] in {'answered', 'partial'} and q.get('answer_binding') not in packet['source_bindings']:
            raise ValueError('answered question needs its source in insights bindings')
    conflicts = packet.get('conflicts')
    if not isinstance(conflicts, list):
        raise ValueError('conflicts must be a reviewed list')
    for conflict in conflicts:
        if not isinstance(conflict, dict) or set(conflict) != {'left', 'right', 'scope', 'resolution', 'rationale', 'section'}:
            raise ValueError('invalid conflict review row')
        if (conflict['left'] not in known_sources or conflict['right'] not in known_sources
                or conflict['left'] == conflict['right'] or conflict['section'] not in HEADINGS
                or conflict['resolution'] not in {'corrected', 'scope_qualified', 'historical_superseded', 'unresolved_disclosed'}
                or not isinstance(conflict['scope'], str) or not conflict['scope'].strip()
                or not isinstance(conflict['rationale'], str) or len(conflict['rationale'].strip()) < 20):
            raise ValueError('conflict needs source pairs, scope, resolution and document section')
    review = packet.get('review')
    validate_review(review)
    if review['rendered_digest'] != sha(text.encode()) or review['inventory_digest'] != inv_digest:
        raise ValueError('stale or incomplete semantic review')
    if packet.get('publication_contract_version') == 2 and packet.get('scope_status', 'complete') == 'complete':
        validate_independent_review(root, case_id, packet.get('independent_review'), text, inv_digest,
                                    packet.get('source_bindings', []))
    return text, rows, inv_digest


def validate_independent_review(root: Path, case_id: str, binding: dict | None,
                                text: str, inventory_hash: str, source_bindings: list) -> None:
    """Check an inspectable separate review record against the frozen output."""
    if not isinstance(binding, dict) or set(binding) != {'path', 'digest', 'locator', 'applicability'}:
        raise ValueError('complete v2 insights need a separate review record')
    if not binding['path'].startswith(f'cases/{case_id}/market_research/case_insights/reviews/'):
        raise ValueError('separate review must be case-local')
    if binding != cases.source_binding(root, binding['path'], locator=binding['locator'],
                                       applicability=binding['applicability']):
        raise ValueError('separate review record changed')
    record = cases.load(cases.safe(root, binding['path']))
    if (not isinstance(record, dict) or set(record) != {'author', 'reviewer', 'review_task_id',
            'rendered_digest', 'inventory_digest', 'outcome', 'material_findings', 'reviewed_sources'}
            or not record['author'] or not record['reviewer'] or record['author'] == record['reviewer']
            or not record['review_task_id'] or record['rendered_digest'] != sha(text.encode())
            or record['inventory_digest'] != inventory_hash or record['outcome'] != 'pass'
            or record['material_findings']
            or record['reviewed_sources'] != sorted(b['path'] + '#' + b['digest'] for b in source_bindings)):
        raise ValueError('separate review does not pass the exact rendered inputs')


def validate_review(review: dict) -> None:
    """Enforce a recorded reviewer decision, never infer it from prose keywords."""
    if not isinstance(review, dict) or set(review) != {'reviewer_type', 'review_mode', 'summary', 'checks', 'rendered_digest', 'inventory_digest', 'outcome', 'blocking_findings'}:
        raise ValueError('complete semantic review is required')
    if (review['reviewer_type'] not in REVIEW_TYPES or review['review_mode'] not in REVIEW_MODES
            or not isinstance(review['summary'], str) or len(review['summary'].strip()) < 20
            or not isinstance(review['checks'], dict) or set(review['checks']) != REVIEW_CHECKS
            or review['outcome'] not in {'pass', 'revise'}
            or not isinstance(review['blocking_findings'], list)
            or any(not isinstance(f, str) or len(f.strip()) < 20 for f in review['blocking_findings'])
            or any(not isinstance(review[key], str) or not re.fullmatch(r'[a-f0-9]{64}', review[key])
                   for key in ('rendered_digest', 'inventory_digest'))):
        raise ValueError('incomplete semantic review')
    for check in review['checks'].values():
        if (not isinstance(check, dict) or set(check) != {'status', 'rationale'}
                or check['status'] not in {'pass', 'fail', 'not_reviewed'}
                or not isinstance(check['rationale'], str) or len(check['rationale'].strip()) < 20):
            raise ValueError('incomplete semantic review check')
    if (review['outcome'] != 'pass' or review['blocking_findings']
            or any(check['status'] != 'pass' for check in review['checks'].values())):
        raise ValueError('semantic review blocks publication: resolve findings and pass every check')


def current_status(root: Path, case_id: str) -> dict:
    scope = cases.resolve(root, case_id)
    cm = cases.case_manifest(root, case_id)
    state = cm.get('insights')
    path = scope / NAME
    if not state or state.get('state') == 'draft':
        return {'status': 'draft', 'reason': 'case insights have not been reviewed'}
    if not path.is_file():
        return {'status': 'invalid', 'reason': 'published case insights are missing'}
    if state.get('state') == 'update_pending':
        return {'status': 'update_pending', 'reason': 'new findings or questions await consolidation'}
    if sha(path.read_bytes()) != state.get('document_digest'):
        return {'status': 'invalid', 'reason': 'published insights changed after review'}
    review_path = state.get('review_path')
    review_file = cases.safe(root, review_path) if isinstance(review_path, str) else None
    if not review_file or not review_file.is_file() or sha(review_file.read_bytes()) != state.get('review_digest'):
        return {'status': 'invalid', 'reason': 'bound insights review is missing or changed'}
    packet = cases.load(review_file)
    try:
        validate_review(packet.get('review'))
    except ValueError as exc:
        return {'status': 'invalid', 'reason': str(exc)}
    if packet['review']['rendered_digest'] != state.get('document_digest'):
        return {'status': 'invalid', 'reason': 'semantic review does not cover published text'}
    try:
        current_inventory = inventory_digest(root, case_id, manifest=cm)
    except (ValueError, OSError):
        return {'status': 'invalid', 'reason': 'research inventory contains an invalid input binding'}
    if current_inventory != state.get('inventory_digest'):
        return {'status': 'update_pending', 'reason': 'research inputs changed since review'}
    if state.get('contract_version') == 2 and state.get('scope_status') == 'complete':
        try:
            validate_independent_review(root, case_id, packet.get('independent_review'),
                                        path.read_text(encoding='utf-8'), current_inventory,
                                        packet.get('source_bindings', []))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            return {'status': 'invalid', 'reason': str(exc)}
    for binding in packet.get('source_bindings', []):
        try:
            current = cases.source_binding(root, binding['path'], locator=binding['locator'],
                                           applicability=binding['applicability'])
        except (OSError, ValueError, KeyError, TypeError):
            return {'status': 'update_pending', 'reason': 'a bound insight source is missing'}
        if current != binding:
            return {'status': 'update_pending', 'reason': 'a bound insight source changed'}
    return {'status': 'current', 'path': str(path), 'review_path': review_path,
            'contract_version': state.get('contract_version', 1),
            'quality_status': ('legacy_not_delivery_qualified' if state.get('contract_version', 1) < 2
                               else 'v2_final_reviewed' if state.get('scope_status') == 'complete'
                               else 'v2_progress'),
            'scope_status': state.get('scope_status', 'complete'),
            'pending_summary': state.get('pending_summary')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--packet', type=Path)
    parser.add_argument('--inventory', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        root = args.workspace.absolute()
        if args.inventory:
            result = {'status': 'inventory', 'inputs': inventory(root, args.case),
                      'inventory_digest': inventory_digest(root, args.case)}
        elif args.prepare:
            if not args.packet or not args.out:
                raise ValueError('--prepare requires --packet and --out')
            target = args.out.absolute()
            if target.exists():
                raise ValueError('review output directory must be fresh')
            packet = cases.load(args.packet)
            rendered = _body(root, args.case, packet)
            rows = inventory(root, args.case, source_bindings=packet.get('source_bindings', []))
            target.mkdir(parents=True)
            (target / NAME).write_text(rendered)
            (target / 'inventory.json').write_text(cases.encoded(rows))
            result = {'status': 'prepared', 'rendered_digest': sha(rendered.encode()),
                      'inventory_digest': inventory_digest(root, args.case, rows=rows), 'output': str(target)}
        elif args.packet:
            text, rows, inv = validate_packet(root, args.case, cases.load(args.packet))
            result = {'status': 'current', 'rendered_digest': sha(text.encode()),
                      'inventory_digest': inv, 'inputs': len(rows)}
        else:
            result = current_status(root, args.case)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] in {'inventory', 'prepared', 'current'} else 2
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'invalid', 'reason': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
