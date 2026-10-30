"""Project-bound local campaign configuration. Does not load credentials or call providers."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import case_workspace as cases, subprojects


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def bytes_digest(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def identifier(value):
    if not isinstance(value, str) or len(value) > 80 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError('project, campaign and connection IDs must be lowercase slugs')
    return value


def safe(base, relative):
    base = Path(base).resolve()
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('path must stay within the selected workspace')
    candidate = base
    for part in rel.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError('symlinks are not allowed in campaign paths')
    if not candidate.resolve().is_relative_to(base):
        raise ValueError('path escapes the selected workspace')
    return candidate


def resolve_project(project, projects_root=None):
    base = Path(projects_root or ROOT / 'projects').resolve()
    root = safe(base, identifier(project))
    if not (root / cases.PROJECT).is_file():
        raise ValueError('selected project is not initialized: ' + project)
    cases.read_project(root)
    destination = subprojects.path(root, 'marketing')
    safe(root, destination.relative_to(root))
    return root


def marketing(root):
    destination = subprojects.path(Path(root), 'marketing')
    safe(root, destination.relative_to(root))
    return destination


def schema_errors(name, document):
    schema = json.loads((ROOT / 'schemas' / name).read_text())
    return [f'{"/".join(map(str, e.path)) or "document"}: {e.message}'
            for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)]


def require_schema(name, document):
    errors = schema_errors(name, document)
    if errors:
        # Do not echo schema exception values: they may be invalid secret material.
        raise ValueError('invalid ' + name + ' at ' + errors[0].split(':', 1)[0])


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load(root, campaign_id):
    path = safe(marketing(root), f'campaigns/{identifier(campaign_id)}/campaign.json')
    document = read_json(path)
    require_schema('marketing-campaign.schema.json', document)
    if document['project_id'] != Path(root).name or document['campaign_id'] != campaign_id:
        raise ValueError('campaign project/ID binding mismatch')
    from scripts.marketing.connections import validate
    connection_doc = read_json(safe(marketing(root), 'connections.json'))
    errors = validate(connection_doc, Path(root).name)
    if errors:
        raise ValueError('invalid project connections: ' + '; '.join(errors))
    available = {c['id'] for c in connection_doc['connections']}
    if set(document['connection_ids']) - available:
        raise ValueError('campaign references an unknown project connection')
    return document


def context_digest(root, campaign_id):
    destination=marketing(root)
    return digest({'campaign':load(root,campaign_id),
        'context':bytes_digest(safe(destination,f'campaigns/{campaign_id}/campaign-context.md').read_bytes()),
        'claims':read_json(safe(destination,f'campaigns/{campaign_id}/approved-claims.json'))})


def queue(root):
    p = safe(marketing(root), 'execution-plan.json')
    return read_json(p) if p.is_file() else {'schema_version':3, 'scope':'Recurring campaign work', 'revision':1, 'actions':[]}


def publish(root, files, reason, status='active', expected_revision=None):
    revision = cases.read_project(root)['manifest_revision'] if expected_revision is None else expected_revision
    return subprojects.publish_marketing_workstream(root, files, expected_manifest_revision=revision,
        decision_id='campaign-' + digest(files)[:16], reason=reason, status=status)


def setup(root, document, connections=None):
    require_schema('marketing-campaign.schema.json', document)
    if document['project_id'] != Path(root).name:
        raise ValueError('campaign belongs to a different project')
    destination = marketing(root)
    relative = f'campaigns/{document["campaign_id"]}'
    if safe(destination, relative + '/campaign.json').exists():
        raise ValueError('campaign already exists; update it through reviewed Marketing publication')
    from scripts.marketing.connections import validate
    config_path = safe(destination, 'connections.json')
    config = connections if connections is not None else (read_json(config_path) if config_path.exists() else
        {'schema_version':1, 'project_id':Path(root).name, 'connections':[]})
    errors = validate(config, Path(root).name)
    if errors:
        raise ValueError('invalid connections: ' + '; '.join(errors))
    if set(document['connection_ids']) - {c['id'] for c in config['connections']}:
        raise ValueError('unknown connection ID')
    if config_path.exists() and config != read_json(config_path):
        raise ValueError('setup cannot replace existing project connections')
    context = ('# Campaign context\n\nAudience: ' + document['audience'] + '\n\nOffer: ' + document['offer'] +
        '\n\nObjective: ' + document['objective'] + '\n\nStatus: supplied brief; factual claims require reviewed sources.\n'
        '\nBanned/regulated language and jurisdiction: to be confirmed for this project.\n'
        '\nJourney hooks and sales path: pending; record sourced touchpoint, useful intervention, '
        'distribution, CTA, qualification and follow-up owner.\n'
        '\nEvent contract: pending; define successful triggers, canonical occurrence IDs, '
        'platform mappings/destinations, optimization role, consent and actual outcome verification.\n'
        '\nApply references/journey-activation-and-measurement.md and '
        'references/ad-platform-connections.md before implementation or launch recommendations. '
        'Local reporting can proceed with these gaps explicitly disclosed.\n')
    files = {relative+'/campaign.json':encoded(document), relative+'/campaign-context.md':context,
        relative+'/approved-claims.json':encoded({'schema_version':1, 'claims':[]})}
    if not config_path.exists(): files['connections.json'] = encoded(config)
    publish(root, files, 'Initialize local campaign configuration; no external authority granted')
    return document


def task_event(root, campaign_id, action_id, event, *, reason='', until='', evidence=''):
    load(root, campaign_id)
    revision = cases.read_project(root)['manifest_revision']
    document = queue(root)
    from scripts.marketing import execution
    if execution.validate(document, marketing(root)):
        raise ValueError('execution plan needs review before changing tasks')
    action = next((a for a in document['actions'] if a['id'] == action_id and a.get('campaign_id') == campaign_id), None)
    if action is None: raise ValueError('task does not belong to the selected campaign')
    if action['commitment_state'] == 'completed': raise ValueError('completed tasks are immutable; prepare a follow-up task')
    if event in {'accept','complete'} and action.get('context_sha256') != context_digest(root,campaign_id):
        raise ValueError('task context changed; review a new follow-up task before accepting or completing it')
    if event == 'accept':
        action.update(commitment_state='accepted', execution_status='awaiting_owner' if action['actor']=='owner' else 'prepared', decline_reason=None, deferred_until=None)
    elif event == 'decline':
        if not reason.strip(): raise ValueError('declining requires a reason')
        action.update(commitment_state='declined', decline_reason=reason, deferred_until=None)
    elif event == 'snooze':
        from datetime import date
        if date.fromisoformat(until) <= datetime.now(timezone.utc).date(): raise ValueError('snooze date must be in the future')
        action.update(commitment_state='deferred', deferred_until=until)
    elif event == 'complete':
        if action['commitment_state'] != 'accepted' or not evidence.strip():
            raise ValueError('completion requires an accepted task and owner-supplied evidence')
        if action.get('action_kind') != 'generic': raise ValueError('non-generic actions need their operation-specific verification workflow')
        action.update(commitment_state='completed', execution_status='verified', verification='Owner attestation: '+evidence)
    else: raise ValueError('unknown task event')
    document['revision'] += 1
    document['updated_at'] = now()
    plan, _ = execution.render(document)
    from scripts.marketing.review_cycle import owner_actions
    owners = owner_actions(document,root)
    publish(root, {'execution-plan.json':encoded(document), 'execution-plan.md':plan, 'owner-actions.md':owners},
        'Record explicit owner task decision; no external operation', expected_revision=revision)
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('setup')
    init.add_argument('--project', required=True); init.add_argument('--campaign', required=True)
    for name in ('objective','audience','offer'): init.add_argument('--'+name, required=True)
    for name in ('property','timezone','currency','attribution','maturity','report-scope','page-url'): init.add_argument('--'+name)
    init.add_argument('--connection', action='append', default=[])
    init.add_argument('--connections', type=Path, help='Secret-free connection definitions, never credential material')
    task = sub.add_parser('task')
    for name in ('project','campaign','action'): task.add_argument('--'+name, required=True)
    task.add_argument('--event', choices=['accept','decline','snooze','complete'], required=True)
    for name in ('reason','until','evidence'): task.add_argument('--'+name, default='')
    args = parser.parse_args()
    try:
        root = resolve_project(args.project)
        if args.command == 'setup':
            doc={'schema_version':1,'project_id':args.project,'campaign_id':identifier(args.campaign),
                'objective':args.objective,'audience':args.audience,'offer':args.offer,
                'connection_ids':args.connection,'measurement':{key:getattr(args,key) for key in ('property','timezone','currency','attribution','maturity','report_scope') if getattr(args,key)}}
            if args.page_url: doc['page_url']=args.page_url
            setup(root, doc, read_json(args.connections) if args.connections else None)
        else: task_event(root,args.campaign,args.action,args.event,reason=args.reason,until=args.until,evidence=args.evidence)
        print(encoded({'status':'saved','project':args.project,'campaign':args.campaign,'external_actions':False}))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(encoded({'status':'error','message':str(exc)}),file=sys.stderr); return 2

if __name__ == '__main__': raise SystemExit(main())
