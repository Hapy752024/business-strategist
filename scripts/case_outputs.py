"""Publish downstream file changes through existing project transactions.

Standalone is an input mode, not an escape from destination ownership. Temporary
staging is local; installers, releases and asset approvals retain their own gates.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import uuid
from pathlib import Path

try:
    from scripts import case_workspace as cases
except ModuleNotFoundError:
    import case_workspace as cases


def business_root(root):
    m = cases.read_project(root)
    return cases.safe(root, m['subprojects']['business']['path']) if m.get('subprojects') else root


def preflight(destination, purpose, entry_mode='standalone', handoff=None):
    destination = Path(destination).absolute()
    root = cases.locate_publication(destination)
    if root is None:
        if entry_mode == 'business_linked':
            raise ValueError('business-linked output requires an explicit current business handoff')
        return None
    m = cases.read_project(root)
    relative = str(destination.relative_to(root))
    cases.safe(root, relative)
    allowed = {'brand': ('branding',), 'website': ('digital-assets/website', 'web-site'),
               'digital-assets': ('digital-assets/others',), 'strategy': ('strategy/baselines',)}[purpose]
    if m.get('controller_kind') == 'umbrella':
        key = {'brand':'branding', 'website':'website', 'digital-assets':'others'}.get(purpose)
        if key is None:
            raise ValueError('strategy belongs to the business subproject')
        allowed = (m['subprojects'][key]['path'],)
    elif (root.parent / cases.PROJECT).is_file() and cases.load(root.parent / cases.PROJECT).get('controller_kind') == 'umbrella':
        if purpose != 'strategy':
            raise ValueError('design outputs belong to independent sibling subprojects')
    if not any(relative == p or relative.startswith(p + '/') for p in allowed):
        raise ValueError('destination conflicts with subproject/output purpose')
    prefix = next(p for p in allowed if relative == p or relative.startswith(p + '/'))
    state_path = cases.safe(root, prefix + '/' + ('brand-manifest.json' if purpose == 'brand' else 'website-manifest.json'))
    if state_path.exists() and cases.load(state_path).get('entry_mode') == 'business_linked':
        entry_mode = 'business_linked'  # ordinary updates never silently unlink inputs
    if entry_mode not in {'standalone', 'business_linked'}:
        raise ValueError('unknown entry mode')
    execution, source, plan_digest = None, None, None
    if entry_mode == 'business_linked':
        source = business_root(root)
        plan = cases.load(cases.safe(source, 'strategy/strategy-plan.json'))
        plan_digest = cases.digest(cases.safe(source, 'strategy/strategy-plan.json').read_bytes())
        cases.check_plan(source, plan)
        execution = plan['execution_binding']
        if handoff:
            try:
                from scripts.brand.validate_business_to_brand_handoff import validate
            except ModuleNotFoundError:
                from brand.validate_business_to_brand_handoff import validate
            errors = validate(Path(handoff), check_sources=True)
            if errors:
                raise ValueError('; '.join(errors))
            context = cases.load(Path(handoff))
            if context.get('case_project_root') != str(source) or context.get('execution_binding') != execution:
                raise ValueError('handoff source authority conflicts with the destination business')
    return {'root': root, 'revision': m['manifest_revision'], 'execution_binding': execution,
            'business_root': source, 'plan_digest': plan_digest, 'entry_mode': entry_mode}


def tree(root, include=()):
    """Only authored workspace files, with no symlink traversal or build caches."""
    result = {}
    if not root.exists():
        return result
    for directory, dirs, files in __import__('os').walk(root, followlinks=False):
        current = Path(directory)
        for name in [*dirs, *files]:
            if (current / name).is_symlink():
                raise ValueError('workspace symlinks are not publication inputs')
        dirs[:] = [d for d in dirs if d not in {'node_modules', '.git', '.next', '__pycache__'}]
        if include:
            dirs[:] = [d for d in dirs if any((current / d).is_relative_to(root / p) or (root / p).is_relative_to(current / d) for p in include)]
        for name in files:
            path = current / name
            if include and not any(path == root / p or path.is_relative_to(root / p) for p in include):
                continue
            result[str(path.relative_to(root))] = path.read_bytes()
    return result


def run_staged(destination, purpose, operation, *, entry_mode='standalone', handoff=None, include=(), inputs=()):
    """Run a local writer privately, then atomically publish only changed files."""
    destination = Path(destination).absolute()
    # The staged operation can spawn children and take substantial time.  It
    # must retain the migration shared lock from authority resolution through
    # final publication so an exclusive cutover cannot begin mid-operation.
    # This also covers legacy destinations, which have no versioned controller
    # for preflight to discover but still have a stable project identity.
    with cases.migration_guard(destination):
        authority = preflight(destination, purpose, entry_mode, handoff)
        if authority is None:
            return operation(destination)
        authority = preflight(destination, purpose, entry_mode, handoff)
        return _run_managed_staged(destination, purpose, operation, authority,
                                   entry_mode=entry_mode, handoff=handoff,
                                   include=include, inputs=inputs)


def _run_managed_staged(destination, purpose, operation, authority, *, entry_mode, handoff, include, inputs):
    before = tree(destination, include)
    def input_state():
        values = {}
        for path in inputs:
            if path:
                path = Path(path).absolute()
                if path.is_symlink() or any(p.is_symlink() for p in path.parents):
                    raise ValueError('input paths must not traverse symlinks')
                values[str(path)] = tree(path) if path.is_dir() else path.read_bytes()
        return values
    original_inputs = input_state()
    handoff_digest = cases.digest(Path(handoff).read_bytes()) if handoff else None
    with tempfile.TemporaryDirectory(prefix='subproject-output-') as temporary:
        stage = Path(temporary) / destination.name
        stage.mkdir()
        for path, data in before.items():
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = operation(stage)
        if isinstance(result, int) and result != 0:
            raise ValueError('staged writer did not succeed')
        after = tree(stage)
        def final_paths(value):
            if isinstance(value, str) and (value == str(stage) or value.startswith(str(stage) + '/')):
                return str(destination) + value[len(str(stage)):]
            if isinstance(value, dict):
                return {key: final_paths(item) for key, item in value.items()}
            if isinstance(value, list):
                return [final_paths(item) for item in value]
            return value
        for path, data in after.items():
            if path.endswith('.json') and before.get(path) != data:
                value = json.loads(data)
                rewritten = final_paths(value)
                if rewritten != value:
                    after[path] = cases.encoded(rewritten).encode()
        changed = {path: after.get(path) for path in set(before) | set(after) if before.get(path) != after.get(path)}
        if changed:
            root = authority['root']
            with contextlib.ExitStack() as locks:
                # Parent first, then business. Do not hold either during a tool run.
                locks.enter_context(cases.project_lock(root))
                source = authority['business_root']
                if source and source != root:
                    locks.enter_context(cases.project_lock(source))
                current = preflight(destination, purpose, entry_mode)  # handoff was read outside the locks
                if current != authority or tree(destination, include) != before:
                    raise ValueError('publication conflict: subproject or input binding changed')
                if input_state() != original_inputs:
                    raise ValueError('publication conflict: source input changed')
                if handoff and cases.digest(Path(handoff).read_bytes()) != handoff_digest:
                    raise ValueError('handoff changed before publication')
                for path in changed:
                    actual = cases.safe(root, str((destination / path).relative_to(root)))
                    if (actual.read_bytes() if actual.exists() else None) != before.get(path):
                        raise ValueError('publication conflict: destination changed')
                prefix = str(destination.relative_to(root))
                changes = {prefix + '/' + path: data for path, data in changed.items()}
                receipt = {'entry_mode': authority['entry_mode'], 'execution_binding': authority['execution_binding'],
                           'changed_files': sorted(changed)}
                changes[prefix + '/publication.json'] = cases.encoded(receipt)
                cases.publish_locked(root, changes, expected_revision=authority['revision'],
                    decision_id=purpose + '-' + uuid.uuid4().hex, reason='Publish ' + purpose + ' outputs (' + entry_mode + ')')
        # Preserve explicitly created empty scaffold directories after file commit.
        for directory, dirs, _ in __import__('os').walk(stage):
            current = Path(directory)
            target = destination / current.relative_to(stage)
            target.mkdir(parents=True, exist_ok=True)
            for name in list(dirs):
                if name in {'node_modules', '.next', '.git'}:
                    dirs.remove(name)
                    # Installer caches are disposable, not current research/design
                    # authority. Keep newly installed caches only after publication.
                    if not (target / name).exists():
                        shutil.move(str(current / name), target / name)
        print(output.getvalue().replace(str(stage), str(destination)), end='')
        return final_paths(result)


def namespace_writer(args, attribute, operation, *, is_file=False, include=(), input_attributes=()):
    output = Path(getattr(args, attribute)).absolute()
    # Resolve owner under the same lock that covers any legacy direct write or
    # managed staged publication; migration cannot complete between lookup and
    # dispatch.
    with cases.migration_guard(output):
        return _namespace_writer_guarded(args, attribute, operation, output,
                                         is_file=is_file, include=include,
                                         input_attributes=input_attributes)


def _namespace_writer_guarded(args, attribute, operation, output, *, is_file=False, include=(), input_attributes=()):
    """Adapt small existing local exporters without duplicating their workflows."""
    import copy
    owner = cases.locate_publication(output)
    if not owner:
        return operation(args)
    relative = str(output.relative_to(owner))
    prefixes = [('branding', 'brand'), ('digital-assets/website', 'website'), ('digital-assets/others', 'digital-assets'), ('web-site', 'website')]
    prefix, purpose = next(((p, kind) for p, kind in prefixes if relative == p or relative.startswith(p + '/')), ('', ''))
    if not purpose:
        raise ValueError('output has no independent design subproject purpose')
    workspace = owner / prefix
    preflight(output, purpose)
    manifest = workspace / ('brand-manifest.json' if purpose == 'brand' else 'website-manifest.json')
    state = cases.load(manifest) if manifest.exists() else {}
    mode = state.get('entry_mode', 'standalone')
    handoff = workspace / state['business_to_brand'] if state.get('business_to_brand') else None
    def run(stage):
        staged = copy.copy(args)
        setattr(staged, attribute, stage / output.name if is_file else stage)
        return operation(staged)
    return run_staged(output.parent if is_file else output, purpose, run, entry_mode=mode, handoff=handoff,
        include=[output.name] if is_file else include, inputs=[getattr(args, key, None) for key in input_attributes])


def write_file(path, data, purpose, *, entry_mode='standalone', handoff=None):
    path = Path(path).absolute()
    return run_staged(path.parent, purpose, lambda stage: (stage / path.name).write_bytes(data) and None,
                      entry_mode=entry_mode, handoff=handoff, include=[path.name])


def asset_operation(args, operation):
    output = args.output_dir.absolute()
    with cases.migration_guard(output):
        return _asset_operation_guarded(args, operation, output)


def _asset_operation_guarded(args, operation, output):
    """Preflight both asset destinations before any provider/download side effect."""
    import copy
    record = args.record.absolute() if args.record else None
    owner = cases.locate_publication(output)
    record_owner = cases.locate_publication(record) if record else owner
    if owner != record_owner:
        raise ValueError('asset output and record have conflicting authorities')
    if owner is None:
        return operation(args)
    relative = str(output.relative_to(owner))
    roots = [('branding', 'brand'), ('digital-assets/website', 'website'), ('digital-assets/others', 'digital-assets'), ('web-site', 'website')]
    prefix, purpose = next(((p, kind) for p, kind in roots if relative == p or relative.startswith(p + '/')), ('', ''))
    if not prefix:
        raise ValueError('unknown asset output purpose')
    workspace = owner / prefix
    preflight(output, purpose)
    if record:
        preflight(record, purpose)
        if not record.is_relative_to(workspace):
            raise ValueError('record belongs to another subproject')
    def run(stage):
        staged = copy.copy(args)
        staged.output_dir = stage / output.relative_to(workspace)
        staged.record = stage / record.relative_to(workspace) if record else None
        return operation(staged)
    include = [str(output.relative_to(workspace))] + ([str(record.relative_to(workspace))] if record else [])
    return run_staged(workspace, purpose, run, include=include)
