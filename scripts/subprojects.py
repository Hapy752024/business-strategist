"""Independent subproject entry points and explicit, optional handoff connections."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
try:
    from scripts import case_workspace as cases
except ModuleNotFoundError:
    import case_workspace as cases

PATHS = {'business': 'business-analysis', 'branding': 'branding', 'marketing': 'marketing', 'website': 'digital-assets/website', 'others': 'digital-assets/others'}


def is_umbrella(root):
    path = Path(root) / cases.PROJECT
    return path.is_file() and cases.load(path).get('controller_kind') == 'umbrella'


def canonical_name(name):
    return 'business' if name == 'business-analysis' else name


def path(root, name):
    name = canonical_name(name)
    if name not in PATHS:
        raise ValueError('unknown subproject')
    relative = PATHS[name]
    if is_umbrella(root):
        relative = cases.read_project(root).get('subprojects', {}).get(name, {}).get('path', relative)
    return cases.safe(root, relative)


def business(root):
    return path(root, 'business') if is_umbrella(root) else Path(root).absolute()


def initialize(root, title):
    root = Path(root).absolute()
    if (root / cases.PROJECT).exists() or (root / 'market_research/manifest.json').exists():
        if not is_umbrella(root):
            raise ValueError('existing layout preserved; migration must be explicit')
        cases.read_project(root)
        return root
    # A controller-less README is either a legacy workspace or a concurrent
    # writer.  Do not silently overwrite it while a layout migration has an
    # intent journal; callers must explicitly recover or migrate first.
    for name in ('README.md', 'history', 'project.lock'):
        if (root / name).exists():
            raise ValueError('unmanaged root content exists; explicit migration or recovery is required')
    cases.initialize(root, title, controller_kind='umbrella')
    m = cases.read_project(root)
    m['controller_kind'] = 'umbrella'
    m['subprojects'] = {name: {'path': relative} for name, relative in PATHS.items()}
    m['next_action'] = 'Start any subproject from its own brief; handoffs are optional.'
    cases.publish(root, {}, expected_revision=m['manifest_revision'], project=m,
                  decision_id='independent-subprojects', reason='Initialize independent subprojects')
    return root


def start(root, name, title='', brief=''):
    name = canonical_name(name)
    root = Path(root).absolute()
    initialize(root, title or root.name)
    target = path(root, name)
    if name == 'business':
        cases.initialize(target, title or cases.read_project(root)['title'], project_id=cases.read_project(root)['project_id'])
        return target
    relative = target.relative_to(root).as_posix()
    if not (target / 'README.md').exists():
        m = cases.read_project(root)
        brief_text = '# Brief\n\n' + (brief or 'Scope and desired outcome to be supplied. No upstream subproject is required.') + '\n'
        files = {relative + '/README.md': '# ' + name.title() + '\n\nCurrent outputs belong here.\n\n[Project overview](' + ('../../' if '/' in relative else '../') + 'README.md)\n',
            relative + '/brief.md': brief_text}
        if name == 'marketing':
            files[relative + '/workstream.json'] = cases.encoded({
                'schema_version': '1.0', 'owner': 'marketing', 'revision': 1, 'status': 'briefed',
                'brief': {'path': 'brief.md', 'sha256': hashlib.sha256(brief_text.encode()).hexdigest()},
                'artifact_refs': [], 'imported_decisions': []})
        cases.publish(root, files,
            expected_revision=m['manifest_revision'], decision_id='start-' + name,
            reason='Start ' + name + ' independently')
    return target


def validate_marketing_workstream(root):
    """Read the registered Marketing workspace and report every stale binding."""
    root = Path(root).absolute()
    destination = path(root, 'marketing')
    workstream_path = cases.safe(root, (destination / 'workstream.json').relative_to(root).as_posix())
    if not workstream_path.is_file():
        raise ValueError('Marketing workstream is not initialized; start the Marketing subproject first')
    state = json.loads(workstream_path.read_text(encoding='utf-8'))
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas/marketing-workstream.schema.json').read_text())
    errors = list(Draft202012Validator(schema).iter_errors(state))
    if errors:
        raise ValueError('invalid Marketing workstream: ' + errors[0].message)
    stale = []

    def verify(base, relative, digest, label):
        try:
            target = cases.safe(base, relative)
            if target.is_symlink() or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                stale.append(label + ': missing or changed ' + relative)
        except (ValueError, OSError):
            stale.append(label + ': invalid or out-of-scope path ' + relative)

    verify(destination, state['brief']['path'], state['brief']['sha256'], 'brief')
    for item in state['artifact_refs']:
        verify(destination, item['path'], item['sha256'], 'artifact')
    for item in state['imported_decisions']:
        verify(root, item['path'], item['sha256'], 'imported decision ' + item['owner'])
        if item.get('review_status') != 'approved':
            stale.append('imported decision needs applicability review: ' + item.get('path', 'unknown'))
        if not item.get('approved_for', '').strip():
            stale.append('imported decision has no approved use: ' + item.get('path', 'unknown'))
    if state['status'] == 'review_required':
        stale.append('workstream is explicitly marked review_required')
    return {'path': str(workstream_path), 'revision': state['revision'], 'status': state['status'],
            'stale_bindings': stale, 'valid_for_use': not stale, 'state': state}


def publish_marketing_workstream(root, artifact_files, *, expected_manifest_revision,
                                 decision_id, reason, status='active', imported_decisions=None):
    """Publish Marketing artifacts and their hash-bound workstream revision together."""
    root = Path(root).absolute()
    current = validate_marketing_workstream(root)
    destination = path(root, 'marketing')
    replacement_paths = set(artifact_files)
    blocking = [issue for issue in current['stale_bindings']
                if not (issue.startswith('artifact: missing or changed ') and
                        issue.removeprefix('artifact: missing or changed ') in replacement_paths)]
    if blocking:
        raise ValueError('Marketing inputs need review before publication: ' + '; '.join(blocking))
    state = dict(current['state'])
    if imported_decisions is not None:
        state['imported_decisions'] = imported_decisions
    if status not in {'active', 'review_required', 'complete'}:
        raise ValueError('Marketing workstream status must be active, review_required, or complete')
    state['status'] = status
    refs = {item['path']: item['sha256'] for item in state['artifact_refs']}
    outputs = {}
    for relative, content in artifact_files.items():
        target = cases.safe(destination, relative)
        if target.name == 'workstream.json' or relative == 'brief.md':
            raise ValueError('publish Marketing outputs cannot replace the workstream or brief directly')
        raw = content.encode('utf-8') if isinstance(content, str) else content
        outputs[(destination / relative).relative_to(root).as_posix()] = raw
        refs[relative] = hashlib.sha256(raw).hexdigest()
    state['artifact_refs'] = [{'path': key, 'sha256': value} for key, value in sorted(refs.items())]
    state['revision'] += 1
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas/marketing-workstream.schema.json').read_text())
    schema_errors = list(Draft202012Validator(schema).iter_errors(state))
    if schema_errors:
        raise ValueError('invalid Marketing publication: ' + schema_errors[0].message)
    for item in state['imported_decisions']:
        try:
            target = cases.safe(root, item['path'])
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('imported decision is missing or changed: ' + item['path'])
        except (ValueError, OSError) as exc:
            raise ValueError('invalid imported decision: ' + item['path']) from exc
    workstream_relative = (destination / 'workstream.json').relative_to(root).as_posix()
    outputs[workstream_relative] = cases.encoded(state)
    project = cases.read_project(root)
    if project['manifest_revision'] != expected_manifest_revision:
        raise ValueError('Marketing publication revision conflict')
    cases.publish(root, outputs, expected_revision=expected_manifest_revision,
                  decision_id=decision_id, reason=reason)
    return state


def refresh_marketing_bindings(root, *, imported_decisions, expected_manifest_revision,
                               decision_id, reason):
    """Record an explicit reviewed refresh after a brief/source/artifact changed."""
    if not isinstance(reason, str) or len(reason.strip()) < 12:
        raise ValueError('review reason must explain why current Marketing inputs apply')
    root = Path(root).absolute()
    current = validate_marketing_workstream(root)
    destination = path(root, 'marketing')
    state = dict(current['state'])
    for item in state['artifact_refs']:
        target = cases.safe(destination, item['path'])
        if not target.is_file():
            raise ValueError('cannot refresh missing Marketing artifact: ' + item['path'])
        item['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    brief = cases.safe(destination, state['brief']['path'])
    if not brief.is_file():
        raise ValueError('cannot refresh missing Marketing brief')
    state['brief']['sha256'] = hashlib.sha256(brief.read_bytes()).hexdigest()
    if not isinstance(imported_decisions, list):
        raise ValueError('review must supply the current imported decision bindings')
    for item in imported_decisions:
        target = cases.safe(root, item['path'])
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('reviewed imported decision does not match current source: ' + item['path'])
        if not item.get('applicability', '').strip() or not item.get('limits', '').strip():
            raise ValueError('reviewed imported decision must state applicability and limits')
    state['imported_decisions'] = imported_decisions
    state['status'] = 'active'
    state['revision'] += 1
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas/marketing-workstream.schema.json').read_text())
    schema_errors = list(Draft202012Validator(schema).iter_errors(state))
    if schema_errors:
        raise ValueError('invalid reviewed Marketing binding: ' + schema_errors[0].message)
    project = cases.read_project(root)
    if project['manifest_revision'] != expected_manifest_revision:
        raise ValueError('Marketing review publication revision conflict')
    relative = (destination / 'workstream.json').relative_to(root).as_posix()
    cases.publish(root, {relative: cases.encoded(state)}, expected_revision=expected_manifest_revision,
        decision_id=decision_id, reason='Reviewed Marketing inputs: ' + reason.strip())
    return state


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', required=True, type=Path)
    p.add_argument('--start', required=True, choices=[*PATHS, 'business-analysis'])
    p.add_argument('--title', default='')
    p.add_argument('--brief', default='')
    a = p.parse_args()
    print(start(a.workspace, a.start, a.title, a.brief))


if __name__ == '__main__':
    main()
