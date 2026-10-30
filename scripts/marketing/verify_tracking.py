"""Compare a tracking plan with event names observed in GA4 or PostHog (default last 7 days).

Unknown is never observed and never zero. Output carries event names, counts and property names only.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts/validate_apis'))
from scripts.marketing import connections
from scripts.marketing.campaign import encoded, read_json, schema_errors
from scripts.marketing.import_presets import import_export
from common import get_secret

PRESETS = {'ga4': 'ga4-events-v1', 'posthog': 'posthog-events-v1'}
NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_$.-]{0,99}$')
POSTHOG_STEPS = [
    'In PostHog create a personal API key with only the query:read scope (Settings > Personal API keys); this is the account owner\'s action.',
    'Export POSTHOG_PERSONAL_API_KEY and POSTHOG_PROJECT_ID, and POSTHOG_HOST if not on https://us.posthog.com (use https://eu.posthog.com for EU Cloud). Keep them out of the repository.',
]
GA4_PROPERTY_STEP = 'Export GA4_PROPERTY_ID (numeric GA4 property ID) so the Data API report targets the right property.'


def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def posthog_settings():
    _, key = get_secret('POSTHOG_PERSONAL_API_KEY'); _, project = get_secret('POSTHOG_PROJECT_ID'); _, host = get_secret('POSTHOG_HOST')
    return key, project, (host or 'https://us.posthog.com').rstrip('/')


def _posthog_query(host, project, key, sql):
    body = json.dumps({'query': {'kind': 'HogQLQuery', 'query': sql}}).encode()
    req = urllib.request.Request(f'{host}/api/projects/{project}/query/', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - host is owner configured, https enforced below
        return json.loads(resp.read())


def probe_posthog(*, query=None):
    """Read-only check: one HogQL `SELECT 1` through POST /api/projects/:id/query/ (scope query:read). No key means no network call."""
    key, project, host = posthog_settings(); steps = []
    if not (key and project):
        status = 'unconnected'; steps = list(POSTHOG_STEPS)
    elif not host.startswith('https://'):
        status = 'error'; steps = ['POSTHOG_HOST must start with https://.']
    else:
        try:
            (query or _posthog_query)(host, project, key, 'SELECT 1')
            status = 'connected'
        except Exception:  # never echo exception text: it may carry the key
            status = 'error'; steps = ['PostHog query API call failed before a usable response; check key scope (query:read), project ID and host.', *POSTHOG_STEPS]
    return {'provider': 'posthog', 'status': status, 'checked_at': _stamp(), 'owner_steps': steps}


def _ga4_live(plan_events, days, request=None):
    from google.auth.transport.requests import AuthorizedSession
    import google.auth
    _, prop = get_secret('GA4_PROPERTY_ID')
    credentials, _ = google.auth.default(scopes=connections.PROBES['ga4']['scopes'])
    session = AuthorizedSession(credentials)
    url = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
    def run(body):
        r = session.post(url, json=body, timeout=30)
        if r.status_code != 200: raise RuntimeError('GA4 report failed')
        return r.json()
    rng = [{'startDate': f'{days}daysAgo', 'endDate': 'yesterday'}]
    out = {}
    for row in run({'dateRanges': rng, 'dimensions': [{'name': 'eventName'}], 'metrics': [{'name': 'eventCount'}], 'limit': 10000}).get('rows', []):
        out[row['dimensionValues'][0]['value']] = {'count': int(row['metricValues'][0]['value']), 'props': {}}
    for e in plan_events:
        if e['name'] not in out: continue
        for prop_name in e['required_properties']:
            try:  # needs a registered event-scoped custom dimension; otherwise stays unknown
                rows = run({'dateRanges': rng, 'dimensions': [{'name': f'customEvent:{prop_name}'}], 'metrics': [{'name': 'eventCount'}],
                            'dimensionFilter': {'filter': {'fieldName': 'eventName', 'stringFilter': {'value': e['name']}}}, 'limit': 100}).get('rows', [])
                out[e['name']]['props'][prop_name] = any(r['dimensionValues'][0]['value'] not in ('(not set)', '') and int(r['metricValues'][0]['value']) > 0 for r in rows)
            except Exception:
                pass
    return out


def _posthog_live(plan_events, days):
    key, project, host = posthog_settings()
    def q(sql): return _posthog_query(host, project, key, sql).get('results', [])
    out = {}
    for name, count in q(f'SELECT event, count() FROM events WHERE timestamp > now() - INTERVAL {int(days)} DAY GROUP BY event LIMIT 10000'):
        out[name] = {'count': int(count), 'props': {}}
    for e in plan_events:
        if e['name'] not in out or not e['required_properties']: continue
        cols = ', '.join(f"countIf(isNotNull(properties.{p}))" for p in e['required_properties'])  # names validated by schema regex
        name = e['name'].replace("'", "''")
        rows = q(f"SELECT {cols} FROM events WHERE event = '{name}' AND timestamp > now() - INTERVAL {int(days)} DAY")
        if rows:
            for p, n in zip(e['required_properties'], rows[0]): out[e['name']]['props'][p] = int(n) > 0
    return out


def _from_export(path, source, metadata, days):
    path = Path(path); meta = dict(metadata or {})
    for line in path.read_text(encoding='utf-8-sig').splitlines()[:25]:
        m = re.match(r'#\s*([a-z_]+)\s*:\s*(\S.*)$', line)
        if m and m.group(1) in {'report_scope', 'property', 'period_start', 'period_end', 'timezone', 'exported_at'}: meta.setdefault(m.group(1), m.group(2).strip())
    doc = import_export(path, PRESETS[source], meta)
    m = doc['metadata']
    span = (date.fromisoformat(m['period_end']) - date.fromisoformat(m['period_start'])).days + 1
    data = {}
    for o in doc['observations']:
        if o['metric'] == 'event_count' and o['availability'] == 'available': data[o['dimension']] = {'count': int(o['value']), 'props': {}}
    return data, {'kind': 'export', 'preset': PRESETS[source], 'period_start': m['period_start'], 'period_end': m['period_end'], 'days': span, 'complete': span >= days}


def verify(plan: Path, source: str, *, export: Path | None = None, days: int = 7, metadata: dict | None = None,
           fetcher=None, store=None) -> dict:
    if source not in PRESETS: raise ValueError('source must be ga4 or posthog')
    document = read_json(Path(plan)); errors = schema_errors('tracking-plan.schema.json', document)
    if errors: raise ValueError('tracking plan invalid: ' + '; '.join(errors[:5]))
    events = [e for e in document['events'] if source in e['destinations']]
    data = None; reasons = []; connection = None
    origin = {'kind': 'none', 'window_days': days}
    if export is not None:
        data, origin = _from_export(export, source, metadata, days)
        connection = {'provider': source, 'status': 'export', 'owner_steps': []}
        if not origin['complete']: reasons.append(f"export period covers {origin['days']} days, shorter than the {days}-day window; events cannot be judged absent")
    else:
        if fetcher:
            connection = {'provider': source, 'status': 'connected', 'owner_steps': []}  # injected data source (tests, replay)
        elif source == 'ga4':
            connection = connections.probe('ga4', store=store)
            if connection['status'] == 'connected' and not get_secret('GA4_PROPERTY_ID')[1]:
                connection = connection | {'status': 'unconnected', 'owner_steps': [GA4_PROPERTY_STEP]}
        else:
            connection = probe_posthog()
        if connection['status'] == 'connected':
            try:
                live = fetcher or (_ga4_live if source == 'ga4' else _posthog_live)
                data = live(events, days); origin = {'kind': 'live', 'window_days': days, 'complete': True}
            except Exception:  # never echo exception text: it may carry token material
                connection = connection | {'status': 'error', 'owner_steps': ['The event query failed; no event was judged.']}
    if data is None:
        reasons.append(f"{source} data unavailable ({connection['status']}); no event was judged")
    complete = data is not None and origin.get('complete', True)
    rows = []
    for e in events:
        gated = e.get('consent_gated', e['consent_category'] != 'necessary')
        seen = (data or {}).get(e['name'])
        row = {'name': e['name'], 'required_for_launch': e['required_for_launch'], 'consent_category': e['consent_category'], 'count': None, 'properties': {}}
        if data is None or not complete: row['status'] = 'unknown'
        elif seen and seen['count'] > 0:
            row['status'] = 'observed'; row['count'] = seen['count']
            for p in e['required_properties']:
                v = seen['props'].get(p); row['properties'][p] = 'unknown' if v is None else ('present' if v else 'missing')
        elif gated: row['status'] = 'unknown_consent_gated'  # zero here may be declined consent; no consent denominator is available
        else: row['status'] = 'not_observed'; row['count'] = 0
        if row['status'] != 'observed':
            row['properties'] = {p: 'unknown' for p in e['required_properties']}
        rows.append(row)
        if e['required_for_launch']:
            if row['status'] != 'observed':
                if data is not None and complete: reasons.append(f"{e['name']}: {row['status']}")
            else:
                bad = [f'{p} {s}' for p, s in row['properties'].items() if s != 'present']
                if bad: reasons.append(f"{e['name']}: required properties not confirmed ({', '.join(bad)})")
    launch = [r for r in rows if r['required_for_launch']]
    ready = bool(launch) and not reasons and all(r['status'] == 'observed' and all(s == 'present' for s in r['properties'].values()) for r in launch)
    if not launch and not reasons: reasons.append('plan has no launch-required event for this source')
    return {'schema_version': 1, 'source': source, 'checked_at': _stamp(), 'window_days': days, 'data_origin': origin,
            'connection': connection, 'events': rows, 'verdict': 'ready' if ready else 'not_ready', 'reasons': reasons,
            'boundary': 'Event names and counts only. Consent-gated zeros and unverifiable properties are unknown, not missing.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path); p.add_argument('--source', choices=sorted(PRESETS), required=True)
    p.add_argument('--export', type=Path); p.add_argument('--days', type=int, default=7)
    p.add_argument('--meta', action='append', default=[], metavar='KEY=VALUE', help='export metadata (property, period_start, period_end, timezone, exported_at, report_scope)')
    a = p.parse_args()
    try:
        result = verify(a.plan, a.source, export=a.export, days=a.days, metadata=dict(m.split('=', 1) for m in a.meta))
    except (ValueError, OSError) as exc:
        print(encoded({'status': 'invalid', 'message': str(exc)[:300]})); return 2
    print(encoded(result)); return 0 if result['verdict'] == 'ready' else 1


if __name__ == '__main__': raise SystemExit(main())
