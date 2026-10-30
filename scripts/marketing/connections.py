"""Validate secret-free reporting connection definitions; `probe` checks read-only Google connections."""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
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


ADS_API_VERSION='v26'  # verify against the Google Ads API release notes when onboarding
PROBES={
    'gsc':{'url':'https://www.googleapis.com/webmasters/v3/sites','scopes':['https://www.googleapis.com/auth/webmasters.readonly'],
           'call':'Search Console sites.list'},
    'ga4':{'url':'https://analyticsadmin.googleapis.com/v1beta/accountSummaries?pageSize=1','scopes':['https://www.googleapis.com/auth/analytics.readonly'],
           'call':'GA4 Admin accountSummaries.list'},
    'google_ads':{'url':f'https://googleads.googleapis.com/{ADS_API_VERSION}/customers:listAccessibleCustomers','scopes':['https://www.googleapis.com/auth/adwords'],
           'call':'Google Ads listAccessibleCustomers'},
}
OWNER_STEPS={
    'gsc':['Run: npx search-console-mcp@2.1.3 setup (browser OAuth; keep the default read-only webmasters.readonly scope) or create Application Default Credentials with the webmasters.readonly scope.',
           'Add the authorizing Google account (or service-account email) as a user of the Search Console property.'],
    'ga4':['Run: gcloud auth application-default login --scopes https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform',
           'Enable the Google Analytics Admin API and Data API in the Cloud project, and give the authorizing account Viewer access to the GA4 property.'],
    'google_ads':['Create Application Default Credentials for an account with access to the Ads customer (scope https://www.googleapis.com/auth/adwords; broad, so read-only rests on the MCP tool list, not the scope).',
                  'Enable the Google Ads API in the Cloud project, set GOOGLE_PROJECT_ID for the MCP, and confirm the project has API access (developer tokens are sunset on 2026-09-09; see references/ad-platform-connections.md).'],
}
COMMON_STEP='Point GOOGLE_APPLICATION_CREDENTIALS at the credentials JSON, or create Application Default Credentials; keep the file outside the repository. This is the account owner\'s action; agents do not log in.'
DEFAULT_STORE=Path(__file__).resolve().parents[2]/'.research-infra/marketing-connections.json'


def adc_path():
    env=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    candidates=[Path(env)] if env else []
    base=os.environ.get('CLOUDSDK_CONFIG') or os.path.join(os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config'),'gcloud')
    candidates.append(Path(base)/'application_default_credentials.json')
    return next((c for c in candidates if c.is_file()),None)


def google_request(method,url,scopes):
    """Default requester: google-auth with ADC; returns the HTTP status only (token never leaves this function)."""
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials,_=google.auth.default(scopes=scopes)
    return AuthorizedSession(credentials).request(method,url,timeout=20).status_code


def probe(provider,*,request=None,store=None):
    """Read-only 1-call check: connected|unconnected|error. Without credentials no network call is made."""
    if provider not in PROBES: raise ValueError('probe supports gsc, ga4 and google_ads')
    spec=PROBES[provider]; steps=[]
    if adc_path() is None:
        status='unconnected'; steps=[COMMON_STEP,*OWNER_STEPS[provider]]
    else:
        try:
            code=(request or google_request)('GET',spec['url'],spec['scopes'])
            status='connected' if code==200 else 'error'
            if status=='error': steps=[f"{spec['call']} returned HTTP {code}.",*OWNER_STEPS[provider]]
        except ImportError:
            status='error'; steps=['Install google-auth (pip install google-auth requests) to run the REST probe.']
        except Exception:  # never echo exception text: it may contain token material
            status='error'; steps=[f"{spec['call']} failed before an HTTP status was returned.",*OWNER_STEPS[provider]]
    result={'provider':provider,'status':status,'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'owner_steps':steps}
    path=Path(store) if store else DEFAULT_STORE
    try: record=json.loads(path.read_text())
    except (OSError,ValueError): record={}
    record.setdefault('probes',{})[provider]=result
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(record,indent=2)+'\n')
    return result


def main_probe(argv):
    p=argparse.ArgumentParser(prog='connections.py probe');p.add_argument('provider',choices=sorted(PROBES));p.add_argument('--store',type=Path)
    a=p.parse_args(argv); r=probe(a.provider,store=a.store); print(encoded(r)); return 0 if r['status']=='connected' else 1


def main():
    if sys.argv[1:2]==['probe']: return main_probe(sys.argv[2:])
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
