"""Validate secret-free reporting connection definitions; does not resolve secrets."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.marketing.campaign import schema_errors, read_json, encoded, marketing, resolve_project


def validate(document, project_id):
    errors=schema_errors('marketing-connections.schema.json',document)
    if errors: return ['connection schema validation failed (values redacted)']
    if document['project_id'] != project_id: errors.append('connection project mismatch')
    ids=[c['id'] for c in document['connections']]
    if len(set(ids)) != len(ids): errors.append('duplicate connection IDs')
    for c in document['connections']:
        if c['credential_ref'].split('/')[0] != project_id:
            errors.append('credential reference belongs to another project')
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);args=p.parse_args()
    try:
        root=resolve_project(args.project); doc=read_json(marketing(root)/'connections.json')
        errors=validate(doc,args.project)
        print(encoded({'status':'invalid' if errors else 'configured_for_local_exports_only','errors':errors,
            'connections':[{'id':c['id'],'provider':c['provider'],'status':'unconfigured'} for c in doc.get('connections',[]) if isinstance(c,dict) and 'id' in c and 'provider' in c],
            'live_access_verified':False}))
        return 2 if errors else 0
    except (ValueError,OSError,KeyError):
        print(encoded({'status':'invalid','message':'Cannot validate the selected project connections'}));return 2

if __name__=='__main__':raise SystemExit(main())
