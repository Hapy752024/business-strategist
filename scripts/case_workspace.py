"""Versioned case state and recoverable local publication. No external side effects.

Callers must use the checked router and purpose-specific publishers. Direct Python
or filesystem access is not a security sandbox. One project lock serializes
metadata commits; immutable research runs may be collected concurrently.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager, nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = 2
PROJECT = 'project-manifest.json'
PENDING = 'history/pending.json'
ASSESSMENT_FILES = {'README.md', 'case_insights.md', 'feasibility.md', 'business-case.md', 'economics.json', 'numeric-claims.json'}


def initial_insights(title):
    """Honest reader-facing empty state; publication remains an unreviewed draft."""
    date = now()[:10]
    return (f'# {title}\nLast updated: {date}\n\n'
            '## Executive assessment\nThis case has not yet been assessed.\n\n'
            '## Customer and problem\nThe target customer and pain are not established.\n\n'
            '## Market and demand\nMarket size and demand are not established.\n\n'
            '## Alternatives and competitive position\nAlternatives have not been assessed.\n\n'
            '## Business potential and feasibility\nCommercial and delivery feasibility have not been assessed.\n\n'
            '## Risks, conflicting evidence and open questions\nThe main uncertainties depend on initial research.\n\n'
            '## Recommended next decisions\nInvestigate the target customer, journey and pain.\n\n'
            '## Sources\nNo research sources have been reviewed for this case.\n')


def pending_insights(text):
    notice = '**Assessment update pending:** New information has not yet been integrated into this case assessment.\n\n'
    if notice in text:
        return text
    lines = text.split('\n', 1)
    if len(lines) != 2:
        return notice + text
    return lines[0] + '\n\n' + notice + lines[1].lstrip('\n')


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError('invalid case/decision identifier')
    return value


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe(root, relative):
    root = Path(root).absolute()
    p = Path(relative)
    if p.is_absolute() or not p.parts or any(x in {'.', '..'} for x in p.parts):
        raise ValueError('path must be project-relative without traversal')
    candidate = root / p
    for parent in [root, *candidate.parents, candidate]:
        if parent.is_symlink():
            raise ValueError('Project paths must not be symlinks')
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('path escapes project')
    return candidate


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = data.encode() if isinstance(data, str) else data
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _migration_identity(root):
    candidate = Path(root).absolute()
    projects_root = ROOT / 'projects'
    if not candidate.is_relative_to(projects_root):
        return None
    parts = candidate.relative_to(projects_root).parts
    return parts[0] if parts and not parts[0].startswith('_') else None


@contextmanager
def migration_guard(root):
    project_id = _migration_identity(root)
    if not project_id:
        yield
        return
    try:
        from scripts import layout_migration
    except ModuleNotFoundError:
        try:
            import layout_migration
        except ModuleNotFoundError as exc:
            raise ValueError('migration coordination is unavailable; refusing project access') from exc
    if layout_migration.permitted(project_id):
        yield
        return
    with layout_migration.lock(project_id):
        layout_migration.assert_available(project_id)
        yield


@contextmanager
def project_lock(root):
    root = Path(root)
    with migration_guard(root):
        path = safe(root, 'project.lock')
        root.mkdir(parents=True, exist_ok=True)
        with path.open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def load(path):
    return json.loads(Path(path).read_text())


def _read_project(root, *, allow_pending=False, allow_legacy=False):
    if not allow_pending and safe(root, PENDING).exists():
        raise ValueError('pending publication: recover before using current state')
    path = safe(root, PROJECT)
    m = load(path) if path.exists() else ({'schema_version': '1.0', 'slug': Path(root).name,
        'project_id': Path(root).name, 'manifest_revision': 0, 'created_at': now(), 'updated_at': now(),
        'active_track': 'none', 'links': [], 'next_action': 'Review migrated cases.', 'open_blockers': []} if allow_legacy else load(path))
    if not allow_legacy and not (m.get('layout_version') == VERSION or (m.get('layout_version') == 3 and m.get('controller_kind') == 'umbrella')):
        raise ValueError('explicit migration required for case mode')
    return m


def read_project(root, *, allow_pending=False, allow_legacy=False):
    with migration_guard(root):
        return _read_project(root, allow_pending=allow_pending, allow_legacy=allow_legacy)


def locate_publication(path):
    """Find a versioned controller from a scope/run without inferring parent depth."""
    p = Path(path).absolute()
    for root in [p, *p.parents]:
        # A replacement can temporarily remove the controller manifest.  The
        # stable migration journal still identifies this project, so refuse to
        # treat it as an unmanaged destination (and let a caller create one).
        if _migration_identity(root):
            with migration_guard(root):
                return _locate_publication(p)
    return _locate_publication(p)


def _locate_publication(p):
    """Internal scan; caller is responsible for any migration barrier."""
    for root in [p, *p.parents]:
        manifest = root / PROJECT
        if (root / PENDING).exists():
            safe(root, PENDING)
            return root  # includes an interrupted legacy-to-case publication
        if manifest.is_file() and load(manifest).get('layout_version') in {VERSION, 3}:
            safe(root, PROJECT)
            return root
    return None


def locate(path):
    root = locate_publication(path)
    if root and (root / PROJECT).is_file() and load(root / PROJECT).get('controller_kind') == 'umbrella':
        return None
    return root


def resolve(root, case_id='', *, allow_pending=False):
    root = Path(root).absolute()
    m = read_project(root, allow_pending=allow_pending)
    if m.get('controller_kind') == 'umbrella':
        raise ValueError('case operations require the business subproject root')
    if not case_id:
        return root
    identifier(case_id)
    case = m['cases'].get(case_id)
    if not case or case.get('retired'):
        raise ValueError('unknown or retired case')
    if case.get('path') != 'cases/' + case_id:
        raise ValueError('registered path must match its stable case identity')
    return safe(root, case['path'])


def case_manifest(root, case_id):
    root = Path(root).absolute()
    path = safe(root, str((resolve(root, case_id) / 'market_research/manifest.json').relative_to(root)))
    try:
        m = load(path)
    except (ValueError, OSError) as exc:
        raise ValueError('invalid case manifest') from exc
    if (not isinstance(m, dict) or m.get('case_id') != case_id or type(m.get('assessment_revision')) is not int
            or m['assessment_revision'] < 1 or not isinstance(m.get('stages'), dict) or not isinstance(m.get('events'), list)):
        raise ValueError('invalid case manifest')
    return m


def overview(m, root=None, updated_paths=()):
    if m.get('controller_kind') == 'umbrella':
        lines = ['# ' + m.get('title', m['slug']), '',
                 'Start any subproject independently, or explicitly connect their current outputs. No upstream completion is required.', '',
                 '| Subproject | Current outputs |', '|---|---|']
        for name, item in m['subprojects'].items():
            lines.append(f"| {('Business analysis' if name == 'business' else name.title())} | [{item['path']}/]({item['path']}/) |")
        return '\n'.join(lines + ['', 'Business owns researched cases, selection, economics, the business plan and GTM.',
            'Branding and digital assets own their briefs, deliverables and approvals.', '',
            f"[Design and digital publication history](history/evolution.md). Business analysis has its own [decision history]({m.get('subprojects', {}).get('business', {}).get('path', 'business-analysis')}/history/evolution.md).", ''])
    selected = m.get('selection')
    lines = ['# ' + m.get('title', m['slug']), '',
             'Current execution selection: ' + (selected['case_id'] if selected else 'none') + '.', '',
             '| Case | Current assessment | Main uncertainty | Next action | Documents |', '|---|---|---|---|---|']
    for name, entry in m['cases'].items():
        links = []
        for filename in ('feasibility.md', 'business-case.md'):
            path = entry['path'] + '/' + filename
            exists = path in updated_paths or (root is not None and safe(root, path).is_file())
            links.append(f'[Read]({path})' if exists else 'Not assessed')
        manifest_path = entry['path'] + '/market_research/manifest.json'
        payload = updated_paths.get(manifest_path) if isinstance(updated_paths, dict) else None
        cm = json.loads(payload) if payload else load(safe(root, manifest_path)) if root is not None and safe(root, manifest_path).exists() else {}
        comparison = cm.get('comparison', {})
        review = 'review_required' in cm.get('open_blockers', []) or comparison.get('assessment_revision') != cm.get('assessment_revision')
        clean = lambda text: str(text).replace('|', '\\|').replace('\n', ' ')
        summary = 'Review required — ' + comparison.get('summary', 'reassess this case') if review and comparison else comparison.get('summary', 'Not assessed')
        insight_path = entry['path'] + '/case_insights.md'
        legacy_path = entry['path'] + '/README.md'
        has_insights = insight_path in updated_paths and updated_paths[insight_path] is not None or (root is not None and safe(root, insight_path).is_file() and not (isinstance(updated_paths, dict) and insight_path in updated_paths and updated_paths[insight_path] is None))
        main = f'[Case insights]({insight_path})' if has_insights else f'[Legacy assessment]({legacy_path})' if root is not None and safe(root, legacy_path).is_file() else 'Not assessed'
        if cm.get('insights', {}).get('state') == 'update_pending':
            summary = 'Update pending — ' + summary
        lines.append(f"| {clean(entry['title'])} {'(retired)' if entry.get('retired') else ''} | {clean(summary)} | {clean(comparison.get('principal_uncertainty', 'Unresolved'))} | {clean('Refresh assessment' if review and comparison else comparison.get('next_action', 'Investigate'))} | {main}; feasibility: {links[0]}; business case: {links[1]} |")
    lines += ['', '[Decision history](history/evolution.md)', '']
    if selected:
        lines += ['Business plan: `strategy/business-plan.md` when assembled and reviewed.', '']
    return '\n'.join(lines)


def initialize(root, title, *, controller_kind='business', project_id=None):
    root = Path(root).absolute()
    safe(root, PROJECT)
    with project_lock(root):
        if (root / PROJECT).exists():
            read_project(root)
            return root
        if (root / 'market_research/manifest.json').exists():
            raise ValueError('explicit migration required; legacy research is preserved')
        m = {'schema_version': '1.0', 'layout_version': VERSION, 'project_id': project_id or root.name,
             'slug': project_id or root.name, 'title': title, 'created_at': now(), 'updated_at': now(),
             'manifest_revision': 0, 'active_track': 'none', 'links': [], 'next_action': 'Investigate cases.',
             'open_blockers': [], 'cases': {}, 'selection': None, 'selection_generation': 0}
        if controller_kind == 'umbrella':
            m.update(layout_version=3, controller_kind='umbrella', subprojects={})
            for key in ('cases', 'selection', 'selection_generation'):
                m.pop(key)
        atomic(root / PROJECT, encoded(m))
        atomic(root / 'README.md', overview(m))
        atomic(root / 'history/evolution.md', '# Project evolution\n\nNo committed decisions.\n')
    return root


def publish(root, outputs, *, expected_revision, decision_id, reason, affected=(),
            project=None, fault=None):
    """Internal publication primitive. Call purpose-specific APIs for authored output."""
    root = Path(root).absolute()
    with project_lock(root):
        return publish_locked(root, outputs, expected_revision=expected_revision,
                              decision_id=decision_id, reason=reason, affected=affected,
                              project=project, fault=fault)


def publish_locked(root, outputs, *, expected_revision, decision_id, reason, affected=(),
                   project=None, fault=None, allow_legacy=False):
    identifier(decision_id)
    if not reason.strip():
        raise ValueError('decision reason required')
    current = read_project(root, allow_legacy=allow_legacy)
    if current['manifest_revision'] != expected_revision:
        raise ValueError('publication revision conflict')
    decision_path = f'history/decisions/{decision_id}.md'
    if safe(root, decision_path).exists():
        raise ValueError('decision identifier already committed')
    changes = {}
    for name, content in outputs.items():
        safe(root, name)
        if name == PROJECT or name.startswith(('history/', 'project.lock')):
            raise ValueError('publication metadata is owned by the publisher')
        if current.get('controller_kind') == 'umbrella' and (name in {'business', 'business-analysis'} or name.startswith(('business/', 'business-analysis/'))):
            raise ValueError('business outputs belong to the business controller')
        changes[name] = content.encode() if isinstance(content, str) else content
    updated = copy.deepcopy(project if project is not None else current)
    updated.update(manifest_revision=expected_revision + 1, updated_at=now(), last_completed_operation_id=decision_id)
    changes['README.md'] = overview(updated, root, changes).encode()
    snapshots = [f'- [{name}](../snapshots/{decision_id}/{name})' for name in changes if safe(root, name).exists()]
    decision = f'# {decision_id}\n\nDate: {now()}\n\nCases: {", ".join(affected) or "project"}\n\n{reason}\n\nPrior versions:\n' + '\n'.join(snapshots) + '\n'
    changes[decision_path] = decision.encode()
    timeline = safe(root, 'history/evolution.md')
    prior_timeline = timeline.read_text() if timeline.exists() else '# Project evolution\n'
    changes['history/evolution.md'] = (prior_timeline + f'\n- [{decision_id}](decisions/{decision_id}.md) — {reason.splitlines()[0]}\n').encode()
    changes[PROJECT] = encoded(updated).encode()  # commit marker always last
    entries = []
    for index, (name, content) in enumerate(changes.items()):
        target = safe(root, name)
        old = target.read_bytes() if target.exists() else None
        before_path = f'history/snapshots/{decision_id}/{name}'
        after_path = f'history/staging/{decision_id}/{index}'
        if old is not None:
            atomic(safe(root, before_path), old)
        if content is not None:
            atomic(safe(root, after_path), content)
        entries.append({'path': name, 'before': before_path if old is not None else None,
                        'before_digest': digest(old) if old is not None else None,
                        'after': after_path if content is not None else None, 'after_digest': digest(content) if content is not None else None})
    pending = {'operation': decision_id, 'expected_revision': expected_revision, 'entries': entries}
    atomic(safe(root, PENDING), encoded(pending))
    if fault:
        fault('pending')
    for entry in entries:
        if entry['after'] is None:
            safe(root, entry['path']).unlink(missing_ok=True)
        else:
            atomic(safe(root, entry['path']), safe(root, entry['after']).read_bytes())
        if fault and entry['path'] != PROJECT:
            fault('replace')
    if fault:
        fault('commit')
    safe(root, PENDING).unlink()
    return updated


def recover(root):
    root = Path(root).absolute()
    with project_lock(root):
        journal = safe(root, PENDING)
        if not journal.exists():
            return 'clean'
        pending = load(journal)
        identifier(pending['operation'])
        observed = {}
        for item in pending['entries']:
            p = safe(root, item['path'])
            actual = digest(p.read_bytes()) if p.exists() else None
            if actual not in {item['before_digest'], item['after_digest']}:
                raise ValueError('outside modification: recovery refused')
            observed[item['path']] = actual
            for kind in ('before', 'after'):
                if item[kind] is not None and digest(safe(root, item[kind]).read_bytes()) != item[kind + '_digest']:
                    raise ValueError('recovery snapshot corrupted')
        m = read_project(root, allow_pending=True, allow_legacy=True)
        committed = (m.get('last_completed_operation_id') == pending['operation'] and
                     all(observed[e['path']] == e['after_digest'] for e in pending['entries']))
        if not committed:
            for item in reversed(pending['entries']):
                target = safe(root, item['path'])
                if item['before'] is None:
                    target.unlink(missing_ok=True)
                else:
                    atomic(target, safe(root, item['before']).read_bytes())
            atomic(safe(root, f"history/staging/{pending['operation']}/aborted.json"), encoded({'status': 'aborted'}))
        journal.unlink()
        return 'completed' if committed else 'rolled_back'


def add_case(root, case_id, title, *, open_blockers=(), next_action='Research segment, journey and pain.'):
    identifier(case_id)
    m = read_project(root)
    if case_id in m['cases']:
        if m['cases'][case_id]['title'] != title:
            raise ValueError('case identity already registered; use an explicit rename')
        return resolve(root, case_id)
    updated = copy.deepcopy(m)
    relative = f'cases/{case_id}'
    if any(p.is_file() or p.is_symlink() for p in safe(root, relative).rglob('*')):
        raise ValueError('case directory contains unregistered files')
    updated['cases'][case_id] = {'title': title, 'path': relative, 'retired': False}
    if not isinstance(open_blockers, (list, tuple)) or not all(isinstance(item, str) and item.strip() for item in open_blockers):
        raise ValueError('case blockers must be non-empty strings')
    if not isinstance(next_action, str) or not next_action.strip():
        raise ValueError('case next action required')
    research = {'schema_version': '1.0', 'manifest_revision': 1, 'case_id': case_id,
                'assessment_revision': 1, 'source_bindings': [], 'topic': title, 'topic_slug': case_id,
                'created_at': now(), 'updated_at': now(), 'current_stage': 'intake', 'stages': {},
                'events': [], 'open_blockers': list(open_blockers), 'artifacts': [], 'next_action': next_action,
                'insights': {'contract_version': 1, 'path': 'case_insights.md', 'state': 'draft'}}
    publish(root, {f'{relative}/case_insights.md': initial_insights(title),
                   f'{relative}/market_research/manifest.json': encoded(research)},
            expected_revision=m['manifest_revision'], decision_id='register-' + case_id,
            reason='Register investigated case: ' + title, affected=[case_id], project=updated)
    return Path(root) / relative


def rename_case(root, case_id, title, decision_id, reason):
    root = Path(root).absolute()
    with project_lock(root):
        m = read_project(root)
        scope = resolve(root, case_id)
        if not isinstance(title, str) or not title.strip() or '\n' in title:
            raise ValueError('a single-line display title is required')
        previous = m['cases'][case_id]['title']
        m['cases'][case_id]['title'] = title
        cm = case_manifest(root, case_id)
        cm.update(topic=title, manifest_revision=cm['manifest_revision'] + 1, updated_at=now())
        if cm.get('insights', {}).get('state') == 'current':
            cm['insights']['state'] = 'update_pending'
        outputs = {f'cases/{case_id}/market_research/manifest.json': encoded(cm)}
        for filename in ('case_insights.md', 'README.md', 'feasibility.md', 'business-case.md'):
            path = scope / filename
            if path.exists():
                first, separator, rest = path.read_text().partition('\n')
                rewritten = first.replace(previous, title) + separator + rest
                outputs[f'cases/{case_id}/{filename}'] = pending_insights(rewritten) if filename == 'case_insights.md' and cm.get('insights', {}).get('state') == 'update_pending' else rewritten
        return publish_locked(root, outputs, expected_revision=m['manifest_revision'], decision_id=decision_id,
                              reason=reason, affected=[case_id], project=m)


def migrate(root, mapping, decision_id, reason, *, fault=None):
    """Explicit reversible layout switch. Existing evidence stays at original paths."""
    root = Path(root).absolute()
    with project_lock(root):
        m = read_project(root, allow_legacy=True)
        if m.get('layout_version') == VERSION:
            raise ValueError('project already uses case layout')
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError('explicit nonempty case mapping required')
        updated = copy.deepcopy(m)
        updated.update(layout_version=VERSION, title=m.get('title', m['slug']), cases={}, selection=None, selection_generation=0)
        outputs = {}
        for cid, item in mapping.items():
            identifier(cid)
            if not isinstance(item, dict) or not isinstance(item.get('title'), str) or not item['title'].strip():
                raise ValueError('mapped case title required')
            relative = f'cases/{cid}'
            if any(p.is_file() or p.is_symlink() for p in safe(root, relative).rglob('*')):
                raise ValueError('migration would overwrite existing case directory')
            bindings = [source_binding(root, b['path'], locator=b['locator'], applicability=b['applicability']) for b in item.get('sources', [])]
            updated['cases'][cid] = {'title': item['title'], 'path': relative, 'retired': False}
            cm = {'schema_version': '1.0', 'manifest_revision': 1, 'case_id': cid, 'assessment_revision': 1,
                  'source_bindings': bindings, 'topic': item['title'], 'topic_slug': cid, 'created_at': now(),
                  'updated_at': now(), 'current_stage': 'intake', 'stages': {}, 'events': [], 'artifacts': [],
                  'open_blockers': ['Legacy findings require case-specific review; no inherited passes.'],
                  'next_action': 'Review source applicability and write local segment, journey and pain assessments.'}
            cm['insights'] = {'contract_version': 1, 'path': 'case_insights.md', 'state': 'draft'}
            outputs[relative + '/market_research/manifest.json'] = encoded(cm)
            outputs[relative + '/case_insights.md'] = initial_insights(item['title'])
        return publish_locked(root, outputs, expected_revision=m['manifest_revision'], project=updated,
            decision_id=decision_id, reason=reason, affected=list(mapping), fault=fault, allow_legacy=True)


def select(root, case_id, configuration, decision_id, reason):
    m = read_project(root)
    if m.get('last_selection_decision_id') == decision_id:
        if (not case_id and m['selection'] is None) or (m['selection'] and m['selection']['case_id'] == case_id and m['selection']['configuration'] == configuration):
            return m
        raise ValueError('selection decision conflict')
    if case_id:
        resolve(root, case_id)
        if not configuration.strip():
            raise ValueError('execution configuration required')
    updated = copy.deepcopy(m)
    updated['selection_generation'] += 1
    updated['last_selection_decision_id'] = decision_id
    updated['selection'] = {'case_id': case_id, 'configuration': configuration,
                            'decision_id': decision_id} if case_id else None
    outputs = mark_plan_review(root, 'Execution selection changed.')
    return publish(root, outputs, expected_revision=m['manifest_revision'], decision_id=decision_id,
            reason=reason, affected=[case_id] if case_id else [], project=updated)


def source_binding(root, relative, *, locator, applicability):
    p = safe(root, relative)
    if not p.is_file() or not p.stat().st_size or not locator.strip() or not applicability.strip():
        raise ValueError('nonempty source, locator and applicability required')
    return {'path': relative, 'digest': digest(p.read_bytes()), 'locator': locator, 'applicability': applicability}


def sources_current(root, manifest):
    bindings = list(manifest.get('source_bindings', []))
    for stage in manifest.get('stages', {}).values():
        if stage.get('status') == 'passed' and stage.get('reviewed_revision') == manifest.get('assessment_revision'):
            bindings.extend(stage.get('source_bindings', []))
    for section in manifest.get('business_plan_sections', {}).values():
        bindings.extend(section.get('source_bindings', []))
    bindings.extend(insights_bindings(root, manifest))
    for b in bindings:
        p = safe(root, b['path'])
        if not p.is_file() or digest(p.read_bytes()) != b['digest']:
            raise ValueError('stale source binding: ' + b['path'])


def insights_bindings(root, manifest):
    state = manifest.get('insights') or {}
    review_path = state.get('review_path')
    if not review_path:
        return []
    path = safe(root, review_path)
    if not path.is_file() or digest(path.read_bytes()) != state.get('review_digest'):
        raise ValueError('current insights review binding is stale')
    packet = load(path)
    return packet.get('source_bindings', [])


def binding(root, case_id):
    m = read_project(root)
    selection = m.get('selection')
    if not selection or selection['case_id'] != case_id:
        raise ValueError('case is not selected for execution')
    case = case_manifest(root, case_id)
    sources_current(root, case)
    result = {'case_id': case_id, 'configuration': selection['configuration'],
              'selection_generation': m['selection_generation'], 'assessment_revision': case['assessment_revision']}
    econ = resolve(root, case_id) / 'economics.json'
    if econ.exists():
        try:
            from scripts.case_economics import validate
        except ModuleNotFoundError:
            from case_economics import validate
        record = load(econ)
        validate(record)
        result['economics_input_digest'] = record['input_digest']
    return result


def check_binding(root, candidate):
    if candidate != binding(root, candidate.get('case_id', '')):
        raise ValueError('stale selection/assessment binding')


def check_plan(root, plan):
    """Check a selected-case plan before every downstream consumer."""
    if plan.get('review_required'):
        raise ValueError('business plan review required: ' + plan['review_required'])
    check_binding(root, plan.get('execution_binding', {}))
    sources_current(root, plan)
    try:
        from scripts.validate_case_insights import current_status
    except ModuleNotFoundError:
        from validate_case_insights import current_status
    case_id = plan.get('execution_binding', {}).get('case_id')
    insight_state = case_manifest(root, case_id).get('insights', {}).get('state') if case_id else None
    if case_id and (plan.get('publication_contract_version') == 2 or insight_state not in {None, 'draft'}) and current_status(root, case_id).get('status') != 'current':
        raise ValueError('business plan review required: selected-case insights are missing or stale')
    if case_id and case_manifest(root, case_id).get('appraisal_contract_version') == 2:
        appraisal = appraisal_status(root, case_id)
        if appraisal['status'] != 'current':
            raise ValueError('business plan review required: ' + appraisal['reason'])
    try:
        from scripts.route_workflow import missing_strategy_stages
    except ModuleNotFoundError:
        from route_workflow import missing_strategy_stages
    catalog = load(Path(__file__).resolve().parents[1] / 'config/skill-catalog.json')
    required = catalog['skills']['startup-business-builder']['strategy_stage_prerequisites']
    scope = resolve(root, plan['execution_binding']['case_id'])
    missing = missing_strategy_stages(scope / 'market_research/manifest.json', required)
    cm = case_manifest(root, plan['execution_binding']['case_id'])
    allowed = set()
    for event in cm.get('events', []):
        if (event.get('event') == 'routing_gate_override:startup-business-builder'
                and event.get('assessment_revision') == cm['assessment_revision']
                and event.get('selection_generation') == plan['execution_binding']['selection_generation']):
            allowed.update(event.get('stages', []))
    missing = [stage for stage in missing if stage not in allowed]
    if missing:
            raise ValueError('business plan prerequisites not current: ' + ', '.join(missing))
    saved = safe(root, 'strategy/strategy-plan.json')
    if (plan.get('publication_contract_version') == 2 and saved.is_file()
            and plan == load(saved)):
        if plan.get('publication_status') != 'final':
            raise ValueError('business plan review required: current plan is a progress publication')
        rendered = safe(root, 'strategy/business-plan.md')
        if not rendered.is_file():
            raise ValueError('business plan review required: rendered plan is missing')
        try:
            from scripts.publication_claims import bundle_digest, check_separate_review
        except ModuleNotFoundError:
            from publication_claims import bundle_digest, check_separate_review
        bound = list(plan.get('source_bindings', []))
        for section in plan.get('business_plan_sections', {}).values():
            for item in section.get('source_bindings', []):
                if item not in bound:
                    bound.append(item)
        review_hash = bundle_digest({'strategy/business-plan.md': rendered.read_text()}, bound)
        check_separate_review(root, plan['execution_binding']['case_id'], plan.get('independent_review'),
                              review_hash, bound,
                              f"strategy/reviews/{plan['execution_binding']['case_id']}/")


def publish_assessment(root, case_id, packet, decision_id, reason):
    root = Path(root).absolute()
    with project_lock(root):
        return _publish_assessment(root, case_id, packet, decision_id, reason)


def appraisal_status(root, case_id):
    """Check an existing final v2 appraisal's exact output and review inputs."""
    cm = case_manifest(root, case_id)
    if cm.get('appraisal_contract_version') != 2:
        return {'status': 'legacy', 'reason': 'legacy appraisal has no v2 review bundle'}
    if cm.get('appraisal_publication_status') != 'final':
        return {'status': 'progress', 'reason': 'case appraisal remains a progress publication'}
    try:
        from scripts.publication_claims import bundle_digest, check_separate_review
    except ModuleNotFoundError:
        from publication_claims import bundle_digest, check_separate_review
    try:
        contents = {}
        for binding in cm['source_bindings']:
            if binding != source_binding(root, binding['path'], locator=binding['locator'],
                                         applicability=binding['applicability']):
                raise ValueError('appraisal source changed after review')
        for rel in cm['appraisal_reviewed_outputs']:
            contents[rel] = (encoded(cm['comparison']) if rel == f'cases/{case_id}/comparison.json'
                             else safe(root, rel).read_text())
        review_hash = bundle_digest(contents, cm['source_bindings'])
        check_separate_review(root, case_id, cm['appraisal_review'], review_hash, cm['source_bindings'],
                              f'cases/{case_id}/market_research/appraisal/reviews/')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {'status': 'update_pending', 'reason': str(exc)}
    return {'status': 'current', 'bundle_digest': review_hash}


def prepare_assessment(root, case_id, packet):
    """Render the exact reviewable appraisal bundle without publishing it."""
    root = Path(root).absolute()
    with project_lock(root):
        return _publish_assessment(root, case_id, packet, 'preview', 'Prepare appraisal review', preview=True)


def record_question(root, case_id, question, decision_id, reason):
    """Persist a founder's research question in existing coaching state."""
    root = Path(root).absolute()
    with project_lock(root):
        project = read_project(root)
        cm = case_manifest(root, case_id)
        if not isinstance(question, dict) or set(question) - {'id', 'question', 'status', 'answer_binding'}:
            raise ValueError('question needs id, text, status and optional answer binding')
        qid = question.get('id')
        if not isinstance(qid, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', qid):
            raise ValueError('invalid research question identifier')
        if not isinstance(question.get('question'), str) or not question['question'].strip() or question.get('status') not in {'open', 'partial', 'answered'}:
            raise ValueError('research question needs text and valid status')
        binding = question.get('answer_binding')
        if question['status'] in {'answered', 'partial'}:
            if not isinstance(binding, dict) or binding != source_binding(root, binding['path'], locator=binding['locator'], applicability=binding['applicability']):
                raise ValueError('answered research question needs a current source binding')
            if not binding['path'].startswith((f'cases/{case_id}/', 'market_research/')):
                raise ValueError('answer source must be case-local or shared research')
            if not binding['path'].startswith(f'cases/{case_id}/') and not re.search(r'\bcase(?:[_ -]?id)?[:= -]+' + re.escape(case_id) + r'\b', binding['applicability'], re.I):
                raise ValueError('shared answer needs case applicability')
        elif binding is not None:
            raise ValueError('open question cannot claim a completed answer')
        cm = copy.deepcopy(cm)
        coaching = cm.setdefault('coaching', {'known_answers': [], 'unresolved_inputs': [], 'pending_question': ''})
        questions = [q for q in coaching.get('research_questions', []) if q['id'] != qid]
        questions.append(question)
        coaching['research_questions'] = sorted(questions, key=lambda q: q['id'])
        coaching['updated_at'] = now()
        cm['manifest_revision'] += 1
        cm['updated_at'] = now()
        outputs = {}
        if cm.get('insights', {}).get('state') == 'current':
            cm['insights']['state'] = 'update_pending'
            path = resolve(root, case_id) / 'case_insights.md'
            outputs[f'cases/{case_id}/case_insights.md'] = pending_insights(path.read_text())
        outputs[f'cases/{case_id}/market_research/manifest.json'] = encoded(cm)
        return publish_locked(root, outputs, expected_revision=project['manifest_revision'],
                              decision_id=decision_id, reason=reason, affected=[case_id])


def register_research_assignment(root, case_id, assignment, decision_id, reason):
    """Freeze the requested case scope in the existing case manifest."""
    root = Path(root).absolute()
    with project_lock(root):
        project = read_project(root)
        cm = case_manifest(root, case_id)
        required = {'schema_version', 'decision', 'customer_segment', 'locales',
                    'parent_run', 'capture_runs', 'source_plan_path'}
        version = assignment.get('schema_version') if isinstance(assignment, dict) else None
        v2_extra = {'studies', 'capture_owners', 'coverage_cells', 'overlap_reviews'}
        if (not isinstance(assignment, dict) or version not in {1, 2}
                or set(assignment) != (required if version == 1 else required | v2_extra)):
            raise ValueError('research assignment has invalid fields or version')
        if any(not isinstance(assignment.get(key), str) or len(assignment[key].strip()) < minimum
               for key, minimum in (('decision', 12), ('customer_segment', 3))):
            raise ValueError('research assignment needs a decision and customer segment')
        locales = assignment['locales']
        if (not isinstance(locales, list) or not locales or len(locales) != len(set(locales))
                or any(not isinstance(item, str) or not re.fullmatch(r'[A-Z]{2}:[a-z]{2}(?:-[a-z]{4})?', item) for item in locales)):
            raise ValueError('research assignment needs unique COUNTRY:language locales')
        parent = assignment['parent_run']
        captures = assignment['capture_runs']
        prefix = f'cases/{case_id}/market_research/pain_points/runs/'
        if (not isinstance(parent, str) or not parent.startswith(prefix)
                or not isinstance(captures, list) or len(captures) != len(set(captures))
                or any(not isinstance(item, str) or not item.startswith(prefix)
                       or (version == 1 and item == parent) for item in captures)
                or assignment['source_plan_path'] != parent + '/customer-feedback/customer-feedback-source-plan.json'):
            raise ValueError('research assignment runs and source plan must be case-local')
        for rel in [parent, *captures]:
            path = safe(root, rel)
            if not path.is_dir() or path.is_symlink():
                raise ValueError(f'research assignment run is missing: {rel}')
        if not safe(root, assignment['source_plan_path']).is_file():
            raise ValueError('research assignment source plan is missing')
        if version == 2:
            studies = assignment['studies']
            owners = assignment['capture_owners']
            cells = assignment['coverage_cells']
            overlap_reviews = assignment['overlap_reviews']
            if (not isinstance(studies, list) or not studies or not isinstance(owners, list)
                    or not isinstance(cells, list) or not cells or not isinstance(overlap_reviews, list)):
                raise ValueError('v2 assignment needs studies, capture owners and coverage cells')
            seen_studies = set()
            for study in studies:
                if not isinstance(study, dict) or set(study) != {'run_dir', 'source_plan_path', 'source_plan_sha256', 'relation', 'applicability'}:
                    raise ValueError('v2 study binding is malformed')
                rel = study['run_dir']
                path = study['source_plan_path']
                if (rel in seen_studies or not isinstance(rel, str) or not rel.startswith(prefix)
                        or path != rel + '/customer-feedback/customer-feedback-source-plan.json'
                        or study['relation'] not in {'target', 'adjacent', 'context'}
                        or not isinstance(study['applicability'], str) or len(study['applicability'].strip()) < 20
                        or not safe(root, rel).is_dir() or safe(root, path).is_symlink()
                        or not safe(root, path).is_file() or digest(safe(root, path).read_bytes()) != study['source_plan_sha256']):
                    raise ValueError('v2 study is missing, changed or outside the case')
                seen_studies.add(rel)
            if parent not in seen_studies:
                raise ValueError('v2 assignment must include its delivery anchor study')
            owned = {}
            for owner in owners:
                if (not isinstance(owner, dict) or set(owner) != {'capture_run', 'study_run'}
                        or owner['capture_run'] in owned or owner['study_run'] not in seen_studies):
                    raise ValueError('v2 capture owner is invalid or duplicated')
                owned[owner['capture_run']] = owner['study_run']
            if set(owned) != set(captures):
                raise ValueError('v2 capture owners must cover every declared capture exactly once')
            for cell in cells:
                if (not isinstance(cell, dict) or set(cell) != {'question', 'locale', 'frame', 'study_run', 'cell_id'}
                        or cell['locale'] not in locales or cell['frame'] not in {'topic_led_voc', 'entity_led_feedback'}
                        or cell['study_run'] not in seen_studies or not isinstance(cell['question'], str)
                        or len(cell['question'].strip()) < 12):
                    raise ValueError('v2 assignment coverage cell is malformed')
        cm = copy.deepcopy(cm)
        cm['research_assignment'] = assignment
        cm['manifest_revision'] += 1
        cm['updated_at'] = now()
        cm.setdefault('events', []).append({'ts': now(), 'event': 'research_assignment', 'decision_id': decision_id})
        return publish_locked(root, {f'cases/{case_id}/market_research/manifest.json': encoded(cm)},
                              expected_revision=project['manifest_revision'], decision_id=decision_id,
                              reason=reason, affected=[case_id])


def check_legacy_insights_conversion(root, case_id, manifest):
    """Do not delete a legacy narrative while current consumers still use it."""
    legacy_rel = f'cases/{case_id}/README.md'
    if not safe(root, legacy_rel).is_file():
        return
    consumers = []

    def check(bindings, owner):
        if any(binding.get('path') == legacy_rel for binding in bindings):
            consumers.append(owner)

    for owner_id, entry in read_project(root)['cases'].items():
        if entry.get('retired') and owner_id != case_id:
            continue
        cm = manifest if owner_id == case_id else case_manifest(root, owner_id)
        check(cm.get('source_bindings', []), f'case {owner_id} source_bindings')
        for stage_name, stage in cm.get('stages', {}).items():
            owner = f'case {owner_id} stage {stage_name}'
            check(stage.get('source_bindings', []), owner)
            if owner_id == case_id and any(
                    (item.get('path') if isinstance(item, dict) else item) == 'README.md'
                    for item in stage.get('artifacts', [])):
                consumers.append(owner + ' artifacts')
        for question in cm.get('coaching', {}).get('research_questions', []):
            check([question.get('answer_binding') or {}], f'case {owner_id} question {question["id"]}')
        check(insights_bindings(root, cm), f'case {owner_id} insights')
    plan_path = safe(root, 'strategy/strategy-plan.json')
    if plan_path.is_file():
        plan = load(plan_path)
        check(plan.get('source_bindings', []), 'selected plan source_bindings')
        for section, item in plan.get('business_plan_sections', {}).items():
            check(item.get('source_bindings', []), f'selected plan section {section}')
    if consumers:
        raise ValueError('legacy README still has current consumers; refresh their original-source references before conversion: '
                         + '; '.join(sorted(set(consumers))))


def publish_insights(root, case_id, packet, decision_id, reason):
    """Publish one reviewed synthesis using the existing case transaction."""
    root = Path(root).absolute()
    with project_lock(root):
        try:
            from scripts import validate_case_insights as insights
            from scripts.verify_numeric_claims import checked_claims
        except ModuleNotFoundError:
            import validate_case_insights as insights
            from verify_numeric_claims import checked_claims
        project = read_project(root)
        cm = case_manifest(root, case_id)
        text, _, _ = insights.validate_packet(root, case_id, packet, manifest=cm)
        scope = resolve(root, case_id)
        review_path = f'cases/{case_id}/market_research/case_insights/reviews/{decision_id}.json'
        if safe(root, review_path).exists():
            raise ValueError('insights review identifier already published')
        review_bytes = encoded(packet).encode()
        claims = packet.get('numeric_claims', [])
        _, numeric = checked_claims(root, {'case_insights.md': packet['document']}, claims, packet['source_bindings'])
        prior_path = scope / 'numeric-claims.json'
        retained = []
        if prior_path.is_file():
            for claim in load(prior_path).get('claims', []):
                if claim.get('document') in {'README.md', 'case_insights.md'}:
                    continue
                authored = {k: v for k, v in claim.items() if k not in {'check_status', 'source_sha256'}}
                marker = '{{source_numeric.' + authored['id'] + '}}'
                binding = [authored['source_binding']] if authored['status'] == 'verified' else []
                checked_claims(root, {authored['document']: marker}, [authored], binding)
                retained.append(claim)
        all_claims = retained + numeric['claims']
        if len({row['id'] for row in all_claims}) != len(all_claims):
            raise ValueError('numeric claim identifier collides with retained annex claim')
        receipt = {'schema_version': '1.0', 'claims': all_claims,
                   'verified_count': sum(c['check_status'] == 'verified' for c in all_claims),
                   'unverified_count': sum(c['check_status'] == 'unverified' for c in all_claims)}
        cm = copy.deepcopy(cm)
        cm['manifest_revision'] += 1
        cm['updated_at'] = now()
        if packet.get('comparison') and not cm.get('comparison'):
            cm['comparison'] = {**packet['comparison'], 'assessment_revision': cm['assessment_revision']}
        legacy_rel = f'cases/{case_id}/README.md'
        legacy = scope / 'README.md'
        if legacy.is_file() and any(b['path'] == legacy_rel for b in packet['source_bindings']):
            raise ValueError('old README cannot remain a current insights source after conversion')
        if legacy.is_file():
            # Consumer checks ran during validation. Retire only the obsolete
            # output registration; evidence bindings and stage passes stay intact.
            cm['artifacts'] = [path for path in cm.get('artifacts', []) if path != 'README.md']
            cm.get('document_bindings', {}).pop('README.md', None)
        post_rows = insights.inventory(root, case_id, manifest=cm,
                                       source_bindings=packet['source_bindings'], include_previous=False)
        if legacy.is_file():
            post_rows = [row for row in post_rows if row['path'] != legacy_rel]
        post_hash = insights.inventory_digest(root, case_id, manifest=cm, rows=post_rows)
        cm['insights'] = {'contract_version': packet.get('publication_contract_version', 1), 'path': 'case_insights.md', 'state': 'current',
                          'document_digest': digest(text.encode()), 'inventory_digest': post_hash,
                          'review_path': review_path, 'review_digest': digest(review_bytes),
                          'assessment_revision': cm['assessment_revision'], 'published_at': now(),
                          'scope_status': packet.get('scope_status', 'complete'),
                          'pending_summary': packet.get('pending_summary')}
        cm.setdefault('events', []).append({'ts': now(), 'event': 'case_insights', 'decision_id': decision_id})
        outputs = {f'cases/{case_id}/case_insights.md': text,
                   review_path: review_bytes,
                   f'cases/{case_id}/numeric-claims.json': encoded(receipt),
                   f'cases/{case_id}/market_research/manifest.json': encoded(cm)}
        if legacy.is_file():
            outputs[legacy_rel] = None
        return publish_locked(root, outputs, expected_revision=project['manifest_revision'],
                              decision_id=decision_id, reason=reason, affected=[case_id])


def _publish_assessment(root, case_id, packet, decision_id, reason, *, preview=False):
    """Final publisher for opportunity-risk-designer's bounded appraisal mode."""
    scope = resolve(root, case_id)
    m = read_project(root)
    cm = case_manifest(root, case_id)
    if set(packet) - {'assessment_revision', 'manifest_revision', 'documents', 'source_bindings', 'economics_inputs', 'material_change', 'economics_input_digest', 'comparison', 'numeric_claims', 'publication_contract_version', 'publication_claims', 'business_plan_sections', 'publication_status', 'independent_review'}:
        raise ValueError('unknown appraisal fields; author inputs, never calculated results')
    if packet.get('manifest_revision') != cm['manifest_revision']:
        raise ValueError('case publication revision conflict')
    if packet.get('assessment_revision') != cm['assessment_revision']:
        raise ValueError('assessment revision conflict')
    try:
        from scripts.evidence_scout.validate_research_completion import initial_case_evidence
    except ModuleNotFoundError:
        from evidence_scout.validate_research_completion import initial_case_evidence
    evidence = initial_case_evidence(root, case_id, packet.get('source_bindings', []))
    if evidence['status'] != 'eligible':
        raise ValueError('reviewed initial case evidence required: ' + ', '.join(evidence['missing']))
    docs = packet.get('documents', {})
    allowed_docs = {'feasibility.md', 'business-case.md'} | ({'README.md'} if not cm.get('insights') else set())
    if not docs or any(name not in allowed_docs for name in docs):
        raise ValueError('appraisal may only publish designated case narratives')
    if any(not isinstance(body, str) or not body.strip() for body in docs.values()):
        raise ValueError('empty assessment document')
    version = packet.get('publication_contract_version', 1)
    if version not in {1, 2}:
        raise ValueError('unsupported appraisal publication contract')
    if version == 2:
        sections = packet.get('business_plan_sections')
        if not isinstance(sections, dict) or set(sections) != set(PLAN_SECTIONS):
            raise ValueError('v2 appraisal needs every business plan decision section')
        lines = ['# Conditional business case', '']
        for key in PLAN_SECTIONS:
            row = sections[key]
            if (not isinstance(row, dict) or row.get('status') not in {'supported', 'provisional', 'missing', 'not_applicable'}
                    or not isinstance(row.get('text'), str) or len(row['text'].strip()) < 25):
                raise ValueError('decision-useful section status and explanation required: ' + key)
            if row['status'] in {'missing', 'not_applicable'} and not row.get('next_action'):
                raise ValueError('missing or inapplicable section needs decision consequence and next action: ' + key)
            lines += ['## ' + key.replace('_', ' ').title(), '', 'Status: ' + row['status'], '', row['text'], '']
            if row.get('next_action'):
                lines += ['Decision consequence and next action: ' + row['next_action'], '']
        docs = {**docs, 'business-case.md': '\n'.join(lines)}
    bindings = packet.get('source_bindings')
    if not isinstance(bindings, list) or not bindings:
        raise ValueError('explicit source-use bindings required')
    for b in bindings:
        if b.get('path') in {f'cases/{case_id}/{name}' for name in ASSESSMENT_FILES}:
            raise ValueError('current outputs cannot be their own evidence inputs')
        if b != source_binding(root, b['path'], locator=b['locator'], applicability=b['applicability']):
            raise ValueError('stale source-use binding')
    if not any(row['claim_ledger'] in {b['path'] for b in bindings} for row in evidence['eligible_runs']):
        raise ValueError('appraisal must bind an eligible reviewed claim ledger')
    numeric_claims = packet.get('numeric_claims', [])
    prior_numeric = scope / 'numeric-claims.json'
    if not packet.get('material_change', True) and prior_numeric.exists() and load(prior_numeric).get('claims') and 'numeric_claims' not in packet:
        raise ValueError('cosmetic appraisal must retain current numeric claims explicitly')
    if not packet.get('material_change', True):
        if bindings != cm.get('source_bindings'):
            raise ValueError('source applicability changes require a material revision')
        if 'economics_inputs' in packet and (not (scope / 'economics.json').exists() or packet['economics_inputs'] != load(scope / 'economics.json')['inputs']):
            raise ValueError('economic assumption changes require a material revision')
    # Refresh is explicit, not a silent inheritance of passed checkpoints.
    updated = invalidate(cm, reason) if packet.get('material_change', True) else copy.deepcopy(cm)
    if not packet.get('material_change', True):
        updated.update(manifest_revision=cm.get('manifest_revision', 0) + 1, updated_at=now())
    if version == 1 or packet.get('publication_status', 'progress') == 'progress':
        for key in ('appraisal_review', 'appraisal_reviewed_outputs'):
            updated.pop(key, None)
    if version == 1:
        updated.pop('appraisal_contract_version', None)
        updated.pop('appraisal_publication_status', None)
    updated['source_bindings'] = bindings
    if packet.get('material_change', True) and updated.get('insights', {}).get('state') == 'current':
        updated['insights']['state'] = 'update_pending'
    if 'comparison' not in packet:
        raise ValueError('appraisal requires a current comparison summary')
    if 'comparison' in packet:
        comparison = packet['comparison']
        if not isinstance(comparison, dict) or set(comparison) != {'summary', 'principal_uncertainty', 'next_action'} or any(not isinstance(v, str) or not v.strip() for v in comparison.values()):
            raise ValueError('comparison requires summary, principal_uncertainty and next_action')
        updated['comparison'] = {**comparison, 'assessment_revision': updated['assessment_revision']}
    try:
        from scripts.verify_numeric_claims import checked_claims, render_markers
    except ModuleNotFoundError:
        from verify_numeric_claims import checked_claims, render_markers
    numeric_texts = {**docs, **{'comparison.' + key: value for key, value in comparison.items()}}
    if version == 2:
        try:
            from scripts.publication_claims import check_numeric_citations
        except ModuleNotFoundError:
            from publication_claims import check_numeric_citations
        check_numeric_citations(numeric_texts, numeric_claims, packet.get('publication_claims', []))
    _, numeric_report = checked_claims(root, numeric_texts, numeric_claims, bindings)
    outputs = {f'cases/{case_id}/{name}': body for name, body in docs.items()}
    if 'numeric_claims' in packet or prior_numeric.exists():
        outputs[f'cases/{case_id}/numeric-claims.json'] = encoded(numeric_report)
    record = None
    if 'economics_inputs' in packet:
        try:
            from scripts.case_economics import calculate
        except ModuleNotFoundError:
            from case_economics import calculate
        record = calculate(packet['economics_inputs'])
        outputs[f'cases/{case_id}/economics.json'] = encoded(record)
    elif (scope / 'economics.json').exists():
        try:
            from scripts.case_economics import validate
        except ModuleNotFoundError:
            from case_economics import validate
        record = load(scope / 'economics.json')
        validate(record)
    if record:
        known = {b['path'] for b in bindings} | {b['path'] + '#' + b['locator'] for b in bindings}
        models = [record, *record['results'].get('scenarios', {}).values()]
        for model in models:
            for item in model['inputs'].get('provenance', {}).values():
                if item.get('status') == 'evidence_backed' and not set(item['source_refs']).issubset(known):
                    raise ValueError('economic evidence must bind a checked local source/locator')
        try:
            from scripts.economics_text import render
        except ModuleNotFoundError:
            from economics_text import render
        for key in ('summary', 'principal_uncertainty', 'next_action'):
            updated['comparison'][key] = render(packet['comparison'][key], record, packet.get('economics_input_digest'))
    for name in ('README.md', 'feasibility.md', 'business-case.md'):
        if name in docs and record:
            try:
                from scripts.economics_text import render
            except ModuleNotFoundError:
                from economics_text import render
            outputs[f'cases/{case_id}/{name}'] = render(docs[name], record, packet.get('economics_input_digest'))
            updated.setdefault('document_bindings', {})[name] = {'authored_digest': digest(docs[name].encode()),
                'economics_input_digest': packet.get('economics_input_digest'), 'model_input_digest': record['input_digest']}
            outputs[f'cases/{case_id}/{name}'] += '\n\nEconomics input digest: `' + record['input_digest'] + '`\n\nCalculated contribution per unit: ' + str(record['results']['contribution_per_unit']) + '. Required monthly sales: ' + str(record['results']['required_sales']) + '. Capacity meets target: ' + str(record['results']['capacity_meets_target']) + '. Unknowns remain unresolved; see economics.json.\n'
        elif name not in docs and packet.get('material_change', True) and (scope / name).exists():
            outputs[f'cases/{case_id}/{name}'] = '# Review required\n\nAssessment changed; refresh this document. Earlier findings are archived in project history.\n'
    for name in docs:
        outputs[f'cases/{case_id}/{name}'] = render_markers(outputs[f'cases/{case_id}/{name}'], numeric_report)
    for key in ('summary', 'principal_uncertainty', 'next_action'):
        updated['comparison'][key] = render_markers(updated['comparison'][key], numeric_report)
    if version == 2:
        try:
            from scripts.publication_claims import render as render_claims
        except ModuleNotFoundError:
            from publication_claims import render as render_claims
        rendered = render_claims(root, {**{name: outputs[f'cases/{case_id}/{name}'] for name in docs},
                                        **{'comparison.' + key: updated['comparison'][key]
                                           for key in ('summary', 'principal_uncertainty', 'next_action')}},
                                 packet.get('publication_claims', []), bindings)
        for name in docs:
            outputs[f'cases/{case_id}/{name}'] = rendered[name]
        for key in ('summary', 'principal_uncertainty', 'next_action'):
            updated['comparison'][key] = rendered['comparison.' + key]
        updated['appraisal_contract_version'] = 2
        updated['appraisal_publication_status'] = packet.get('publication_status', 'progress')
    if updated.get('insights', {}).get('state') == 'update_pending' and (scope / 'case_insights.md').is_file():
        outputs[f'cases/{case_id}/case_insights.md'] = pending_insights((scope / 'case_insights.md').read_text())
    updated.setdefault('events', []).append({'ts': now(), 'event': 'appraisal', 'decision_id': decision_id})
    outputs[f'cases/{case_id}/market_research/manifest.json'] = encoded(updated)
    if packet.get('material_change', True) and (m.get('selection') or {}).get('case_id') == case_id:
        outputs.update(mark_plan_review(root, 'Selected-case assessment changed.'))
    if version == 2:
        try:
            from scripts.publication_claims import bundle_digest, check_separate_review
        except ModuleNotFoundError:
            from publication_claims import bundle_digest, check_separate_review
        reviewed_outputs = {key: value for key, value in outputs.items()
                            if key.startswith(f'cases/{case_id}/') and not key.endswith('market_research/manifest.json')
                            and key != f'cases/{case_id}/case_insights.md'}
        economics_rel = f'cases/{case_id}/economics.json'
        if economics_rel not in reviewed_outputs and (scope / 'economics.json').is_file():
            reviewed_outputs[economics_rel] = (scope / 'economics.json').read_text()
        reviewed_outputs[f'cases/{case_id}/comparison.json'] = encoded(updated['comparison'])
        review_hash = bundle_digest(reviewed_outputs, bindings)
        if preview:
            return {'bundle_digest': review_hash, 'outputs': reviewed_outputs,
                    'reviewed_sources': sorted(b['path'] + '#' + b['digest'] for b in bindings)}
        if packet.get('publication_status', 'progress') == 'final':
            check_separate_review(root, case_id, packet.get('independent_review'), review_hash, bindings,
                                  f'cases/{case_id}/market_research/appraisal/reviews/')
            updated['appraisal_review'] = packet['independent_review']
            updated['appraisal_reviewed_outputs'] = sorted(reviewed_outputs)
            outputs[f'cases/{case_id}/market_research/manifest.json'] = encoded(updated)
        elif packet.get('publication_status', 'progress') != 'progress':
            raise ValueError('appraisal publication status must be progress or final')
    elif preview:
        raise ValueError('legacy appraisal has no final-quality review bundle')
    return publish_locked(root, outputs, expected_revision=m['manifest_revision'], decision_id=decision_id, reason=reason, affected=[case_id])


PLAN_SECTIONS = ('business', 'customer_market', 'competitive_choice', 'product_revenue', 'acquisition_sales',
                 'delivery_team', 'finances', 'milestones_risks', 'funding_legal_ip')


def publish_business_plan(root, case_id, plan, decision_id, reason):
    root = Path(root).absolute()
    with project_lock(root):
        return _publish_business_plan(root, case_id, plan, decision_id, reason)


def prepare_business_plan(root, case_id, plan):
    root = Path(root).absolute()
    with project_lock(root):
        return _publish_business_plan(root, case_id, plan, 'preview', 'Prepare plan review', preview=True)


def _publish_business_plan(root, case_id, plan, decision_id, reason, *, preview=False):
    """Assemble one root plan from the existing structured strategy authority."""
    try:
        from scripts.strategy_review import validate_plan
    except ModuleNotFoundError:
        from strategy_review import validate_plan
    m = read_project(root)
    existing = safe(root, 'strategy/strategy-plan.json')
    prior_digest = digest(existing.read_bytes()) if existing.exists() else None
    if 'publication_base_digest' not in plan or plan['publication_base_digest'] != prior_digest:
        raise ValueError('business plan publication conflict; refresh the current plan digest')
    current = binding(root, case_id)
    if plan.get('execution_binding') != current:
        raise ValueError('stale or missing execution binding')
    errors = validate_plan(plan)
    if errors:
        raise ValueError('; '.join(errors))
    check_plan(root, plan)
    sections = plan.get('business_plan_sections', {})
    if set(sections) != set(PLAN_SECTIONS):
        raise ValueError('business plan needs explicit coverage for every section')
    lines = ['# Business plan', '', 'Selected case: ' + case_id, '',
             'Selection generation: ' + str(current['selection_generation']),
             'Assessment revision: ' + str(current['assessment_revision']), '']
    econ_path = resolve(root, case_id) / 'economics.json'
    economics = load(econ_path) if econ_path.exists() else None
    try:
        from scripts.economics_text import render
    except ModuleNotFoundError:
        from economics_text import render
    version = plan.get('publication_contract_version', 1)
    if version not in {1, 2}:
        raise ValueError('unsupported business plan publication contract')
    all_bindings = list(plan.get('source_bindings', []))
    for section in sections.values():
        for item in section.get('source_bindings', []):
            if item not in all_bindings:
                all_bindings.append(item)
    if version == 2:
        try:
            from scripts.publication_claims import render as render_claims, bundle_digest, check_separate_review
        except ModuleNotFoundError:
            from publication_claims import render as render_claims, bundle_digest, check_separate_review
        if any(ref.get('document') not in {'section.' + key for key in PLAN_SECTIONS}
               for ref in plan.get('publication_claims', [])):
            raise ValueError('plan citation targets must be business plan sections')
    for key in PLAN_SECTIONS:
        section = sections[key]
        status = section.get('status')
        if status not in {'supported', 'provisional', 'missing', 'not_applicable'} or not section.get('text', '').strip():
            raise ValueError('section status and explanation required: ' + key)
        if status == 'supported' and not section.get('source_bindings'):
            raise ValueError('supported section needs source-use bindings: ' + key)
        for b in section.get('source_bindings', []):
            if b != source_binding(root, b['path'], locator=b['locator'], applicability=b['applicability']):
                raise ValueError('stale plan source: ' + key)
        section_text = render(section['text'], economics, section.get('economics_input_digest'))
        if version == 2:
            relevant = [ref for ref in plan.get('publication_claims', []) if ref.get('document') == 'section.' + key]
            section_text = render_claims(root, {'section.' + key: section_text}, relevant, all_bindings)['section.' + key]
        lines += ['## ' + key.replace('_', ' ').title(), '', 'Status: ' + status, '', section_text, '']
    econ_path = resolve(root, case_id) / 'economics.json'
    if econ_path.exists():
        try:
            from scripts.case_economics import validate
        except ModuleNotFoundError:
            from case_economics import validate
        economics = load(econ_path)
        validate(economics)
        lines += ['## Calculated economics', '', 'Input digest: `' + economics['input_digest'] + '`', '',
                  '```json', encoded(economics['results']), '```', '']
    rendered_plan = '\n'.join(lines)
    if version == 2:
        review_hash = bundle_digest({'strategy/business-plan.md': rendered_plan}, all_bindings)
        if preview:
            return {'bundle_digest': review_hash, 'document': rendered_plan,
                    'reviewed_sources': sorted(b['path'] + '#' + b['digest'] for b in all_bindings)}
        if plan.get('publication_status', 'progress') == 'final':
            check_separate_review(root, case_id, plan.get('independent_review'), review_hash, all_bindings,
                                  f'strategy/reviews/{case_id}/')
        elif plan.get('publication_status', 'progress') != 'progress':
            raise ValueError('plan publication status must be progress or final')
    elif preview:
        raise ValueError('legacy plan has no final-quality review bundle')
    return publish_locked(root, {'strategy/business-plan.md': rendered_plan, 'strategy/strategy-plan.json': encoded(plan)},
                   expected_revision=m['manifest_revision'], decision_id=decision_id, reason=reason, affected=[case_id])


def invalidate(manifest, reason):
    m = copy.deepcopy(manifest)
    m['assessment_revision'] += 1
    m['manifest_revision'] = m.get('manifest_revision', 0) + 1
    m['updated_at'] = now()
    for stage in m.get('stages', {}).values():
        if stage.get('status') == 'passed':
            stage.update(status='blocked', gate_result='not_run', blocked_reason='review_required: ' + reason)
    m['open_blockers'] = ['review_required: ' + reason]
    return m


def mark_plan_review(root, reason):
    outputs = {}
    if safe(root, 'strategy/business-plan.md').exists():
        outputs['strategy/business-plan.md'] = '# Business plan\n\nReview required: ' + reason + '\n'
    path = safe(root, 'strategy/strategy-plan.json')
    if path.exists():
        plan = load(path)
        plan['review_required'] = reason
        for section in plan.get('business_plan_sections', {}).values():
            if section.get('status') == 'supported':
                section['status'] = 'provisional'
            section['text'] = 'Review required: ' + reason + '\n\n' + section.get('text', '')
        outputs['strategy/strategy-plan.json'] = encoded(plan)
    return outputs


def correct(root, case_ids, reason, decision_id, *, source_path=None):
    m = read_project(root)
    targets = set(case_ids)
    if source_path:
        safe(root, source_path)
        plan_path = safe(root, 'strategy/strategy-plan.json')
        if plan_path.exists():
            plan = load(plan_path)
            if any(b['path'] == source_path for section in plan.get('business_plan_sections', {}).values()
                   for b in section.get('source_bindings', [])):
                consumer = plan.get('execution_binding', {}).get('case_id')
                if consumer in m['cases'] and not m['cases'][consumer].get('retired'):
                    targets.add(consumer)
        for case_id in m['cases']:
            cm = case_manifest(root, case_id)
            bs = list(cm.get('source_bindings', []))
            for stage in cm.get('stages', {}).values():
                bs.extend(stage.get('source_bindings', []))
            bs.extend(insights_bindings(root, cm))
            if any(b['path'] == source_path for b in bs):
                targets.add(case_id)
    outputs = {}
    for case_id in sorted(targets):
        resolve(root, case_id)
        cm = invalidate(case_manifest(root, case_id), reason)
        if cm.get('insights', {}).get('state') == 'current':
            cm['insights']['state'] = 'update_pending'
        cm.setdefault('events', []).append({'ts': now(), 'event': 'correction', 'decision_id': decision_id})
        outputs[f'cases/{case_id}/market_research/manifest.json'] = encoded(cm)
        withdrawn = set()
        for name in ('README.md', 'feasibility.md', 'business-case.md'):
            path = resolve(root, case_id) / name
            if path.exists():
                outputs[f'cases/{case_id}/{name}'] = '# Review required\n\n' + reason + '\n\nPrevious findings are archived in project history.\n'
                withdrawn.add(name)
        numeric_path = resolve(root, case_id) / 'numeric-claims.json'
        if withdrawn and numeric_path.is_file():
            prior_numeric = load(numeric_path)
            retained = [claim for claim in prior_numeric.get('claims', []) if claim.get('document') not in withdrawn]
            if len(retained) != len(prior_numeric.get('claims', [])):
                outputs[f'cases/{case_id}/numeric-claims.json'] = encoded({
                    **prior_numeric, 'claims': retained,
                    'verified_count': sum(claim['check_status'] == 'verified' for claim in retained),
                    'unverified_count': sum(claim['check_status'] == 'unverified' for claim in retained)})
        insight_path = resolve(root, case_id) / 'case_insights.md'
        if insight_path.is_file() and cm.get('insights', {}).get('state') == 'update_pending':
            outputs[f'cases/{case_id}/case_insights.md'] = pending_insights(insight_path.read_text())
    selection = m.get('selection')
    if selection and selection['case_id'] in targets:
        outputs.update(mark_plan_review(root, reason))
    publish(root, outputs, expected_revision=m['manifest_revision'], decision_id=decision_id,
            reason=reason, affected=sorted(targets))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'add', 'rename', 'select', 'clear', 'correct', 'recover', 'show', 'appraise', 'plan', 'insights', 'record-question', 'register-research', 'prepare-appraisal', 'prepare-plan'])
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--case', default='')
    parser.add_argument('--title', default='')
    parser.add_argument('--configuration', default='')
    parser.add_argument('--decision-id', default='')
    parser.add_argument('--reason', default='')
    parser.add_argument('--source', default=None)
    parser.add_argument('--input', type=Path, help='Authored appraisal or structured strategy JSON; results are calculated.')
    parser.add_argument('--out', type=Path, help='Fresh directory for exact rendered review bundle.')
    args = parser.parse_args(argv)
    try:
        if args.action not in {'recover', 'show'} and (args.workspace / PROJECT).exists() and load(args.workspace / PROJECT).get('controller_kind') == 'umbrella':
            args.workspace = safe(args.workspace, read_project(args.workspace)['subprojects']['business']['path'])
        if args.action == 'init':
            initialize(args.workspace, args.title or args.workspace.name)
        elif args.action == 'add':
            add_case(args.workspace, args.case, args.title or args.case)
        elif args.action == 'rename':
            rename_case(args.workspace, args.case, args.title, args.decision_id, args.reason)
        elif args.action in {'select', 'clear'}:
            select(args.workspace, args.case if args.action == 'select' else '', args.configuration, args.decision_id, args.reason)
        elif args.action == 'correct':
            correct(args.workspace, [args.case] if args.case else [], args.reason, args.decision_id, source_path=args.source)
        elif args.action == 'recover':
            print(recover(args.workspace))
        elif args.action == 'record-question':
            if args.input is None:
                raise ValueError('--input required')
            record_question(args.workspace, args.case, load(args.input), args.decision_id, args.reason)
        elif args.action == 'register-research':
            if args.input is None:
                raise ValueError('--input required')
            register_research_assignment(args.workspace, args.case, load(args.input), args.decision_id, args.reason)
        elif args.action == 'insights':
            if args.input is None:
                raise ValueError('--input required')
            publish_insights(args.workspace, args.case, load(args.input), args.decision_id, args.reason)
        elif args.action in {'appraise', 'plan'}:
            if args.input is None:
                raise ValueError('--input required')
            function = publish_assessment if args.action == 'appraise' else publish_business_plan
            function(args.workspace, args.case, load(args.input), args.decision_id, args.reason)
        elif args.action in {'prepare-appraisal', 'prepare-plan'}:
            if args.input is None or args.out is None:
                raise ValueError('--input and --out required')
            out = args.out.absolute()
            if out.exists():
                raise ValueError('review output directory must be fresh')
            function = prepare_assessment if args.action == 'prepare-appraisal' else prepare_business_plan
            bundle = function(args.workspace, args.case, load(args.input))
            out.mkdir(parents=True)
            if 'outputs' in bundle:
                for path, body in bundle['outputs'].items():
                    target = out / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(body if isinstance(body, bytes) else body.encode())
                bundle = {key: value for key, value in bundle.items() if key != 'outputs'}
            else:
                (out / 'business-plan.md').write_text(bundle.pop('document'))
            (out / 'review-bundle.json').write_text(encoded(bundle))
            print(encoded({'status': 'prepared', 'output': str(out), **bundle}))
            return 0
        print(encoded(read_project(args.workspace)))
        return 0
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
