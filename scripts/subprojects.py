"""Independent subproject entry points and explicit, optional handoff connections."""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from scripts import case_workspace as cases
except ModuleNotFoundError:
    import case_workspace as cases

PATHS = {'business': 'business-analysis', 'branding': 'branding', 'website': 'digital-assets/website', 'others': 'digital-assets/others'}


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
    relative = PATHS[name]
    if not (target / 'README.md').exists():
        m = cases.read_project(root)
        cases.publish(root, {relative + '/README.md': '# ' + name.title() + '\n\nCurrent outputs belong here.\n\n[Project overview](' + ('../../' if '/' in relative else '../') + 'README.md)\n',
            relative + '/brief.md': '# Brief\n\n' + (brief or 'Scope and desired outcome to be supplied. No upstream subproject is required.') + '\n'},
            expected_revision=m['manifest_revision'], decision_id='start-' + name,
            reason='Start ' + name + ' independently')
    return target


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
