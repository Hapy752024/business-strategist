"""Independent subproject entry points and explicit, optional handoff connections."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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


def marketing_artifact_errors(relative, raw, destination, staged=None):
    """Shared publication/resume validation for evidence-bearing Marketing artifacts."""
    from scripts.marketing.keyword_map import validate as validate_map, validate_resource
    from scripts.marketing.earned_media import validate as validate_opportunities
    if not relative.endswith(('keyword-map.json', 'content-brief.json', 'opportunities.json', 'opportunity.json')):
        return []
    try:
        doc = json.loads(raw)
        if relative.endswith(('opportunities.json', 'opportunity.json')):
            return validate_opportunities(doc, destination, staged)
        if relative.endswith('keyword-map.json'):
            return validate_map(doc, destination, staged)
        if not isinstance(doc, dict):
            return ['content brief must be an object']
        return validate_resource(doc['public_resource'], destination, staged) if 'public_resource' in doc else []
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return [str(exc)]


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
        if item['path'] == 'execution-plan.json':
            try:
                from scripts.marketing.execution import scope_complete as execution_scope_complete, validate as validate_execution
            except ModuleNotFoundError:
                from marketing.execution import scope_complete as execution_scope_complete, validate as validate_execution
            try:
                execution = json.loads((destination / item['path']).read_text(encoding='utf-8'))
            except (OSError, ValueError):
                stale.append('marketing execution: missing or malformed execution-plan.json')
                continue
            errors = validate_execution(execution, destination)
            stale.extend('marketing execution: ' + error for error in errors)
            if state['status'] == 'complete' and not errors and not execution_scope_complete(execution, destination):
                stale.append('marketing execution: required actions are not all verified complete')
        try:
            from scripts.marketing.link_observations import resolve_bytes
            issues = marketing_artifact_errors(item['path'], resolve_bytes(destination, item['path']), destination)
            stale.extend('marketing artifact ' + item['path'] + ': ' + e for e in issues)
        except (OSError, ValueError) as exc:
            stale.append('marketing artifact ' + item['path'] + ': ' + str(exc))
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
    artifact_files = dict(artifact_files)
    current = validate_marketing_workstream(root)
    destination = path(root, 'marketing')
    replacement_paths = set(artifact_files)
    def repaired_with_transaction(issue):
        if issue.startswith('artifact: missing or changed '):
            return issue.removeprefix('artifact: missing or changed ') in replacement_paths
        if issue == 'marketing execution: required actions are not all verified complete':
            return 'execution-plan.json' in replacement_paths
        if issue.startswith('marketing execution: ') and ': observation:' in issue:
            return bool(replacement_paths)
        if issue.startswith('marketing artifact '):
            # Every prospective artifact is validated again before commit.
            return bool(replacement_paths)
        marker = ': prepared material missing, changed or out of scope: '
        if issue.startswith('marketing execution: ') and marker in issue and 'execution-plan.json' in replacement_paths:
            material = issue.split(marker, 1)[1]
            return material in replacement_paths
        return False
    blocking = [issue for issue in current['stale_bindings'] if not repaired_with_transaction(issue)]
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
    execution_path = destination / 'execution-plan.json'
    from scripts.marketing.link_observations import bound_bytes
    if execution_path.is_file():
        try:
            old_execution = json.loads(execution_path.read_bytes())
            old_actions = {row.get('id'): row for row in old_execution.get('actions', [])}
            for old in old_actions.values():
                binding = old.get('observation')
                if binding:
                    # A staged restoration is legal only if it matches the historical digest.
                    try:
                        observation = json.loads(bound_bytes(binding, destination, artifact_files))
                        bound_bytes(observation['capture'], destination, artifact_files)
                    except (ValueError, OSError, KeyError) as exc:
                        raise ValueError('placement evidence is immutable; restore original bytes or use a new observation/capture path') from exc
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            old_actions = {}
    else:
        old_actions = {}
    if 'execution-plan.json' in artifact_files:
        try:
            new_execution = json.loads(artifact_files['execution-plan.json'])
            for action in new_execution.get('actions', []):
                old = old_actions.get(action.get('id'), {})
                try:
                    from scripts.marketing.execution import invalidate_changed_action
                except ModuleNotFoundError:
                    from marketing.execution import invalidate_changed_action
                invalidate_changed_action(old, action)
            artifact_files['execution-plan.json'] = json.dumps(new_execution, ensure_ascii=False, indent=2) + '\n'
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            pass  # The normal schema validation below reports malformed replacement input.
    for relative, content in artifact_files.items():
        target = cases.safe(destination, relative)
        if target.name == 'workstream.json' or relative == 'brief.md':
            raise ValueError('publish Marketing outputs cannot replace the workstream or brief directly')
        raw = content.encode('utf-8') if isinstance(content, str) else content
        issues = marketing_artifact_errors(relative, raw, destination, artifact_files)
        if issues:
            raise ValueError('invalid Marketing artifact: ' + '; '.join(issues))
        if relative == 'execution-plan.json':
            try:
                from scripts.marketing.execution import validate as validate_execution
            except ModuleNotFoundError:
                from marketing.execution import validate as validate_execution
            execution = json.loads(raw.decode('utf-8'))
            errors = validate_execution(execution, destination, artifact_files)
            if errors:
                raise ValueError('invalid Marketing execution plan: ' + '; '.join(errors))
        outputs[(destination / relative).relative_to(root).as_posix()] = raw
        refs[relative] = hashlib.sha256(raw).hexdigest()
    state['artifact_refs'] = [{'path': key, 'sha256': value} for key, value in sorted(refs.items())]
    state['revision'] += 1
    # Revalidate all prospective artifacts, including source-only updates/restoration.
    from scripts.marketing.link_observations import resolve_bytes
    for relative in refs:
        issues = marketing_artifact_errors(relative, resolve_bytes(destination, relative, artifact_files), destination, artifact_files)
        if issues:
            raise ValueError('invalid Marketing artifact: ' + '; '.join(issues))
    # Revalidate bound actions even when only a capture/material is replaced.
    candidate = artifact_files.get('execution-plan.json')
    if candidate is None and execution_path.is_file():
        candidate = execution_path.read_bytes()
    if candidate is not None:
        try:
            from scripts.marketing.execution import validate as validate_execution
        except ModuleNotFoundError:
            from marketing.execution import validate as validate_execution
        prospective_execution = json.loads(candidate)
        issues = validate_execution(prospective_execution, destination, artifact_files)
        if issues:
            raise ValueError('invalid Marketing execution plan: ' + '; '.join(issues))
    if status == 'complete':
        candidate = artifact_files.get('execution-plan.json')
        if candidate is None and execution_path.is_file():
            candidate = execution_path.read_bytes()
        if candidate is not None:
            try:
                from scripts.marketing.execution import scope_complete as execution_scope_complete
            except ModuleNotFoundError:
                from marketing.execution import scope_complete as execution_scope_complete
            completed_plan = json.loads(candidate) if isinstance(candidate, str) else json.loads(candidate.decode('utf-8'))
            if not execution_scope_complete(completed_plan, destination, artifact_files):
                raise ValueError('Marketing scope cannot be complete while required actions are unverified')
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
